#!/bin/bash
# Increment19 finding 469 (3): start the full installed-wheel run on the final head only on a quiet
# host: 1-minute load below 7 at five consecutive checks one minute apart. Checks every 60 s for at
# most 6 h; never generates load; never starts while another driver of this folder is running.
HERE=$(dirname "$(realpath "$0")"); OUT="$HERE/$1"; quiet=0
for _ in $(seq 360); do
  if pgrep -f "verify-platform-regression-20261021[t]" >/dev/null; then quiet=0
  elif awk '{exit !($1 < 7)}' /proc/loadavg; then quiet=$((quiet+1)); else quiet=0; fi
  if [ $quiet -ge 5 ]; then
    echo "triggered $(date -u +%FT%TZ) load $(cut -d' ' -f1-3 /proc/loadavg)"
    exec python3 "$HERE/verify-platform-regression-20261021t.py" "$OUT"
  fi
  sleep 60
done
echo "quiet condition never arose within 6 h"
