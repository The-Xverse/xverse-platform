"""Immutable public-only transport and original worker publication; no authority."""
from dataclasses import dataclass
import fcntl
import hashlib
import os
import re
import stat
import time

from .coverage import CoverageAdmission, canonical, _json, _number, _path
from .persistence import PersistenceError, SEALS

MAX_PUBLIC_BLOB = 1 << 20


@dataclass(frozen=True)
class BrokerArtifact:
    relative_path: str
    maximum_bytes: int
    coverage_digest: str


def admit_broker_artifact(coverage, *, expected_digest):
    if type(coverage) is not CoverageAdmission:
        raise PersistenceError('ML-EVIDENCE-BLOB-ADMISSION')
    data = coverage.data(expected_digest)
    entry = next(a for a in data['artifacts'] if a['path'] == data['brokerPath'])
    return BrokerArtifact(data['brokerPath'], min(entry['maximumBytes'], MAX_PUBLIC_BLOB), expected_digest)


def decode_broker_artifact(value, coverage, expected_digest):
    if type(value) is not dict or set(value) != {'relative_path','maximum_bytes','coverage_digest'}:
        raise PersistenceError('ML-EVIDENCE-BLOB-ADMISSION')
    expected = admit_broker_artifact(coverage, expected_digest=expected_digest)
    if (type(value['maximum_bytes']) is not int or canonical(value) != canonical(vars(expected))):
        raise PersistenceError('ML-EVIDENCE-BLOB-ADMISSION')
    return expected


def sealed_public_blob(data, check):
    if type(data) is not bytes or not 0 < len(data) <= MAX_PUBLIC_BLOB:
        raise PersistenceError('ML-EVIDENCE-BLOB-SIZE')
    check()
    fd = os.memfd_create('maestro-public-evidence', os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
    try:
        offset = 0
        while offset < len(data):
            check()
            count = os.write(fd, data[offset:offset+65536])
            if count <= 0:
                raise PersistenceError('ML-EVIDENCE-BLOB-WRITE')
            offset += count
        fcntl.fcntl(fd, fcntl.F_ADD_SEALS, SEALS)
        check()
        return fd
    except BaseException:
        os.close(fd)
        raise


def read_public_blob(fd, body, until, maximum, check, *, purposes=('broker-projection',)):
    if (type(body) is not dict or set(body) != {'purpose','bytes','sha256'}
        or body['purpose'] not in purposes or type(body['bytes']) is not int
        or not 0 < body['bytes'] <= maximum <= MAX_PUBLIC_BLOB
        or type(body['sha256']) is not str or re.fullmatch('[a-f0-9]{64}', body['sha256']) is None):
        raise PersistenceError('ML-EVIDENCE-BLOB-REQUEST')
    def checkpoint():
        check()
        if not 0 < until - time.monotonic_ns() <= 5_000_000_000:
            raise PersistenceError('ML-EVIDENCE-BLOB-DEADLINE')
    checkpoint()
    info = os.fstat(fd)
    try:seals=fcntl.fcntl(fd,fcntl.F_GET_SEALS)
    except OSError as error:raise PersistenceError('ML-EVIDENCE-BLOB-DESCRIPTOR') from error
    if (not stat.S_ISREG(info.st_mode) or info.st_size != body['bytes']
        or seals & SEALS != SEALS):
        raise PersistenceError('ML-EVIDENCE-BLOB-DESCRIPTOR')
    data = bytearray()
    while len(data) < info.st_size:
        checkpoint()
        chunk = os.pread(fd, min(65536, info.st_size-len(data)), len(data))
        if not chunk:
            raise PersistenceError('ML-EVIDENCE-BLOB-SHORT')
        data.extend(chunk)
    checkpoint()
    after = os.fstat(fd)
    if ((after.st_dev,after.st_ino,after.st_size) != (info.st_dev,info.st_ino,info.st_size)
        or hashlib.sha256(data).hexdigest() != body['sha256']):
        raise PersistenceError('ML-EVIDENCE-BLOB-CHANGED')
    return bytes(data)


def decode_broker_data(data, coverage, expected_digest, *, observed_until=None):
    """Compatibility adapter retaining the original runtime exception identity."""
    from .collection_evidence import BrokerDataError, decode_broker_data as decode
    try:
        return decode(data, coverage, expected_digest, observed_until=observed_until)
    except BrokerDataError as error:
        raise PersistenceError(str(error)) from error


def write_public_bytes(evidence, path, data, maximum, check, *, schema_version='1.0'):
    from .artifacts import _root, _identity, _file_state
    if not _path(path) or type(data) is not bytes or not 0 < len(data) <= maximum:
        raise PersistenceError('ML-EVIDENCE-BLOB-SIZE')
    root, identity = evidence.export_root
    def rooted():
        check()
        current = _root(evidence.root)
        try:
            if _identity(root) != identity or _identity(current) != identity:
                raise PersistenceError('ML-EVIDENCE-BLOB-ROOT')
        finally: os.close(current)
    def parent(create=False):
        fd = os.dup(root)
        try:
            for part in path.split('/')[:-1]:
                rooted()
                if create:
                    try: os.mkdir(part, 0o700, dir_fd=fd)
                    except FileExistsError: pass
                child = os.open(part, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC, dir_fd=fd)
                os.close(fd);fd=child
            return fd
        except BaseException:
            os.close(fd);raise
    rooted();directory=parent(create=True);fd=None
    try:
        name=path.split('/')[-1]
        fd=os.open(name,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,0o600,dir_fd=directory)
        offset=0
        while offset<len(data):
            rooted();count=os.write(fd,data[offset:offset+65536])
            if count<=0:raise PersistenceError('ML-EVIDENCE-BLOB-WRITE')
            offset+=count
        os.fsync(fd);rooted();before=_file_state(fd)
        observed=bytearray()
        while len(observed)<len(data):
            rooted();chunk=os.pread(fd,min(65536,len(data)-len(observed)),len(observed))
            if not chunk:raise PersistenceError('ML-EVIDENCE-BLOB-SHORT')
            observed.extend(chunk)
        current=parent()
        try:
            named=os.stat(name,dir_fd=current,follow_symlinks=False)
            if (_identity(current)!=_identity(directory) or (named.st_dev,named.st_ino)!=before[:2]
                or _file_state(fd)!=before or bytes(observed)!=data):
                raise PersistenceError('ML-EVIDENCE-BLOB-CHANGED')
        finally:os.close(current)
        os.fsync(directory);rooted()
        expected=dict(path=path,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),
            mediaType='application/json',schemaVersion=schema_version,role='evidence')
        entry=evidence.writer.record_artifact(path,media_type='application/json',schema_version=schema_version,role='evidence')
        if canonical(entry)!=canonical(expected):raise PersistenceError('ML-EVIDENCE-BLOB-INDEX')
        rooted()
        if hasattr(evidence, 'artifact_receipts'):
            evidence.artifact_receipts[path] = canonical(entry)
        return entry
    finally:
        if fd is not None:os.close(fd)
        os.close(directory)


