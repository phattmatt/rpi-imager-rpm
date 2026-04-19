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
sudo dnf install dnf-plugins-core git rpm-build rpmdevtools
sudo dnf builddep ./rpi-imager.spec
bash scripts/build-rpm.sh
```

Built packages are written under `.rpmbuild/RPMS/` and `.rpmbuild/SRPMS/`.

## Smoke test an RPM

Install the freshly built binary RPM:

```bash
sudo dnf install .rpmbuild/RPMS/*/rpi-imager-*.rpm
rpm -q rpi-imager
rpm -V rpi-imager
ldd /usr/bin/rpi-imager | grep "not found" || true
```

Launch testing is best done on a normal desktop session:

```bash
rpi-imager
```

GitHub Actions uses a headless-safe smoke test because GUI startup may abort in a container.

## Update to a new upstream release

To update to a known upstream version:

```bash
python3 scripts/update-version.py --version 2.0.9 --packager "Your Name <you@example.com>"
```

To update to GitHub's latest upstream release:

```bash
python3 scripts/update-version.py --latest --packager "Your Name <you@example.com>"
```

Then build the RPM and review whether the existing patches still apply cleanly.

## Release tags

After the update is merged and the build passes, create an RPM release tag:

```bash
git tag rpm-v2.0.9-1
git push origin rpm-v2.0.9-1
```

The tag workflow publishes only the installable binary RPM to the GitHub Release. Debug and source RPMs remain available from workflow artifacts.

## Pull requests

Please include:

- What changed.
- Which Fedora or RPM-based environment was tested.
- The local build command or GitHub Actions run.
- Any dependency, patch, or release artifact changes.
