"""Original-worker collection over inert broker facts; grants no runtime authority."""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import os
import re
import time

from .artifacts import CollectionError
from .coverage import canonical, _json, _number
from .persistence import PersistenceError
from .public_blobs import MAX_PUBLIC_BLOB, decode_broker_data, sealed_public_blob, write_public_bytes
from .time import HostDeadline
from .collection_evidence import document, output_available, starts_fenced, validate_item


def _hash(data):
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def decode_context(data, coverage, expected_digest, plan, generation_ns, observed_until):
    """Runtime adapter preserving broker-data PersistenceError compatibility."""
    from .collection_evidence import BrokerDataError, decode_context as decode
    try:
        return decode(data, coverage, expected_digest, plan, generation_ns, observed_until)
    except BrokerDataError as error:
        raise PersistenceError(str(error)) from error






def _item(plan, index, row, entry):
    d = plan.declarations[index]
    return dict(unitId=d.unit_id, generation=d.generation, source=d.source, destination=d.destination,
                required=d.required, mediaType=d.media_type, status=row.status,
                bytes=len(row.content) if row.content is not None else None, sha256=row.sha256,
                diagnostic=row.diagnostic, entry=entry.public_entry() if entry is not None else None)






class WorkerCollection:
    """Created only in the original writer process from independently sealed admission."""

    def __init__(self, evidence, claims, data, deadline, check):
        self.evidence, self.plan, self.check = evidence, evidence.collection_plan, check
        self.context = decode_context(data, evidence.coverage, self.plan.coverage_digest,
                                      self.plan, evidence.collection_generation_ns, time.monotonic())
        self.checkpoint(deadline)
        broker = self.context['broker']
        if len(canonical(broker)) > evidence.broker_artifact.maximum_bytes:
            raise CollectionError('ML-COLLECTION-CONTEXT-SIZE')
        evidence._history(claims); evidence._mirrors(claims)
        if any((p := event['extensions']['xverse.maestro'])['action'] == 'run-terminal'
               or p['scope'] == 'run' and p['action'] == 'disposition' for event in evidence.events.values()):
            raise CollectionError('ML-COLLECTION-TERMINAL-ORDER')
        seen = set()
        for row in broker['generations']:
            key = row['unitId'], row['generation']; seen.add(key)
            issued = evidence.issued_handles.get(key)
            if issued is not None:
                handle, event = issued
                reference = 'handle-' + hashlib.sha256(canonical([evidence.permits._run_id, asdict(handle)])).hexdigest()
                if row['issued'] is not True or row['issuedEventId'] != event or row['handleRef'] != reference:
                    raise CollectionError('ML-COLLECTION-ISSUANCE')
            elif row['issued'] is True:
                raise CollectionError('ML-COLLECTION-ISSUANCE')
        if set(evidence.issued_handles) - seen:
            raise CollectionError('ML-COLLECTION-ISSUANCE')
        evidence.reserve_event(claims)
        self.started_at = time.monotonic()
        self.collector = evidence.collection_source.bind(evidence.root, self.plan.declarations,
            HostDeadline(deadline.session, self.context['collectionDeadlineNs'] / 1e9),
            byte_limits=self.plan.byte_limits, create_parents=True)
        try:
            self.items = []
            self.finished = self.finish_attempted = False
            self.checkpoint(deadline)
        except BaseException:
            self.collector.close()
            raise

    def checkpoint(self, deadline):
        self.check(deadline)
        if (time.monotonic_ns() >= self.context['collectionDeadlineNs']
            or deadline.monotonic_seconds > self.context['collectionDeadlineNs'] / 1e9
            or deadline.monotonic_seconds - time.monotonic() > self.plan.operation_seconds):
            raise CollectionError('ML-COLLECTION-TIMEOUT')

    def begin_ack(self):
        return dict(contextDigest=_hash(canonical(self.context)), startedAt=self.started_at,
                    collectionDeadlineNs=self.context['collectionDeadlineNs'], itemCount=len(self.plan.declarations))

    def item(self, index, deadline):
        self.checkpoint(deadline)
        if (type(index) is not int or not 0 <= index < len(self.plan.declarations)
            or index > len(self.items) or self.finish_attempted):
            raise CollectionError('ML-COLLECTION-ORDER')
        if index < len(self.items):
            return dict(index=index, item=self.items[index])
        d = self.plan.declarations[index]
        if output_available(self.context, d):
            row = self.collector.collect_next(index, deadline)
        else:
            row = self.collector.unavailable_next(index, deadline)
        entry = self.collector.index_item(self.evidence.writer, index, row, deadline)
        result = _item(self.plan, index, row, entry)
        if result['entry'] is not None:
            self.evidence.artifact_receipts[d.destination] = canonical(result['entry'])
        self.items.append(result)
        self.checkpoint(deadline)
        return dict(index=index, item=result)

    def finish(self, operation, claims, deadline):
        self.checkpoint(deadline)
        if self.finish_attempted or len(self.items) != len(self.plan.declarations):
            raise CollectionError('ML-COLLECTION-ORDER')
        self.finish_attempted = True
        self.collector.collect(deadline)  # Complete retained result; no reread of accepted items.
        self.evidence.reserve_event(claims)
        finished_at = time.monotonic()
        data = canonical(document(self.plan, self.context, self.items, self.started_at, finished_at))
        entry = write_public_bytes(self.evidence, self.plan.metadata_path, data,
            self.plan.metadata_maximum_bytes, lambda: self.checkpoint(deadline))
        complete = document(self.plan, self.context, self.items, self.started_at, finished_at)['collectionComplete']
        fields = _record_collect(self.evidence, claims, operation, _hash(data), complete,
                                 deadline, self.checkpoint)
        self.finished = True
        self.collector.close()
        return dict(entry=entry, contextDigest=_hash(canonical(self.context)), metadataDigest=_hash(data),
                    startedAt=self.started_at, finishedAt=finished_at,
                    collectionDeadlineNs=self.context['collectionDeadlineNs'], itemCount=len(self.items),
                    collectionComplete=complete, event=fields)


