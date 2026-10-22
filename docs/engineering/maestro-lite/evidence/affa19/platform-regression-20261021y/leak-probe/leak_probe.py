"""Observation-only: at session finish, report live descendant processes and threads of this pytest process."""
import os, threading, subprocess, time
def pytest_sessionfinish(session, exitstatus):
    me = os.getpid()
    out = subprocess.run(["ps", "-eo", "pid,ppid,pgid,etimes,pcpu,stat,args", "--sort=pid"], capture_output=True, text=True).stdout.splitlines()
    rows = [r.split(None, 6) for r in out[1:]]
    kids = {me}; changed = True
    while changed:
        changed = False
        for r in rows:
            if int(r[1]) in kids and int(r[0]) not in kids: kids.add(int(r[0])); changed = True
    pg = os.getpgid(me)
    with open(os.environ["LEAK_PROBE_OUT"], "w") as f:
        f.write(f"pid {me} pgid {pg} threads {[t.name for t in threading.enumerate()]}\n")
        for r in rows:
            if int(r[0]) in kids - {me} or (int(r[2]) == pg and int(r[0]) != me):
                f.write(" ".join(r)[:300] + "\n")
