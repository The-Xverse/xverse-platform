# Argus Lite Phase 2 — validation record

| Field | Value |
| --- | --- |
| Feature | ARGUS2 (Argus Lite Phase 2 — bounded run evidence persistence, X-COM observation projection import and read-only reconstruction) |
| Stage / role | validation (repository-owned Spec Kit work-product workflow, ADR-0020) |
| Revision | 5 (bound to the revision-6 repaired implementation candidate; supersedes the revision-4 record bound to the revision-5 candidate) |
| Supersedes | Revision 4 (`docs/engineering/argus-lite/validation.md` sha256 `7f04be4f790e1d832090ae24b8791bc5cf66c48d3336dd45e75fc6ef636144da`, `engineering/stage-results/argus2-validation.json` sha256 `5dcfd01877293c2a5a58f8d436b77988da37a00897e99f59e6546e8ba39fcfd7`) and, transitively, revisions 3 (`22439643…`/`ae03ef96…`) and 2 (`ac66ab6c…`/`0fd824a0…`). Those records were bound to older candidates (219/222/229 owned cases) and are stale for this candidate; their bytes are superseded by this revision and their identities are preserved here as lineage. |
| Date | 2026-10-02 |
| Admitted platform baseline | `c1fd213cd00259b74f8308d8ca58157ea985aaa0` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 (`ARGUS2-SR-001` … `ARGUS2-SR-012`, sha256 `1b6d30ee…`), immutable |
| Design authority | [`architecture.md`](architecture.md) rev 1 rework (`f2a44c73…`), [`detailed-design.md`](detailed-design.md) rev 1 rework (`4f9537d6…`) |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 rework (`ea6fd473…`) |
| Verification authority | [`verification-plan.md`](verification-plan.md) rev 2 (`5e36301a…`, §5-8 integration/installed-wheel, §9 trace), frozen measure `engineering/verification/measures/ARGUS2-VALIDATION.json` (`360213e4…`) |
| Implementation / integration authority | [`implementation.md`](implementation.md) (`873b738f…`), [`integration.md`](integration.md) (`e59ab4b3…`), bound by `engineering/stage-results/argus2-implementation.json` (`b1c08083…`) and `…-integration.json` (`4b02df9d…`) |
| Classification | Public-safe engineering work-product |
| Maturity | **Intended-use validation passes in the worker.** The revision-6 repaired candidate satisfies the frozen `ARGUS2-VALIDATION` scenario set (30 identifiers over eight scenarios) through the real public API, the read-only CLI and a real accepted compiler plan, including the five adversarial `ARGUS2-VS-08` cases that bind `AR-F01`–`AR-F05`, the revision-4/revision-5 residual repairs (`AR-F03` non-finite manifest rejection, `AR-F04` newline-inclusive exact manifest byte bound, `AR-RVW-001` bounded deep-nesting rejection) and the revision-6 residual repair of both `AR-F03` enclosing-depth failures (event export after document wrapping and obligation admission during manifest preview). This is candidate-local, worker-run evidence only; it is **not** trusted target-repository verification and no compatibility, parity, acceptance or delivery claim follows. |

## 1. Purpose and boundary

This stage exercises the eight frozen intended-use validation scenarios `ARGUS2-VS-01` … `ARGUS2-VS-08`
through the single frozen measure `ARGUS2-VALIDATION` (30 identifiers), records the exact discovered
identifiers, confirms that the mutable current trace file's code-endpoint revisions are finalized and
non-stale for the revision-6 candidate, and re-verifies preservation of every inherited artifact.

It writes exactly one owned artifact, `docs/engineering/argus-lite/validation.md`, and the stage record
`engineering/stage-results/argus2-validation.json`. It changes **no** source, test, fixture, schema,
packaging or historical record, and it does **not** modify `engineering/trace/links.json` (see §7).

The earlier worker reported "nine passing integration cases" but returned no routing JSON, so that
observation was **not** treated as accepted validation: every check in §3–§6 was re-executed against the
current revision-6 candidate and its results recorded here.

No assertion was weakened, skipped or deleted: the exercised identifier set is exactly the set frozen in
`engineering/verification/measures/ARGUS2-VALIDATION.json` (30/30), and every scenario is executed
verbatim against the candidate.

## 2. Frozen ARGUS2-VALIDATION identifier set

