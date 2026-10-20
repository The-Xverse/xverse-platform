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
add(['ML-SR-021','ML-SR-022'],'runtime-collection-index-20261019a','runtime-collection-index-20261019a-verification.json',
 ['src/xverse/maestro/artifacts.py::CollectionSource','src/xverse/maestro/artifacts.py::CollectionAdmission.collect_next','src/xverse/maestro/artifacts.py::CollectionAdmission.index_item','src/xverse/maestro/artifacts.py::CollectionAdmission._scope'],
 ['tests/thesis_lite/maestro/test_collection_incremental.py::test_early_pin_actual_later_bytes_and_single_binding','tests/thesis_lite/maestro/test_collection_incremental.py::test_shared_total_debit_survives_steps_and_failed_copy','tests/thesis_lite/maestro/test_collection_incremental.py::test_one_aggregate_end_and_expired_item_outcomes_are_not_retried','tests/thesis_lite/maestro/test_collection_incremental.py::test_item_and_whole_index_share_original_ack_and_closed_bytes','tests/thesis_lite/maestro/test_collection_incremental.py::test_uncertain_index_is_single_attempt_and_never_republished','tests/thesis_lite/maestro/test_collection_incremental.py::test_changed_original_index_receipt_cannot_rewrite_acknowledged_cache'])
add(['ML-SR-021','ML-SR-024'],'runtime-collection-admission-20261019a/collection-v6','runtime-collection-admission-20261019a/collection-v6-verification.json',
 ['src/xverse/maestro/collection_plan.py::admit_collection','src/xverse/maestro/collection_plan.py::decode_collection','src/xverse/maestro/collection_plan.py::bind_collection','src/xverse/maestro/persistence.py::encode_configuration','src/xverse/maestro/persistence.py::PersistenceClient._holder','src/xverse/maestro/persistence_worker.py::_load','src/xverse/maestro/persistence_worker.py::serve'],
 ['tests/thesis_lite/maestro/test_collection_plan.py::test_original_full_output_universe_includes_inactive_future_context','tests/thesis_lite/maestro/test_collection_plan.py::test_dropped_or_changed_output_is_rejected_before_filesystem','tests/thesis_lite/maestro/test_collection_plan.py::test_sealed_collection_input_is_independently_rederived','tests/thesis_lite/maestro/test_collection_plan.py::test_original_worker_rejects_wrong_source_before_journal_or_writer','tests/thesis_lite/maestro/test_collection_plan.py::test_actual_worker_pinned_source_substitution_prevents_first_claim','tests/thesis_lite/maestro/test_collection_plan.py::test_original_collection_metadata_pin_rejects_changed_parent_without_rpc'])
add(['ML-SR-023'],'runtime-collection-admission-20261019a/collection-v6','runtime-collection-admission-20261019a/collection-v6-verification.json',
 ['src/xverse/maestro/persistence.py::PersistenceClient.__init__'],
 ['tests/thesis_lite/maestro/test_dispatch_observe.py::test_scheduled_observe_queries_only_its_declared_original_unit','tests/thesis_lite/maestro/test_persistence.py::test_actual_revalidation_failure_prevents_native_release'])

result=dict(schema_version=1,revision='ML3-AFFA17-2026-10-19-original-runtime-collection-partial',
    scope='additive component trace; full integrated increment17 trace remains required',
    parent_trace=dict(path=str(parent_path),sha256=sha(parent_path)),requirements=list(rows.values()),
    source_parent_register=parent['source_parent_register'],reverse_endpoint_requirements=reverse,
    source_parent_semantics_validated=False,software_requirements_retained=24,source_parents_retained=18,
    scenario_pairs_retained=30,endpoint_obligations_retained=90,full_runtime_cases_retained=9,
    all_seven_phase3_tasks_complete=False,full_candidate_review_complete=False,
    full_M1_complete=False,U7_U8_complete=False,stable_increment17=False,
    accepted=False,merged=False,canonical_note_edited=False,factory_run_created=False)
(OUT/'original-runtime-collection-partial-traceability.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(requirements=len(rows),source_parents=18,exact_snapshot_endpoints=len(reverse),full_closure=False)))
