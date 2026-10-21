"""C1 negative control (finding 472 (c)): a finalize fault on a documented failure falls through as before.

The failed native run of test_dv09_native_failed_lifecycle combined with the owned worker writer fault
'recovery' (W-04) of test_terminal_native_writer_failures. The report is finalizable, finalize is
attempted and fails; the public states equal the eligible-path expectation for W-04, and no evidence
completeness is claimed. Worker-side code: run with one installed version (finding 442).
"""
import pytest

from .test_dv09_native_failed_lifecycle import failed_run, closure
from .test_terminal_native_writer_failures import EXPECTED, run_bootstrap_binary as run_bootstrap_binary
from .test_run_broker import broker_stack as broker_stack
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries


@pytest.mark.parametrize('run_bootstrap_binary', ['recovery'], indirect=True)
def test_finalize_fault_on_a_documented_failure_keeps_the_w04_states(request, monkeypatch, run_bootstrap_binary):
    keep = {}
    result, checked, facts, *_ = failed_run(request, monkeypatch, keep=keep)
    writer = facts["writer"]
    assert facts["report"]["blockers"] == ["terminal-outcome"] and not facts["report"]["eligible"], facts["report"]
    assert writer["before_state"] == "open" and writer["finalize_attempted"] and not writer["finalize_completed"], writer
    assert (writer["stage"], writer["after_state"], writer["durable_writer_state"], writer["abort_usability"],
            writer["abort_attempted"], writer["abort_completed"]) == EXPECTED["recovery"][:6], writer
    assert not writer["evidence_complete"] and not checked.complete
    closed = closure(keep)
    assert not closed.execution_succeeded and "ML-CLOSURE-REPORT-INCOMPLETE" in closed.diagnostics, closed
