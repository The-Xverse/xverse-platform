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
"$1/bin/python" -m pip install --no-deps --no-index --quiet "$2"
"$1/bin/python" -I -c 'import xverse.maestro, xverse_xdl; print(xverse.maestro.__file__)'
