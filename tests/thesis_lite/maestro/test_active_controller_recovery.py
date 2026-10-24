"""Original active coordinator, genuine replacement and productive generations."""
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
from xverse.maestro.controller import ControllerSession
from xverse.maestro.persistence import PersistenceClient
from xverse.maestro.providers import ProcessReadiness
from xverse.maestro.recovery import IssuerRecovery
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
def binaries(tmp_path_factory, original_binaries):
    root=tmp_path_factory.mktemp('recovery-current-marker')
    source=Path(__file__).with_name('catalog_workload_current.c');binary=root/'workload'
    argv=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(source),'-o',str(binary)]
    compiled=subprocess.run(argv,capture_output=True,timeout=30);assert compiled.returncode==0,compiled.stderr
    out=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if out:
        target=Path(out);target.mkdir(parents=True,exist_ok=True)
        (target/'recovery-workload.bin').write_bytes(binary.read_bytes())
        (target/'recovery-workload.json').write_text(json.dumps(dict(command=argv,returncode=0,
            source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest()))+'\n')
    return dict(original_binaries,workload=binary)


@pytest.mark.parametrize('mode',['before-start','mixed-initial','planned','dead-before-drain','heartbeat-race','generation2','restart-after','stopped-then-recovery','cleaned-then-restart','snapshot-loss'])
def test_original_active_replacement_retains_owner_writer_and_productive_access(request,monkeypatch,mode):
    names=('terminal-instance',) if mode in ('generation2','restart-after','cleaned-then-restart') else ()
    stack,old,driver=scheduled(request,monkeypatch,restarts=True,transitive=True,
        restart_artifact_names=names,controller_recovery=True)
    broker,facade,client,work=stack
    assert driver.plan.recovery_operation_seconds==3 and driver.plan.active_seconds==20
    assert json.loads(driver.plan.canonical_bytes)['version']==5
    leaf=next(u.unit_id for u in driver.prepared.units if u.unit_id.endswith('/terminal-instance'))
    future=next(c for c in client._future_contexts if c.binding.unit_id==leaf)
    conflict_context=next(c for c in client._future_contexts if c.binding.unit_id!=leaf)
    original_worker=client.process;original_authority=broker.connection.child
    tickets=[];restarts=[];handles={};borrowed=[];threads=[];new_probes={};productive=[]
    result=closure=None
    race_ready=[]
    expected_states={}
    def enqueue():
        if tickets:return
        handles.update({i.unit_id:i._handle for i in broker.issuers if i._handle is not None})
        end=HostDeadline(client.session,driver._active_end)
        before=FileEvidenceJournal(work.parent/'m3.jsonl').records;sequence=client._sequence
        contexts=client.coverage.data(client.coverage_digest)['contexts']
        for issuer in broker.issuers:
            if issuer.unit_id not in handles:
                expected_states[issuer.unit_id]='never-issued'
                continue
            generation=next(c['generation'] for c in contexts if c['executionId']==handles[issuer.unit_id].execution_id)
            terminal=[r.status for r in before if r.kind=='outcome' and r.status in ('stopped','cleaned')
                      and r.details.get('maestroUnitId')==issuer.unit_id and r.details.get('generation')==generation]
            expected_states[issuer.unit_id]=('released' if terminal[-1]=='cleaned' else 'stopped') if terminal else 'owned'
        def submit():
            threads.append((threading.get_ident(),broker.owner._dispatch_thread))
            ticket=driver.replace_controller(client.run_id,session_id='active-successor-'+mode,deadline=end)
            tickets.append(ticket)
            assert driver.replace_controller(client.run_id,session_id=ticket.session_id,deadline=end) is ticket
            with pytest.raises(ValueError,match='RECOVERY-ORIGINAL'):
                driver.controller_recovery_result(replace(ticket))
            with pytest.raises(ValueError,match='RECOVERY-CONFLICT'):
                driver.replace_controller(client.run_id,session_id='conflicting-controller',deadline=end)
            with pytest.raises(ValueError,match='RESTART-CONFLICT'):
                driver.restart(client.run_id,conflict_context.binding.unit_id,
                    permit=conflict_context.binding.permit,generation=2,deadline=end)
        if mode in ('dead-before-drain','heartbeat-race'):
            errors=[]
            def external():
                try:submit()
                except BaseException as e:errors.append(e)
            thread=threading.Thread(target=external);thread.start();thread.join(2)
            assert not thread.is_alive() and not errors,errors
            signal.pidfd_send_signal(old.process._capability.fileno(),signal.SIGKILL)
        else:submit()
        assert FileEvidenceJournal(work.parent/'m3.jsonl').records==before and client._sequence==sequence
        assert driver.controller_recovery_result(tickets[0]) is None
    statement=driver._statement
    def after_statement(kind,step,**kw):
        reply=statement(kind,step,**kw)
        observed=sum(s.phase=='observe' and s.step_id in driver._outcomes for s in driver.prepared.steps)
        if mode=='heartbeat-race':
            if kind=='step-complete' and step.phase=='start' and sum(s.phase=='start' and s.step_id in driver._outcomes for s in driver.prepared.steps)==3:
                race_ready.append(True)
            if race_ready and not tickets:
                # Hold the schedule (bounded) until the old controller's first lease-renewal heartbeat, which
                # enqueues the replacement; a fast persistence path would otherwise end before any renewal
                # (stabilization S1a finding 10).
                import time as _time
                _time.sleep(.25)
            return reply
        if mode=='before-start':
            trigger=step.phase=='prepare' and not broker.owner._claims
        elif mode=='mixed-initial':
            trigger=step.phase=='start' and sum(s.phase=='start' and s.step_id in driver._outcomes for s in driver.prepared.steps)==0
        elif mode=='stopped-then-recovery':
            trigger=step.step_id=='stop-terminal'
        else:
            trigger=step.step_id=='cleanup-terminal' if mode=='cleaned-then-restart' else step.phase=='observe' and observed==3
        if kind=='step-complete' and trigger and not tickets and not restarts:
            if mode=='generation2':
                restarts.append(driver.restart(client.run_id,leaf,permit=future.binding.permit,generation=2,
                    deadline=HostDeadline(client.session,driver._active_end)))
            else:enqueue()
        return reply
    monkeypatch.setattr(driver,'_statement',after_statement)
    drain_restart=driver._drain_restart
    def after_restart():
        changed=drain_restart()
        if mode=='generation2' and restarts and driver.restart_result(restarts[0]) is not None:enqueue()
        return changed
    monkeypatch.setattr(driver,'_drain_restart',after_restart)
    drain_recovery=driver._drain_controller_recovery
    def after_recovery():
        changed=drain_recovery()
        if mode in ('restart-after','cleaned-then-restart') and tickets and not restarts:
            outcome=driver.controller_recovery_result(tickets[0])
            if outcome and outcome.disposition=='completed':
                restarts.append(driver.restart(client.run_id,leaf,permit=future.binding.permit,generation=2,
                    deadline=HostDeadline(client.session,driver._active_end)))
        return changed
    monkeypatch.setattr(driver,'_drain_controller_recovery',after_recovery)
    reconcile=ControllerSession.reconcile
    def borrowed_reconcile(controller,policies,active,cleanup,**kw):
        assert kw['_coordinator'] is driver and kw['_request'] is tickets[0]
        assert broker.owner._dispatch_owner is driver and broker.owner._dispatch_thread==threading.get_ident()
        before=broker.owner._view_epoch
        with pytest.raises(ValueError,match='COORDINATOR'):
            IssuerRecovery(broker.session,broker.owner,policies=policies,controller=controller,
                _coordinator=object(),_request=tickets[0])
        assert broker.owner._view_epoch==before
        try:return reconcile(controller,policies,active,cleanup,**kw)
        finally:
            borrowed.append(dict(end=active.monotonic_seconds,owner_retained=broker.owner._dispatch_owner is driver,
                thread_retained=broker.owner._dispatch_thread==threading.get_ident(),new_session=controller.session_id))
            assert borrowed[-1]['owner_retained'] and borrowed[-1]['thread_retained']
            if controller._view is not None:
                new_probes.update({u:asdict(v) for u,v in controller._view._observations.items()})
    monkeypatch.setattr(ControllerSession,'reconcile',borrowed_reconcile)
    snapshot=PersistenceClient.reconcile_snapshot
    def original_snapshot(self,*a,**kw):
        if self is client and mode=='snapshot-loss':
            signal.pidfd_send_signal(self.process._capability.fileno(),signal.SIGSTOP)
        return snapshot(self,*a,**kw)
    monkeypatch.setattr(PersistenceClient,'reconcile_snapshot',original_snapshot)
    controller_request=ControllerSession.request
    def observed_request(controller,unit,phase,end):
        if mode=='heartbeat-race' and race_ready and controller is old and phase=='heartbeat' and not tickets:
            enqueue()
        value=controller_request(controller,unit,phase,end)
        if controller is not old and unit is not None:
            productive.append(dict(session=controller.session_id,unit=unit,phase=phase))
        return value
    monkeypatch.setattr(ControllerSession,'request',observed_request)
    output=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if output:
        target=Path(output);target.mkdir(parents=True,exist_ok=True)
        with (target/('active-recovery-inputs-'+mode+'.json')).open('x') as f:
            json.dump(dict(original_admission=json.loads(client.coverage.public_bytes),admission_digest=client.coverage_digest,
                original_collection=json.loads(client.collection.canonical_bytes),original_schedule=json.loads(client.schedule.canonical_bytes),
                generation_ns=client.generation_ns,runtime_digest=runtime_admission_digest(client.coverage,client.collection,client.generation_ns),
                original_fixture=str(work.parent),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),f,indent=2);f.write('\n')
    try:
        result=run(driver)
        assert len(tickets)==1 and len(broker._controllers)==2,result.diagnostic
        outcome=driver.controller_recovery_result(tickets[0]);assert outcome is not None
        assert old._retirement.original_child_dead and old._retirement.original_child_reaped and old._retirement.own_boundary_released
        assert client.process is original_worker and broker.connection.child is original_authority
        assert broker.owner._dispatch_owner is None and borrowed
        if mode=='snapshot-loss':
            assert outcome.disposition=='failed' and not outcome.ordinary_reconciled and not result.execution_succeeded
            assert driver.facade is broker._current_controller._recovery._view
            assert not driver.facade._bindings and not driver.facade._released and not new_probes
            assert driver.facade._cleanup_only
            with pytest.raises(ValueError,match='NOT-OPEN'):
                ProcessReadiness(broker.owner,policies=driver.plan.policies)
            with pytest.raises(ValueError,match='CLEANUP-CAPABILITY'):
                ProcessReadiness(broker.owner,policies=driver.plan.policies,_cleanup_recovery=object())
            with pytest.raises(ValueError,match='CLEANUP-ONLY'):
                driver.facade.bind(broker.issuer(leaf),handles[leaf])
            with pytest.raises(ValueError,match='CLEANUP-ONLY'):
                driver.facade.check_health(deadline(.5),force=True)
            with pytest.raises(ValueError):broker._current_controller._start_access()
        else:
            assert outcome.disposition=='completed' and outcome.ordinary_reconciled,outcome
            assert result.execution_succeeded and result.terminal_recorded,result.diagnostic
            assert driver._controller is broker._current_controller and driver.facade is driver._controller._view
            assert verify(client,work.parent/'argus').complete
            assert result.terminal.public_data()['report']['eligible']
            if mode!='heartbeat-race':assert productive
            with pytest.raises(ValueError,match='STALE-VIEW'):facade.check_health(deadline(.5),force=True)
            with pytest.raises(ValueError):old.request(None,'heartbeat',deadline(.5))
            reconciliation=driver._controller._recovery._result
            assert {r.unit_id:r.status for r in reconciliation.units}==expected_states
            assert all(r.native_running is (True if r.status=='owned' else None if r.status=='never-issued' else False) for r in reconciliation.units)
            assert set(new_probes)=={u for u,state in expected_states.items() if state=='owned'}
            contexts=client.coverage.data(client.coverage_digest)['contexts']
            assert all(v['generation']==next(c['generation'] for c in contexts
                       if c['unitId']==u and c['executionId']==handles[u].execution_id) for u,v in new_probes.items())
            if mode in ('dead-before-drain','heartbeat-race'):assert threads[0][0]!=threads[0][1]
            if mode in ('generation2','restart-after','cleaned-then-restart'):
                assert len(restarts)==1 and driver.restart_result(restarts[0]).disposition=='completed'
                assert broker.issuer(leaf)._handle.execution_id==future.binding.execution_id
                if mode=='generation2':assert handles[leaf] is broker.issuer(leaf)._handle
            for declaration in client.collection.declarations:
                assert (work.parent/'argus'/declaration.destination).read_bytes()==b'EXEC\n'
        closure=RunClosure(broker.session,dispatcher=driver).close(deadline(6))
        assert closure.root_reaped and all(h.process_reaped for h in closure.helpers)
        assert len([h for h in closure.helpers if h.role==5])==2
        assert all(b.empty and b.released for b in closure.boundaries)
        if mode=='snapshot-loss':
            assert closure.cleanup_complete and not closure.normal_unit_records_complete
            assert all(n.issued and n.direct_child_reaped and n.native_retired for n in closure.native_units)
        else:assert closure.cleanup_complete and closure.normal_unit_records_complete
        assert not closure.lifecycle_complete and not closure.ready_for_execution
    finally:
        if output:
            with (Path(output)/('active-recovery-'+mode+'.json')).open('x') as f:
                json.dump(dict(mode=mode,tickets=[asdict(t) for t in tickets],
                    outcomes=[asdict(driver.controller_recovery_result(t)) if driver.controller_recovery_result(t) else None for t in tickets],
                    handles={u:asdict(h) for u,h in handles.items()},expected_states=expected_states,
                    reconciliation=asdict(broker._current_controller._recovery._result) if broker._current_controller._recovery is not None and broker._current_controller._recovery._result is not None else None,
                    borrowed=borrowed,new_probes=new_probes,
                    productive=productive,threads=threads,original_fixture=str(work.parent),
                    old_retirement=asdict(old._retirement) if old._retirement else None,
                    public_m3=FileEvidenceJournal(work.parent/'m3.jsonl').public_records(),
                    diagnostic=result.diagnostic if result else None,terminal=result.terminal.public_data() if result and result.terminal else None,
                    closure={**asdict(closure),'terminal_reports':[r.public_data() for r in closure.terminal_reports]} if closure else None,
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),full_increment17_complete=False),f,indent=2);f.write('\n')


