"""Original public-input retention and confined export; no lifecycle assessment."""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import time

MAX_EXPORT_BYTES = 16 << 20
ANNOTATION_FIELDS = frozenset(('eventId', 'producerId', 'eventKind', 'producerSequence',
    'correlationId', 'causationId', 'clocks', 'annotation', 'extensions', 'ingestionOrdinal'))
TRUST_BOUNDARY = ('Original worker retains caller-supplied annotation fields and acknowledged ordinals; '
                  'no unreturned writer fields or open-manifest completeness are claimed.')


class PublicInputError(ValueError):
    pass


@dataclass(frozen=True)
class PublicExport:
    relative_path: str
    maximum_bytes: int

    def __post_init__(self):
        if (type(self.relative_path) is not str
            or re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}', self.relative_path) is None
            or self.relative_path in ('manifest.json', 'events.jsonl', 'lifecycle-coverage.json')
            or type(self.maximum_bytes) is not int or not 0 < self.maximum_bytes <= MAX_EXPORT_BYTES):
            raise PublicInputError('ML-EVIDENCE-EXPORT-DECLARATION')


def export_declarations(values):
    if type(values) not in (list, tuple) or len(values) > 8:
        raise PublicInputError('ML-EVIDENCE-EXPORT-COUNT')
    values = tuple(values)
    for value in values:
        if type(value) is not PublicExport:
            raise PublicInputError('ML-EVIDENCE-EXPORT-DECLARATION')
        value.__post_init__()
    if (len({v.relative_path for v in values}) != len(values)
        or sum(v.maximum_bytes for v in values) > MAX_EXPORT_BYTES):
        raise PublicInputError('ML-EVIDENCE-EXPORT-COUNT')
    return values


