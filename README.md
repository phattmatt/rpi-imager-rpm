# Raspberry Pi Imager RPM packaging

This repository packages [raspberrypi/rpi-imager](https://github.com/raspberrypi/rpi-imager) as an RPM for Fedora-style distributions.

The current spec tracks upstream `v2.0.8`. Upstream's Linux build requires Qt 6.9 or newer, so older RPM distributions may need newer Qt packages before this will build.

## Build locally on Fedora

Quick path in a fresh Fedora VM:

```bash
bash scripts/build-rpm.sh --install-deps
```

Install the build tooling and declared dependencies:

```bash
sudo dnf install dnf-plugins-core git rpm-build rpmdevtools
sudo dnf builddep ./rpi-imager.spec
```

Build the RPMs:

```bash
mkdir -p .rpmbuild/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
spectool -g -C "$PWD/.rpmbuild/SOURCES" ./rpi-imager.spec
cp -a patches/*.patch "$PWD/.rpmbuild/SOURCES/"
rpmbuild -ba ./rpi-imager.spec --define "_topdir $PWD/.rpmbuild"
```

Install the built package:

```bash
sudo dnf install .rpmbuild/RPMS/*/rpi-imager-*.rpm
```

## Release following

The repository includes two GitHub Actions workflows:

- `Watch upstream releases` runs daily and opens a pull request when Raspberry Pi publishes a new upstream release.
- `Build RPM` builds binary and source RPM artifacts for pull requests, pushes to `main`, manual runs, and tags named `rpm-v*`.

To publish the installable binary RPM on GitHub, merge the automated update PR after the build passes, then create a tag such as:

```bash
git tag rpm-v2.0.8-1
git push origin rpm-v2.0.8-1
```

Tagged releases publish only the main installable RPM, for example `rpi-imager-2.0.8-1.fc43.x86_64.rpm`. Debug and source RPMs remain available from workflow artifacts.

## Support and contributing

- Use the GitHub issue forms to report install, runtime, build, upstream-release, or packaging problems.
- See [SUPPORT.md](SUPPORT.md) for where to report packaging issues versus upstream Raspberry Pi Imager issues.
- See [CONTRIBUTING.md](CONTRIBUTING.md) for local build, smoke test, update, and release tag guidance.
- See [docs/troubleshooting.md](docs/troubleshooting.md) for common install and runtime checks.
- See [docs/release-checklist.md](docs/release-checklist.md) when publishing a new RPM release.
- See [docs/labels.md](docs/labels.md) for the suggested issue label set.

## Updating manually

To bump the spec to a specific upstream release:

```bash
python3 scripts/update-version.py --version 2.0.8 --packager "Your Name <you@example.com>"
```

To bump to GitHub's latest upstream release:

```bash
python3 scripts/update-version.py --latest --packager "Your Name <you@example.com>"
```

## Packaging notes

The RPM spec applies small build-system patches so the package can build from a GitHub source archive without network access:

- system libraries are used instead of CMake `FetchContent` downloads;
- the upstream version is provided explicitly because GitHub source archives do not include `.git`;
- generated timezone, country, and capital-city resources use the fallback files already shipped in the upstream source tree.

## License

This packaging repository is licensed under the Apache License 2.0. Raspberry Pi Imager itself remains upstream's project and is licensed by Raspberry Pi Ltd under the Apache License 2.0.
