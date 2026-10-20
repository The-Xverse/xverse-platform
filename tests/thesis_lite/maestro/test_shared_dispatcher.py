"""Declared XDL five-phase scheduling on one actual native run authority."""
from dataclasses import asdict
import copy
import hashlib
import json
import os
from pathlib import Path
import signal
import time

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.dispatcher import FiniteDispatcher
from xverse.maestro.projection import Limits
from xverse.maestro.providers import ProbePolicy
from xverse.maestro.run_broker import RunBroker
from xverse.maestro.run_closure import RunClosure
from xverse.maestro.schedule_plan import admit_schedule
from xverse.maestro.time import HostDeadline
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_run_broker import broker_stack as broker_stack, stage_all
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


def scheduled(request, monkeypatch, *, pauses=1, implicit=False, restart_operation_seconds=None, transitive=False,
              recovery_operation_seconds=None):
    from . import test_launcher, test_run_broker
    original_docs = test_launcher.documents
    def documents():
        data = original_docs()
        scenario = data['scenario.json']['spec']
        template = scenario['steps'][0]
        definitions = [
            ('prepare-source','source','prepare',0,[]),
            ('prepare-sink','sink','prepare',0,[]),
            ('start-source','source','start',0,['prepare-source']),
            ('start-sink','sink','start',0,['prepare-sink','start-source']),
            ('observe-source','source','observe',1,['start-source']),
            ('observe-sink','sink','observe',1,['start-sink']),
            ('stop-sink','sink','stop',2,['observe-sink']),
            ('cleanup-sink','sink','cleanup',2,['stop-sink']),
            ('stop-source','source','stop',3,['observe-source']),
            ('cleanup-source','source','cleanup',3,['stop-source']),
        ]
        if transitive:
            definitions=[]
            for name,parent in (('source',None),('sink','source'),('terminal','sink'),('unrelated',None)):
                definitions.extend([
                    ('prepare-'+name,name,'prepare',0,[]),
                    ('start-'+name,name,'start',0,['prepare-'+name]+(['start-'+parent] if parent else [])),
                    ('observe-'+name,name,'observe',1,['start-'+name])])
            for tick,name in enumerate(('terminal','sink','source','unrelated'),2):
                definitions.extend([('stop-'+name,name,'stop',tick,['observe-'+name]),
                                    ('cleanup-'+name,name,'cleanup',tick,['stop-'+name])])
        if implicit:
            definitions = [row for row in definitions if row[2] not in ('stop','cleanup')]
        scenario['steps'] = []
        for name, unit, phase, tick, dependencies in definitions:
            step = copy.deepcopy(template)
            step['id'] = name
            step['targetRef']['element'] = unit+'-instance'
            step['actionKind'] = 'validate' if phase=='prepare' else phase
            step['action']['operation'] = step['actionKind']
            step['schedule']['at'] = tick
            ext = step['extensions']['io.xverse.experiment']
            ext['target']['element'] = name
            ext['phase'] = phase
            ext['dependsOn'] = dependencies
            scenario['steps'].append(step)
        return data
    monkeypatch.setattr(test_launcher, 'documents', documents)
    prepare = test_launcher.prepare_lifecycle
    monkeypatch.setattr(test_launcher, 'prepare_lifecycle',
        lambda *a, **kw: prepare(*a, limits=Limits(horizon_ticks=5 if transitive else 3), **kw))
    encode = test_launcher.encode_configuration
    def configuration(prepared, *a, **kw):
        # The admitted active window is created here, before worker init (~0.4 s) and
        # before the first schedule statement. Measured over 305 clean runs of this
        # fixture, the span after init-begin reaches p99 4.55 s; restart-capable runs
        # additionally spend their restart/recovery budget inside the same window, so a
        # 4.8 s window left no margin for ordinary jitter (finding 362, CAPA-222 class).
        # The window therefore reserves the explicit restart/recovery budgets; no
        # statement budget, lease, health cadence or product constant changes.
        base_active_seconds = 20 if transitive else 8 if pauses>1 else 4.8
        # Only the tight 4.8 s base window reserves the explicit restart/recovery budgets; the
        # 20 s transitive and 8 s paused windows hold ample margin and are asserted literally.
        reserved_seconds = ((restart_operation_seconds or 0)+(recovery_operation_seconds or 0)
                            if base_active_seconds == 4.8 else 0)
        plan = admit_schedule(prepared, policies=tuple(ProbePolicy(u.unit_id,5,5,0.5) for u in prepared.units),
            ticks=(0,)*pauses+((1,2,3,4,5) if transitive else (1,2,3)),
            active_seconds=base_active_seconds+reserved_seconds,
            operation_seconds=.3 if transitive else .5, per_unit_seconds=2 if transitive else 1,
            poll_seconds=.05, request_limit=1024, service_operation_count=4,
            restart_operation_seconds=restart_operation_seconds,use_action_timeouts=transitive,
            recovery_operation_seconds=recovery_operation_seconds)
        return encode(prepared, *a, schedule=plan, **kw)
    monkeypatch.setattr(test_launcher, 'encode_configuration', configuration)
    # The native facade must use precisely the original sealed schedule policies.
    facade = test_run_broker.ProcessReadiness
    monkeypatch.setattr(test_run_broker, 'ProcessReadiness',
        lambda owner, **kw: facade(owner, policies=owner.persistence.schedule.policies))
    admit = RunBroker.admit
    monkeypatch.setattr(RunBroker, 'admit', classmethod(
        lambda cls, *a, **kw: admit(*a, controller_sessions=1, **kw)))
    stack = request.getfixturevalue('broker_stack')
    broker, view, client, _ = stack
    controller = broker.admit_controller('scheduled-controller', deadline(1))
    stage_all(stack)
    driver = FiniteDispatcher(view, broker.session,
        gates=tuple((u.unit_id,broker.connection) for u in broker.owner._prepared.units),
        controller=controller)
    return stack, controller, driver


