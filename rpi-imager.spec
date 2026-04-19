%bcond_without telemetry
%bcond_without check_version

%if %{with telemetry}
%global telemetry_cmake ON
%else
%global telemetry_cmake OFF
%endif

%if %{with check_version}
%global check_version_cmake ON
%else
%global check_version_cmake OFF
%endif

%global udevrulesdir %{_prefix}/lib/udev/rules.d

Name:           rpi-imager
Version:        2.0.8
Release:        1%{?dist}
Summary:        Raspberry Pi Imaging utility

License:        Apache-2.0
URL:            https://github.com/raspberrypi/rpi-imager
Source0:        %{url}/archive/refs/tags/v%{version}/%{name}-%{version}.tar.gz

Patch0:         0001-use-system-libraries-for-rpm-builds.patch
Patch1:         0002-allow-version-override-for-archive-builds.patch
Patch2:         0003-use-bundled-resource-fallbacks-for-offline-builds.patch

ExclusiveArch:  x86_64 aarch64

BuildRequires:  cmake >= 3.22
BuildRequires:  desktop-file-utils
BuildRequires:  gcc-c++
BuildRequires:  git-core
BuildRequires:  libappstream-glib
BuildRequires:  libxml2
BuildRequires:  make
BuildRequires:  ninja-build
BuildRequires:  pkgconfig
BuildRequires:  shared-mime-info

BuildRequires:  cmake(Qt6Core) >= 6.9
BuildRequires:  cmake(Qt6DBus) >= 6.9
BuildRequires:  cmake(Qt6Gui) >= 6.9
BuildRequires:  cmake(Qt6LinguistTools) >= 6.9
BuildRequires:  cmake(Qt6Network) >= 6.9
BuildRequires:  cmake(Qt6Quick) >= 6.9
BuildRequires:  cmake(Qt6Svg) >= 6.9

BuildRequires:  /usr/bin/lsblk
BuildRequires:  pkgconfig(gnutls)
BuildRequires:  pkgconfig(libarchive)
BuildRequires:  pkgconfig(libcurl)
BuildRequires:  pkgconfig(libdrm)
BuildRequires:  pkgconfig(libidn2)
BuildRequires:  pkgconfig(liblzma)
BuildRequires:  pkgconfig(libnghttp2)
BuildRequires:  pkgconfig(libusb-1.0)
BuildRequires:  pkgconfig(libudev)
BuildRequires:  pkgconfig(liburing)
BuildRequires:  pkgconfig(libzstd)
BuildRequires:  pkgconfig(nettle)
BuildRequires:  pkgconfig(zlib)

Requires:       /usr/bin/lsblk
Requires:       /usr/bin/pkexec
Requires:       /usr/sbin/fdisk
Requires:       /usr/sbin/mkfs.vfat
Requires:       hicolor-icon-theme
Requires:       shared-mime-info
Recommends:     udisks2

%description
Raspberry Pi Imager is a user-friendly tool for creating bootable media for
Raspberry Pi devices.

%prep
%autosetup -n %{name}-%{version} -p1

%build
export RPM_USE_SYSTEM_LIBS=1
export IMAGER_VERSION_OVERRIDE=v%{version}
export IMAGER_OFFLINE_BUILD=1

%cmake src \
    -DBUILD_TESTING=OFF \
    -DENABLE_CHECK_VERSION=%{check_version_cmake} \
    -DENABLE_TELEMETRY=%{telemetry_cmake} \
    -DFETCHCONTENT_FULLY_DISCONNECTED=ON

%cmake_build

%install
%cmake_install
install -Dpm 0644 debian/com.raspberrypi.rpi-imager.policy \
    %{buildroot}%{_datadir}/polkit-1/actions/com.raspberrypi.rpi-imager.policy
install -Dpm 0644 debian/com.raspberrypi.rpi-imager-manifest.xml \
    %{buildroot}%{_datadir}/mime/packages/com.raspberrypi.rpi-imager-manifest.xml
install -Dpm 0644 doc/man/rpi-imager.1 \
    %{buildroot}%{_mandir}/man1/rpi-imager.1
install -Dpm 0644 src/linux/99-rpiboot.rules \
    %{buildroot}%{udevrulesdir}/99-rpiboot.rules

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/com.raspberrypi.rpi-imager.desktop
appstream-util validate-relax --nonet %{buildroot}%{_metainfodir}/com.raspberrypi.rpi-imager.metainfo.xml
xmllint --noout %{buildroot}%{_datadir}/mime/packages/com.raspberrypi.rpi-imager-manifest.xml
xmllint --noout %{buildroot}%{_datadir}/polkit-1/actions/com.raspberrypi.rpi-imager.policy

%files
%license license.txt
%doc CONTRIBUTING.md README.md
%{_bindir}/rpi-imager
%{_datadir}/applications/com.raspberrypi.rpi-imager.desktop
%{_datadir}/icons/hicolor/scalable/apps/rpi-imager.svg
%{_metainfodir}/com.raspberrypi.rpi-imager.metainfo.xml
%{_datadir}/mime/packages/com.raspberrypi.rpi-imager-manifest.xml
%{_datadir}/polkit-1/actions/com.raspberrypi.rpi-imager.policy
%{_mandir}/man1/rpi-imager.1*
%{udevrulesdir}/99-rpiboot.rules

%changelog
* Sun Apr 19 2026 rpi-imager-rpm maintainers <packagers@example.invalid> - 2.0.8-1
- Initial RPM package for upstream 2.0.8.
- Ship upstream Polkit policy, MIME registration, man page, and rpiboot udev rules.
