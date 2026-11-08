#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Validate release metadata and the files selected for public distribution."""
import json
import plistlib
import re
from pathlib import Path
from source import source_files

root = Path(__file__).resolve().parents[1]
package = json.loads((root / 'package.json').read_text())
version = package['version']
info = plistlib.loads((root / 'Info.plist').read_bytes())
assert info['CFBundleShortVersionString'] == version, 'App/package version mismatch'
assert package['license'] == 'AGPL-3.0-only', 'Unexpected project license'
assert 'GNU AFFERO GENERAL PUBLIC LICENSE' in (root / 'LICENSE').read_text()
lock = json.loads((root / 'package-lock.json').read_text())
assert lock['version'] == version and lock['packages']['']['version'] == version, 'Lockfile version mismatch'
for name in ['Handleiding.pdf'] + [f'User-Guide-{lang}.pdf' for lang in ('EN','FR','DE','ES','IT','PT')]:
    assert (root / name).read_bytes().startswith(b'%PDF-'), f'Missing/invalid guide: {name}'
for name in ('README.md','RELEASE-NOTES.md','NOTICE'):
    assert version in (root/name).read_text(), f'Missing version in {name}'
patterns = [
    re.compile(r'[/]Users/[^\s"\']+'),
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    re.compile(r'\b(?:sk-proj-|sk-svcacct-)[A-Za-z0-9_-]{24,}'),
    re.compile(r'\b(?:ghp_|github_pat_)[A-Za-z0-9_]{30,}'),
]
issues = []
files = list(source_files(root))
for path in files:
    if path.suffix.lower() in {'.pdf','.png','.icns','.jpg','.jpeg','.woff','.woff2'}:
        continue
    content = path.read_text(errors='replace')
    if any(pattern.search(content) for pattern in patterns):
        issues.append(str(path.relative_to(root)))
assert not issues, 'Review private paths or secret-like content in: ' + ', '.join(issues)
print(f'PASS: v{version}; metadata, seven guides, license, allowlist and secret-pattern scan ({len(files)} files)')