def _record_collect(evidence, claims, operation, metadata_digest, complete, deadline, check):
    from .evidence import retained_intent
    previous = max([0] + [e['ingestionOrdinal'] for e in evidence.events.values()]
                   + [retained_intent(c)['ingestionOrdinal'] for c in evidence._all_claims(claims)])
    fields = dict(eventId=operation + '-collect', producerId='maestro.collection17', eventKind='annotation',
        producerSequence=1, correlationId=evidence.permits._run_id, causationId=evidence.permits._run_id,
        clocks=dict(host=dict(domain='host:' + deadline.session, unit='s', value=time.monotonic()),
                    utc=dict(domain='utc:' + deadline.session, unit='s', value=datetime.now(timezone.utc).timestamp())),
        annotation=dict(text='Maestro original declared collection ' + metadata_digest),
        extensions={'xverse.maestro':dict(schemaVersion='2.0', lifecycleDigest='sha256:' + evidence.permits._prepared.lifecycle_digest,
            runId=evidence.permits._run_id, sessionId=deadline.session, scope='run', unitId=None, generation=0,
            operationId=operation, action='collect', outcome='succeeded' if complete else 'unknown', dependencies=[],
            sourceRefs=[dict(kind='admitted-lifecycle', id='original-coverage-admission', sequence=0,
                            sha256=evidence.coverage.digest)])})
    check(deadline)
    ordinal = evidence.writer.append_event(event_id=fields['eventId'], producer_id=fields['producerId'],
        event_kind=fields['eventKind'], producer_sequence=1, correlation_id=fields['correlationId'],
        causation_id=fields['causationId'], clocks=fields['clocks'], annotation=fields['annotation'], extensions=fields['extensions'])
    check(deadline); evidence.writer.flush_buffer(); check(deadline)
    if type(ordinal) is not int or ordinal != previous + 1:
        raise CollectionError('ML-COLLECTION-EVENT-ACK')
    fields['ingestionOrdinal'] = ordinal
    evidence.events[fields['eventId']] = fields
    return fields


