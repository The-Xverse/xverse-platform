"""Admission-derived lifecycle coverage; inert values, pure assessment, confined offline I/O."""
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import math
import re

MAX_ROWS = 8192
MAX_BYTES = 16 << 20
WRITER_KINDS = ['run-opened', 'run-closed', 'run-failed']
FIELDS = {'eventId','producerId','eventKind','producerSequence','correlationId','causationId',
          'clocks','annotation','extensions','ingestionOrdinal'}
M3_FIELDS = {'actionId','catalogIdentity','details','executionId','handleId','handleActionId',
    'handleProviderId','handleProviderKind','handleResourceIdentity','kind','permitId','permitNonce',
    'planDigest','environmentIdentity','resourceRevisions','artifactDigests','selection','permitIssuerLabel',
    'permitOperationClasses','permitExclusions','permitPublicSafetyClassification','sequence','status','timestamp'}
PAYLOAD_FIELDS = {'schemaVersion','lifecycleDigest','runId','sessionId','scope','unitId','generation',
    'operationId','action','outcome','sourceRefs','dependencies'}
PAYLOAD_OPTIONAL = {'stepId','handleRef','probeId','diagnosticCode','obligationId','cause','disposition'}
OUTCOMES = {'pending','succeeded','failed','cancelled','skipped','unknown','unresolved'}
DISPOSITIONS = dict(completed='succeeded',failed='failed',blocked='skipped',skipped='skipped',
                    cancelled='cancelled',unresolved='unresolved',**{'not-applicable':'skipped'})
TRUST = ('Original externally pinned admission and caller-retained public fields are trusted inputs; '
         'pre-closure is provisional. Offline checks actual closed-reader records and confined bytes. '
         'Coverage grants no execution or cleanup authority.')


class CoverageError(ValueError):
    pass


def canonical(value):
    try:
        return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
    except (ValueError,TypeError,RecursionError) as error:
        raise CoverageError('ML-COVERAGE-JSON') from error


def digest(value):
    return 'sha256:'+hashlib.sha256(canonical(value)).hexdigest()


def _identifier(value,maximum=128):
    return type(value) is str and 0<len(value)<=maximum and not any(ord(c)<32 for c in value)


def _number(value):
    try:return type(value) in (int,float) and math.isfinite(value)
    except OverflowError:return False


def _path(value):
    return (type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]{0,255}',value) is not None
            and all(p not in ('','.','..') for p in value.split('/')))


def _plain(value,depth=0):
    if depth>32:raise CoverageError('ML-COVERAGE-DEPTH')
    if type(value) is dict:
        if len(value)>MAX_ROWS or any(type(k) is not str for k in value):raise CoverageError('ML-COVERAGE-SHAPE')
        return {k:_plain(v,depth+1) for k,v in value.items()}
    if type(value) in (tuple,list):
        if len(value)>MAX_ROWS:raise CoverageError('ML-COVERAGE-COUNT')
        return [_plain(v,depth+1) for v in value]
    if value is None or type(value) in (str,bool,int):return value
    if type(value) is float and math.isfinite(value):return value
    raise CoverageError('ML-COVERAGE-SHAPE')


def _json(data,maximum=MAX_BYTES):
    if type(data) is not bytes or len(data)>maximum:raise CoverageError('ML-COVERAGE-BYTES')
    def pairs(items):
        result={}
        for k,v in items:
            if k in result:raise CoverageError('ML-COVERAGE-DUPLICATE')
            result[k]=v
        return result
    try:return _plain(json.loads(data,object_pairs_hook=pairs))
    except (ValueError,TypeError,RecursionError,UnicodeError) as error:raise CoverageError('ML-COVERAGE-JSON') from error


def _list(value,limit=MAX_ROWS):
    if type(value) not in (list,tuple) or len(value)>limit:raise CoverageError('ML-COVERAGE-COUNT')
    return _plain(value)


@dataclass(frozen=True)
class ArtifactExpectation:
    relative_path: str
    required: bool = True
    maximum_bytes: int = 1<<20
    unit_id: str | None = None
    generation: int = 0

    def __post_init__(self):
        if (not _path(self.relative_path) or type(self.required) is not bool or type(self.maximum_bytes) is not int
            or not 0<self.maximum_bytes<=MAX_BYTES or type(self.generation) is not int or self.generation<0
            or self.unit_id is not None and not _identifier(self.unit_id)):
            raise CoverageError('ML-COVERAGE-ARTIFACT-ADMISSION')


def _templates(body):
    rows=[]
    def add(identity,kind,unit=None,generation=0,**extra):
        if len(rows)>=MAX_ROWS:raise CoverageError('ML-COVERAGE-CAPACITY')
        rows.append(dict(id=identity,kind=kind,unit=unit,generation=generation,**extra))
    add('ob.input-integrity','normal-record',suffix='integrity')
    for unit in body['units']:
        uid=unit['unitId'];key=hashlib.sha256(uid.encode()).hexdigest()
        add('ob.'+key+'.unit-disposition','unit-disposition',uid,suffix='unit-disposition')
        for context in [c for c in body['contexts'] if c['unitId']==uid]:
            gen=context['generation'];base='ob.'+key+'.g'+str(gen)+'.'
            for suffix in ('intent','issued','outcome','ready','stop','cleanup','emergency'):
                add(base+suffix,'emergency-fact' if suffix=='emergency' else 'normal-record',uid,gen,suffix=suffix)
            ratio=(body['end']-body['start'])/unit['cadence']
            if not _number(ratio) or ratio>MAX_ROWS:raise CoverageError('ML-COVERAGE-CAPACITY')
            count=math.ceil(ratio)
            for slot in range(1,count+1):add(base+'health.'+str(slot),'normal-record',uid,gen,suffix='health',slot=slot)
    for step in body['steps']:
        add('ob.step.'+hashlib.sha256(step['stepId'].encode()).hexdigest(),'step-disposition',step['unitId'],suffix='step-disposition',step=step['stepId'])
    for artifact in body['artifacts']:
        if artifact['path']!=body['reportPath']:
            add('ob.artifact.'+hashlib.sha256(artifact['path'].encode()).hexdigest(),'artifact',artifact['unitId'],artifact['generation'],suffix='artifact',path=artifact['path'],required=artifact['required'])
    for name in ('run-validation','collect','run-terminal','run-disposition'):add('ob.'+name,'normal-record',suffix=name)
    if len(rows)>MAX_ROWS:raise CoverageError('ML-COVERAGE-CAPACITY')
    return rows


@dataclass(frozen=True)
class CoverageAdmission:
    public_bytes: bytes

    @property
    def digest(self):return 'sha256:'+hashlib.sha256(self.public_bytes).hexdigest()

    def data(self,expected_digest):
        if self.digest!=expected_digest:raise CoverageError('ML-COVERAGE-ADMISSION-DIGEST')
        body=_json(self.public_bytes,1<<20)
        required={'version','runId','lifecycleDigest','experimentDigest','hostSession','simulationDomain','horizonTicks','start','end','units','contexts','steps','artifacts',
                  'sourceDigests','reportPath','retainedPath','brokerPath','templates'}
        if type(body) is not dict or set(body)!=required or body['version']!=1 or type(body['version']) is not int:
            raise CoverageError('ML-COVERAGE-ADMISSION')
        try:_validate_admission(body)
        except (TypeError,KeyError,AttributeError,OverflowError) as error:raise CoverageError('ML-COVERAGE-ADMISSION') from error
        if canonical(body)!=self.public_bytes or body['templates']!=_templates(body):
            raise CoverageError('ML-COVERAGE-TEMPLATES')
        _report_capacity(body['templates'])
        return body


