#!/bin/bash
# runv.sh plus the observation-only interior trace plugin (PYTHONPATH holds only the plugin).
VENV=$1; TREE=$2; OUT=$3; shift 3
HERE=$(dirname "$(realpath "$0")")
T=$(mktemp -d /dev/shm/maestro-affa19-venv-XXXXXX)
cd "$TREE" && env PYTHONPATH="$HERE/trace-plugin" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  PYTEST_PLUGINS=maestro_receipt_namespace,interior_trace_plugin INTERIOR_TRACE_OUT="$OUT" TMPDIR=$T \
  "$VENV/bin/python" -m pytest -p no:cacheprovider --basetemp $T/base "$@"
rc=$?; rm -rf $T; exit $rc
