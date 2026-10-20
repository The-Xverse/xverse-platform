"""Read-only exact-snapshot audit; inspect actual closed bytes and original sources."""
from pathlib import Path
import hashlib
import json
from jsonschema import Draft202012Validator
from xverse.argus import EvidenceStore
from xverse.maestro.coverage import CoverageAdmission, canonical, assess_preclosure
from xverse.maestro.public_blobs import decode_broker_data

OUT = Path(__file__).resolve().parent / 'runtime-collection-execution-20261019b'
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
run = read(OUT / 'running.json'); root = Path(run['frozen_source_root'])
manifest = read(OUT / 'frozen-inputs.json')
assert all(sha(root / n) == h for n, h in manifest.items())
identity = read(OUT / 'installed-identity.json'); assert len(identity) == 41
assert all(sha(Path(r['file'])) == r['sha256'] == sha(root / 'src/xverse/maestro' / n) for n, r in identity.items())
result = read(OUT / 'result-after-wheel.json')
assert result['component_checks_passed'] and result['collected_per_phase'] == 250
assert sha(OUT / 'dist/xverse_xdl-0.4.0-py3-none-any.whl') == result['wheel_sha256']
validator = Draft202012Validator(read(root / 'tests/thesis_lite/maestro/lifecycle-payload-v2.schema.json'))
coverage_schema = Draft202012Validator(read(root / 'tests/thesis_lite/maestro/lifecycle-coverage-v2.schema.json'))
roots = []; waits = []; public = []; controls = []
for phase in ('source', 'wheel'):
    receipt = read(OUT / (phase + '-receipt.json'))
    assert receipt['returncode'] == receipt['public_capture_returncode'] == 0
    log = OUT / (phase + '.log')
    assert '250 passed' in log.read_text() and sha(log) == receipt['log_sha256']
    directory = OUT / (phase + '-harness')
    for path in directory.glob('maestro-component-*.json'):
        fact = read(path)
        assert fact['root_removed'] and fact['workers_reaped']
        assert not (Path(fact['parent_path']) / fact['root_name']).exists()
        roots.append(dict(path=str(path.relative_to(OUT)), sha256=sha(path)))
    for path in directory.glob('run-broker-waits-*.json'):
        fact = read(path)
        assert all(fact[k] for k in ('bootstrap_reaped', 'registered_helpers_reaped', 'storage_reaped', 'original_C1_released'))
        waits.append(dict(path=str(path.relative_to(OUT)), sha256=sha(path)))
    index = read(OUT / (phase + '-public-evidence-index.json'))
    assert all(sha(OUT / f['snapshot']) == f['sha256'] for f in index)
    public.extend(index)
    exported = list(directory.glob('collection-runtime-public-*.json')); assert len(exported) == 2
    for path in exported:
        fact = read(path)
        assert fact['source_sha256'] == sha(root / 'tests/thesis_lite/maestro/test_collection_runtime.py')
        assert not fact['full_M1_complete'] and not fact['scientific_result']
        original = Path(fact['original_fixture']); evidence = original / 'argus'
        admission = CoverageAdmission(canonical(fact['admission']))
        assert admission.digest == fact['admission_digest']
        raw = (evidence / fact['receipt']['entry']['path']).read_bytes()
        metadata = read(evidence / fact['receipt']['entry']['path'])
        assert metadata == fact['metadata'] and raw == canonical(metadata)
        assert fact['receipt']['entry']['bytes'] == len(raw)
        assert fact['receipt']['entry']['sha256'] == hashlib.sha256(raw).hexdigest()
        assert metadata['contextDigest'] == 'sha256:' + hashlib.sha256(canonical(metadata['context'])).hexdigest()
        broker = decode_broker_data(canonical(metadata['context']['broker']), admission, admission.digest,
                                    observed_until=metadata['startedAt'])
        assert broker['nativeCancellationAcknowledged'] is True and metadata['startsFenced'] is True
        assert metadata['collectionComplete'] is True
        stat = (original / 'work').stat()
        assert metadata['sourceRootIdentity'] == [stat.st_dev, stat.st_ino]
        rows = {(r['unitId'], r['generation']): r for r in broker['generations']}
        copied = 0
        for item in metadata['items']:
            if item['status'] == 'missing':
                assert item['required'] is False and item['entry'] is None
                continue
            assert item['status'] == 'collected'
            declared = next(r for r in fact['admission']['artifacts'] if r['path'] == item['destination'])
            assert (declared['unitId'], declared['generation'], declared['required']) == (
                item['unitId'], item['generation'], item['required'])
            assert item['bytes'] <= declared['maximumBytes']
            row = rows[item['unitId'], item['generation']]
            assert all(row[k] is True for k in ('issued', 'directChildReaped', 'c1Empty', 'c1Released'))
            actual = (evidence / item['destination']).read_bytes()
            assert actual == (original / 'work' / item['source']).read_bytes() == b'EXEC\n'
            assert item['bytes'] == len(actual) and item['sha256'] == hashlib.sha256(actual).hexdigest()
            copied += 1
        reader = EvidenceStore.read_run(evidence)
        assert reader.manifest['writerState'] == 'failed'
        assert fact['receipt']['entry'] in reader.manifest['artifacts']
        assert not any('ARTIFACT' in d.code or 'CAUSAL' in d.code for d in reader.diagnostics)
        retained_event = fact['receipt']['event']; validator.validate(retained_event['extensions']['xverse.maestro'])
        actual_event = next(e for e in reader.records() if e['eventId'] == retained_event['eventId'])
        assert canonical({k: actual_event[k] for k in retained_event}) == canonical(retained_event)
        assert retained_event['annotation']['text'].endswith('sha256:' + hashlib.sha256(raw).hexdigest())
        coverage_verified = False
        if 'provisional_report' in fact:
            entries = reader.manifest['artifacts']; actual_bytes = {e['path']: (evidence / e['path']).read_bytes() for e in entries}
            report = assess_preclosure(admission, expected_admission_digest=admission.digest,
                annotations=fact['retained']['annotations'], public_m3=fact['retained']['publicM3'], broker=fact['broker'],
                artifact_entries=entries, artifact_bytes=actual_bytes).report()
            assert report == fact['provisional_report']; coverage_schema.validate(report)
            assert report['overallStatus'] == 'incomplete'
            assert next(r for r in report['rows'] if r['obligationId'] == 'ob.collect')['status'] == 'satisfied'
            assert next(r for r in report['rows'] if r['obligationId'] == 'ob.run-terminal')['status'] == 'missing'
            coverage_verified = True
        controls.append(dict(phase=phase, path=str(path.relative_to(OUT)), sha256=sha(path),
            actual_native_output_files=copied, actual_metadata_bytes=len(raw), original_closed_reader_checked=True,
            provisional_collect_row_verified=coverage_verified, full_lifecycle_complete=False))

