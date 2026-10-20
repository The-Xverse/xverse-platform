"""Real sealed descriptor transport and original-worker public broker publication."""
from dataclasses import replace
import array
import fcntl
import hashlib
import json
import os
from pathlib import Path
import socket
import time
from types import SimpleNamespace

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro import persistence
from xverse.maestro.coverage import canonical,admit_coverage
from xverse.maestro.public_blobs import (admit_broker_artifact,decode_broker_artifact,decode_broker_data,
    sealed_public_blob,write_public_bytes)
from xverse.maestro.teardown import ReverseTeardown
from .test_coverage import Fixture
from .test_coverage_producers import configure as coverage_configuration
from .test_run_broker import broker_stack as broker_stack,stage_all
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries,deadline
from .test_persistence import storage as storage
from .test_boundary import native as native
from .test_releasegate import guard_binary as guard_binary


@pytest.fixture
def channels():
    a,b=socket.socketpair(socket.AF_UNIX,socket.SOCK_SEQPACKET)
    for c in (a,b):c.setsockopt(socket.SOL_SOCKET,socket.SO_PASSCRED,1);c.setblocking(False)
    try:yield a,b
    finally:a.close();b.close()


def packet(data, *, end=None):
    return persistence._frame('public-blob',1,'ml-'+'1'*32,end or time.monotonic_ns()+1_000_000_000,'0'*64,
        dict(purpose='broker-projection',bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))


def test_real_sealed_transfer_above_packet_bound_preserves_all_bytes_and_closes_right(channels,monkeypatch):
    a,b=channels;data=b'neutral-public-data-'*5000
    assert len(data)>persistence.MAX_PACKET
    fd=sealed_public_blob(data,lambda:None);closed=[];close=os.close
    def tracked(value):closed.append(value);close(value)
    try:
        with pytest.raises(PermissionError):os.write(fd,b'cannot change sealed data')
        frame=packet(data)
        persistence._send_public_blob(a,frame,fd)
        with monkeypatch.context() as patch:
            patch.setattr(persistence.os,'close',tracked)
            received,actual=persistence._receive_packet(b,(os.getpid(),os.getuid(),os.getgid()),
                frame['deadline'],lambda:None,maximum_blob=1<<20)
        assert received==frame and actual==data and len(closed)==1 and closed[0]!=fd
        with pytest.raises(OSError):os.fstat(closed[0])
        assert os.fstat(fd).st_size==len(data)
    finally:os.close(fd)


@pytest.mark.parametrize('mode',['default','missing','extra','truncated','peer','frame','check','unsealed','regular','pidfd',
    'size','hash','bool','expired','future-end','duplicate-json'])
def test_actual_bad_transport_disposes_every_delivered_right(channels,monkeypatch,tmp_path,mode):
    a,b=channels;data=b'owned public bytes';fd=sealed_public_blob(data,lambda:None)
    if mode=='unsealed':os.close(fd);fd=os.memfd_create('unsealed',os.MFD_ALLOW_SEALING|os.MFD_CLOEXEC);os.write(fd,data)
    elif mode=='regular':os.close(fd);path=tmp_path/'regular';path.write_bytes(data);fd=os.open(path,os.O_RDONLY|os.O_CLOEXEC)
    elif mode=='pidfd':os.close(fd);fd=os.pidfd_open(os.getpid(),0)
    closed=[];close=os.close;frame=packet(data);expected=(os.getpid(),os.getuid(),os.getgid());calls=0
    if mode=='peer':expected=(os.getpid()+100000,os.getuid(),os.getgid())
    elif mode=='frame':frame['kind']='commit'
    elif mode=='size':frame['body']['bytes']+=1
    elif mode=='hash':frame['body']['sha256']='0'*64
    elif mode=='bool':frame['body']['bytes']=True
    elif mode=='expired':frame['deadline']=time.monotonic_ns()-1
    elif mode=='future-end':frame['deadline']=time.monotonic_ns()+6_000_000_000
    raw=canonical(frame)
    if mode=='duplicate-json':raw=raw.replace(b'"purpose":',b'"purpose":"broker-projection","purpose":',1)
    rights=[] if mode=='missing' else [(socket.SOL_SOCKET,socket.SCM_RIGHTS,array.array('i',[fd]*(100 if mode=='truncated' else 2 if mode=='extra' else 1)))]
    def tracked(value):closed.append(value);close(value)
    def check():
        nonlocal calls
        calls+=1
        if mode=='check' and calls==2:raise ValueError('owned receive checkpoint failure')
    try:
        before=set(os.listdir('/proc/self/fd'))
        a.sendmsg([raw],rights)
        with monkeypatch.context() as patch:
            patch.setattr(persistence.os,'close',tracked)
            with pytest.raises((ValueError,OSError)):
                persistence._receive_packet(b,expected,time.monotonic_ns()+7_000_000_000,check,
                    maximum_blob=0 if mode=='default' else 1<<20)
        assert set(os.listdir('/proc/self/fd'))==before
        assert len(closed)==(0 if mode=='missing' else 2 if mode=='extra' else len(closed) if mode=='truncated' else 1)
        if mode=='truncated':assert 0<len(closed)<100
        for value in closed:
            with pytest.raises(OSError):os.fstat(value)
        assert fcntl.fcntl(fd,fcntl.F_GETFD)&fcntl.FD_CLOEXEC
        if mode!='pidfd':assert os.fstat(fd).st_size==len(data)
    finally:os.close(fd)


