"""Actual frozen native issuance, separately from start outcome and readiness."""
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import hashlib
import math
import re
import time

from xverse.argus.schema import canonical_bytes
from xverse_xdl.lifecycle import OwnedResourceHandle
from xverse_xdl.models import freeze
from .persistence import PersistenceError


def digest(value):
    return 'sha256:'+hashlib.sha256(canonical_bytes(value)).hexdigest()


@dataclass(frozen=True)
class IssuanceStatement:
    issuer: object
    claim: object
    handle: object
    native_ack: object
    observed_at: float
    deadline_ns: int

    def __reduce_ex__(self, protocol):
        raise TypeError('original active issuance statement cannot be copied')


@dataclass(frozen=True)
class IssuanceReceipt:
    unit_id: str
    generation: int
    event_id: str
    m3_sequence: int
    public_bytes: bytes

    def __reduce_ex__(self, protocol):
        raise TypeError('original issuance receipt cannot be copied')


def record_issued(evidence, body, claims, operation, deadline, check):
    check(deadline)
    if set(body) != {'unit','claim','generation','handle','observed_at','session'}:
        raise PersistenceError('ML-ISSUED-INPUT')
    unit = body['unit']
    claim = claims.get(unit)
    if claim is None or body['claim'] != claim.operation:
        raise PersistenceError('ML-ISSUED-CLAIM')
    permits = evidence.permits
    original = permits._issued.get(id(claim.receipt))
    if original is None or original[0] is not claim.receipt:
        raise PersistenceError('ML-ISSUED-CLAIM')
    saved = original[1]
    generation = saved.details['generation']
    if (type(body['generation']) is not int or body['generation'] != generation
        or body['session'] != deadline.session or check(deadline) > claim.deadline_ns):
        raise PersistenceError('ML-ISSUED-SCOPE')
    observed = body['observed_at']
    if (type(observed) not in (int,float) or not math.isfinite(observed)
        or not 0 <= time.monotonic()-observed <= 5):
        raise PersistenceError('ML-ISSUED-CLOCK')
    try:
        handle = OwnedResourceHandle(**body['handle'])
    except (TypeError,ValueError) as error:
        raise PersistenceError('ML-ISSUED-HANDLE') from error
    target = next(u for u in permits._prepared.units if u.unit_id == unit)
    start = next(a for a in target.plan.actions if a.phase=='start')
    if ((handle.execution_id,handle.action_id,handle.provider_id,handle.provider_kind)
        != (saved.execution_id,start.action_id,target.provider.provider_id,'process')
        or type(handle.opaque_id) is not str or re.fullmatch('[a-f0-9]{64}',handle.opaque_id) is None
        or type(handle.resource_identity) is not str or re.fullmatch('maestro-boundary:[a-f0-9]{64}',handle.resource_identity) is None
        or (unit,generation) in evidence.issued_handles):
        raise PersistenceError('ML-ISSUED-HANDLE')
    permits.revalidate_start_intent(claim.receipt, now=datetime.now(timezone.utc))
    evidence.reserve_event(claims)
    before = evidence._history(claims)
    evidence._mirrors(claims)
    now = datetime.now(timezone.utc)
    record = replace(saved,sequence=0,kind='observation',action_id=start.action_id,status='staged',
        timestamp=now.isoformat(),permit_nonce=None,handle_id=handle.opaque_id,
        handle_action_id=handle.action_id,handle_provider_id=handle.provider_id,
        handle_provider_kind=handle.provider_kind,handle_resource_identity=handle.resource_identity,
        details=freeze(dict(maestroRunId=permits._run_id,maestroUnitId=unit,generation=generation,
            lifecycleDigest=permits._prepared.lifecycle_digest,
            issuance=dict(hostSession=deadline.session,observedAt=observed,handleDigest=digest(asdict(handle))))))
    check(deadline)
    permits._journal.append(record)
    check(deadline)
    expected = replace(record,sequence=len(before)+1)
    actual = permits._journal.records
    if actual != (*before,expected):
        raise PersistenceError('ML-ISSUED-M3-ACK')
    evidence.history = actual
    public = next(r for r in permits._journal.public_records() if r['sequence']==expected.sequence)
    fields = dict(eventId=operation+'-issued',producerId='maestro.issuance17',eventKind='annotation',
        producerSequence=evidence.issuance_sequence+1,correlationId=permits._run_id,
        causationId=claim.event_id,
        clocks=dict(host=dict(domain='host:'+deadline.session,unit='s',value=observed),
                    utc=dict(domain='utc:'+deadline.session,unit='s',value=now.timestamp())),
        annotation=dict(text='Maestro issued succeeded'),extensions={'xverse.maestro':dict(
            schemaVersion='2.0',lifecycleDigest='sha256:'+permits._prepared.lifecycle_digest,
            runId=permits._run_id,sessionId=deadline.session,scope='unit',unitId=unit,
            generation=generation,operationId=operation,action='issued',outcome='succeeded',
            dependencies=[],handleRef='handle-'+digest([permits._run_id,asdict(handle)])[7:],
            sourceRefs=[dict(kind='m3-record',id='m3-record-'+str(expected.sequence),
                sequence=expected.sequence,sha256=digest(public))])})
    ordinal = evidence.writer.append_event(event_id=fields['eventId'],producer_id=fields['producerId'],
        event_kind=fields['eventKind'],producer_sequence=fields['producerSequence'],
        correlation_id=fields['correlationId'],causation_id=fields['causationId'],clocks=fields['clocks'],
        annotation=fields['annotation'],extensions=fields['extensions'])
    check(deadline)
    evidence.writer.flush_buffer()
    check(deadline)
    fields['ingestionOrdinal'] = ordinal
    evidence.events[fields['eventId']] = fields
    evidence.issuance_sequence += 1
    evidence.issued_handles[unit,generation] = handle,fields['eventId']
    evidence._history(claims)
    evidence._mirrors(claims)
    check(deadline)
    return dict(event=fields,record=public)


