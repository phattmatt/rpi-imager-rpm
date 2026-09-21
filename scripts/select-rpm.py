#!/usr/bin/env python3
"""Select exactly one main binary by RPM metadata, excluding debug/source packages."""
import subprocess
import sys
from pathlib import Path


def select_rpm(directory: Path) -> Path:
    matches = []
    for path in sorted(directory.rglob('*.rpm')):
        name, arch = subprocess.check_output(
            ['rpm', '-qp', '--qf', '%{NAME}\t%{ARCH}', str(path)], text=True
        ).split('\t')
        if name == 'rpi-imager' and arch in ('x86_64', 'aarch64'):
            matches.append(path)
    if len(matches) != 1:
        raise SystemExit(f'Expected one main binary RPM in {directory}, found {len(matches)}')
    return matches[0]


if __name__ == '__main__':
    print(select_rpm(Path(sys.argv[1])))
