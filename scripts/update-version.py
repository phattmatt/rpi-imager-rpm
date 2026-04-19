#!/usr/bin/env python3
"""Update rpi-imager.spec to a requested or latest upstream release."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "rpi-imager.spec"
LATEST_RELEASE_URL = "https://api.github.com/repos/raspberrypi/rpi-imager/releases/latest"


def github_output(name: str, value: str) -> None:
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write(f"{name}={value}\n")


def normalize_version(value: str) -> str:
    value = value.strip()
    if value.startswith("v"):
        value = value[1:]
    if not re.match(r"^[0-9]+(\.[0-9]+)+([~._+][A-Za-z0-9]+)?$", value):
        raise SystemExit(f"Unsupported upstream version for RPM Version: {value!r}")
    return value


def latest_version() -> str:
    request = urllib.request.Request(
        LATEST_RELEASE_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "rpi-imager-rpm-update-script",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    tag = data.get("tag_name")
    if not tag:
        raise SystemExit("GitHub release response did not include tag_name")
    return normalize_version(tag)


def spec_version(text: str) -> str:
    match = re.search(r"^Version:\s*(\S+)\s*$", text, flags=re.MULTILINE)
    if not match:
        raise SystemExit("Could not find Version in rpi-imager.spec")
    return match.group(1)


def changelog_date() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%a %b %d %Y")


def update_spec(version: str, packager: str) -> bool:
    text = SPEC.read_text(encoding="utf-8")
    current = spec_version(text)
    github_output("current", current)
    github_output("version", version)

    if current == version:
        print(f"rpi-imager.spec already targets {version}")
        return False

    text = re.sub(
        r"^Version:\s*\S+\s*$",
        f"Version:        {version}",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"^Release:\s*\S+\s*$",
        "Release:        1%{?dist}",
        text,
        count=1,
        flags=re.MULTILINE,
    )

    entry = (
        f"* {changelog_date()} {packager} - {version}-1\n"
        f"- Update to upstream {version}.\n"
    )
    text = text.replace("%changelog\n", f"%changelog\n{entry}", 1)
    SPEC.write_text(text, encoding="utf-8")
    print(f"Updated rpi-imager.spec from {current} to {version}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--version", help="Upstream version, with or without leading v")
    source.add_argument("--latest", action="store_true", help="Use GitHub's latest release")
    parser.add_argument(
        "--packager",
        default=os.environ.get("RPM_PACKAGER", "rpi-imager-rpm maintainers <packagers@example.invalid>"),
        help="Packager identity for the RPM changelog",
    )
    args = parser.parse_args()

    version = latest_version() if args.latest else normalize_version(args.version)
    update_spec(version, args.packager)
    return 0


if __name__ == "__main__":
    sys.exit(main())