def validate_issued(client, statement, operation, body):
    if type(body) is not dict or set(body) != {'event','record'}:
        raise PersistenceError('ML-ISSUED-ACK')
    event, record = body['event'], body['record']
    issuer = statement.issuer
    target = issuer.owner._unit(issuer.unit_id)
    generation = issuer.recipe.descriptor.generation
    public_fields = {'actionId','catalogIdentity','details','executionId','handleId',
        'handleActionId','handleProviderId','handleProviderKind','handleResourceIdentity','kind',
        'permitId','permitNonce','planDigest','environmentIdentity','resourceRevisions','artifactDigests',
        'selection','permitIssuerLabel','permitOperationClasses','permitExclusions',
        'permitPublicSafetyClassification','sequence','status','timestamp'}
    if type(event) is not dict or type(record) is not dict or set(record) != public_fields:
        raise PersistenceError('ML-ISSUED-ACK')
    if (type(record.get('sequence')) is not int or record['sequence']<=client._evidence_m3
        or record.get('kind')!='observation' or record.get('status')!='staged'
        or record.get('executionId')!=statement.handle.execution_id
        or record.get('actionId')!=statement.handle.action_id or record.get('planDigest')!=target.plan.digest
        or record.get('handleId')!='withheld' or record.get('handleResourceIdentity')!='withheld'
        or record.get('permitNonce') is not None or record.get('handleProviderId')!=target.provider.provider_id
        or record.get('handleProviderKind')!='process'):
        raise PersistenceError('ML-ISSUED-M3-ACK')
    details = record.get('details',{})
    if (details.get('maestroRunId')!=client.run_id or details.get('maestroUnitId')!=issuer.unit_id
        or details.get('generation')!=generation or details.get('lifecycleDigest')!=client.prepared.lifecycle_digest):
        raise PersistenceError('ML-ISSUED-M3-ACK')
    expected = dict(eventId=operation+'-issued',producerId='maestro.issuance17',eventKind='annotation',
        producerSequence=client._issuance_sequence+1,correlationId=client.run_id,
        causationId=statement.claim.event_id,clocks=event.get('clocks'),
        annotation=dict(text='Maestro issued succeeded'),ingestionOrdinal=event.get('ingestionOrdinal'),
        extensions={'xverse.maestro':dict(schemaVersion='2.0',lifecycleDigest='sha256:'+client.prepared.lifecycle_digest,
            runId=client.run_id,sessionId=client.session,scope='unit',unitId=issuer.unit_id,generation=generation,
            operationId=operation,action='issued',outcome='succeeded',dependencies=[],
            handleRef='handle-'+digest([client.run_id,asdict(statement.handle)])[7:],
            sourceRefs=[dict(kind='m3-record',id='m3-record-'+str(record['sequence']),
                sequence=record['sequence'],sha256=digest(record))])})
    if canonical_bytes(event) != canonical_bytes(expected) or type(event.get('ingestionOrdinal')) is not int or event['ingestionOrdinal']<=client._evidence_ordinal:
        raise PersistenceError('ML-ISSUED-ACK')
    clocks = event['clocks']
    if type(clocks) is not dict or set(clocks)!={'host','utc'}:
        raise PersistenceError('ML-ISSUED-CLOCK')
    for name in ('host','utc'):
        clock = clocks[name]
        if (type(clock) is not dict or set(clock)!={'domain','unit','value'}
            or clock['domain']!=name+':'+client.session or clock['unit']!='s'
            or type(clock['value']) not in (int,float) or not math.isfinite(clock['value'])
            or name=='host' and clock['value']!=statement.observed_at):
            raise PersistenceError('ML-ISSUED-CLOCK')
    return IssuanceReceipt(issuer.unit_id,generation,event['eventId'],record['sequence'],canonical_bytes(body))
