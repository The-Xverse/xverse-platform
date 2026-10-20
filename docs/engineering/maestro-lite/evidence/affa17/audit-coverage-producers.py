"""Audit exact passing producer component snapshots, preserving known remaining gaps."""
from pathlib import Path
import hashlib,json,re,sys
from jsonschema import Draft202012Validator
from xverse.argus import EvidenceStore
from xverse.maestro.coverage import CoverageAdmission,canonical,assess_preclosure
OUT=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
version=int(sys.argv[1]);assert version in (3,4)
tag='coverage-producers-v'+str(version);expected=213 if version==3 else 223
run=read(OUT/(tag+'-running.json'));ROOT=Path(run['frozen_source_root'])
frozen=read(OUT/(tag+'-frozen-inputs.json'));assert all(sha(ROOT/n)==h for n,h in frozen.items())
identity=read(OUT/(tag+'-installed-identity.json'));assert len(identity)==38
for name,fact in identity.items():assert sha(Path(fact['file']))==fact['sha256']==sha(ROOT/'src/xverse/maestro'/name)
regression=read(OUT/(tag+'-regression.json'));assert regression['affected_regression_passed']
validator=Draft202012Validator(read(ROOT/'tests/thesis_lite/maestro/lifecycle-payload-v2.schema.json'))
coverage_schema=Draft202012Validator(read(ROOT/'tests/thesis_lite/maestro/lifecycle-coverage-v2.schema.json'))
roots=[];waits=[];public=[];native=[]
for phase in ('source','wheel'):
    base=tag+'-'+phase;receipt=read(OUT/(base+'-receipt.json'));log=OUT/(base+'.log')
    assert receipt['returncode']==0 and receipt['public_capture_returncode']==0
    assert str(expected)+' passed' in log.read_text() and sha(log)==receipt['log_sha256']
    directory=OUT/(base+'-harness')
    for f in directory.glob('maestro-component-*.json'):
        j=read(f);assert j['root_removed'] and j['workers_reaped'] and not (Path(j['parent_path'])/j['root_name']).exists()
        roots.append(dict(path=str(f.relative_to(OUT)),sha256=sha(f)))
    for f in directory.glob('run-broker-waits-*.json'):
        j=read(f);assert j['bootstrap_reaped'] and j['registered_helpers_reaped'] and j['storage_reaped'] and j['original_C1_released']
        waits.append(dict(path=str(f.relative_to(OUT)),sha256=sha(f)))
    snapshots=read(OUT/(base+'-public-evidence-index.json'))
    assert all(sha(OUT/f['snapshot'])==f['sha256'] for f in snapshots);public.extend(snapshots)
    exports=list(directory.glob('coverage-producer-public-*.json'));assert len(exports)==1
    for path in exports:
        facts=read(path);assert facts['source_sha256']==sha(ROOT/'tests/thesis_lite/maestro/test_coverage_producers.py')
        assert not facts['full_M1_complete'] and not facts['scientific_result']
        admission=CoverageAdmission(canonical(facts['admission']));assert admission.digest==facts['admission_digest']
        private=Path(receipt['original_private_basetemp'])
        original=list({f.resolve() for f in private.glob('test_real_validation_flush_pre*/argus/retained-inputs.json')});assert len(original)==1
        raw=original[0].read_bytes();assert json.loads(raw)==facts['retained']
        reader=EvidenceStore.read_run(original[0].parent)
        assert not any('CAUSAL' in d.code for d in reader.diagnostics)
        entry=next(e for e in reader.manifest['artifacts'] if e['path']=='retained-inputs.json')
        actual=assess_preclosure(admission,expected_admission_digest=facts['admission_digest'],
            annotations=facts['retained']['annotations'],public_m3=facts['retained']['publicM3'],
            broker=facts['broker'],artifact_entries=[entry],artifact_bytes={'retained-inputs.json':raw})
        assert actual.report()==facts['report'];coverage_schema.validate(actual.report())
        report=actual.report();assert report['overallStatus']=='incomplete'
        assert next(r for r in report['rows'] if r['obligationId']=='ob.run-validation')['status']=='satisfied'
        if version==4:
            assert next(r for r in report['rows'] if r['obligationId']=='ob.input-integrity')['status']=='satisfied'
            assert all(r['status']=='satisfied' for r in report['rows'] if r['obligationId'].endswith(('.stop','.cleanup')))
        sources={r['sequence']:r for r in facts['retained']['publicM3']};links=0
        for e in facts['retained']['annotations']:
            payload=e['extensions']['xverse.maestro'];validator.validate(payload)
            for ref in payload['sourceRefs']:
                if ref['kind']=='m3-record':
                    assert ref['sha256']=='sha256:'+hashlib.sha256(canonical(sources[ref['sequence']])).hexdigest();links+=1
        native.append(dict(phase=phase,path=str(path.relative_to(OUT)),sha256=sha(path),actual_source_links=links,
            externally_pinned_admission=facts['admission_digest'],original_reader_causal_diagnostics_absent=True,
            normal_teardown_reference_defect_112_present=version==3,normal_teardown_rows_verified=version==4))
assert len(native)==2
result=dict(revision=tag+'-exact-passing-component-audit',source_checks_passed=expected,installed_wheel_checks_passed=expected,
    source_manifest_sha256=sha(OUT/(tag+'-frozen-inputs.json')),installed_identity_sha256=sha(OUT/(tag+'-installed-identity.json')),
    wheel_sha256=regression['wheel_sha256'],owned_roots_absent=roots,original_helper_waits=waits,
    public_snapshots=len(public),actual_public_source_links=sum(f['source_links'] for f in public),original_native_coverage_controls=native,
    original_fixtures_lost=sum(any(g['source']=='original fixture' for g in f['reader_gaps']) for f in public),
    no_isolated_timing_claim=True,all_prior_timing_failures_explained=False,
    component_scope_only=True,full_M1_complete=False,U7_U8_runtime_complete=False,full_platform_regression=False,
    stable_increment17=False,full_candidate_review_complete=False,accepted=False,merged=False,
    canonical_note_edited=False,factory_run_created=False,scientific_result=False)
(OUT/(tag+'-verification.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(version=version,source_passed=expected,wheel_passed=expected,roots_absent=len(roots),
    original_helper_waits=len(waits),public_snapshots=len(public),source_links=result['actual_public_source_links'],fixtures_lost=result['original_fixtures_lost'])))
