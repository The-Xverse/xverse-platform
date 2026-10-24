import json, sys, tempfile, time
from pathlib import Path
sys.path.insert(0, ".")
import tests.thesis_lite.maestro.test_persistence_config_bound as m
m.PHASE8_UNITS = m.PHASE8_UNITS + tuple(f"extra-unit-{i}" for i in range(9))
rows = []
for n in (8, 10, 12, 16):
    for shape, h in (("phase8", 600), ("bench", 300)):
        with tempfile.TemporaryDirectory(dir="/dev/shm") as t:
            try:
                t0 = time.monotonic(); c = m.configuration(Path(t), n, shape=shape, horizon=h, operation=0.1)
                rows.append(dict(shape=shape, horizon=h, op=0.1, units=n, bytes=len(c.private_bytes), seconds=round(time.monotonic()-t0, 2)))
            except Exception as e:
                rows.append(dict(shape=shape, horizon=h, units=n, error=f"{type(e).__name__}: {e}"[:200]))
        print(rows[-1], flush=True)
Path(sys.argv[1]).write_text(json.dumps(rows, indent=1))