def test_full_synthetic_admitted_inventory_above_packet_transfers_without_row_loss(tmp_path,channels):
    f=Fixture(tmp_path)
    admission=admit_coverage(f.prepared,f.result,f.resources,run_id='coverage-fixture',host_session='coverage-host',
        contexts=[(u.unit_id,g,'synthetic-large-'+str(i)+'-'+str(g)) for i,u in enumerate(f.units) for g in range(1,65)],
        health_policies={u.unit_id:(5,5) for u in f.units},active_start=0,active_end=1)
    ad=admission.data(admission.digest);body=f.broker
    body['admittedUnits']=[dict(unitId=u.unit_id,initialGeneration=1,maximumGeneration=64) for u in f.units]
    body['futureContexts']=[c for c in ad['contexts'] if c['generation']!=1]
    template=body['generations'][0];body['generations']=[]
    for c in ad['contexts']:
        row={k:None for k in template}
        row.update(unitId=c['unitId'],generation=c['generation'],issued=False,stageAttempted=False,
            releaseObserved=False,c1TerminationObserved=None,c1Empty=None)
        body['generations'].append(row)
    raw=canonical(body);assert persistence.MAX_PACKET<len(raw)<1<<20
    assert len(decode_broker_data(raw,admission,admission.digest)['generations'])==128
    a,b=channels;frame=packet(raw);fd=sealed_public_blob(raw,lambda:None)
    try:
        persistence._send_public_blob(a,frame,fd)
        _,received=persistence._receive_packet(b,(os.getpid(),os.getuid(),os.getgid()),frame['deadline'],lambda:None,maximum_blob=1<<20)
        assert received==raw and len(json.loads(received)['generations'])==128
    finally:os.close(fd);f.writer.abort(reason='Synthetic metadata transport; no runtime authority')


@pytest.mark.parametrize('mode',['run','lifecycle','session','generation','boolean','unit-shape','future-shape','epoch','clock','extra'])
def test_closed_broker_validation_rejects_bad_inventory_and_identity(tmp_path,mode):
    f=Fixture(tmp_path);body=f.broker
    for row in body['generations']:row.update(c1TerminationObserved=False,c1Empty=True if row['c1Released'] else None)
    assert decode_broker_data(canonical(body),f.admission,f.admission.digest)['runId']=='coverage-fixture'
    if mode=='run':body['runId']='foreign-run'
    elif mode=='lifecycle':body['lifecycleDigest']='sha256:'+'0'*64
    elif mode=='session':body['hostSession']='foreign-session'
    elif mode=='generation':body['generations'][0]['generation']=99
    elif mode=='boolean':body['admittedUnits'][0]['maximumGeneration']=True
    elif mode=='unit-shape':body['generations'][0]['unitId']=[]
    elif mode=='future-shape':body['futureContexts'][0]['generation']=True
    elif mode=='epoch':body['epochs'][0]['epoch']=True
    elif mode=='clock':body['observedAt']=-1
    elif mode=='extra':body['generations'][0]['nativeHandle']='forbidden'
    try:
        with pytest.raises(ValueError):decode_broker_data(canonical(body),f.admission,f.admission.digest)
    finally:f.writer.abort(reason='Synthetic public shape control')


