# Release Checklist

Use this checklist when publishing a new RPM for an upstream Raspberry Pi Imager release.

## Release policy

- Stable and prerelease updates are reviewed and merged into `main`.
- The daily watcher considers both and ignores versions older than the spec.
- Prereleases are published as GitHub prereleases, based on upstream release metadata.
- Use the spec and GitHub Releases as version references; the README does not track a current version.

## Prepare

- Confirm the upstream release tag exists at `raspberrypi/rpi-imager`.
- Update `rpi-imager.spec` with `scripts/update-version.py`.
- If the upstream release is a prerelease, confirm the RPM version was translated into RPM prerelease form, for example `2.0.7-rc2` to `2.0.7~rc2`.
- Review whether existing patches still apply and are still needed.
- Confirm the RPM `Release` value is correct for this packaging revision.

## Build

- Approve pending workflows on automated update PRs, then wait for the GitHub Actions build (or build locally on Fedora 44 for investigation).
- Confirm source and binary RPM artifacts were produced.
- Confirm the clean Fedora 44 installation and offscreen GUI startup checks passed.
- Complete a desktop launch and a write/verify test using a spare SD card whose contents can be erased.
- Review any dependency or file list changes.
- Use RPM metadata for version checks and the actual generated filename for installation.

## Publish

- Merge the update after the build passes.
- Create and push a tag using the `rpm-v<upstream-version>-<rpm-release>` format.
- For prereleases, keep the Git tag in upstream-style form and do not use `~` in the Git ref.
- Confirm the GitHub Release contains only the installable binary RPM.
- Confirm the tag matches the spec upstream version and packaging release, without the Fedora distribution suffix; CI rejects mismatches.
- Confirm debug and source RPMs remain workflow artifacts only.

Stable example:

```bash
git switch main
git tag rpm-v2.0.10-1
git push origin rpm-v2.0.10-1
```

Prerelease example:

```bash
git switch main
git tag rpm-v2.0.11-rc1-1
git push origin rpm-v2.0.11-rc1-1
```
