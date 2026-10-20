"""Bounded declared-file collection; no provider, cleanup or execution authority."""

from dataclasses import dataclass, field
import hashlib
import os
import re
import stat
import threading
import time
from functools import wraps

from .time import HostDeadline

_BIND_SOURCE = object()


class CollectionError(ValueError):
    pass


def _serialized(method):
    @wraps(method)
    def guarded(self, *args, **kwargs):
        if not self._lock.acquire(False):
            raise CollectionError('ML-COLLECTION-CONFLICT')
        try:
            return method(self, *args, **kwargs)
        finally:
            self._lock.release()
    return guarded


def _parts(path):
    if (type(path) is not str or re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]{0,255}', path) is None
        or any(p in ('', '.', '..') for p in path.split('/'))):
        raise CollectionError('ML-COLLECTION-PATH')
    return path.split('/')


def _identity(fd):
    s = os.fstat(fd)
    return s.st_dev, s.st_ino


def _file_state(fd):
    s = os.fstat(fd)
    return s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns


def _root(path):
    path = os.fspath(path)
    if not os.path.isabs(path) or '..' in path.split('/'):
        raise CollectionError('ML-COLLECTION-ROOT')
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in path.split('/'):
            if part in ('', '.'):
                continue
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


@dataclass(frozen=True)
class ArtifactDeclaration:
    unit_id: str
    generation: int
    source: str
    destination: str
    required: bool = True
    media_type: str = 'application/octet-stream'

    def __post_init__(self):
        if (type(self.unit_id) is not str or not 1 <= len(self.unit_id) <= 512
            or type(self.generation) is not int or not 1 <= self.generation <= 128
            or type(self.required) is not bool or type(self.media_type) is not str
            or not 3 <= len(self.media_type) <= 128
            or re.fullmatch(r'[A-Za-z0-9.+-]+/[A-Za-z0-9.+-]+', self.media_type) is None):
            raise CollectionError('ML-COLLECTION-DECLARATION')
        _parts(self.source)
        _parts(self.destination)


@dataclass(frozen=True)
class CollectedArtifact:
    declaration: ArtifactDeclaration
    status: str
    content: bytes | None = field(repr=False)
    sha256: str | None = None
    diagnostic: str | None = None


@dataclass(frozen=True)
class CollectionResult:
    artifacts: tuple[CollectedArtifact, ...]

    @property
    def collection_complete(self):
        return all(a.status == 'collected' or (a.status == 'missing' and not a.declaration.required)
                   for a in self.artifacts)


@dataclass(frozen=True)
class IndexedArtifact:
    path: str
    bytes: int
    sha256: str
    media_type: str
    schema_version: str
    role: str

    def public_entry(self):
        return dict(path=self.path, bytes=self.bytes, sha256=self.sha256,
                    mediaType=self.media_type, schemaVersion=self.schema_version, role=self.role)


