"""Execution compatibility overlay: actual native case without receipt environment."""
import os
import pytest
from .test_terminal_native_writer_failures import (
    run_bootstrap_binary as run_bootstrap_binary,
    test_actual_native_writer_failure_preserves_original_state_and_cleanup as original,
)
from .test_lazy_dispatcher import observe_original_operations as observe_original_operations
from .test_run_broker import broker_stack as broker_stack
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries


@pytest.fixture(autouse=True)
def without_export_environment(monkeypatch):
    monkeypatch.delenv('MAESTRO_BOUNDARY_RECEIPTS',raising=False)


@pytest.mark.parametrize('run_bootstrap_binary',['fsync-once'],indirect=True)
def test_original_native_control_without_export_environment(request,monkeypatch,run_bootstrap_binary):
    assert 'MAESTRO_BOUNDARY_RECEIPTS' not in os.environ
    original(request,monkeypatch,run_bootstrap_binary)
