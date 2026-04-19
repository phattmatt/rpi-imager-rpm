# Support

This repository maintains Fedora-style RPM packaging for Raspberry Pi Imager. It does not maintain the Raspberry Pi Imager application itself.

## Report issues here

Open an issue in this repository for:

- RPM install failures, dependency resolution errors, or file conflicts.
- RPM runtime problems that do not happen with upstream builds.
- GitHub Actions, build script, RPM spec, patch, or release artifact problems.
- Requests to package a new upstream Raspberry Pi Imager release.
- Packaging documentation fixes.

## Report issues upstream

Open an issue with upstream Raspberry Pi Imager for:

- Application features or behavior unrelated to RPM packaging.
- Imaging failures that also happen with upstream builds.
- UI bugs, translation issues, or device support problems in the application.
- Security issues in Raspberry Pi Imager itself.

Upstream project: https://github.com/raspberrypi/rpi-imager

## Useful details for reports

For install problems, include:

```bash
cat /etc/fedora-release
uname -m
sudo dnf install ./rpi-imager-*.rpm
```

For runtime problems, include:

```bash
rpm -q rpi-imager
rpm -qi rpi-imager
rpm -V rpi-imager
rpi-imager
ldd /usr/bin/rpi-imager | grep "not found" || true
```

Please paste command output as text so it can be searched and quoted.
