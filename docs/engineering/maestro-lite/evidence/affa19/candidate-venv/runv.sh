#!/bin/bash
# Usage: runv.sh <venv-dir> <tree> <pytest args...>. Focused run with one installed version:
# no PYTHONPATH, so the test process and the native-started worker import the same package.
VENV=$1; TREE=$2; shift 2
T=$(mktemp -d /dev/shm/maestro-affa19-venv-XXXXXX)
cd "$TREE" && env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  PYTEST_PLUGINS=maestro_receipt_namespace TMPDIR=$T "$VENV/bin/python" -m pytest -p no:cacheprovider --basetemp $T/base "$@"
rc=$?; rm -rf $T; exit $rc
