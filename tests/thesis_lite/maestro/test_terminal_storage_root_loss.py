"""Original post-collection storage/root loss, unknown terminal ACKs and owned cleanup."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import time

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.persistence import PersistenceClient
from xverse.maestro.run_closure import RunClosure
from xverse.maestro.runtime_verification import runtime_admission_digest
from xverse.maestro.time import HostDeadline
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_terminal_runtime import scheduled,run,verify
from .test_lazy_dispatcher import observe_original_operations as observe_original_operations
from .test_run_broker import broker_stack as broker_stack
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries,deadline


def identity(path):
    st=path.stat();return [st.st_dev,st.st_ino]


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize('fault',['storage-stall','storage-death','source-root-loss','evidence-root-loss'])
def test_original_post_collection_loss_retains_unknown_ack_and_original_cleanup(request,monkeypatch,fault):
    stack,_,driver=scheduled(request,monkeypatch);broker,_,client,work=stack
    root=work.parent/'argus';actual_root=root;observations=[];closed=None;result=None
    pins=dict(original_admission=json.loads(client.coverage.public_bytes),admission_digest=client.coverage_digest,
        original_collection=json.loads(client.collection.canonical_bytes),generation_ns=client.generation_ns,
        runtime_digest=runtime_admission_digest(client.coverage,client.collection,client.generation_ns),
        original_fixture=str(work.parent),source_sha256=digest(Path(__file__)))
    output=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if output:
        target=Path(output);target.mkdir(parents=True,exist_ok=True)
        with (target/('loss-original-inputs-'+fault+'.json')).open('x') as f:json.dump(pins,f,indent=2);f.write('\n')
    original=PersistenceClient.finish_run

    def lose(self,owner,end):
        nonlocal actual_root
        if self is not client:return original(self,owner,end)
        assert owner is broker and not observations
        assert self._collection_outcome is not None and self._collection_outcome[0] is broker
        collection=self._collection_outcome[2].public_data();assert collection['collectionComplete']
        rows=EvidenceStore.read_run(root).records()
        terminal=[e for e in rows if e.get('extensions',{}).get('xverse.maestro',{}).get('action')=='run-terminal']
        assert len(terminal)==1 and terminal[0]['extensions']['xverse.maestro']['outcome']=='succeeded'
        assert driver.teardown._result.unit_cleanup_complete and driver.teardown._result.normal_records_complete
        before=dict(fault=fault,original_report_end=[end.session,end.monotonic_seconds],
            before_manifest_sha256=digest(root/'manifest.json'),before_evidence_identity=identity(root),
            before_source_identity=identity(work),before_m3_sha256=digest(work.parent/'m3.jsonl'),
            before_events_sha256=digest(root/'events.jsonl'),collection=collection,
            original_terminal_event=terminal[0],original_helper_retained=self.process is self._pins[0],
            observed_at=time.monotonic(),nonconsuming_signal_observation=None,
            retained_source_path=None,retained_evidence_path=str(root))
        observations.append(before)
        if fault in ('storage-stall','storage-death'):
            child=self.process;child._holder();fd=child._capability.fileno()
            signum=signal.SIGSTOP if fault=='storage-stall' else signal.SIGKILL
            signal.pidfd_send_signal(fd,signum)
            # This observes only the original pidfd; it does not consume exit
            # status or substitute a PID/path for signal or cleanup ownership.
            until=min(end.monotonic_seconds,time.monotonic()+.1);observed=None
            while time.monotonic()<until:
                flags=os.WSTOPPED if fault=='storage-stall' else os.WEXITED
                observed=os.waitid(os.P_PIDFD,fd,flags|os.WNOHANG|os.WNOWAIT)
                if observed is not None:break
                select.select([],[],[],.001)
            assert observed is not None
            assert observed.si_code==(os.CLD_STOPPED if fault=='storage-stall' else os.CLD_KILLED)
            assert observed.si_status==signum
            before['nonconsuming_signal_observation']=dict(code=observed.si_code,status=observed.si_status)
        elif fault=='source-root-loss':
            retained=work.with_name('source-retained-after-loss');assert not retained.exists()
            work.rename(retained)
            assert not work.exists() and identity(retained)==before['before_source_identity']
            before['retained_source_path']=str(retained)
        else:
            retained=root.with_name('evidence-retained-after-loss');assert not retained.exists()
            root.rename(retained);actual_root=retained
            assert not root.exists() and identity(retained)==before['before_evidence_identity']
            before['retained_evidence_path']=str(retained)
        before['injection_completed_at']=time.monotonic()
        return original(self,owner,end)

    monkeypatch.setattr(PersistenceClient,'finish_run',lose)
    no_replay=False
    try:
        result=run(driver)
        assert len(observations)==1,'original post-collection fault boundary not reached'
        assert result.execution_succeeded and result.terminal_recorded,result.diagnostic
        assert result.terminal is not None,result.diagnostic
        facts=result.terminal.public_data()
        assert facts['report'] is None and facts['writer'] is None and facts['diagnostic'] is not None,facts
        assert facts['lastAcknowledgedWriterState']==client.last_writer_state=='open'
        assert client._failed and client.latch.cancelled and not client._aborted
        assert facts['storageDrain']['worker_reaped'] and facts['storageDrain']['returncode'] is not None,facts
        assert not result.lifecycle_complete and not result.terminal.lifecycle_complete
        assert result.collection is client._collection_outcome[2] and result.collection.public_data()['collectionComplete']
        before=observations[0];assert client._terminal_outcome[1]==tuple(before['original_report_end'])
        assert digest(actual_root/'manifest.json')==before['before_manifest_sha256']
        assert EvidenceStore.read_run(actual_root).manifest['writerState']=='open'
        checked=verify(client,actual_root)
        assert not checked.complete and not checked.collection_verified and not checked.collection_complete
        sequence=client._sequence
        with monkeypatch.context() as patch:
            patch.setattr(PersistenceClient,'_rpc',lambda *a,**kw:pytest.fail('writer RPC after original unknown terminal result'))
            assert original(client,broker,HostDeadline(*before['original_report_end'])) is result.terminal
            closed=RunClosure(broker.session,dispatcher=driver).close(deadline(6))
        no_replay=True
        assert client._sequence==sequence and not client._closure_attempted
        assert closed.cleanup_complete and closed.root_reaped and closed.normal_unit_records_complete,closed
        assert closed.terminal_reports==(result.terminal,) and not closed.writers
        assert {h.role for h in closed.helpers}=={3,4,5} and all(h.process_reaped for h in closed.helpers)
        assert all(b.empty and b.released for b in closed.boundaries)
        assert 'ML-CLOSURE-REPORT-INCOMPLETE' in closed.diagnostics
        assert not closed.lifecycle_complete and not closed.ready_for_execution
        assert digest(actual_root/'manifest.json')==before['before_manifest_sha256']
        assert digest(actual_root/'events.jsonl')==before['before_events_sha256']
        assert digest(work.parent/'m3.jsonl')==before['before_m3_sha256']
        assert identity(actual_root)==before['before_evidence_identity']
        if fault=='source-root-loss':assert not work.exists()
        if fault=='evidence-root-loss':assert not root.exists()
    finally:
        if output:
            closure=asdict(closed) if closed is not None else None
            if closure is not None:closure['terminal_reports']=[r.public_data() for r in closed.terminal_reports]
            row=dict(fault=fault,observations=observations,receipt=result.terminal.public_data() if result and result.terminal else None,
                diagnostic=result.diagnostic if result else None,execution_succeeded=result.execution_succeeded if result else None,
                terminal_recorded=result.terminal_recorded if result else None,closure=closure,
                original_fixture=str(work.parent),actual_evidence_root=str(actual_root),original_evidence_root=str(root),
                public_m3=list(FileEvidenceJournal(work.parent/'m3.jsonl').public_records()),
                argus_events=EvidenceStore.read_run(actual_root).records(),source_sha256=digest(Path(__file__)),
                no_writer_rpc_replay=no_replay,original_bounds_preserved=True,
                original_evidence_path_missing=not root.exists(),original_source_path_missing=not work.exists(),
                full_TR06_complete=False,full_M1_complete=False,scientific_result=False)
            with (target/('loss-outcome-'+fault+'.json')).open('x') as f:json.dump(row,f,indent=2);f.write('\n')
