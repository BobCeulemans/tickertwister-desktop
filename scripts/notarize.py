#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Developer ID preflight and fail-closed app/DMG notarization on macOS.

Credentials are read by notarytool from a named Keychain profile, never by Python.
The output DMG is created only after both Apple acceptance and local validation.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MACH_MAGICS = {bytes.fromhex(v) for v in (
    'feedface', 'feedfacf', 'cefaedfe', 'cffaedfe', 'cafebabe', 'bebafeca',
    'cafebabf', 'bfbafeca')}


def run(args):
    return subprocess.run([str(a) for a in args], check=True, capture_output=True,
                          text=True).stdout


def check_identity(identity):
    if not identity.startswith('Developer ID Application: '):
        raise ValueError('Use the full Developer ID Application certificate name, including Team ID.')
    identities = run(['/usr/bin/security', 'find-identity', '-v', '-p', 'codesigning'])
    if '"' + identity + '"' not in identities:
        raise ValueError('No valid Developer ID Application identity/private key found in Keychain.')


def signature(path):
    result = subprocess.run(['/usr/bin/codesign', '-d', '--verbose=4', str(path)],
                            check=True, capture_output=True, text=True)
    return result.stdout + result.stderr


def signature_team(metadata):
    team = re.search(r'^TeamIdentifier=([A-Z0-9]+)$', metadata, re.M)
    if not team or 'Authority=Developer ID Application: ' not in metadata or not re.search(r'^Timestamp=', metadata, re.M):
        raise ValueError('Developer ID Application signature, Team ID and secure timestamp required.')
    return team.group(1)


def check_app(app):
    if not app.is_dir() or app.suffix != '.app':
        raise ValueError('Expected an existing .app bundle.')
    run(['/usr/bin/codesign', '--verify', '--deep', '--strict', app])
    outer = signature(app)
    team = signature_team(outer)
    if 'runtime' not in outer:
        raise ValueError('The main app must enable hardened runtime.')
    count = 0
    # Include every embedded Python extension, dylib and executable, not just
    # the Swift host. Skip aliases so their targets are verified only once.
    for path in app.rglob('*'):
        if path.is_symlink() or not path.is_file():
            continue
        with path.open('rb') as stream:
            magic = stream.read(4)
        if magic not in MACH_MAGICS:
            continue
        metadata = signature(path)
        if signature_team(metadata) != team:
            raise ValueError(f'Embedded code signed by a different team: {path.name}')
        if 'runtime' not in metadata:
            raise ValueError(f'Hardened runtime missing: {path.name}')
        run(['/usr/bin/codesign', '--verify', '--strict', path])
        count += 1
    if count < 2:
        raise ValueError('Expected the native host and bundled Python engine.')
    print(f'PASS: Developer ID preflight; {count} Mach-O files; team {team}. Not yet notarized.', flush=True)
    return team


def submit(path, profile, logs, name, staple_target=None):
    # A timeout/error never starts a second submission. The JSON/log records
    # allow the maintainer to inspect the original job with notarytool info/log.
    result = subprocess.run(['xcrun', 'notarytool', 'submit', str(path),
        '--keychain-profile', profile, '--wait', '--timeout', '30m', '--output-format', 'json'],
        capture_output=True, text=True)
    (logs / (name + '-submission.json')).write_text(result.stdout)
    (logs / (name + '-stderr.txt')).write_text(result.stderr)
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f'Notary service returned no JSON result. Inspect {logs}.')
    if data.get('id'):
        log = subprocess.run(['xcrun', 'notarytool', 'log', data['id'],
            '--keychain-profile', profile], capture_output=True, text=True)
        (logs / (name + '-apple-log.json')).write_text(log.stdout or log.stderr)
    if result.returncode or data.get('status') != 'Accepted':
        raise RuntimeError(f'Apple did not accept {name}: {data.get("status", "unknown")}. Inspect {logs}; no automatic retry.')
    target = staple_target or path
    run(['xcrun', 'stapler', 'staple', target])
    run(['xcrun', 'stapler', 'validate', target])


def notarize(app, output, identity, profile, dmg_python):
    check_identity(identity)
    team = check_app(app)
    if not identity.endswith('(' + team + ')'):
        raise ValueError('The app and DMG signing identity must have the same Team ID.')
    if output.exists():
        raise ValueError('Refusing to replace an existing release DMG.')
    if output.suffix != '.dmg':
        raise ValueError('Output filename must end with .dmg.')
    output.parent.mkdir(parents=True, exist_ok=True)
    logs = output.parent / (output.stem + '-notary-logs')
    logs.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory(prefix='tickertwister-notary-') as temp:
        temp = Path(temp)
        # Do not modify the developer build or any installed app.
        staged_app = temp / app.name
        run(['/usr/bin/ditto', app, staged_app])
        archive = temp / 'app.zip'
        run(['/usr/bin/ditto', '-c', '-k', '--keepParent', staged_app, archive])
        # ZIPs cannot be stapled: submit the ZIP, then staple its .app.
        submit(archive, profile, logs, 'app', staple_target=staged_app)
        dmg = temp / 'release.dmg'
        run(['/bin/bash', ROOT / 'scripts/package-dmg.sh', staged_app, dmg, dmg_python])
        run(['/usr/bin/codesign', '--force', '--timestamp', '--sign', identity, dmg])
        submit(dmg, profile, logs, 'dmg')
        run(['/usr/bin/codesign', '--verify', '--strict', dmg])
        run(['/usr/sbin/spctl', '--assess', '--type', 'execute', '--verbose=2', staged_app])
        run(['/usr/sbin/spctl', '--assess', '--type', 'open', '--context', 'context:primary-signature', '--verbose=2', dmg])
        run(['/usr/bin/ditto', dmg, output])
    print(f'Accepted, stapled and verified: {output}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-identity')
    parser.add_argument('--check-app', type=Path)
    parser.add_argument('--app', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--identity', default=os.environ.get('DEVELOPER_ID_APPLICATION'))
    parser.add_argument('--keychain-profile')
    parser.add_argument('--dmg-python', default='python3')
    args = parser.parse_args()
    if args.check_identity:
        check_identity(args.check_identity)
        print('PASS: Developer ID Application identity available.')
    elif args.check_app:
        check_app(args.check_app.resolve())
    else:
        if not all((args.app, args.output, args.identity, args.keychain_profile)):
            parser.error('--app, --output, --identity (or DEVELOPER_ID_APPLICATION) and --keychain-profile are required')
        notarize(args.app.resolve(), args.output.resolve(), args.identity,
                 args.keychain_profile, args.dmg_python)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error))
