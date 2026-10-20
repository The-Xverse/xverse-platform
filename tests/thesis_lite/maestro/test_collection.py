"""U8 declared-file I/O controls; no provider or native process execution."""
import copy
from dataclasses import replace
import hashlib
import os
import stat
import time

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.artifacts import ArtifactDeclaration, CollectionAdmission, CollectionError
from xverse.maestro.time import HostDeadline
from .test_preparation import compiled


def end(seconds=2, session='collection-test'):
    return HostDeadline(session,time.monotonic()+seconds)


@pytest.fixture
def directories(tmp_path):
    source=tmp_path/'source'; target=tmp_path/'evidence'
    source.mkdir(); target.mkdir()
    return source,target


def declaration(**kwargs):
    return ArtifactDeclaration('unit-a',1,kwargs.pop('source','item'),kwargs.pop('destination','copied'),**kwargs)


def test_nested_actual_bytes_hash_and_repeat_without_new_io(directories,monkeypatch):
    source,target=directories
    (source/'nested').mkdir(); (target/'nested').mkdir()
    (source/'nested/item').write_bytes(b'actual bytes\x00')
    original=end()
    with CollectionAdmission(source,target,[declaration(source='nested/item',destination='nested/copy')],original) as admission:
        result=admission.collect(original)
        row=result.artifacts[0]
        assert result.collection_complete and row.status=='collected'
        assert row.content==(target/'nested/copy').read_bytes()==b'actual bytes\x00'
        assert row.sha256==hashlib.sha256(row.content).hexdigest()
        with monkeypatch.context() as patch:
            patch.setattr(admission,'_read',lambda *a:pytest.fail('repeat read'))
            patch.setattr(admission,'_copy',lambda *a:pytest.fail('repeat write'))
            assert admission.collect(original) is result
        with pytest.raises(CollectionError,match='ORIGINAL'):
            admission.collect(end(session='foreign'))
        with pytest.raises(TypeError):
            copy.copy(admission)


@pytest.mark.parametrize('path',['../escape','/absolute','sub/../escape','sub//item','sub/./item','back\\slash',''])
def test_invalid_declaration_path_rejected_before_io(path):
    with pytest.raises(CollectionError,match='PATH'):
        declaration(source=path)
    with pytest.raises(CollectionError,match='PATH'):
        declaration(destination=path)


@pytest.mark.parametrize('kind',['source-link','source-parent-link','target-link','target-parent-link','fifo','directory','existing-target'])
def test_unsafe_paths_never_replace_targets_or_copy_outside(directories,tmp_path,kind):
    source,target=directories
    outside=tmp_path/'outside'; outside.mkdir(); (outside/'item').write_bytes(b'outside')
    (source/'item').write_bytes(b'source')
    declared=declaration()
    if kind=='source-link':
        (source/'item').unlink(); (source/'item').symlink_to(outside/'item')
    elif kind=='source-parent-link':
        (source/'link').symlink_to(outside,target_is_directory=True); declared=declaration(source='link/item')
    elif kind=='target-link':
        (target/'copied').symlink_to(outside/'item')
    elif kind=='target-parent-link':
        (target/'link').symlink_to(outside,target_is_directory=True); declared=declaration(destination='link/copied')
    elif kind=='fifo':
        (source/'item').unlink(); os.mkfifo(source/'item')
    elif kind=='directory':
        (source/'item').unlink(); (source/'item').mkdir()
    else:
        (target/'copied').write_bytes(b'existing')
    original=end()
    with CollectionAdmission(source,target,[declared],original) as admission:
        result=admission.collect(original)
    assert not result.collection_complete and result.artifacts[0].status=='error'
    assert (outside/'item').read_bytes()==b'outside' and not (outside/'copied').exists()
    if kind=='existing-target':
        assert (target/'copied').read_bytes()==b'existing'


@pytest.mark.parametrize('root',['source','evidence'])
def test_root_substitution_rejects_before_collection(directories,root):
    source,target=directories
    original=end()
    with CollectionAdmission(source,target,[declaration()],original) as admission:
        replaced=source if root=='source' else target
        replaced.rename(replaced.with_name(root+'-old')); replaced.mkdir()
        with pytest.raises(CollectionError,match='ROOT-CHANGED'):
            admission.collect(original)
    assert not (target/'copied').exists()


@pytest.mark.parametrize('mutation',['content','source-parent','target-parent'])
def test_actual_mid_read_or_copy_substitution_never_yields_stable_hash(directories,monkeypatch,mutation):
    source,target=directories
    (source/'nested').mkdir(); (target/'nested').mkdir()
    data=b'x'*70000
    (source/'nested/item').write_bytes(data)
    original=end()
    real_read=os.read
    changed=False
    def change(fd,count):
        nonlocal changed
        value=real_read(fd,count)
        if not changed and stat.S_ISREG(os.fstat(fd).st_mode):
            changed=True
            if mutation=='content':
                with (source/'nested/item').open('ab') as stream:stream.write(b'y')
            else:
                parent=(source if mutation=='source-parent' else target)/'nested'
                parent.rename(parent.with_name('old')); parent.mkdir()
        return value
    if mutation=='target-parent':
        real_write=os.write
        def write_change(fd,value):
            nonlocal changed
            count=real_write(fd,value)
            if not changed:
                changed=True
                (target/'nested').rename(target/'old'); (target/'nested').mkdir()
            return count
        monkeypatch.setattr(os,'write',write_change)
    else:
        monkeypatch.setattr(os,'read',change)
    with CollectionAdmission(source,target,[declaration(source='nested/item',destination='nested/copy')],original) as admission:
        result=admission.collect(original)
    assert changed and not result.collection_complete
    assert result.artifacts[0].status=='error' and result.artifacts[0].sha256 is None
    assert not (target/'nested/copy').exists()
    if mutation=='target-parent':assert not (target/'old/copy').exists()


