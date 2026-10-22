#!/bin/bash
# Increment19 finding 487: as run-x-quiet-watch.sh (469 (3)): start the full installed-wheel run
# only after the 1-minute load stays below 7 at five consecutive checks one minute apart (at most
# 6 h of checks, never generating load), and additionally sample /proc/loadavg every 30 s for the
# whole run into <out>/load-samples.jsonl, so the 469 ruling ("recorded host load exceeds 10 at
# any sample") is applied to samples taken during the run, not only at launch and end.
HERE=$(dirname "$(realpath "$0")"); OUT="$HERE/$1"; quiet=0
for _ in $(seq 360); do
  if pgrep -f "verify-platform-regression-20261021[t]" >/dev/null; then quiet=0
  elif awk '{exit !($1 < 7)}' /proc/loadavg; then quiet=$((quiet+1)); else quiet=0; fi
  if [ $quiet -ge 5 ]; then
    echo "triggered $(date -u +%FT%TZ) load $(cut -d' ' -f1-3 /proc/loadavg)"
    python3 "$HERE/verify-platform-regression-20261021t.py" "$OUT" & driver=$!
    while kill -0 $driver 2>/dev/null; do
      if [ -d "$OUT" ]; then
        printf '{"utc": "%s", "loadavg": "%s"}\n' "$(date -u +%FT%TZ)" "$(cut -d' ' -f1-3 /proc/loadavg)" >> "$OUT/load-samples.jsonl"
      fi
      sleep 30
    done
    wait $driver; exit $?
  fi
  sleep 60
done
echo "quiet condition never arose within 6 h"
