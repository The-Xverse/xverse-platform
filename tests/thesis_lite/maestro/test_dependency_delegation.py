"""Actual native delegation: one final live admission probe, unchanged fixed end."""
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import time

import pytest

from xverse.maestro.affa_protocol import AuthorityKind as K
from xverse.maestro.time import HostDeadline
from .test_run_broker import broker_stack as broker_stack, stage_all
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries


@pytest.mark.parametrize('mode',['normal','parent-dies-after-arm','changed-end'])
def test_native_delegation_keeps_final_live_guard_without_duplicate_owner_probe(broker_stack,monkeypatch,mode):
    broker,facade,client,work=broker_stack
    end=stage_all(broker_stack)
    parent,unit=broker.owner._prepared.resource_order
    source=broker.issuer(parent);sink=broker.issuer(unit)
    assert facade.start(parent,source.recipe.descriptor,broker.connection,end).ready
    token,capability=broker.connection._handles[(source.slot,source.recipe.descriptor.generation)]
    assert token.hex()==source._handle.opaque_id
    events=[]
    rpc=client._rpc;exchange=broker.connection._exchange;release=broker.owner.release

    def observe_rpc(kind,body,deadline,**kwargs):
        began=time.monotonic()
        try:
            return rpc(kind,body,deadline,**kwargs)
        finally:
            events.append(dict(channel='rpc',kind=kind,unit=body.get('unit'),
                end=deadline.monotonic_seconds,began=began,ended=time.monotonic()))

    def observe_native(frame,**kwargs):
        began=time.monotonic();error=None
        try:
            result=exchange(frame,**kwargs)
        except Exception as exc:
            error=str(exc)
            raise
        finally:
            events.append(dict(channel='native',kind=frame.kind.name,slot=frame.slot,
                               began=began,ended=time.monotonic(),diagnostic=error))
        if frame.kind is K.ARM and frame.slot==sink.slot and mode=='parent-dies-after-arm':
            signal.pidfd_send_signal(capability.fileno(),signal.SIGKILL)
            assert select.select([capability.fileno()],[],[],.5)[0]
        return result

    def changed(unit_id,descriptor,gate,deadline,**kwargs):
        return release(unit_id,descriptor,gate,HostDeadline(deadline.session,deadline.monotonic_seconds-.001),**kwargs)

    monkeypatch.setattr(client,'_rpc',observe_rpc)
    monkeypatch.setattr(broker.connection,'_exchange',observe_native)
    if mode=='changed-end':monkeypatch.setattr(broker.owner,'release',changed)
    succeeded=False;failure=None
    if mode=='normal':
        succeeded=facade.start(unit,sink.recipe.descriptor,broker.connection,end).ready
        assert succeeded
    else:
        with pytest.raises(ValueError) as raised:
            facade.start(unit,sink.recipe.descriptor,broker.connection,end)
        failure=str(raised.value)
        assert broker.owner.latch.cancelled
    probes=[e for e in events if e['channel']=='rpc' and e['kind']=='probe' and e['unit']==parent]
    arms=[e for e in events if e['channel']=='native' and e['kind']=='ARM' and e['slot']==sink.slot]
    releases=[e for e in events if e['channel']=='native' and e['kind']=='RELEASE' and e['slot']==sink.slot]
    out=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if out:
        root=Path(out);root.mkdir(parents=True,exist_ok=True)
        (root/('dependency-delegation-'+mode+'.json')).write_text(json.dumps(dict(
            mode=mode,parent=parent,unit=unit,events=events,parent_probes=len(probes),
            native_arms=len(arms),native_releases=len(releases),execution_succeeded=succeeded,
            original_fixed_end=end.monotonic_seconds,original_fixture=str(work.parent),
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            deadlines_unchanged=True,observed_failure=failure,scientific_result=False),indent=2)+'\n')
    assert all(e['end']==end.monotonic_seconds for e in probes)
    if mode=='changed-end':
        assert not arms and not releases
    else:
        assert len(arms)==1
        if mode=='normal':
            assert any(e['channel']=='native' and e['kind']=='QUERY' and e['slot']==source.slot
                       and e['began']>=arms[0]['ended'] for e in events)
        assert len(releases)==(1 if mode=='normal' else 0)
        if releases:assert probes[-1]['ended']<=releases[0]['began']
    assert (work/(sink.owner._unit(unit).binding_id+'.marker')).exists() is succeeded
    assert len(probes)==(1 if mode=='normal' else 0)


