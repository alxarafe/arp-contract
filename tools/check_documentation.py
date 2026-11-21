#!/usr/bin/env python3
"""Offline local Markdown references and historical integrity, without remote requests."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r'(?<!!)\[[^\]]+\]\(([^\s)]+)\)')
LOCAL_GITHUB = 'https://github.com/alxarafe/arp-contract/'


def markdown_anchors(text):
    anchors = set()
    counts = {}
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith(('```', '~~~')):
            fenced = not fenced
        if fenced:
            continue
        match = re.match(r'^#{1,6}\s+(.+?)\s*#*$', line)
        if match:
            title = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', match[1])
            slug = re.sub(r'[^\w\- ]', '', title.lower()).replace(' ', '-')
            count = counts.get(slug, 0)
            counts[slug] = count + 1
            anchors.add(slug + (f'-{count}' if count else ''))
        anchors.update(re.findall(r'<a\s+(?:name|id)=["\']([^"\']+)', line))
    return anchors


def check(root=ROOT):
    errors = []
    local_links = 0
    external = set()
    paths = subprocess.check_output(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=root
    ).decode().split('\0')
    for relative in sorted(set(paths)):
        path = root / relative
        if not relative.endswith('.md') or not path.is_file():
            continue
        content = path.read_text(encoding='utf-8')
        content = re.sub(r'^```.*?^```[^\n]*', '', content, flags=re.MULTILINE | re.DOTALL)
        for target in LINK.findall(content):
            url = urlsplit(target)
            if url.scheme:
                if target.startswith(LOCAL_GITHUB):
                    # Validate repository paths at their explicit revision using local Git objects.
                    parts = url.path.split('/', 5)
                    if len(parts) == 6 and parts[3] in ('blob', 'tree'):
                        revision, name = parts[4], unquote(parts[5])
                        if revision == 'main':
                            exists = (root / name).exists()
                        else:
                            exists = subprocess.run(
                                ['git', 'cat-file', '-e', revision + ':' + name], cwd=root,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                            ).returncode == 0
                        if not exists:
                            errors.append(f'{relative}: missing repository reference {target}')
                        local_links += 1
                        continue
                external.add(target)
                continue
            if target.startswith('//'):
                external.add(target)
                continue
            destination = (path.parent / unquote(url.path)).resolve() if url.path else path
            if not destination.exists():
                errors.append(f'{relative}: missing local target {target}')
            elif url.fragment and destination.suffix == '.md':
                anchors = markdown_anchors(destination.read_text(encoding='utf-8'))
                if unquote(url.fragment) not in anchors:
                    errors.append(f'{relative}: missing Markdown fragment {target}')
            local_links += 1
    manifest = json.loads((root / 'docs/history/manifest.json').read_text(encoding='utf-8'))
    for entry in manifest['files']:
        archived = (root / entry['archivePath']).read_bytes()
        original = subprocess.check_output(
            ['git', 'show', manifest['sourceRevision'] + ':' + entry['originalPath']], cwd=root)
        for name, data in (('original', original), ('archive', archived)):
            if hashlib.sha256(data).hexdigest() != entry[name + 'Sha256']:
                errors.append(f'{entry["originalPath"]}: {name} hash mismatch')
    if errors:
        raise ValueError('\n'.join(errors))
    return {'localReferences': local_links, 'archivedDocuments': len(manifest['files']),
            'externalUrlsNotFetched': len(external)}


if __name__ == '__main__':
    print('PASS: documentation references and historical hashes', check())