def run(driver):
    active = HostDeadline(driver.owner.session, time.monotonic()+driver.plan.active_seconds-0.05)
    terminal = HostDeadline(driver.owner.session, active.monotonic_seconds+driver.plan.terminal_reserve_seconds+0.01)
    return driver.run(active, terminal)


def retain(stack, result, closure, name):
    output = os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if output:
        work = stack[3]
        (Path(output)/('shared-dispatch-public-'+str(os.getpid())+'-'+name+'.json')).write_text(json.dumps(dict(
            dispatch=asdict(result), closure=asdict(closure),
            public_m3=FileEvidenceJournal(work.parent/'m3.jsonl').public_records(),
            argus_events=EvidenceStore.read_run(work.parent/'argus').records(),
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), full_M1_complete=False)))


def test_actual_shared_five_phase_dispatch_and_complete_helper_cleanup(request, monkeypatch):
    stack, controller, driver = scheduled(request, monkeypatch)
    result = run(driver)
    assert result.execution_succeeded and result.terminal_recorded, result.diagnostic
    assert len(result.steps)==10 and all(s.disposition=='completed' and s.normal_recorded for s in result.steps)
    assert result.cleanup.unit_cleanup_complete and result.cleanup.normal_records_complete
    assert controller._sequence==10 + result.lease_renewals//2
    closure = RunClosure(stack[0].session, dispatcher=driver).close(deadline(6))
    assert closure.cleanup_complete and closure.normal_unit_records_complete and closure.execution_succeeded
    assert {h.role for h in closure.helpers}=={3,4,5}
    retain(stack,result,closure,'normal')


def test_paused_shared_ticks_renew_both_original_leases_and_observe_health(request, monkeypatch):
    stack, controller, driver = scheduled(request, monkeypatch, pauses=70)
    old_lease = stack[0].connection.lease_ns
    result = run(driver)
    assert result.execution_succeeded and result.terminal_recorded, result.diagnostic
    assert result.health_scans>=1 and result.lease_renewals>=2
    assert stack[0].connection.lease_ns>old_lease and stack[0].session._lease>old_lease
    closure = RunClosure(stack[0].session, dispatcher=driver).close(deadline(6))
    assert closure.cleanup_complete
    events = EvidenceStore.read_run(stack[3].parent/'argus').records()
    completed_ticks = [e for e in events if e.get('extensions',{}).get('xverse.maestro',{}).get('obligationId','').startswith('tick-')]
    assert len(completed_ticks) == len(driver.plan.ticks) == 73
    assert controller._sequence == 10 + result.lease_renewals//2
    retain(stack,result,closure,'paused')


def test_stopped_controller_records_failure_without_unacknowledged_start(request, monkeypatch):
    stack, controller, driver = scheduled(request, monkeypatch)
    signal.pidfd_send_signal(controller.process._capability.fileno(), signal.SIGSTOP)
    result = run(driver)
    assert not result.execution_succeeded
    assert not list(stack[3].glob('*.marker'))
    assert any(s.disposition!='completed' for s in result.steps)
    retirement = controller.retire(deadline(0.8), terminate=True)
    assert retirement.original_child_dead and retirement.original_child_reaped
    closure = RunClosure(stack[0].session, dispatcher=driver).close(deadline(6))
    assert closure.root_reaped and all(b.released for b in closure.boundaries)
    retain(stack,result,closure,'controller-stall')
