# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify a downloaded Blender portable ZIP by SHA256 and extract it.

Usage: python extract_portable.py <downloads_dir> <version> <dest_dir>
"""

import hashlib
import sys
import zipfile
from pathlib import Path


def main():
    downloads, version, dest = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    name = "blender-%s-windows-x64.zip" % version
    archive = downloads / name
    sha_file = downloads / ("blender-%s.sha256" % version)
    expected = next(
        line.split()[0] for line in sha_file.read_text(encoding="utf-8").splitlines() if line.strip().endswith(name)
    )
    h = hashlib.sha256()
    with archive.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    if h.hexdigest() != expected:
        raise SystemExit("SHA256 mismatch for %s" % name)
    dest.mkdir(parents=True, exist_ok=True)
    root = dest.resolve()
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            if not (dest / info.filename).resolve().is_relative_to(root):
                raise SystemExit("Unsafe path in archive: %s" % info.filename)
        z.extractall(dest)
    print("extracted", version, expected)


if __name__ == "__main__":
    main()
