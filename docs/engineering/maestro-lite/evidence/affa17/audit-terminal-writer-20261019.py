"""Immutable component audit; synthetic fixtures are not native runtime evidence."""
from pathlib import Path
import hashlib
import json
import os
import platform
import re
import stat
import subprocess
import sys
import tarfile

BASE=Path(__file__).resolve().parent
CANDIDATE=BASE.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(path,value):
    with path.open('x') as stream:stream.write(json.dumps(value,indent=2)+'\n')

def audit(prefix,session,terminal_status):
    out=BASE/prefix
    frozen=json.loads((out/'frozen-inputs.json').read_bytes())
    running=json.loads((out/'running.json').read_bytes())
    source=Path(running['frozen_source_root']);consumer=Path(running['consumer'])
    assert all(sha(source/n)==h for n,h in frozen.items())
    identity=json.loads((out/'installed-identity.json').read_bytes())
    assert len(identity)==43
    assert all(sha(Path(v['file']))==v['sha256']==frozen['src/xverse/maestro/'+n] for n,v in identity.items())
    rows=[];snapshots=[]
    for phase in ('source','wheel'):
        receipt_file=out/(phase+'-receipt.json')
        if not receipt_file.exists():continue
        receipt=json.loads(receipt_file.read_bytes());log=out/(phase+'.log')
        assert sha(log)==receipt['log_sha256']
        assert receipt['input_manifest_sha256']==sha(out/'frozen-inputs.json')
        content=log.read_text()
        passed=re.search(r'(\d+) passed',content)
        failed=re.search(r'(\d+) failed',content)
        count=(int(passed.group(1)) if passed else 0)+(int(failed.group(1)) if failed else 0)
        assert count==72
        assert receipt['returncode']==(1 if failed else 0)
        private=Path(receipt['original_private_basetemp'])
        files=[];total=0;manifests=[]
        # Only original owned synthetic output bytes, with independent path/type/
        # byte bounds. Never follow an untrusted manifest's artifact declarations.
        for path in sorted(private.rglob('*')):
            if not path.is_file() or path.is_symlink():continue
            relative=path.relative_to(private)
            if 'argus' not in relative.parts and path.name!='synthetic-m3.jsonl':continue
            info=path.lstat()
            assert stat.S_ISREG(info.st_mode) and info.st_size<=16<<20
            total+=info.st_size;assert total<=64<<20
            files.append(path)
            if path.name=='manifest.json':manifests.append(dict(path=str(relative),sha256=sha(path)))
        assert files and len(files)<1024
        archive=out/(phase+'-synthetic-public-evidence.tar.gz')
        with archive.open('xb') as target:
            with tarfile.open(fileobj=target,mode='w:gz') as tar:
                for path in files:tar.add(path,arcname=str(path.relative_to(private)),recursive=False)
        index={str(p.relative_to(private)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in files}
        save(out/(phase+'-synthetic-public-index.json'),dict(original_basetemp=str(private),files=index,
            manifest_bytes=manifests,archive_sha256=sha(archive),synthetic_observations=True,native_runtime_proof=False))
        snapshots.append(dict(phase=phase,files=len(files),bytes=total,manifests=len(manifests),
            archive_sha256=sha(archive),index_sha256=sha(out/(phase+'-synthetic-public-index.json'))))
        rows.append(dict(phase=phase,passed=int(passed.group(1)) if passed else 0,
            failed=int(failed.group(1)) if failed else 0,returncode=receipt['returncode'],
            receipt_sha256=sha(receipt_file),log_sha256=sha(log)))
    environment=subprocess.check_output([running['verification_python'],'-I','-c',
        'import sys,platform,json,importlib.metadata as m; print(json.dumps(dict(python=sys.version,platform=platform.platform(),packages={p:m.version(p) for p in ("pytest","jsonschema","referencing","ruamel.yaml","build","hatchling")})))'],cwd=consumer,text=True)
    pass_all=len(rows)==2 and all(r['returncode']==0 for r in rows)
    assert terminal_status==(0 if pass_all else 1)
    result=dict(scope='synthetic actual Argus writer/reader and public closure failure stages; no worker orchestration',
        observed_original_tool_session=session,observed_tool_terminal_exit=terminal_status,
        phases=rows,affected_component_checks_passed=pass_all,retained_synthetic_outputs=snapshots,
        environment=json.loads(environment),source_manifest_sha256=sha(out/'frozen-inputs.json'),
        source_archive_sha256=sha(out/'tested-inputs.tar.gz'),
        wheel_sha256=sha(out/'dist/xverse_xdl-0.4.0-py3-none-any.whl'),
        installed_identity_sha256=sha(out/'installed-identity.json'),
        installed_maestro_modules=39,native_resources_matched_but_not_executed=4,
        driver_sha256=sha(BASE/('verify-'+prefix+'.py')),auditor_sha256=sha(Path(__file__)),
        native_helpers_started=False,original_report_rpc_integrated=False,automatic_dispatcher_closure=False,
        full_platform_regression=False,full_M1_complete=False,stable_increment17=False,accepted=False,merged=False)
    save(out/'verification.json',result)
    print(json.dumps(dict(namespace=prefix,checks=rows,synthetic_captures=snapshots,passed=pass_all)))

if __name__=='__main__':
    audit(sys.argv[1],int(sys.argv[2]),int(sys.argv[3]))