def admit_coverage(prepared,result,resources,*,run_id,host_session,contexts,health_policies,
                   active_start,active_end,artifacts=(),source_digests=(),report_path='lifecycle-coverage.json',
                   retained_path='retained-inputs.json',broker_path='broker-projection.json'):
    """Pure original admission compilation; context triples are inert public permit bindings."""
    from .admission import _verify_prepared
    _verify_prepared(prepared,result,resources)
    if (not _identifier(run_id) or not _identifier(host_session) or not _number(active_start)
        or not _number(active_end) or not 0<=active_start<active_end or active_end-active_start>394):
        raise CoverageError('ML-COVERAGE-ADMISSION')
    units=[];uidset={u.unit_id for u in prepared.units}
    if type(health_policies) is not dict or set(health_policies)!=uidset:raise CoverageError('ML-COVERAGE-POLICIES')
    reverse={}
    for edge in prepared.graph_edges:reverse.setdefault(edge.target,set()).add(edge.source)
    parents={}
    for u in prepared.units:
        todo=[(u.unit_id,'dispatch')];seen=set()
        while todo:
            node=todo.pop()
            if node not in seen:seen.add(node);todo.extend(reverse.get(node,()))
        parents[u.unit_id]=[v.unit_id for v in prepared.units if v.unit_id!=u.unit_id and (v.unit_id,'ready') in seen]
    for u in prepared.units:
        policy=health_policies[u.unit_id]
        if (type(policy) not in (tuple,list) or len(policy)!=2 or not all(_number(v) for v in policy)
            or not 0<policy[0]<=policy[1]<=5):raise CoverageError('ML-COVERAGE-POLICIES')
        if next(a.condition for a in u.plan.actions if a.phase=='observe')!='running':raise CoverageError('ML-COVERAGE-PROBE')
        units.append(dict(unitId=u.unit_id,planDigest=u.plan.digest,catalogIdentity=u.plan.catalog_identity,
            environmentIdentity=u.plan.environment_identity,providerId=u.plan.provider_id,providerKind=u.plan.provider_kind,
            artifactDigests=list(u.plan.artifact_digests),actions={a.phase:a.action_id for a in u.plan.actions},
            parents=parents[u.unit_id],hasDependent=any(u.unit_id in p for p in parents.values()),
            cadence=policy[0],freshness=policy[1]))
    scopes=[]
    for row in _list(contexts,128):
        if (type(row) is not list or len(row)!=3 or row[0] not in uidset or type(row[1]) is not int
            or not 1<=row[1]<=128 or not _identifier(row[2],200)):
            raise CoverageError('ML-COVERAGE-CONTEXT')
        scopes.append(dict(unitId=row[0],generation=row[1],executionId=row[2]))
    if (len({(c['unitId'],c['generation']) for c in scopes})!=len(scopes)
        or len({c['executionId'] for c in scopes})!=len(scopes)
        or any((uid,1) not in {(c['unitId'],c['generation']) for c in scopes} for uid in uidset)):
        raise CoverageError('ML-COVERAGE-CONTEXT')
    if type(artifacts) not in (tuple,list) or len(artifacts)>128:raise CoverageError('ML-COVERAGE-ARTIFACT-ADMISSION')
    entries=[]
    for item in artifacts:
        if type(item) is not ArtifactExpectation:raise CoverageError('ML-COVERAGE-ARTIFACT-ADMISSION')
        item.__post_init__()
        if item.unit_id is not None and (item.unit_id,item.generation) not in {(c['unitId'],c['generation']) for c in scopes}:
            raise CoverageError('ML-COVERAGE-ARTIFACT-ADMISSION')
        entries.append(dict(path=item.relative_path,required=item.required,maximumBytes=item.maximum_bytes,
                            unitId=item.unit_id,generation=item.generation))
    for path in (report_path,retained_path,broker_path):
        if not _path(path):raise CoverageError('ML-COVERAGE-ARTIFACT-ADMISSION')
        if not any(e['path']==path for e in entries):entries.append(dict(path=path,required=True,maximumBytes=1<<20,unitId=None,generation=0))
    if (len({e['path'] for e in entries})!=len(entries) or len({report_path,retained_path,broker_path})!=3
        or len(entries)>128 or sum(e['maximumBytes'] for e in entries)>MAX_BYTES
        or any(not next(e['required'] for e in entries if e['path']==p) for p in (report_path,retained_path,broker_path))):
        raise CoverageError('ML-COVERAGE-ARTIFACT-ADMISSION')
    pins=_list(source_digests,128)
    if any(type(d) is not str or re.fullmatch('sha256:[a-f0-9]{64}',d) is None for d in pins):raise CoverageError('ML-COVERAGE-SOURCE-PIN')
    body=dict(version=1,runId=run_id,lifecycleDigest='sha256:'+prepared.lifecycle_digest,
        experimentDigest='sha256:'+prepared.experiment_digest,hostSession=host_session,
        simulationDomain=prepared.clock.domain,horizonTicks=prepared.clock.horizon_ticks,
        start=active_start,end=active_end,units=units,contexts=sorted(scopes,key=lambda c:(c['unitId'],c['generation'])),
        steps=[dict(stepId=s.step_id,unitId=s.unit_id,phase=s.phase) for s in prepared.steps],
        artifacts=sorted(entries,key=lambda e:e['path']),sourceDigests=sorted(set(pins)|{'sha256:'+prepared.lifecycle_digest}),
        reportPath=report_path,retainedPath=retained_path,brokerPath=broker_path)
    body['templates']=_templates(body)
    _validate_admission(body)
    _report_capacity(body['templates'])
    data=canonical(body)
    if len(data)>1<<20:raise CoverageError('ML-COVERAGE-ADMISSION-SIZE')
    return CoverageAdmission(data)


def runtime_coverage_input(admission):
    body = admission.data(admission.digest)
    return dict(inputs={k:v for k,v in body.items() if k != 'templates'}, digest=admission.digest)


def decode_runtime_coverage(row):
    """Expand compact private metadata; verify the original FULL admission digest."""
    if type(row) is not dict or set(row) != {'inputs','digest'} or type(row['inputs']) is not dict:
        raise CoverageError('ML-COVERAGE-RUNTIME-CONFIG')
    body = _plain(row['inputs'])
    required={'version','runId','lifecycleDigest','experimentDigest','hostSession','simulationDomain','horizonTicks',
        'start','end','units','contexts','steps','artifacts','sourceDigests','reportPath','retainedPath','brokerPath'}
    if set(body) != required:
        raise CoverageError('ML-COVERAGE-RUNTIME-CONFIG')
    try:
        body['templates'] = []
        _validate_admission(body)
        body['templates'] = _templates(body)
    except (TypeError,KeyError,AttributeError,OverflowError) as error:
        raise CoverageError('ML-COVERAGE-RUNTIME-CONFIG') from error
    admission = CoverageAdmission(canonical(body))
    admission.data(row['digest'])
    return admission


def bind_runtime_coverage(admission, expected_digest, prepared, result, resources, *,
                          run_id, session, generation_ns, bindings, future_contexts=(), schedule=None):
    """Rederive inert admission from actual private original bindings, before sinks."""
    if type(admission) is not CoverageAdmission:
        raise CoverageError('ML-COVERAGE-RUNTIME-ADMISSION')
    body = admission.data(expected_digest)
    if (body['runId'] != run_id or body['hostSession'] != session
        or run_id in WRITER_KINDS or body['end'] > generation_ns / 1e9):
        raise CoverageError('ML-COVERAGE-RUNTIME-IDENTITY')
    if schedule is not None:
        policies = {p.unit_id: (p.cadence_seconds, p.freshness_seconds) for p in schedule.policies}
        if (any((u['cadence'], u['freshness']) != policies.get(u['unitId']) for u in body['units'])
            or schedule.required_events + 1 > schedule.event_limit):
            raise CoverageError('ML-COVERAGE-RUNTIME-CAPACITY')
        if digest(_json(schedule.canonical_bytes)) not in body['sourceDigests']:
            raise CoverageError('ML-COVERAGE-RUNTIME-SCHEDULE-SOURCE')
    all_bindings = (*bindings, *(c.binding for c in future_contexts))
    actual = admit_coverage(prepared, result, resources, run_id=run_id, host_session=session,
        contexts=[(b.unit_id, b.generation, b.execution_id) for b in all_bindings],
        health_policies={u['unitId']: (u['cadence'], u['freshness']) for u in body['units']},
        active_start=body['start'], active_end=body['end'],
        artifacts=[ArtifactExpectation(a['path'], a['required'], a['maximumBytes'], a['unitId'], a['generation'])
                   for a in body['artifacts']], source_digests=body['sourceDigests'],
        report_path=body['reportPath'], retained_path=body['retainedPath'], broker_path=body['brokerPath'])
    if actual.public_bytes != admission.public_bytes:
        raise CoverageError('ML-COVERAGE-RUNTIME-INPUTS')
    return admission


def _report_capacity(templates):
    size=4096
    for t in templates:
        size+=len(canonical(dict(obligationId=t['id'],obligationClass=t['kind'],unitId=t['unit'],
            generation=t['generation'],operationId=t['id'],required=False,applicable=False,
            status='not-applicable',evidenceIds=['x'*128,'x'*128],diagnostic='x'*256)))+1
    if size>1<<20:raise CoverageError('ML-COVERAGE-REPORT-CAPACITY')