def test_required_optional_missing_and_missing_destination_are_distinct(directories):
    source,target=directories
    (source/'item').write_bytes(b'present')
    original=end()
    declarations=[declaration(source='missing',destination='a'),
        declaration(source='optional',destination='b',required=False),
        declaration(destination='absent-parent/c')]
    with CollectionAdmission(source,target,declarations,original) as admission:
        rows=admission.collect(original).artifacts
    assert [r.status for r in rows]==['missing','missing','error']
    original=end()
    with CollectionAdmission(source,target,[declarations[1]],original) as admission:
        assert admission.collect(original).collection_complete


def test_size_count_and_original_deadline_bounds(directories,monkeypatch):
    source,target=directories
    (source/'item').write_bytes(b'x'*((1<<20)+1))
    original=end()
    with CollectionAdmission(source,target,[declaration()],original) as admission:
        row=admission.collect(original).artifacts[0]
        assert row.status=='error' and row.diagnostic=='ML-COLLECTION-SIZE' and row.sha256 is None
    with pytest.raises(CollectionError,match='COUNT'):
        CollectionAdmission(source,target,[declaration(source=str(n),destination=str(n)) for n in range(9)],end())
    with pytest.raises(CollectionError,match='DEADLINE'):
        CollectionAdmission(source,target,[],end(11))
    with CollectionAdmission(source,target,[],original) as admission:
        with pytest.raises(CollectionError,match='ORIGINAL'):
            admission.collect(end(3))
        monkeypatch.setattr(time,'monotonic',lambda:original.monotonic_seconds+1)
        with pytest.raises(CollectionError,match='TIMEOUT'):
            admission.collect(original)


def test_expiry_during_read_preserves_prior_facts_and_removes_no_existing_file(directories,monkeypatch):
    source,target=directories
    (source/'item').write_bytes(b'x'*70000)
    original=end()
    real_read=os.read
    def expired(fd,count):
        data=real_read(fd,count)
        monkeypatch.setattr(time,'monotonic',lambda:original.monotonic_seconds+1)
        return data
    with CollectionAdmission(source,target,[declaration()],original) as admission:
        monkeypatch.setattr(os,'read',expired)
        result=admission.collect(original)
        assert not result.collection_complete and result.artifacts[0].diagnostic=='ML-COLLECTION-TIMEOUT'
        assert admission.collect(original) is result
    assert not (target/'copied').exists()


def writer(source,target):
    result,_=compiled()
    target.rmdir()  # Fixture-owned empty directory; the accepted writer creates its root.
    return EvidenceStore.open_run(target,run_id='collection-run',plan=result.plan,
        clocks={'host':{'domain':'host:collection-test','unit':'s','value':time.monotonic()}})


def test_actual_public_index_and_closed_reader_bytes(directories):
    source,target=directories
    (source/'item').write_bytes(b'indexed actual bytes')
    run=writer(source,target)
    original=end()
    with CollectionAdmission(source,target,[declaration()],original) as admission:
        result=admission.collect(original)
        entries=admission.index(run,result,original)
        assert entries[0].public_entry()==run.record_artifact('copied',media_type='application/octet-stream')
        assert admission.index(run,result,original) is entries
        with pytest.raises(CollectionError,match='ORIGINAL'):
            admission.index(run,replace(result),original)
        run.finalize()
    reader=EvidenceStore.read_run(target)
    assert reader.manifest['artifacts']==[entries[0].public_entry()]
    assert not any('ARTIFACT' in d.code for d in reader.diagnostics)


def test_malformed_actual_index_ack_never_returns_an_index_receipt(directories,monkeypatch):
    source,target=directories
    (source/'item').write_bytes(b'indexed actual bytes')
    run=writer(source,target)
    original=end()
    with CollectionAdmission(source,target,[declaration()],original) as admission:
        result=admission.collect(original)
        real_index=run.record_artifact
        def damaged(*args,**kwargs):
            entry=real_index(*args,**kwargs); entry['sha256']='0'*64; return entry
        monkeypatch.setattr(run,'record_artifact',damaged)
        with pytest.raises(CollectionError,match='INDEX-ACK'):
            admission.index(run,result,original)
    run.abort(reason='owned collection test failure')