`engineering/verification/measures/ARGUS2-VALIDATION.json` (kind `validation`, revision 1,
`sha256=360213e4be428caab28bfb1eeebaffb51825c1e8606992588fb44912b49ab97b`) freezes 30 identifiers,
which are the union of the eight scenario `test_ids`. Each scenario's `test_ids` is a subset of the
measure and the union equals the measure exactly (re-checked in this stage; 3+3+3+5+4+3+4+5 = 30).

| Scenario | Intended use | Cases |
| --- | --- | --- |
| `ARGUS2-VS-01` | Caller opens one run from a real compiled plan and captures a bounded causal evidence stream | 3 |
| `ARGUS2-VS-02` | Analyst imports an owned X-COM observation projection and preserves visibility, loss and interval facts | 3 |
| `ARGUS2-VS-03` | Analyst reconstructs evidence read-only with deterministic selection and declared metric-input links | 3 |
| `ARGUS2-VS-04` | Integrator receives stable categorized diagnostics for every declared rejection class | 5 |
| `ARGUS2-VS-05` | Operator recovers incomplete or damaged evidence without mutating the originals | 4 |
| `ARGUS2-VS-06` | Maintainer consumes the installed wheel and the preserved existing contracts | 3 |
| `ARGUS2-VS-07` | Metamorphic determinism and honest completeness across equivalent inputs | 4 |
| `ARGUS2-VS-08` | Adversarial repair validation: confined bounded I/O, assessed corruption, strict schemas, publication byte bound, admission snapshot isolation and bounded deep nesting, including the enclosing-depth export/admission boundaries | 5 |

Every one of the twelve accepted software requirements `ARGUS2-SR-001` … `ARGUS2-SR-012` is validated
by at least one scenario through the `validates` links (12 of 12 re-checked against the trace: 37
`validates` links with `target` in `ARGUS2-SR-001` … `ARGUS2-SR-012`, distinct targets = 12). The five
additive `ARGUS2-VS-08` cases bind `AR-F01`–`AR-F05`, realized by the frozen adversarial cases
`ARGUS2-ADV-01` … `ARGUS2-ADV-07` and the 21 additive repair unit cases in
`tests/thesis_lite/argus/test_argus2_repair_unit.py`.

## 3. Executed validation — actual result

Command, verbatim as declared by the frozen measure:

```
python3 -m pytest -vv tests/thesis_lite/argus/test_argus2_validation.py
```

Result: **exit 0 — `30 passed in 8.73s`.** The 30 nodes discovered by `-vv` are exactly the 30
frozen identifiers (no missing, no extra, no duplicates, no failures), verified programmatically against
the measure record (30 discovered, 30 unique, 0 missing, 0 extra, all `PASSED`):

| Scenario | Discovered identifiers (all PASSED) |
| --- | --- |
| `ARGUS2-VS-01` | `test_caller_opens_run_from_real_compiled_plan_and_persists_events`, `test_evidence_stream_records_identity_clocks_and_causation`, `test_manifest_published_open_then_closed_with_verified_artifacts` |
| `ARGUS2-VS-02` | `test_owned_observation_projection_preserves_visibility_and_loss`, `test_metadata_only_redacted_and_truncated_payloads_remain_distinct`, `test_snapshot_interval_closure_required_for_completeness` |
| `ARGUS2-VS-03` | `test_reader_reconstructs_evidence_read_only_deterministically`, `test_metric_inputs_link_captured_selection_without_computation`, `test_replay_never_executes_components_or_oracle` |
| `ARGUS2-VS-04` | `test_digest_mutation_and_unsupported_versions_rejected_without_partial_state`, `test_duplicate_identity_and_nonfinite_values_rejected`, `test_missing_clock_domain_and_unit_rejected`, `test_exceeded_caller_bounds_rejected_with_stable_diagnostics`, `test_unsafe_paths_and_symlink_escapes_rejected` |
| `ARGUS2-VS-05` | `test_truncated_stream_and_interrupted_finalize_report_incomplete`, `test_known_loss_and_unmet_obligation_never_become_complete`, `test_missing_causal_and_interval_closure_remain_visible`, `test_recovery_reads_bounded_prefix_without_mutating_originals` |
| `ARGUS2-VS-06` | `test_installed_wheel_imports_argus_and_preserved_xdl_contracts`, `test_additive_unknown_field_and_unknown_major_behaviour_explicit`, `test_existing_xdl_cli_and_public_api_unchanged` |
| `ARGUS2-VS-07` | `test_repeated_reads_and_exports_are_byte_equal`, `test_retention_counters_do_not_substitute_for_interval_closure`, `test_ingestion_order_is_not_temporal_or_causal_order`, `test_canonical_serialization_independent_of_input_key_order` |
| `ARGUS2-VS-08` | `test_adversarial_reads_confined_and_bounded_before_io`, `test_adversarial_corrupt_evidence_assessed_incomplete_never_primary_complete`, `test_adversarial_strict_schema_and_identities_yield_only_stable_diagnostics`, `test_adversarial_manifest_byte_bound_enforced_at_every_publication`, `test_adversarial_admission_snapshots_and_views_immune_to_caller_mutation` |