def test_readiness_window_records_survive_an_active_controller_recovery(request, monkeypatch):
    """S1b review finding 26 LOW-1 (thesis DR-17, ADR-ML3-PROBE-0001 S1b-1 revision L1): ``_commit_controller_view``
    replaces the dispatcher's facade with the recovery's new ProcessReadiness view, whose window list starts empty.
    The records made before the recovery must still be in ``DispatchResult.readiness_windows``, in order, and in the
    committed view. This stack declares ``running`` probes only, so each start of the original facade adds one
    ``ReadinessWindow`` of the shape a marker start records (the carrying under test does not depend on how a
    record was made); the recovery is the 'planned' one of the test above (after the third observation)."""
    from xverse.maestro.providers import ReadinessWindow
    stack, old, driver = scheduled(request, monkeypatch, restarts=True, transitive=True, controller_recovery=True)
    broker, facade, client, work = stack
    made, tickets = [], []
    original_start = ProcessReadiness.start

    def start(self, unit_id, descriptor, gate, deadline):
        value = original_start(self, unit_id, descriptor, gate, deadline)
        if self is facade:
            record = ReadinessWindow(unit_id, descriptor.generation, 1.5, 1.5 - .25 * len(made),
                                     broker.session._lease / 1e9, time.monotonic(), bool(made))
            self._windows.append(record)
            made.append(record)
        return value

    monkeypatch.setattr(ProcessReadiness, 'start', start)
    statement = driver._statement

    def after_statement(kind, step, **kw):
        reply = statement(kind, step, **kw)
        observed = sum(s.phase == 'observe' and s.step_id in driver._outcomes for s in driver.prepared.steps)
        if kind == 'step-complete' and step.phase == 'observe' and observed == 3 and not tickets:
            tickets.append(driver.replace_controller(client.run_id, session_id='window-successor',
                                                     deadline=HostDeadline(client.session, driver._active_end)))
        return reply

    monkeypatch.setattr(driver, '_statement', after_statement)
    result = run(driver)
    assert len(tickets) == 1, result.diagnostic
    outcome = driver.controller_recovery_result(tickets[0])
    assert outcome is not None and outcome.disposition == 'completed' and outcome.ordinary_reconciled, outcome
    assert result.execution_succeeded and result.terminal_recorded, result.diagnostic
    assert driver.facade is not facade and driver.facade is driver._controller._view  # the view was committed
    assert len(made) >= 2, made  # records made by the original facade before the recovery
    assert result.readiness_windows[:len(made)] == tuple(made), (result.readiness_windows, made)
    assert tuple(driver.facade._windows[:len(made)]) == tuple(made)
    assert len(result.readiness_windows) == len(made)  # running-only view: no record added after the recovery
    closure = RunClosure(broker.session, dispatcher=driver).close(deadline(6))
    assert closure.root_reaped and closure.cleanup_complete