class CollectionSource:
    """Original pre-workload directory pin; never recovered from a later path."""

    def __init__(self, path, expected_identity):
        if (type(expected_identity) is not tuple or len(expected_identity) != 2
            or any(type(v) is not int or v < 0 for v in expected_identity)):
            raise CollectionError('ML-COLLECTION-SOURCE-IDENTITY')
        self._lock = threading.Lock()
        self._fd = _root(path)
        self._original = self
        self._pin = os.fspath(path), self._fd, expected_identity, os.getpid()
        self._bound = None
        try:
            self._verify()
        except BaseException:
            os.close(self._fd)
            self._fd = None
            raise

    def __reduce_ex__(self, protocol):
        raise TypeError('original collection source cannot be copied')

    def _verify(self):
        path, fd, identity, pid = self._pin
        if self._original is not self or pid != os.getpid() or self._fd != fd:
            raise CollectionError('ML-COLLECTION-ORIGINAL')
        current = None
        try:
            current = _root(path)
            if _identity(fd) != identity or _identity(current) != identity:
                raise CollectionError('ML-COLLECTION-ROOT-CHANGED')
        except OSError as error:
            raise CollectionError('ML-COLLECTION-ROOT-CHANGED') from error
        finally:
            if current is not None:
                os.close(current)

    @_serialized
    def bind(self, evidence_root, declarations, deadline, *, byte_limits=None, create_parents=False):
        self._verify()
        if self._bound is not None:
            prior = self._bound
            prior._scope(deadline)
            if (os.fspath(evidence_root) != prior.evidence_root
                or deadline is not prior.deadline
                or type(declarations) not in (tuple, list)
                or tuple(declarations) != prior.declarations
                or type(create_parents) is not bool or create_parents != prior.create_parents
                or (tuple(byte_limits) if type(byte_limits) in (tuple, list)
                    else (1 << 20,) * len(prior.declarations) if byte_limits is None else byte_limits)
                   != prior.byte_limits):
                raise CollectionError('ML-COLLECTION-ORIGINAL')
            return prior
        self._bound = CollectionAdmission(self._pin[0], evidence_root, declarations, deadline,
                                         byte_limits=byte_limits, source_pin=self, _source_key=_BIND_SOURCE,
                                         create_parents=create_parents)
        return self._bound

    @_serialized
    def close(self):
        if self._original is not self or self._pin[3] != os.getpid():
            raise CollectionError('ML-COLLECTION-ORIGINAL')
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class CollectionAdmission:
    """Original descriptor pins and immutable declarations; explicitly close after use."""

    def __init__(self, source_root, evidence_root, declarations, deadline, *,
                 byte_limits=None, source_pin=None, _source_key=None, create_parents=False):
        if type(declarations) not in (tuple, list) or len(declarations) > 128:
            raise CollectionError('ML-COLLECTION-COUNT')
        declarations = tuple(declarations)
        if len(declarations) > 128 or any(type(d) is not ArtifactDeclaration for d in declarations):
            raise CollectionError('ML-COLLECTION-COUNT')
        units = {d.unit_id for d in declarations}
        if (len(units) > 16 or any(sum(d.unit_id == u for d in declarations) > 8 for u in units)
            or len({d.destination for d in declarations}) != len(declarations)
            or len({(d.unit_id, d.generation, d.source) for d in declarations}) != len(declarations)):
            raise CollectionError('ML-COLLECTION-COUNT')
        if type(deadline) is not HostDeadline:
            raise CollectionError('ML-COLLECTION-DEADLINE')
        deadline.__post_init__()
        if not 0 < deadline.monotonic_seconds - time.monotonic() <= 10:
            raise CollectionError('ML-COLLECTION-DEADLINE')
        if byte_limits is None:
            byte_limits = (1 << 20,) * len(declarations)
        if (type(byte_limits) not in (tuple, list) or len(byte_limits) != len(declarations)
            or any(type(v) is not int or not 0 <= v <= 1 << 20 for v in byte_limits)):
            raise CollectionError('ML-COLLECTION-BYTE-LIMITS')
        if source_pin is not None:
            if type(source_pin) is not CollectionSource or _source_key is not _BIND_SOURCE:
                raise CollectionError('ML-COLLECTION-ORIGINAL')
            source_pin._verify()
            if os.fspath(source_root) != source_pin._pin[0]:
                raise CollectionError('ML-COLLECTION-ORIGINAL')
        self.byte_limits = tuple(byte_limits)
        if type(create_parents) is not bool:
            raise CollectionError('ML-COLLECTION-DECLARATION')
        self.create_parents = create_parents
        self._source_pin = source_pin
        self.source_root, self.evidence_root = os.fspath(source_root), os.fspath(evidence_root)
        self.declarations, self.deadline = declarations, deadline
        self._lock = threading.Lock()
        self._source = self._target = None
        try:
            self._source = _root(self.source_root)
            if source_pin is not None:
                source_pin._verify()
                if _identity(self._source) != source_pin._pin[2]:
                    raise CollectionError('ML-COLLECTION-ROOT-CHANGED')
            self._target = _root(self.evidence_root)
            if _identity(self._source) == _identity(self._target):
                raise CollectionError('ML-COLLECTION-DISTINCT-ROOTS')
            self._pins = (self._source, _identity(self._source), self._target, _identity(self._target),
                          declarations, deadline, os.getpid())
            self._result = None
            self._indexes = {}
            self._rows = []
            self._row_pins = []
            self._remaining = 16 << 20
            self._item_indexes = {}
            self._scope_pin = (self.source_root, self.evidence_root,
                               deadline.session, deadline.monotonic_seconds,
                               self.byte_limits, source_pin,
                               tuple(tuple(vars(d).items()) for d in declarations), create_parents)
        except BaseException:
            self.close()
            raise

    def __reduce_ex__(self, protocol):
        raise TypeError('original collection admission cannot be copied')

    def _scope(self, deadline):
        if (type(deadline) is not HostDeadline or deadline.session != self.deadline.session
            or deadline.monotonic_seconds > self.deadline.monotonic_seconds
            or os.getpid() != self._pins[6] or self.declarations is not self._pins[4]
            or self.deadline is not self._pins[5] or self._source != self._pins[0]
            or self._target != self._pins[2]):
            raise CollectionError('ML-COLLECTION-ORIGINAL')
        deadline.__post_init__()
        if (self.source_root != self._scope_pin[0] or self.evidence_root != self._scope_pin[1]
            or (self.deadline.session, self.deadline.monotonic_seconds) != self._scope_pin[2:4]
            or self.byte_limits is not self._scope_pin[4] or self._source_pin is not self._scope_pin[5]
            or self.create_parents is not self._scope_pin[7]
            or tuple(tuple(vars(d).items()) for d in self.declarations) != self._scope_pin[6]):
            raise CollectionError('ML-COLLECTION-ORIGINAL')
        if (len(self._rows) != len(self._row_pins)
            or any(tuple(vars(row).items()) != pin for row, pin in zip(self._rows, self._row_pins))
            or self._result is not None and (len(self._result.artifacts) != len(self._rows)
                or any(a is not b for a, b in zip(self._result.artifacts, self._rows)))):
            raise CollectionError('ML-COLLECTION-ORIGINAL')

    def _check(self, deadline):
        self._scope(deadline)
        if time.monotonic() >= deadline.monotonic_seconds:
            raise CollectionError('ML-COLLECTION-TIMEOUT')
        if self._source_pin is not None:
            self._source_pin._verify()
        for path, fd, identity in [(self.source_root, self._source, self._pins[1]),
                                    (self.evidence_root, self._target, self._pins[3])]:
            try:
                current = _root(path)
            except OSError as error:
                raise CollectionError('ML-COLLECTION-ROOT-CHANGED') from error
            try:
                if _identity(current) != identity or _identity(fd) != identity:
                    raise CollectionError('ML-COLLECTION-ROOT-CHANGED')
            finally:
                os.close(current)

    def _parent_live(self, root, path, parent, deadline):
        self._check(deadline)
        try:
            current, _ = self._parent(root, path, deadline)
        except OSError as error:
            raise CollectionError('ML-COLLECTION-PARENT-CHANGED') from error
        try:
            if _identity(current) != _identity(parent):
                raise CollectionError('ML-COLLECTION-PARENT-CHANGED')
        finally:
            os.close(current)

    def _parent(self, root, path, deadline, *, create=False):
        parts = _parts(path)
        fd = os.dup(root)
        try:
            for part in parts[:-1]:
                self._check(deadline)
                if create:
                    if root != self._target:
                        raise CollectionError('ML-COLLECTION-DESTINATION')
                    try:
                        os.mkdir(part, 0o700, dir_fd=fd)
                    except FileExistsError:
                        pass
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
                os.close(fd)
                fd = child
            return fd, parts[-1]
        except BaseException:
            os.close(fd)
            raise

    def _read(self, declaration, deadline, remaining):
        parent, name = self._parent(self._source, declaration.source, deadline)
        fd = None
        try:
            self._check(deadline)
            try:
                fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=parent)
            except FileNotFoundError:
                self._parent_live(self._source, declaration.source, parent, deadline)
                raise
            before = _file_state(fd)
            if not stat.S_ISREG(before[2]):
                raise CollectionError('ML-COLLECTION-NONREGULAR')
            if before[3] > min(1 << 20, remaining):
                raise CollectionError('ML-COLLECTION-SIZE')
            chunks = []
            size = 0
            while True:
                self._check(deadline)
                chunk = os.read(fd, min(65536, before[3] - size + 1))
                if not chunk:
                    break
                size += len(chunk)
                if size > before[3]:
                    raise CollectionError('ML-COLLECTION-CHANGED')
                chunks.append(chunk)
            self._check(deadline)
            try:
                named = os.stat(name, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError as error:
                raise CollectionError('ML-COLLECTION-CHANGED') from error
            if (_file_state(fd) != before or size != before[3]
                or (named.st_dev, named.st_ino) != before[:2]):
                raise CollectionError('ML-COLLECTION-CHANGED')
            self._parent_live(self._source, declaration.source, parent, deadline)
            return b''.join(chunks)
        finally:
            if fd is not None:
                os.close(fd)
            os.close(parent)

    def _copy(self, declaration, data, deadline):
        try:
            parent, name = self._parent(self._target, declaration.destination, deadline, create=self.create_parents)
        except OSError as error:
            raise CollectionError('ML-COLLECTION-DESTINATION') from error
        fd = None
        identity = None
        try:
            self._check(deadline)
            fd = os.open(name, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                         0o600, dir_fd=parent)
            identity = _identity(fd)
            offset = 0
            while offset < len(data):
                self._check(deadline)
                written = os.write(fd, data[offset:offset+65536])
                if written <= 0:
                    raise CollectionError('ML-COLLECTION-WRITE')
                offset += written
            os.fsync(fd)
            self._check(deadline)
            before = _file_state(fd)
            os.lseek(fd, 0, os.SEEK_SET)
            actual = bytearray()
            while len(actual) <= len(data):
                self._check(deadline)
                chunk = os.read(fd, min(65536, len(data)-len(actual)+1))
                if not chunk:
                    break
                actual.extend(chunk)
            named = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if (bytes(actual) != data or (named.st_dev, named.st_ino) != identity
                or _file_state(fd) != before):
                raise CollectionError('ML-COLLECTION-COPY-CHANGED')
            self._parent_live(self._target, declaration.destination, parent, deadline)
            os.fsync(parent)
            self._check(deadline)
        except BaseException as error:
            if identity is not None:
                try:
                    named = os.stat(name, dir_fd=parent, follow_symlinks=False)
                    if (named.st_dev, named.st_ino) == identity:
                        os.unlink(name, dir_fd=parent)
                except OSError:
                    pass
            if isinstance(error, FileNotFoundError):
                raise CollectionError('ML-COLLECTION-DESTINATION') from error
            raise
        finally:
            if fd is not None:
                os.close(fd)
            os.close(parent)

    @_serialized
    def collect(self, deadline):
        self._scope(deadline)
        if self._result is not None:
            return self._result
        self._check(deadline)
        while len(self._rows) < len(self.declarations):
            self._next(deadline)
        if self._result is None:
            self._result = CollectionResult(tuple(self._rows))
        return self._result

    def _next(self, deadline):
        index = len(self._rows)
        declaration = self.declarations[index]
        try:
            self._check(deadline)
            data = self._read(declaration, deadline, min(self._remaining, self.byte_limits[index]))
            self._remaining -= len(data)
            self._copy(declaration, data, deadline)
            row = CollectedArtifact(declaration, 'collected', data, hashlib.sha256(data).hexdigest())
        except FileNotFoundError:
            try:
                self._check(deadline)
            except (CollectionError, OSError) as error:
                code = str(error) if isinstance(error, CollectionError) else 'ML-COLLECTION-IO'
                row = CollectedArtifact(declaration, 'error', None, diagnostic=code)
            else:
                row = CollectedArtifact(declaration, 'missing', None, diagnostic='ML-COLLECTION-MISSING')
        except (CollectionError, OSError) as error:
            code = str(error) if isinstance(error, CollectionError) else 'ML-COLLECTION-IO'
            row = CollectedArtifact(declaration, 'error', None, diagnostic=code)
        return self._retain_row(row)

    def _retain_row(self, row):
        self._rows.append(row)
        self._row_pins.append(tuple(vars(row).items()))
        if len(self._rows) == len(self.declarations):
            self._result = CollectionResult(tuple(self._rows))
        return row

    @_serialized
    def unavailable_next(self, index, deadline, diagnostic='ML-COLLECTION-OWNERSHIP'):
        """Retain a factual unavailable scope without opening any declared file."""
        self._scope(deadline)
        if (type(index) is not int or not 0 <= index < len(self.declarations)
            or index > len(self._rows) or diagnostic not in ('ML-COLLECTION-OWNERSHIP', 'ML-COLLECTION-NEVER-ISSUED')):
            raise CollectionError('ML-COLLECTION-ORDER')
        if index < len(self._rows):
            row = self._rows[index]
            if row.status != 'unavailable' or row.diagnostic != diagnostic:
                raise CollectionError('ML-COLLECTION-ORIGINAL')
            return row
        return self._retain_row(CollectedArtifact(self.declarations[index], 'unavailable', None,
                                                  diagnostic=diagnostic))

    @_serialized
    def collect_next(self, index, deadline):
        """One declared item; original aggregate end and debit persist across RPCs."""
        self._scope(deadline)
        if type(index) is not int or not 0 <= index < len(self.declarations) or index > len(self._rows):
            raise CollectionError('ML-COLLECTION-ORDER')
        if index < len(self._rows):
            return self._rows[index]
        return self._next(deadline)

    def _index_item(self, writer, index, row, deadline):
        from xverse.argus import EvidenceRun

        if (type(writer) is not EvidenceRun or type(index) is not int
            or not 0 <= index < len(self._rows) or row is not self._rows[index]):
            raise CollectionError('ML-COLLECTION-ORIGINAL')
        self._scope(deadline)
        key = id(writer), index
        prior = self._item_indexes.get(key)
        if prior is not None and prior[0] is writer:
            if prior[1] is None:
                raise CollectionError('ML-COLLECTION-INDEX-UNCERTAIN')
            if tuple(vars(prior[1]).items()) != prior[2]:
                raise CollectionError('ML-COLLECTION-INDEX-REPLACED')
            return prior[1]
        if row.status != 'collected':
            return None
        self._check(deadline)
        receipt = IndexedArtifact(row.declaration.destination, len(row.content), row.sha256,
                                  row.declaration.media_type, '1.0', 'evidence')
        self._item_indexes[key] = writer, None
        actual = writer.record_artifact(receipt.path, media_type=receipt.media_type,
                                        schema_version='1.0', role='evidence')
        if actual != receipt.public_entry() or type(actual.get('bytes')) is not int:
            raise CollectionError('ML-COLLECTION-INDEX-ACK')
        self._check(deadline)
        self._item_indexes[key] = writer, receipt, tuple(vars(receipt).items())
        return receipt

    @_serialized
    def index_item(self, writer, index, row, deadline):
        return self._index_item(writer, index, row, deadline)

    @_serialized
    def index(self, writer, result, deadline):
        from xverse.argus import EvidenceRun

        if type(writer) is not EvidenceRun or result is not self._result or result is None:
            raise CollectionError('ML-COLLECTION-ORIGINAL')
        self._scope(deadline)
        prior = self._indexes.get(id(writer))
        if prior is not None and prior[0] is writer:
            if tuple(tuple(vars(entry).items()) for entry in prior[1]) != prior[2]:
                raise CollectionError('ML-COLLECTION-INDEX-REPLACED')
            return prior[1]
        entries = []
        for index, row in enumerate(result.artifacts):
            receipt = self._index_item(writer, index, row, deadline)
            if receipt is not None:
                entries.append(receipt)
        entries = tuple(entries)
        self._indexes[id(writer)] = writer, entries, tuple(tuple(vars(entry).items()) for entry in entries)
        return entries

    @_serialized
    def close(self):
        for name in ('_source', '_target'):
            fd = getattr(self, name, None)
            if fd is not None:
                os.close(fd)
                setattr(self, name, None)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
