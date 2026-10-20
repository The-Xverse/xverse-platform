"""Audit every diagnostic outcome and actual public source link, including gaps."""
from pathlib import Path
import hashlib
import json
from xverse.argus.schema import canonical_bytes

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[4]
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
frozen=read(OUT/'preparation-v2-frozen-inputs.json')
assert all(sha(ROOT/n)==h for n,h in frozen.items())
rows=[]
for family,count in [('nominal',5)]:
    for i in range(1,count+1):
        name='preparation-v2-'+family+'-'+str(i)
        receipt=read(OUT/(name+'-receipt.json'))
        rpc=read(OUT/(name+'-rpc.json'))
        assert receipt['log_sha256']==sha(OUT/(name+'.log'))
        assert receipt['rpc_sha256']==sha(OUT/(name+'-rpc.json'))
        directory=OUT/(name+'-harness')
        snapshots=list(directory.glob('dispatcher-snapshot-*-test_full_five_phase_dispatch_records_actual_outcomes_and_dispositions.json'))
        assert len(snapshots)==1
        snapshot=snapshots[0];data=read(snapshot)
        assert data['source_sha256']==sha(ROOT/'tests/thesis_lite/maestro/test_dispatcher.py')
        records={r['sequence']:r for r in data['public_m3']}
        mirrored=set();links=0;gaps=[]
        for event in data['events']:
            for ref in event.get('extensions',{}).get('xverse.maestro',{}).get('sourceRefs',[]):
                if ref['kind']=='m3-record':
                    r=records.get(ref['sequence'])
                    if r is not None and ref['sha256']=='sha256:'+hashlib.sha256(canonical_bytes(r)).hexdigest():
                        links+=1;mirrored.add(ref['sequence'])
                    else:gaps.append(dict(kind='missing_or_mismatched_source',event=event['eventId'],reference=ref))
        gaps.extend(dict(kind='missing_mirror',sequence=s) for s in records.keys()-mirrored)
        roots=list(directory.glob('maestro-component-*.json'))
        assert len(roots)==1
        for p in roots:
            facts=read(p)
            assert facts['root_removed'] and facts['workers_reaped']
            assert not (Path(facts['parent_path'])/facts['root_name']).exists()
        waits=list(directory.glob('bootstrap-children-*.json'))
        assert len(waits)==1
        facts=read(waits[0])
        assert facts['supervisor_reaped'] and facts['registered_children_reaped'] and facts['all_original_boundaries_released']
        rows.append(dict(name=name,returncode=receipt['returncode'],receipt_sha256=sha(OUT/(name+'-receipt.json')),
            observed_failed_RPCS=[r for r in rpc if not r['acknowledged']],snapshot=str(snapshot.relative_to(OUT)),
            snapshot_sha256=sha(snapshot),actual_source_hash_links_verified=links,reader_gaps=gaps,
            owned_root_absent=True,original_helper_waits_observed=True,
            instrumentation_can_affect_timing=family=='syscall',
            root_cause_proven=False))
assert [r['returncode'] for r in rows]==[0,0,0,0,0]
result=dict(attempts=rows,all_original_failures_retained=True,source_inputs_unchanged=True,
    all_five_nominal_cases_passed=True,root_cause_proven=False,
    full_regression_passed=False,stable_increment17=False,full_M1_complete=False,
    full_phase3_complete=False,accepted=False,merged=False)
(OUT/'preparation-v2-nominal-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(diagnostic_attempts=len(rows),passed=sum(r['returncode']==0 for r in rows),
    failed=sum(r['returncode']!=0 for r in rows),actual_source_links=sum(r['actual_source_hash_links_verified'] for r in rows),
    snapshots_with_gaps=sum(bool(r['reader_gaps']) for r in rows),owned_roots_absent=len(rows),root_cause_proven=False)))
