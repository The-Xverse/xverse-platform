"""Original v6 report/closure protocol; public receipts grant no runtime authority."""
from dataclasses import asdict, dataclass, field
import hashlib
import re
import time

from xverse.argus.recovery import read_confined_bytes
from .coverage import canonical, _json, assess_preclosure
from .collection_runtime import decode_context, document, output_available, validate_item
from .evidence import retained_snapshot
from .persistence import PersistenceError
from .public_blobs import decode_broker_data, write_public_bytes
from .runtime_verification import runtime_admission_digest
from .evidence_scope import RuntimeEvidenceScope
from .terminal_writer import TerminalWriterObservation, close_runtime_writer
from .time import HostDeadline


def _hash(data):
    return 'sha256:'+hashlib.sha256(data).hexdigest()


class WorkerTerminal:
    """Original sealed admission and privately retained report predicate/receipt."""
    def __init__(self,evidence):
        if evidence.collection_source is None:
            raise PersistenceError('ML-TERMINAL-ADMISSION')
        self.evidence=evidence;self.plan=evidence.collection_plan
        self.ad=evidence.coverage.data(evidence.coverage.digest)
        self.runtime_digest=runtime_admission_digest(evidence.coverage,self.plan,evidence.collection_generation_ns)
        self.assessment_scope=RuntimeEvidenceScope(self.plan.canonical_bytes,evidence.collection_generation_ns)
        self.end=None;self.publish_attempted=self.close_attempted=False
        self.receipt_bytes=None;self.eligible=self.finalizable=False

    def checkpoint(self,deadline,check):
        check(deadline)
        if (self.end is None or time.monotonic_ns()>=self.end
            or int(deadline.monotonic_seconds*1e9)>self.end):
            raise PersistenceError('ML-TERMINAL-DEADLINE')

    def read(self,path,cap,deadline,check):
        from .artifacts import _root, _identity
        def rooted():
            self.checkpoint(deadline,check)
            current=_root(self.evidence.root)
            try:
                original,identity=self.evidence.export_root
                if _identity(current)!=identity or _identity(original)!=identity:
                    raise PersistenceError('ML-TERMINAL-ROOT')
            finally:
                import os
                os.close(current)
        rooted()
        raw,errors=read_confined_bytes(self.evidence.root,path,max_bytes=cap,bound_field='original terminal evidence')
        rooted()
        if errors or raw is None:raise PersistenceError('ML-TERMINAL-CONFINED-BYTES')
        return raw

    def indexed(self,path,deadline,check):
        declaration=next(r for r in self.ad['artifacts'] if r['path']==path)
        receipt=self.evidence.artifact_receipts.get(path)
        if receipt is None:raise PersistenceError('ML-TERMINAL-INDEX-MISSING')
        entry=_json(receipt,65536)
        raw=self.read(path,declaration['maximumBytes'],deadline,check)
        if (entry.get('path')!=path or entry.get('bytes')!=len(raw)
            or entry.get('sha256')!=hashlib.sha256(raw).hexdigest()):
            raise PersistenceError('ML-TERMINAL-INDEX-CHANGED')
        return entry,raw

    def publish(self,claims,end,deadline,check):
        if (self.publish_attempted or type(end) is not int
            or not 0<end-time.monotonic_ns()<=int(self.plan.terminal_seconds*1e9)
            or end>self.evidence.collection_generation_ns-int(self.plan.drain_seconds*1e9)):
            raise PersistenceError('ML-TERMINAL-REQUEST')
        self.end=end;self.publish_attempted=True
        self.checkpoint(deadline,check)
        e=self.evidence;retained_entry=entry=None;stage='collection';blockers=[]
        normal=required=collected=terminal=False;annotations=records=0;core_digest=None
        try:
            state=e.collection_state
            if state is None or not state.finished:raise PersistenceError('ML-TERMINAL-COLLECTION')
            _,metadata=self.indexed(self.plan.metadata_path,deadline,check)
            body=_json(metadata,self.plan.metadata_maximum_bytes)
            decode_context(canonical(body['context']),e.coverage,e.coverage.digest,self.plan,
                           e.collection_generation_ns,body['startedAt'])
            if metadata!=canonical(document(self.plan,state.context,state.items,state.started_at,body['finishedAt'])):
                raise PersistenceError('ML-TERMINAL-COLLECTION')
            for index,item in enumerate(state.items):
                validate_item(self.plan,index,dict(index=index,item=item))
                if item['status']=='collected' and not output_available(state.context,self.plan.declarations[index]):
                    raise PersistenceError('ML-TERMINAL-COLLECTION')
            collected=body['collectionComplete']
            stage='final-broker'
            _,broker_raw=self.indexed(self.ad['brokerPath'],deadline,check)
            broker=decode_broker_data(broker_raw,e.coverage,e.coverage.digest,observed_until=time.monotonic())
            for row in broker['generations']:
                issued=e.issued_handles.get((row['unitId'],row['generation']))
                if issued is None:
                    if row['issued'] is True:raise PersistenceError('ML-TERMINAL-ISSUANCE')
                else:
                    handle,event=issued
                    reference='handle-'+hashlib.sha256(canonical([self.ad['runId'],asdict(handle)])).hexdigest()
                    if row['issued'] is not True or row['issuedEventId']!=event or row['handleRef']!=reference:
                        raise PersistenceError('ML-TERMINAL-ISSUANCE')
            stage='retained-inputs'
            cap=next(a['maximumBytes'] for a in self.ad['artifacts'] if a['path']==self.ad['retainedPath'])
            retained,annotations,records=retained_snapshot(e,claims,cap,lambda:self.checkpoint(deadline,check))
            if self.ad['retainedPath'] in e.artifact_receipts:
                retained_entry,previous=self.indexed(self.ad['retainedPath'],deadline,check)
                if previous!=retained:raise PersistenceError('ML-TERMINAL-RETAINED-CHANGED')
            else:
                retained_entry=write_public_bytes(e,self.ad['retainedPath'],retained,cap,
                    lambda:self.checkpoint(deadline,check))
            facts=_json(retained,cap)
            terminals=[r for r in facts['annotations'] if r['extensions']['xverse.maestro']['action']=='run-terminal']
            if (len(terminals)!=1 or broker['observedAt']<terminals[0]['clocks']['host']['value']
                or broker['observedAt']<body['finishedAt']):
                raise PersistenceError('ML-TERMINAL-FINAL-BROKER')
            terminal=terminals[0]['extensions']['xverse.maestro']['outcome']=='succeeded'
            stage='assessment';entries=[];contents={}
            allowed={r['path'] for r in self.ad['artifacts']}
            if set(e.artifact_receipts)-allowed:raise PersistenceError('ML-TERMINAL-ARTIFACT-UNIVERSE')
            for path in sorted(e.artifact_receipts):
                if path==self.ad['reportPath']:raise PersistenceError('ML-TERMINAL-REPORT-REPLAY')
                entries.append(_json(e.artifact_receipts[path],65536))
                cap=next(a['maximumBytes'] for a in self.ad['artifacts'] if a['path']==path)
                try:
                    contents[path]=self.read(path,cap,deadline,check)
                except (OSError,PersistenceError):
                    self.checkpoint(deadline,check)
            report=assess_preclosure(e.coverage,expected_admission_digest=e.coverage.digest,
                annotations=facts['annotations'],public_m3=facts['publicM3'],broker=broker,
                artifact_entries=entries,artifact_bytes=contents,runtime_scope=self.assessment_scope,
                expected_runtime_digest=self.runtime_digest)
            core=report.report();core_digest=_hash(report.public_bytes)
            normal=core['normalRecordStatus']=='complete'
            required=all(r['status'] in ('satisfied','not-applicable') for r in core['rows'] if r['required'])
            if not normal:blockers.append('normal-records')
            if not required:blockers.append('required-coverage')
            if any(r['applicable'] is None for r in core['rows']):blockers.append('uncertain-applicability')
            if any(not r['required'] and r['status'] in ('conflicting','unverifiable') for r in core['rows']):
                blockers.append('optional-integrity')
            if not collected:blockers.append('collection')
            if not terminal:blockers.append('terminal-outcome')
            stage='report-write'
            cap=next(a['maximumBytes'] for a in self.ad['artifacts'] if a['path']==self.ad['reportPath'])
            entry=write_public_bytes(e,self.ad['reportPath'],report.public_bytes,cap,
                                    lambda:self.checkpoint(deadline,check),schema_version='2.0')
            stage='published'
        except Exception:
            blockers.append('publication')
        self.checkpoint(deadline,check)
        self.eligible=not blockers and entry is not None
        receipt=dict(schemaVersion='1.0',admissionDigest=e.coverage.digest,runtimeAdmissionDigest=self.runtime_digest,
            reportEndNs=end,entry=entry,retainedEntry=retained_entry,coreDigest=core_digest,
            normalComplete=normal,requiredRowsSatisfied=required,collectionComplete=collected,
            terminalSucceeded=terminal,eligible=self.eligible,blockers=blockers,stage=stage,
            annotationCount=annotations,m3Count=records)
        self.finalizable=finalizable(receipt)
        self.receipt_bytes=canonical(receipt)
        if len(self.receipt_bytes)>65536:raise PersistenceError('ML-TERMINAL-RECEIPT-SIZE')
        return receipt

    def close(self,end,receipt_digest,deadline,check):
        if (self.close_attempted or self.receipt_bytes is None or type(end) is not int
            or end!=self.end or receipt_digest!=_hash(self.receipt_bytes)):
            raise PersistenceError('ML-TERMINAL-CLOSE-ORIGINAL')
        self.checkpoint(deadline,check);self.close_attempted=True
        e=self.evidence
        observation=close_runtime_writer(e.writer,e.root,eligible=self.eligible,admission=e.coverage,
            plan=self.plan,generation_ns=e.collection_generation_ns,expected_admission_digest=e.coverage.digest,
            expected_runtime_digest=self.runtime_digest,check=lambda:self.checkpoint(deadline,check),
            finalize=self.finalizable)
        return dict(reportReceiptDigest=receipt_digest,writer=asdict(observation))


