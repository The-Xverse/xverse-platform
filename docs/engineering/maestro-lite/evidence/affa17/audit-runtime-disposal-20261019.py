"""Audit original disposal sources and retained failures; no native execution."""
import hashlib
import json
from pathlib import Path
import re
import sys
import sysconfig
import zipfile

from xverse.argus import EvidenceStore
from xverse.argus.schema import canonical_bytes
from xverse_xdl.lifecycle import FileEvidenceJournal

out = Path(sys.argv[1]).resolve(strict=True)
repaired = sys.argv[2] == 'repair'
assert sys.argv[2] in ('red', 'repair')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
frozen = read(out / 'frozen-inputs.json')
source = Path(read(out / 'running.json')['frozen_source_root'])
assert all(sha(source / n) == h for n, h in frozen.items())
production = {n:h for n,h in frozen.items() if n.startswith('src/') and n.endswith(('.py','.c'))}
assert len(production) == 81
red = read(out.parent / 'runtime-disposal-20261019a/frozen-inputs.json')
changed = sorted(n for n,h in production.items() if red[n] != h)
assert changed == (['src/xverse/maestro/persistence.py','src/xverse/maestro/run_broker.py'] if repaired else [])
installed = Path(sysconfig.get_path('purelib'))
with zipfile.ZipFile(next((out/'dist').glob('*.whl'))) as wheel:
    for name, digest in production.items():
        entry = name.removeprefix('src/')
        assert hashlib.sha256(wheel.read(entry)).hexdigest() == digest == sha(installed/entry)

phases, roots, cases, projections = [], [], [], []
seen = set()
for path in sorted(out.glob('*-receipt.json')):
    receipt = read(path)
    if 'cohort' not in receipt:
        continue
    label = path.name.removesuffix('-receipt.json')
    log = out/(label+'.log')
    assert sha(log) == receipt['log_sha256'] and receipt['public_capture_returncode'] == 0
    assert receipt['input_manifest_sha256'] == sha(out/'frozen-inputs.json')
    last = log.read_text().splitlines()[-1]
    counts = {key:int(m.group(1)) if (m:=re.search(r'(\d+) '+('errors?' if key=='errors' else key),last)) else 0
              for key in ('passed','failed','errors')}
    assert sum(counts.values()) > 0
    assert (receipt['returncode']==0) == (counts['failed']==counts['errors']==0)
    phases.append(dict(cohort=receipt['cohort'],phase=receipt['phase'],**counts,
        returncode=receipt['returncode'],receipt_sha256=sha(path)))
    harness = out/(label+'-harness')
    for raw in harness.glob('maestro-component-*.json'):
        row = read(raw)
        identity = row['parent_path'],row['root_name']
        assert identity not in seen
        seen.add(identity)
        assert row['root_removed'] and row['workers_reaped']
        assert not (Path(row['parent_path'])/row['root_name']).exists()
        roots.append(dict(path=str(raw.relative_to(out)),sha256=sha(raw)))
    for raw in harness.glob('runtime-disposal-*.json'):
        row = read(raw)
        assert row['actual_original_root_wait'] and row['actual_original_helper_waits']
        assert row['all_original_C1_released'] and row['live_disposal_rejected']
        assert row['actual_M1_admissions']==0 and not row['full_runtime_case_complete']
        assert row['root_wait_before_disposal'] and row['registered_helper_wait_before_disposal']
        if row['case']=='late-root-wait':
            assert row['hidden_client_wait_observations'] > 0
            assert row['earlier_drain']['worker_reaped'] is False
            assert row['earlier_drain']['diagnostic']=='ML-PERSIST-DRAIN-UNRESOLVED'
        else:
            assert row['reused_released_broker_fd']
        if repaired:
            assert row['protected_close_attempts']==0 and not row['disposal_errors']
            assert row['earlier_drain_unchanged'] and row['original_result_unchanged']
            if row['case']=='broker-close-error':
                assert row['injected_close_error_after_actual_close'] and row['close_uncertainty_retained']
                assert row['external_local_disposal'] and not row['product_disposed']
            else:
                assert row['product_disposed'] and row['matching_disposal_retained']
                assert not row['external_local_disposal']
            assert not row['external_storage_drain_refresh']
            if row['case']!='late-root-wait':
                assert row['canary_untouched']
        else:
            assert not row['product_disposed'] and row['external_local_disposal']
            assert row['protected_close_attempts'] == (0 if row['case']=='late-root-wait' else 1)
            assert row['external_storage_drain_refresh'] is (row['case']=='late-root-wait')
            assert len(row['disposal_errors'])==1
        cases.append(dict(phase=receipt['phase'],case=row['case'],path=str(raw.relative_to(out)),
            sha256=sha(raw),product_disposed=row['product_disposed'],
            external_local_disposal=row['external_local_disposal'],
            protected_close_attempts=row['protected_close_attempts'],
            primary_execution_succeeded=row['primary_execution_succeeded']))
    for item in read(out/(label+'-public-evidence-index.json')):
        raw = out/item['snapshot']
        assert sha(raw)==item['sha256']
        data = read(raw)
        if data['original_fixture'] is None:
            assert any(g['source']=='original fixture' for g in data['reader_gaps'])
            assert not data['m3'] and not data['argus']
            projections.append(dict(label=label,**item))
            continue
        fixture = Path(data['original_fixture'])
        records = list(FileEvidenceJournal(fixture/'m3.jsonl').public_records()) if (fixture/'m3.jsonl').is_file() else []
        assert data['m3']==records
        try:
            events = list(EvidenceStore.read_run(fixture/'argus').records())
        except Exception:
            assert any(g['source']=='Argus' for g in data['reader_gaps'])
            events = []
        assert data['argus']==events
        by_sequence = {r['sequence']:r for r in records}
        links = 0
        for event in events:
            for ref in event.get('extensions',{}).get('xverse.maestro',{}).get('sourceRefs',[]):
                if ref.get('kind')=='m3-record' and (actual:=by_sequence.get(ref['sequence'])) is not None:
                    if ref['sha256']=='sha256:'+hashlib.sha256(canonical_bytes(actual)).hexdigest():
                        links+=1
        assert links==item['source_links']==data['actual_normal_source_hashes_verified']
        projections.append(dict(label=label,**item))

