# Contributing

Thanks for helping maintain the Raspberry Pi Imager RPM packaging.

This repository should stay focused on packaging. Changes to Raspberry Pi Imager itself should usually be proposed upstream first.

## Packaging principles

- Prefer Fedora/RPM system packages over bundled dependencies.
- Keep patches small and specific to source-archive or RPM build requirements.
- Avoid carrying behavior changes that belong upstream.
- Keep release artifacts predictable: tagged releases should publish the installable binary RPM.
- Update documentation when commands, release steps, or supported environments change.

## Build locally

On a Fedora machine or VM:

```bash
bash scripts/build-rpm.sh --install-deps
```

Without installing dependencies automatically:

```bash
sudo dnf install dnf-plugins-core git python3 python3-rpm rpm-build rpmdevtools
sudo dnf builddep ./rpi-imager.spec
bash scripts/build-rpm.sh
```

Built packages are written under `.rpmbuild/RPMS/` and `.rpmbuild/SRPMS/`.

## Smoke test an RPM

Install the freshly built binary RPM. The selector rejects missing or multiple main packages; move older build outputs out of `.rpmbuild/RPMS/` if needed:

```bash
rpm_path="$(python3 scripts/select-rpm.py .rpmbuild/RPMS)"
sudo dnf install "$rpm_path"
rpm -q rpi-imager
rpm -V rpi-imager
ldd /usr/bin/rpi-imager
```

Launch testing is best done on a normal desktop session:

```bash
rpi-imager
```

Any `not found` entry in the `ldd` output is a failure.

CI installs the main package in a fresh Fedora 44 container with no build dependencies and optional dependencies disabled, verifies installed files and shared libraries, then runs the GUI offscreen with software rendering for 20 seconds. Early exit or Qt/QML loading errors fail the test. This catches startup problems but does not replace desktop and hardware checks.

Before publishing, launch on a normal desktop and verify device discovery, authentication, writing and verification using a spare SD card whose contents can be erased.

## Lightweight checks

Install `python3-rpm` and `ShellCheck`, then run:

```bash
python3 -m unittest discover -s tests -v
shellcheck scripts/*.sh
git diff --check
```

CI also runs actionlint before the RPM build.

## Update to a new upstream release

Install `python3-rpm` for RPM version comparison. To update to a known upstream version:

```bash
python3 scripts/update-version.py --version 2.0.9 --packager "Your Name <you@example.com>"
```

To update to GitHub's latest upstream release:

```bash
python3 scripts/update-version.py --latest --packager "Your Name <you@example.com>"
```

To allow prereleases while selecting the latest GitHub release:

```bash
python3 scripts/update-version.py --latest --include-prereleases --packager "Your Name <you@example.com>"
```

The daily watcher includes prereleases. Review and merge both stable and prerelease updates into `main`; GitHub Releases marks prereleases separately. For a PR created by the watcher, select **Approve workflows to run** before assessing CI results, as described in [GitHub's trigger rules](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).

Automatic updates ignore older versions. An intentional manual downgrade requires `--version <version> --allow-downgrade`; review its effect on installed systems before publishing.

Then build the RPM and review whether the existing patches still apply cleanly.

For prereleases, the updater converts upstream tags such as `2.0.7-rc2` into RPM versions such as `2.0.7~rc2` so the eventual stable release still upgrades cleanly.

## Release tags

After the update is merged and the build passes, create an RPM release tag:

```bash
git tag rpm-v2.0.9-1
git push origin rpm-v2.0.9-1
```

For prereleases, keep the Git tag in upstream-style form because Git refs cannot contain `~`:

```bash
git tag rpm-v2.0.7-rc2-1
git push origin rpm-v2.0.7-rc2-1
```

The tag must match the spec upstream version and RPM release (without `.fc44`). Publication checks the built package metadata and waits for the clean installation test. See [the release checklist](docs/release-checklist.md).

The tag workflow publishes only the installable binary RPM to the GitHub Release. Debug and source RPMs remain available from workflow artifacts.

## Pull requests

Please include:

- What changed.
- Which Fedora or RPM-based environment was tested.
- The local build command or GitHub Actions run.
- Any dependency, patch, or release artifact changes.