def _validate_admission(body):
    if (not _identifier(body['runId']) or not _identifier(body['hostSession'])
        or not _identifier(body['simulationDomain']) or type(body['horizonTicks']) is not int or not 0<=body['horizonTicks']<=10000
        or any(type(body[k]) is not str or re.fullmatch('sha256:[a-f0-9]{64}',body[k]) is None for k in ('lifecycleDigest','experimentDigest'))
        or not _number(body['start']) or not _number(body['end']) or not 0<=body['start']<body['end']
        or body['end']-body['start']>394):raise CoverageError('ML-COVERAGE-ADMISSION')
    for name,cap in [('units',16),('contexts',128),('steps',128),('artifacts',128),('sourceDigests',128),('templates',8192)]:
        if type(body[name]) is not list or len(body[name])>cap:raise CoverageError('ML-COVERAGE-COUNT')
    unit_fields={'unitId','planDigest','catalogIdentity','environmentIdentity','providerId','providerKind','artifactDigests','actions','parents','hasDependent','cadence','freshness'}
    ids=[]
    for u in body['units']:
        if (type(u) is not dict or set(u)!=unit_fields or not _identifier(u['unitId'])
            or not _number(u['cadence']) or not _number(u['freshness']) or not 0<u['cadence']<=u['freshness']<=5
            or type(u['actions']) is not dict or not {'start','observe','stop','cleanup'}<=set(u['actions'])
            or any(not _identifier(v,512) for v in u['actions'].values()) or type(u['parents']) is not list
            or type(u['hasDependent']) is not bool):raise CoverageError('ML-COVERAGE-UNIT')
        ids.append(u['unitId'])
        if (type(u['planDigest']) is not str or re.fullmatch('sha256:[a-f0-9]{64}',u['planDigest']) is None
            or any(not _identifier(u[k],512) for k in ('catalogIdentity','environmentIdentity','providerId','providerKind'))
            or type(u['artifactDigests']) is not list or len(u['artifactDigests'])>128
            or any(type(d) is not str or re.fullmatch('sha256:[a-f0-9]{64}',d) is None for d in u['artifactDigests'])):raise CoverageError('ML-COVERAGE-UNIT')
    if not ids or len(set(ids))!=len(ids) or any(len(set(u['parents']))!=len(u['parents']) or not set(u['parents'])<=set(ids)-{u['unitId']} for u in body['units']):raise CoverageError('ML-COVERAGE-UNIT')
    if any(u['hasDependent']!=any(u['unitId'] in v['parents'] for v in body['units']) for u in body['units']):raise CoverageError('ML-COVERAGE-GRAPH')
    remaining=set(ids)
    while remaining:
        ready={u['unitId'] for u in body['units'] if u['unitId'] in remaining and not remaining.intersection(u['parents'])}
        if not ready:raise CoverageError('ML-COVERAGE-GRAPH')
        remaining-=ready
    scopes=[];executions=[]
    for c in body['contexts']:
        if (type(c) is not dict or set(c)!={'unitId','generation','executionId'} or c['unitId'] not in ids
            or type(c['generation']) is not int or not 1<=c['generation']<=128 or not _identifier(c['executionId'],200)):
            raise CoverageError('ML-COVERAGE-CONTEXT')
        scopes.append((c['unitId'],c['generation']));executions.append(c['executionId'])
    if len(set(scopes))!=len(scopes) or len(set(executions))!=len(executions) or any((uid,1) not in scopes for uid in ids):raise CoverageError('ML-COVERAGE-CONTEXT')
    step_ids=[]
    for s in body['steps']:
        if type(s) is not dict or set(s)!={'stepId','unitId','phase'} or s['unitId'] not in ids or not _identifier(s['stepId']):raise CoverageError('ML-COVERAGE-STEP')
        step_ids.append(s['stepId'])
    if len(set(step_ids))!=len(step_ids):raise CoverageError('ML-COVERAGE-STEP')
    paths=[]
    for a in body['artifacts']:
        if (type(a) is not dict or set(a)!={'path','required','maximumBytes','unitId','generation'}
            or not _path(a['path']) or type(a['required']) is not bool or type(a['maximumBytes']) is not int
            or not 0<a['maximumBytes']<=MAX_BYTES or type(a['generation']) is not int
            or a['unitId'] is not None and (a['unitId'],a['generation']) not in scopes):raise CoverageError('ML-COVERAGE-ARTIFACT-ADMISSION')
        paths.append(a['path'])
    if (len(set(paths))!=len(paths) or sum(a['maximumBytes'] for a in body['artifacts'])>MAX_BYTES
        or len({body[k] for k in ('reportPath','retainedPath','brokerPath')})!=3
        or any(not _path(body[k]) or body[k] not in paths for k in ('reportPath','retainedPath','brokerPath'))):raise CoverageError('ML-COVERAGE-ARTIFACT-ADMISSION')
    if any(type(d) is not str or re.fullmatch('sha256:[a-f0-9]{64}',d) is None for d in body['sourceDigests']):raise CoverageError('ML-COVERAGE-SOURCE-PIN')


@dataclass(frozen=True)
class CoverageResult:
    public_bytes: bytes

    def report(self):return _json(self.public_bytes,1<<20)

    @property
    def normal_complete(self):return self.report()['normalRecordStatus']=='complete'


def _terminal_annotation(event,payload,ad):
    action=payload['action'];scope=payload['scope']
    if action in ('disposition','cancel','run-terminal'):return True
    if action=='collect':return scope in ('unit','run')
    if action in ('stop','cleanup'):
        return scope=='unit' or scope=='step' and any(s['stepId']==payload.get('stepId')
            and s['unitId']==payload['unitId'] and s['phase']==action for s in ad['steps'])
    if action=='intent':return scope=='unit' and event['producerId']=='maestro.teardown13'
    return (action in ('validate','health-loss')
            and payload['outcome'] in ('failed','cancelled','unknown','unresolved','skipped'))


def _payload(event,ad,*,terminal_end=None):
    payload=event.get('extensions',{}).get('xverse.maestro')
    if (type(payload) is not dict or not PAYLOAD_FIELDS<=set(payload) or set(payload)-PAYLOAD_FIELDS-PAYLOAD_OPTIONAL
        or payload['schemaVersion']!='2.0' or payload['runId']!=ad['runId'] or payload['lifecycleDigest']!=ad['lifecycleDigest']
        or payload['sessionId']!=ad['hostSession'] or not _identifier(payload['operationId'])
        or type(payload['generation']) is not int or payload['generation']<0 or type(payload['outcome']) is not str or payload['outcome'] not in OUTCOMES
        or payload['scope'] not in ('run','unit','step')
        or type(payload['action']) is not str or payload['action'] not in {'intent','issued','started','probe','ready','health','health-loss','validate','cancel','stop','cleanup','collect','disposition','run-terminal'}):return None
    if payload['scope']=='run':
        if payload['unitId'] is not None or payload['generation']!=0 or 'stepId' in payload:return None
    else:
        if not _identifier(payload['unitId']) or payload['unitId'] not in {u['unitId'] for u in ad['units']}:return None
        if payload['generation'] and (payload['unitId'],payload['generation']) not in {(c['unitId'],c['generation']) for c in ad['contexts']}:return None
        if payload['scope']=='step':
            if (payload['unitId'],payload.get('stepId')) not in {(s['unitId'],s['stepId']) for s in ad['steps']}:return None
        elif 'stepId' in payload:return None
        if payload['generation']==0 and payload['action'] not in ('validate','disposition','cancel'):return None
    if payload['action']=='disposition' and DISPOSITIONS.get(payload.get('disposition'))!=payload['outcome']:return None
    if payload['action']=='run-terminal' and (payload['scope']!='run' or payload['outcome'] not in ('succeeded','failed','cancelled','unresolved')):return None
    if payload['action'] in ('probe','ready','health','health-loss') and not _identifier(payload.get('probeId')):return None
    if payload['action'] in ('probe','ready','health','health-loss') and payload.get('probeId')!='running':return None
    if 'cause' in payload and payload['cause'] not in {'normal','journal-failure','argus-failure','cancellation','readiness-failure','issuer-loss','deadline-exceeded','external'}:return None
    if 'handleRef' in payload and not _identifier(payload['handleRef']):return None
    if type(payload['sourceRefs']) is not list or not 1<=len(payload['sourceRefs'])<=16:return None
    if type(payload['dependencies']) is not list or len(payload['dependencies'])>16:return None
    host=event.get('clocks',{}).get('host',{})
    if host.get('domain')!='host:'+ad['hostSession'] or host.get('unit')!='s' or not _number(host.get('value')):return None
    end=terminal_end if terminal_end is not None and _terminal_annotation(event,payload,ad) else ad['end']
    if host['value']<ad['start'] or host['value']>end:return None
    for name,clock in event['clocks'].items():
        if type(clock) is not dict or set(clock)!={'domain','unit','value'}:return None
        if name=='utc' and (clock['domain']!='utc:'+ad['hostSession'] or clock['unit']!='s' or not _number(clock['value'])):return None
        if name=='simulation' and (clock['domain']!=ad['simulationDomain'] or clock['unit']!='tick' or type(clock['value']) is not int or not 0<=clock['value']<=ad['horizonTicks']):return None
        if name not in ('host','utc','simulation'):return None
    return payload


