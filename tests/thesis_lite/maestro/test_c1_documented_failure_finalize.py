"""C1 (findings 468, 471): a factually complete failed run is finalized; every other report is not.

Unit-level controls of the finalize rule shared by the worker (close_runtime_writer) and the parent
(_writer_ack, RunClosure). Eligibility keeps its meaning; finalization never grants it.
"""
import copy

import pytest

from xverse.maestro.terminal_runtime import PersistenceError, _hash, _writer_ack, finalizable
from xverse.maestro.terminal_writer import TerminalWriterObservation, close_runtime_writer
from xverse.maestro.coverage import canonical

ENTRY = dict(path='lifecycle-coverage.json', bytes=10, sha256='a' * 64, mediaType='application/json',
             schemaVersion='2.0', role='evidence')


def report(**changes):
    base = dict(eligible=False, blockers=['terminal-outcome'], entry=ENTRY, retainedEntry=dict(ENTRY, path='r'),
                stage='published', normalComplete=True, requiredRowsSatisfied=True, collectionComplete=True,
                terminalSucceeded=False)
    base.update(changes)
    return base


def test_documented_failure_is_finalizable():
    assert finalizable(report())


def test_eligible_report_is_finalizable():
    assert finalizable(report(eligible=True, blockers=[], terminalSucceeded=True))


@pytest.mark.parametrize('changes', [
    dict(blockers=['terminal-outcome', 'collection'], collectionComplete=False),
    dict(blockers=['normal-records', 'terminal-outcome'], normalComplete=False),
    dict(blockers=['terminal-outcome', 'required-coverage'], requiredRowsSatisfied=False),
    dict(blockers=['terminal-outcome', 'uncertain-applicability']),
    dict(blockers=['terminal-outcome', 'optional-integrity']),
    dict(blockers=['terminal-outcome', 'publication']),
    dict(blockers=['publication']),
    dict(entry=None),
    dict(retainedEntry=None),
    dict(stage='report-write'),
    dict(normalComplete=False),
    dict(terminalSucceeded=True),
], ids=lambda c: '+'.join(sorted(c)))
def test_any_other_gap_is_not_finalizable(changes):
    assert not finalizable(report(**changes))


class _Writer:
    def __init__(self):
        self.writer_state = 'open'; self.calls = []

    def finalize(self):
        self.calls.append('finalize'); self.writer_state = 'closed'

    def flush_buffer(self):
        self.calls.append('flush')

    def abort(self, **kw):
        self.calls.append('abort'); self.writer_state = 'failed'


@pytest.mark.parametrize('eligible,finalize', [(True, False), (False, 1), (False, 'yes'), ('no', None)])
def test_writer_closure_rejects_inconsistent_finalize_flags(eligible, finalize):
    writer = _Writer()
    with pytest.raises(ValueError, match='ML-TERMINAL-WRITER-ELIGIBILITY'):
        close_runtime_writer(writer, None, eligible=eligible, finalize=finalize, admission=None, plan=None,
                             generation_ns=0, expected_admission_digest=None, expected_runtime_digest=None,
                             check=lambda: None)
    assert writer.calls == []


def _closed_row(rep):
    fields = TerminalWriterObservation.__dataclass_fields__
    row = dict(before_state='open', after_state='closed', eligible=rep['eligible'], finalize_attempted=True,
               finalize_completed=True, abort_attempted=False, abort_completed=False, abort_usability='unknown',
               after_usability='not-applicable', stage='finalize-completed', manifest_sha256='b' * 64,
               durable_writer_state='closed', durable_recorded_status='complete', durable_assessed_status='complete',
               reader_diagnostics=[], collection_verified=True, collection_complete=True, evidence_complete=True)
    assert set(row) == set(fields)
    return row


def _aborted_row(rep):
    row = _closed_row(rep)
    row.update(after_state='failed', finalize_attempted=False, finalize_completed=False, abort_attempted=True,
               abort_completed=True, abort_usability='usable', after_usability='unusable', stage='abort-completed',
               durable_writer_state='failed', evidence_complete=False)
    return row


def ack(rep, row):
    return _writer_ack(dict(reportReceiptDigest=_hash(canonical(rep)), writer=row), rep)


def test_parent_accepts_finalized_documented_failure_and_rejects_its_abort():
    rep = report()
    assert ack(rep, _closed_row(rep))['finalize_completed']
    with pytest.raises(PersistenceError, match='ML-TERMINAL-CLOSE-ACK'):
        ack(rep, _aborted_row(rep))  # the old policy is no longer a valid ACK for this report


def test_parent_still_requires_abort_path_for_other_gaps():
    rep = report(blockers=['terminal-outcome', 'collection'], collectionComplete=False)
    with pytest.raises(PersistenceError, match='ML-TERMINAL-CLOSE-ACK'):
        ack(rep, _closed_row(rep))
    assert ack(rep, _aborted_row(rep))['abort_completed']
