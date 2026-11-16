import { test } from 'node:test';
import assert from 'node:assert/strict';
import { negotiate, DICTIONARY_CAPABILITIES } from '../../out-unit/remote/protocol.js';

for (const runtime of ['dotnet', 'java', 'php']) {
    const info = { runtime, demoProtocol: `arp-demo-${runtime}/1`, capabilities: [...DICTIONARY_CAPABILITIES] };
    test(`${runtime}: truthful recognized identity and capabilities`, () => {
        assert.deepEqual(negotiate(runtime, info), DICTIONARY_CAPABILITIES);
        assert.equal(negotiate(runtime, { ...info, runtime: 'other' }), undefined);
        assert.equal(negotiate(runtime, { ...info, demoProtocol: 'unrecognized/1' }), undefined);
    });
    test(`${runtime}: missing operations never become capabilities`, () => {
        assert.deepEqual(negotiate(runtime, { ...info, capabilities: ['dictionary.list', 'crud.create'] }),
            ['dictionary.list']);
        assert.deepEqual(negotiate(runtime, { ...info, capabilities: [] }), []);
        for (const capabilities of [null, 'dictionary.list', [17]]) {
            assert.equal(negotiate(runtime, { ...info, capabilities }), undefined);
        }
        assert.equal(negotiate(runtime, null), undefined);
    });
}