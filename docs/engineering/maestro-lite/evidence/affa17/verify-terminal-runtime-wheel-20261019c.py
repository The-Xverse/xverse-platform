"""First installed-wheel phase of exact b candidate; no source test rerun."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time

BASE=Path(__file__).resolve().parent
ORIGINAL=BASE/'terminal-runtime-20261019b'
OUT=BASE/'terminal-runtime-wheel-20261019c'
assert not OUT.exists(),'existing evidence namespace'
OUT.mkdir()
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,value):
    with (OUT/name).open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')
run=read(ORIGINAL/'running.json');source=Path(run['frozen_source_root']);consumer=Path(run['consumer'])
manifest=read(ORIGINAL/'frozen-inputs.json');identity=read(ORIGINAL/'installed-identity.json')
assert len(identity)==44 and all(sha(source/n)==h for n,h in manifest.items())
assert all(sha(Path(v['file']))==v['sha256']==manifest['src/xverse/maestro/'+n] for n,v in identity.items())
assert all(sha(Path(run['candidate'])/n)==h for n,h in manifest.items())
for name in ('frozen-inputs.json','installed-identity.json','running.json','collection-receipt.json'):
    shutil.copyfile(ORIGINAL/name,OUT/name)
save('original-phase-link.json',dict(original_namespace=str(ORIGINAL),original_source_receipt_sha256=sha(ORIGINAL/'source-receipt.json'),
    original_source_terminal_tool_session=53576,original_source_terminal_exit=1,
    original_source_tests_rerun=False,source_archive_sha256=sha(ORIGINAL/'tested-inputs.tar.gz'),
    wheel_sha256=sha(ORIGINAL/'dist/xverse_xdl-0.4.0-py3-none-any.whl')))
PYTHON=run['verification_python']
files=['test_coverage.py','test_runtime_verification.py','test_terminal_writer.py','test_terminal_runtime.py','test_lazy_dispatcher.py','test_fenced_teardown.py']
private=Path(tempfile.mkdtemp(prefix='maestro-terminal-runtime-wheel-20261019c-private-'))
env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONDONTWRITEBYTECODE='1',MAESTRO_BOUNDARY_RECEIPTS=str(OUT/'wheel-harness'))
env.pop('PYTHONPATH',None)
command=[PYTHON,'-I','-m','pytest',*[str(consumer/'tests/thesis_lite/maestro'/n) for n in files],'-q','--basetemp',str(private)]
began=time.monotonic()
with (OUT/'wheel.log').open('x') as stream:
    result=subprocess.run(command,cwd=consumer,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=300)
assert all(sha(source/n)==h for n,h in manifest.items())
assert all(sha(Path(v['file']))==v['sha256'] for v in identity.values())
shutil.copyfile(BASE/'capture-retained-teardown.py',OUT/'capture-public.py')
with (OUT/'wheel-public-capture.log').open('x') as stream:
    capture=subprocess.run([PYTHON,'-I',str(OUT/'capture-public.py'),'wheel',str(private)],cwd=consumer,env=env,
                           stdout=stream,stderr=subprocess.STDOUT,timeout=30)
receipt=dict(command=command,cwd=str(consumer),returncode=result.returncode,elapsed_seconds=time.monotonic()-began,
    original_private_basetemp=str(private),public_capture_returncode=capture.returncode,frozen_source_root=str(source),
    log_sha256=sha(OUT/'wheel.log'),input_manifest_sha256=sha(OUT/'frozen-inputs.json'))
save('wheel-receipt.json',receipt)
save('result-after-wheel.json',dict(receipts=[receipt],collected_per_phase=96,source_phase_executed_here=False,
    installed_wheel_phase_executed=True,component_checks_passed=result.returncode==capture.returncode==0,
    full_source_wheel_scope_passed=False,original_source_failure_preserved=True,
    source_manifest_sha256=sha(OUT/'frozen-inputs.json'),installed_identity_sha256=sha(OUT/'installed-identity.json'),
    wheel_sha256=sha(ORIGINAL/'dist/xverse_xdl-0.4.0-py3-none-any.whl'),installed_maestro_modules=40,native_resources=4,
    full_platform_regression=False,full_M1_complete=False,stable_increment17=False,accepted=False,merged=False))
print('wheel',result.returncode,'collected',96,flush=True)
raise SystemExit(result.returncode or capture.returncode)