assert len(controls) == 4 and sum(r['provisional_collect_row_verified'] for r in controls) == 2
summary = dict(source_passed=250, installed_wheel_passed=250,
    source_manifest_sha256=sha(OUT / 'frozen-inputs.json'), installed_identity_sha256=sha(OUT / 'installed-identity.json'),
    wheel_sha256=result['wheel_sha256'], original_roots_absent=roots, original_broker_helper_waits=waits,
    public_snapshots=len(public), original_source_links=sum(f['source_links'] for f in public),
    original_fixtures_lost=sum(any(g['source'] == 'original fixture' for g in f['reader_gaps']) for f in public),
    real_collection_controls=controls, context_and_item_bytes_verified=True,
    original_private_collection_plan_independently_rederived_by_this_audit=False,
    earlier_109_pass_1_failure_explained=False, earlier_813_pass_1_failure_explained=False,
    terminal_lease_service_verified=False, lazy_issuance_complete=False, terminal_and_writer_closure_complete=False,
    full_platform_regression=False, full_M1_complete=False, stable_increment17=False, full_candidate_review_complete=False,
    accepted=False, merged=False, canonical_note_edited=False, factory_run_created=False, scientific_result=False)
with (OUT / 'verification.json').open('x') as stream:
    stream.write(json.dumps(summary, indent=2) + '\n')
print(json.dumps(dict(source=250, wheel=250, roots=len(roots), helper_waits=len(waits),
    native_collection_exports=len(controls), source_links=summary['original_source_links'], lost_fixtures=summary['original_fixtures_lost'])))
