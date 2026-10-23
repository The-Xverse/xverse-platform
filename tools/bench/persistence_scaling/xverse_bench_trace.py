"""Bench-only timing trace of the Maestro persistence worker (S1-T01/T02). Never part of the product.

Installed into a bench-only virtual environment as ``xverse_bench_trace.py`` plus a ``.pth`` line
``import xverse_bench_trace``. It activates only in a process whose command line runs
``xverse.maestro.persistence_worker`` and only while the flag file ``/dev/shm/xverse-bench-trace/ON``
exists. It wraps the request receive function and the suspected per-event costs (research R-1 rows A-C)
and writes one JSON line per handled request to ``/dev/shm/xverse-bench-trace/worker-<pid>.jsonl``
(the worker may not write elsewhere; ``run-bench.sh`` moves the file into the run directory), flushed per
line so that the trace survives SIGKILL. An installation error is written to ``install-error-<pid>.txt``. The wrappers only time
the original callables; they never change arguments, results or exceptions.
"""

import json
import os
import sys
import time

_FLAG = "/dev/shm/xverse-bench-trace/ON"


def _active():
    try:
        with open("/proc/self/cmdline", "rb") as handle:
            if b"xverse.maestro.persistence_worker" not in handle.read():
                return None
        with open(_FLAG) as handle:
            return handle.read().strip() or None
    except OSError:
        return None


def _install(out):
    import xverse.argus.api as argus_api
    import xverse.argus.writer as argus_writer
    import xverse.maestro.lifecycle_evidence as lifecycle_evidence
    import xverse.maestro.persistence as persistence
    import xverse_xdl.lifecycle as xdl_lifecycle

    stream = open(os.path.join(os.path.dirname(_FLAG), f"worker-{os.getpid()}.jsonl"), "a", buffering=1)
    parts, calls = {}, {}
    state = {"pending": None, "events": 0, "seq": 0}

    def timed(name, original, *, count_events=False):
        def wrapper(*args, **kwargs):
            start = time.perf_counter_ns()
            try:
                return original(*args, **kwargs)
            finally:
                parts[name] = parts.get(name, 0) + time.perf_counter_ns() - start
                calls[name] = calls.get(name, 0) + 1
                if count_events:
                    state["events"] += 1
        wrapper.__wrapped__ = original
        return wrapper

    store = argus_api.EvidenceStore
    original_read_run = store.__dict__["read_run"].__func__
    store.read_run = classmethod(timed("argus.read_run", original_read_run))
    journal = xdl_lifecycle.FileEvidenceJournal
    journal._reload = timed("m3.reload", journal._reload)
    run = argus_writer.EvidenceRun
    run.append_event = timed("argus.append_event", run.append_event, count_events=True)
    run.flush_buffer = timed("argus.flush_buffer", run.flush_buffer)
    if hasattr(run, "abort"):
        run.abort = timed("argus.abort", run.abort)
    if hasattr(run, "finalize"):
        run.finalize = timed("argus.finalize", run.finalize)
    outcomes = lifecycle_evidence.OutcomeJournal
    outcomes._mirrors = timed("outcomes.mirrors", outcomes._mirrors)
    outcomes._history = timed("outcomes.history", outcomes._history)
    lifecycle_evidence._same_json = timed("outcomes.same_json", lifecycle_evidence._same_json)
    original_receive = persistence._receive

    def receive(*args, **kwargs):
        now = time.perf_counter_ns()
        pending = state["pending"]
        if pending is not None:
            line = dict(pending, handleNs=now - pending.pop("_received"), events=state["events"],
                        parts=dict(parts), calls=dict(calls))
            stream.write(json.dumps(line, sort_keys=True) + "\n")
            parts.clear()
            calls.clear()
        result = original_receive(*args, **kwargs)
        request = result[0] if isinstance(result, tuple) else result
        state["seq"] += 1
        body = request.get("body") if isinstance(request, dict) else None
        state["pending"] = {"seq": state["seq"], "kind": request.get("kind") if isinstance(request, dict) else None,
                            "bodyKind": body.get("kind") if isinstance(body, dict) else None,
                            "monotonicNs": time.monotonic_ns(), "_received": time.perf_counter_ns()}
        return result

    persistence._receive = receive


class _Hook:
    """Installs the wrappers when the worker module is first imported: the ``.pth`` line runs before the
    system site-packages are on ``sys.path``, so the platform's dependencies are not importable yet."""

    def __init__(self, out):
        self.out = out

    def find_spec(self, name, path=None, target=None):
        if name == "xverse.maestro.persistence_worker" and self.out:
            out, self.out = self.out, None
            sys.meta_path.remove(self)
            try:
                _install(out)
            except Exception as exc:  # noqa: BLE001 - bench-only: record and leave the worker untouched
                with open(os.path.join(os.path.dirname(_FLAG), f"install-error-{os.getpid()}.txt"), "w") as handle:
                    handle.write(repr(exc) + "\n")
        return None


_OUT = _active()
if _OUT:
    sys.meta_path.insert(0, _Hook(_OUT))