def decode_exports(config):
    values = config.get('public_exports', [])
    if type(values) is not list or len(values) > 8:
        raise PublicInputError('ML-EVIDENCE-EXPORT-COUNT')
    rows = []
    for value in values:
        if type(value) is not dict or set(value) != {'relative_path', 'maximum_bytes'}:
            raise PublicInputError('ML-EVIDENCE-EXPORT-DECLARATION')
        rows.append(PublicExport(**value))
    return export_declarations(rows)


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def _bounded(value, maximum, checkpoint):
    """Canonical JSON bytes of ``value``, refused above ``maximum`` bytes, with ``checkpoint`` between elements.

    ADR-ML3-EVIDENCE-0001 amendment S1a-4: a top-level object is emitted key by key (sorted, as ``sort_keys``) and a
    list value element by element, each through the same encoder (its C path), so the bytes are identical to a single
    ``iterencode`` of ``value`` while the deadline is checked once per element instead of once per pure-Python chunk.
    Any other shape uses the original chunked encoding."""
    encoder = json.JSONEncoder(sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
    chunks, size = [], 0

    def emit(text):
        nonlocal size
        encoded = text.encode()
        size += len(encoded)
        if size > maximum:
            raise PublicInputError('ML-EVIDENCE-EXPORT-SIZE')
        chunks.append(encoded)

    if type(value) is not dict or any(type(key) is not str for key in value):
        for part in encoder.iterencode(value):
            checkpoint()
            emit(part)
        return b''.join(chunks)
    checkpoint()
    emit('{')
    for index, key in enumerate(sorted(value)):
        emit((',' if index else '') + encoder.encode(key) + ':')
        item = value[key]
        if type(item) is list:
            emit('[')
            for position, element in enumerate(item):
                checkpoint()
                emit((',' if position else '') + encoder.encode(element))
            emit(']')
        else:
            checkpoint()
            emit(encoder.encode(item))
    emit('}')
    return b''.join(chunks)


def retained_intent(claim):
    data = claim.public_event_bytes
    if type(data) is not bytes or not 0 < len(data) <= 65536:
        raise PublicInputError('ML-EVIDENCE-RETAINED-INTENT')
    event = json.loads(data)
    if (type(event) is not dict or set(event) != ANNOTATION_FIELDS or _canonical(event) != data
        or event['eventId'] != claim.event_id or event['eventKind'] != 'annotation'
        or type(event['ingestionOrdinal']) is not int or event['ingestionOrdinal'] <= 0):
        raise PublicInputError('ML-EVIDENCE-RETAINED-INTENT')
    return event


def record_validation(evidence, admission, operation, deadline, check):
    """Publish actual prepared-input validation after original Init, before its ACK."""
    check(deadline)
    evidence.reserve_event({})
    run_id = evidence.permits._run_id
    if evidence.events or evidence.permits._journal.records or run_id in ('run-opened', 'run-closed', 'run-failed'):
        raise PublicInputError('ML-COVERAGE-VALIDATION-ORDER')
    fields = dict(eventId=run_id, producerId='maestro.validation17', eventKind='annotation',
        producerSequence=1, correlationId=None, causationId=None,
        clocks=dict(host=dict(domain='host:'+deadline.session, unit='s', value=time.monotonic()),
                    utc=dict(domain='utc:'+deadline.session, unit='s', value=datetime.now(timezone.utc).timestamp())),
        annotation=dict(text='Maestro original prepared inputs validated'),
        extensions={'xverse.maestro':dict(schemaVersion='2.0', lifecycleDigest='sha256:'+evidence.permits._prepared.lifecycle_digest,
            runId=run_id, sessionId=deadline.session, scope='run', unitId=None, generation=0,
            operationId=operation, action='validate', outcome='succeeded', dependencies=[],
            sourceRefs=[dict(kind='admitted-lifecycle', id='original-coverage-admission', sequence=0, sha256=admission.digest)])})
    ordinal = evidence.writer.append_event(event_id=fields['eventId'], producer_id=fields['producerId'],
        event_kind=fields['eventKind'], producer_sequence=fields['producerSequence'],
        correlation_id=None, causation_id=None, clocks=fields['clocks'],
        annotation=fields['annotation'], extensions=fields['extensions'])
    check(deadline)
    evidence.writer.flush_buffer()
    check(deadline)
    if type(ordinal) is not int or ordinal != 1:
        raise PublicInputError('ML-COVERAGE-VALIDATION-ORDINAL')
    fields['ingestionOrdinal'] = ordinal
    evidence.events[run_id] = fields
    return dict(admission_digest=admission.digest, event_id=run_id,
                ingestion_ordinal=ordinal, operation_id=operation)


def retained_snapshot(evidence, claims, maximum, checkpoint):
    """Worker-only original inputs; the returned data conveys no execution authority."""
    checkpoint()
    evidence._history(claims)
    evidence._mirrors(claims)
    events = []
    for claim in evidence._all_claims(claims):
        checkpoint()
        events.append(retained_intent(claim))
    events.extend(evidence.events.values())
    if len(events) > 8192:
        raise PublicInputError('ML-EVIDENCE-EXPORT-COUNT')
    seen_ids, seen_ordinals = set(), set()
    for event in events:
        checkpoint()
        if (type(event) is not dict or set(event) != ANNOTATION_FIELDS
            or event['eventKind'] != 'annotation' or type(event['ingestionOrdinal']) is not int
            or event['ingestionOrdinal'] <= 0 or event['eventId'] in seen_ids
            or event['ingestionOrdinal'] in seen_ordinals):
            raise PublicInputError('ML-EVIDENCE-RETAINED-ANNOTATION')
        seen_ids.add(event['eventId']); seen_ordinals.add(event['ingestionOrdinal'])
    events.sort(key=lambda event: event['ingestionOrdinal'])
    public = evidence.permits._journal.public_records()
    if len(public) > 8192:
        raise PublicInputError('ML-EVIDENCE-EXPORT-COUNT')
    body = dict(schemaVersion='1.0', runId=evidence.permits._run_id,
        lifecycleDigest='sha256:'+evidence.permits._prepared.lifecycle_digest,
        trustBoundary=TRUST_BOUNDARY, annotations=events, publicM3=list(public))
    return _bounded(body, maximum, checkpoint), len(events), len(public)


def pin_export_root(evidence):
    from .artifacts import _root, _identity
    fd = _root(evidence.root)
    return fd, _identity(fd)


def publish_export(evidence, claims, body, deadline, check):
    """One declared write/index operation in the original independently supervised worker."""
    from .artifacts import _root, _identity, _file_state

    check(deadline)
    if type(body) is not dict or set(body) != {'relative_path'}:
        raise PublicInputError('ML-EVIDENCE-EXPORT-REQUEST')
    path = body['relative_path']
    declaration = next((e for e in evidence.public_exports if e.relative_path == path), None)
    if declaration is None or path in evidence.export_attempted:
        raise PublicInputError('ML-EVIDENCE-EXPORT-REQUEST')
    evidence.export_attempted.add(path)
    checkpoint = lambda: check(deadline)
    data, annotations, records = retained_snapshot(evidence, claims, declaration.maximum_bytes, checkpoint)
    root_fd, original = evidence.export_root
    def rooted():
        checkpoint()
        current = _root(evidence.root)
        try:
            if _identity(root_fd) != original or _identity(current) != original:
                raise PublicInputError('ML-EVIDENCE-EXPORT-ROOT')
        finally:
            os.close(current)
    rooted()
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                 0o600, dir_fd=root_fd)
    try:
        offset = 0
        while offset < len(data):
            rooted()
            count = os.write(fd, data[offset:offset+65536])
            if count <= 0:
                raise PublicInputError('ML-EVIDENCE-EXPORT-WRITE')
            offset += count
        os.fsync(fd)
        rooted()
        before = _file_state(fd)
        os.lseek(fd, 0, os.SEEK_SET)
        observed = bytearray()
        while len(observed) <= len(data):
            rooted()
            chunk = os.read(fd, min(65536, len(data)-len(observed)+1))
            if not chunk:
                break
            observed.extend(chunk)
        named = os.stat(path, dir_fd=root_fd, follow_symlinks=False)
        if (bytes(observed) != data or _file_state(fd) != before
            or (named.st_dev, named.st_ino) != before[:2]):
            raise PublicInputError('ML-EVIDENCE-EXPORT-CHANGED')
        os.fsync(root_fd)
        rooted()
        expected = dict(path=path, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                        mediaType='application/json', schemaVersion='1.0', role='evidence')
        entry = evidence.writer.record_artifact(path, media_type='application/json', schema_version='1.0', role='evidence')
        if _canonical(entry) != _canonical(expected):
            raise PublicInputError('ML-EVIDENCE-EXPORT-INDEX')
        evidence.artifact_receipts[path] = _canonical(entry)
        rooted()
        return dict(entry=entry, runId=evidence.permits._run_id,
            lifecycleDigest='sha256:'+evidence.permits._prepared.lifecycle_digest,
            annotationCount=annotations, m3Count=records, snapshotDigest='sha256:'+entry['sha256'])
    finally:
        os.close(fd)


