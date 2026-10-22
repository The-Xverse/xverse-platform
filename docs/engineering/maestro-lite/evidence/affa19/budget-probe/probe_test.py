"""Temporary diagnostic probe (finding 428); removed after use, never committed."""
import json, os, time
from xverse.maestro.dispatcher import FiniteDispatcher
from .test_terminal_runtime import scheduled, run
from .test_lazy_dispatcher import observe_original_operations as observe_original_operations
from .test_run_broker import broker_stack as broker_stack
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries


def test_probe(request, monkeypatch):
    stack, _, driver = scheduled(request, monkeypatch)
    log = []
    end = FiniteDispatcher._end
    send = FiniteDispatcher._send

    def traced_end(self, *, terminal=False, restart=False, recovery=False, unit=None, phase=None):
        now = time.monotonic()
        terms = dict(limit=(self._work_end if terminal else self._active_end) - now,
                     budget=self.plan.operation_seconds, root_lease=self.bootstrap._lease / 1e9 - now)
        health = self.facade.next_health_deadline
        if health is not None:
            terms['health'] = health.monotonic_seconds - self.plan.health_scan_seconds - now
        for u, gate in self.gates.items():
            if u not in self.teardown._stopped:
                terms['gate:' + u.rsplit('/', 1)[-1]] = gate.lease_ns / 1e9 - now
        try:
            value = end(self, terminal=terminal, restart=restart, recovery=recovery, unit=unit, phase=phase)
        except Exception as exc:
            log.append(dict(where='end', terminal=terminal, terms=terms, error=str(exc)))
            raise
        log.append(dict(where='end', terminal=terminal, terms={k: round(v, 4) for k, v in terms.items()},
                        given=round(value.monotonic_seconds - now, 4),
                        limited_by=min(terms, key=terms.get)))
        return value

    def traced_send(self, kind, until, **values):
        began = time.monotonic()
        try:
            reply = send(self, kind, until, **values)
            log.append(dict(where='send', kind=kind, budget=round(until.monotonic_seconds - began, 4), took=round(time.monotonic() - began, 4)))
            return reply
        except Exception as exc:
            log.append(dict(where='send', kind=kind, budget=round(until.monotonic_seconds - began, 4), error=str(exc), took=round(time.monotonic() - began, 4)))
            raise

    monkeypatch.setattr(FiniteDispatcher, '_end', traced_end)
    monkeypatch.setattr(FiniteDispatcher, '_send', traced_send)
    result = run(driver)
    client = stack[2]
    failure = client.rpc_failure
    small = [e for e in log if e['where'] == 'end' and e.get('given', 1) < 0.15]
    from collections import Counter
    print('PROBE', json.dumps(dict(succeeded=result.execution_succeeded, diagnostic=result.diagnostic,
        rpc_failure=None if failure is None else dict(kind=failure.kind, budget=round((failure.deadline_ns - failure.started_ns) / 1e9, 4) if failure.deadline_ns else None, diagnostic=failure.diagnostic),
        small_budget_ends=len(small), limited_by=dict(Counter(e['limited_by'] for e in small)),
        tail=log[-6:])))
