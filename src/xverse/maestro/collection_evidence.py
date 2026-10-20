"""Inert public broker/collection evidence codecs; no runtime authority or I/O."""
import hashlib
import re

from .artifacts import CollectionError
from .coverage import canonical, _json, _number

MAX_PUBLIC_BLOB = 1 << 20


class BrokerDataError(ValueError):
    """Pure broker-data rejection; runtime adapters retain PersistenceError."""


def _hash(data):
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def decode_broker_data(data, coverage, expected_digest, *, observed_until=None):
    ad = coverage.data(expected_digest)
    body = _json(data, MAX_PUBLIC_BLOB)
    fields = {'schemaVersion','runId','lifecycleDigest','hostSession','observedAt','admittedUnits','futureContexts',
              'generations','epochs','cancellationRequested','startsClosedLocally','authorityRevocationRequested',
              'nativeCancellationAcknowledged'}
    def reject():
        raise BrokerDataError('ML-EVIDENCE-BLOB-BROKER')
    if (type(body) is not dict or set(body) != fields or canonical(body) != data
        or body['schemaVersion'] != '1.0' or body['runId'] != ad['runId']
        or body['lifecycleDigest'] != ad['lifecycleDigest'] or body['hostSession'] != ad['hostSession']
        or not _number(body['observedAt']) or body['observedAt'] < ad['start']
        or observed_until is not None and body['observedAt']>observed_until
        or any(type(body[k]) is not bool for k in ('cancellationRequested','startsClosedLocally',
            'authorityRevocationRequested','nativeCancellationAcknowledged'))): reject()
    units = {u['unitId'] for u in ad['units']}
    contexts = {(c['unitId'],c['generation']) for c in ad['contexts']}
    if (type(body['admittedUnits']) is not list or len(body['admittedUnits']) != len(units)
        or type(body['futureContexts']) is not list or len(body['futureContexts'])>128
        or type(body['generations']) is not list or not len(units) <= len(body['generations']) <= len(contexts)
        or type(body['epochs']) is not list or not 0 < len(body['epochs']) <= 8192): reject()
    for c in body['futureContexts']:
        if (type(c) is not dict or set(c)!={'unitId','generation','executionId'}
            or type(c['unitId']) is not str or type(c['generation']) is not int or type(c['executionId']) is not str):reject()
    if canonical(sorted(body['futureContexts'],key=lambda c:(c['unitId'],c['generation'])))!=canonical([c for c in ad['contexts'] if c['generation']!=1]):reject()
    seen = set()
    for u in body['admittedUnits']:
        if (type(u) is not dict or set(u) != {'unitId','initialGeneration','maximumGeneration'}
            or type(u['unitId']) is not str or u['unitId'] not in units or u['unitId'] in seen or type(u['initialGeneration']) is not int
            or u['initialGeneration'] != 1 or type(u['maximumGeneration']) is not int
            or not max(g for uid,g in contexts if uid==u['unitId']) <= u['maximumGeneration'] <= 128): reject()
        seen.add(u['unitId'])
    row_fields = {'unitId','generation','stageAttempted','issued','intentEventId','issuedEventId','handleRef',
        'releaseObserved','releaseRequestedAt','releaseAcknowledgedAt','stopRequestedAt','stopAcknowledgedAt',
        'directChildReaped','nativeRetired','c1TerminationObserved','c1Empty','c1Released'}
    seen = set()
    for row in body['generations']:
        if (type(row) is not dict or set(row) != row_fields or type(row['generation']) is not int
            or type(row['unitId']) is not str
            or (row['unitId'],row['generation']) not in contexts or (row['unitId'],row['generation']) in seen
            or type(row['stageAttempted']) is not bool
            or any(type(row[k]) not in (bool,type(None)) for k in ('issued','releaseObserved','directChildReaped',
                'nativeRetired','c1TerminationObserved','c1Empty','c1Released'))
            or row['issued'] is True and row['stageAttempted'] is not True
            or row['issued'] is False and row['stageAttempted'] is not False): reject()
        seen.add((row['unitId'],row['generation']))
        for key in ('intentEventId','issuedEventId','handleRef'):
            value = row[key]
            if value is not None and (type(value) is not str or not 0 < len(value) <= 128): reject()
        for begin,end in [('releaseRequestedAt','releaseAcknowledgedAt'),('stopRequestedAt','stopAcknowledgedAt')]:
            a,b = row[begin],row[end]
            if (a is not None and (not _number(a) or not ad['start'] <= a <= body['observedAt'])
                or b is not None and (a is None or not _number(b) or not a <= b <= body['observedAt'])): reject()
        if row['releaseObserved'] is True and row['releaseAcknowledgedAt'] is None: reject()
        if (row['releaseObserved'] is True and row['issued'] is not True
            or row['issued'] is False and row['handleRef'] is not None
            or row['handleRef'] is not None and re.fullmatch('handle-[a-f0-9]{64}',row['handleRef']) is None
            or row['c1Released'] is True and row['c1Empty'] is not True):reject()
    if any((u,1) not in seen for u in units): reject()
    prior_epoch, prior_sequence = 0, -1
    for i,e in enumerate(body['epochs']):
        if (type(e) is not dict or set(e) != {'kind','epoch','sequence'}
            or e['kind'] not in ('ready','advanced','cancelled') or type(e['epoch']) is not int
            or not prior_epoch <= e['epoch'] <= (1<<64)-1 or type(e['sequence']) is not int
            or not prior_sequence < e['sequence'] <= (1<<64)-1
            or i==0 and (e['kind']!='ready' or e['epoch']!=0)):
            reject()
        prior_epoch,prior_sequence = e['epoch'],e['sequence']
    if body['nativeCancellationAcknowledged'] != any(e['kind']=='cancelled' for e in body['epochs']): reject()
    return body


