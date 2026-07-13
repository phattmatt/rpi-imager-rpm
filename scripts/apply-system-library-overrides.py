#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path


INSERTIONS = {
    "src/dependencies/curl.cmake": (
        "# Bundled libcurl\n",
        """if(DEFINED ENV{RPM_USE_SYSTEM_LIBS})
    find_package(CURL REQUIRED)
    set(CURL_FOUND TRUE CACHE BOOL "" FORCE)
    set(CURL_LIBRARIES CURL::libcurl CACHE STRING "" FORCE)
    set(CURL_INCLUDE_DIR ${CURL_INCLUDE_DIRS} CACHE STRING "" FORCE)
    return()
endif()
""",
    ),
    "src/dependencies/libarchive.cmake": (
        "# Bundled libarchive configured for static zlib and zstd\n",
        """if(DEFINED ENV{RPM_USE_SYSTEM_LIBS})
    find_package(LibArchive REQUIRED)
    if(TARGET LibArchive::LibArchive)
        set(LibArchive_LIBRARIES LibArchive::LibArchive CACHE STRING "" FORCE)
    endif()
    set(LibArchive_FOUND TRUE CACHE BOOL "" FORCE)
    set(LibArchive_INCLUDE_DIR ${LibArchive_INCLUDE_DIRS} CACHE STRING "" FORCE)
    return()
endif()
""",
    ),
    "src/dependencies/libusb.cmake": (
        "# Bundled libusb for rpiboot USB communication\n",
        """if(DEFINED ENV{RPM_USE_SYSTEM_LIBS})
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(LIBUSB REQUIRED IMPORTED_TARGET libusb-1.0)
    set(LIBUSB_FOUND TRUE CACHE BOOL "" FORCE)
    set(LIBUSB_INCLUDE_DIR ${LIBUSB_INCLUDE_DIRS} CACHE STRING "" FORCE)
    set(LIBUSB_LIBRARIES PkgConfig::LIBUSB CACHE STRING "" FORCE)
    if(NOT TARGET usb-1.0-static)
        add_custom_target(usb-1.0-static)
    endif()
    return()
endif()
""",
    ),
    "src/dependencies/nghttp2.cmake": (
        "# Remote nghttp2\n",
        """if(DEFINED ENV{RPM_USE_SYSTEM_LIBS})
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(NGHTTP2 REQUIRED IMPORTED_TARGET libnghttp2)
    set(NGHTTP2_FOUND TRUE CACHE BOOL "" FORCE)
    set(NGHTTP2_LIBRARIES PkgConfig::NGHTTP2 CACHE STRING "" FORCE)
    set(NGHTTP2_LIBRARY PkgConfig::NGHTTP2 CACHE STRING "" FORCE)
    set(NGHTTP2_INCLUDE_DIR ${NGHTTP2_INCLUDE_DIRS} CACHE STRING "" FORCE)
    return()
endif()
""",
    ),
    "src/dependencies/xz.cmake": (
        "# Bundled liblzma (xz)\n",
        """if(DEFINED ENV{RPM_USE_SYSTEM_LIBS})
    find_package(LibLZMA REQUIRED)
    if(TARGET LibLZMA::LibLZMA)
        set(LIBLZMA_LIBRARIES LibLZMA::LibLZMA CACHE STRING "" FORCE)
    endif()
    set(LIBLZMA_FOUND TRUE CACHE BOOL "" FORCE)
    set(LIBLZMA_INCLUDE_DIR ${LIBLZMA_INCLUDE_DIRS} CACHE STRING "" FORCE)
    return()
endif()
""",
    ),
    "src/dependencies/zlib.cmake": (
        "# Bundled zlib\n",
        """if(DEFINED ENV{RPM_USE_SYSTEM_LIBS})
    find_package(ZLIB REQUIRED)
    set(ZLIB_FOUND TRUE CACHE BOOL "" FORCE)
    set(ZLIB_LIBRARIES ZLIB::ZLIB CACHE STRING "" FORCE)
    set(ZLIB_LIBRARY ZLIB::ZLIB CACHE STRING "" FORCE)
    set(ZLIB_INCLUDE_DIR ${ZLIB_INCLUDE_DIRS} CACHE STRING "" FORCE)
    if(NOT TARGET zlibstatic)
        add_custom_target(zlibstatic)
    endif()
    return()
endif()
""",
    ),
    "src/dependencies/zstd.cmake": (
        "# Bundled zstd\n",
        """if(DEFINED ENV{RPM_USE_SYSTEM_LIBS})
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(ZSTD REQUIRED IMPORTED_TARGET libzstd)
    set(ZSTD_FOUND TRUE CACHE BOOL "" FORCE)
    set(Zstd_FOUND TRUE CACHE BOOL "" FORCE)
    set(ZSTD_INCLUDE_DIR ${ZSTD_INCLUDE_DIRS} CACHE STRING "" FORCE)
    set(Zstd_INCLUDE_DIR ${ZSTD_INCLUDE_DIRS} CACHE STRING "" FORCE)
    set(ZSTD_LIBRARIES PkgConfig::ZSTD CACHE STRING "" FORCE)
    set(Zstd_LIBRARIES PkgConfig::ZSTD CACHE STRING "" FORCE)
    return()
endif()
""",
    ),
}


def apply_override(root: Path, relative_path: str, marker: str, block: str) -> bool:
    path = root / relative_path
    text = path.read_text(encoding="utf-8")

    if "RPM_USE_SYSTEM_LIBS" in text:
        return False

    if not text.startswith(marker):
        raise RuntimeError(f"{relative_path} no longer starts with expected marker: {marker.rstrip()}")

    path.write_text(marker + "\n" + block + text[len(marker) :], encoding="utf-8", newline="\n")
    return True


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()

    updated = []
    for relative_path, (marker, block) in INSERTIONS.items():
        if apply_override(root, relative_path, marker, block):
            updated.append(relative_path)

    if updated:
        print("Applied RPM system library overrides:")
        for relative_path in updated:
            print(f"  {relative_path}")
    else:
        print("RPM system library overrides already present.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
