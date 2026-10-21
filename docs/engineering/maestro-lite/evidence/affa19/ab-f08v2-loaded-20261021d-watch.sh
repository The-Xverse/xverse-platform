#!/bin/bash
# Increment19 finding 467 (c): wait for natural external load (llama-server of another project and
# 1-minute load >= 10), then run A/B d once with 4 pairs. Checks every 60 s for at most 3 h; never
# generates load; gives up silently when the condition never arises.
HERE=$(dirname "$(realpath "$0")"); OUT="$HERE/$1"
for _ in $(seq 180); do
  if pgrep -x llama-server >/dev/null && awk '{exit !($1 >= 10)}' /proc/loadavg; then
    echo "triggered $(date -u +%FT%TZ) load $(cut -d' ' -f1-3 /proc/loadavg)"
    exec python3 "$HERE/ab-f08v2-loaded-20261021d.py" "$OUT" 4
  fi
  sleep 60
done
echo "condition never arose within 3 h"