def publish_broker(evidence, data, deadline, check):
    check(deadline)
    if evidence.broker_artifact is None or evidence.broker_artifact_attempted:
        raise PersistenceError('ML-EVIDENCE-BLOB-REPLAY')
    evidence.broker_artifact_attempted=True
    declaration=evidence.broker_artifact
    body=decode_broker_data(data,evidence.coverage,declaration.coverage_digest,observed_until=time.monotonic())
    checkpoint=lambda:check(deadline)
    entry=write_public_bytes(evidence,declaration.relative_path,data,declaration.maximum_bytes,checkpoint)
    return dict(entry=entry,runId=body['runId'],lifecycleDigest=body['lifecycleDigest'],
        admissionDigest=declaration.coverage_digest,snapshotDigest='sha256:'+entry['sha256'],observedAt=body['observedAt'])


@dataclass(frozen=True)
class BrokerArtifactReceipt:
    public_bytes: bytes

    def public_data(self):return _json(self.public_bytes,65536)


def validate_broker_receipt(client, source, body):
    expected=dict(entry=dict(path=client._broker_artifact.relative_path,bytes=len(source),
        sha256=hashlib.sha256(source).hexdigest(),mediaType='application/json',schemaVersion='1.0',role='evidence'),
        runId=client.run_id,lifecycleDigest='sha256:'+client.prepared.lifecycle_digest,
        admissionDigest=client.coverage_digest,snapshotDigest='sha256:'+hashlib.sha256(source).hexdigest(),
        observedAt=_json(source,MAX_PUBLIC_BLOB)['observedAt'])
    if canonical(body)!=canonical(expected):raise PersistenceError('ML-EVIDENCE-BLOB-ACK')
    return BrokerArtifactReceipt(canonical(body))
