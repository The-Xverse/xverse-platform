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
add(['ML-SR-005','ML-SR-006','ML-SR-016','ML-SR-019'],'issued-v1','issuance-component-verification.json',
    ['src/xverse/maestro/issuance_evidence.py::record_issued','src/xverse/maestro/issuance_evidence.py::validate_issued',
     'src/xverse/maestro/persistence.py::PersistenceClient.record_issued','src/xverse/maestro/run_broker.py::RunUnitIssuer.stage'],
    ['tests/thesis_lite/maestro/test_issuance.py::test_actual_frozen_issuance_precedes_start_and_real_ready_causation',
     'tests/thesis_lite/maestro/test_issuance.py::test_missing_issued_mirror_prevents_release_and_keeps_original_cleanup',
     'tests/thesis_lite/maestro/test_issuance.py::test_actual_new_generation_has_distinct_durable_issuance_and_retained_old_source',
     'tests/thesis_lite/maestro/test_issuance.py::test_malformed_actual_issued_ack_never_publishes_a_receipt'])
add(['ML-SR-021','ML-SR-022'],'collection-v6','collection-current-verification.json',
    ['src/xverse/maestro/artifacts.py::CollectionAdmission.collect','src/xverse/maestro/artifacts.py::CollectionAdmission._read',
     'src/xverse/maestro/artifacts.py::CollectionAdmission._copy','src/xverse/maestro/artifacts.py::CollectionAdmission.index'],
    ['tests/thesis_lite/maestro/test_collection.py::test_nested_actual_bytes_hash_and_repeat_without_new_io',
     'tests/thesis_lite/maestro/test_collection.py::test_actual_public_index_and_closed_reader_bytes',
     'tests/thesis_lite/maestro/test_collection.py::test_actual_mid_read_or_copy_substitution_never_yields_stable_hash',
     'tests/thesis_lite/maestro/test_collection.py::test_original_total_byte_budget_cannot_be_replenished_by_extra_declarations',
     'tests/thesis_lite/maestro/test_collection.py::test_missing_lookup_race_is_error_for_optional_file',
     'tests/thesis_lite/maestro/test_collection.py::test_destination_disappearing_during_copy_is_error_for_optional_file',
     'tests/thesis_lite/maestro/test_collection.py::test_collect_index_and_close_conflicts_preserve_one_original_result',
     'tests/thesis_lite/maestro/test_collection.py::test_unbounded_declaration_iterable_rejects_without_calling_it'])
result=dict(schema_version=1,revision='ML3-AFFA17-2026-10-19-issuance-collection-partial',
    scope='additive component trace; full integrated increment17 trace remains required',
    parent_trace=dict(path=str(parent_path),sha256=sha(parent_path)),requirements=list(rows.values()),
    source_parent_register=parent['source_parent_register'],reverse_endpoint_requirements=reverse,
    source_parent_semantics_validated=False,software_requirements_retained=24,source_parents_retained=18,
    scenario_pairs_retained=30,endpoint_obligations_retained=90,full_runtime_cases_retained=9,
    all_seven_phase3_tasks_complete=False,full_candidate_review_complete=False,
    full_M1_complete=False,U7_U8_complete=False,stable_increment17=False,
    accepted=False,merged=False,canonical_note_edited=False,factory_run_created=False)
(OUT/'issuance-collection-partial-traceability.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(requirements=len(rows),source_parents=18,exact_snapshot_endpoints=len(reverse),full_closure=False)))