expected_cases = ['late-root-wait','broker-repeat','entry-retry']+(['broker-close-error'] if repaired else [])
assert {(r['phase'],r['case']) for r in cases} == {(p,c) for p in ('source','wheel') for c in expected_cases}
assert len(cases)==2*len(expected_cases)
for phase in ('source','wheel'):
    row = next(r for r in phases if r['cohort']=='runtime_disposal' and r['phase']==phase)
    assert (row['passed'],row['failed'],row['errors'])==((4,0,0) if repaired else (0,3,0))
counts = {p:{k:sum(r[k] for r in phases if r['phase']==p) for k in ('passed','failed','errors')}
          for p in ('source','wheel')}
result = dict(auditor_sha256=sha(Path(__file__)),phases=phases,counts=counts,
    frozen_manifest_sha256=sha(out/'frozen-inputs.json'),packaged_python_c_files=81,
    changed_packaged_sources=changed,other_packaged_sources_unchanged=81-len(changed),
    root_receipts=roots,disposal_cases=cases,public_projections=projections,
    source_links=sum(r['source_links'] for r in projections),
    source_projection_gaps=sum(len(r['reader_gaps']) for r in projections),
    earlier_wait_and_execution_outcomes_preserved=True,actual_M1_admissions=0,
    independent_cause_confirmation=False,CAPA_effectiveness_demonstrated=False,
    full_maestro_regression_passed=False,whole_platform_regression=False,
    stable_increment17=False,accepted=False,merged=False)
with (out/'verification.json').open('x') as stream:
    json.dump(result,stream,indent=2)
    stream.write('\n')
print(json.dumps(dict(counts=counts,original_owned_roots_absent=len(roots),
    source_links=result['source_links'],source_projection_gaps=result['source_projection_gaps'],
    product_disposed_cases=sum(r['product_disposed'] for r in cases),
    external_local_disposal_cases=sum(r['external_local_disposal'] for r in cases))))
