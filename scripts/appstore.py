#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Stage a separate sandboxed Mac App Store build from the matching desktop app."""
import argparse
import datetime
import hashlib
import os
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import tempfile
import zipfile

PROJECT = Path(__file__).resolve().parents[1]
BUNDLE = "be.bobceulemans.tickertwister.desktop"
HOST = {
    "com.apple.security.app-sandbox": True,
    "com.apple.security.network.client": True,
    "com.apple.security.files.user-selected.read-write": True,
    "com.apple.security.print": True,
}
CHILD = {"com.apple.security.app-sandbox": True, "com.apple.security.inherit": True}


def run(*args):
    subprocess.run(args, check=True)


def output(*args):
    return subprocess.check_output(args)


def profile_entitlements(path, signing, installer):
    if not signing.startswith(("Apple Distribution: ", "3rd Party Mac Developer Application: ")):
        raise ValueError("A Mac App Store application signing identity is required")
    if not installer.startswith(("3rd Party Mac Developer Installer: ", "Mac Installer Distribution: ")):
        raise ValueError("A Mac App Store installer signing identity is required")
    profile = plistlib.loads(output("security", "cms", "-D", "-i", path))
    team, = profile["TeamIdentifier"]
    prefixes = profile["ApplicationIdentifierPrefix"]
    app_id = profile["Entitlements"].get("com.apple.application-identifier")
    if app_id not in [f"{prefix}.{BUNDLE}" for prefix in prefixes]:
        raise ValueError("The profile must match the explicit desktop bundle identifier")
    if not signing.endswith(f"({team})") or not installer.endswith(f"({team})"):
        raise ValueError("Both identities must belong to the profile's team")
    if profile["ExpirationDate"] <= datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None):
        raise ValueError("The provisioning profile has expired")
    if (profile.get("ProvisionedDevices") or profile.get("ProvisionsAllDevices") or
            profile["Entitlements"].get("com.apple.security.get-task-allow")):
        raise ValueError("Select a Mac App Store distribution profile")
    lines = output("security", "find-identity", "-v", "-p", "basic").decode()
    fingerprints = {fp.upper() for fp, name in re.findall(r'([0-9a-fA-F]{40}) "([^"]+)"', lines)
                    if name == signing}
    allowed = {hashlib.sha1(cert).hexdigest().upper() for cert in profile["DeveloperCertificates"]}
    if not fingerprints.intersection(allowed) or f'"{installer}"' not in lines:
        raise ValueError("Install the matching application and installer certificates with their private keys")
    return {"com.apple.application-identifier": app_id, "com.apple.developer.team-identifier": team}


def build_helper(python, tmp, identity, identifier):
    engine = PROJECT / "engine"
    run(python, "-c", """
from importlib.metadata import version
from pathlib import Path
import sys
if sys.version_info[:2] != (3, 14):
    raise SystemExit('The packaged engine requires Python 3.14')
for line in Path(sys.argv[1]).read_text().splitlines():
    if line and not line.startswith('#'):
        name, expected = line.split('==')
        if version(name) != expected:
            raise SystemExit(f'Build dependency mismatch for {name}')
""", PROJECT / "requirements-engine.txt")
    run(python, "-m", "PyInstaller", "--noconfirm", "--onedir", "--windowed", "--name", "YahooEngine",
        "--osx-bundle-identifier", identifier + ".engine", "--distpath", tmp / "dist",
        "--workpath", tmp / "work", "--specpath", tmp, "--add-data", f"{engine}/labels.json:.",
        "--collect-all", "curl_cffi", "--collect-all", "yfinance", "--copy-metadata", "yfinance",
        *([] if identity == "-" else ["--codesign-identity", identity]), engine / "engine.py")
    return tmp / "dist/YahooEngine.app"


def sign(target, identity, tmp, entitlements=None):
    args = ["codesign", "--force", "--sign", identity]
    if identity != "-":
        args += ["--options", "runtime"]
    if entitlements:
        path = tmp / "signing-entitlements.plist"
        path.write_bytes(plistlib.dumps(entitlements))
        args += ["--entitlements", path]
    run(*args, target)


