# Raspberry Pi Imager RPM packaging

This repository packages [raspberrypi/rpi-imager](https://github.com/raspberrypi/rpi-imager) for Fedora. See [GitHub Releases](https://github.com/phattmatt/rpi-imager-rpm/releases) for available versions and `rpi-imager.spec` for the version being packaged.

## Install a release

Download the main binary RPM for your architecture from [Releases](https://github.com/phattmatt/rpi-imager-rpm/releases), then install that file with DNF so dependencies are resolved:

```bash
sudo dnf install ./path/to/downloaded-package.rpm
rpi-imager
```

Prereleases are marked on GitHub. Use a stable release unless you want to test upstream prerelease changes.

## Supported environments

| Environment | Coverage |
| --- | --- |
| Fedora 44, x86_64 | CI builds, clean installation checks, and headless startup checks; release binary target. |
| Fedora 44, aarch64 | Allowed by the spec; no CI build or published binary currently. |
| Other RPM distributions / Fedora versions | Not tested; compatible dependencies are required. |

Upstream requires Qt 6.9 or newer. CI pins Fedora 44; updates within that Fedora release still follow its package repositories.

## Build locally on Fedora

```bash
bash scripts/build-rpm.sh --install-deps
```

If dependencies are already installed, omit `--install-deps`. Source and binary packages are written to `.rpmbuild/SRPMS/` and `.rpmbuild/RPMS/`. See [CONTRIBUTING.md](CONTRIBUTING.md) for dependency setup and testing.

## Release following

- `Watch upstream releases` runs daily and proposes updates, including prereleases. Both stable and prerelease updates are reviewed and merged into `main`.
- Older versions are ignored by automatic updates. Manual downgrades require `--allow-downgrade`.
- Automated PR workflows require a maintainer to select **Approve workflows to run** before reviewing the build and installation checks. See [GitHub's workflow trigger rules](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).
- `Build RPM` checks scripts, builds packages, and tests installation in a fresh Fedora container for pull requests, pushes to `main`, manual runs, and `rpm-v*` tags.
- Release tags must be `rpm-v<upstream-version>-<rpm-release>`, without the Fedora distribution suffix. Publication validates the tag and package metadata and waits for installation checks.

Tagged releases publish only the main installable RPM. Debug and source RPMs remain workflow artifacts. Follow [the release checklist](docs/release-checklist.md) to publish.

## Updating manually

Install `python3-rpm` before running the updater, which uses RPM's own version ordering:

```bash
sudo dnf install python3-rpm
python3 scripts/update-version.py --latest --packager "Your Name <you@example.com>"
```

Use `--latest --include-prereleases` to consider prereleases, or `--version <upstream-version>` for a specific release. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Packaging notes

The spec makes small build-system changes for source archive builds:

- A prep-time helper switches bundled dependencies to system libraries instead of CMake downloads. It checks upstream markers and tolerates repeat application.
- The upstream version is provided explicitly because GitHub source archives lack `.git`.
- Upstream's timezone and country generators attempt downloads and fall back to files shipped in the source tree. Source fetching needs network access; fully offline builds have not been validated.
- Prerelease versions such as `2.0.7-rc2` become `2.0.7~rc2` in RPM metadata so the stable version sorts newer. Use the actual generated filename when installing.
- Telemetry and update checks default to enabled. Disable them at build time with:

```bash
bash scripts/build-rpm.sh -- --without telemetry --without check_version
```

## Support and contributing

- [SUPPORT.md](SUPPORT.md): packaging versus upstream issue reporting.
- [CONTRIBUTING.md](CONTRIBUTING.md): builds, checks, and updates.
- [Troubleshooting](docs/troubleshooting.md): installation and runtime checks.
- [Release checklist](docs/release-checklist.md): publishing a package.
- [Suggested labels](docs/labels.md): issue and update labels.

## License

This packaging repository is licensed under Apache License 2.0. Raspberry Pi Imager remains upstream's project and is licensed by Raspberry Pi Ltd under Apache License 2.0.
