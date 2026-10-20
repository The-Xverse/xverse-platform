"""Fresh-process U7 verification with runtime imports forbidden; synthetic facts."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from .test_evidence_scope import ClockFixture


CHILD = r'''
import importlib.abc,json,sys
from pathlib import Path
forbidden = {'persistence','owner','providers','bootstrap','run_broker','fence','prbc',
             'supervisor','controller','collection_runtime','public_blobs','terminal_runtime','child'}
class DenyRuntime(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.startswith('xverse.maestro.') and fullname.split('.')[2] in forbidden:
            raise ImportError('Offline verifier imported runtime component: '+fullname)
sys.meta_path.insert(0,DenyRuntime())
from xverse.maestro.coverage import CoverageAdmission,canonical
from xverse.maestro.collection_plan import decode_collection
from xverse.maestro.runtime_verification import verify_runtime_closed
body=json.loads(Path(sys.argv[1]).read_bytes())
ad=CoverageAdmission(canonical(body['admission']))
plan=decode_collection(body['collection'],ad,body['pins']['expected_admission_digest'])
result=verify_runtime_closed(ad,plan,Path(body['root']),**body['pins'])
assert result.complete, result.diagnostics
loaded=sorted(n for n in sys.modules if n.startswith('xverse.maestro.'))
assert not any(n.split('.')[2] in forbidden for n in loaded)
print(json.dumps(dict(complete=result.complete,modules=loaded,denied_modules=sorted(forbidden))))
'''


@pytest.mark.parametrize('late_teardown',[False,True])
def test_closed_verification_in_fresh_process_has_no_runtime_imports(tmp_path,late_teardown):
    fixture=ClockFixture(tmp_path,late_teardown=late_teardown)
    fixture.close()
    assert fixture.verify().complete
    before={str(p.relative_to(fixture.root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in fixture.root.rglob('*') if p.is_file()}
    inputs=tmp_path/'offline-inputs.json'
    inputs.write_text(json.dumps(dict(admission=fixture.ad,collection=fixture.collection_plan.configuration(),
                                      root=str(fixture.root),pins=fixture.pins)))
    command=[sys.executable,*(['-I'] if sys.flags.isolated else []),'-c',CHILD,str(inputs)]
    result=subprocess.run(command,capture_output=True,text=True,timeout=15)
    after={str(p.relative_to(fixture.root)):hashlib.sha256(p.read_bytes()).hexdigest()
           for p in fixture.root.rglob('*') if p.is_file()}
    assert before==after
    out=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if out:
        target=Path(out);target.mkdir(parents=True,exist_ok=True)
        (target/('offline-boundary-'+str(late_teardown)+'.json')).write_text(json.dumps(dict(
            late_teardown=late_teardown,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr,
            command=command,original_inputs=str(inputs),input_sha256=hashlib.sha256(inputs.read_bytes()).hexdigest(),
            evidence_sha256=before,unchanged_evidence=before==after,
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            synthetic_facts=True,scientific_result=False),indent=2)+'\n')
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)['complete']


@pytest.mark.parametrize('decoder',['broker','context'])
def test_runtime_decoder_keeps_original_exception_identity(tmp_path,decoder):
    from xverse.maestro import collection_evidence, collection_runtime, public_blobs
    from xverse.maestro.coverage import canonical
    from xverse.maestro.persistence import PersistenceError
    fixture=ClockFixture(tmp_path)
    try:
        body=json.loads(fixture.runtime_bytes['collection.json'])['context']
        body['broker']['runId']='substituted-run'
        if decoder=='broker':
            arguments=(canonical(body['broker']),fixture.admission,fixture.admission.digest)
            pure=collection_evidence.decode_broker_data
            runtime=public_blobs.decode_broker_data
        else:
            arguments=(canonical(body),fixture.admission,fixture.admission.digest,
                       fixture.collection_plan,fixture.generation_ns,4.5)
            pure=collection_evidence.decode_context
            runtime=collection_runtime.decode_context
        with pytest.raises(collection_evidence.BrokerDataError,match='ML-EVIDENCE-BLOB-BROKER'):
            pure(*arguments)
        with pytest.raises(PersistenceError,match='ML-EVIDENCE-BLOB-BROKER') as error:
            runtime(*arguments)
        assert type(error.value) is PersistenceError
    finally:
        fixture.writer.abort(reason='Synthetic decoder exception compatibility control')
