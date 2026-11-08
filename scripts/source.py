#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Export corresponding source from an explicit allowlist, never a home/work folder."""
from pathlib import Path
import sys
import zipfile

ROOT_FILES = {
    'AppIcon.icns', 'Info.plist', 'package.json', 'package-lock.json',
    'requirements-engine.txt', 'requirements-docs.txt', 'requirements-dmg.txt',
    'LICENSE', 'LICENSE-Apache-2.0.txt', 'LICENSE-React.txt', 'NOTICE',
    'README.md', 'README.nl.md', 'CHANGELOG.md', 'CONTRIBUTING.md', 'SECURITY.md',
    'TRANSLATING.md', 'IMAGE-PROVENANCE.md', 'RELEASE-NOTES.md',
    'RELEASE-CHECKLIST.md', 'Handleiding.html', 'Handleiding.pdf',
    'User-Guide-EN.pdf', 'User-Guide-FR.pdf', 'User-Guide-DE.pdf',
    'User-Guide-ES.pdf', 'User-Guide-IT.pdf', 'User-Guide-PT.pdf',
    '.gitignore', '.gitattributes',
}
SOURCE_DIRS = {'Sources', 'engine', 'web', 'scripts', 'tests', 'licenses', 'docs', '.github'}
EXCLUDED = {'node_modules', 'dist', '__pycache__', '.git', '.pytest_cache', '.venv', '.DS_Store'}

def source_files(root):
    root = Path(root)
    for item in sorted(root.iterdir()):
        if item.name in ROOT_FILES:
            if item.is_symlink():
                raise ValueError(f'Symlink refused in source: {item.name}')
            if item.is_file():
                yield item
        elif item.name in SOURCE_DIRS:
            if item.is_symlink():
                raise ValueError(f'Symlink refused in source: {item.name}')
            for path in sorted(item.rglob('*')):
                rel = path.relative_to(root)
                if any(part in EXCLUDED for part in rel.parts):
                    continue
                if path.name.startswith('.env') or path.suffix in {'.pyc', '.pyo', '.pem', '.key', '.p12'}:
                    raise ValueError(f'Private/build file refused in source: {rel}')
                if path.is_symlink():
                    raise ValueError(f'Symlink refused in source: {rel}')
                if path.is_file():
                    yield path

def package(root, output):
    root, output = Path(root), Path(output)
    files = list(source_files(root))
    if output.resolve() in {p.resolve() for p in files}:
        raise ValueError('Write the archive outside the source allowlist')
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            info = zipfile.ZipInfo(str(Path('Tickertwister') / path.relative_to(root)))
            info.date_time = (2026, 11, 8, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100755 if path.suffix == '.sh' else 0o100644) << 16
            archive.writestr(info, path.read_bytes())
    print(f'Source archive: {output} ({len(files)} files)')

if __name__ == '__main__':
    package(Path(__file__).resolve().parents[1], sys.argv[1])
