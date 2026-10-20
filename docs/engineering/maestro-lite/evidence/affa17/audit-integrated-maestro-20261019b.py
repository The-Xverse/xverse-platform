"""Read-only terminal-phase inventory and public projections; no runtime verdict."""
import hashlib
import json
from pathlib import Path
import re
import sys
import sysconfig
import zipfile

from xverse.argus import EvidenceStore
from xverse.argus.schema import canonical_bytes
from xverse.maestro.collection_plan import decode_collection
from xverse.maestro.coverage import CoverageAdmission, canonical
from xverse.maestro.runtime_verification import runtime_admission_digest, verify_runtime_closed
from xverse_xdl.lifecycle import FileEvidenceJournal

out = Path(sys.argv[1]).resolve(strict=True)
phase = sys.argv[2]
assert phase in ('source', 'wheel')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
label = 'maestro_full-' + phase
receipt_path = out / (label + '-receipt.json')
receipt = read(receipt_path)  # missing terminal receipt refuses an audit
started = read(out / (label + '-started.json'))
assert receipt['original_pid'] == started['original_pid']
assert receipt['outer_timeout'] is False  # timeout needs a separate cleanup audit
log = out / (label + '.log')
assert sha(log) == receipt['log_sha256']
running = read(out / 'running.json')
frozen = read(out / 'frozen-inputs.json')
source = Path(running['frozen_source_root'])
assert all(sha(source / name) == digest for name, digest in frozen.items())
assert receipt['input_manifest_sha256'] == sha(out / 'frozen-inputs.json')
assert frozen == read(out.parent / 'runtime-disposal-20261019c/frozen-inputs.json')
assert len(frozen) == 273
collection = read(out / 'collection-receipt.json')
assert collection['collected'] == started['collected'] == 1501
control = read(out / 'control-inputs.json')
assert sha(out / 'receipt_namespace.py') == control['plugin_sha256'] == receipt['plugin_sha256']
assert sha(out.parent / 'verify-integrated-maestro-20261019b.py') == control['driver_sha256']
installed = Path(sysconfig.get_path('purelib'))
packaged = {n: h for n, h in frozen.items() if n.startswith('src/') and n.endswith(('.py', '.c'))}
wheel_path = next((out / 'dist').glob('*.whl'))
with zipfile.ZipFile(wheel_path) as wheel:
    for name, digest in packaged.items():
        entry = name.removeprefix('src/')
        assert hashlib.sha256(wheel.read(entry)).hexdigest() == digest == sha(installed / entry)
assert len(packaged) == 81
private = Path(started['private_basetemp']).resolve(strict=True)
harness = Path(started['receipt_root']).resolve(strict=True)
destination = out / (label + '-terminal-audit')
destination.mkdir(exist_ok=False)
inventory, roots, receipt_errors, fixtures, pins = [], [], [], {}, {}
for path in sorted(harness.rglob('*')):
    if not path.is_file():
        continue
    assert not path.is_symlink()
    inventory.append(dict(path=str(path.relative_to(out)), sha256=sha(path), bytes=path.stat().st_size))
    if path.suffix != '.json':
        continue
    try:
        data = read(path)
    except Exception as error:
        receipt_errors.append(dict(path=str(path.relative_to(out)), error=type(error).__name__))
        continue
    if not isinstance(data, dict):
        continue
    if path.name.startswith('maestro-component-') and 'root_name' in data:
        actual = Path(data['parent_path']) / data['root_name']
        roots.append(dict(receipt=str(path.relative_to(out)), sha256=sha(path),
            recorded_removed=data.get('root_removed'), recorded_workers_reaped=data.get('workers_reaped'),
            actual_path_absent=not actual.exists(), identity=data.get('root_identity')))
    fixture_name = data.get('original_fixture')
    if not isinstance(fixture_name, str):
        for prefix in ('run-broker-waits-', 'run-bootstrap-waits-', 'runtime-entry-waits-'):
            if path.stem.startswith(prefix):
                fixture_name = str(private / path.stem.removeprefix(prefix))
                break
    if fixture_name is None:
        continue
    fixture = Path(fixture_name).resolve()
    assert fixture.is_relative_to(private), 'fixture outside original phase'
    fixtures.setdefault(str(fixture), []).append(str(path.relative_to(out)))
    if path.name.startswith('entry-original-inputs-'):
        assert str(fixture) not in pins
        pins[str(fixture)] = (path, data)