def decode_context(data, coverage, expected_digest, plan, generation_ns, observed_until):
    body = _json(data, MAX_PUBLIC_BLOB)
    if (type(body) is not dict or set(body) != {'schemaVersion', 'broker', 'authority', 'collectionDeadlineNs'}
        or canonical(body) != data or body['schemaVersion'] != '1.0'
        or type(body['authority']) is not dict or set(body['authority']) != {'issuerDead', 'issuerReaped'}
        or any(type(body['authority'][k]) is not bool for k in ('issuerDead', 'issuerReaped'))
        or body['authority']['issuerReaped'] and not body['authority']['issuerDead']
        or type(body['collectionDeadlineNs']) is not int
        or not 0 < body['collectionDeadlineNs'] / 1e9 - observed_until <= plan.collection_seconds
        or body['collectionDeadlineNs'] > generation_ns - int((plan.terminal_seconds + plan.drain_seconds) * 1e9)):
        raise CollectionError('ML-COLLECTION-CONTEXT')
    broker = decode_broker_data(canonical(body['broker']), coverage, expected_digest, observed_until=observed_until)
    if (broker['startsClosedLocally'] is not True or broker['cancellationRequested'] is not True
        or any(body['authority'].values()) and broker['authorityRevocationRequested'] is not True):
        raise CollectionError('ML-COLLECTION-FENCE-CONTEXT')
    return body


def starts_fenced(context):
    return (context['broker']['nativeCancellationAcknowledged'] is True
            or context['authority']['issuerDead'] is True and context['authority']['issuerReaped'] is True)


def output_available(context, declaration):
    row = next((r for r in context['broker']['generations']
                if (r['unitId'], r['generation']) == (declaration.unit_id, declaration.generation)), None)
    return bool(starts_fenced(context) and row is not None and row['issued'] is True
                and row['directChildReaped'] is True and row['c1Empty'] is True and row['c1Released'] is True)


def validate_item(plan, index, body):
    if (type(body) is not dict or set(body) != {'index', 'item'}
        or type(body['index']) is not int or body['index'] != index or type(body['item']) is not dict):
        raise CollectionError('ML-COLLECTION-ITEM-ACK')
    row = body['item']; d = plan.declarations[index]
    expected = dict(unitId=d.unit_id, generation=d.generation, source=d.source, destination=d.destination,
                    required=d.required, mediaType=d.media_type)
    if (set(row) != set(expected) | {'status', 'bytes', 'sha256', 'diagnostic', 'entry'}
        or canonical({k: row[k] for k in expected}) != canonical(expected)
        or type(row['status']) is not str or row['status'] not in ('collected', 'missing', 'error', 'unavailable')):
        raise CollectionError('ML-COLLECTION-ITEM-ACK')
    if row['status'] == 'collected':
        if (type(row['bytes']) is not int or not 0 <= row['bytes'] <= plan.byte_limits[index]
            or type(row['sha256']) is not str or re.fullmatch('[a-f0-9]{64}', row['sha256']) is None
            or row['diagnostic'] is not None
            or canonical(row['entry']) != canonical(dict(path=d.destination, bytes=row['bytes'], sha256=row['sha256'],
                mediaType=d.media_type, schemaVersion='1.0', role='evidence'))):
            raise CollectionError('ML-COLLECTION-ITEM-ACK')
    elif (any(row[k] is not None for k in ('bytes', 'sha256', 'entry'))
          or type(row['diagnostic']) is not str or re.fullmatch('ML-COLLECTION-[A-Z-]{1,64}', row['diagnostic']) is None
          or row['status'] == 'missing' and row['diagnostic'] != 'ML-COLLECTION-MISSING'
          or row['status'] == 'unavailable' and row['diagnostic'] != 'ML-COLLECTION-OWNERSHIP'):
        raise CollectionError('ML-COLLECTION-ITEM-ACK')
    return row


def document(plan, context, items, started_at, finished_at):
    complete = starts_fenced(context) and all(r['status'] == 'collected'
        or r['status'] == 'missing' and not r['required'] for r in items)
    return dict(schemaVersion='1.0', runId=context['broker']['runId'], lifecycleDigest=context['broker']['lifecycleDigest'],
                hostSession=context['broker']['hostSession'],
                admissionDigest=plan.coverage_digest, collectionPlanDigest=_hash(plan.canonical_bytes),
                sourceRootIdentity=list(plan.source_identity), contextDigest=_hash(canonical(context)), context=context,
                collectionDeadlineNs=context['collectionDeadlineNs'], startedAt=started_at, finishedAt=finished_at,
                startsFenced=starts_fenced(context), collectionComplete=complete, items=items)