@dataclass(frozen=True)
class TerminalReceipt:
    public_bytes: bytes = field(repr=False)
    lifecycle_complete: bool = field(default=False,init=False)

    def public_data(self):return _json(self.public_bytes,65536)


def finalizable(report):
    """Eligible, or factually complete with a failed execution (finding 471)."""
    return report['eligible'] or (report['blockers']==['terminal-outcome'] and report['entry'] is not None
        and report['retainedEntry'] is not None and report['stage']=='published'
        and all(report[k] is True for k in ('normalComplete','requiredRowsSatisfied','collectionComplete'))
        and report['terminalSucceeded'] is False)


def _report_ack(client,body,end):
    keys={'schemaVersion','admissionDigest','runtimeAdmissionDigest','reportEndNs','entry','retainedEntry',
          'coreDigest','normalComplete','requiredRowsSatisfied','collectionComplete','terminalSucceeded',
          'eligible','blockers','stage','annotationCount','m3Count'}
    def reject():raise PersistenceError('ML-TERMINAL-REPORT-ACK')
    if (type(body) is not dict or set(body)!=keys or body['schemaVersion']!='1.0'
        or body['admissionDigest']!=client.coverage_digest or type(body['reportEndNs']) is not int or body['reportEndNs']!=end
        or body['runtimeAdmissionDigest']!=runtime_admission_digest(client.coverage,client.collection,client.generation_ns)
        or any(type(body[k]) is not bool for k in ('normalComplete','requiredRowsSatisfied','collectionComplete','terminalSucceeded','eligible'))
        or type(body['blockers']) is not list or len(body['blockers'])>7
        or any(type(b) is not str or b not in ('normal-records','required-coverage','uncertain-applicability',
            'optional-integrity','collection','terminal-outcome','publication') for b in body['blockers'])
        or len(set(body['blockers']))!=len(body['blockers'])
        or body['stage'] not in ('collection','final-broker','retained-inputs','assessment','report-write','published')
        or any(type(body[k]) is not int or not 0<=body[k]<=8192 for k in ('annotationCount','m3Count'))):reject()
    ad=client.coverage.data(client.coverage_digest)
    for key,path,schema in [('entry',ad['reportPath'],'2.0'),('retainedEntry',ad['retainedPath'],'1.0')]:
        row=body[key]
        if row is None:continue
        cap=next(r['maximumBytes'] for r in ad['artifacts'] if r['path']==path)
        if (type(row) is not dict or set(row)!={'path','bytes','sha256','mediaType','schemaVersion','role'}
            or row['path']!=path or type(row['bytes']) is not int or not 0<row['bytes']<=cap
            or type(row['sha256']) is not str or re.fullmatch('[a-f0-9]{64}',row['sha256']) is None
            or row['mediaType']!='application/json' or row['schemaVersion']!=schema or row['role']!='evidence'):reject()
    if (body['coreDigest'] is not None and (type(body['coreDigest']) is not str
        or re.fullmatch('sha256:[a-f0-9]{64}',body['coreDigest']) is None)
        or body['entry'] is not None and body['coreDigest']!='sha256:'+body['entry']['sha256']
        or body['eligible']!=(not body['blockers'] and body['entry'] is not None)
        or body['eligible'] and (body['retainedEntry'] is None or body['stage']!='published'
            or not all(body[k] for k in ('normalComplete','requiredRowsSatisfied','collectionComplete','terminalSucceeded')))):
        reject()
    return body


