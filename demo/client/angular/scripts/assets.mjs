// Copy original bytes, never decode/re-encode numeric fixture metadata in JavaScript.
import { copyFile, mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const root = process.env.ARP_CONTRACT_PATH ?? resolve('../../..');
const sources = [
    'fixtures/dictionary/v1/catalog.json',
    'fixtures/dictionary/v1/values.json',
    'fixtures/dictionary/v1/definitions.json',
    'fixtures/dictionary/v1/catalogs.json',
    'docs/features/arp-res-001-borrador-especificacion.md',
    'examples/demo/cds/logical.yaml',
    'examples/demo/cds/public.yaml',
    'examples/demo/cds/summary.yaml',
    'fixtures/cds/v1/manifest.json',
    'fixtures/cds/v1/historical-updates.json',
    'fixtures/services/v1/cases.json',
    'fixtures/services/v1/invocation-cases.json',
];
for (const source of sources) {
    const destination = resolve('public/contract', source);
    await mkdir(resolve(destination, '..'), { recursive: true });
    await copyFile(resolve(root, source), destination);
}
await copyFile('config/instances.json', 'public/instances.json');
const revision = process.env.ARP_CONTRACT_REVISION ?? 'working-tree';
await writeFile('public/revision.txt', revision);
// Config is demo-only; refuse a typo that would silently omit a runtime.
const instances = JSON.parse(await readFile('config/instances.json', 'utf8'));
if (Object.keys(instances).sort().join(',') !== 'dotnet,java,php'
    || Object.values(instances).some(value => typeof value !== 'string')) {
    throw new Error('instances.json must contain dotnet, java and php URL strings');
}