def stage(base, helper, app, tmp, args, entitlements):
    run("ditto", "--norsrc", "--noextattr", "--noqtn", base, app)
    contents = app / "Contents"
    old = contents / "Resources/Engine"
    shutil.rmtree(old)
    old.mkdir()
    helpers = contents / "Helpers"
    helpers.mkdir(exist_ok=True)
    nested = helpers / "YahooEngine.app"
    run("ditto", "--norsrc", "--noextattr", "--noqtn", helper, nested)
    (old / "YahooEngine").symlink_to("../../Helpers/YahooEngine.app/Contents/MacOS/YahooEngine")
    if not (old / "YahooEngine").is_file():
        raise ValueError("The host's engine entry point is missing")
    info_path = contents / "Info.plist"
    info = plistlib.loads(info_path.read_bytes())
    if info["CFBundleIdentifier"] != BUNDLE:
        raise ValueError("The input is not the desktop application")
    info["LSApplicationCategoryType"] = "public.app-category.finance"
    if args.sandbox_test:
        info["CFBundleIdentifier"] += ".sandboxtest"
        info["CFBundleDisplayName"] += " Sandbox Test"
        info.pop("CFBundleDocumentTypes", None)
        info.pop("UTExportedTypeDeclarations", None)
    else:
        shutil.copyfile(args.profile, contents / "embedded.provisionprofile")
    info_path.write_bytes(plistlib.dumps(info))
    nested_info_path = nested / "Contents/Info.plist"
    nested_info = plistlib.loads(nested_info_path.read_bytes())
    nested_info.update(LSBackgroundOnly=True, CFBundleIdentifier=info["CFBundleIdentifier"] + ".engine",
                       CFBundleVersion=info["CFBundleVersion"],
                       CFBundleShortVersionString=info["CFBundleShortVersionString"])
    nested_info_path.write_bytes(plistlib.dumps(nested_info))
    for framework in sorted((p for p in nested.rglob("*.framework") if not p.is_symlink()),
                            key=lambda p: len(p.parts), reverse=True):
        sign(framework, args.identity, tmp)
    sign(nested, args.identity, tmp, CHILD)
    sign(app, args.identity, tmp, entitlements)
    run("codesign", "--verify", "--deep", "--strict", app)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, required=True, help="desktop app built from the current checkout")
    parser.add_argument("--python", type=Path, required=True, help="Python 3.14 venv with requirements-engine.txt")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--identity")
    parser.add_argument("--installer")
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--sandbox-test", action="store_true", help="local ad-hoc .app with a separate identifier")
    args = parser.parse_args()
    if args.sandbox_test:
        if args.identity or args.installer or args.profile or args.output.suffix != ".app":
            parser.error("--sandbox-test creates a local .app without signing credentials")
        args.identity = "-"
        entitlements = HOST
    else:
        if not all((args.identity, args.installer, args.profile)) or args.output.suffix != ".pkg":
            parser.error("distribution needs --identity, --installer, --profile and a new .pkg path")
        entitlements = HOST | profile_entitlements(args.profile, args.identity, args.installer)

    run("codesign", "--verify", "--deep", "--strict", args.app)
    with zipfile.ZipFile(args.app / "Contents/Resources/Source/Tickertwister-source.zip") as source:
        paths = [PROJECT / "requirements-engine.txt", PROJECT / "Info.plist"]
        paths.extend(p for p in (PROJECT / "engine").rglob("*") if p.suffix in {".py", ".json"})
        for path in paths:
            if source.read("Tickertwister/" + str(path.relative_to(PROJECT))) != path.read_bytes():
                raise ValueError(f"Rebuild the desktop app from this checkout before packaging ({path.name})")
    dest = args.output.absolute()
    if os.path.lexists(dest):
        raise FileExistsError(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=dest.parent) as work:
        tmp = Path(work)
        identifier = BUNDLE + (".sandboxtest" if args.sandbox_test else "")
        helper = build_helper(args.python, tmp, args.identity, identifier)
        app = tmp / "Tickertwister Desktop.app"
        stage(args.app, helper, app, tmp, args, entitlements)
        if args.sandbox_test:
            app.rename(dest)
        else:
            package = tmp / "Tickertwister Desktop.pkg"
            run("productbuild", "--component", app, "/Applications", "--sign", args.installer, package)
            run("pkgutil", "--check-signature", package)
            os.link(package, dest)
    print(dest)


if __name__ == "__main__":
    main()
