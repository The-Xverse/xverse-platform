#!/bin/bash
# Usage: calibrate.sh <out-dir> <repeats>; quiet-host RPC service-time capture on the unmodified stack.
ROOT=/home/jefferson/xverse-platform-worktrees/maestro-lite-affa19-20261021
HERE=$(dirname "$(readlink -f "$0")")
OUT=$1; N=$2; mkdir -p "$OUT"
MODS="tests/thesis_lite/maestro/test_dispatcher.py tests/thesis_lite/maestro/test_terminal_runtime.py tests/thesis_lite/maestro/test_teardown.py tests/thesis_lite/maestro/test_time_context_controls.py tests/thesis_lite/maestro/test_active_restart.py tests/thesis_lite/maestro/test_shared_dispatcher.py"
for i in $(seq 1 $N); do
  T=$(mktemp -d /dev/shm/maestro-cal-XXXXXX)
  L=$(cut -d' ' -f1 /proc/loadavg)
  (cd $ROOT && env PYTHONPATH=$ROOT/src:$HERE PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
    PYTEST_PLUGINS=maestro_receipt_namespace,rpc_timeline_plugin TMPDIR=$T RPC_TIMELINE_OUT=$OUT/r$i \
    /tmp/maestro-lite-platform-regression-target-20261020h/bin/python -m pytest -q -rf -p no:cacheprovider --basetemp $T/base $MODS > $OUT/r$i.log 2>&1)
  echo "r$i load=$L $(tail -1 $OUT/r$i.log)"
  rm -rf $T
done
