"""Additive exact-snapshot trace; never closes full requirements or source parents."""
from pathlib import Path
import ast,hashlib,json

OUT=Path(__file__).resolve().parent;CANDIDATE=OUT.parents[4]
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parent_path=CANDIDATE/'docs/engineering/maestro-lite/evidence/recovery16/traceability.json'
parent=read(parent_path);assert len(parent['requirements'])==24
assert len(parent['source_parent_register']['requirements'])==18
rows={r['id']:dict(id=r['id'],feature_parents=r['feature_parents'],
    inherited_status=r['status'],full_requirement_closure=False,component_deltas=[]) for r in parent['requirements']}
reverse={}
def add(ids,manifest,proof,code,tests):
    run=read(OUT/(manifest+'-running.json'));root=Path(run['frozen_source_root'])
    frozen=read(OUT/(manifest+'-frozen-inputs.json'))
    def endpoint(text):
        path,name=text.split('::');p=root/path
        assert sha(p)==frozen[path]
        tree=ast.parse(p.read_text());nodes=tree.body
        for part in name.split('.'):
            node=next(n for n in nodes if isinstance(n,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==part)
            nodes=node.body
        reverse.setdefault(text,[]).extend(i for i in ids if i not in reverse.get(text,[]))
        return dict(endpoint=text,file_sha256=sha(p),frozen_manifest=manifest+'-frozen-inputs.json')
    item=dict(maturity='partial_component_evidence_only',code=[endpoint(n) for n in code],
        tests=[endpoint(n) for n in tests],verification=dict(path=proof,sha256=sha(OUT/proof)),
        all_original_requirement_clauses_verified=False)
    for i in ids:rows[i]['component_deltas'].append(item)
add(['ML-SR-004', 'ML-SR-024'],'public-blob-v2','public-blob-v2-verification.json',['src/xverse/maestro/public_blobs.py::admit_broker_artifact', 'src/xverse/maestro/public_blobs.py::decode_broker_artifact', 'src/xverse/maestro/persistence.py::encode_configuration', 'src/xverse/maestro/persistence_worker.py::_load'],['tests/thesis_lite/maestro/test_public_blobs.py::test_bad_sealed_broker_artifact_rejects_before_original_writer', 'tests/thesis_lite/maestro/test_public_blobs.py::test_original_replacement_conflict_and_cancelled_publication_preserve_no_start'])
add(['ML-SR-016', 'ML-SR-017', 'ML-SR-020'],'public-blob-v2','public-blob-v2-verification.json',['src/xverse/maestro/persistence.py::_receive_packet', 'src/xverse/maestro/persistence.py::_receive', 'src/xverse/maestro/persistence.py::_send_public_blob', 'src/xverse/maestro/public_blobs.py::sealed_public_blob', 'src/xverse/maestro/public_blobs.py::read_public_blob', 'src/xverse/maestro/public_blobs.py::decode_broker_data'],['tests/thesis_lite/maestro/test_public_blobs.py::test_real_sealed_transfer_above_packet_bound_preserves_all_bytes_and_closes_right', 'tests/thesis_lite/maestro/test_public_blobs.py::test_actual_bad_transport_disposes_every_delivered_right', 'tests/thesis_lite/maestro/test_public_blobs.py::test_full_synthetic_admitted_inventory_above_packet_transfers_without_row_loss', 'tests/thesis_lite/maestro/test_public_blobs.py::test_closed_broker_validation_rejects_bad_inventory_and_identity'])
add(['ML-SR-019', 'ML-SR-021', 'ML-SR-022'],'public-blob-v2','public-blob-v2-verification.json',['src/xverse/maestro/public_blobs.py::write_public_bytes', 'src/xverse/maestro/public_blobs.py::publish_broker', 'src/xverse/maestro/public_blobs.py::validate_broker_receipt', 'src/xverse/maestro/persistence.py::PersistenceClient.publish_broker_artifact'],['tests/thesis_lite/maestro/test_public_blobs.py::test_original_worker_publishes_actual_broker_bytes_indexes_and_caches_without_new_intents', 'tests/thesis_lite/maestro/test_public_blobs.py::test_failed_actual_publication_never_certifies_receipt_or_rewrites_existing_bytes', 'tests/thesis_lite/maestro/test_public_blobs.py::test_confined_public_artifact_nested_bytes_and_actual_closed_reader'])
add(['ML-SR-005', 'ML-SR-006', 'ML-SR-019', 'ML-SR-023'],'public-blob-v2','public-blob-v2-verification.json',['src/xverse/maestro/persistence_worker.py::serve'],['tests/thesis_lite/maestro/test_public_blobs.py::test_actual_v5_revalidation_failure_still_prevents_native_release'])
add(['ML-SR-005','ML-SR-019','ML-SR-023'],'public-blob-v2','public-blob-v2-verification.json',['tests/thesis_lite/maestro/persistence_fixture.py::receiving','tests/thesis_lite/maestro/persistence_fixture.py::injected'],['tests/thesis_lite/maestro/test_persistence.py::test_actual_revalidation_failure_prevents_native_release'])
result=dict(schema_version=1,revision='ML3-AFFA17-2026-10-19-original-public-blob-partial',
    scope='additive component trace; full integrated increment17 trace remains required',
    parent_trace=dict(path=str(parent_path),sha256=sha(parent_path)),requirements=list(rows.values()),
    source_parent_register=parent['source_parent_register'],reverse_endpoint_requirements=reverse,
    source_parent_semantics_validated=False,software_requirements_retained=24,source_parents_retained=18,
    scenario_pairs_retained=30,endpoint_obligations_retained=90,full_runtime_cases_retained=9,
    all_seven_phase3_tasks_complete=False,full_candidate_review_complete=False,
    full_M1_complete=False,U7_U8_complete=False,stable_increment17=False,
    accepted=False,merged=False,canonical_note_edited=False,factory_run_created=False)
(OUT/'original-public-blob-partial-traceability.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(requirements=len(rows),source_parents=18,exact_snapshot_endpoints=len(reverse),full_closure=False)))
