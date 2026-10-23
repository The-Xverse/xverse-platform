#!/bin/bash
# Usage: run-bench.sh <bench-venv> <out-dir> [trace]. Runs one benchmark run with the venv-installed platform
# (no PYTHONPATH, so the native-started persistence worker imports the same package; finding 442 of
# increment 19). With "trace", the bench venv's xverse_bench_trace records the worker-side timings.
set -u
VENV=$1; OUT=$2; TRACE=${3:-}
HERE=$(cd "$(dirname "$0")" && pwd); ROOT=$(cd "$HERE/../../.." && pwd)
mkdir -p "$OUT"
if [ "$TRACE" = trace ]; then mkdir -p /dev/shm/xverse-bench-trace && echo "$OUT" > /dev/shm/xverse-bench-trace/ON; fi
T=$(mktemp -d /dev/shm/xverse-bench-XXXXXX)
(cd "$ROOT" && env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 PYTEST_PLUGINS=maestro_receipt_namespace \
   XVERSE_BENCH_OUT="$OUT" TMPDIR=$T "$VENV/bin/python" -m pytest -q -p no:cacheprovider --basetemp $T/base --rootdir "$ROOT" \
   "$HERE/bench_persistence.py") > "$OUT/pytest.log" 2>&1
rc=$?
rm -f /dev/shm/xverse-bench-trace/ON
if [ "$TRACE" = trace ]; then mv /dev/shm/xverse-bench-trace/worker-*.jsonl /dev/shm/xverse-bench-trace/install-error-*.txt "$OUT/" 2>/dev/null; fi
rm -rf "$T"
echo "exit=$rc" >> "$OUT/pytest.log"
exit $rc
