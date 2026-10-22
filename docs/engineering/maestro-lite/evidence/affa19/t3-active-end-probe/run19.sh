#!/bin/bash
# Focused pytest run in the increment19 worktree with driver r/s environment (src on PYTHONPATH).
ROOT=/home/jefferson/xverse-platform-worktrees/maestro-lite-affa19-20261021
T=$(mktemp -d /dev/shm/maestro-affa19-focused-XXXXXX)
cd $ROOT && env PYTHONPATH=$ROOT/src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  PYTEST_PLUGINS=maestro_receipt_namespace TMPDIR=$T \
  /tmp/maestro-lite-platform-regression-target-20261020h/bin/python -m pytest -p no:cacheprovider --basetemp $T/base "$@"
rc=$?; rm -rf $T; exit $rc