class _Assessment:
    def __init__(self,admission,external,annotations,public_m3,broker,entries,contents,*,runtime_scope=None,expected_runtime_digest=None):
        self.admission=admission;self.ad=admission.data(external)
        self.terminal_end,self.runtime_digest=_assessment_bounds(admission,external,runtime_scope,expected_runtime_digest)
        self.events=_list(annotations);self.m3=_list(public_m3)
        self.broker=_plain(broker) if type(broker) is dict else {}
        if len(canonical(self.broker))>1<<20:raise CoverageError('ML-COVERAGE-BROKER-SIZE')
        self.entries=_list(entries,128)
        if any(type(e) is not dict or not _path(e.get('path')) for e in self.entries):raise CoverageError('ML-COVERAGE-ARTIFACT-ENTRY')
        if type(contents) is not dict or len(contents)>128 or any(type(k) is not str or type(v) is not bytes for k,v in contents.items()):raise CoverageError('ML-COVERAGE-ARTIFACT-BYTES')
        if sum(len(v) for v in contents.values())>MAX_BYTES:raise CoverageError('ML-COVERAGE-ARTIFACT-SIZE')
        self.contents=contents;self.errors=[];self.valid={};self.payloads={};self.by_id={};self.sources={};self.brows={}
        self.units={u['unitId']:u for u in self.ad['units']};self.contexts={(c['unitId'],c['generation']):c for c in self.ad['contexts']}
        try:self._index()
        except (KeyError,TypeError,AttributeError,OverflowError) as error:raise CoverageError('ML-COVERAGE-INPUT') from error
        paths={e['path'] for e in self.ad['artifacts']}
        if (any(e.get('path') not in paths for e in self.entries) or len({e.get('path') for e in self.entries})!=len(self.entries)
            or any(p not in paths for p in contents)):
            self.errors.append('undeclared/duplicate artifact')
        for field,expected in [('retainedPath',dict(annotations=self.events,publicM3=self.m3)),('brokerPath',self.broker)]:
            data=contents.get(self.ad[field])
            if data is not None:
                try:
                    actual=_json(data)
                    if field=='retainedPath':
                        if actual.get('runId')!=self.ad['runId'] or actual.get('lifecycleDigest')!=self.ad['lifecycleDigest']:
                            self.errors.append('retained public input identity mismatch')
                        actual={k:actual.get(k) for k in ('annotations','publicM3')}
                    if canonical(actual)!=canonical(expected):self.errors.append('retained public input bytes mismatch')
                except (CoverageError,AttributeError):self.errors.append('retained public input JSON mismatch')

    def _index(self):
        total=0
        for index,record in enumerate(self.m3,1):
            size=len(canonical(record));total+=size
            if size>1<<20 or total>MAX_BYTES:raise CoverageError('ML-COVERAGE-SOURCE-SIZE')
            if (type(record) is not dict or set(record)!=M3_FIELDS or type(record.get('sequence')) is not int
                or record['sequence']!=index or record['permitNonce'] not in (None,'withheld')
                or type(record['details']) is not dict
                or record['handleId'] not in (None,'withheld') or record['handleResourceIdentity'] not in (None,'withheld')):
                self.errors.append('public M3 shape/sequence/redaction');continue
            try:
                stamp=datetime.fromisoformat(record['timestamp'])
                if stamp.tzinfo is None or stamp.utcoffset() is None:raise ValueError('unqualified source UTC')
            except (TypeError,ValueError):self.errors.append('public M3 timestamp');continue
            self.sources[index]=record
        ordinals=set();sequences=set()
        for e in self.events:
            total+=len(canonical(e))
            if total>MAX_BYTES:raise CoverageError('ML-COVERAGE-SOURCE-SIZE')
            if (type(e) is not dict or set(e)!=FIELDS or len(canonical(e))>65536 or not _identifier(e.get('eventId'))
                or not _identifier(e.get('producerId')) or e.get('eventKind')!='annotation'
                or type(e.get('ingestionOrdinal')) is not int or e['ingestionOrdinal']<=0
                or type(e.get('producerSequence')) is not int or e['producerSequence']<=0):
                self.errors.append('annotation shape');continue
            eid=e['eventId'];p=_payload(e,self.ad,terminal_end=self.terminal_end)
            if eid in self.by_id or e['ingestionOrdinal'] in ordinals or (e['producerId'],e['producerSequence']) in sequences:self.errors.append('duplicate event/ordinal/producer sequence')
            self.by_id[eid]=e;ordinals.add(e['ingestionOrdinal']);sequences.add((e['producerId'],e['producerSequence']))
            self.valid[eid]='satisfied' if p is not None else 'conflicting'
            if p is not None:self.payloads[eid]=p
            else:self.errors.append('payload/clock identity')
        admitted={u['unitId'] for u in self.ad['units']}
        supplied=self.broker.get('admittedUnits',[])
        futures=self.broker.get('futureContexts',[])
        broker_fields={'schemaVersion','runId','lifecycleDigest','hostSession','observedAt','admittedUnits','futureContexts','generations','epochs',
            'cancellationRequested','startsClosedLocally','authorityRevocationRequested','nativeCancellationAcknowledged'}
        self.broker_ok=(set(self.broker)==broker_fields and self.broker.get('schemaVersion')=='1.0'
            and _number(self.broker.get('observedAt'))
            and all(type(self.broker.get(k)) is bool for k in ('cancellationRequested','startsClosedLocally','authorityRevocationRequested','nativeCancellationAcknowledged'))
            and self.broker.get('runId')==self.ad['runId'] and self.broker.get('lifecycleDigest')==self.ad['lifecycleDigest']
            and self.broker.get('hostSession')==self.ad['hostSession'] and type(supplied) is list
            and len(supplied)==len(admitted) and {u.get('unitId') for u in supplied if type(u) is dict}==admitted
            and type(futures) is list and canonical(sorted(futures,key=lambda c:(c['unitId'],c['generation'])))==canonical([c for c in self.ad['contexts'] if c['generation']!=1]))
        if self.broker and not self.broker_ok:self.errors.append('original broker inventory mismatch')
        if self.broker_ok:
            for u in supplied:
                if (set(u)!={'unitId','initialGeneration','maximumGeneration'} or type(u['initialGeneration']) is not int
                    or u['initialGeneration']!=1 or type(u['maximumGeneration']) is not int
                    or not 1<=u['maximumGeneration']<=128
                    or u['maximumGeneration']<max(c['generation'] for c in self.ad['contexts'] if c['unitId']==u['unitId'])):
                    self.errors.append('broker admission capacity shape')
            for row in self.broker.get('generations',[]):
                required={'unitId','generation','stageAttempted','issued','intentEventId','issuedEventId','handleRef','releaseObserved',
                    'releaseRequestedAt','releaseAcknowledgedAt','directChildReaped','nativeRetired','c1Released'}
                if not required<=set(row) or set(row)-required-{'stopRequestedAt','stopAcknowledgedAt','c1TerminationObserved','c1Empty'}:
                    self.errors.append('broker fact shape');continue
                key=row.get('unitId'),row.get('generation')
                if type(row.get('generation')) is not int or key not in self.contexts or key in self.brows:self.errors.append('broker generation mismatch');continue
                self.brows[key]=row
            if any((u,1) not in self.brows for u in admitted):self.errors.append('missing original broker generation')
            for key,row in self.brows.items():
                if (type(row.get('stageAttempted')) is not bool or type(row.get('issued')) not in (bool,type(None))
                    or type(row.get('releaseObserved')) not in (bool,type(None))
                    or row.get('issued') is True and row.get('stageAttempted') is not True
                    or row.get('issued') is False and row.get('stageAttempted') is not False):
                    self.errors.append('broker fact shape')
        referenced=set()
        for eid,p in self.payloads.items():
            event=self.by_id[eid];cause=event.get('causationId');correlation=event.get('correlationId')
            if correlation is not None and (not _identifier(correlation) or correlation not in self.by_id or self.by_id[correlation]['ingestionOrdinal']>=event['ingestionOrdinal']):
                self.valid[eid]='conflicting';self.errors.append('unresolved/or late run correlation')
            if cause is not None and (cause not in self.by_id or self.by_id[cause]['ingestionOrdinal']>=event['ingestionOrdinal']):
                self.valid[eid]='conflicting';self.errors.append('causal order')
            for ref in p['sourceRefs']:
                if (type(ref) is not dict or set(ref)!={'kind','id','sha256','sequence'} or not _identifier(ref.get('id'))
                    or type(ref.get('sequence')) is not int or type(ref.get('sha256')) is not str or re.fullmatch('sha256:[a-f0-9]{64}',ref['sha256']) is None):
                    self.valid[eid]='conflicting';continue
                if ref['kind']=='m3-record':
                    source=self.sources.get(ref['sequence'])
                    if source is None:self.valid[eid]='missing';continue
                    referenced.add(ref['sequence'])
                    if ref['sha256']!=digest(source):self.valid[eid]='conflicting'
                elif ref['kind']=='admitted-lifecycle':
                    if ref['sequence']!=0 or ref['sha256'] not in {*self.ad['sourceDigests'],self.admission.digest}:self.valid[eid]='conflicting'
                elif ref['kind']=='broker-record':
                    if event['producerId']=='maestro.teardown13':
                        if not self.teardown_reference(event,p,ref):self.valid[eid]='conflicting'
                    else:
                        rows=list(self.brows.values());n=ref['sequence']
                        if not 1<=n<=len(rows) or ref['sha256']!=digest(rows[n-1]):self.valid[eid]='conflicting'
                else:self.valid[eid]='conflicting'
        for eid in sorted(self.payloads,key=lambda x:self.by_id[x]['ingestionOrdinal']):
            p=self.payloads[eid];e=self.by_id[eid];key=(p['unitId'],p['generation'])
            if self.valid[eid]!='satisfied':continue
            if (p['action']=='intent' and e['clocks']['host']['value']>self.ad['end']
                and not self.terminal_intent(e)):
                self.valid[eid]='conflicting';continue
            phase_kind_status=None
            if p['action']=='intent' and e['producerId']=='maestro.owner7':phase_kind_status=('start','intent',{'pending'})
            elif p['action']=='issued':phase_kind_status=('start','observation',{'staged'})
            elif p['action']=='started':phase_kind_status=('start','outcome',{'running'} if p['outcome']=='succeeded' else {'failed','unresolved','not-ready'})
            elif p['action'] in ('probe','ready','health','health-loss'):
                # A lost observation is recorded as health-loss/unknown over an M3 'unknown' observation (F-10, findings 439-440).
                phase_kind_status=('observe','observation',{'running'} if p['outcome']=='succeeded'
                                   else {'unknown'} if p['action']=='health-loss' and p['outcome']=='unknown' else {'not-ready'})
            elif p['action'] in ('stop','cleanup'):phase_kind_status=(p['action'],'outcome',{'stopped'} if p['action']=='stop' else {'cleaned'})
            if phase_kind_status and not self.source_ok(e,*phase_kind_status):self.valid[eid]='conflicting'
            row=self.brows.get(key)
            if p['action']=='disposition' and p.get('disposition')=='completed' and p['scope']!='run':
                refs=[self.sources.get(ref['sequence']) for ref in p['sourceRefs'] if ref['kind']=='m3-record']
                if refs and not any(r is not None and r['details'].get('maestroUnitId')==p['unitId']
                    and (p['generation']==0 or r['details'].get('generation')==p['generation']) for r in refs):self.valid[eid]='conflicting'
            if p['action'] in ('issued','started','probe','ready','health','health-loss','stop','cleanup'):
                if row is None:self.valid[eid]='unverifiable'
                elif p['action']=='started' and p['outcome']!='succeeded' and row.get('issued') is False:
                    if p.get('handleRef') is not None:self.valid[eid]='conflicting'
                elif row.get('issued') is not True:self.valid[eid]='conflicting';self.errors.append('issued/inactive contradiction')
                elif p.get('handleRef')!=row.get('handleRef'):self.valid[eid]='conflicting'
            if p['action']=='started' and row and row.get('issuedEventId') and not self.ancestor(eid,row['issuedEventId']):self.valid[eid]='conflicting'
            if p['action'] in ('started','probe','ready','health','health-loss') and not (
                    p['action']=='health-loss' and p['outcome']=='unknown'):  # lost observation: no parent proof (F-10, finding 440)
                if not self.dependencies(e):self.valid[eid]='conflicting'
        if set(self.sources)-referenced:self.errors.append('unmirrored original M3 source')
        if any(v!='satisfied' for v in self.valid.values()):self.errors.append('invalid/missing source or annotation')

    def terminal_intent(self,event):
        p=self.payloads[event['eventId']];row=self.brows.get((p['unitId'],p['generation']),{})
        if event['producerId']!='maestro.teardown13' or p.get('handleRef')!=row.get('handleRef') or row.get('issued') is not True:
            return False
        for phase in ('stop','cleanup'):
            if not self.source_ok(event,phase,'intent',{'pending'}):continue
            for ref in p['sourceRefs']:
                source=self.sources.get(ref['sequence']) if ref['kind']=='m3-record' else None
                proof=source.get('details',{}).get('teardown') if source else None
                if (source is not None and source['kind']=='intent' and source['actionId']==self.units[p['unitId']]['actions'][phase]
                    and type(proof) is dict and set(proof)=={'unit','generation','phase','stage','step','session','observed_at',
                        'boundary_digest','leader_reaped','empty','released','force_observed','handle_digest'}
                    and proof['unit']==p['unitId'] and type(proof['generation']) is int and proof['generation']==p['generation']
                    and proof['phase']==phase and proof['stage']=='intent' and proof['session']==p['sessionId']
                    and _identifier(proof['step']) and _number(proof['observed_at'])
                    and proof['observed_at']==event['clocks']['host']['value']
                    and all(type(proof[k]) is bool for k in ('leader_reaped','empty','released','force_observed'))
                    and proof['released'] is False
                    and all(type(proof[k]) is str and re.fullmatch('sha256:[a-f0-9]{64}',proof[k])
                            for k in ('boundary_digest','handle_digest'))):return True
        return False

    def teardown_reference(self,event,payload,ref):
        refs=[r for r in payload['sourceRefs'] if r['kind']=='m3-record']
        if len(refs)!=1 or ref['sequence']!=event['producerSequence'] or payload['action'] not in ('stop','cleanup'):
            return False
        source=self.sources.get(refs[0]['sequence'])
        proof=source.get('details',{}).get('teardown') if source else None
        fields={'unit','generation','phase','stage','step','session','observed_at','boundary_digest',
                'leader_reaped','empty','released','force_observed','handle_digest'}
        return (type(proof) is dict and set(proof)==fields and ref['sha256']==digest(proof)
            and proof['unit']==payload['unitId'] and type(proof['generation']) is int
            and proof['generation']==payload['generation'] and proof['phase']==payload['action']
            and proof['stage']=='outcome' and proof['step']==ref['id'] and proof['session']==payload['sessionId']
            and _number(proof['observed_at']) and proof['observed_at']==event['clocks']['host']['value']
            and all(type(proof[k]) is bool for k in ('leader_reaped','empty','released','force_observed'))
            and proof['leader_reaped'] is True and proof['empty'] is True
            and proof['released']==(payload['action']=='cleanup')
            and all(type(proof[k]) is str and re.fullmatch('sha256:[a-f0-9]{64}',proof[k])
                    for k in ('boundary_digest','handle_digest')))

    def ancestor(self,eid,target):
        seen=set()
        while eid in self.by_id and eid not in seen:
            seen.add(eid);eid=self.by_id[eid].get('causationId')
            if eid==target:return True
        return False

    def dependencies(self,event):
        p=self.payloads[event['eventId']];expected=set(self.units[p['unitId']]['parents']);actual=set()
        now=event['clocks']['host']['value']
        for dep in p['dependencies']:
            if (type(dep) is not dict or set(dep)!={'unitId','generation','probeEventId'}
                or not _identifier(dep['unitId']) or not _identifier(dep['probeEventId'])
                or dep['unitId'] not in expected or dep['unitId'] in actual or type(dep['generation']) is not int):return False
            actual.add(dep['unitId']);sample=self.by_id.get(dep['probeEventId']);proof=self.payloads.get(dep['probeEventId'],{})
            if (sample is None or self.valid.get(dep['probeEventId'])!='satisfied' or proof.get('unitId')!=dep['unitId']
                or proof.get('generation')!=dep['generation'] or proof.get('action') not in ('probe','health') or proof.get('outcome')!='succeeded'
                or sample['ingestionOrdinal']>=event['ingestionOrdinal']
                or not 0<=now-sample['clocks']['host']['value']<=self.units[dep['unitId']]['freshness']):return False
            choices=[g for (u,g),row in self.brows.items() if u==dep['unitId'] and row.get('releaseObserved') is True
                     and _number(row.get('releaseAcknowledgedAt')) and row['releaseAcknowledgedAt']<=now]
            if not choices or max(choices)!=dep['generation']:return False
        return actual==expected

    def events_for(self,action,unit=None,generation=None,scope='unit',step=None):
        return [e for eid,e in self.by_id.items() if (p:=self.payloads.get(eid)) and p['action']==action and p['scope']==scope
                and p['unitId']==unit and (generation is None or p['generation']==generation) and (step is None or p.get('stepId')==step)]

    def source_ok(self,event,phase,kind,statuses):
        p=self.payloads[event['eventId']];u=self.units[p['unitId']];ctx=self.contexts.get((p['unitId'],p['generation']))
        if ctx is None:return False
        for ref in p['sourceRefs']:
            if ref['kind']!='m3-record':continue
            r=self.sources.get(ref['sequence'])
            if r is None:continue
            d=r['details']
            if (r['actionId']==u['actions'][phase] and r['kind']==kind and r['status'] in statuses
                and r['executionId']==ctx['executionId'] and r['planDigest']==u['planDigest']
                and r['catalogIdentity']==u['catalogIdentity'] and r['environmentIdentity']==u['environmentIdentity']
                and r['handleProviderId'] in (None,u['providerId']) and r['handleProviderKind'] in (None,u['providerKind'])
                and r['handleActionId'] in (None,u['actions']['start'])
                and r['artifactDigests']==u['artifactDigests'] and d.get('maestroUnitId')==p['unitId']
                and type(d.get('generation')) is int and d['generation']==p['generation']
                and d.get('maestroRunId')==self.ad['runId'] and d.get('lifecycleDigest')==self.ad['lifecycleDigest'][7:]):
                if kind=='outcome' and phase in ('stop','cleanup') and (d.get('teardown',{}).get('leader_reaped') is not True or d['teardown'].get('empty') is not True):continue
                if kind=='outcome' and phase=='cleanup' and d['teardown'].get('released') is not True:continue
                return True
        return False

    def one(self,events,*,many=False,source=None):
        if not events:return 'missing',[]
        if not many and len(events)!=1:return 'conflicting',[e['eventId'] for e in events][:2]
        states=[self.valid[e['eventId']] if self.valid[e['eventId']]!='satisfied' or source is None or source(e) else 'conflicting' for e in events]
        good=[e['eventId'] for e,s in zip(events,states) if s=='satisfied']
        if good and (many or all(s=='satisfied' for s in states)):return 'satisfied',good[:1]
        return ('missing' if all(s=='missing' for s in states) else 'unverifiable' if any(s=='unverifiable' for s in states) else 'conflicting'),[e['eventId'] for e in events][:2]

    def terminal_proven(self,unit):
        terminal=self.events_for('run-terminal',scope='run')
        disp=self.events_for('disposition',unit,scope='unit')
        return len(terminal)==len(disp)==1 and all(self.valid[e['eventId']]=='satisfied' for e in terminal+disp)

    def inactive(self,key):
        if not self.broker_ok or not self.terminal_proven(key[0]):return None
        disposition=self.payloads[self.events_for('disposition',key[0],scope='unit')[0]['eventId']]
        current=max((g for (u,g),r in self.brows.items() if u==key[0] and (r.get('issued') is True
            or r.get('stageAttempted') is True and r.get('issued') is None)),default=0)
        if disposition['generation']!=current or disposition.get('disposition')=='completed' and current==0:return None
        terminal=self.payloads[self.events_for('run-terminal',scope='run')[0]['eventId']]
        if terminal['outcome']=='succeeded' and disposition.get('disposition')!='completed':return None
        row=self.brows.get(key)
        if row is None:
            observed=any(self.events_for(a,*key) for a in ('intent','issued','started','probe','ready','health','stop','cleanup'))
            observed=observed or any(r['details'].get('maestroUnitId')==key[0] and r['details'].get('generation')==key[1] for r in self.sources.values())
            return True if key[1]!=1 and not observed else False if observed else None
        return True if (row.get('stageAttempted') is False and row.get('issued') is False and row.get('intentEventId') is None
                        and not any(self.events_for(a,*key) for a in ('intent','issued','started','probe','ready','health','stop','cleanup'))) else False

    def assess(self):
        rows=[];expectations=[]
        for t in self.ad['templates']:
            uid=t['unit'];gen=t['generation'];suffix=t['suffix'];key=(uid,gen)
            applicable=True;status='missing';ids=[];diagnostic=None;window=None
            row=self.brows.get(key,{})
            if suffix=='integrity':
                status='conflicting' if self.errors else 'satisfied' if self.events or self.broker_ok else 'unverifiable'
                diagnostic='; '.join(sorted(set(self.errors)))[:256] or None
            elif suffix=='artifact':
                status,ids=self.artifact(t['path'])
            elif suffix in ('unit-disposition','step-disposition','run-disposition'):
                scope='unit' if suffix=='unit-disposition' else 'step' if suffix=='step-disposition' else 'run'
                events=self.events_for('disposition',uid,scope=scope,step=t.get('step'))
                status,ids=self.one(events)
                if status=='satisfied' and scope!='run':
                    p=self.payloads[events[0]['eventId']]
                    current=max((g for (u,g),r in self.brows.items() if u==uid and (r.get('issued') is True
                        or r.get('stageAttempted') is True and r.get('issued') is None)),default=0)
                    if scope=='unit' and p['generation']!=current:status='conflicting'
                    needs_start=p.get('disposition')=='completed' and (scope=='unit' or next(s['phase'] for s in self.ad['steps'] if s['stepId']==t['step']) in ('start','observe'))
                    if needs_start and (p['generation']==0 or not any(self.valid[e['eventId']]=='satisfied'
                        and self.payloads[e['eventId']]['outcome']=='succeeded' for e in self.events_for('started',uid,p['generation']))):status='conflicting'
            elif suffix=='run-validation':
                events=[e for e in self.events_for('validate',scope='run') if e['eventId']==self.ad['runId']];status,ids=self.one(events)
                if status=='satisfied' and (ids[0]!=self.ad['runId'] or self.by_id[ids[0]]['correlationId'] is not None):status='conflicting'
                if status=='satisfied' and not any(r['kind']=='admitted-lifecycle' for r in self.payloads[ids[0]]['sourceRefs']):status='conflicting'
            elif suffix in ('collect','run-terminal'):
                events=self.events_for(suffix,scope='run');status,ids=self.one(events)
                if status=='satisfied' and suffix=='run-terminal':
                    prior=[e['ingestionOrdinal'] for eid,e in self.by_id.items() if eid!=events[0]['eventId']
                        and not (self.payloads.get(eid,{}).get('action')=='disposition' and self.payloads[eid]['scope']=='run')]
                    if not self.events_for('collect',scope='run') or any(n>=events[0]['ingestionOrdinal'] for n in prior):status='conflicting'
                    if self.payloads[events[0]['eventId']]['outcome']=='succeeded':
                        for unit in self.ad['units']:
                            declared=self.events_for('disposition',unit['unitId'],scope='unit')
                            if len(declared)!=1 or self.payloads[declared[0]['eventId']].get('disposition')!='completed':status='conflicting'
                        for step in self.ad['steps']:
                            declared=self.events_for('disposition',step['unitId'],scope='step',step=step['stepId'])
                            if len(declared)!=1 or self.payloads[declared[0]['eventId']].get('disposition')!='completed':status='conflicting'
            else:
                inactive=self.inactive(key)
                issued=(True if row.get('issued') is True else False if inactive is True or
                    row.get('issued') is False and row.get('stageAttempted') is False and self.terminal_proven(uid) else None)
                intents=[e for e in self.events_for('intent',*key) if e['producerId']=='maestro.owner7']
                intent=True if intents or row.get('intentEventId') is not None else False if inactive is True else None
                started=self.events_for('started',*key)
                running=any(r['status']=='running' and r['details'].get('maestroUnitId')==uid and r['details'].get('generation')==gen for r in self.sources.values())
                active=True if running else False if started and all(self.payloads[e['eventId']]['outcome']!='succeeded' for e in started) or inactive is True else None
                if suffix=='intent':
                    applicable=intent;status,ids=self.one(intents,source=lambda e:self.source_ok(e,'start','intent',{'pending'}))
                    if status=='satisfied' and row and row.get('intentEventId')!=ids[0]:status='conflicting'
                elif suffix=='issued':
                    applicable=issued;events=self.events_for('issued',*key)
                    status,ids=self.one(events,source=lambda e:self.source_ok(e,'start','observation',{'staged'}))
                    if status=='satisfied' and (row.get('issuedEventId')!=ids[0] or self.payloads[ids[0]].get('handleRef')!=row.get('handleRef')
                        or not intents or self.by_id[ids[0]].get('causationId')!=intents[0]['eventId']):status='conflicting'
                elif suffix=='outcome':
                    applicable=intent;status,ids=self.one(started,source=lambda e:self.source_ok(e,'start','outcome',{'running','failed','unresolved','not-ready'}))
                elif suffix=='ready':
                    applicable=active if self.units[uid]['hasDependent'] else False
                    events=self.events_for('ready',*key);status,ids=self.one(events,source=lambda e:self.source_ok(e,'observe','observation',{'running'}))
                    if status=='satisfied':
                        cause=self.by_id[ids[0]].get('causationId');p=self.payloads.get(cause,{})
                        if p.get('action')!='probe' or p.get('generation')!=gen or p.get('unitId')!=uid or self.valid.get(cause)!='satisfied':status='conflicting'
                    if not events and any(self.payloads[eid].get('action')=='ready' and self.payloads[eid].get('unitId')==uid
                        and any(self.sources.get(ref['sequence'],{}).get('details',{}).get('generation')==gen for ref in self.payloads[eid]['sourceRefs'] if ref['kind']=='m3-record') for eid in self.payloads):status='conflicting'
                elif suffix in ('stop','cleanup'):
                    applicable=issued;events=self.events_for(suffix,*key)
                    status,ids=self.one(events,source=lambda e:self.source_ok(e,suffix,'outcome',{'stopped' if suffix=='stop' else 'cleaned'}))
                elif suffix=='health':
                    applicable,window=self.health_window(t,row,inactive)
                    events=[e for e in self.events_for('health',*key) if window and window[0]<=e['clocks']['host']['value']<=window[1]]
                    status,ids=self.one(events,many=True,source=lambda e:self.source_ok(e,'observe','observation',{'running','not-ready'}))
                elif suffix=='emergency':
                    dispositions=self.events_for('disposition',uid,scope='unit')
                    applicable=False if inactive is True or issued is False else True if any(self.payloads[e['eventId']].get('cause') in ('issuer-loss','journal-failure','argus-failure') for e in dispositions) else False if self.terminal_proven(uid) else None
                    status='satisfied' if row.get('c1Released') is True and (row.get('directChildReaped') is True
                        or row.get('c1TerminationObserved') is True and row.get('c1Empty') is True) else 'unverifiable'
                    if status=='satisfied':ids=['broker-'+hashlib.sha256(canonical(row)).hexdigest()]
                if applicable is False:status='not-applicable';ids=[]
                elif applicable is None:status='unverifiable';diagnostic='Applicability is not established by original retained facts.'
            required=t.get('required',True)
            output=dict(obligationId=t['id'],obligationClass=t['kind'],unitId=uid,generation=gen,operationId=t['id'],
                        required=required,applicable=applicable,status=status,evidenceIds=ids,diagnostic=diagnostic)
            rows.append(output)
            expectations.append(dict(template=t,applicable=applicable,window=window))
        normal=[r for r in rows if r['obligationClass']!='emergency-fact' and r['required']]
        # Artifact status is separate from mandatory normal records.
        normal=[r for r in normal if r['obligationClass']!='artifact']
        emergency=[r for r in rows if r['obligationClass']=='emergency-fact' and r['applicable'] is not False]
        report=dict(schemaVersion='2.0',lifecycleDigest=self.ad['lifecycleDigest'],runId=self.ad['runId'],
            assessmentStage='pre-closure',eventScope='maestro-lifecycle-before-writer-closure',
            admittedTemplatesDigest=digest(self.ad['templates']),expectedObligationsDigest=digest(expectations),trustBoundary=TRUST,
            rows=rows,normalRecordStatus=_aggregate(normal),emergencyFactStatus=_aggregate(emergency) if emergency else 'not-needed',
            overallStatus='incomplete',excludedWriterKinds=WRITER_KINDS,excludedReportRelativePath=self.ad['reportPath'],
            inputDigests=self.input_digests())
        report['retainedInputsDigest']=digest(report['inputDigests'])
        data=canonical(report)
        if len(data)>1<<20:raise CoverageError('ML-COVERAGE-REPORT-SIZE')
        return CoverageResult(data)

    def health_window(self,t,row,inactive):
        if inactive is True or row.get('releaseObserved') is False:return False,None
        if row.get('releaseObserved') is not True:return None,None
        anchor=row.get('releaseAcknowledgedAt');begin=row.get('releaseRequestedAt')
        if not _number(anchor) or not _number(begin) or not self.ad['start']<=begin<=anchor<=self.ad['end']:return None,None
        c=self.units[t['unit']]['cadence'];window=[anchor+(t['slot']-1)*c,anchor+t['slot']*c]
        if window[0]>=window[1]:return None,window
        if window[1]>self.ad['end']:return False,window
        stop_begin=row.get('stopRequestedAt');stop_end=row.get('stopAcknowledgedAt')
        if not _number(stop_begin) or not _number(stop_end) or not anchor<=stop_begin<=stop_end<=self.terminal_end:return None,window
        return (True if window[1]<=stop_begin else False if window[1]>stop_end else None),window

    def artifact(self,path):
        expected=next(e for e in self.ad['artifacts'] if e['path']==path)
        rows=[e for e in self.entries if type(e) is dict and e.get('path')==path]
        if not rows:return 'missing',[]
        if len(rows)!=1:return 'conflicting',[]
        entry=rows[0];data=self.contents.get(path)
        if (set(entry)!={'path','bytes','sha256','mediaType','schemaVersion','role'} or type(entry['bytes']) is not int
            or not 0<=entry['bytes']<=expected['maximumBytes']
            or any(not _identifier(entry[k],256) for k in ('mediaType','schemaVersion','role'))):return 'conflicting',[]
        if data is None:return 'unverifiable',[]
        if entry['bytes']!=len(data) or entry['sha256']!=hashlib.sha256(data).hexdigest():return 'conflicting',[]
        if expected['unitId'] is not None and self.brows.get((expected['unitId'],expected['generation']),{}).get('c1Released') is not True:return 'unverifiable',[]
        return 'satisfied',['artifact-'+hashlib.sha256(path.encode()).hexdigest()]

    def input_digests(self):
        path=self.ad['reportPath']
        result=dict(admission=self.admission.digest,annotations=digest(sorted(self.events,key=lambda e:e.get('ingestionOrdinal',0))),
            publicM3=digest(self.m3),broker=digest(self.broker),artifacts=digest(sorted([e for e in self.entries if e.get('path')!=path],key=lambda e:e['path'])),
            artifactBytes=digest({p:'sha256:'+hashlib.sha256(v).hexdigest() for p,v in self.contents.items() if p!=path}))
        if self.runtime_digest is not None:result['runtimeAdmission']=self.runtime_digest
        return result


