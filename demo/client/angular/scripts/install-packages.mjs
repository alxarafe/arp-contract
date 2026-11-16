// Install only built public APF archives; refuse lockfile or existing dependency drift.
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { writeFileSync } from 'node:fs';

const lock = readFileSync('package-lock.json', 'utf8');
const before = JSON.parse(readFileSync('node_modules/.package-lock.json', 'utf8')).packages;
const packages = [
    ['ui-runtime', '0.3.0-alpha.3'],
    ...['default', 'alternative', 'cyberpunk', 'vintage', 'high-contrast'].map(id => [
        `ui-theme-${id}`, '0.1.0-alpha.3',
    ]),
];
const archives = packages.map(([name, version]) => `/artifacts/alxarafe-${name}-${version}.tgz`);
execFileSync('npm', ['install', '--no-save', '--no-audit', '--no-fund', ...archives], { stdio: 'inherit' });
assert.equal(readFileSync('package-lock.json', 'utf8'), lock, 'Consumer lockfile changed');
const after = JSON.parse(readFileSync('node_modules/.package-lock.json', 'utf8')).packages;
for (const [path, metadata] of Object.entries(before)) {
    for (const key of ['version', 'resolved', 'integrity']) {
        assert.equal(after[path]?.[key], metadata[key], `${path}: changed ${key}`);
    }
}
for (const [name, version] of packages) {
    const path = `node_modules/@alxarafe/${name}`;
    const manifest = JSON.parse(readFileSync(`${path}/package.json`, 'utf8'));
    assert.equal(manifest.version, version);
    assert(existsSync(`${path}/${manifest.exports['.'].types}`), `${name}: missing public types`);
}
writeFileSync('/artifacts/packages.json', JSON.stringify({
    sourceCommit: process.env.AUR_SOURCE_COMMIT,
    archives: archives.map(path => ({
        path: path.split('/').at(-1),
        sha256: createHash('sha256').update(readFileSync(path)).digest('hex'),
    })),
}, null, 2));