def test_confined_public_artifact_nested_bytes_and_actual_closed_reader(tmp_path):
    from xverse.maestro.evidence import pin_export_root
    f=Fixture(tmp_path);e=SimpleNamespace(root=f.root,writer=f.writer);e.export_root=pin_export_root(e)
    try:
        data=canonical({'owned':'neutral public bytes'})
        entry=write_public_bytes(e,'nested/broker.json',data,1<<20,lambda:None)
        assert entry['sha256']==hashlib.sha256(data).hexdigest()
        with pytest.raises(FileExistsError):write_public_bytes(e,'nested/broker.json',b'changed',1<<20,lambda:None)
        f.writer.finalize()
        reader=EvidenceStore.read_run(f.root)
        assert entry in reader.manifest['artifacts'] and not any('ARTIFACT' in d.code for d in reader.diagnostics)
        assert (f.root/'nested/broker.json').read_bytes()==data
    finally:os.close(e.export_root[0])


def configure(monkeypatch,mode='valid'):
    from . import test_launcher
    original=test_launcher.encode_configuration
    def encoded(*args,**kw):
        admission=admit_broker_artifact(kw['coverage'],expected_digest=kw['coverage'].digest)
        config=original(*args,**kw,broker_artifact=admission)
        body=json.loads(config.private_bytes)
        if mode=='version':body['version']=4
        elif mode=='bool':body['broker_artifact']['maximum_bytes']=True
        elif mode=='path':body['broker_artifact']['relative_path']='foreign.json'
        elif mode=='digest':body['broker_artifact']['coverage_digest']='sha256:'+'0'*64
        elif mode=='extra':body['broker_artifact']['nativeScope']='forbidden'
        return replace(config,private_bytes=canonical(body)) if mode!='valid' else config
    monkeypatch.setattr(test_launcher,'encode_configuration',encoded)
    return coverage_configuration(monkeypatch)


def test_original_worker_publishes_actual_broker_bytes_indexes_and_caches_without_new_intents(request,monkeypatch):
    saved=configure(monkeypatch);stack=request.getfixturevalue('broker_stack')
    broker,facade,client,work=stack
    assert json.loads(saved['config'].private_bytes)['version']==5
    end=stage_all(stack)
    for unit in client.prepared.resource_order:
        issuer=broker.issuer(unit)
        assert facade.start(unit,issuer.recipe.descriptor,broker.connection,end).ready
    cleanup=ReverseTeardown(facade,per_unit_seconds=.8).run(deadline(3))
    assert cleanup.unit_cleanup_complete and cleanup.normal_records_complete
    count=len(EvidenceStore.read_run(work.parent/'argus').records());claims=dict(client._claims)
    receipt=client.publish_broker_artifact(broker,deadline(2));body=receipt.public_data()
    path=work.parent/'argus'/body['entry']['path'];data=path.read_bytes()
    observed=decode_broker_data(data,client.coverage,client.coverage_digest)
    assert body['entry']['bytes']==len(data) and body['entry']['sha256']==hashlib.sha256(data).hexdigest()
    assert all(r['directChildReaped'] is True and r['c1Released'] is True for r in observed['generations'])
    assert len(EvidenceStore.read_run(work.parent/'argus').records())==count and client._claims==claims
    with monkeypatch.context() as patch:
        patch.setattr(client,'_rpc',lambda *a,**kw:pytest.fail('repeat RPC'))
        patch.setattr(broker,'public_projection',lambda *a,**kw:pytest.fail('repeat projection'))
        assert client.publish_broker_artifact(broker,deadline(1)) is receipt
    client.abort(deadline(1));reader=EvidenceStore.read_run(work.parent/'argus')
    assert body['entry'] in reader.manifest['artifacts']
    assert not any('ARTIFACT' in d.code for d in reader.diagnostics)
    output=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if output:
        (Path(output)/('broker-artifact-public-'+str(os.getpid())+'.json')).write_text(json.dumps(dict(
            admission=json.loads(client.coverage.public_bytes),admission_digest=client.coverage_digest,
            broker=observed,receipt=body,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            full_M1_complete=False,scientific_result=False)))


@pytest.mark.parametrize('mode',['version','bool','path','digest','extra'])
def test_bad_sealed_broker_artifact_rejects_before_original_writer(request,monkeypatch,tmp_path,mode):
    configure(monkeypatch,mode)
    with pytest.raises(ValueError):request.getfixturevalue('broker_stack')
    assert not (tmp_path/'m3.jsonl').exists() and not (tmp_path/'argus').exists()