def _aggregate(rows):
    if any(r['status']=='unverifiable' for r in rows):return 'unverifiable'
    if any(r['status'] not in ('satisfied','not-applicable') for r in rows):return 'incomplete'
    return 'complete'


def _assessment_bounds(admission,external,runtime_scope,expected_runtime_digest):
    ad=admission.data(external)
    if runtime_scope is None:
        if expected_runtime_digest is not None:raise CoverageError('ML-COVERAGE-RUNTIME-SCOPE')
        return ad['end'],None
    from .evidence_scope import RuntimeEvidenceScope
    if type(runtime_scope) is not RuntimeEvidenceScope:raise CoverageError('ML-COVERAGE-RUNTIME-SCOPE')
    return runtime_scope.validate(admission,external,expected_runtime_digest),expected_runtime_digest


def assess_preclosure(admission,*,expected_admission_digest,annotations,public_m3,broker,artifact_entries=(),artifact_bytes=None,runtime_scope=None,expected_runtime_digest=None):
    if type(admission) is not CoverageAdmission:raise CoverageError('ML-COVERAGE-ADMISSION')
    return _Assessment(admission,expected_admission_digest,annotations,public_m3,broker,artifact_entries,artifact_bytes or {},
        runtime_scope=runtime_scope,expected_runtime_digest=expected_runtime_digest).assess()