def _writer_ack(body,report):
    if (type(body) is not dict or set(body)!={'reportReceiptDigest','writer'}
        or body['reportReceiptDigest']!=_hash(canonical(report))):
        raise PersistenceError('ML-TERMINAL-CLOSE-ACK')
    row=body['writer']
    bools=('eligible','finalize_attempted','finalize_completed','abort_attempted','abort_completed',
           'collection_verified','collection_complete','evidence_complete')
    if (type(row) is not dict or set(row)!=set(TerminalWriterObservation.__dataclass_fields__)
        or any(type(row[k]) is not bool for k in bools) or row['eligible'] is not report['eligible']
        or row['before_state'] not in ('open','closed','failed') or row['after_state'] not in ('open','closed','failed')
        or row['stage'] not in ('not-open','finalize-completed','finalize-error','flush-error','abort-completed','abort-error')
        or row['abort_usability'] not in ('unknown','usable')
        or row['after_usability']!={'open':'unknown','closed':'not-applicable','failed':'unusable'}[row['after_state']]
        or row['finalize_attempted'] != (finalizable(report) and row['before_state']=='open')
        or row['before_state']!='open' and (row['after_state']!=row['before_state'] or row['stage']!='not-open'
            or any(row[k] for k in ('finalize_attempted','finalize_completed','abort_attempted','abort_completed')))
        or row['abort_attempted']!=(row['abort_usability']=='usable')
        or row['finalize_completed']!=(row['stage']=='finalize-completed')
        or row['abort_completed']!=(row['stage']=='abort-completed')
        or row['finalize_completed'] and row['after_state']!='closed'
        or row['abort_completed'] and row['after_state']!='failed'
        or row['finalize_completed'] and row['abort_attempted']
        or row['durable_writer_state'] not in (None,'open','closed','failed','unverifiable')
        or row['durable_recorded_status'] not in (None,'complete','incomplete','unassessed')
        or row['durable_assessed_status'] not in (None,'complete','incomplete','unverifiable')
        or row['manifest_sha256'] is not None and (type(row['manifest_sha256']) is not str
            or re.fullmatch('[a-f0-9]{64}',row['manifest_sha256']) is None)
        or type(row['reader_diagnostics']) is not list or len(row['reader_diagnostics'])>128
        or any(type(c) is not str or not 0<len(c)<=256 for c in row['reader_diagnostics'])
        or row['evidence_complete'] and (not row['collection_verified'] or not row['collection_complete']
            or row['after_state']!='closed' or row['durable_writer_state']!='closed'
            or row['durable_assessed_status']!='complete' or row['reader_diagnostics'])):
        raise PersistenceError('ML-TERMINAL-CLOSE-ACK')
    return row


