"""C1 offline size measurement (dry run, no process). Run from the worktree root with the installed venv."""
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, ".")
from tests.thesis_lite.maestro.test_persistence_config_bound import configuration
rows = []
for shape, horizon, op in (("bench", 300, 0.2), ("bench", 100, 0.2), ("phase8", 600, 0.25), ("phase8", 300, 0.25)):
    for n in (4, 5, 6, 7):
        with tempfile.TemporaryDirectory(dir="/dev/shm") as t:
            c = configuration(Path(t), n, shape=shape, horizon=horizon, operation=op)
            body = json.loads(c.private_bytes)
            parts = {k: len(json.dumps(v, separators=(",", ":"), sort_keys=True)) for k, v in body.items()}
            rows.append(dict(shape=shape, horizon=horizon, op=op, units=n, bytes=len(c.private_bytes), parts=parts))
            print(shape, horizon, n, len(c.private_bytes), flush=True)
Path(sys.argv[1]).write_text(json.dumps(rows, indent=1))
