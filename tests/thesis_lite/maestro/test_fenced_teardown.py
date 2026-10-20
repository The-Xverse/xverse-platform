"""Actual normal provenance after native cancellation; no productive lease renewal."""
import json
import os
from pathlib import Path
import select
import time

from xverse.argus import EvidenceStore
from xverse.maestro.teardown import ReverseTeardown
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_collection_runtime import configure
from .test_run_broker import broker_stack as broker_stack, stage_all
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


def running(request,monkeypatch):
    configure(monkeypatch)
    stack=request.getfixturevalue('broker_stack');broker,facade,_,_=stack
    end=stage_all(stack)
    for unit in broker.owner._prepared.resource_order:
        issuer=broker.issuer(unit)
        assert facade.start(unit,issuer.recipe.descriptor,broker.connection,end).ready
    return stack,ReverseTeardown(facade,per_unit_seconds=.8)


def test_actual_normal_cleanup_past_old_native_lease_keeps_original_ends_and_waits(request,monkeypatch):
    stack,stopper=running(request,monkeypatch);broker,_,client,work=stack
    old=broker.connection._lease
    original=[(i._handle,i.recipe.operation_deadline_ns) for i in broker.issuers]
    assert broker.cancel('fenced-normal',deadline=deadline(.5)).native_epoch_confirmed
    broker.service_terminal(deadline(.5))
    finish=old/1e9+.05
    while time.monotonic()<finish:
        select.select([],[],[],min(.6,finish-time.monotonic()))
        broker.service_terminal(deadline(.5))
    began=time.monotonic();result=stopper.run(deadline(3))
    assert result.normal_records_complete and result.unit_cleanup_complete
    assert broker.connection._lease==old and broker.owner.latch.cancelled
    assert original==[(i._handle,i.recipe.operation_deadline_ns) for i in broker.issuers]
    facts=broker.public_projection(deadline(.5)).public_data()
    assert all(r['directChildReaped'] is True and r['nativeRetired'] is True and r['c1Released'] is True
               for r in facts['generations'])
    normal=[r for r in FileEvidenceJournal(work.parent/'m3.jsonl').records if 'teardown' in r.details]
    assert len(normal)==8 and all(r.details['teardown']['observed_at']>=began>old/1e9 for r in normal)
    collected=client.collect_outputs(broker,deadline(2))
    assert collected.public_data()['collectionComplete']
    client.abort(deadline(.8));reader=EvidenceStore.read_run(work.parent/'argus')
    assert reader.manifest['writerState']=='failed'
    assert not any('CAUSAL' in d.code or 'ARTIFACT' in d.code for d in reader.diagnostics)
    out=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if out:
        (Path(out)/('fenced-teardown-'+work.parent.name+'.json')).write_text(json.dumps(dict(
            old_native_lease_ns=old,normal_teardown_began=began,original_native_lease_unchanged=True,
            native_generation_facts=facts,normal_records=len(normal),original_fixture=str(work.parent),
            original_collection=collected.public_data(),full_lifecycle_complete=False),indent=2)+'\n')


def test_actual_cancellation_without_original_terminal_scope_keeps_normal_gap(request,monkeypatch):
    stack,stopper=running(request,monkeypatch);broker=stack[0]
    broker.cancel('not-normal-terminal',deadline=deadline(.5))
    assert not broker.session._terminal
    result=stopper.run(deadline(3))
    assert result.unit_cleanup_complete and not result.normal_records_complete
    assert all(r.emergency and not r.normal_records_complete for r in result.units)
    assert not any('teardown' in r.details for r in FileEvidenceJournal(stack[3].parent/'m3.jsonl').records)
