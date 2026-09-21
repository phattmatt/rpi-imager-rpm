#!/usr/bin/env bash
set -euo pipefail

# Run as root in a fresh Fedora container, with only the RPM tooling installed.
rpm_path="$(python3 scripts/select-rpm.py "${1:?Usage: smoke-test-rpm.sh RPM-directory}")"
# Check required dependencies without optional desktop/hardware services.
dnf -y --setopt=install_weak_deps=False install "$rpm_path"
rpm -q rpi-imager
rpm -V rpi-imager
test -x /usr/bin/rpi-imager
for path in applications/com.raspberrypi.rpi-imager.desktop \
    metainfo/com.raspberrypi.rpi-imager.metainfo.xml \
    polkit-1/actions/com.raspberrypi.rpi-imager.policy; do
    test -f "/usr/share/$path"
done
ldd /usr/bin/rpi-imager | tee /tmp/rpi-imager-ldd.txt
if grep -q 'not found' /tmp/rpi-imager-ldd.txt; then
    exit 1
fi

# Load Qt/QML without a display or access to imaging hardware.
export QT_QPA_PLATFORM=offscreen
export QT_QUICK_BACKEND=software
export XDG_RUNTIME_DIR
XDG_RUNTIME_DIR="$(mktemp -d)"
trap 'rm -rf "$XDG_RUNTIME_DIR"' EXIT
status=0
timeout --kill-after=5s 20s /usr/bin/rpi-imager > /tmp/rpi-imager-startup.log 2>&1 || status=$?
cat /tmp/rpi-imager-startup.log
# A healthy GUI remains running until timeout terminates it.
[[ "$status" -eq 124 ]]
if grep -Eiq 'failed to load component|is not installed|is not a type|cannot load library|error while loading shared libraries' /tmp/rpi-imager-startup.log; then
    exit 1
fi
