"""Actual original-worker inputs expose remaining runtime gaps; no fabricated closure."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import time

from xverse.maestro.coverage import admit_coverage,assess_preclosure
from xverse.maestro.teardown import ReverseTeardown
from .test_retained_inputs import prepare,read_export
from .test_run_broker import broker_stack as broker_stack,stage_all
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries,deadline


def test_actual_original_public_inputs_do_not_fill_missing_runtime_producers(request,monkeypatch):
    saved=prepare(monkeypatch)
    stack=request.getfixturevalue('broker_stack')
    broker,facade,client,work=stack
    bindings=json.loads(saved['config'].private_bytes)['bindings']
    admission=admit_coverage(client.prepared,client._result_input,client._resources,run_id=client.run_id,host_session=client.session,
        contexts=[(b['unit_id'],b['generation'],b['execution_id']) for b in bindings],
        health_policies={u.unit_id:(facade._policies[u.unit_id].cadence_seconds,facade._policies[u.unit_id].freshness_seconds) for u in client.prepared.units},
        active_start=time.monotonic(),active_end=client.generation_ns/1e9-2)
    end=stage_all(stack)
    for unit in client.prepared.resource_order:
        issuer=broker.issuer(unit)
        assert facade.start(unit,issuer.recipe.descriptor,broker.connection,end).ready
    cleanup=ReverseTeardown(facade,per_unit_seconds=.8).run(deadline(3),reason='coverage-component')
    assert cleanup.unit_cleanup_complete and cleanup.normal_records_complete
    projection=broker.public_projection(deadline(.5)).public_data()
    receipt=client.export_public_inputs(saved['declaration'],deadline(2))
    retained=read_export(stack,receipt)
    data=(work.parent/'argus'/receipt.declaration.relative_path).read_bytes()
    result=assess_preclosure(admission,expected_admission_digest=admission.digest,annotations=retained['annotations'],
        public_m3=retained['publicM3'],broker=projection,artifact_entries=[receipt.public_entry()],
        artifact_bytes={receipt.declaration.relative_path:data})
    report=result.report()
    assert report['overallStatus']=='incomplete' and report['normalRecordStatus']!='complete'
    for suffix in ('run-validation','collect','run-terminal'):
        assert next(r for r in report['rows'] if r['obligationId']=='ob.'+suffix)['status']=='missing'
    assert all(r['stopRequestedAt'] is not None and r['stopAcknowledgedAt'] is not None for r in projection['generations'])
    target=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if target:
        (Path(target)/('coverage-original-public-'+str(os.getpid())+'.json')).write_text(json.dumps(dict(
            admission=json.loads(admission.public_bytes),admission_digest=admission.digest,report=report,
            retained=retained,broker=projection,cleanup=asdict(cleanup),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            full_M1_complete=False,scientific_result=False)))
