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
add(['ML-SR-016', 'ML-SR-017'],'coverage-v5','coverage-component-verification.json',['src/xverse/maestro/coverage.py::admit_coverage', 'src/xverse/maestro/coverage.py::CoverageAdmission.data', 'src/xverse/maestro/coverage.py::_templates', 'src/xverse/maestro/coverage.py::assess_preclosure', 'src/xverse/maestro/coverage.py::_Assessment.assess'],['tests/thesis_lite/maestro/test_coverage.py::test_original_universe_and_provisional_nominal_cannot_promote_execution', 'tests/thesis_lite/maestro/test_coverage.py::test_deletions_never_shrink_original_template_universe', 'tests/thesis_lite/maestro/test_coverage.py::test_original_admission_digest_and_template_deletion_are_checked', 'tests/thesis_lite/maestro/test_coverage.py::test_inconsistent_original_identities_never_complete', 'tests/thesis_lite/maestro/test_coverage.py::test_missing_original_interval_bounds_leave_health_unverifiable', 'tests/thesis_lite/maestro/test_coverage.py::test_stale_same_generation_prerequisite_is_not_fresh_evidence', 'tests/thesis_lite/maestro/test_coverage.py::test_future_intent_without_acknowledged_issuer_never_becomes_inactive', 'tests/thesis_lite/maestro/test_coverage.py::test_missing_real_run_validation_is_not_reconstructed_from_correlation', 'tests/thesis_lite/maestro/test_coverage.py::test_completed_never_issued_unit_is_not_a_false_inactive_start'])
add(['ML-SR-018', 'ML-SR-020'],'coverage-v5','coverage-component-verification.json',['src/xverse/maestro/coverage.py::verify_closed'],['tests/thesis_lite/maestro/test_coverage.py::test_actual_closed_writer_independent_coverage_separates_execution_outcome', 'tests/thesis_lite/maestro/test_coverage.py::test_missing_normal_outcome_remains_missing_with_complete_emergency_facts', 'tests/thesis_lite/maestro/test_coverage.py::test_cleanup_only_c1_facts_are_independent_of_missing_ordinary_wait', 'tests/thesis_lite/maestro/test_coverage.py::test_closed_reader_rejects_report_loss_tampering_or_failed_closure', 'tests/thesis_lite/maestro/test_coverage.py::test_open_reader_is_not_artifact_index_or_closed_coverage_proof'])
add(['ML-SR-021', 'ML-SR-022'],'coverage-v5','coverage-component-verification.json',['src/xverse/maestro/coverage.py::_Assessment.artifact', 'src/xverse/maestro/coverage.py::_Assessment.input_digests'],['tests/thesis_lite/maestro/test_coverage.py::test_actual_indexed_output_byte_mutation_never_keeps_complete_coverage', 'tests/thesis_lite/maestro/test_coverage.py::test_report_artifact_loss_keeps_normal_record_status_separate', 'tests/thesis_lite/maestro/test_coverage.py::test_optional_missing_output_does_not_create_false_offline_corruption', 'tests/thesis_lite/maestro/test_coverage.py::test_assessor_uses_no_ambient_clock_io_or_provider_callback', 'tests/thesis_lite/maestro/test_coverage.py::test_required_artifact_missing_is_distinct_from_normal_record_coverage'])
add(['ML-SR-023', 'ML-SR-024'],'coverage-v5','coverage-component-verification.json',['src/xverse/maestro/coverage.py::_report_capacity', 'src/xverse/maestro/coverage.py::_validate_admission'],['tests/thesis_lite/maestro/test_coverage.py::test_unbounded_inputs_or_bad_clock_cadence_reject_before_assessment', 'tests/thesis_lite/maestro/test_coverage.py::test_bool_generation_and_capacity_do_not_alias_original_integers'])
add(['ML-SR-016','ML-SR-017','ML-SR-018'],'coverage-v5','coverage-component-verification.json',['src/xverse/maestro/coverage.py::_Assessment.health_window'],['tests/thesis_lite/maestro/test_coverage_native.py::test_actual_original_public_inputs_do_not_fill_missing_runtime_producers'])
result=dict(schema_version=1,revision='ML3-AFFA17-2026-10-19-coverage-assessment-partial',
    scope='additive component trace; full integrated increment17 trace remains required',
    parent_trace=dict(path=str(parent_path),sha256=sha(parent_path)),requirements=list(rows.values()),
    source_parent_register=parent['source_parent_register'],reverse_endpoint_requirements=reverse,
    source_parent_semantics_validated=False,software_requirements_retained=24,source_parents_retained=18,
    scenario_pairs_retained=30,endpoint_obligations_retained=90,full_runtime_cases_retained=9,
    all_seven_phase3_tasks_complete=False,full_candidate_review_complete=False,
    full_M1_complete=False,U7_U8_complete=False,stable_increment17=False,
    accepted=False,merged=False,canonical_note_edited=False,factory_run_created=False)
(OUT/'coverage-assessment-partial-traceability.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(requirements=len(rows),source_parents=18,exact_snapshot_endpoints=len(reverse),full_closure=False)))
