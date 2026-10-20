"""TR03 public writer failure stages with actual Argus and labelled fault seams."""
import hashlib

import pytest
from xverse.maestro.terminal_writer import close_runtime_writer
from .test_runtime_verification import RuntimeFixture


def prepared(tmp_path):
    f=RuntimeFixture(tmp_path)
    report=f.provisional()
    (f.root/f.ad['reportPath']).write_bytes(report.public_bytes)
    f.writer.record_artifact(f.ad['reportPath'],schema_version='2.0')
    return f


def close(f,eligible=True,check=lambda:None):
    return close_runtime_writer(f.writer,f.root,eligible=eligible,admission=f.admission,
        plan=f.collection_plan,check=check,**f.pins)


def test_actual_finalize_closed_reader_and_raw_manifest_hash(tmp_path):
    f=prepared(tmp_path);result=close(f)
    assert result.stage=='finalize-completed'
    assert result.finalize_attempted and result.finalize_completed
    assert not result.abort_attempted and not result.abort_completed
    assert result.before_state=='open' and result.after_state==result.durable_writer_state=='closed'
    assert result.abort_usability=='unknown' and result.after_usability=='not-applicable'
    assert result.collection_verified and result.collection_complete and result.evidence_complete
    assert result.durable_recorded_status==result.durable_assessed_status=='complete'
    assert result.manifest_sha256==hashlib.sha256((f.root/'manifest.json').read_bytes()).hexdigest()
    assert not result.reader_diagnostics
    before=(f.root/'manifest.json').read_bytes()
    repeated=close(f)
    assert repeated.stage=='not-open' and not repeated.finalize_attempted and not repeated.abort_attempted
    assert (f.root/'manifest.json').read_bytes()==before


def test_ineligible_actual_writer_flushes_then_aborts_incomplete(tmp_path):
    f=prepared(tmp_path);result=close(f,False)
    assert not result.finalize_attempted
    assert result.abort_attempted and result.abort_completed and result.stage=='abort-completed'
    assert result.abort_usability=='usable' and result.after_usability=='unusable'
    assert result.after_state==result.durable_writer_state=='failed'
    assert result.durable_recorded_status==result.durable_assessed_status=='incomplete'
    assert result.collection_verified and result.collection_complete and not result.evidence_complete
    before=(f.root/'manifest.json').read_bytes()
    repeated=close(f,False)
    assert repeated.stage=='not-open' and not repeated.abort_attempted
    assert before==(f.root/'manifest.json').read_bytes()


def test_finalize_error_with_positive_fresh_flush_permits_actual_abort(tmp_path,monkeypatch):
    f=prepared(tmp_path);calls=[]
    def fail():calls.append('finalize');raise OSError('synthetic finalize-entry failure')
    original=f.writer.flush_buffer
    def flush():calls.append('flush');return original()
    monkeypatch.setattr(f.writer,'finalize',fail)
    monkeypatch.setattr(f.writer,'flush_buffer',flush)
    result=close(f)
    assert calls==['finalize','flush']
    assert result.finalize_attempted and not result.finalize_completed
    assert result.abort_attempted and result.abort_completed and result.after_state=='failed'
    assert result.stage=='abort-completed' and result.abort_usability=='usable'
    assert not result.evidence_complete


def test_finalize_flush_error_open_state_is_not_abort_usability(tmp_path,monkeypatch):
    f=prepared(tmp_path);calls=[]
    def fail():calls.append('flush');raise OSError('synthetic original flush failure')
    with monkeypatch.context() as patch:
        patch.setattr(f.writer,'flush_buffer',fail)
        patch.setattr(f.writer,'abort',lambda **kw:pytest.fail('abort without positive flush'))
        result=close(f)
        assert calls==['flush','flush']
        assert result.finalize_attempted and not result.finalize_completed
        assert not result.abort_attempted and result.abort_usability=='unknown'
        assert result.stage=='flush-error' and result.after_state=='open'
        assert not result.evidence_complete
    f.writer.abort(reason='Synthetic fault removed; cleanup still usable original writer')


def test_actual_manifest_publication_error_failed_writer_is_never_aborted(tmp_path,monkeypatch):
    f=prepared(tmp_path);before=(f.root/'manifest.json').read_bytes()
    def fail(*args,**kw):raise OSError('synthetic closed-manifest publication failure')
    monkeypatch.setattr(f.writer,'_publish',fail)  # Fault injection only; production routine uses public API.
    monkeypatch.setattr(f.writer,'abort',lambda **kw:pytest.fail('abort failed writer'))
    result=close(f)
    assert result.finalize_attempted and not result.finalize_completed
    assert result.after_state=='failed' and result.stage=='finalize-error'
    assert not result.abort_attempted
    assert result.durable_writer_state=='open'  # Durable prior manifest is distinct from process state.
    assert result.manifest_sha256==hashlib.sha256(before).hexdigest()
    assert (f.root/'manifest.json').read_bytes()==before and not result.evidence_complete


@pytest.mark.parametrize('eligible',[0,1,None,'true'])
def test_eligibility_is_exact_boolean_before_writer_effects(tmp_path,eligible):
    f=prepared(tmp_path)
    with pytest.raises(ValueError,match='ML-TERMINAL-WRITER-ELIGIBILITY'):close(f,eligible)
    assert f.writer.writer_state=='open'
    f.writer.abort(reason='Synthetic eligibility control')


def test_expired_original_budget_has_no_finalize_or_abort_effect(tmp_path,monkeypatch):
    f=prepared(tmp_path)
    monkeypatch.setattr(f.writer,'finalize',lambda:pytest.fail('finalize after expiry'))
    def expired():raise TimeoutError('synthetic original deadline expired')
    with pytest.raises(TimeoutError):close(f,check=expired)
    assert f.writer.writer_state=='open'
    f.writer.abort(reason='Synthetic expired-entry control')
