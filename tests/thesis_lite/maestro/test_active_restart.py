"""Actual explicit restart on the original blocking v6 finite coordinator."""
from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import threading

import pytest
from xverse.maestro.dispatcher import RestartRequest
from xverse.maestro.run_closure import RunClosure
from xverse.maestro.runtime_verification import runtime_admission_digest
from xverse.maestro.time import HostDeadline
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_terminal_controller_inventory import scheduled
from .test_terminal_runtime import run, verify
from .test_lazy_dispatcher import observe_original_operations as observe_original_operations
from .test_run_broker import broker_stack as broker_stack
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as original_binaries, deadline


@pytest.fixture(scope='module')
def binaries(tmp_path_factory,original_binaries):
    root=tmp_path_factory.mktemp('current-generation-marker')
    source=Path(__file__).with_name('catalog_workload_current.c')
    binary=root/'workload'
    argv=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(source),'-o',str(binary)]
    completed=subprocess.run(argv,capture_output=True,timeout=30)
    assert completed.returncode==0,completed.stderr
    output=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if output:
        path=Path(output);path.mkdir(parents=True,exist_ok=True)
        (path/'current-workload.bin').write_bytes(binary.read_bytes())
        (path/'current-workload.json').write_text(json.dumps(dict(command=argv,returncode=0,
            source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest()))+'\n')
    return dict(original_binaries,workload=binary)


