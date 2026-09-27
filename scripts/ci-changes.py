#!/usr/bin/env python3
"""Check committed whitespace and conservatively select the RPM build jobs."""

import json
import os
from pathlib import Path
import re
import subprocess


LIGHTWEIGHT_FILES = {
    "README.md", "CONTRIBUTING.md", "SECURITY.md", "SUPPORT.md",
    ".github/dependabot.yml", ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/workflows/watch-upstream.yml",
}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def commit(sha: str) -> str:
    if not re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", sha):
        raise ValueError(f"Expected a commit SHA, got {sha!r}")
    return git("rev-parse", "--verify", f"{sha}^{{commit}}")


def empty_tree() -> str:
    return subprocess.check_output(
        ["git", "hash-object", "-t", "tree", "--stdin"], input=b""
    ).decode().strip()


def diff_range(event_name: str, event: dict) -> tuple[str, str]:
    if event_name == "pull_request":
        pr = event["pull_request"]
        base = commit(pr["base"]["sha"])
        head = commit(pr["head"]["sha"])
        # Check only the PR's changes, excluding unrelated changes on main.
        return git("merge-base", base, head), head
    if event_name == "push" and event.get("ref", "").startswith("refs/heads/"):
        head = commit(event["after"])
        before = event["before"]
        if before and set(before) == {"0"}:
            # A newly created branch has no previous tip: inspect its full tree.
            return empty_tree(), head
        return commit(before), head
    # Tags and manual runs always build; check the selected commit's changes.
    head = git("rev-parse", "HEAD")
    parents = git("rev-list", "--parents", "-n", "1", head).split()
    if len(parents) > 1:
        return parents[1], head
    return empty_tree(), head


def requires_build(event_name: str, ref: str, paths: list[str]) -> bool:
    if event_name not in {"pull_request", "push"} or ref.startswith("refs/tags/"):
        return True
    if event_name == "push" and not ref.startswith("refs/heads/"):
        return True
    for path in paths:
        if path in LIGHTWEIGHT_FILES:
            continue
        if path.startswith("docs/") and path.endswith(".md"):
            continue
        if path.startswith("tests/") or path.startswith(".github/ISSUE_TEMPLATE/"):
            continue
        # Unknown files and all build/release scripts take the full path.
        return True
    return False


def main() -> None:
    event_name = os.environ["GITHUB_EVENT_NAME"]
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    base, head = diff_range(event_name, event)
    # A missing comparison commit fails checks rather than silently skipping CI.
    subprocess.run(["git", "diff", "--check", base, head, "--"], check=True)
    names = subprocess.check_output(
        ["git", "diff", "--no-renames", "--name-only", "-z", base, head, "--"]
    )
    # Disabling rename detection checks both old and new paths, including deletions.
    paths = names.decode("utf-8", errors="surrogateescape").split("\0")[:-1]
    full_build = requires_build(event_name, os.environ["GITHUB_REF"], paths)
    value = str(full_build).lower()
    print(f"Compared {base}..{head}: {len(paths)} changed paths; full_build={value}")
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"full_build={value}\n")


if __name__ == "__main__":
    main()
