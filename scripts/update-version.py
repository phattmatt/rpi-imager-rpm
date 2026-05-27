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
RELEASES_URL = "https://api.github.com/repos/raspberrypi/rpi-imager/releases"


def github_output(name: str, value: str) -> None:
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write(f"{name}={value}\n")


def github_api_json(url: str) -> object:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "rpi-imager-rpm-update-script",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def normalize_upstream_version(value: str) -> str:
    value = value.strip()
    if value.startswith("v"):
        value = value[1:]
    if not re.match(r"^[0-9]+(\.[0-9]+)+([-._+][A-Za-z0-9][A-Za-z0-9._+-]*)?$", value):
        raise SystemExit(f"Unsupported upstream version: {value!r}")
    return value


def rpm_version_from_upstream(upstream_version: str) -> str:
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)+)(?:([-._+].+))?", upstream_version)
    if not match:
        raise SystemExit(f"Unsupported upstream version for RPM Version: {upstream_version!r}")

    base = match.group(1)
    suffix = match.group(2)
    if not suffix:
        return base

    suffix = suffix.lstrip("-._+")
    suffix = re.sub(r"[^A-Za-z0-9._+]+", ".", suffix)
    suffix = re.sub(r"\.+", ".", suffix).strip(".")
    if not suffix or not re.match(r"^[A-Za-z0-9][A-Za-z0-9._+]*$", suffix):
        raise SystemExit(f"Unsupported prerelease suffix for RPM Version: {upstream_version!r}")

    return f"{base}~{suffix}"


def branch_version_from_upstream(upstream_version: str) -> str:
    safe = re.sub(r"[~^:\?\*\[\\\s]", "-", upstream_version)
    safe = safe.replace("..", ".")
    safe = safe.strip("./")
    if not safe or safe.endswith(".lock"):
        raise SystemExit(f"Unsupported branch-safe version derived from upstream version: {upstream_version!r}")
    return safe


def latest_release(include_prereleases: bool) -> tuple[str, bool]:
    if include_prereleases:
        releases = github_api_json(RELEASES_URL)
        if not isinstance(releases, list):
            raise SystemExit("GitHub releases response was not a list")
        for release in releases:
            if release.get("draft"):
                continue
            tag = release.get("tag_name")
            if not tag:
                continue
            return normalize_upstream_version(tag), bool(release.get("prerelease"))
        raise SystemExit("GitHub releases response did not include a usable release")

    data = github_api_json(LATEST_RELEASE_URL)
    if not isinstance(data, dict):
        raise SystemExit("GitHub latest release response was not an object")
    tag = data.get("tag_name")
    if not tag:
        raise SystemExit("GitHub release response did not include tag_name")
    return normalize_upstream_version(tag), bool(data.get("prerelease"))


def spec_version(text: str) -> str:
    match = re.search(r"^Version:\s*(\S+)\s*$", text, flags=re.MULTILINE)
    if not match:
        raise SystemExit("Could not find Version in rpi-imager.spec")
    return match.group(1)


def spec_upstream_version(text: str) -> str:
    match = re.search(r"^%global upstream_version\s+(\S+)\s*$", text, flags=re.MULTILINE)
    if match:
        return match.group(1)
    return spec_version(text)


def changelog_date() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%a %b %d %Y")


def update_spec(upstream_version: str, packager: str, prerelease: bool) -> bool:
    text = SPEC.read_text(encoding="utf-8")
    current = spec_version(text)
    current_upstream = spec_upstream_version(text)
    rpm_version = rpm_version_from_upstream(upstream_version)
    upstream_tag = f"v{upstream_version}"
    branch_version = branch_version_from_upstream(upstream_version)

    github_output("current", current)
    github_output("current_upstream", current_upstream)
    github_output("version", rpm_version)
    github_output("upstream_version", upstream_version)
    github_output("upstream_tag", upstream_tag)
    github_output("branch_version", branch_version)
    github_output("prerelease", "true" if prerelease else "false")

    if current == rpm_version and current_upstream == upstream_version:
        print(f"rpi-imager.spec already targets {upstream_version}")
        return False

    if re.search(r"^%global upstream_version\s+\S+\s*$", text, flags=re.MULTILINE):
        text = re.sub(
            r"^%global upstream_version\s+\S+\s*$",
            f"%global upstream_version {upstream_version}",
            text,
            count=1,
            flags=re.MULTILINE,
        )
    else:
        text = text.replace("Name:           rpi-imager\n", f"%global upstream_version {upstream_version}\nName:           rpi-imager\n", 1)

    text = re.sub(
        r"^Version:\s*\S+\s*$",
        f"Version:        {rpm_version}",
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
        f"* {changelog_date()} {packager} - {rpm_version}-1\n"
        f"- Update to upstream {upstream_version}.\n"
    )
    text = text.replace("%changelog\n", f"%changelog\n{entry}", 1)
    SPEC.write_text(text, encoding="utf-8")
    print(f"Updated rpi-imager.spec from {current_upstream} ({current}) to {upstream_version} ({rpm_version})")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--version", help="Upstream version, with or without leading v")
    source.add_argument("--latest", action="store_true", help="Use GitHub's latest release")
    parser.add_argument(
        "--include-prereleases",
        action="store_true",
        help="When used with --latest, consider upstream prereleases as well as stable releases.",
    )
    parser.add_argument(
        "--packager",
        default=os.environ.get("RPM_PACKAGER", "rpi-imager-rpm maintainers <packagers@example.invalid>"),
        help="Packager identity for the RPM changelog",
    )
    args = parser.parse_args()

    if args.include_prereleases and not args.latest:
        parser.error("--include-prereleases requires --latest")

    if args.latest:
        upstream_version, prerelease = latest_release(args.include_prereleases)
    else:
        upstream_version = normalize_upstream_version(args.version)
        prerelease = rpm_version_from_upstream(upstream_version) != upstream_version

    update_spec(upstream_version, args.packager, prerelease)
    return 0


if __name__ == "__main__":
    sys.exit(main())
