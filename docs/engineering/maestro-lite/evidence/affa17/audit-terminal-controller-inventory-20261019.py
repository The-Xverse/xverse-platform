"""Exact original v6 report, future universe and retired/current helper inventory."""
import hashlib
import json
from pathlib import Path
import re
import sys
import sysconfig
import tarfile
import zipfile

from xverse.argus import EvidenceStore
from xverse.argus.schema import canonical_bytes
from xverse_xdl.lifecycle import FileEvidenceJournal
from xverse.maestro.coverage import CoverageAdmission,canonical
from xverse.maestro.collection_plan import decode_collection
from xverse.maestro.runtime_verification import runtime_admission_digest,verify_runtime_closed

OUT=Path(sys.argv[1]).resolve(strict=True);TOOL=int(sys.argv[2]);EXIT=int(sys.argv[3])
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
run=read(OUT/'running.json');source=Path(run['frozen_source_root']);manifest=read(OUT/'frozen-inputs.json')
assert all(sha(source/n)==h for n,h in manifest.items())
identity=read(OUT/'installed-identity.json');assert len(identity)==46
assert all(sha(Path(r['file']))==r['sha256']==manifest['src/xverse/maestro/'+n] for n,r in identity.items())
package=OUT/'dist/xverse_xdl-0.4.0-py3-none-any.whl';installed=Path(sysconfig.get_path('purelib'));packaged=[]
with zipfile.ZipFile(package) as wheel:
 for n,h in manifest.items():
  if n.startswith('src/') and n.endswith(('.py','.c')):
   name=n.removeprefix('src/');assert hashlib.sha256(wheel.read(name)).hexdigest()==h==sha(installed/name);packaged.append(name)
