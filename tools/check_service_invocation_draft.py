#!/usr/bin/env python3
"""Candidate invocation oracle; synthetic trusted host and atomic boundary, no runtime/DB."""
from __future__ import annotations

import copy

import check_services_draft as updates

FILE = updates.ROOT / "fixtures/services/v1/invocation-cases.json"
FAMILIES = {"definition-invalid", "physical-incompatible", "invalid-data",
            "operation-not-allowed", "execution-failure"}


def invoke(case):
    """Return public response separately from private test observations.

    currentAtCommit simulates an interleaving before one indivisible compare/write.
    Host facts and confirmation evidence are fixture setup, never client authority.
    """
    host = case["host"]
    request = case["request"]
    current = copy.deepcopy(host.get("currentAtCommit", host["current"]))
    observed = {"persisted": current, "writtenFields": [], "effects": 0, "dispatches": 0}

    def finish(status, family=None, code=None, **data):
        response = {"status": status, "diagnostics": []}
        if family:
            response["diagnostics"].append({"family": family, "code": code})
        response.update(data)
        return {"response": response, "observed": observed}

    def reject(code, family="operation-not-allowed"):
        return finish("rejected", family, code)

    if not isinstance(request, dict):
        return reject("INPUT_SHAPE", "invalid-data")
    if set(request) - {"target", "operation", "inputs"}:
        return reject("INPUT_SHAPE", "invalid-data")
    if not host.get("authorized", True) or not host.get("recordAccessible", True):
        return reject("UNAVAILABLE")
    if (request.get("target") != "demo.items" or request.get("operation") not in {"UPDATE", "inspect"}
            or not host.get("enabled", True) or not host.get("registered", True)):
        return reject("UNAVAILABLE")
    if not host.get("definitionValid", True):
        return reject("INVALID_DEFINITION", "definition-invalid")
    if host.get("capacity", "compatible") == "incompatible":
        return reject("INCOMPATIBLE_STORAGE", "physical-incompatible")
    if host.get("capacity", "compatible") == "not-verified":
        return reject("UNVERIFIED_CAPABILITY")
    inputs = request.get("inputs")
    if not isinstance(inputs, dict):
        return reject("INPUT_SHAPE", "invalid-data")
    if request["operation"] == "inspect":
        if inputs:
            return reject("INPUT_SHAPE", "invalid-data")
        observed["dispatches"] = 1
        if host.get("handlerFailure", False):
            # Private synthetic effect; the caller cannot infer it from failed.
            observed["effects"] = host.get("handlerFailureEffects", 0)
            return finish("failed", "execution-failure", "HANDLER_FAILED")
        if host.get("businessReject", False):
            return reject("BUSINESS_REJECTED", "invalid-data")
        return finish("success", output={"accepted": True})
    if (set(inputs) - {"key", "changes", "baseline", "confirmation"}
            or inputs.get("key") != "item-1"
            or not isinstance(inputs.get("changes"), dict)
            or not isinstance(inputs.get("baseline"), dict)):
        return reject("INPUT_SHAPE", "invalid-data")
    changes, baseline = inputs["changes"], inputs["baseline"]
    confirmed = {}
    if "confirmation" in inputs:
        evidence = host.get("confirmationEvidence")
        binding = {"target": request["target"], "operation": request["operation"],
                   "key": inputs["key"], "changes": changes, "baseline": baseline,
                   "context": host.get("context", {})}
        if (not evidence or inputs["confirmation"] != evidence["handle"]
                or evidence["binding"] != binding or not evidence.get("active", True)):
            return reject("INVALID_CONFIRMATION", "invalid-data")
        confirmed = evidence["confirmedCurrent"]
        if not set(confirmed) <= set(changes):
            return reject("INVALID_CONFIRMATION", "invalid-data")
        if not set(confirmed) <= set(host.get("readableFields", ["code", "price", "rating"])):
            return reject("UNAVAILABLE")
    update = {"current": current, "changes": changes, "baseline": baseline,
              "confirmedCurrent": confirmed}
    for name in ("exposedFields", "writableFields", "readableFields", "dependentRuleReject"):
        if name in host:
            update[name] = host[name]
    result = updates.outcome(update)
    status = result["status"]
    if status == "conflict":
        return finish("conflict", conflictCode="CONCURRENT_CHANGE", conflicts=result["conflicts"])
    if status != "accepted":
        family = {"precondition-required": "invalid-data", "definition-invalid": "invalid-data"}.get(status, status)
        return reject({"precondition-required": "PRECONDITION_REQUIRED"}.get(status, "UPDATE_REJECTED"), family)
    if host.get("commitFailure", False):
        return finish("failed", "execution-failure", "COMMIT_FAILED")
    observed.update(persisted=result["persisted"], writtenFields=result["writtenFields"],
                    effects=int(bool(result["writtenFields"])))
    return finish("success", output={"changed": bool(result["writtenFields"])})


def check(path=FILE):
    fixtures = updates.load(path)
    assert fixtures["feature"] == "ARP-SERVICES-002"
    assert fixtures["status"] == "unreleased-draft"
    ids = [case["id"] for case in fixtures["cases"]]
    assert ids and len(ids) == len(set(ids))
    for case in fixtures["cases"]:
        before = copy.deepcopy(case)
        result = invoke(case)
        assert result == case["expected"], f"{case['id']}: {result} != {case['expected']}"
        assert before == case, f"{case['id']}: mutated fixture"
        response = result["response"]
        assert all(d["family"] in FAMILIES for d in response["diagnostics"])
        if (response["status"] in {"rejected", "conflict"}
                or (response["status"] == "failed" and case["host"].get("commitFailure", False))):
            assert not result["observed"]["writtenFields"] and not result["observed"]["effects"]
    return len(ids)


if __name__ == "__main__":
    print(f"PASS: {check()} ARP-SERVICES-002 cases (STATIC ONLY; no runtime/DB)")