"""Fixed code embedded in the owned role3 helper, not a production worker mode."""
ROLE3 = r'''import ctypes,fcntl,hashlib,json,os,time
from xverse.argus.writer import EvidenceRun
from xverse.maestro import persistence_worker
mode=MODE_LITERAL
fd=os.open(TRACE_LITERAL,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
writer=None
phase=None
def log(operation,result,**values):
    os.write(fd,(json.dumps(dict(operation=operation,result=result,phase=phase,
        observed_ns=time.monotonic_ns(),writer_state=writer.writer_state if writer is not None else None,
        **values))+'\n').encode())
image=os.environ.get('LD_PRELOAD')
assert image and image.startswith('/proc/self/fd/')
image_fd=int(image.rsplit('/',1)[1])
seals=fcntl.fcntl(image_fd,fcntl.F_GET_SEALS)
assert seals&15==15
image_hash=hashlib.sha256(os.pread(image_fd,IMAGE_SIZE_LITERAL,0)).hexdigest()
assert image_hash==IMAGE_HASH_LITERAL
library=ctypes.CDLL(None)
library.owned_writer_probe.restype=ctypes.c_uint
assert library.owned_writer_probe()==0x57534631
library.owned_writer_arm.argtypes=[]
library.owned_writer_arm.restype=None
log('loader','verified',image_sha256=image_hash,seals=seals)
finalize=EvidenceRun.finalize
flush=EvidenceRun.flush_buffer
abort=EvidenceRun.abort
def final(self,*args,**kwargs):
    global writer,phase
    writer=self;phase='finalize';log('finalize','entered')
    if mode=='close-after':library.owned_writer_arm()
    try:
        value=finalize(self,*args,**kwargs);log('finalize','returned');return value
    except BaseException as error:
        log('finalize','raised',error_type=type(error).__name__);raise
    finally:phase=None
def flushed(self,*args,**kwargs):
    global phase
    if phase=='finalize':
        log('finalize-public-flush','entered')
        value=flush(self,*args,**kwargs)
        log('finalize-public-flush','original-returned')
        if mode in ('seeded-flush-once','seeded-flush-persistent'):
            library.owned_writer_arm()
            try:
                self.append_event(event_id='owned-stream-fault-marker',producer_id='owned-stream-fixture',
                    event_kind='annotation',annotation={'text':'Owned native flush fixture annotation; no Maestro coverage credit.'})
            except OSError as error:
                assert error.errno==5
                log('fixture-annotation','seed-write-failed',error_type=type(error).__name__)
            else:raise AssertionError('native seed failure was not demonstrated')
        log('finalize-public-flush','wrapper-returned')
        return value
    if writer is not self:return flush(self,*args,**kwargs)
    previous=phase;phase='policy-flush';log('flush_buffer','entered')
    try:
        value=flush(self,*args,**kwargs);log('flush_buffer','returned');return value
    except BaseException as error:
        log('flush_buffer','raised',error_type=type(error).__name__);raise
    finally:phase=previous
def aborted(self,*args,**kwargs):
    global phase
    previous=phase;phase='abort';log('abort','entered')
    try:
        value=abort(self,*args,**kwargs);log('abort','returned');return value
    except BaseException as error:
        log('abort','raised',error_type=type(error).__name__);raise
    finally:phase=previous
EvidenceRun.finalize=final
EvidenceRun.flush_buffer=flushed
EvidenceRun.abort=aborted
status=persistence_worker.main()
os.close(fd)
os._exit(status)
'''

ROLE5 = r'''import ctypes,json,os,time
from xverse.maestro import controller_worker
absent=True
try:ctypes.CDLL(None).owned_writer_probe
except AttributeError:pass
else:absent=False
preload_absent=os.environ.get('LD_PRELOAD') is None
fd=os.open(TRACE_LITERAL,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
os.write(fd,(json.dumps(dict(preload_absent=preload_absent,symbol_absent=absent,
    observed_ns=time.monotonic_ns()))+'\n').encode())
os.close(fd)
assert absent and preload_absent
os._exit(controller_worker.main())
'''