@dataclass(frozen=True)
class CollectionReceipt:
    public_bytes: bytes = field(repr=False)
    lifecycle_complete: bool = field(default=False, init=False)

    def public_data(self):
        return _json(self.public_bytes, 65536)


def _validate_finish(client, context, items, started_at, operation, response, until):
    plan = client.collection
    if (type(response) is not dict or set(response) != {'entry', 'contextDigest', 'metadataDigest', 'startedAt',
        'finishedAt', 'collectionDeadlineNs', 'itemCount', 'collectionComplete', 'event'}
        or not _number(response['finishedAt']) or not started_at <= response['finishedAt'] <= until / 1e9):
        raise CollectionError('ML-COLLECTION-FINISH-ACK')
    data = canonical(document(plan, context, items, started_at, response['finishedAt']))
    if len(data) > plan.metadata_maximum_bytes:
        raise CollectionError('ML-COLLECTION-FINISH-ACK')
    event = response['event']
    if (type(event) is not dict or type(event.get('clocks')) is not dict
        or set(event['clocks']) != {'host', 'utc'}
        or any(type(event['clocks'][k]) is not dict or set(event['clocks'][k]) != {'domain', 'unit', 'value'}
               or event['clocks'][k]['domain'] != k + ':' + client.session or event['clocks'][k]['unit'] != 's'
               or not _number(event['clocks'][k]['value']) for k in ('host', 'utc'))
        or not response['finishedAt'] <= event['clocks']['host']['value'] <= until / 1e9
        or type(event.get('ingestionOrdinal')) is not int or event['ingestionOrdinal'] <= client._evidence_ordinal):
        raise CollectionError('ML-COLLECTION-EVENT-ACK')
    doc = _json(data)
    expected_event = dict(eventId=operation + '-collect', producerId='maestro.collection17', eventKind='annotation',
        producerSequence=1, correlationId=client.run_id, causationId=client.run_id, clocks=event['clocks'],
        annotation=dict(text='Maestro original declared collection ' + _hash(data)),
        extensions={'xverse.maestro':dict(schemaVersion='2.0', lifecycleDigest='sha256:' + client.prepared.lifecycle_digest,
            runId=client.run_id, sessionId=client.session, scope='run', unitId=None, generation=0, operationId=operation,
            action='collect', outcome='succeeded' if doc['collectionComplete'] else 'unknown', dependencies=[],
            sourceRefs=[dict(kind='admitted-lifecycle', id='original-coverage-admission', sequence=0,
                            sha256=client.coverage_digest)])}, ingestionOrdinal=event['ingestionOrdinal'])
    expected = dict(entry=dict(path=plan.metadata_path, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
        mediaType='application/json', schemaVersion='1.0', role='evidence'),
        contextDigest=_hash(canonical(context)), metadataDigest=_hash(data), startedAt=started_at,
        finishedAt=response['finishedAt'], collectionDeadlineNs=context['collectionDeadlineNs'],
        itemCount=len(items), collectionComplete=doc['collectionComplete'], event=expected_event)
    if canonical(response) != canonical(expected):
        raise CollectionError('ML-COLLECTION-FINISH-ACK')
    return CollectionReceipt(canonical(expected))


