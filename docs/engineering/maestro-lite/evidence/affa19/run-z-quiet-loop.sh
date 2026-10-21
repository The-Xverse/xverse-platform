#!/bin/bash
# Increment19 finding 488: repeat the full installed-wheel run (driver
# verify-platform-regression-20261021t.py) on the same head until one run is decisive under 469:
#   clean (driver exit 0)                      -> stop, "clean"
#   failed and every in-run sample <= 10       -> stop, "failed-at-low-load" (regression signal, 487)
#   failed and some in-run sample > 10         -> observation: archive, then wait and repeat
# Each attempt waits for the run-x/run-y quiet condition (1-minute load < 7 at five consecutive
# checks one minute apart), samples /proc/loadavg every 30 s into <out>/load-samples.jsonl, then
# archives the receipts and removes only that attempt's own tmpfs work directory. Overall bound
# 10 h; never generates load while waiting; one driver at a time.
HERE=$(dirname "$(realpath "$0")"); PREFIX=$1; DEADLINE=$(( $(date +%s) + 36000 )); attempt=0
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
  quiet=0
  while [ "$(date +%s)" -lt "$DEADLINE" ] && [ $quiet -lt 5 ]; do
    if pgrep -f "verify-platform-regression-20261021[t]" >/dev/null; then quiet=0
    elif awk '{exit !($1 < 7)}' /proc/loadavg; then quiet=$((quiet+1)); else quiet=0; fi
    [ $quiet -lt 5 ] && sleep 60
  done
  [ $quiet -lt 5 ] && break
  attempt=$((attempt+1)); OUT="$HERE/$PREFIX-$attempt"
  echo "attempt $attempt triggered $(date -u +%FT%TZ) load $(cut -d' ' -f1-3 /proc/loadavg) out $(basename "$OUT")"
  python3 "$HERE/verify-platform-regression-20261021t.py" "$OUT" & driver=$!
  while kill -0 $driver 2>/dev/null; do
    [ -d "$OUT" ] && printf '{"utc": "%s", "loadavg": "%s"}\n' "$(date -u +%FT%TZ)" "$(cut -d' ' -f1-3 /proc/loadavg)" >> "$OUT/load-samples.jsonl"
    sleep 30
  done
  wait $driver; rc=$?
  max=$(python3 -c "import json,sys;print(max(float(json.loads(l)['loadavg'].split()[0]) for l in open(sys.argv[1])))" "$OUT/load-samples.jsonl")
  work=$(python3 -c "import json,sys,os;print(os.path.dirname(json.load(open(sys.argv[1]))['receipts_root']))" "$OUT/wheel-receipt.json" 2>/dev/null)
  case "$work" in
    /dev/shm/maestro-platform-20261021t-*) tar -C "$work" -czf "$OUT/receipts.tar.gz" receipts && rm -rf "$work" ;;
    *) echo "attempt $attempt: work directory not identified ($work); left in place" ;;
  esac
  echo "attempt $attempt rc $rc max-sample $max $(grep -E '^[0-9]+ (passed|failed)' "$OUT/wheel.log" | tail -1)"
  if [ $rc -eq 0 ]; then echo "decisive: clean"; exit 0; fi
  if awk -v m="$max" 'BEGIN{exit !(m <= 10)}'; then echo "decisive: failed-at-low-load"; exit 2; fi
  echo "attempt $attempt: observation (sample above 10); repeating"
done
echo "no decisive run within 10 h ($attempt attempts)"; exit 3