projections, closed = [], []
for index, (fixture_name, references) in enumerate(sorted(fixtures.items())):
    fixture = Path(fixture_name)
    data = dict(original_fixture=fixture_name, original_receipts=references,
        maturity='owned_public_projection_only', m3=[], argus=[], reader_gaps=[])
    if not fixture.is_dir():
        data['reader_gaps'].append(dict(source='original fixture', error='missing'))
    else:
        try:
            if not (fixture / 'm3.jsonl').is_file():
                raise FileNotFoundError()
            data['m3'] = list(FileEvidenceJournal(fixture / 'm3.jsonl').public_records())
        except Exception as error:
            data['reader_gaps'].append(dict(source='M3', error=type(error).__name__))
        try:
            data['argus'] = list(EvidenceStore.read_run(fixture / 'argus').records())
        except Exception as error:
            data['reader_gaps'].append(dict(source='Argus', error=type(error).__name__))
    by_sequence = {r['sequence']: r for r in data['m3']}
    mirrored, links = set(), 0
    for event in data['argus']:
        for ref in event.get('extensions', {}).get('xverse.maestro', {}).get('sourceRefs', []):
            if ref.get('kind') != 'm3-record':
                continue
            actual = by_sequence.get(ref['sequence'])
            if actual is None or ref['sha256'] != 'sha256:' + hashlib.sha256(canonical_bytes(actual)).hexdigest():
                data['reader_gaps'].append(dict(source='M3 reference', event=event['eventId'], reference=ref))
            else:
                mirrored.add(ref['sequence'])
                links += 1
    for sequence in sorted(by_sequence.keys() - mirrored):
        data['reader_gaps'].append(dict(source='Argus mirror', m3_sequence=sequence))
    data['actual_normal_source_hashes_verified'] = links
    target = destination / ('projection-' + str(index) + '.json')
    with target.open('x') as stream:
        json.dump(data, stream, indent=2)
        stream.write('\n')
    projections.append(dict(path=str(target.relative_to(out)), sha256=sha(target),
        original_fixture=fixture_name, source_links=links, reader_gaps=len(data['reader_gaps'])))
    if fixture_name in pins:
        pin_path, original = pins[fixture_name]
        result = dict(original_inputs=str(pin_path.relative_to(out)), inputs_sha256=sha(pin_path),
            original_fixture=fixture_name, independently_held_custody_proven=False)
        try:
            admission = CoverageAdmission(canonical(original['original_admission']))
            plan = decode_collection(original['original_collection'], admission, original['admission_digest'])
            assert runtime_admission_digest(admission, plan, original['generation_ns']) == original['runtime_digest']
            verified = verify_runtime_closed(admission, plan, fixture / 'argus',
                expected_admission_digest=original['admission_digest'], generation_ns=original['generation_ns'],
                expected_runtime_digest=original['runtime_digest'])
            result['complete'] = verified.complete
        except Exception as error:
            result['complete'] = None
            result['error'] = type(error).__name__
        closed.append(result)

summaries = [line for line in log.read_text().splitlines() if re.search(r'\d+ (passed|failed|skipped|error)', line)]
summary = summaries[-1] if summaries else None
counts = {name: int(m.group(1)) if summary and (m := re.search(r'(\d+) ' + ('errors?' if name == 'errors' else name) + r'\b', summary)) else 0
          for name in ('passed', 'failed', 'skipped', 'errors', 'xfailed', 'xpassed')}
assert (receipt['returncode'] == 0) == (counts['failed'] == counts['errors'] == 0)
if counts['errors'] == 0:
    assert sum(counts.values()) == collection['collected']
failures = [line for line in log.read_text().splitlines() if line.startswith(('FAILED ', 'ERROR '))]
result = dict(auditor_sha256=sha(Path(__file__)), phase=phase, terminal_receipt_sha256=sha(receipt_path),
    original_returncode=receipt['returncode'], original_summary=summary, observed_counts=counts,
    collected_per_phase=collection['collected'], exact_affected_snapshot_manifest_sha256=sha(out.parent / 'runtime-disposal-20261019c/frozen-inputs.json'),
    original_failure_lines=failures, frozen_files_checked=len(frozen), packaged_python_c_files=81,
    wheel_sha256=sha(wheel_path), receipt_inventory=inventory, receipt_parse_errors=receipt_errors,
    root_reservations=roots, all_recorded_roots_removed_and_workers_reaped=bool(roots) and all(
        r['recorded_removed'] and r['recorded_workers_reaped'] and r['actual_path_absent'] for r in roots),
    public_projections=projections, original_input_closed_recomputations=closed,
    source_links=sum(row['source_links'] for row in projections),
    projection_reader_gaps=sum(row['reader_gaps'] for row in projections),
    negative_control_gaps_not_classified_as_product_defects=True,
    complete_runtime_case_coverage_proven=False, actual_M1_admissions=0,
    whole_platform_regression=False, cause_proven=False, CAPA_effectiveness_proven=False,
    stable_increment17=False, accepted=False, merged=False)
with (destination / 'audit.json').open('x') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print(json.dumps({k: v for k, v in result.items() if not isinstance(v, list)}))