Every identifier resolves to `tests/thesis_lite/argus/test_argus2_validation.py::<case>`
(`sha256=098f019de68f02b9175943a148476351d7a449458d76171e1e8fee6ea7c92c26`); the module identifier
contains no hyphen, so the trusted `test_id.replace('-', '_')` normalization is a no-op.

## 4. Terminal-review repair findings exercised (AR-F01 – AR-F05, AR-RVW-001)

The five `ARGUS2-VS-08` cases prove each external finding end to end through the public API and the CLI;
the 21 additive adversarial unit cases prove the residual repairs at the boundary:

| Finding | Required proof | Exercised by (all PASSED) |
| --- | --- | --- |
| `AR-F01` | Bounded reads before parsing; traversal/symlink/non-regular manifest and stream paths rejected before I/O; manifest/event/record/diagnostic bounds enforced without trusting limits echoed by damaged inputs | `test_adversarial_reads_confined_and_bounded_before_io` (traversal `ARGUS2-PATH-ESCAPE`, escaping symlink `ARGUS2-PATH-SYMLINK`, manifest `max_manifest_bytes`, per-line `max_event_bytes`, damaged-manifest limit echo combined by per-field minimum: `max_read_records=2` caps the read and emits `ARGUS2-BOUND-EXCEEDED`); `test_recovery_diagnostic_emission_stops_at_caller_bound` and `test_reader_damaged_stream_never_returns_more_diagnostics_than_bound` (diagnostic emission bound honoured, originals non-mutating) |
| `AR-F02` | Assessed incomplete/unverifiable status and reasons exposed on corruption/loss/truncation; recorded manifest facts preserved separately; corrupt evidence never exported as primary complete | `test_adversarial_corrupt_evidence_assessed_incomplete_never_primary_complete` (`recorded_evidence_status="complete"` with `assessed_evidence_status="incomplete"` + reasons; `export_json()["evidenceStatus"]=="incomplete"`; `verify` exits 1; manifest-shape corruption yields `ARGUS2-CORRUPT-MANIFEST-SHAPE` / `ARGUS2-REASON-CORRUPT-MANIFEST`) |
| `AR-F03` | Complete frozen nested schemas, required run/event/producer identity, per-run ID uniqueness, monotonic ingestion ordinals, run-ID consistency and finite values; malformed containers/versions/I/O yield bounded stable diagnostics and never an uncaught `TypeError`/`ValueError` | `test_adversarial_strict_schema_and_identities_yield_only_stable_diagnostics` (duplicate `ARGUS2-CORRUPT-DUPLICATE-EVENT`, ordinal `ARGUS2-CORRUPT-ORDINAL`, run-id `ARGUS2-CORRUPT-RUN-ID-MISMATCH`, missing identity `ARGUS2-INPUT-IDENTITY-MISSING`, non-finite `ARGUS2-INPUT-NONFINITE`, container `ARGUS2-INPUT-CLOCK-MISSING`; no reader/CLI exception); the residual non-finite cases `test_reader_rejects_nonfinite_manifest_values_before_assessment_or_export` and `test_reader_rejects_nonfinite_manifest_tokens_from_raw_text` (NaN/Infinity/-Infinity and overflowing literals such as `1e400` rejected anywhere in the parsed manifest with one stable `ARGUS2-INPUT-NONFINITE` diagnostic before the schema-version check, limits echo, assessment or export); malformed-container cases `test_reader_malformed_clock_domains_container_yields_stable_diagnostic`, `test_reader_malformed_metric_inputs_never_raise_on_export_or_cli`, `test_reader_malformed_event_containers_never_raise` |
| `AR-F03` (revision-6 enclosing depth) | An admitted event record whose nesting fits the standalone parse bound but exceeds the wrapped export document must yield a stable bounded diagnostic on both JSON and CLI export and never a primary complete status; an admitted obligation whose nesting fits the standalone parse bound but overflows manifest-preview serialization must yield a bounded `EvidenceError` before any run root or temp file is created | `test_event_json_export_last_accepted_and_first_rejected_depths` and `test_cli_export_first_rejected_event_depth_is_bounded` (reader accounts for `_EXPORT_WRAP_DEPTH=2`; the over-deep record is withheld with one `ARGUS2-BOUND-EXCEEDED` diagnostic, assessed `incomplete`, JSON and CLI export exit without raising and never report primary `complete`; the admitted record stays in `records()`); `test_obligation_admission_last_accepted_and_first_rejected_depths` (`api.open_run` and `writer._publish` convert the manifest-preview nesting overflow into a bounded `ARGUS2-INPUT-FIELD-INVALID` `EvidenceError` before any run root/temp file, preserving prior manifest bytes and claiming no closed/complete persistence) |
| `AR-F04` | Actual serialized byte bound enforced before every manifest publication including artifact/obligation/finalized growth; prior manifest preserved on bound or I/O failure; stable errors with no closed/complete claim | `test_adversarial_manifest_byte_bound_enforced_at_every_publication` (open, successful finalize, failed finalize and abort all measured through `_publish`; `max_manifest_bytes` failure raises `ARGUS2-BOUND-EXCEEDED`, `writer_state != "closed"`, prior `manifest.json` bytes unchanged); residual exact-bound case `test_manifest_publication_bound_includes_the_final_newline` (the bound covers `len(encoded)+1`, the manifest's single trailing newline, before any temp file or run root is created) |
| `AR-F05` | Caller-owned nested obligations and admitted mutable objects snapshotted; post-admission mutation cannot lower obligations or rewrite indexed hashes; returned views cannot mutate internal admission facts | `test_adversarial_admission_snapshots_and_views_immune_to_caller_mutation` (nested `detail.minimum` mutation ignored: obligation stays `3`, `evidence_status="incomplete"` with `ARGUS2-REASON-UNMET-OBLIGATION`; mutating returned records/manifest/metric-input views leaves `export_json()` byte-identical and re-read `eventId` unchanged); `test_admitted_annotation_is_an_independent_snapshot`, `test_append_nonfinite_or_nonjson_extensions_rejected_at_admission`, `test_append_nonfinite_clocks_rejected_without_writing` |
| `AR-RVW-001` | Small, deeply nested JSON must return stable bounded diagnostics instead of an uncaught `RecursionError` at manifest and event-line parsing, canonical serialization, `open_run` obligations and `append_event` extensions/observation | The seven additive cases `test_canonical_serialization_rejects_deep_nesting_with_value_error_not_recursion_error`, `test_json_nesting_scanner_ignores_brackets_inside_strings`, `test_reader_rejects_deeply_nested_manifest_without_recursion_error` (`ARGUS2-CORRUPT-MANIFEST-SHAPE`, assessed `incomplete`, `export` exits 0), `test_reader_rejects_deeply_nested_event_line_without_recursion_error` (`ARGUS2-CORRUPT-STREAM-TRUNCATED`), `test_open_run_rejects_deeply_nested_obligation_without_recursion_error` (`ARGUS2-INPUT-FIELD-INVALID`, no run root created), `test_append_event_rejects_deeply_nested_extensions_without_recursion_error` and `test_append_event_rejects_deeply_nested_observation_without_recursion_error` (`ARGUS2-INPUT-FIELD-INVALID`, stream bytes unchanged). A pre-decoded, string-aware, linear nesting scan (`MAX_JSON_NESTING = 128`) rejects too-deep input with a stable bounded `ValueError`/`ARGUS2` diagnostic before any recursive operation; residual `RecursionError` is converted to the same bounded failure in `parse_json_bounded`, `canonical_json`, reader and admission paths. |

The `AR-RVW-001` repair is additionally confirmed by an independent, non-test invocation in this stage:
`parse_json_bounded` and `canonical_json` each raise `ValueError: JSON nesting exceeds the bounded
maximum depth` (never `RecursionError`) for a 5000-deep document, while shallow values are unchanged.

## 5. Required case classes exercised

All case classes the stage contract requires are exercised by executed assertions, not by inspection:

| Required class | Exercised by (all PASSED) |
| --- | --- |
| Failure — rejected input | `test_digest_mutation_and_unsupported_versions_rejected_without_partial_state`, `test_duplicate_identity_and_nonfinite_values_rejected`, `test_missing_clock_domain_and_unit_rejected`, `test_exceeded_caller_bounds_rejected_with_stable_diagnostics` |
| Security — confinement | `test_unsafe_paths_and_symlink_escapes_rejected`, `test_adversarial_reads_confined_and_bounded_before_io` (the escape target is asserted absent; reads are confined and bounded before I/O) |
| Uncertainty — clocks and causation | `test_evidence_stream_records_identity_clocks_and_causation`, `test_missing_causal_and_interval_closure_remain_visible`, `test_missing_clock_domain_and_unit_rejected`, `test_ingestion_order_is_not_temporal_or_causal_order` |
| Retention — loss and visibility | `test_owned_observation_projection_preserves_visibility_and_loss`, `test_metadata_only_redacted_and_truncated_payloads_remain_distinct`, `test_retention_counters_do_not_substitute_for_interval_closure` |
| Recovery — damage without mutation | `test_truncated_stream_and_interrupted_finalize_report_incomplete`, `test_recovery_reads_bounded_prefix_without_mutating_originals`, `test_recovery_diagnostic_emission_stops_at_caller_bound` (originals hash-equal before/after) |
| Honest completeness | `test_known_loss_and_unmet_obligation_never_become_complete`, `test_snapshot_interval_closure_required_for_completeness`, `test_missing_causal_and_interval_closure_remain_visible`, `test_adversarial_corrupt_evidence_assessed_incomplete_never_primary_complete` |
| Metamorphic determinism | `test_repeated_reads_and_exports_are_byte_equal`, `test_canonical_serialization_independent_of_input_key_order` |
| Compatibility / additive behaviour | `test_installed_wheel_imports_argus_and_preserved_xdl_contracts`, `test_additive_unknown_field_and_unknown_major_behaviour_explicit`, `test_existing_xdl_cli_and_public_api_unchanged` |
| Read-only reconstruction | `test_reader_reconstructs_evidence_read_only_deterministically`, `test_metric_inputs_link_captured_selection_without_computation`, `test_replay_never_executes_components_or_oracle` (socket/subprocess are monkeypatched to fail and are never reached) |
| Durability / bounded publication | `test_adversarial_manifest_byte_bound_enforced_at_every_publication`, `test_adversarial_admission_snapshots_and_views_immune_to_caller_mutation` |
| Non-finite rejection (residual `AR-F03`) | `test_reader_rejects_nonfinite_manifest_values_before_assessment_or_export`, `test_reader_rejects_nonfinite_manifest_tokens_from_raw_text` |
| Exact byte bound (residual `AR-F04`) | `test_manifest_publication_bound_includes_the_final_newline` |
| Bounded deep nesting (`AR-RVW-001`) | the seven additive deep-nesting cases named in §4 |
| Enclosing-depth export/admission (`AR-F03`, revision 6) | `test_event_json_export_last_accepted_and_first_rejected_depths`, `test_cli_export_first_rejected_event_depth_is_bounded`, `test_obligation_admission_last_accepted_and_first_rejected_depths` |

## 6. Supporting regression checks (worker-run, preliminary)

| # | Command (from the candidate checkout) | Exit | Observed result |
| --- | --- | --- | --- |
| 1 | `python3 -m pytest -vv -p no:cacheprovider tests/thesis_lite/argus/test_argus2_validation.py` | 0 | `30 passed in 8.73s` — frozen set equality re-verified (30 discovered, 30 unique, 0 missing, 0 extra, all PASSED) |
| 2 | `python3 -m pytest -vv -p no:cacheprovider tests/thesis_lite/argus/test_argus2_repair_unit.py` | 0 | `21 passed in 3.89s` — 21 additive adversarial cases, including the seven `AR-RVW-001` deep-nesting cases and the three revision-6 `AR-F03` enclosing-depth cases |
| 3 | `python3 -m pytest -vv -p no:cacheprovider tests/thesis_lite/argus/test_argus2_integration.py` | 0 | `9 passed in 47.73s` — discovered set equals the frozen `ARGUS2-INTEGRATION` measure exactly (9/9); re-executed, not inherited from the earlier observation |
| 4 | `python3 -m pytest -q -p no:cacheprovider tests/thesis_lite/argus` | 0 | `232 passed in 79.00s` (193 unit — 172 frozen + 21 additive adversarial — , 9 integration, 30 validation) |
| 5 | `python3 -m pytest -q -p no:cacheprovider tests` | 0 | `527 passed in 106.80s` — no regression in the accepted XDL, catalog, lifecycle, CLI or C++ X-COM suites |
| 6 | `python3 -m pytest --collect-only -q -p no:cacheprovider tests/thesis_lite/argus` | 0 | 232 nodes collected; all 172 `ARGUS2-UNIT` + 9 `ARGUS2-INTEGRATION` + 30 `ARGUS2-VALIDATION` frozen identifiers present (0 missing) |
| 7 | `ast.parse` over `src/**/*.py` and `tests/thesis_lite/argus/**/*.py` (trusted `static` branch, no writes) | 0 | `STATIC_CHECK_PASSED 49` source/test files parse |

These are candidate-local worker checks, not trusted measure evidence. The trusted host repeats the
exact sealed candidate over the pinned target repository and the installed wheel.

## 7. Trace finalization and preservation

`engineering/trace/links.json` is the mutable current trace file. The revision-6 implementation repaired
`src/xverse/argus/api.py` (`74858074…`), `reader.py` (`1347eda6…`) and `writer.py` (`7f8d816e…`) on top
of `schema.py` (`48c0c184…`) and `recovery.py` (`528c8756…`), and refreshed the `implemented_by` code
endpoints that target them; that refresh is bound by `argus2-implementation.json` (`b1c08083…`) and is
**not** repeated here.

This stage verified, read-only, that no endpoint is stale and therefore finalized the file unchanged:

* `engineering/trace/links.json` `sha256=b5c8e4d57680c105ef6a43f28ad222f398839ffbae33521295ab03e058a60e1f`
  (unchanged; `project_id=xverse-platform`, 3595 link objects, 968 artifacts).
* `engineering/project.json` `sha256=9d5927ebbf13f8141d8b7100c0fc07c764722a577e09f65057506006565df7ad`
  (unchanged).
* A read-only local replay of `fabro_engineering.core.validate_trace(checkout, 'xverse-platform')`
  returns **`{'artifacts': 968, 'links': 3595}`** with no stale endpoint; `core.validate_stage` over the
  six inherited ARGUS2 stage records also passes with 110/110 artifact hashes matching.
* No trace link references `docs/engineering/argus-lite/validation.md` or
  `engineering/stage-results/argus2-validation.json`, so writing this stage's artifacts creates no stale
  endpoint.

Modifying `links.json` here would invalidate the artifact hash bound by `argus2-implementation.json`, so
the correct final action is to confirm it is already current and leave it byte-preserved.

## 8. Prior-artifact preservation

The 110 artifacts recorded by the six completed prior ARGUS2 stage records were recomputed by SHA-256
through `fabro_engineering.core.validate_stage` and all match:

| Stage record | Artifacts | Match |
| --- | --- | --- |
| `argus2-requirements.json` (`94e67cbd…`) | 24 | 24 |
| `argus2-architecture.json` (`a099e7a1…`) | 14 | 14 |
| `argus2-unit_specification.json` (`1556d7e3…`) | 13 | 13 |
| `argus2-verification_design.json` (`191b5afd…`) | 14 | 14 |
| `argus2-implementation.json` (`b1c08083…`) | 44 | 44 |
| `argus2-integration.json` (`4b02df9d…`) | 1 | 1 |

110 of 110 match. The twelve exact `bounded_partial` REF-002 parents (`XVE-SYS-00015`, `XVE-SYS-0016`,
`XVE-SYS-0179`, `XVE-SYS-0183`, `XVE-SYS-0185`, `XVE-SYS-0186`, `XVE-SYS-0188`, `XVE-SYS-0194`,
`XVE-SYS-0198`, `XVE-SYS-0201`, `XVE-SYS-0203`, `XVE-SYS-0211`) and their anchor copies remain
unchanged, and no parent disposition is promoted or closed. The predecessor validation records bound to
the revision-3, revision-4 and revision-5 candidates are superseded by this revision-5 record, whose
identity is preserved here as lineage.

## 9. Limitations and honest status

* Trusted whole-system verification, candidate sealing, the external assembly policy and terminal author
  acceptance remain external host/user gates. This stage replicated the frozen validation command
  faithfully but cannot substitute for them; worker checks are not reported as trusted verification.
* The external findings file bound by an earlier implementation record is not present in this validation
  worker; the findings `AR-F01`–`AR-F05`, `AR-RVW-001` and the two `AR-F03` enclosing-depth failures were
  re-derived verbatim from the admitted, frozen `ARGUS2-VS-08` scenario, the frozen continuation rework
  basis and the revision-6 implementation record rather than from an unavailable file. This is recorded
  as a limitation, not hidden.
* The measured validation runs used the repository root as the accepted platform source root because
  `/target` is not mounted in this worker (`ARGUS_PLATFORM_SOURCE_ROOT` falls back to the checkout root,
  as the frozen contract permits); the trusted host supplies `/target`.
* Successful finalization of an Argus run means only that the caller-declared capture obligations and
  integrity checks were satisfied; it never proves scientific validity, safety, compatibility, parity or
  readiness. Nothing here claims otherwise.
* Inherited limitation: the admitted planning bundle names a required launch-evidence `admission/review.md`
  that is not an admitted input for this run; it remains an external, unverified later-gate input and is
  neither fabricated nor substituted.
* No REF-002 parent disposition is promoted or closed and no new system requirement ID is created.

## 10. Evidence identities (temporary, worker-run)

The bounded evidence below lives under `/tmp` and is not shipped; the hashes are recorded for the host
evidence bundle.

| Evidence | SHA-256 |
| --- | --- |
| `/tmp/argus2_val6/validation30.log` (30 frozen validation cases, 30 passed) | `07c43e28b17483e1f58deba12bb2ce303634b40a3f933fcd7af2beae31a381c2` |
| `/tmp/argus2_val6/repair_unit.log` (21 additive adversarial cases, 21 passed) | `7829d1bf5baa7c46257f89ee8846cd2f7a9709fcddcefa0490518c44e4dad17f` |
| `/tmp/argus2_val6/integration9.log` (9 frozen integration cases, 9 passed) | `9a36e6921f869a89990b6b7226139737be3aa173212c86e9718ab9d150ae3503` |
| `/tmp/argus2_val6/owned_suite.log` (owned Argus suite, 232 passed) | `ab5362e59ea5842aa764a8be762f66dda5367a039b6cbe1992e07dafa4b062c5` |
| `/tmp/argus2_val6/platform_suite.log` (full platform pytest, 527 passed) | `5f69d3991f4721b1645fba45f2c9ba883894bca1df83d2a08388bb44a12f3b37` |
| `/tmp/argus2_val6/static.log` (AST parse, 49 files) | `568ac854c48f46fcbc0c65f70c5c821e945c093ac9c3ec37e6a293ec2e0466a8` |
| `/tmp/argus2_val6/collect.log` (owned collection, 232 nodes, 0 frozen id missing) | `13303000b1d78883fa0e7aaf17f90d7a2d1bfda1fe15087066ebe5ebc79ab7ce` |

## 11. Model and next step

The pinned `deepseek-v4-flash` with **high** reasoning remained the only authorized and most
cost-effective route for this deterministic validation-and-trace-finalization work; no model switch,
no subagent and no fallback occurred, and no benchmark or exact-cost claim is made. Escalation would be
justified only by a measured, reproducible failure this route cannot resolve.

Next step: **documentation** — write `maintenance.md`, `implementation.md` and `reports/review-index.md`,
documenting API/CLI usage, limits, versions, dependencies, loss/incomplete and recovery behaviour, wheel
packaging, clock and authority boundaries and limitations, without fabricating host verification success
and without code repairs. Blockers: none for this stage; the trusted host must still bind and execute the
four ARGUS2 measures (unit, static, integration, validation) against the sealed candidate, and the
separate read-only internal review precedes terminal acceptance.