assert len(packaged)==76
phases=[];controls=[];waits=[];roots=[];links=0;negative=[]
for phase in ('source','wheel'):
 receipt=read(OUT/(phase+'-receipt.json'));log=OUT/(phase+'.log');assert sha(log)==receipt['log_sha256']
 assert receipt['public_capture_returncode']==0
 summary=log.read_text().splitlines()[-1]
 counts={k:int(m.group(1)) if (m:=re.search(r'(\d+) '+k,summary)) else 0 for k in ('passed','failed','errors')}
 assert counts['passed']+counts['failed']==2
 assert (receipt['returncode']==0)==(counts['failed']==counts['errors']==0)
 phases.append(dict(phase=phase,returncode=receipt['returncode'],**counts))
 harness=OUT/(phase+'-harness');private=Path(receipt['original_private_basetemp'])
 for p in harness.glob('run-broker-waits-*.json'):
  r=read(p);assert all(r[k] for k in ('bootstrap_reaped','registered_helpers_reaped','storage_reaped','original_C1_released'))
  waits.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p)))
 for p in harness.glob('maestro-component-*.json'):
  r=read(p);assert r['root_removed'] and r['workers_reaped'] and not (Path(r['parent_path'])/r['root_name']).exists()
  roots.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p)))
 for r in read(OUT/(phase+'-public-evidence-index.json')):
  assert not r['reader_gaps'] and sha(OUT/r['snapshot'])==r['sha256'];links+=r['source_links']
 for mode in ('successor-live','successor-dead'):
  path=harness/('controller-inventory-'+mode+'.json');r=read(path)
  assert r['source_sha256']==manifest['tests/thesis_lite/maestro/test_terminal_controller_inventory.py']
  assert r['mode']==mode and r['execution_succeeded'] and r['no_writer_rpc_replay'] and r['original_bounds_preserved']
  assert not any(r[k] for k in ('actual_generation2_issued','productive_controller_recovery','full_TR06_complete','full_M1_complete','scientific_result'))
  assert len(r['transitions'])==1;transition=r['transitions'][0];closed=r['closure'];facts=r['receipt']
  assert transition['old_session']!=transition['new_session'] and transition['old_slot']!=transition['new_slot']
  assert transition['successor_productive_access_rejected']
  assert all(transition['old_retirement'][k] for k in ('original_child_dead','original_child_reaped','own_boundary_released'))
  assert not transition['old_retirement']['workload_waits_known']
  assert transition.get('successor_death_observed_without_reap',False) is (mode=='successor-dead')
  assert facts['diagnostic'] is None and facts['report']['eligible'] and facts['writer']['evidence_complete']
  assert facts['writer']['after_state']==facts['writer']['durable_writer_state']=='closed'
  assert facts['storageDrain']['worker_reaped']
  fixture=Path(r['original_fixture']);root=fixture/'argus'
  assert sha(root/'manifest.json')==r['manifest_sha256']==facts['writer']['manifest_sha256']
  reader=EvidenceStore.read_run(root);assert reader.manifest==r['manifest'] and reader.records()==r['argus_events']
  assert list(FileEvidenceJournal(fixture/'m3.jsonl').public_records())==r['public_m3']
  assert {record['details']['generation'] for record in r['public_m3']}=={1}
  pin_file=harness/('controller-inventory-inputs-'+mode+'.json');pin=read(pin_file)
  assert pin['source_sha256']==r['source_sha256'] and pin['original_fixture']==r['original_fixture']
  ad=CoverageAdmission(canonical(pin['original_admission']));body=ad.data(pin['admission_digest'])
  plan=decode_collection(pin['original_collection'],ad,pin['admission_digest'])
  assert len(body['units'])==2 and len(body['contexts'])==4
  assert {c['generation'] for c in body['contexts']}=={1,2}
  assert runtime_admission_digest(ad,plan,pin['generation_ns'])==pin['runtime_digest']
  args=dict(expected_admission_digest=pin['admission_digest'],expected_runtime_digest=pin['runtime_digest'],generation_ns=pin['generation_ns'])
  checked=verify_runtime_closed(ad,plan,root,**args);assert checked.complete
  report=checked.lifecycle.coverage.report();future=[row for row in report['rows'] if row['generation']==2]
  expected={row['id'] for row in body['templates'] if row['generation']==2}
  assert expected and {row['obligationId'] for row in future}==expected
  assert all(row['applicable'] is False and row['status']=='not-applicable' for row in future)
  assert closed['root_reaped'] and closed['inventory_complete'] and closed['unacknowledged_births']==0
  assert closed['normal_unit_records_complete'] and closed['authority_fenced'] and not closed['diagnostics']
  assert len(closed['helpers'])==4 and all(h['process_reaped'] for h in closed['helpers'])
  assert {h['role'] for h in closed['helpers']}=={3,4,5}
  assert {h['slot'] for h in closed['helpers'] if h['role']==5}=={transition['old_slot'],transition['new_slot']}
  assert all(x['empty'] and x['released'] for x in closed['boundaries'])
  assert all(x['issued'] is False or x['direct_child_reaped'] is True for x in closed['native_units'])
  assert closed['terminal_reports']==[facts] and closed['writers']==[]
  assert not closed['lifecycle_complete'] and not closed['ready_for_execution']
  for forged in r.get('offline_counterexamples',[]):
   copied=Path(forged['root']);assert copied!=root and copied.is_relative_to(fixture)
   before=sha(root/'manifest.json');generic=EvidenceStore.read_run(copied)
   assert generic.manifest['writerState']=='closed'
   assert not any('ARTIFACT' in d.code for d in generic.diagnostics)
   failed=verify_runtime_closed(ad,plan,copied,**args);assert not failed.complete
   assert sha(root/'manifest.json')==before==r['manifest_sha256']
   negative.append(dict(phase=phase,mode=mode,fault=forged['fault'],root=str(copied),
    original_pins_sha256=sha(pin_file),manifest_sha256=sha(copied/'manifest.json'),
    diagnostics=list(failed.diagnostics),normal_status=failed.lifecycle.coverage.report()['normalRecordStatus']))
  if OUT.name.endswith('20261019b'):assert len(r.get('offline_counterexamples',[]))==2
  controls.append(dict(phase=phase,mode=mode,path=str(path.relative_to(OUT)),sha256=sha(path),
   old_slot=transition['old_slot'],new_slot=transition['new_slot'],future_rows=len(future),
   original_pins_sha256=sha(pin_file),manifest_sha256=r['manifest_sha256']))
 files=[p for p in private.rglob('*') if p.is_file() and not p.is_symlink()
        and ('argus' in p.relative_to(private).parts or p.name=='m3.jsonl'
             or any(part.startswith('forged-') for part in p.relative_to(private).parts))]
 assert files and sum(p.stat().st_size for p in files)<32<<20
 with (OUT/(phase+'-actual-owned-public-bytes.tar.gz')).open('xb') as stream:
  with tarfile.open(fileobj=stream,mode='w:gz') as archive:
   for p in files:archive.add(p,arcname=str(p.relative_to(private)),recursive=False)
 with (OUT/(phase+'-actual-owned-public-index.json')).open('x') as f:
  json.dump({str(p.relative_to(private)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in files},f,indent=2);f.write('\n')
assert len(controls)==len(waits)==len(roots)==4
assert EXIT==(0 if all(r['returncode']==0 for r in phases) else 1)
result=dict(original_driver_session=TOOL,original_driver_terminal_exit=EXIT,phases=phases,
 affected_source_wheel_scope_passed=EXIT==0,controls=controls,offline_counterexamples=negative,
 original_broker_waits=waits,original_roots_absent=roots,actual_original_source_links=links,
 source_manifest_sha256=sha(OUT/'frozen-inputs.json'),installed_identity_sha256=sha(OUT/'installed-identity.json'),
 wheel_sha256=sha(package),installed_package_source_files_checked=76,auditor_sha256=sha(Path(__file__)),
 actual_generation2_issued=False,productive_controller_recovery=False,full_TR06_complete=False,
 full_platform_regression=False,full_M1_complete=False,stable_increment17=False,accepted=False,merged=False,
 canonical_note_edited=False,factory_run_created=False,scientific_result=False)
with (OUT/'verification.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(phases=phases,original_waits=len(waits),original_roots_absent=len(roots),
 actual_source_links=links,offline_counterexamples=len(negative),full_TR06_complete=False)))
