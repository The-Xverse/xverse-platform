"""Retain actual instrumented worker timings; no performance/stability inference."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys
import tarfile

BASE=Path(__file__).resolve().parent;OUT=BASE/'persistence-cost-20261019a'
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
run=read(OUT/'running.json');root=Path(run['frozen_source_root'])
manifest=read(OUT/'frozen-inputs.json');identity=read(OUT/'installed-identity.json')
assert all(sha(root/p)==h for p,h in manifest.items())
assert len(identity)==46 and all(sha(Path(r['file']))==r['sha256']==manifest['src/xverse/maestro/'+n] for n,r in identity.items())
rows=[];waits=roots=links=0
for phase in ('source','wheel'):
 receipt=read(OUT/(phase+'-receipt.json'));assert receipt['returncode']==receipt['public_capture_returncode']==0
 assert sha(OUT/(phase+'.log'))==receipt['log_sha256']
 assert (OUT/(phase+'.log')).read_text().splitlines()[-1].startswith('2 passed')
 files=[];harness=OUT/(phase+'-harness')
 for p in harness.glob('worker-cost-helper-*.json'):
  r=read(p);assert r['admission_precedes_birth'] and r['unchanged_original_assertions_and_bounds']
  assert r['observer_io_overhead_included'] and not r['production_diagnostic_mode_added']
  assert r['source_sha256']==manifest['tests/thesis_lite/maestro/test_persistence_profile.py']
  assert r['original_native_source_sha256']==manifest['src/xverse/maestro/native/bootstrap.c']
  code=r['fixed_diagnostic_code'];assert hashlib.sha256(code.encode()).hexdigest()==r['fixed_diagnostic_code_sha256']
  source,binary=Path(r['command'][-4]),Path(r['command'][-1]);assert sha(source)==r['compiled_source_sha256'] and sha(binary)==r['binary_sha256']
  anchor='args[2]="-m";args[3]="xverse.maestro.persistence_worker"'
  original=(root/'src/xverse/maestro/native/bootstrap.c').read_text();assert original.count(anchor)==1
  assert source.read_text()==original.replace(anchor,'args[2]="-c";args[3]='+json.dumps(code))
  raw=Path(r['profile_file']);lines=raw.read_bytes().splitlines();assert lines and len(lines)<4096
  costs=[json.loads(line) for line in lines];assert all(set(x)=={'rpc','kind','unit','deadline','label','began','ended','depth','error'} for x in costs)
  assert all(x['ended']>=x['began'] and x['depth']>=0 for x in costs)
  case='lazy-nominal' if 'lazy-nominal' in p.name else 'paused-shared'
  operations=read(harness/('lazy-operations-test_original_persistence_costs_with_unchanged_oracles-'+case+'.json'))['operations']
  groups=defaultdict(list)
  for x in costs:
   if x['rpc']:
    actual=operations[x['rpc']-1];assert x['kind']==actual['kind'] and x['unit']==actual['unit']
   groups[x['rpc']].append(x)
  rpc=[]
  for number,group in sorted(groups.items()):
   totals=defaultdict(float);counts=defaultdict(int)
   for x in group:totals[x['label']]+=x['ended']-x['began'];counts[x['label']]+=1
   actual=operations[number-1] if number else None
   rpc.append(dict(sequence=number,kind=group[0]['kind'],unit=group[0]['unit'],
    original_client=actual,inclusive_nested_seconds=dict(totals),call_counts=dict(counts),
    worker_errors=[x['label']+':'+x['error'] for x in group if x['error']]))
  target=OUT/(phase+'-worker-cost-'+case+'.jsonl')
  with target.open('xb') as f:f.write(raw.read_bytes())
  files.extend((source,binary,raw))
  rows.append(dict(phase=phase,case=case,helper_receipt=str(p.relative_to(OUT)),helper_receipt_sha256=sha(p),
    retained_profile=str(target.relative_to(OUT)),retained_profile_sha256=sha(target),timing_rows=len(costs),rpcs=rpc))
 for p in harness.glob('run-broker-waits-*.json'):
  r=read(p);assert all(r[k] for k in ('bootstrap_reaped','registered_helpers_reaped','storage_reaped','original_C1_released'));waits+=1
 for p in harness.glob('maestro-component-*.json'):
  r=read(p);assert r['root_removed'] and r['workers_reaped'] and not (Path(r['parent_path'])/r['root_name']).exists();roots+=1
 for r in read(OUT/(phase+'-public-evidence-index.json')):
  p=OUT/r['snapshot'];assert sha(p)==r['sha256'] and not r['reader_gaps'];links+=r['source_links']
  public=read(p);assert public['original_fixture'] and public['m3'] and public['argus']
 # Retain public output bytes plus exact diagnostic helper and observations only.
 private=Path(receipt['original_private_basetemp'])
 for p in private.rglob('*'):
  if p.is_file() and not p.is_symlink() and ('argus' in p.relative_to(private).parts or p.name=='m3.jsonl'):files.append(p)
 assert sum(p.stat().st_size for p in files)<32<<20
 with (OUT/(phase+'-owned-public-and-diagnostic-bytes.tar.gz')).open('xb') as stream:
  with tarfile.open(fileobj=stream,mode='w:gz') as archive:
   for p in files:archive.add(p,arcname=str(p.relative_to(private)),recursive=False)
assert len(rows)==4 and waits==roots==4
result=dict(original_driver_session=5400,original_driver_terminal_exit=0,phases=[dict(phase=p,passed=2,failed=0) for p in ('source','wheel')],
 original_broker_waits=waits,original_roots_absent=roots,actual_source_links=links,profiles=rows,
 source_manifest_sha256=sha(OUT/'frozen-inputs.json'),installed_identity_sha256=sha(OUT/'installed-identity.json'),
 wheel_sha256=sha(OUT/'dist/xverse_xdl-0.4.0-py3-none-any.whl'),auditor_sha256=sha(Path(__file__)),
 production_code_changed=False,original_assertions_and_bounds_preserved=True,observer_overhead_included=True,
 historical_timeout_cause_proved=False,timing_stability_proved=False,stable_increment17=False,accepted=False,merged=False)
with (OUT/'verification.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(profiles=len(rows),original_broker_waits=waits,original_roots_absent=roots,actual_source_links=links,
 production_changed=False,historical_timeout_cause_proved=False)))
