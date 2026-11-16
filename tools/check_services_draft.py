#!/usr/bin/env python3
"""Static in-memory oracle for candidate ARP-SERVICES-001 vectors.

Not a production service engine, SQL transaction or authorization system.
"""
from __future__ import annotations

import copy
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "fixtures/services/v1/cases.json"


def load(path=FILE):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique_pairs)


def valid(field, value):
    """Only demonstration fields, not an ARP dictionary implementation."""
    if field == "rating":
        return isinstance(value, str) and value in {str(i) for i in range(11)}
    if field == "price":
        if not isinstance(value, str) or not value or value.strip() != value:
            return False
        try:
            candidate = Decimal(value)
        except InvalidOperation:
            return False
        return candidate.is_finite() and candidate >= 0
    if field == "code":
        return isinstance(value, str) and len(value) > 0
    return False


def normalize(field, value):
    """Example normalization only: numeric equality without float rounding."""
    if field in ("rating", "price") and valid(field, value):
        return Decimal(value)
    return value


def same(field, a, b):
    if a is None or b is None:
        return a is b
    return normalize(field, a) == normalize(field, b)


def outcome(case):
    current = copy.deepcopy(case["current"])
    changes = case["changes"]
    baseline = case["baseline"]
    fields = set(case.get("exposedFields", ["code", "rating", "price"]))
    writable = set(case.get("writableFields", ["code", "rating", "price"]))
    readable = set(case.get("readableFields", ["code", "rating", "price"]))
    confirmation = case.get("confirmedCurrent", {})

    if case.get("operationEnabled", True) is False or case.get("authorized", True) is False:
        return {"status": "operation-not-allowed", "persisted": current, "writtenFields": []}
    if not isinstance(changes, dict) or not isinstance(baseline, dict):
        return {"status": "definition-invalid", "persisted": current, "writtenFields": []}
    if any(field not in fields or field not in writable for field in changes):
        return {"status": "operation-not-allowed", "persisted": current, "writtenFields": []}
    if any(field not in baseline or field not in current for field in changes):
        return {"status": "precondition-required", "persisted": current, "writtenFields": []}
    if any(field not in changes for field in confirmation):
        return {"status": "definition-invalid", "persisted": current, "writtenFields": []}
    for field, value in changes.items():
        if not valid(field, value):
            return {"status": "invalid-data", "field": field, "persisted": current, "writtenFields": []}

    conflicts = []
    for field, proposed in changes.items():
        expected = confirmation.get(field, baseline[field])
        if not same(field, expected, current[field]):
            if field not in readable:
                return {"status": "operation-not-allowed", "persisted": current, "writtenFields": []}
            conflicts.append({"field": field, "original": baseline[field],
                              "actual": current[field], "proposed": proposed})
    if conflicts:
        return {"status": "conflict", "conflicts": sorted(conflicts, key=lambda x: x["field"]),
                "persisted": current, "writtenFields": []}
    if case.get("dependentRuleReject", False):
        return {"status": "invalid-data", "field": "_dependent", "persisted": current,
                "writtenFields": []}
    written = []
    for field, proposed in changes.items():
        if not same(field, proposed, current[field]):
            current[field] = proposed
            written.append(field)
    return {"status": "accepted", "persisted": current,
            "writtenFields": sorted(written)}


def check(path=FILE):
    fixtures = load(path)
    assert fixtures["feature"] == "ARP-SERVICES-001"
    assert fixtures["status"] == "unreleased-draft"
    assert fixtures["scope"] == "UPDATE-partial-field-concurrency"
    cases = fixtures["cases"]
    ids = [case["id"] for case in cases]
    assert len(ids) == len(set(ids)), "duplicated scenario id"
    for case in cases:
        before = copy.deepcopy(case)
        result = outcome(case)
        assert result == case["expected"], f"{case['id']}: {result} != {case['expected']}"
        assert case == before, f"{case['id']} mutated fixture"
    return len(cases)


if __name__ == "__main__":
    print(f"PASS: {check()} ARP-SERVICES-001 candidate cases (STATIC ONLY; no runtime/DB)")
