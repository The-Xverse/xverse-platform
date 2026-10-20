"""Original storage/root loss: actual bytes, independent pins and original waits."""
from pathlib import Path
import hashlib
import json
import os
import signal
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
run=read(OUT/'running.json');source=Path(run['frozen_source_root'])
manifest=read(OUT/'frozen-inputs.json');identity=read(OUT/'installed-identity.json')
assert all(sha(source/n)==h for n,h in manifest.items())
assert len(identity)==46 and all(sha(Path(r['file']))==r['sha256']==manifest['src/xverse/maestro/'+n] for n,r in identity.items())
package=OUT/'dist/xverse_xdl-0.4.0-py3-none-any.whl';installed=Path(sysconfig.get_path('purelib'))
packaged=[]
with zipfile.ZipFile(package) as wheel:
 for n,h in manifest.items():
  if n.startswith('src/') and n.endswith(('.py','.c')):
   name=n.removeprefix('src/');assert hashlib.sha256(wheel.read(name)).hexdigest()==h==sha(installed/name)
   packaged.append(name)
assert len(packaged)==76
phases=[];controls=[];waits=[];roots=[];links=0;raw_gaps=[];archives=[]
for phase in ('source','wheel'):
 receipt=read(OUT/(phase+'-receipt.json'));log=OUT/(phase+'.log')
 assert sha(log)==receipt['log_sha256'] and receipt['public_capture_returncode']==0
 summary=log.read_text().splitlines()[-1]
 counts={k:int(m.group(1)) if (m:=re.search(r'(\d+) '+k,summary)) else 0 for k in ('passed','failed','errors')}
 assert counts['passed']+counts['failed']==4
 assert (receipt['returncode']==0)==(counts['failed']==counts['errors']==0)
 phases.append(dict(phase=phase,returncode=receipt['returncode'],**counts))
 harness=OUT/(phase+'-harness');private=Path(receipt['original_private_basetemp'])
 for p in harness.glob('run-broker-waits-*.json'):
  r=read(p);assert all(r[k] for k in ('bootstrap_reaped','registered_helpers_reaped','storage_reaped','original_C1_released'))
  waits.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p)))
 for p in harness.glob('maestro-component-*.json'):
  r=read(p);assert r['root_removed'] and r['workers_reaped']
  assert not (Path(r['parent_path'])/r['root_name']).exists()
  roots.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p)))
 for row in read(OUT/(phase+'-public-evidence-index.json')):
  p=OUT/row['snapshot'];assert sha(p)==row['sha256']
  if row['reader_gaps']:raw_gaps.append(dict(phase=phase,snapshot=row['snapshot'],gaps=row['reader_gaps']))
 for fault in ('storage-stall','storage-death','source-root-loss','evidence-root-loss'):
  p=harness/('loss-outcome-'+fault+'.json');r=read(p)
  assert r['fault']==fault and r['source_sha256']==manifest['tests/thesis_lite/maestro/test_terminal_storage_root_loss.py']
  assert r['original_bounds_preserved'] and not r['full_TR06_complete'] and not r['full_M1_complete'] and not r['scientific_result']
  assert r['no_writer_rpc_replay'] and r['execution_succeeded'] and r['terminal_recorded']
  assert len(r['observations'])==1
  original=r['observations'][0];facts=r['receipt'];closed=r['closure'];fixture=Path(r['original_fixture'])
  assert original['original_helper_retained'] and original['collection']['collectionComplete']
  assert original['injection_completed_at']>=original['observed_at']
  assert original['injection_completed_at']<original['original_report_end'][1]
  assert facts['report'] is None and facts['writer'] is None and facts['diagnostic']
  assert facts['lastAcknowledgedWriterState']=='open' and facts['storageDrain']['worker_reaped']
  assert facts['storageDrain']['returncode'] is not None
  if fault=='storage-stall':
   assert original['nonconsuming_signal_observation']=={'code':os.CLD_STOPPED,'status':int(signal.SIGSTOP)}
  elif fault=='storage-death':
   assert original['nonconsuming_signal_observation']=={'code':os.CLD_KILLED,'status':int(signal.SIGKILL)}
  else:assert original['nonconsuming_signal_observation'] is None
  root=Path(r['actual_evidence_root']);named=Path(r['original_evidence_root'])
  st=root.stat();assert [st.st_dev,st.st_ino]==original['before_evidence_identity']
  assert root==Path(original['retained_evidence_path'])
  assert r['original_evidence_path_missing'] is (fault=='evidence-root-loss')
  assert r['original_source_path_missing'] is (fault=='source-root-loss')
  if fault=='evidence-root-loss':assert not named.exists() and root!=named
  else:assert named==root and named.is_dir()
  if fault=='source-root-loss':
   retained=Path(original['retained_source_path']);st=retained.stat()
   assert [st.st_dev,st.st_ino]==original['before_source_identity'] and not (fixture/'work').exists()
  raw_manifest=root/'manifest.json';events=EvidenceStore.read_run(root).records()
  assert sha(raw_manifest)==original['before_manifest_sha256']
  assert sha(root/'events.jsonl')==original['before_events_sha256']
  assert sha(fixture/'m3.jsonl')==original['before_m3_sha256']
  assert EvidenceStore.read_run(root).manifest['writerState']=='open'
  m3=list(FileEvidenceJournal(fixture/'m3.jsonl').public_records())
  assert m3==r['public_m3'] and events==r['argus_events']
  by_sequence={row['sequence']:row for row in m3};mirrored=set();source_links=0
  for event in events:
   for ref in event.get('extensions',{}).get('xverse.maestro',{}).get('sourceRefs',[]):
    if ref.get('kind')=='m3-record':
     assert ref['sha256']=='sha256:'+hashlib.sha256(canonical_bytes(by_sequence[ref['sequence']])).hexdigest()
     mirrored.add(ref['sequence']);source_links+=1
  assert set(by_sequence)==mirrored
  links+=source_links
  pin_file=harness/('loss-original-inputs-'+fault+'.json');pin=read(pin_file)
  assert pin['source_sha256']==r['source_sha256'] and pin['original_fixture']==r['original_fixture']
  ad=CoverageAdmission(canonical(pin['original_admission']));ad.data(pin['admission_digest'])
  plan=decode_collection(pin['original_collection'],ad,pin['admission_digest'])
  assert runtime_admission_digest(ad,plan,pin['generation_ns'])==pin['runtime_digest']
  check=verify_runtime_closed(ad,plan,root,expected_admission_digest=pin['admission_digest'],
       expected_runtime_digest=pin['runtime_digest'],generation_ns=pin['generation_ns'])
  assert check.lifecycle.writer_state=='open' and not check.complete
  assert not check.collection_verified and not check.collection_complete
  assert check.lifecycle.manifest_sha256==sha(raw_manifest)
  assert closed['root_reaped'] and closed['inventory_complete'] and closed['unacknowledged_births']==0
  assert closed['normal_unit_records_complete'] and closed['authority_fenced']
  assert {h['role'] for h in closed['helpers']}=={3,4,5} and all(h['process_reaped'] for h in closed['helpers'])
  assert all(x['empty'] and x['released'] for x in closed['boundaries'])
  assert all(x['issued'] is False or x['direct_child_reaped'] is True for x in closed['native_units'])
  assert closed['terminal_reports']==[facts] and closed['writers']==[]
  assert 'ML-CLOSURE-REPORT-INCOMPLETE' in closed['diagnostics']
  assert not closed['lifecycle_complete'] and not closed['ready_for_execution']
  controls.append(dict(phase=phase,fault=fault,outcome=str(p.relative_to(OUT)),outcome_sha256=sha(p),
   original_pins=str(pin_file.relative_to(OUT)),original_pins_sha256=sha(pin_file),
   original_fixed_report_end=original['original_report_end'],diagnostic=facts['diagnostic'],
   storage_returncode=facts['storageDrain']['returncode'],source_links=source_links,
   actual_evidence_root=str(root),original_evidence_path_missing=not named.exists(),
   original_manifest_sha256=sha(raw_manifest),actual_original_source_bytes_retained=True))
 files=[]
 for p in private.rglob('*'):
  if not p.is_file() or p.is_symlink():continue
  rel=p.relative_to(private)
  if any(part in ('argus','evidence-retained-after-loss','source-retained-after-loss') for part in rel.parts) or p.name=='m3.jsonl':
   assert p.stat().st_size<=16<<20;files.append(p)
 assert files and sum(p.stat().st_size for p in files)<32<<20
 target=OUT/(phase+'-actual-owned-public-bytes.tar.gz')
 with target.open('xb') as stream:
  with tarfile.open(fileobj=stream,mode='w:gz') as tar:
   for p in files:tar.add(p,arcname=str(p.relative_to(private)),recursive=False)
 index={str(p.relative_to(private)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in files}
 with (OUT/(phase+'-actual-owned-public-index.json')).open('x') as f:json.dump(index,f,indent=2);f.write('\n')
 archives.append(dict(phase=phase,sha256=sha(target),files=len(files)))
assert EXIT==(0 if all(r['returncode']==0 for r in phases) else 1)
assert len(controls)==len(waits)==len(roots)==8
result=dict(original_driver_session=TOOL,original_driver_terminal_exit=EXIT,phases=phases,
 affected_source_wheel_scope_passed=EXIT==0,controls=controls,original_broker_waits=waits,original_roots_absent=roots,
 actual_original_source_links=links,original_named_path_capture_gaps=raw_gaps,
 retained_original_roots_audited_separately=True,retained_actual_public_outputs=archives,
 source_manifest_sha256=sha(OUT/'frozen-inputs.json'),installed_identity_sha256=sha(OUT/'installed-identity.json'),
 wheel_sha256=sha(package),installed_package_source_files_checked=len(packaged),auditor_sha256=sha(Path(__file__)),
 full_TR06_complete=False,all_nine_full_runtime_cases_complete=False,full_platform_regression=False,
 full_M1_complete=False,stable_increment17=False,accepted=False,merged=False,canonical_note_edited=False,
 factory_run_created=False,scientific_result=False)
with (OUT/'verification.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(phases=phases,original_waits=len(waits),original_roots_absent=len(roots),
 actual_source_links=links,named_path_gap_snapshots=len(raw_gaps),full_TR06_complete=False)))