@pytest.mark.parametrize('mode',['normal','unrelated-dead'])
def test_native_final_parent_guard_keeps_unrelated_live_preflight(request,monkeypatch,mode):
    from .test_generation_dependents import chain
    chain(monkeypatch)
    stack=request.getfixturevalue('broker_stack');broker,facade,client,work=stack
    end=stage_all(stack)
    named={u.unit_id.rsplit('/',1)[-1]:u.unit_id for u in broker.owner._prepared.units}
    parent,unit,unrelated=[named[n+'-instance'] for n in ('source','sink','unrelated')]
    for target in (parent,unrelated):
        issuer=broker.issuer(target)
        assert facade.start(target,issuer.recipe.descriptor,broker.connection,end).ready
    if mode=='unrelated-dead':
        issuer=broker.issuer(unrelated)
        _,capability=broker.connection._handles[(issuer.slot,issuer.recipe.descriptor.generation)]
        signal.pidfd_send_signal(capability.fileno(),signal.SIGKILL)
        assert select.select([capability.fileno()],[],[],.5)[0]
    events=[];rpc=client._rpc;exchange=broker.connection._exchange
    def storage(kind,body,deadline,**kwargs):
        began=time.monotonic()
        try:return rpc(kind,body,deadline,**kwargs)
        finally:events.append(dict(channel='rpc',kind=kind,unit=body.get('unit'),began=began,
                                   ended=time.monotonic(),end=deadline.monotonic_seconds))
    def native(frame,**kwargs):
        began=time.monotonic()
        try:return exchange(frame,**kwargs)
        finally:events.append(dict(channel='native',kind=frame.kind.name,slot=frame.slot,
                                   began=began,ended=time.monotonic()))
    monkeypatch.setattr(client,'_rpc',storage);monkeypatch.setattr(broker.connection,'_exchange',native)
    sink=broker.issuer(unit)
    if mode=='normal':assert facade.start(unit,sink.recipe.descriptor,broker.connection,end).ready
    else:
        with pytest.raises(ValueError):facade.start(unit,sink.recipe.descriptor,broker.connection,end)
    arms=[e for e in events if e['channel']=='native' and e['kind']=='ARM' and e['slot']==sink.slot]
    releases=[e for e in events if e['channel']=='native' and e['kind']=='RELEASE' and e['slot']==sink.slot]
    probes=lambda target:[e for e in events if e['channel']=='rpc' and e['kind']=='probe' and e['unit']==target]
    if mode=='normal':
        assert len(arms)==len(releases)==len(probes(parent))==len(probes(unrelated))==1
        assert probes(unrelated)[0]['ended']<=arms[0]['began']
        assert arms[0]['ended']<=probes(parent)[0]['began']<probes(parent)[0]['ended']<=releases[0]['began']
        assert all(e['end']==end.monotonic_seconds for e in probes(parent)+probes(unrelated))
    else:assert not arms and not releases
    output=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if output:
        path=Path(output);path.mkdir(parents=True,exist_ok=True)
        (path/('dependency-unrelated-'+mode+'.json')).write_text(json.dumps(dict(mode=mode,events=events,
            parent=parent,unrelated=unrelated,unit=unit,original_fixed_end=end.monotonic_seconds,
            original_fixture=str(work.parent),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))+'\n')
