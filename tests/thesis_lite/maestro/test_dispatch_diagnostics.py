"""Actual original helper stalls followed by caller-side cleanup ACK loss."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import signal

import pytest

from .test_lazy_dispatcher import (
    scheduled, run, observe_original_operations as observe_original_operations,
    broker_stack as broker_stack, run_bootstrap_binary as run_bootstrap_binary,
    authority_binary as authority_binary, environment as environment,
    binaries as binaries,
)


@pytest.mark.parametrize('target', ['storage', 'controller'])
def test_actual_primary_helper_timeout_survives_secondary_cleanup_ack_loss(request, monkeypatch, target):
    stack, controller, driver = scheduled(request, monkeypatch)
    child = stack[2].process if target == 'storage' else controller.process
    signal.pidfd_send_signal(child._capability.fileno(), signal.SIGSTOP)
    failures = []
    cleanup = []
    original_send = driver._send
    original_cleanup = driver._cleanup

    def send(kind, *args, **kwargs):
        if kind == 'failure':
            failures.append(dict(kwargs))
        return original_send(kind, *args, **kwargs)

    def lose_cleanup_ack():
        try:
            actual = original_cleanup()
        except Exception as error:
            cleanup.append(dict(actual_error=str(error), returned=None))
            raise
        cleanup.append(dict(actual_error=None, returned=asdict(actual)))
        raise ValueError('ML-TEST-CLEANUP-ACK-LOST')

    monkeypatch.setattr(driver, '_send', send)
    monkeypatch.setattr(driver, '_cleanup', lose_cleanup_ack)
    result = run(driver)
    expected = 'ML-PERSIST-TIMEOUT' if target == 'storage' else 'ML-CONTROLLER-TIMEOUT'
    assert len(failures) == len(cleanup) == 1
    assert failures[0]['diagnostic'] == expected
    out = os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if out:
        (Path(out) / ('primary-diagnostic-' + target + '.json')).write_text(json.dumps(dict(
            target=target, original_fixture=str(stack[3].parent),
            original_failure=failures[0], original_cleanup=cleanup[0],
            observed_diagnostic=result.diagnostic, cleanup=asdict(result.cleanup),
            execution_succeeded=result.execution_succeeded,
            lifecycle_complete=result.lifecycle_complete, ready_for_execution=result.ready_for_execution,
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            actual_original_helper_stopped=True, original_cleanup_invoked=True,
            original_bounds_preserved=True, scientific_result=False), indent=2)+'\n')
    assert not result.execution_succeeded
    assert result.cleanup.starts_closed and not result.cleanup.normal_records_complete
    assert not result.lifecycle_complete and not result.ready_for_execution
    assert result.diagnostic == expected
    assert driver.run(*driver._scope) is result