def collect_outputs(client, broker, deadline):
    from .run_broker import RunBroker
    client._holder()
    if (type(broker) is not RunBroker or broker.storage is not client or client.collection is None
        or type(deadline) is not HostDeadline or deadline.session != client.session):
        raise CollectionError('ML-COLLECTION-ORIGINAL')
    deadline.__post_init__(); broker._holder()
    identity = deadline.session, deadline.monotonic_seconds
    if not client._collection_lock.acquire(False):
        raise CollectionError('ML-COLLECTION-CONFLICT')
    try:
        if client._collection_outcome is not None:
            prior = client._collection_outcome
            if prior[0] is not broker or prior[1] != identity:
                raise CollectionError('ML-COLLECTION-ORIGINAL')
            return prior[2]
        if client._collection_attempted:
            raise CollectionError('ML-COLLECTION-UNCERTAIN')
        plan = client.collection; end = int(deadline.monotonic_seconds * 1e9)
        if (not 0 < end / 1e9 - time.monotonic() <= plan.collection_seconds
            or end > client.generation_ns - int((plan.terminal_seconds + plan.drain_seconds) * 1e9)
            or client._request_limit - client._sequence < plan.additional_requests + len(client._public_exports) + 1):
            raise CollectionError('ML-COLLECTION-BUDGET')
        def operation_end():
            client._live(allow_cancel=True)
            value = min(end, time.monotonic_ns() + int(plan.operation_seconds * 1e9))
            if value <= time.monotonic_ns():
                raise CollectionError('ML-COLLECTION-TIMEOUT')
            return HostDeadline(client.session, value / 1e9)
        client._collection_attempted = True
        try:
            cancelled = broker.cancel('collect-output-fence', deadline=operation_end())
            dead, reaped = cancelled.issuer_dead, cancelled.issuer_reaped
            if not cancelled.native_epoch_confirmed:
                observed = broker.connection.revoke(operation_end())
                dead, reaped = observed.issuer_dead, observed.issuer_reaped
            # Service the original root between bounded storage operations. An
            # individual operation is capped by the current short root lease;
            # blocked persistence cannot renew itself or extend the aggregate end.
            ordinary_end = operation_end
            def operation_end():
                requested = ordinary_end()
                service_end = HostDeadline(client.session, min(requested.monotonic_seconds,
                    time.monotonic() + 0.5, broker.session._lease / 1e9))
                lease = broker.service_terminal(service_end)
                return HostDeadline(client.session, min(requested.monotonic_seconds, lease / 1e9 - 0.05))
            projection = broker.public_projection(operation_end())
            context = dict(schemaVersion='1.0', broker=projection.public_data(),
                authority=dict(issuerDead=dead, issuerReaped=reaped), collectionDeadlineNs=end)
            data = canonical(context)
            if len(data) > MAX_PUBLIC_BLOB:
                raise CollectionError('ML-COLLECTION-CONTEXT-SIZE')
            check = lambda: operation_end()
            fd = sealed_public_blob(data, check)
            began = time.monotonic()
            try:
                _, _, response = client._rpc('public-blob', dict(purpose='collection-context', bytes=len(data),
                    sha256=hashlib.sha256(data).hexdigest()), operation_end(), public_blob_fd=fd)
            finally:
                os.close(fd)
            if (type(response) is not dict or set(response) != {'contextDigest', 'startedAt', 'collectionDeadlineNs', 'itemCount'}
                or not _number(response['startedAt']) or not began <= response['startedAt'] <= time.monotonic()
                or canonical({k: v for k, v in response.items() if k != 'startedAt'}) != canonical(dict(
                    contextDigest=_hash(data), collectionDeadlineNs=end, itemCount=len(plan.declarations)))):
                raise CollectionError('ML-COLLECTION-BEGIN-ACK')
            started_at = response['startedAt']; items = []
            for index in range(len(plan.declarations)):
                _, _, result = client._rpc('collect', dict(action='item', index=index), operation_end())
                row = validate_item(plan, index, result)
                if row['status'] == 'collected' and not output_available(context, plan.declarations[index]):
                    raise CollectionError('ML-COLLECTION-ITEM-ACK')
                items.append(row)
            operation, until, response = client._rpc('collect', dict(action='finish'), operation_end())
            receipt = _validate_finish(client, context, items, started_at, operation, response, until)
            client._evidence_ordinal = response['event']['ingestionOrdinal']
            client._collection_outcome = client._collection_outcome_pin = broker, identity, receipt, receipt.public_bytes
            return receipt
        except Exception:
            client._fail()
            raise
    finally:
        client._collection_lock.release()
