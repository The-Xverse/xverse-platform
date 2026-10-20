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
add(['ML-SR-004', 'ML-SR-024'],'coverage-producers-v4','coverage-producers-v4-verification.json',['src/xverse/maestro/coverage.py::bind_runtime_coverage', 'src/xverse/maestro/coverage.py::decode_runtime_coverage', 'src/xverse/maestro/coverage.py::runtime_coverage_input', 'src/xverse/maestro/persistence.py::encode_configuration', 'src/xverse/maestro/persistence.py::PersistenceClient._holder', 'src/xverse/maestro/persistence.py::PersistenceClient.coverage_digest', 'src/xverse/maestro/persistence_worker.py::_load', 'src/xverse/maestro/bootstrap.py::BootstrapSession.persistence', 'src/xverse/maestro/providers.py::ProcessReadiness.__init__'],['tests/thesis_lite/maestro/test_coverage_producers.py::test_bad_sealed_coverage_rejects_before_journal_writer_or_workload', 'tests/thesis_lite/maestro/test_coverage_producers.py::test_worker_independently_rejects_coverage_before_creating_any_sink', 'tests/thesis_lite/maestro/test_coverage_producers.py::test_original_runtime_admission_pin_rejects_replaced_object_or_bytes_before_rpc', 'tests/thesis_lite/maestro/test_coverage_producers.py::test_reserved_run_identity_and_root_event_capacity_reject_purely', 'tests/thesis_lite/maestro/test_coverage_producers.py::test_actual_policy_mismatch_cannot_release_workloads'])
add(['ML-SR-016', 'ML-SR-017', 'ML-SR-019'],'coverage-producers-v4','coverage-producers-v4-verification.json',['src/xverse/maestro/evidence.py::record_validation', 'src/xverse/maestro/lifecycle_evidence.py::_same_json', 'src/xverse/maestro/lifecycle_evidence.py::OutcomeJournal._mirrors', 'src/xverse/maestro/persistence.py::PersistenceClient.__init__'],['tests/thesis_lite/maestro/test_coverage_producers.py::test_real_validation_flush_precedes_stage_and_reader_resolves_original_correlations', 'tests/thesis_lite/maestro/test_coverage_producers.py::test_actual_validation_init_ack_failure_closes_starts_and_retains_original_cleanup', 'tests/thesis_lite/maestro/test_coverage_producers.py::test_validation_caller_field_mutation_is_not_hidden_by_boolean_integer_alias', 'tests/thesis_lite/maestro/test_coverage_producers.py::test_typed_mirror_comparison_preserves_canonical_json_distinctions'])
add(['ML-SR-006', 'ML-SR-012', 'ML-SR-013', 'ML-SR-015', 'ML-SR-016', 'ML-SR-017'],'coverage-producers-v4','coverage-producers-v4-verification.json',['src/xverse/maestro/run_broker.py::RunUnitIssuer.stop_owned', 'src/xverse/maestro/run_broker.py::RunUnitIssuer._identity', 'src/xverse/maestro/evidence.py::broker_projection', 'src/xverse/maestro/coverage.py::_Assessment.teardown_reference', 'src/xverse/maestro/coverage.py::_Assessment.health_window'],['tests/thesis_lite/maestro/test_coverage_producers.py::test_real_stop_bracket_repeat_is_identical_and_projection_adds_no_rpc', 'tests/thesis_lite/maestro/test_coverage_producers.py::test_unacknowledged_stop_exports_open_original_bracket_without_normal_wait'])
add(['ML-SR-017', 'ML-SR-018', 'ML-SR-023'],'coverage-producers-v4','coverage-producers-v4-verification.json',['src/xverse/maestro/coverage.py::assess_preclosure', 'src/xverse/maestro/coverage.py::_Assessment.assess'],['tests/thesis_lite/maestro/test_coverage_producers.py::test_actual_shared_schedule_preserves_single_original_validation_and_distinct_tick_records'])
add(['ML-SR-016','ML-SR-017','ML-SR-018'],'coverage-producers-v4','coverage-producers-v4-verification.json',['src/xverse/maestro/coverage.py::_Assessment.teardown_reference'],['tests/thesis_lite/maestro/test_coverage.py::test_original_teardown_proof_references_bind_paired_m3_and_exact_context','tests/thesis_lite/maestro/test_coverage.py::test_other_run_validation_records_do_not_replace_or_duplicate_original_root'])
result=dict(schema_version=1,revision='ML3-AFFA17-2026-10-19-coverage-runtime-producers-partial',
    scope='additive component trace; full integrated increment17 trace remains required',
    parent_trace=dict(path=str(parent_path),sha256=sha(parent_path)),requirements=list(rows.values()),
    source_parent_register=parent['source_parent_register'],reverse_endpoint_requirements=reverse,
    source_parent_semantics_validated=False,software_requirements_retained=24,source_parents_retained=18,
    scenario_pairs_retained=30,endpoint_obligations_retained=90,full_runtime_cases_retained=9,
    all_seven_phase3_tasks_complete=False,full_candidate_review_complete=False,
    full_M1_complete=False,U7_U8_complete=False,stable_increment17=False,
    accepted=False,merged=False,canonical_note_edited=False,factory_run_created=False)
(OUT/'coverage-runtime-producers-partial-traceability.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(requirements=len(rows),source_parents=18,exact_snapshot_endpoints=len(reverse),full_closure=False)))
