# Troubleshooting

This guide covers problems that are specific to the RPM package. If the same problem happens with upstream Raspberry Pi Imager, report it upstream instead.

## Installation fails with missing dependencies

Install the RPM with `dnf`, not plain `rpm`, so dependencies can be resolved:

```bash
sudo dnf install ./rpi-imager-2.0.8-1.fc43.x86_64.rpm
```

If `dnf` says a required file or package is missing, collect:

```bash
cat /etc/fedora-release
uname -m
dnf repolist
sudo dnf install ./rpi-imager-*.rpm
```

Then open an install problem issue and paste the full output.

## The application does not launch

Start Raspberry Pi Imager from a terminal:

```bash
rpi-imager
```

Check the installed package and shared library links:

```bash
rpm -q rpi-imager
rpm -V rpi-imager
ldd /usr/bin/rpi-imager | grep "not found" || true
```

If any library is shown as `not found`, open a runtime issue and include the output.

## Permission prompts or device access do not work

The RPM installs upstream Polkit policy and rpiboot udev rules. Verify that those files exist:

```bash
rpm -ql rpi-imager | grep -E 'polkit|udev'
```

After installing or updating udev rules, unplug and reconnect the target device. A reboot can also help confirm the current session has picked up policy and udev changes.

## The package appears to be damaged

Use RPM verification:

```bash
rpm -V rpi-imager
```

No output means the installed files match RPM metadata. Any output may indicate local file changes, missing files, or permission changes.

## Reinstall cleanly

```bash
sudo dnf remove rpi-imager
sudo dnf install ./rpi-imager-*.rpm
```

If reinstalling changes the behavior, include both the original and reinstall output in the issue.

## Build fails locally

Start with the helper script on a Fedora VM:

```bash
bash scripts/build-rpm.sh --install-deps
```

If the failure continues, open a build problem issue and include:

- Fedora version and architecture.
- Upstream rpi-imager version.
- The command you ran.
- The first real compiler, CMake, dependency, or rpmbuild error.