@dataclass(frozen=True)
class OfflineCoverageResult:
    coverage: CoverageResult
    writer_state: str
    recorded_argus_status: str | None
    assessed_argus_status: str
    reader_diagnostics: tuple[str,...]
    accepted_reader_executed: bool
    manifest_sha256: str | None = None
    accepted_annotation_bytes: bytes | None = None


def _offline_failure(admission,external,reason):
    result=assess_preclosure(admission,expected_admission_digest=external,annotations=[],public_m3=[],broker={})
    report=result.report();report['assessmentStage']='offline-post-closure';report['overallStatus']='unverifiable'
    return OfflineCoverageResult(CoverageResult(canonical(report)),'unverifiable',None,'unverifiable',(reason,),False)


def verify_closed(admission,root,*,expected_admission_digest,runtime_scope=None,expected_runtime_digest=None):
    """Independent accepted-reader path. Confined evidence reads are its only I/O."""
    from xverse.argus import EvidenceStore,EvidenceLimits
    from xverse.argus.recovery import read_confined_bytes

    if type(admission) is not CoverageAdmission:raise CoverageError('ML-COVERAGE-ADMISSION')
    ad=admission.data(expected_admission_digest)
    _assessment_bounds(admission,expected_admission_digest,runtime_scope,expected_runtime_digest)
    declarations={e['path']:e for e in ad['artifacts']}
    diagnostics=[]
    def read(path,maximum):
        data,errors=read_confined_bytes(root,path,max_bytes=maximum,bound_field='Maestro admitted bytes')
        diagnostics.extend(e.code for e in errors)
        return data
    # Bound manifest-indexed file work before the accepted reader hashes artifacts.
    raw_manifest=read('manifest.json',1<<20)
    try:
        manifest=_json(raw_manifest,1<<20)
        entries=manifest.get('artifacts',[])
        if (type(entries) is not list or len(entries)>128 or any(type(e) is not dict or e.get('path') not in declarations
            or type(e.get('bytes')) is not int or not 0<=e['bytes']<=declarations[e['path']]['maximumBytes'] for e in entries)
            or sum(e['bytes'] for e in entries)>MAX_BYTES):raise CoverageError('ML-COVERAGE-MANIFEST-BOUND')
        stream=manifest.get('eventStream',{})
        if (type(stream) is not dict or not _path(stream.get('path')) or type(stream.get('bytes')) is not int
            or not 0<=stream['bytes']<=MAX_BYTES):raise CoverageError('ML-COVERAGE-MANIFEST-BOUND')
        if read(stream['path'],MAX_BYTES) is None:raise CoverageError('ML-COVERAGE-STREAM-BOUND')
    except (CoverageError,TypeError,AttributeError) as error:
        return _offline_failure(admission,expected_admission_digest,'ML-COVERAGE-MANIFEST-BOUND: '+type(error).__name__)
    limits=EvidenceLimits(max_event_bytes=65536,max_events=8192,max_read_records=8192,max_id_length=128,
        max_text_length=256,max_payload_bytes=65536,max_artifacts=128,max_obligations=8192,
        max_diagnostic_count=128,max_manifest_bytes=1<<20,max_causal_index_entries=8192)
    reader=EvidenceStore.read_run(root,limits=limits)
    manifest=reader.manifest
    diagnostics.extend(d.code for d in reader.diagnostics)
    actual_entries=manifest.get('artifacts',[])
    contents={}
    for path,expectation in declarations.items():
        if not expectation['required'] and not any(e.get('path')==path for e in actual_entries):continue
        data=read(path,expectation['maximumBytes'])
        if data is not None:contents[path]=data
    try:
        retained=_json(contents.get(ad['retainedPath']))
        broker=_json(contents.get(ad['brokerPath']))
        if (type(retained) is not dict or retained.get('runId')!=ad['runId'] or retained.get('lifecycleDigest')!=ad['lifecycleDigest']
            or type(retained.get('annotations')) is not list or type(retained.get('publicM3')) is not list):raise CoverageError('ML-COVERAGE-RETAINED-IDENTITY')
    except CoverageError:
        retained=dict(annotations=[],publicM3=[]);broker={};diagnostics.append('ML-COVERAGE-RETAINED-INPUT-MISSING')
    annotations=[]
    for event in reader.records():
        if event.get('eventKind') in WRITER_KINDS:continue
        if event.get('extensions',{}).get('xverse.maestro') is not None:
            annotations.append({field:event.get(field) for field in FIELDS})
    try:
        assessment=_Assessment(admission,expected_admission_digest,annotations,retained['publicM3'],broker,actual_entries,contents,
            runtime_scope=runtime_scope,expected_runtime_digest=expected_runtime_digest)
        core=assessment.assess().report()
    except CoverageError:
        failure=_offline_failure(admission,expected_admission_digest,'ML-COVERAGE-PUBLIC-INPUT-SHAPE')
        return OfflineCoverageResult(failure.coverage,manifest.get('writerState','unverifiable'),reader.recorded_evidence_status,
            reader.assessed_evidence_status,tuple(dict.fromkeys([*diagnostics,'ML-COVERAGE-PUBLIC-INPUT-SHAPE']))[:128],True,
            hashlib.sha256(raw_manifest).hexdigest())
    report=dict(core)
    report['assessmentStage']='offline-post-closure'
    report_row=dict(obligationId='ob.artifact.'+hashlib.sha256(ad['reportPath'].encode()).hexdigest(),
        obligationClass='artifact',unitId=None,generation=0,operationId='ob.coverage-report',required=True,
        applicable=True,status='missing',evidenceIds=[],diagnostic=None)
    status,ids=assessment.artifact(ad['reportPath']);report_row.update(status=status,evidenceIds=ids)
    stored=None
    try:
        stored=_json(contents.get(ad['reportPath']),1<<20)
        keys=set(core)-{'assessmentStage','overallStatus'}
        if (type(stored) is not dict or set(stored)!=set(core) or stored.get('assessmentStage')!='pre-closure'
            or stored.get('overallStatus')!='incomplete' or any(canonical(stored[k])!=canonical(core[k]) for k in keys)):
            report_row.update(status='conflicting',diagnostic='Stored provisional core disagrees with independent recomputation.')
    except CoverageError:
        report_row.update(status='missing' if ad['reportPath'] not in contents else 'unverifiable',diagnostic='Coverage report absent or not valid bounded JSON.')
    if canonical(retained['annotations'])!=canonical(annotations):
        report_row.update(status='conflicting',diagnostic='Actual reader annotations disagree with retained caller fields.')
    plan=manifest.get('plan',{}).get('semanticDigest',{})
    if manifest.get('runId')!=ad['runId'] or plan.get('algorithm')!='sha256' or 'sha256:'+str(plan.get('value'))!=ad['experimentDigest']:
        report_row.update(status='conflicting',diagnostic='Manifest run/experiment identity disagrees with original admission.')
    final_manifest=read('manifest.json',1<<20)
    if final_manifest!=raw_manifest:report_row.update(status='unverifiable',diagnostic='Manifest changed during offline verification.')
    report['rows']=[*report['rows'],report_row]
    required=[r for r in report['rows'] if r['required']]
    overall=_aggregate(required)
    writer=manifest.get('writerState','unverifiable')
    if overall=='complete' and (writer!='closed' or reader.assessed_evidence_status!='complete' or diagnostics):overall='incomplete'
    if reader.diagnostics and overall!='unverifiable':overall='unverifiable'
    report['overallStatus']=overall
    # This comparison intentionally keeps the recorded provisional core unchanged.
    result=CoverageResult(canonical(report))
    return OfflineCoverageResult(result,writer,reader.recorded_evidence_status,reader.assessed_evidence_status,
                                 tuple(dict.fromkeys(diagnostics))[:128],True,
                                 hashlib.sha256(final_manifest).hexdigest() if final_manifest is not None else None,
                                 canonical(annotations))
