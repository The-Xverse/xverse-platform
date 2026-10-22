#!/bin/bash
# Usage: mkvenv.sh <venv-dir> <wheel>. One interpreter per candidate (finding 442): system site
# packages as the regression target venv, the candidate wheel without dependencies, and the
# receipt-namespace pytest plugin copied from the target venv. Writes only <venv-dir>.
set -euo pipefail
BASE=/home/jefferson/.pyenv/versions/3.13.13/bin/python3.13
TARGET=/tmp/maestro-lite-platform-regression-target-20261020h
"$BASE" -m venv --system-site-packages "$1"
SP=$("$1/bin/python" -c 'import sysconfig;print(sysconfig.get_paths()["purelib"])')
cp "$TARGET/lib/python3.13/site-packages/maestro_receipt_namespace.py" "$SP/"
# Build tools of environment h, copied file by file from their RECORD entries (finding 458; the
# Argus packaging tests run `python -m build`). pip and xverse_xdl are not copied.
"$1/bin/python" -I - "$TARGET/lib/python3.13/site-packages" "$SP" <<'PY'
import csv, shutil, sys
from pathlib import Path
source, target = Path(sys.argv[1]), Path(sys.argv[2])
for dist in ("build", "hatchling", "packaging", "pluggy", "pyproject_hooks", "tomlkit", "trove_classifiers"):
    info = next(source.glob(dist + "-*.dist-info"))
    for row in csv.reader((info / "RECORD").read_text().splitlines()):
        relative = Path(row[0])
        if relative.is_absolute() or ".." in relative.parts or relative.parts[0] in ("..", "bin"):
            continue
        origin = source / relative
        if origin.is_file():
            (target / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origin, target / relative)
PY
"$1/bin/python" -m build --version
"$1/bin/python" -I -c 'import hatchling, importlib.metadata as m; print("hatchling", m.version("hatchling"))'
"$1/bin/python" -m pip install --no-deps --no-index --quiet "$2"
"$1/bin/python" -I -c 'import xverse.maestro, xverse_xdl; print(xverse.maestro.__file__)'
