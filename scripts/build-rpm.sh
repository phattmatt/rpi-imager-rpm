#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: bash scripts/build-rpm.sh [--install-deps]

Build source and binary RPMs in .rpmbuild/.

Options:
  --install-deps  Install Fedora build tooling and BuildRequires with dnf first.
EOF
}

install_deps=0
if [[ "${1:-}" == "--install-deps" ]]; then
    install_deps=1
elif [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    usage
    exit 0
elif [[ $# -gt 0 ]]; then
    usage >&2
    exit 2
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "${script_dir}/.." && pwd)"
topdir="${repo_root}/.rpmbuild"

if [[ "${install_deps}" -eq 1 ]]; then
    sudo dnf -y install dnf-plugins-core git rpm-build rpmdevtools
    sudo dnf -y builddep "${repo_root}/rpi-imager.spec"
fi

mkdir -p \
    "${topdir}/BUILD" \
    "${topdir}/BUILDROOT" \
    "${topdir}/RPMS" \
    "${topdir}/SOURCES" \
    "${topdir}/SPECS" \
    "${topdir}/SRPMS"

spectool -g -C "${topdir}/SOURCES" "${repo_root}/rpi-imager.spec"
rm -f "${topdir}/SOURCES/"*.patch
cp -a "${repo_root}/patches/"*.patch "${topdir}/SOURCES/"

rpmbuild -ba "${repo_root}/rpi-imager.spec" --define "_topdir ${topdir}"

cat <<EOF

Built RPMs:
  ${topdir}/RPMS/
  ${topdir}/SRPMS/
EOF
