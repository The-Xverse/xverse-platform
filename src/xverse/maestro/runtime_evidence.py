"""Read actual externally pinned files/current host; never issue run authority."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import os
import stat
import time

from .child import _PidfdCapability
from .owner import _deadline
from .prbc import ProcessBoundaryOps, _cgroup2, _identity
from .runtime_admission import (
    AdmissionPins, FacilityAttestation, RunAuthorization, RUNTIME_CASES,
    RuntimeAdmissionError, validate_run_admission,
)
from .time import HostDeadline

MAX_EVIDENCE_FILE = 1024*1024


@dataclass(frozen=True)
class RuntimeEvidenceFiles:
    authorization: int = field(repr=False)
    facility: int = field(repr=False)
    runtime_cases: tuple[tuple[str,int], ...] = field(repr=False)


@dataclass(frozen=True)
class RuntimeEvidencePins:
    admission: AdmissionPins
    receipt_digests: tuple[tuple[str,str], ...]
    kernel_identity: str
    parent_identity: tuple
    ready_for_execution: bool = field(default=False,init=False)


def _file(fd,deadline):
    if type(fd) is not int or fd<0:
        raise RuntimeAdmissionError('ML-RUNTIME-EVIDENCE-FD')
    _deadline(deadline,deadline.session)
    original=os.dup(fd)
    try:
        before=os.fstat(original)
        if not stat.S_ISREG(before.st_mode) or not 0<before.st_size<=MAX_EVIDENCE_FILE:
            raise RuntimeAdmissionError('ML-RUNTIME-EVIDENCE-LIMIT')
        chunks=[];offset=0
        while offset<before.st_size:
            _deadline(deadline,deadline.session)
            data=os.pread(original,min(16384,before.st_size-offset),offset)
            if not data:raise RuntimeAdmissionError('ML-RUNTIME-EVIDENCE-CHANGED')
            chunks.append(data);offset+=len(data)
        after=os.fstat(original)
        fields=lambda info:(info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns)
        if fields(before)!=fields(after):raise RuntimeAdmissionError('ML-RUNTIME-EVIDENCE-CHANGED')
        _deadline(deadline,deadline.session)
        return b''.join(chunks)
    finally:os.close(original)


def verify_runtime_evidence(persistence,bootstrap,authorization,facility,files,boundaries,*,deadline,**pins):
    """At-use read-only checks. External owner must approve receipt semantics.

    Caller-supplied files and matching hashes are not authenticated approval and
    the returned value is never an execution capability. No fixture runs here.
    """
    if (type(files) is not RuntimeEvidenceFiles or type(boundaries) is not ProcessBoundaryOps
        or type(authorization) is not RunAuthorization or type(facility) is not FacilityAttestation
        or type(deadline) is not HostDeadline):
        raise RuntimeAdmissionError('ML-RUNTIME-EVIDENCE-INPUT')
    admission=validate_run_admission(persistence,bootstrap,authorization,facility,
        now=datetime.now(timezone.utc),host_now=HostDeadline(deadline.session,time.monotonic()),**pins)
    _deadline(deadline,authorization.cleanup_until.session)
    if (type(files.runtime_cases) is not tuple or len(files.runtime_cases)!=len(RUNTIME_CASES)
        or any(type(row) is not tuple or len(row)!=2 for row in files.runtime_cases)
        or tuple(row[0] for row in files.runtime_cases)!=RUNTIME_CASES):
        raise RuntimeAdmissionError('ML-RUNTIME-EVIDENCE-SET')
    try:
        if (_file(files.authorization,deadline)!=authorization.canonical_bytes()
            or _file(files.facility,deadline)!=facility.canonical_bytes()):
            raise RuntimeAdmissionError('ML-RUNTIME-EVIDENCE-CANONICAL')
        receipts=[]
        for (name,fd),(_,expected) in zip(files.runtime_cases,facility.runtime_case_receipts):
            digest='sha256:'+hashlib.sha256(_file(fd,deadline)).hexdigest()
            if digest!=expected:raise RuntimeAdmissionError('ML-RUNTIME-EVIDENCE-PIN')
            receipts.append((name,digest))
        boundaries._holder()
        if (boundaries._admission.run_id!=persistence.run_id
            or boundaries._admission.bootstrap_approval_ref!=bootstrap.admission.approval_ref
            or boundaries._root_fd!=bootstrap.admission.boundary_parent
            or boundaries._admission.teardown_deadline!=authorization.cleanup_until
            or boundaries._entries or boundaries._latch.cancelled
            or _identity(boundaries._root_fd)!=boundaries._root_identity
            or time.monotonic()>=authorization.cleanup_until.monotonic_seconds):
            raise RuntimeAdmissionError('ML-RUNTIME-EVIDENCE-ORIGINAL-C1')
        if facility.kernel_identity!=os.uname().release:
            raise RuntimeAdmissionError('ML-RUNTIME-EVIDENCE-KERNEL')
        _cgroup2(boundaries._root_fd)
        if any(entry.is_dir(follow_symlinks=False) for entry in os.scandir(boundaries._root_fd)):
            raise RuntimeAdmissionError('ML-RUNTIME-EVIDENCE-POPULATED')
        for name in ('cgroup.type','cgroup.events','cgroup.procs','cgroup.freeze','cgroup.kill'):
            mode=os.O_WRONLY if name in ('cgroup.kill','cgroup.freeze') else os.O_RDONLY
            fd=os.open(name,mode|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK,dir_fd=boundaries._root_fd)
            try:
                if not stat.S_ISREG(os.fstat(fd).st_mode):
                    raise RuntimeAdmissionError('ML-RUNTIME-EVIDENCE-CONTROL')
                if name=='cgroup.type' and os.read(fd,128).strip()!=b'domain':
                    raise RuntimeAdmissionError('ML-RUNTIME-EVIDENCE-CONTROL')
                if name=='cgroup.procs' and os.read(fd,128).strip():
                    raise RuntimeAdmissionError('ML-RUNTIME-EVIDENCE-POPULATED')
                if name=='cgroup.events' and not {b'populated 0',b'frozen 0'}<=set(os.read(fd,128).splitlines()):
                    raise RuntimeAdmissionError('ML-RUNTIME-EVIDENCE-POPULATED')
            finally:os.close(fd)
        # Self identity is an original capability probe, never PID discovery.
        fd=os.pidfd_open(os.getpid(),0)
        try:
            capability=_PidfdCapability(fd)
            capability.close()
        finally:os.close(fd)
        # A valid entry window can expire during receipt I/O or host checks.
        # The original deadline never extends authorization or the active lease.
        admission=validate_run_admission(persistence,bootstrap,authorization,facility,
            now=datetime.now(timezone.utc),host_now=HostDeadline(deadline.session,time.monotonic()),**pins)
        _deadline(deadline,authorization.cleanup_until.session)
        return RuntimeEvidencePins(admission,tuple(receipts),facility.kernel_identity,boundaries._root_identity)
    except RuntimeAdmissionError:raise
    except (ValueError,OSError,TypeError,AttributeError) as error:
        raise RuntimeAdmissionError('ML-RUNTIME-EVIDENCE-UNAVAILABLE') from error
