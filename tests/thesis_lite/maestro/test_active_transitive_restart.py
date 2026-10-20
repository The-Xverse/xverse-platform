"""Original v6 transitive cohorts, normal released generations and terminal scope."""
from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import threading
import time

import pytest
from xverse.argus import EvidenceStore
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
    root=tmp_path_factory.mktemp('cohort-current-marker')
    source=Path(__file__).with_name('catalog_workload_current.c');binary=root/'workload'
    argv=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(source),'-o',str(binary)]
    result=subprocess.run(argv,capture_output=True,timeout=30);assert result.returncode==0,result.stderr
    directory=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if directory:
        output=Path(directory);output.mkdir(parents=True,exist_ok=True)
        (output/'cohort-workload.bin').write_bytes(binary.read_bytes())
        (output/'cohort-workload.json').write_text(json.dumps(dict(command=argv,returncode=0,
            source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest()))+'\n')
    return dict(original_binaries,workload=binary)


@pytest.mark.parametrize('mode',['cohort','omitted-dependent','mid-storage-loss','cleaned-leaf'])
def test_original_transitive_cohort_retains_unrelated_and_all_generations(request,monkeypatch,mode):
    names=() if mode=='omitted-dependent' else ('terminal-instance',) if mode=='cleaned-leaf' else (
        'source-instance','sink-instance','terminal-instance')
    stack,controller,driver=scheduled(request,monkeypatch,restarts=True,transitive=True,restart_artifact_names=names)
    broker,facade,client,work=stack
    named={u.unit_id.rsplit('/',1)[-1]:u.unit_id for u in driver.prepared.units}
    source,middle,leaf,unrelated=[named[n+'-instance'] for n in ('source','sink','terminal','unrelated')]
    assert driver.plan.use_action_timeouts and driver.plan.operation_seconds==.3
    assert driver.plan.active_seconds==20 and driver.plan.restart_operation_seconds==2
    assert driver.plan.per_unit_seconds==2 and len(driver.prepared.steps)==20
    contexts={c.binding.unit_id:c for c in client._future_contexts}
    chosen=(leaf,) if mode=='cleaned-leaf' else (source,middle) if mode=='omitted-dependent' else (source,middle,leaf)
    tickets=[];old_handles={};prepared_order=[];live_unrelated=[];result=None;closure=None
    statement_bounds=[]
    send=driver._send
    def observe_statement(kind,end,**values):
        if kind in ('step-dispatch','step-complete'):
            step=driver._steps[values['step']]
            cap=next(a.timeout_seconds for u in driver.prepared.units if u.unit_id==step.unit_id
                     for a in u.plan.actions if a.phase==step.phase)
            remaining=end.monotonic_seconds-time.monotonic()
            assert 0<remaining<=cap
            statement_bounds.append(dict(kind=kind,step=step.step_id,cap=cap,remaining=remaining,
                                         end=end.monotonic_seconds))
        return send(kind,end,**values)
    monkeypatch.setattr(driver,'_send',observe_statement)
    original_worker=client.process;statement=driver._statement
    def enqueue(kind,step,**kw):
        response=statement(kind,step,**kw)
        observed=sum(s.phase=='observe' and s.step_id in driver._outcomes for s in driver.prepared.steps)
        trigger=(step.step_id=='cleanup-terminal' if mode=='cleaned-leaf' else step.phase=='observe' and observed==3)
        if kind=='step-complete' and trigger and not tickets:
            old_handles.update({u:broker.issuer(u)._handle for u in named.values()})
            end=HostDeadline(client.session,driver._active_end)
            inputs=tuple((u,contexts[u].binding.permit,2) for u in chosen)
            before=FileEvidenceJournal(work.parent/'m3.jsonl').records
            with pytest.raises(ValueError,match='RESTART-INPUT'):
                driver.restart_many(client.run_id,(inputs[0],inputs[0]),deadline=end)
            with pytest.raises(ValueError,match='RESTART-PERMIT'):
                driver.restart_many(client.run_id,((chosen[0],replace(contexts[chosen[0]].binding.permit),2),),deadline=end)
            accepted=driver.restart_many(client.run_id,tuple(reversed(inputs)),deadline=end)
            assert tuple(t.unit_id for t in accepted)==chosen
            tickets.extend(accepted)
            assert tuple(driver.restart_many(client.run_id,inputs,deadline=end))==tuple(tickets)
            assert FileEvidenceJournal(work.parent/'m3.jsonl').records==before
            assert all(driver.restart_result(t) is None for t in tickets)
        return response
    monkeypatch.setattr(driver,'_statement',enqueue)
    prepare=broker._prepare_generation
    def original_prepare(teardown,unit,descriptor,end):
        assert threading.get_ident()==broker.owner._dispatch_thread
        assert broker.issuer(unrelated)._handle is old_handles[unrelated]
        assert unrelated in facade._released and unrelated not in driver.teardown._stopped
        live_unrelated.append(dict(unit=unit,handle=asdict(broker.issuer(unrelated)._handle),observed_at=__import__('time').monotonic()))
        prepared_order.append(unit)
        return prepare(teardown,unit,descriptor,end)
    monkeypatch.setattr(broker,'_prepare_generation',original_prepare)
    advance=broker.advance_generation
    def original_advance(prepared,end):
        issuer=advance(prepared,end)
        if mode=='mid-storage-loss' and issuer.unit_id==middle:
            signal.pidfd_send_signal(client.process._capability.fileno(),signal.SIGSTOP)
        return issuer
    monkeypatch.setattr(broker,'advance_generation',original_advance)
    output=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if output:
        out=Path(output);out.mkdir(parents=True,exist_ok=True)
        with (out/('cohort-inputs-'+mode+'.json')).open('x') as stream:
            json.dump(dict(original_admission=json.loads(client.coverage.public_bytes),admission_digest=client.coverage_digest,
                original_collection=json.loads(client.collection.canonical_bytes),original_schedule=json.loads(client.schedule.canonical_bytes),
                generation_ns=client.generation_ns,runtime_digest=runtime_admission_digest(client.coverage,client.collection,client.generation_ns),
                original_fixture=str(work.parent),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),stream,indent=2)
            stream.write('\n')
    try:
        result=run(driver)
        assert len(tickets)==len(chosen),result.diagnostic
        outcomes=[driver.restart_result(t) for t in tickets]
        assert all(r is not None for r in outcomes)
        records=FileEvidenceJournal(work.parent/'m3.jsonl').records
        if mode=='mid-storage-loss':
            assert [r.disposition for r in outcomes]==['completed','failed','cancelled'],outcomes
            assert prepared_order==[source,middle] and not result.execution_succeeded
        else:
            expected='rejected' if mode=='omitted-dependent' else 'completed'
            assert all(r.disposition==expected for r in outcomes),outcomes
            assert result.execution_succeeded and result.terminal_recorded,result.diagnostic
            completion=next(r for r in statement_bounds if r['kind']=='step-complete'
                            and r['step']=='cleanup-unrelated')
            assert driver.plan.operation_seconds<completion['remaining']<=completion['cap']==1
            checked=verify(client,work.parent/'argus');assert checked.complete,checked
            assert result.terminal.public_data()['report']['eligible']
            assert broker.issuer(unrelated)._handle is old_handles[unrelated]
            if mode=='omitted-dependent':
                assert not prepared_order and not driver._teardown_history
                assert {r.details['generation'] for r in records}=={1}
                assert all(r.diagnostic=='ML-GENERATION-DEPENDENTS' for r in outcomes)
            else:
                assert prepared_order==list(chosen)
                for unit in chosen:
                    assert broker.issuer(unit)._handle.execution_id==contexts[unit].binding.execution_id
                    assert broker.issuer(unit)._handle is not old_handles[unit]
                    for generation in (1,2):
                        cleaned=[r for r in records if r.details['maestroUnitId']==unit and r.details['generation']==generation
                                 and r.kind=='outcome' and r.status=='cleaned']
                        assert len(cleaned)==1
                if mode=='cohort':
                    old_clean=[r.details['maestroUnitId'] for r in records if r.kind=='outcome' and r.status=='cleaned'
                               and r.details['generation']==1 and r.details['maestroUnitId'] in chosen]
                    assert old_clean==[leaf,middle,source]
                    events=EvidenceStore.read_run(work.parent/'argus').records()
                    for unit,parents in ((middle,{source}),(leaf,{source,middle})):
                        ready=[e['extensions']['xverse.maestro'] for e in events if e.get('extensions',{}).get('xverse.maestro',{}).get('unitId')==unit
                               and e['extensions']['xverse.maestro'].get('generation')==2 and e['extensions']['xverse.maestro'].get('action')=='ready']
                        assert len(ready)==1 and {d['unitId'] for d in ready[0]['dependencies']}==parents
                        assert all(d['generation']==2 for d in ready[0]['dependencies'])
                else:
                    leaf_done=next(r.sequence for r in records if r.details['maestroUnitId']==leaf and r.details['generation']==2 and r.kind=='outcome' and r.status=='cleaned')
                    parent_stop=next(r.sequence for r in records if r.details['maestroUnitId']==middle and r.details['generation']==1 and r.kind=='intent' and r.action_id==broker.owner._unit(middle).plan.actions[3].action_id)
                    assert leaf_done<parent_stop
                for declaration in client.collection.declarations:
                    assert (work.parent/'argus'/declaration.destination).read_bytes()==b'EXEC\n'
        assert client.process is original_worker
        journal=FileEvidenceJournal(work.parent/'m3.jsonl')
        for unit,context in contexts.items():
            expected=unit in ((source,middle) if mode=='mid-storage-loss' else () if mode=='omitted-dependent' else chosen)
            assert journal.permit_consumed(context.binding.permit.permit_id,context.binding.permit.nonce) is expected
        closure=RunClosure(broker.session,dispatcher=driver).close(deadline(6))
        assert closure.root_reaped and all(h.process_reaped for h in closure.helpers)
        assert all(b.empty and b.released for b in closure.boundaries)
        if mode=='mid-storage-loss':
            assert not closure.cleanup_complete and 'ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN' in closure.diagnostics
        else:assert closure.cleanup_complete and closure.normal_unit_records_complete
        assert not closure.lifecycle_complete and not closure.ready_for_execution
    finally:
        if output:
            with (out/('cohort-'+mode+'.json')).open('x') as stream:
                json.dump(dict(mode=mode,chosen=chosen,unrelated=unrelated,prepared_order=prepared_order,live_unrelated=live_unrelated,
                    old_handles={u:asdict(h) for u,h in old_handles.items()},tickets=[asdict(t) for t in tickets],
                    outcomes=[asdict(driver.restart_result(t)) if driver.restart_result(t) else None for t in tickets],
                    statement_bounds=statement_bounds,
                    diagnostic=result.diagnostic if result else None,terminal=result.terminal.public_data() if result and result.terminal else None,
                    public_m3=FileEvidenceJournal(work.parent/'m3.jsonl').public_records(),original_fixture=str(work.parent),
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    closure={**asdict(closure),'terminal_reports':[r.public_data() for r in closure.terminal_reports]} if closure else None,
                    full_selected_increment17_complete=False,scientific_result=False),stream,indent=2)
                stream.write('\n')
