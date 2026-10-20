"""TR01–TR06 partial actual native report/ACK-bound writer closure controls."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.persistence import PersistenceClient, PersistenceError
from xverse.maestro.runtime_verification import runtime_admission_digest, verify_runtime_closed
from .test_lazy_dispatcher import scheduled as original_scheduled, run
from .test_lazy_dispatcher import observe_original_operations as observe_original_operations
from .test_run_broker import broker_stack as broker_stack
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


def scheduled(request,monkeypatch,**kw):
    stack,controller,driver=original_scheduled(request,monkeypatch,**kw)
    target=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if target:
        root=Path(target);root.mkdir(parents=True,exist_ok=True);client=stack[2]
        (root/('terminal-original-inputs-'+stack[3].parent.name+'.json')).write_text(json.dumps(dict(
            original_admission=json.loads(client.coverage.public_bytes),admission_digest=client.coverage_digest,
            original_collection=json.loads(client.collection.canonical_bytes),generation_ns=client.generation_ns,
            runtime_digest=runtime_admission_digest(client.coverage,client.collection,client.generation_ns),
            original_fixture=str(stack[3].parent),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n')
    return stack,controller,driver


def verify(client,root):
    return verify_runtime_closed(client.coverage,client.collection,root,
        expected_admission_digest=client.coverage_digest,generation_ns=client.generation_ns,
        expected_runtime_digest=runtime_admission_digest(client.coverage,client.collection,client.generation_ns))


def retain(stack,result,case):
    broker,_,client,work=stack
    target=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if target:
        root=Path(target);root.mkdir(parents=True,exist_ok=True)
        reader=EvidenceStore.read_run(work.parent/'argus')
        raw=(work.parent/'argus/manifest.json').read_bytes()
        (root/('terminal-runtime-'+work.parent.name+'.json')).write_text(json.dumps(dict(
            case=case,receipt=result.terminal.public_data() if result.terminal else None,
            execution_succeeded=result.execution_succeeded,diagnostic=result.diagnostic,
            original_admission=json.loads(client.coverage.public_bytes),admission_digest=client.coverage_digest,
            original_collection=json.loads(client.collection.canonical_bytes),generation_ns=client.generation_ns,
            runtime_digest=runtime_admission_digest(client.coverage,client.collection,client.generation_ns),
            manifest=reader.manifest,manifest_sha256=hashlib.sha256(raw).hexdigest(),
            original_fixture=str(work.parent),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            native_helper_closure_not_inferred=True,full_M1_complete=False,scientific_result=False),indent=2)+'\n')


@pytest.mark.parametrize('implicit',[False,True])
def test_actual_native_report_close_and_external_closed_recomputation(request,monkeypatch,implicit):
    stack,_,driver=scheduled(request,monkeypatch,implicit=implicit)
    broker,_,client,work=stack
    result=run(driver)
    assert result.execution_succeeded and result.terminal_recorded,result.diagnostic
    assert result.terminal is not None,result.diagnostic
    facts=result.terminal.public_data()
    assert facts['diagnostic'] is None,facts
    report=facts['report'];writer=facts['writer']
    assert report['eligible'] and not report['blockers'],report
    assert writer['finalize_completed'] and not writer['abort_attempted'],writer
    assert writer['after_state']==writer['durable_writer_state']=='closed'
    assert writer['evidence_complete'] and writer['collection_verified'] and writer['collection_complete'],writer
    assert facts['storageDrain']['worker_reaped'] and facts['storageDrain']['returncode']==0
    checked=verify(client,work.parent/'argus')
    assert checked.complete,checked
    assert checked.lifecycle.coverage.report()['overallStatus']=='complete'
    assert checked.lifecycle.manifest_sha256==writer['manifest_sha256']
    actual=EvidenceStore.read_run(work.parent/'argus').records()
    for event in actual:
        payload=event.get('extensions',{}).get('xverse.maestro',{})
        if payload.get('scope')=='step' and payload.get('action') in ('started','probe','stop','cleanup'):
            assert payload.get('handleRef','').startswith('handle-')
            if payload['action'] in ('started','probe') and 'sink-instance' in payload['unitId']:
                assert len(payload['dependencies'])==1
            if payload['action']=='started':
                assert len(payload['sourceRefs'])==3
    assert not result.lifecycle_complete and not result.terminal.lifecycle_complete
    assert client.last_writer_state=='closed' and client._aborted and not client._failed
    end=client._terminal_outcome[1]
    from xverse.maestro.time import HostDeadline
    with monkeypatch.context() as patch:
        patch.setattr(PersistenceClient,'_rpc',lambda *a,**kw:pytest.fail('matching terminal replay RPC'))
        assert client.finish_run(broker,HostDeadline(*end)) is result.terminal
        with pytest.raises(ValueError,match='ML-TERMINAL-ORIGINAL'):
            client.finish_run(broker,deadline(.5))
    retain(stack,result,'implicit' if implicit else 'explicit')


@pytest.mark.parametrize('fault',['lost-report-ack','changed-report-ack','lost-close-ack'])
def test_actual_lost_or_changed_ack_preserves_unknown_state_and_never_replays(request,monkeypatch,fault):
    stack,_,driver=scheduled(request,monkeypatch);client=stack[2]
    original=PersistenceClient._rpc;intercepted=[]
    def observed(self,kind,body,end,**kw):
        result=original(self,kind,body,end,**kw)
        if self is client and kind=='terminal-report':
            intercepted.append(body['action'])
            if body['action']=='publish' and fault=='lost-report-ack':
                raise PersistenceError('ML-TEST-LOST-ACK')
            if body['action']=='publish' and fault=='changed-report-ack':
                operation,until,reply=result;reply=deepcopy(reply);reply['annotationCount']+=1
                return operation,until,reply
            if body['action']=='close' and fault=='lost-close-ack':
                raise PersistenceError('ML-TEST-LOST-ACK')
        return result
    monkeypatch.setattr(PersistenceClient,'_rpc',observed)
    result=run(driver);facts=result.terminal.public_data()
    assert result.execution_succeeded and result.terminal_recorded
    assert facts['writer'] is None and facts['diagnostic'] is not None
    assert facts['lastAcknowledgedWriterState']=='open' and client.last_writer_state=='open'
    assert client._failed and not result.lifecycle_complete
    assert intercepted==(['publish'] if fault=='lost-report-ack' else ['publish','close'] if fault=='lost-close-ack' else ['publish'])
    # A closed durable writer after a lost close ACK is independently observable;
    # it does not retrospectively mint that missing original acknowledgement.
    manifest=EvidenceStore.read_run(stack[3].parent/'argus').manifest
    assert manifest['writerState']==('closed' if fault=='lost-close-ack' else 'open')
    from xverse.maestro.time import HostDeadline
    before=client._sequence
    assert client.finish_run(stack[0],HostDeadline(*client._terminal_outcome[1])) is result.terminal
    assert client._sequence==before
    retain(stack,result,fault)


def test_actual_required_output_loss_publishes_incomplete_report_then_aborts(request,monkeypatch):
    stack,_,driver=scheduled(request,monkeypatch)
    client=stack[2];original=PersistenceClient.collect_outputs
    def missing(self,broker,end):
        if self is client:
            for path in stack[3].glob('*.marker'):path.unlink()
        return original(self,broker,end)
    monkeypatch.setattr(PersistenceClient,'collect_outputs',missing)
    result=run(driver);facts=result.terminal.public_data()
    assert not result.execution_succeeded and result.terminal_recorded
    assert facts['diagnostic'] is None and facts['report']['entry'] is not None,facts
    assert not facts['report']['eligible'] and not facts['report']['collectionComplete']
    assert 'collection' in facts['report']['blockers'] and 'required-coverage' in facts['report']['blockers']
    assert not facts['writer']['finalize_attempted'] and facts['writer']['abort_completed']
    assert facts['writer']['after_state']=='failed' and not facts['writer']['evidence_complete']
    assert not verify(client,stack[3].parent/'argus').complete
    retain(stack,result,'required-missing')


def test_terminal_before_collection_rejects_without_consuming_original_request(request,monkeypatch):
    stack,_,driver=scheduled(request,monkeypatch);client=stack[2]
    sequence=client._sequence
    with pytest.raises(ValueError,match='ML-TERMINAL-BUDGET'):client.finish_run(stack[0],deadline(1))
    assert client._sequence==sequence and not client._terminal_attempted and not client._failed
    result=run(driver)
    assert result.terminal.public_data()['writer']['evidence_complete'],result.terminal.public_data()
    retain(stack,result,'preflight')


@pytest.mark.parametrize('optional',[False,True])
def test_actual_changed_collected_output_blocks_finalize_even_when_optional(request,monkeypatch,optional):
    stack,_,driver=scheduled(request,monkeypatch,optional=optional);client=stack[2]
    original=PersistenceClient.finish_run
    def changed(self,broker,end):
        if self is client:
            destination=stack[3].parent/'argus'/self.collection.declarations[0].destination
            destination.write_bytes(b'changed')
        return original(self,broker,end)
    monkeypatch.setattr(PersistenceClient,'finish_run',changed)
    result=run(driver);facts=result.terminal.public_data()
    assert result.execution_succeeded and result.terminal_recorded
    assert facts['diagnostic'] is None and facts['report']['entry'] is not None,facts
    assert facts['report']['normalComplete'] and facts['report']['collectionComplete']
    assert not facts['report']['eligible']
    assert ('optional-integrity' if optional else 'required-coverage') in facts['report']['blockers']
    assert facts['report']['requiredRowsSatisfied'] is optional
    assert not facts['writer']['finalize_attempted'] and facts['writer']['abort_completed']
    assert facts['writer']['after_state']=='failed' and not facts['writer']['evidence_complete']
    retain(stack,result,'changed-optional' if optional else 'changed-required')
