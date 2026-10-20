"""Read-only audit of exact coverage-v1..v5 artifacts; not full-candidate review."""
from pathlib import Path
import hashlib
import json
import sys
from jsonschema import Draft202012Validator

OUT=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[];roots=[];waits=[];public=[]
for version,expected in [(1,30),(2,30),(3,36),(4,38),(5,41)]:
    tag='coverage-v'+str(version)
    run=read(OUT/(tag+'-running.json'));root=Path(run['frozen_source_root'])
    frozen=read(OUT/(tag+'-frozen-inputs.json'))
    assert all(sha(root/n)==h for n,h in frozen.items())
    identity=read(OUT/(tag+'-installed-identity.json'));assert len(identity)==38
    for name,fact in identity.items():
        assert sha(Path(fact['file']))==fact['sha256']==sha(root/'src/xverse/maestro'/name)
    for phase in ('source','wheel'):
        name=tag+'-'+phase;receipt=OUT/(name+'-receipt.json')
        if version==1 and phase=='wheel':
            assert not receipt.exists();continue
        facts=read(receipt);log=OUT/(name+'.log')
        assert sha(log)==facts['log_sha256'] and facts['public_capture_returncode']==0
        assert facts['returncode']==(1 if version==1 else 0)
        assert ('4 failed, 26 passed' if version==1 else str(expected)+' passed') in log.read_text()
        for p in (OUT/(name+'-harness')).glob('maestro-component-*.json'):
            f=read(p);assert f['root_removed'] and f['workers_reaped']
            assert not (Path(f['parent_path'])/f['root_name']).exists()
            roots.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p)))
        for p in (OUT/(name+'-harness')).glob('run-broker-waits-*.json'):
            f=read(p)
            assert f['bootstrap_reaped'] and f['registered_helpers_reaped'] and f['storage_reaped'] and f['original_C1_released']
            waits.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p)))
        for f in read(OUT/(name+'-public-evidence-index.json')):
            assert sha(OUT/f['snapshot'])==f['sha256'];public.append(f)
        rows.append(dict(revision=tag,phase=phase,returncode=facts['returncode'],
            source_manifest_sha256=sha(OUT/(tag+'-frozen-inputs.json')),receipt_sha256=sha(receipt)))
assert len(roots)==len(waits)==len(public)==6
run=read(OUT/'coverage-v5-running.json');ROOT=Path(run['frozen_source_root'])
sys.path.insert(0,str(ROOT))
from tests.thesis_lite.maestro.test_preparation import compiled,PIN
from xverse.maestro.projection import prepare_lifecycle
from xverse.maestro.coverage import admit_coverage,verify_closed,CoverageAdmission,assess_preclosure,canonical
from xverse.argus import EvidenceStore
result,resources=compiled();prepared=prepare_lifecycle(result,resources,provider_descriptors=(PIN,))
admission=admit_coverage(prepared,result,resources,run_id='coverage-fixture',host_session='coverage-host',
    contexts=[(u.unit_id,g,'synthetic-execution-'+str(i)+'-g'+str(g)) for i,u in enumerate(prepared.units) for g in (1,2)],
    health_policies={u.unit_id:(1,5) for u in prepared.units},active_start=0,active_end=5)
schema=Draft202012Validator(read(ROOT/'tests/thesis_lite/maestro/lifecycle-coverage-v2.schema.json'))
closed=[];native=[]
for phase in ('source','wheel'):
    receipt=read(OUT/('coverage-v5-'+phase+'-receipt.json'));private=Path(receipt['original_private_basetemp'])
    paths=[p for p in private.glob('test_actual_closed_writer_inde*/argus') if not p.parent.name.endswith('current')]
    assert len(paths)==2
    for path in paths:
        before={p.name:sha(p) for p in path.iterdir() if p.is_file()}
        verified=verify_closed(admission,path,expected_admission_digest=admission.digest)
        report=verified.coverage.report();schema.validate(report)
        assert verified.writer_state=='closed' and verified.accepted_reader_executed and not verified.reader_diagnostics
        assert report['overallStatus']=='complete' and report['normalRecordStatus']=='complete'
        assert before=={p.name:sha(p) for p in path.iterdir() if p.is_file()}
        closed.append(dict(phase=phase,path=str(path),manifest_sha256=verified.manifest_sha256,
            original_admission_digest=admission.digest,report_sha256=hashlib.sha256(verified.coverage.public_bytes).hexdigest(),
            synthetic_fixture=True,scientific_result=False))
    exports=list((OUT/('coverage-v5-'+phase+'-harness')).glob('coverage-original-public-*.json'));assert len(exports)==1
    for path in exports:
        facts=read(path);original=CoverageAdmission(canonical(facts['admission']))
        assert facts['source_sha256']==sha(ROOT/'tests/thesis_lite/maestro/test_coverage_native.py')
        assert original.digest==facts['admission_digest'] and not facts['full_M1_complete'] and not facts['scientific_result']
        files=list({p.resolve() for p in private.glob('test_actual_original_public_in*/argus/retained-inputs.json')});assert len(files)==1
        data=files[0].read_bytes();assert json.loads(data)==facts['retained']
        reader=EvidenceStore.read_run(files[0].parent)
        entry=next(e for e in reader.manifest['artifacts'] if e['path']=='retained-inputs.json')
        observed=assess_preclosure(original,expected_admission_digest=facts['admission_digest'],
            annotations=facts['retained']['annotations'],public_m3=facts['retained']['publicM3'],
            broker=facts['broker'],artifact_entries=[entry],artifact_bytes={'retained-inputs.json':data})
        assert observed.report()==facts['report'];schema.validate(observed.report())
        assert observed.report()['overallStatus']=='incomplete' and observed.report()['normalRecordStatus']!='complete'
        assert any('CAUSAL' in d.code for d in reader.diagnostics)
        native.append(dict(phase=phase,path=str(path.relative_to(OUT)),sha256=sha(path),
            accepted_reader_diagnostics=[d.code for d in reader.diagnostics],full_runtime_complete=False))
assert len(closed)==4 and len(native)==2
output=dict(revision='ML3-AFFA17-2026-10-19-coverage-v5-component-audit',
    source_checks_passed=41,installed_wheel_checks_passed=41,source_snapshots=rows,
    retained_owned_roots_absent=roots,original_helper_waits=waits,public_native_snapshots=public,
    independent_closed_reader_audits=closed,actual_original_worker_gap_controls=native,
    original_fixtures_lost=0,full_M1_complete=False,U7_U8_runtime_complete=False,
    full_candidate_review_complete=False,stable_increment17=False,accepted=False,merged=False,
    canonical_note_edited=False,factory_run_created=False,scientific_result=False)
(OUT/'coverage-component-verification.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(dict(source_checks_passed=41,installed_checks_passed=41,roots_absent=len(roots),
    independent_closed_fixture_reads=len(closed),original_native_gap_reads=len(native))))
