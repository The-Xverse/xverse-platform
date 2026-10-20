"""Owned direct-child fixture; never used as a Maestro provider or launcher."""

import os
import signal
import sys
import time


if __name__ == "__main__":
    mode = sys.argv[1]
    ready = int(sys.argv[2])
    if mode == "ignore-term":
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    os.write(ready, b"R")
    os.close(ready)
    if mode == "exit":
        raise SystemExit(int(sys.argv[3]))
    if mode == "storage":
        os.read(int(sys.argv[3]), 1)
    else:
        while True:
            time.sleep(60)
