"""Independent closed runtime evidence, bound to external original admission pins."""
from dataclasses import dataclass
import hashlib
import re

from xverse.argus.recovery import read_confined_bytes
from .coverage import CoverageError, canonical, _json, _number, verify_closed
from .collection_plan import CollectionPlan, decode_collection
from .collection_evidence import decode_context, document, output_available, validate_item, decode_broker_data
from .evidence_scope import RuntimeEvidenceScope,runtime_admission_digest


@dataclass(frozen=True)
class RuntimeVerification:
    lifecycle: object
    collection_verified: bool
    collection_complete: bool
    diagnostics: tuple[str, ...]

    @property
    def complete(self):
        """Evidence completeness; grants no execution success or helper-cleanup credit."""
        return (self.collection_verified and self.collection_complete and not self.diagnostics
                and self.lifecycle.coverage.report()['overallStatus']=='complete')


def validate_runtime_admission(admission, plan, *, expected_admission_digest,
                               expected_runtime_digest, generation_ns):
    """Validate external original pins without reading the evidence root."""
    ad=admission.data(expected_admission_digest)
    if (type(plan) is not CollectionPlan or type(generation_ns) is not int
        or generation_ns < int((ad['end']+plan.terminal_reserve_seconds)*1e9)
        or runtime_admission_digest(admission,plan,generation_ns)!=expected_runtime_digest):
        raise CoverageError('ML-RUNTIME-ADMISSION-PIN')
    decode_collection(_json(plan.canonical_bytes),admission,expected_admission_digest)
    return ad


def verify_runtime_closed(admission, plan, root, *, expected_admission_digest,
                          expected_runtime_digest, generation_ns):
    """Confined read-only verification using caller-trusted original external pins."""
    ad=validate_runtime_admission(admission,plan,expected_admission_digest=expected_admission_digest,
        expected_runtime_digest=expected_runtime_digest,generation_ns=generation_ns)
    lifecycle=verify_closed(admission,root,expected_admission_digest=expected_admission_digest,
        runtime_scope=RuntimeEvidenceScope(plan.canonical_bytes,generation_ns),expected_runtime_digest=expected_runtime_digest)
    # Reuse actual accepted annotations from the bounded generic pass. Never run a
    # second accepted reader against an unchecked or changed manifest.
    if (not lifecycle.accepted_reader_executed or lifecycle.accepted_annotation_bytes is None
        or lifecycle.writer_state not in ('closed','failed')):
        return RuntimeVerification(lifecycle,False,False,('ML-RUNTIME-CLOSED-READER',))
    def read(path,maximum):
        data,diagnostics=read_confined_bytes(root,path,max_bytes=maximum,bound_field='original runtime evidence')
        if diagnostics or data is None:raise CoverageError('ML-RUNTIME-CONFINED-BYTES')
        return data
    def indexed(manifest,path,data):
        entries=[e for e in manifest['artifacts'] if e['path']==path]
        if (len(entries)!=1 or entries[0]['bytes']!=len(data)
            or entries[0]['sha256']!=hashlib.sha256(data).hexdigest()):
            raise CoverageError('ML-RUNTIME-COLLECTION-INDEX')
    try:
        raw_manifest=read('manifest.json',1<<20)
        if hashlib.sha256(raw_manifest).hexdigest()!=lifecycle.manifest_sha256:
            raise CoverageError('ML-RUNTIME-MANIFEST-CHANGED')
        manifest=_json(raw_manifest,1<<20)
        raw=read(plan.metadata_path,plan.metadata_maximum_bytes)
        indexed(manifest,plan.metadata_path,raw)
        body=_json(raw,plan.metadata_maximum_bytes)
        if (type(body) is not dict or not _number(body.get('startedAt')) or not _number(body.get('finishedAt'))
            or not _number(body.get('collectionDeadlineNs'))
            or not body['startedAt']<=body['finishedAt']<=body['collectionDeadlineNs']/1e9):
            raise CoverageError('ML-RUNTIME-COLLECTION-TIME')
        context=decode_context(canonical(body['context']),admission,expected_admission_digest,
                               plan,generation_ns,body['startedAt'])
        if type(body['items']) is not list or len(body['items'])!=len(plan.declarations):
            raise CoverageError('ML-RUNTIME-COLLECTION-UNIVERSE')
        for index,item in enumerate(body['items']):
            validate_item(plan,index,dict(index=index,item=item))
            if item['status']=='collected' and not output_available(context,plan.declarations[index]):
                raise CoverageError('ML-RUNTIME-COLLECTION-OWNERSHIP')
        if raw!=canonical(document(plan,context,body['items'],body['startedAt'],body['finishedAt'])):
            raise CoverageError('ML-RUNTIME-COLLECTION-DOCUMENT')
        cap=next(a['maximumBytes'] for a in ad['artifacts'] if a['path']==ad['brokerPath'])
        broker_raw=read(ad['brokerPath'],cap);indexed(manifest,ad['brokerPath'],broker_raw)
        broker=decode_broker_data(broker_raw,admission,expected_admission_digest)
        if broker['observedAt']<body['finishedAt']:
            raise CoverageError('ML-RUNTIME-COLLECTION-FINAL-TIME')
        final={(r['unitId'],r['generation']):r for r in broker['generations']}
        prior={(r['unitId'],r['generation']):r for r in context['broker']['generations']}
        for index,item in enumerate(body['items']):
            if item['status']=='collected':
                key=item['unitId'],item['generation'];row=final.get(key,{})
                if (not all(row.get(k) is True for k in ('issued','directChildReaped','c1Empty','c1Released'))
                    or any(row.get(k) is None or row.get(k)!=prior[key][k]
                           for k in ('handleRef','issuedEventId','intentEventId'))):
                    raise CoverageError('ML-RUNTIME-COLLECTION-FINAL-FACTS')
                actual=read(item['destination'],plan.byte_limits[index])
                indexed(manifest,item['destination'],actual)
                if len(actual)!=item['bytes'] or hashlib.sha256(actual).hexdigest()!=item['sha256']:
                    raise CoverageError('ML-RUNTIME-COLLECTION-CONTENT')
        annotations=_json(lifecycle.accepted_annotation_bytes)
        payload=lambda e:e.get('extensions',{}).get('xverse.maestro',{})
        events=[e for e in annotations if payload(e).get('scope')=='run' and payload(e).get('action')=='collect']
        if (len(events)!=1 or events[0].get('annotation')!={'text':'Maestro original declared collection sha256:'+hashlib.sha256(raw).hexdigest()}
            or payload(events[0])['outcome']!=('succeeded' if body['collectionComplete'] else 'unknown')
            or not _number(events[0]['clocks']['host']['value'])
            or not body['finishedAt']<=events[0]['clocks']['host']['value']<=body['collectionDeadlineNs']/1e9):
            raise CoverageError('ML-RUNTIME-COLLECTION-EVENT')
        if read('manifest.json',1<<20)!=raw_manifest:
            raise CoverageError('ML-RUNTIME-MANIFEST-CHANGED')
        complete=body['collectionComplete']
    except Exception as exc:
        code=str(exc)
        diagnostic=code if re.fullmatch(r'ML-[A-Z0-9-]{1,120}',code) else 'ML-RUNTIME-COLLECTION-UNVERIFIABLE'
        return RuntimeVerification(lifecycle,False,False,(diagnostic,))
    return RuntimeVerification(lifecycle,True,complete,())
