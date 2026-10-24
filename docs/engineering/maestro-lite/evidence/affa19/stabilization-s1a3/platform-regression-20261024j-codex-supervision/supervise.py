from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json,os,subprocess,time
ROOT=Path("/home/jefferson/xverse-platform-worktrees/stabilization-s1a3-20261023")
BASE=ROOT/"docs/engineering/maestro-lite/evidence/affa19"
CONTROL=Path(__file__).resolve().parent
OUT=BASE/"stabilization-s1a3/platform-regression-20261024j-codex-1"
HEAD="4bedba9efd21c750b84322e5fc265eb6adf86cc9"
DRIVER=BASE/"verify-platform-regression-20261021t.py"
# Existing driver limits: build 600 + environment 600 + collection 300 + tests 7200 seconds.
END=datetime(2026,10,24,23,0,tzinfo=ZoneInfo("Europe/Lisbon")).timestamp()
ADMIT_END=END-(600+600+300+7200+60)
def state(phase,**kw):
 data=dict(phase=phase,utc=datetime.now(ZoneInfo("UTC")).isoformat(),candidate=HEAD,output=str(OUT),**kw)
 tmp=CONTROL/"state.tmp";tmp.write_text(json.dumps(data,indent=2)+"\n");os.replace(tmp,CONTROL/"state.json")
 print(data,flush=True)
def busy():
 for p in Path("/proc").iterdir():
  if not p.name.isdigit():continue
  try:a=(p/"cmdline").read_bytes().split(b"\0")
  except OSError:continue
  if b"pytest" in a or any(x.endswith(b"/verify-platform-regression-20261021t.py") for x in a):return True
 return False
try:
 quiet=0
 state("waiting-for-five-quiet-samples",admission_end_unix=ADMIT_END)
 while time.time()<ADMIT_END:
  load=float(Path("/proc/loadavg").read_text().split()[0])
  quiet=quiet+1 if load<7 and not busy() else 0
  with (CONTROL/"quiet-samples.jsonl").open("a") as f:f.write(json.dumps(dict(unix=time.time(),load=load,consecutive=quiet))+"\n")
  if quiet>=5:break
  time.sleep(60)
 else:
  state("not-started-cutoff");raise SystemExit(3)
 head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
 dirty=subprocess.check_output(["git","status","--porcelain","--untracked-files=no"],cwd=ROOT,text=True).strip()
 if head!=HEAD or dirty:
  state("not-started-input-drift",observed_head=head,tracked_dirty=bool(dirty));raise SystemExit(4)
 with (CONTROL/"driver.log").open("x") as log:
  process=subprocess.Popen(["/usr/bin/python3",str(DRIVER),str(OUT)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
  state("running",driver_pid=process.pid,driver_sha256=hashlib.sha256(DRIVER.read_bytes()).hexdigest())
  while process.poll() is None:
   if OUT.is_dir():
    with (OUT/"load-samples.jsonl").open("a") as f:f.write(json.dumps(dict(utc=datetime.now(ZoneInfo("UTC")).isoformat(),loadavg=Path("/proc/loadavg").read_text().strip()))+"\n")
   time.sleep(30)
  code=process.returncode
 samples=[float(json.loads(l)["loadavg"].split()[0]) for l in (OUT/"load-samples.jsonl").read_text().splitlines()]
 receipt=OUT/"wheel-receipt.json"
 if not receipt.is_file():state("harness-failed",returncode=code);raise SystemExit(4)
 peak=max(samples)
 verdict="clean" if code==0 else ("failed-at-low-load" if peak<=10 else "nondecisive-high-load")
 # Retain all original tmpfs receipts and evidence. No automatic merge, retry, CAPA edit or acceptance.
 state("terminal",returncode=code,verdict=verdict,max_sampled_load=peak,receipt=str(receipt),accepted=False,merged=False)
except Exception as exc:
 state("supervisor-error",error=repr(exc));raise
