"""Temporary diagnostic probe (finding 418); removed after use, never committed."""
import time
from xverse.maestro.dispatcher import FiniteDispatcher
from .test_bootstrap import boot_stack as boot_stack, supervisor_binary as supervisor_binary
from .test_boundary import environment as environment, native as native
from .test_dispatcher import dispatcher, ends, full_stack
from .test_launcher import binaries as binaries


def test_probe(request, monkeypatch):
    stack = full_stack(request, monkeypatch, pauses=400, request_limit=2048)
    driver = dispatcher(stack)
    send = FiniteDispatcher._send
    log = []

    def traced(self, kind, until, **values):
        began = time.monotonic()
        try:
            reply = send(self, kind, until, **values)
            log.append((kind, round(until.monotonic_seconds - began, 4), "ok", round(time.monotonic() - began, 4)))
            return reply
        except Exception as exc:
            log.append((kind, round(until.monotonic_seconds - began, 4), type(exc).__name__ + ":" + str(exc), round(time.monotonic() - began, 4)))
            raise

    monkeypatch.setattr(FiniteDispatcher, "_send", traced)
    active, terminal = ends(driver)
    result = driver.run(active, terminal)
    print("PROBE", result.diagnostic, "active_end_minus_return", round(active.monotonic_seconds - time.monotonic(), 3))
    first = next((i for i, e in enumerate(log) if e[2] != "ok"), None)
    print("PROBE-FIRST-FAIL", None if first is None else log[max(0, first - 3):first + 1])
    from collections import Counter
    print("PROBE-KINDS", Counter(k for k, *_ in log))
    print("PROBE-MINREMAIN-TICK", min(r for k, r, *_ in log if k == "tick"))
