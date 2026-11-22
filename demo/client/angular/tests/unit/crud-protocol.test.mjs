import { test } from "node:test";
import assert from "node:assert/strict";
import { changes, metadata, parseExact, record, supportsCrud } from "../../out-unit/remote/crud-protocol.js";

const info = { runtime: "php", demoProtocol: "arp-demo-php/1", capabilities: ["crud.metadata", "crud.invoke"] };
const fields = [
    { name: "serial", label: "Serial", type: "INTEGER", nullable: false, key: true, constraints: {} },
    { name: "amount", label: "Amount", type: "DECIMAL", nullable: true, key: false, constraints: {} },
    { name: "active", label: "Active", type: "BOOLEAN", nullable: false, key: false, constraints: {} },
];
const meta = { demoProtocol: "arp-demo-php-crud/1", target: "other.target", projection: "other.public",
    fields, operations: ["LIST", "GET"], pagination: { defaultLimit: 3, maxLimit: 20, maxPage: 10 },
    update: { onConflict: "reload" }, delete: { privateEvidence: false, confirmation: "complete displayed values" } };

test("CRUD negotiates only the recognized PHP identity and both advertised capabilities", () => {
    assert.equal(supportsCrud("php", info), true);
    for (const runtime of ["java", "dotnet"]) assert.equal(supportsCrud(runtime, info), false);
    for (const value of [null, {}, { ...info, demoProtocol: "unknown" },
        { ...info, capabilities: ["crud.invoke"] }, { ...info, capabilities: ["crud.metadata"] }]) {
        assert.equal(supportsCrud("php", value), false);
    }
});

test("metadata drives arbitrary target fields and refuses unsupported preconditions and shapes", () => {
    assert.deepEqual(metadata(meta), meta);
    for (const value of [{ ...meta, fields: [...fields, fields[0]] }, { ...meta, fields: [] },
        { ...meta, pagination: { defaultLimit: 0, maxLimit: 100, maxPage: 100 } },
        { ...meta, update: { onConflict: "overwrite" } }, { ...meta, delete: { privateEvidence: true } },
        { ...meta, operations: ["SQL"] }]) assert.throws(() => metadata(value));
});

test("numeric scalar strings and decimal metadata never pass through Number", () => {
    const value = parseExact('{"integer":"18446744073709551615","decimal":"0.123456789012345678901",'
        + '"bound":18446744073709551615,"fraction":1.00000000000000000001,"limit":10,"exponent":1e127}');
    assert.deepEqual(JSON.parse(JSON.stringify(value)), { integer: "18446744073709551615", decimal: "0.123456789012345678901",
        bound: "18446744073709551615", fraction: "1.00000000000000000001", limit: 10, exponent: "1e127" });
    assert.throws(() => parseExact('{'));
});

test("records preserve exact scalar kinds and partial changes exclude keys and untouched fields", () => {
    const original = { serial: "18446744073709551615", amount: "0.123456789012345678901", active: true };
    const row = { key: { components: [] }, values: original };
    assert.deepEqual(record(row, fields), row);
    assert.throws(() => record({ ...row, values: { ...original, serial: 123 } }, fields));
    const wrongKind = parseExact('{"key":{},"values":{"serial":18446744073709551615,'
        + '"amount":"1","active":true}}');
    assert.throws(() => record(wrongKind, fields));
    assert.deepEqual(changes(fields, original, { ...original, serial: "1", amount: null }), { amount: null });
    assert.deepEqual(changes(fields, original, { ...original }), {});
});