def finish_run(client,broker,deadline):
    from .run_broker import RunBroker
    client._holder()
    if (type(broker) is not RunBroker or broker.storage is not client or client.collection is None
        or type(deadline) is not HostDeadline or deadline.session!=client.session):
        raise PersistenceError('ML-TERMINAL-ORIGINAL')
    deadline.__post_init__();broker._holder()
    identity=deadline.session,deadline.monotonic_seconds
    if not client._terminal_lock.acquire(False):raise PersistenceError('ML-TERMINAL-CONFLICT')
    try:
        if client._terminal_outcome is not None:
            original,scope,result,_=client._terminal_outcome
            if original is not broker or scope!=identity:raise PersistenceError('ML-TERMINAL-ORIGINAL')
            return result
        if client._terminal_attempted:raise PersistenceError('ML-TERMINAL-UNCERTAIN')
        plan=client.collection;end=int(deadline.monotonic_seconds*1e9)
        if (client._collection_outcome is None or client._collection_outcome[0] is not broker
            or not 0<end-time.monotonic_ns()<=int(plan.terminal_seconds*1e9)
            or end>client.generation_ns-int(plan.drain_seconds*1e9)
            or client._request_limit-client._sequence<2+int(client._broker_publication is None)):
            raise PersistenceError('ML-TERMINAL-BUDGET')
        def operation_end():
            client._live(allow_cancel=True)
            now=time.monotonic()
            service=HostDeadline(client.session,min(end/1e9,now+.5,broker.session._lease/1e9))
            lease=broker.service_terminal(service)
            value=min(end/1e9,lease/1e9-.05)
            if value<=time.monotonic():raise PersistenceError('ML-TERMINAL-TIMEOUT')
            return HostDeadline(client.session,value)
        client._terminal_attempted=True
        facts=dict(schemaVersion='1.0',report=None,writer=None,diagnostic=None,
                   lastAcknowledgedWriterState=client.last_writer_state,storageDrain=None)
        try:
            client.publish_broker_artifact(broker,operation_end())
            _,_,reply=client._rpc('terminal-report',dict(action='publish',reportEndNs=end),operation_end())
            facts['report']=_report_ack(client,reply,end)
            _,_,reply=client._rpc('terminal-report',dict(action='close',reportEndNs=end,
                reportReceiptDigest=_hash(canonical(facts['report']))),operation_end())
            writer=_writer_ack(reply,facts['report']);facts['writer']=writer
            client.last_writer_state=writer['after_state']
            facts['lastAcknowledgedWriterState']=client.last_writer_state
            if writer['after_state'] in ('closed','failed'):client._aborted=True
            else:client._fail()
            client.latch.cancel('persistence-terminal')
        except Exception as error:
            facts['diagnostic']=str(error) if re.fullmatch('ML-[A-Z0-9-]{1,120}',str(error)) else 'ML-TERMINAL-UNRESOLVED'
            client._fail()
        # Storage wait is its own observation; other original helper/root/C1 waits
        # remain with RunClosure. Never infer their completion from writer ACKs.
        try:
            drain_end=min(client.generation_ns/1e9,end/1e9+plan.drain_seconds,
                          time.monotonic()+plan.drain_seconds)
            facts['storageDrain']=asdict(client.drain(HostDeadline(client.session,drain_end)))
        except Exception:
            facts['diagnostic']=facts['diagnostic'] or 'ML-TERMINAL-STORAGE-WAIT-UNKNOWN'
        result=TerminalReceipt(canonical(facts))
        client._terminal_outcome=client._terminal_outcome_pin=(broker,identity,result,result.public_bytes)
        return result
    finally:client._terminal_lock.release()