def test_actual_copy_tampered_before_index_cannot_gain_a_matching_receipt(directories):
    source,target=directories
    (source/'item').write_bytes(b'original')
    run=writer(source,target)
    original=end()
    with CollectionAdmission(source,target,[declaration()],original) as admission:
        result=admission.collect(original)
        (target/'copied').write_bytes(b'tampered')
        with pytest.raises(CollectionError,match='INDEX-ACK'):
            admission.index(run,result,original)
    run.abort(reason='actual mutated artifact')


def test_original_total_byte_budget_cannot_be_replenished_by_extra_declarations(directories):
    source,target=directories
    declarations=[]
    for i in range(17):
        (source/str(i)).write_bytes(b'x'*(1<<20))
        declarations.append(ArtifactDeclaration('unit-'+str(i//8),1,str(i),str(i)))
    original=end(8)
    with CollectionAdmission(source,target,declarations,original) as admission:
        result=admission.collect(original)
    assert len([a for a in result.artifacts if a.status=='collected'])==16
    assert result.artifacts[-1].diagnostic=='ML-COLLECTION-SIZE'
    assert not result.collection_complete and not (target/'16').exists()


def test_missing_root_never_becomes_optional_missing_success(directories):
    source,target=directories
    original=end()
    with CollectionAdmission(source,target,[declaration(required=False)],original) as admission:
        source.rmdir()
        with pytest.raises(CollectionError,match='ROOT-CHANGED'):
            admission.collect(original)


@pytest.mark.parametrize('mutation',['root','parent','timeout'])
def test_missing_lookup_race_is_error_for_optional_file(directories,monkeypatch,mutation):
    source,target=directories
    (source/'nested').mkdir()
    original=end()
    real_open=os.open
    changed=False
    def changed_open(path,*args,**kwargs):
        nonlocal changed
        if path=='item' and 'dir_fd' in kwargs and not changed:
            changed=True
            if mutation=='root':
                source.rename(source.with_name('old-source')); source.mkdir()
            elif mutation=='parent':
                (source/'nested').rename(source/'old-nested'); (source/'nested').mkdir()
            else:
                monkeypatch.setattr(time,'monotonic',lambda:original.monotonic_seconds+1)
            raise FileNotFoundError('actual missing lookup after boundary change')
        return real_open(path,*args,**kwargs)
    with CollectionAdmission(source,target,[declaration(source='nested/item',required=False)],original) as admission:
        monkeypatch.setattr(os,'open',changed_open)
        result=admission.collect(original)
    assert changed and not result.collection_complete
    assert result.artifacts[0].status=='error' and result.artifacts[0].sha256 is None


def test_destination_disappearing_during_copy_is_error_for_optional_file(directories,monkeypatch):
    source,target=directories
    (source/'item').write_bytes(b'copied actual bytes')
    original=end()
    real_write=os.write
    changed=False
    def unlinked(fd,data):
        nonlocal changed
        count=real_write(fd,data)
        if not changed:
            changed=True
            (target/'copied').unlink()
        return count
    with CollectionAdmission(source,target,[declaration(required=False)],original) as admission:
        monkeypatch.setattr(os,'write',unlinked)
        result=admission.collect(original)
    assert changed and not result.collection_complete
    assert result.artifacts[0].status=='error' and result.artifacts[0].sha256 is None
    assert not (target/'copied').exists()


def test_collect_index_and_close_conflicts_preserve_one_original_result(directories,monkeypatch):
    import threading
    source,target=directories
    (source/'item').write_bytes(b'one actual collection')
    run=writer(source,target)
    original=end()
    entered,proceed=threading.Event(),threading.Event()
    results=[];errors=[]
    with CollectionAdmission(source,target,[declaration()],original) as admission:
        actual_read=admission._read
        def paused(*args):
            entered.set()
            assert proceed.wait(1)
            return actual_read(*args)
        monkeypatch.setattr(admission,'_read',paused)
        def collect():
            try:results.append(admission.collect(original))
            except BaseException as error:errors.append(error)
        thread=threading.Thread(target=collect)
        thread.start()
        try:
            assert entered.wait(1)
            with pytest.raises(CollectionError,match='CONFLICT'):
                admission.collect(original)
            with pytest.raises(CollectionError,match='CONFLICT'):
                admission.index(run,None,original)
            with pytest.raises(CollectionError,match='CONFLICT'):
                admission.close()
        finally:
            proceed.set(); thread.join(2)
        assert not thread.is_alive() and not errors and len(results)==1
        assert results[0].collection_complete and admission.collect(original) is results[0]
        assert admission.index(run,results[0],original)[0].sha256==hashlib.sha256(b'one actual collection').hexdigest()
    run.finalize()


def test_unbounded_declaration_iterable_rejects_without_calling_it(directories):
    source,target=directories
    class Poison:
        def __iter__(self):
            pytest.fail('unadmitted iterator invoked')
    with pytest.raises(CollectionError,match='COUNT'):
        CollectionAdmission(source,target,Poison(),end())
    with pytest.raises(CollectionError,match='COUNT'):
        CollectionAdmission(source,target,[declaration()]*129,end())
    with pytest.raises(CollectionError,match='DECLARATION'):
        declaration(media_type='application/'+'x'*129)