def test_readiness_window_records_are_not_duplicated_by_a_cleanup_only_recommit(request, monkeypatch):
    """S1b review finding 28 LOW-1 (finding 29): a recovery whose ordinary commit succeeds but which then fails (the
    post-commit ML-SCHEDULE-RECOVERY-INCOMPLETE check) re-commits the same view cleanup-only. The L1 carry must not
    prepend the records a second time: one record per start of the original facade (reviewer probe of finding 28)."""
    from xverse.maestro.dispatcher import FiniteDispatcher
    from xverse.maestro.owner import OwnerError
    from xverse.maestro.providers import ReadinessWindow
    stack, old, driver = scheduled(request, monkeypatch, restarts=True, transitive=True, controller_recovery=True)
    broker, facade, client, work = stack
    made, tickets, commits = [], [], []
    original_start = ProcessReadiness.start

    def start(self, unit_id, descriptor, gate, deadline):
        value = original_start(self, unit_id, descriptor, gate, deadline)
        if self is facade:
            record = ReadinessWindow(unit_id, descriptor.generation, 1.5, 1.5, broker.session._lease / 1e9,
                                     time.monotonic(), False)
            self._windows.append(record)
            made.append(record)
        return value

    monkeypatch.setattr(ProcessReadiness, 'start', start)
    original_commit = FiniteDispatcher._commit_controller_view

    def commit(self, controller, ticket, *, cleanup_only=False):
        original_commit(self, controller, ticket, cleanup_only=cleanup_only)
        commits.append((cleanup_only, id(self.facade)))
        if not cleanup_only:  # stands in for the post-commit ML-SCHEDULE-RECOVERY-INCOMPLETE check
            raise OwnerError("ML-SCHEDULE-RECOVERY-INCOMPLETE")

    monkeypatch.setattr(FiniteDispatcher, '_commit_controller_view', commit)
    statement = driver._statement

    def after_statement(kind, step, **kw):
        reply = statement(kind, step, **kw)
        observed = sum(s.phase == 'observe' and s.step_id in driver._outcomes for s in driver.prepared.steps)
        if kind == 'step-complete' and step.phase == 'observe' and observed == 3 and not tickets:
            tickets.append(driver.replace_controller(client.run_id, session_id='window-successor',
                                                     deadline=HostDeadline(client.session, driver._active_end)))
        return reply

    monkeypatch.setattr(driver, '_statement', after_statement)
    result = run(driver)
    assert len(tickets) == 1 and len(made) >= 2, (tickets, made)
    assert [c[0] for c in commits] == [False, True] and commits[0][1] == commits[1][1], commits  # same view twice
    assert result.readiness_windows == tuple(made), (len(result.readiness_windows), len(made))
