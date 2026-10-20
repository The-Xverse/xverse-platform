"""Diagnostic-only successor wheel; original candidate/source wheel untouched."""
from pathlib import Path
import base64
import csv
import hashlib
import io
import json
import tempfile
import zipfile

OUT=Path(__file__).resolve().parent
private=Path(tempfile.mkdtemp(prefix='maestro-affa17-worker-profile-private-'))
source=OUT/'teardown-v2-dist/xverse_xdl-0.4.0-py3-none-any.whl'
target_dir=OUT/'worker-profile-diagnostic-dist';target_dir.mkdir()
target=target_dir/source.name
module='xverse/maestro/persistence_worker.py'
wrapper=r'''
# Diagnostic-only instrumentation; never installed as the engineering candidate.
def _diagnostic_profile_main():
    import cProfile
    import json
    from pathlib import Path
    profiler = cProfile.Profile()
    target = Path(PROFILE_DIRECTORY) / ("worker-" + str(os.getpid()) + ".json")
    def dump():
        profiler.disable()
        rows=[]
        for item in profiler.getstats():
            code=item.code
            if isinstance(code,str):
                name=code
                file="builtin"
                line=0
            else:
                name=code.co_name
                file=Path(code.co_filename).name
                line=code.co_firstlineno
            rows.append(dict(file=file,line=line,function=name,calls=item.callcount,
                             recursive_calls=item.reccallcount,total_seconds=item.totaltime,
                             own_seconds=item.inlinetime))
        rows.sort(key=lambda r:r['total_seconds'],reverse=True)
        target.write_text(json.dumps(rows,indent=2)+'\n')
    def terminated(signum, frame):
        try:
            dump()
        finally:
            os._exit(128+signum)
    signal.signal(signal.SIGTERM,terminated)
    profiler.enable()
    try:
        return main()
    finally:
        dump()
'''.replace('PROFILE_DIRECTORY',repr(str(private)))
with zipfile.ZipFile(source) as z:
    contents={n:z.read(n) for n in z.namelist()}
original=contents[module]
needle='if __name__ == "__main__":\n    os._exit(main())'
assert needle in original.decode()
contents[module]=original.decode().replace(needle,wrapper+'\nif __name__ == "__main__":\n    os._exit(_diagnostic_profile_main())').encode()
record=next(n for n in contents if n.endswith('.dist-info/RECORD'))
stream=io.StringIO(newline='');writer=csv.writer(stream,lineterminator='\n')
for name,data in contents.items():
    if name!=record:
        digest=base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b'=').decode()
        writer.writerow([name,'sha256='+digest,len(data)])
writer.writerow([record,'','']);contents[record]=stream.getvalue().encode()
with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for name,data in contents.items():z.writestr(name,data)
with zipfile.ZipFile(source) as old,zipfile.ZipFile(target) as new:
    changed=[n for n in old.namelist() if old.read(n)!=new.read(n)]
assert sorted(changed)==sorted([module,record])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result=dict(original_wheel_sha256=sha(source),diagnostic_wheel=str(target),diagnostic_wheel_sha256=sha(target),
    changed_members=changed,diagnostic_worker_sha256=hashlib.sha256(contents[module]).hexdigest(),
    original_worker_sha256=hashlib.sha256(original).hexdigest(),private_profile_directory=str(private),
    instrumentation_may_change_timing_and_termination=True,engineering_candidate_unchanged=True,
    operation_bounds_unchanged=True,acceptance_evidence=False)
(OUT/'worker-profile-diagnostic-identity.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='private_profile_directory'}))
