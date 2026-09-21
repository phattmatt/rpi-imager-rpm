#!/usr/bin/env python3
"""Validate a release tag and built package before preparing publication files."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import urllib.request


def query(command: list[str]) -> str:
    return subprocess.check_output(command, text=True).strip()


def validate_tag(tag: str, upstream: str, release: str) -> None:
    expected = f'rpm-v{upstream}-{release}'
    if tag != expected:
        raise SystemExit(f'Release tag {tag!r} does not match spec: expected {expected!r}')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--tag', required=True)
    parser.add_argument('--rpm', type=Path, required=True)
    args = parser.parse_args()
    spec = Path('rpi-imager.spec')
    match = re.search(r'^%global upstream_version\s+(\S+)$', spec.read_text(), re.M)
    if not match:
        raise SystemExit('Could not find upstream_version in the spec')
    upstream = match.group(1)
    base = ['rpmspec', '-q', '--srpm']
    release = query(base + ['--define', 'dist %{nil}', '--qf', '%{RELEASE}', str(spec)])
    validate_tag(args.tag, upstream, release)
    fmt = '%{NAME}-%{VERSION}-%{RELEASE}'
    expected = query(base + ['--qf', fmt, str(spec)])
    actual = query(['rpm', '-qp', '--qf', fmt, str(args.rpm)])
    if actual != expected:
        raise SystemExit(f'Built RPM {actual!r} does not match spec {expected!r}')
    arch = query(['rpm', '-qp', '--qf', '%{ARCH}', str(args.rpm)])
    if arch not in ('x86_64', 'aarch64'):
        raise SystemExit(f'Unexpected binary architecture: {arch}')
    request = urllib.request.Request(
        f'https://api.github.com/repos/raspberrypi/rpi-imager/releases/tags/v{upstream}',
        headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'rpi-imager-rpm'})
    with urllib.request.urlopen(request, timeout=30) as response:
        metadata = json.load(response)
    if metadata.get('draft') or metadata.get('tag_name') != f'v{upstream}':
        raise SystemExit('Upstream release metadata does not match the requested release')
    prerelease = bool(metadata.get('prerelease'))
    directory = Path('release')
    directory.mkdir(exist_ok=True)
    shutil.copy2(args.rpm, directory / args.rpm.name)
    note = '> This package tracks an upstream prerelease.\n\n' if prerelease else ''
    (directory / 'notes.md').write_text(
        f'Automated RPM build for upstream tag `v{upstream}`.\n\n{note}'
        f'RPM package: `{actual}.{arch}`\n\nPublished asset: installable binary RPM only.\n')
    with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
        output.write(f'prerelease={str(prerelease).lower()}\n')
        output.write(f'release_name={args.tag}' + (' (prerelease)' if prerelease else '') + '\n')


if __name__ == '__main__':
    main()
