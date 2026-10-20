"""Worker-private public writer operations; original report orchestration is separate."""
from dataclasses import dataclass

from .runtime_verification import validate_runtime_admission, verify_runtime_closed


@dataclass(frozen=True)
class TerminalWriterObservation:
    before_state: str
    after_state: str
    eligible: bool
    finalize_attempted: bool
    finalize_completed: bool
    abort_attempted: bool
    abort_completed: bool
    abort_usability: str
    after_usability: str
    stage: str
    manifest_sha256: str | None
    durable_writer_state: str | None
    durable_recorded_status: str | None
    durable_assessed_status: str | None
    reader_diagnostics: tuple[str, ...]
    collection_verified: bool
    collection_complete: bool
    evidence_complete: bool


def close_runtime_writer(writer, root, *, eligible, admission, plan, generation_ns,
                         expected_admission_digest, expected_runtime_digest, check):
    """Called only after the original worker independently establishes eligibility.

    This routine has no authority authentication or RPC entry point. Its caller
    must bind the original report ACK and fixed end; it never grants lifecycle
    completion. Only public writer operations and independently accepted closed
    evidence can contribute observations.
    """
    if type(eligible) is not bool:
        raise ValueError('ML-TERMINAL-WRITER-ELIGIBILITY')
    pins=dict(expected_admission_digest=expected_admission_digest,
              expected_runtime_digest=expected_runtime_digest,generation_ns=generation_ns)
    validate_runtime_admission(admission,plan,**pins)
    check()
    before=writer.writer_state
    finalize_attempted=finalize_completed=abort_attempted=abort_completed=False
    usability='unknown';stage='not-open'
    if before=='open' and eligible:
        finalize_attempted=True
        try:
            writer.finalize()
            check()
            finalize_completed=True;stage='finalize-completed'
        except Exception:
            stage='finalize-error'
    # An open state after finalize raises can conceal an unusable closed stream.
    # A fresh successful public flush, including its deadline check, is required.
    check()
    if before=='open' and writer.writer_state=='open' and not finalize_completed:
        try:
            writer.flush_buffer()
            check()
        except Exception:
            stage='flush-error'
        else:
            usability='usable'
            check()
            abort_attempted=True
            try:
                writer.abort(reason='Maestro terminal report; lifecycle evidence remains incomplete')
                check()
                abort_completed=True;stage='abort-completed'
            except Exception:
                stage='abort-error'
    check()
    after=writer.writer_state
    durable_state=recorded=assessed=manifest_sha=None
    codes=();collection_verified=collection_complete=evidence_complete=False
    try:
        observed=verify_runtime_closed(admission,plan,root,**pins)
        check()
        lifecycle=observed.lifecycle
        durable_state=lifecycle.writer_state
        manifest_sha=lifecycle.manifest_sha256
        recorded=lifecycle.recorded_argus_status
        assessed=lifecycle.assessed_argus_status
        codes=tuple(dict.fromkeys((*lifecycle.reader_diagnostics,*observed.diagnostics)))[:128]
        collection_verified=observed.collection_verified
        collection_complete=observed.collection_complete
        evidence_complete=observed.complete
    except Exception:
        codes=('ML-TERMINAL-CLOSED-READER-UNRESOLVED',)
    check()
    return TerminalWriterObservation(before,after,eligible,finalize_attempted,finalize_completed,
        abort_attempted,abort_completed,usability,
        {'closed':'not-applicable','failed':'unusable'}.get(after,'unknown'),stage,
        manifest_sha,durable_state,recorded,assessed,codes,
        collection_verified,collection_complete,evidence_complete)
