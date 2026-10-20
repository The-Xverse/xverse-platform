"""Audit exact pure collection tests and actual retained copied/indexed bytes."""
from pathlib import Path
import hashlib
import json
from xverse.argus import EvidenceStore

OUT=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
run=read(OUT/'collection-v4-running.json');root=Path(run['frozen_source_root'])
frozen=read(OUT/'collection-v4-frozen-inputs.json')
assert all(sha(root/n)==h for n,h in frozen.items())
identity=read(OUT/'collection-v4-installed-identity.json');assert len(identity)==36
for n,r in identity.items():assert sha(Path(r['file']))==r['sha256']==sha(root/'src/xverse/maestro'/n)
rows=[]
for phase in ['source','wheel']:
    name='collection-v4-'+phase
    receipt=read(OUT/(name+'-receipt.json'))
    assert receipt['returncode']==0 and receipt['public_capture_returncode']==0
    assert receipt['log_sha256']==sha(OUT/(name+'.log'))
    assert '32 passed' in (OUT/(name+'.log')).read_text()
    private=Path(receipt['original_private_basetemp'])
    def fixture(prefix):
        values=list(private.glob(prefix+'*'))
        values=[v for v in values if v.is_dir() and not v.is_symlink()]
        assert len(values)==1,(prefix,values)
        return values[0]
    nested=fixture('test_nested_actual_bytes_hash_')/'evidence/nested/copy'
    assert nested.read_bytes()==b'actual bytes\x00'
    indexed=fixture('test_actual_public_index_and_c')/'evidence'
    assert (indexed/'copied').read_bytes()==b'indexed actual bytes'
    reader=EvidenceStore.read_run(indexed)
    entries=reader.manifest['artifacts'];assert len(entries)==1
    assert entries[0]['sha256']==sha(indexed/'copied') and entries[0]['bytes']==len(b'indexed actual bytes')
    assert not any('ARTIFACT' in d.code for d in reader.diagnostics)
    total=fixture('test_original_total_byte_budg')/'evidence'
    expected=hashlib.sha256(b'x'*(1<<20)).hexdigest()
    assert all(sha(total/str(i))==expected for i in range(16)) and not (total/'16').exists()
    rows.append(dict(phase=phase,checks_passed=32,actual_nested_copy_sha256=sha(nested),
        actual_public_artifact_entry=entries[0],actual_copied_budget_bytes=16<<20,
        original_private_fixture_root=str(private),log_sha256=receipt['log_sha256']))
red=read(OUT/'collection-race-red-receipt.json');assert red['returncode']==1
assert '4 failed, 28 deselected' in (OUT/'collection-race-red.log').read_text()
old=read(OUT/'collection-v2-source-receipt.json');assert old['returncode']==1
assert '2 failed, 23 passed' in (OUT/'collection-v2-source.log').read_text()
result=dict(revision='ML3-AFFA17-2026-10-19-collection-v4',actual_terminal_session=39202,
    phases=rows,installed_identity_sha256=sha(OUT/'collection-v4-installed-identity.json'),
    frozen_inputs_sha256=sha(OUT/'collection-v4-frozen-inputs.json'),
    wheel_sha256=sha(OUT/'collection-v4-dist/xverse_xdl-0.4.0-py3-none-any.whl'),
    failed_predecessors=['collection-v1 startup Python3.12 missing ruamel before pytest','collection-v2 source23 passed2 failed fixture root lifecycle','collection-v3 new race controls4 actual failures before repair'],
    provider_or_native_workloads_executed=False,full_current_source_regression=False,
    U7_U8_complete=False,runtime_collection_composed=False,full_M1_complete=False,
    stable_increment17=False,accepted=False,merged=False,canonical_note_edited=False,factory_run_created=False)
(OUT/'collection-successor-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['phases','provider_or_native_workloads_executed','runtime_collection_composed','U7_U8_complete']}))