@pytest.mark.parametrize('mode',['leaf','external-thread','parent-reject','controller-loss','stage-storage-loss'])
def test_original_active_explicit_restart_and_closed_generation_universe(request,monkeypatch,mode):
    successful=mode in ('leaf','external-thread')
    stack,controller,driver=scheduled(request,monkeypatch,restarts=True,restart_leaf_artifact=successful)
    broker,facade,client,work=stack
    assert driver.plan.operation_seconds==.5 and driver.plan.active_seconds==5.8
    assert driver.plan.restart_operation_seconds==1.0
    source,leaf=driver.prepared.resource_order
    unit=source if mode=='parent-reject' else leaf
    context=next(c for c in client._future_contexts if c.binding.unit_id==unit)
    other=next(c for c in client._future_contexts if c.binding.unit_id!=unit)
    original_worker=client.process
    tickets=[];old_handles={};execution_threads=[];retired=None;result=None;closed=None
    statement=driver._statement
    def enqueue(kind,step,**kw):
        response=statement(kind,step,**kw)
        if kind=='step-complete' and step.step_id=='observe-sink':
            old_handles.update({u:broker.issuer(u)._handle for u in (source,leaf)})
            end=HostDeadline(client.session,driver._active_end)
            with pytest.raises(ValueError,match='RESTART-PERMIT'):
                driver.restart(client.run_id,unit,permit=replace(context.binding.permit),generation=2,deadline=end)
            with pytest.raises(ValueError,match='RESTART-INPUT'):
                driver.restart(client.run_id,unit,permit=context.binding.permit,generation=True,deadline=end)
            submitted=[];submit_errors=[]
            def submit():
                try:submitted.append(driver.restart(client.run_id,unit,permit=context.binding.permit,generation=2,deadline=end))
                except BaseException as e:submit_errors.append(e)
            if mode=='external-thread':
                thread=threading.Thread(target=submit);thread.start();thread.join(.2)
                assert not thread.is_alive() and not submit_errors,submit_errors
                assert thread.ident!=broker.owner._dispatch_thread
            else:submit()
            assert not submit_errors and len(submitted)==1,submit_errors
            ticket=submitted[0]
            tickets.append(ticket)
            assert driver.restart(client.run_id,unit,permit=context.binding.permit,generation=2,deadline=end) is ticket
            assert driver.restart_result(ticket) is None
            with pytest.raises(ValueError,match='RESTART-ORIGINAL'):
                driver.restart_result(RestartRequest(ticket.run_id,ticket.unit_id,ticket.generation,ticket.deadline))
            with pytest.raises(ValueError,match='RESTART-CONFLICT'):
                driver.restart(client.run_id,other.binding.unit_id,permit=other.binding.permit,generation=2,deadline=end)
            if mode=='controller-loss':
                signal.pidfd_send_signal(controller.process._capability.fileno(),signal.SIGKILL)
        return response
    monkeypatch.setattr(driver,'_statement',enqueue)
    prepare=broker._prepare_generation
    def original_prepare(*a,**kw):
        execution_threads.append((threading.get_ident(),broker.owner._dispatch_thread))
        return prepare(*a,**kw)
    monkeypatch.setattr(broker,'_prepare_generation',original_prepare)
    advance=broker.advance_generation
    def native_advance(*a,**kw):
        issuer=advance(*a,**kw)
        if mode=='stage-storage-loss':
            signal.pidfd_send_signal(client.process._capability.fileno(),signal.SIGSTOP)
        return issuer
    monkeypatch.setattr(broker,'advance_generation',native_advance)
    target=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if target:
        path=Path(target);path.mkdir(parents=True,exist_ok=True)
        with (path/('active-restart-inputs-'+mode+'.json')).open('x') as f:
            json.dump(dict(original_admission=json.loads(client.coverage.public_bytes),
                admission_digest=client.coverage_digest,original_collection=json.loads(client.collection.canonical_bytes),
                original_schedule=json.loads(client.schedule.canonical_bytes),
                generation_ns=client.generation_ns,runtime_digest=runtime_admission_digest(client.coverage,client.collection,client.generation_ns),
                original_fixture=str(work.parent),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),f,indent=2)
            f.write('\n')
    try:
        result=run(driver)
        assert len(tickets)==1,result.diagnostic
        outcome=driver.restart_result(tickets[0])
        assert outcome is not None
        records=FileEvidenceJournal(work.parent/'m3.jsonl').records
        if successful:
            assert outcome.disposition=='completed',outcome
            assert result.execution_succeeded and result.terminal_recorded,result.diagnostic
            assert result.terminal.public_data()['report']['eligible'],result.terminal.public_data()
            checked=verify(client,work.parent/'argus');assert checked.complete,checked
            assert {r.details['generation'] for r in records}=={1,2}
            assert execution_threads and all(a==b for a,b in execution_threads)
            assert broker.issuer(leaf)._handle is not old_handles[leaf]
            assert broker.issuer(source)._handle is old_handles[source]
            assert broker.issuer(leaf)._handle.execution_id==context.binding.execution_id==outcome.execution_id
            assert len(driver._teardown_history)==1
            assert driver._teardown_history[0]._cleaned[leaf].generation==1
            assert driver.teardown._cleaned[leaf].generation==2
            output=next(d.destination for d in client.collection.declarations if d.unit_id==leaf)
            assert (work.parent/'argus'/output).read_bytes()==b'EXEC\n'
        elif mode=='parent-reject':
            assert outcome.disposition=='rejected' and outcome.diagnostic=='ML-GENERATION-DEPENDENTS',outcome
            assert result.execution_succeeded and result.terminal_recorded,result.diagnostic
            assert verify(client,work.parent/'argus').complete
            assert {r.details['generation'] for r in records}=={1}
            assert not execution_threads and not driver._teardown_history
        else:
            assert outcome.disposition=='failed' and not result.execution_succeeded,outcome
            assert broker.owner.latch.cancelled
            assert bool(execution_threads) is (mode=='stage-storage-loss')
        assert client.process is original_worker
        assert sum(s.phase=='start' for s in driver.prepared.steps)==2
        assert len(driver.prepared.steps)==10 and len(driver._outcomes)==10
        consumed=FileEvidenceJournal(work.parent/'m3.jsonl').permit_consumed(context.binding.permit.permit_id,context.binding.permit.nonce)
        assert consumed is (successful or mode=='stage-storage-loss')
        closed=RunClosure(broker.session,dispatcher=driver).close(deadline(6))
        assert closed.root_reaped,closed
        if mode=='stage-storage-loss':
            assert not closed.cleanup_complete and 'ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN' in closed.diagnostics
            unknown=[u for u in closed.native_units if u.unit_id==leaf and u.generation==2]
            assert len(unknown)==1 and unknown[0].issued is None and unknown[0].direct_child_reaped is None
        else:assert closed.cleanup_complete,closed
        assert all(h.process_reaped for h in closed.helpers)
        assert all(b.empty and b.released for b in closed.boundaries)
        assert not closed.lifecycle_complete and not closed.ready_for_execution
    finally:
        if target:
            path=Path(target);path.mkdir(parents=True,exist_ok=True)
            # Failures retain original observations; no substitute closure result.
            row=dict(mode=mode,original_fixture=str(work.parent),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                tickets=[asdict(t) for t in tickets],restart_results=[asdict(driver.restart_result(t)) if driver.restart_result(t) else None for t in tickets],
                diagnostic=result.diagnostic if result else None,
                terminal=result.terminal.public_data() if result and result.terminal else None,
                public_m3=FileEvidenceJournal(work.parent/'m3.jsonl').public_records(),
                old_handles={u:asdict(h) for u,h in old_handles.items()},execution_threads=execution_threads,
                closure={**asdict(closed),'terminal_reports':[t.public_data() for t in closed.terminal_reports]} if closed else None,
                restart_operation_seconds=driver.plan.restart_operation_seconds,
                scheduled_operation_seconds=driver.plan.operation_seconds,active_seconds=driver.plan.active_seconds,
                original_deadlines_preserved=True,full_selected_increment17_complete=False,scientific_result=False)
            with (path/('active-restart-'+mode+'.json')).open('x') as f:json.dump(row,f,indent=2);f.write('\n')