@dataclass(frozen=True)
class PublicExportReceipt:
    declaration: PublicExport
    public_bytes: bytes

    def public_entry(self):
        return json.loads(self.public_bytes)['entry']


def validate_export(client, declaration, body):
    if type(body) is not dict or set(body) != {'entry','runId','lifecycleDigest','annotationCount','m3Count','snapshotDigest'}:
        raise PublicInputError('ML-EVIDENCE-EXPORT-ACK')
    entry = body['entry']
    if (type(entry) is not dict or set(entry) != {'path','bytes','sha256','mediaType','schemaVersion','role'}
        or entry['path'] != declaration.relative_path or type(entry['bytes']) is not int
        or not 0 < entry['bytes'] <= declaration.maximum_bytes
        or type(entry['sha256']) is not str or re.fullmatch(r'[a-f0-9]{64}', entry['sha256']) is None
        or entry['mediaType'] != 'application/json' or entry['schemaVersion'] != '1.0' or entry['role'] != 'evidence'
        or body['runId'] != client.run_id or body['lifecycleDigest'] != 'sha256:'+client.prepared.lifecycle_digest
        or body['snapshotDigest'] != 'sha256:'+entry['sha256']
        or any(type(body[k]) is not int or not 0 <= body[k] <= 8192 for k in ['annotationCount','m3Count'])):
        raise PublicInputError('ML-EVIDENCE-EXPORT-ACK')
    return PublicExportReceipt(declaration, _canonical(body))


@dataclass(frozen=True)
class BrokerPublicProjection:
    public_bytes: bytes

    def public_data(self):
        return json.loads(self.public_bytes)