@pytest.mark.parametrize('mode',['existing','symlink','ack','lost'])
def test_failed_actual_publication_never_certifies_receipt_or_rewrites_existing_bytes(request,monkeypatch,tmp_path,mode):
    configure(monkeypatch);stack=request.getfixturevalue('broker_stack');broker,_,client,work=stack
    path=work.parent/'argus'/client._broker_artifact.relative_path
    sentinel=tmp_path/'sentinel';sentinel.write_bytes(b'owned sentinel')
    if mode=='existing':path.write_bytes(b'existing')
    elif mode=='symlink':path.symlink_to(sentinel)
    elif mode in ('ack','lost'):
        original=client._rpc
        def damaged(*args,**kw):
            operation,end,body=original(*args,**kw)
            if mode=='lost':raise ValueError('owned lost public-blob ACK')
            body['entry']['bytes']=True
            return operation,end,body
        monkeypatch.setattr(client,'_rpc',damaged)
    with pytest.raises((ValueError,OSError)):client.publish_broker_artifact(broker,deadline(2))
    assert client._broker_publication is None and client.latch.cancelled
    assert sentinel.read_bytes()==b'owned sentinel' and not list(work.glob('*.marker'))
    if mode=='existing':assert path.read_bytes()==b'existing'


def test_original_replacement_conflict_and_cancelled_publication_preserve_no_start(request,monkeypatch):
    configure(monkeypatch);stack=request.getfixturevalue('broker_stack');broker,_,client,work=stack
    sequence=client._sequence;original=client._broker_artifact
    client._broker_artifact=replace(original)
    try:
        with pytest.raises(ValueError,match='REPLACED'):client.publish_broker_artifact(broker,deadline(1))
    finally:client._broker_artifact=original
    original_path=original.relative_path
    try:
        object.__setattr__(original,'relative_path','foreign.json')
        with pytest.raises(ValueError,match='REPLACED'):client.publish_broker_artifact(broker,deadline(1))
    finally:object.__setattr__(original,'relative_path',original_path)
    with pytest.raises(ValueError,match='ORIGINAL'):client.publish_broker_artifact(SimpleNamespace(storage=client),deadline(1))
    client._publication_lock.acquire()
    try:
        with pytest.raises(ValueError,match='CONFLICT'):client.publish_broker_artifact(broker,deadline(1))
    finally:client._publication_lock.release()
    assert client._sequence==sequence and not client.latch.cancelled
    broker.cancel('public-evidence-after-cancellation')
    receipt=client.publish_broker_artifact(broker,deadline(2))
    assert receipt.public_data()['runId']==client.run_id and client.latch.cancelled
    assert not client._claims and not list(work.glob('*.marker'))


@pytest.mark.parametrize('mode',['revalidate-hang','revalidate-fail'])
def test_actual_v5_revalidation_failure_still_prevents_native_release(storage,native,guard_binary,mode):
    from . import test_persistence
    import select
    original=test_persistence.encode_configuration
    def configuration(prepared,result,resources,**kw):
        coverage=admit_coverage(prepared,result,resources,run_id=kw['run_id'],host_session=kw['session'],
            contexts=[(b.unit_id,b.generation,b.execution_id) for b in kw['bindings']],
            health_policies={u.unit_id:(1,2) for u in prepared.units},active_start=time.monotonic(),
            active_end=kw['generation_deadline'].monotonic_seconds-2)
        return original(prepared,result,resources,**kw,coverage=coverage,
            broker_artifact=admit_broker_artifact(coverage,expected_digest=coverage.digest))
    # The storage fixture creates its original configuration during setup. Its
    # start callback accepts an independently sealed replacement before birth.
    start,stage,base,manager,latch=storage
    # Reuse the fixture's exact original inputs/private bindings; do not mint any
    # new approval or discover ownership by PID/path.
    raw=json.loads(base.private_bytes)
    from xverse.maestro.persistence_worker import _decode_binding,_decode_approval
    selected=configuration(base.prepared,base.result,base.resources,run_id=base.run_id,session=base.session,
        generation_deadline=persistence.HostDeadline(base.session,base.generation_ns/1e9),bindings=[_decode_binding(b) for b in raw['bindings']],
        approvals=[_decode_approval(a) for a in raw['approvals']],journal_path=raw['journal_path'],evidence_root=raw['evidence_root'])
    owner,client,announce,release=start(mode,override=selected)
    assert client._broker_artifact is not None
    unit=selected.prepared.units[0].unit_id;end=deadline(1.5)
    owner.commit_intent(unit,end)
    unit,descriptor,child,marker,gate=stage(owner,guard_binary,native)
    with pytest.raises(ValueError):owner.release(unit,descriptor,gate,end)
    assert latch.cancelled and gate._sequence==0 and not select.select([marker],[],[],.02)[0]
    assert manager.force_cleanup(descriptor).termination_observed
    assert child.wait(timeout=2)==0 and client.drain(deadline(1)).worker_reaped