def broker_projection(broker, until):
    """Called only under the genuine original broker's normal mutation lock."""
    from dataclasses import asdict
    from .affa_protocol import AuthorityKind as K
    from .owner import OwnerError

    connection = broker.connection
    history = connection._epoch_history
    state = (broker.owner.latch.cancelled, connection._starts_closed, connection._revoked)
    def checkpoint():
        if time.monotonic_ns() >= until:
            raise OwnerError('ML-EVIDENCE-BROKER-TIMEOUT')
    checkpoint()
    units = [dict(unitId=u.unit_id, initialGeneration=broker._issuers[u.unit_id]._image.admission.descriptor.generation,
        maximumGeneration=broker._issuers[u.unit_id]._image.admission.maximum_generation) for u in broker.owner._prepared.units]
    contexts = [dict(unitId=c.binding.unit_id,generation=c.binding.generation,executionId=c.binding.execution_id)
                for c in broker.storage._future_contexts]
    rows = []
    for (unit,generation), issuer in broker._generation_issuers.items():
        checkpoint()
        fact = issuer._closure_fact()
        choices = [r for r in broker.storage._claims.values() if r.unit_id==unit and r.generation==generation]
        if len(choices)>1:
            raise OwnerError('ML-EVIDENCE-BROKER-CLAIM')
        claim = choices[0] if choices else None
        issued = broker.storage._issued_receipts.get((unit,generation))
        if issued is not None and (issuer._issuance_proof is None or issuer._issuance_proof[1] is not issued):
            raise OwnerError('ML-EVIDENCE-BROKER-ISSUANCE')
        terminal = broker.session.boundaries._entries[issuer._image.admission.descriptor.key].terminal
        released = issuer._release_ack
        bracket = issuer._release_bracket
        if released is not None and (released.kind is not K.RELEASED or released.handle != bytes.fromhex(issuer._handle.opaque_id)
                                    or released.generation != generation or released.slot != issuer.slot):
            raise OwnerError('ML-EVIDENCE-BROKER-RELEASE')
        rows.append(dict(unitId=unit,generation=generation,stageAttempted=issuer._attempted,
            issued=fact.issued,intentEventId=claim.event_id if claim else None,
            issuedEventId=issued.event_id if issued else None,
            handleRef=('handle-'+hashlib.sha256(_canonical([broker.storage.run_id,asdict(issuer._handle)])).hexdigest())
                if issuer._handle is not None else None,
            releaseObserved=True if released is not None else None if bracket is not None else False,
            releaseRequestedAt=bracket[0] if bracket is not None else None,
            releaseAcknowledgedAt=bracket[1] if bracket is not None else None,
            stopRequestedAt=issuer._stop_bracket[0] if issuer._stop_bracket is not None else None,
            stopAcknowledgedAt=issuer._stop_bracket[1] if issuer._stop_bracket is not None else None,
            directChildReaped=fact.direct_child_reaped,nativeRetired=fact.native_retired,
            c1TerminationObserved=terminal.termination_observed if terminal is not None else None,
            c1Empty=(terminal.residual_count == 0 if terminal.membership_complete else None)
                if terminal is not None else None,
            c1Released=terminal.boundary_released if terminal is not None else None))
    epochs = []
    for frame in history:
        if frame.kind not in (K.READY,K.ADVANCED,K.CANCELLED):
            raise OwnerError('ML-EVIDENCE-BROKER-EPOCH')
        epochs.append(dict(kind=frame.kind.name.lower(),epoch=frame.epoch,sequence=frame.sequence))
    body = dict(schemaVersion='1.0',runId=broker.storage.run_id,
        lifecycleDigest='sha256:'+broker.storage.prepared.lifecycle_digest,hostSession=broker.owner.session,
        observedAt=time.monotonic(),admittedUnits=units,futureContexts=contexts,generations=rows,
        epochs=epochs,cancellationRequested=state[0],startsClosedLocally=state[1],
        authorityRevocationRequested=state[2],
        nativeCancellationAcknowledged=any(frame.kind is K.CANCELLED for frame in history))
    data = _bounded(body,1<<20,checkpoint)
    broker._holder()
    if (history is not connection._epoch_history or state !=
        (broker.owner.latch.cancelled,connection._starts_closed,connection._revoked)):
        raise OwnerError('ML-EVIDENCE-BROKER-CONFLICT')
    checkpoint()
    return BrokerPublicProjection(data)
