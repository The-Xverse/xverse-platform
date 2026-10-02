# Argus Lite Phase 2 — verification plan

**Feature:** ARGUS2 (Argus Lite Phase 2 — bounded run evidence persistence, X-COM observation import and read-only reconstruction)
**Stage:** verification_design (repository-owned Spec Kit work-product workflow, ADR-0020)
**Attempt:** ARGUS2 attempt 1 — **Revision 2 (terminal-review rework)**
**Date:** 2026-10-02
**Admitted platform baseline:** `c1fd213cd00259b74f8308d8ca58157ea985aaa0` (Phase 1 XDL Lite accepted and merged)
**Maturity: planned / target.** This plan freezes identifiers, measures, scenarios and the real interoperability fixture; it executes nothing and proves nothing. Source or design inspection does not demonstrate runtime success.

This document is the verification-design work product for the bounded ARGUS2 slice. Revision 2 is the
terminal-review rework of the unaccepted candidate: it flips every measure onto the reworked design and
unit specification, freezes one additive adversarial validation scenario for findings `AR-F01`–`AR-F05`,
and preserves all 139 pre-rework unit identifiers plus the original seven scenarios. It binds four scoped
measures to exact, frozen identifiers, freezes the real owned C++ observation/snapshot producer fixture and
the accepted XDL compiler consumer cases, and completes the parent → software → design → unit → test →
measure and scenario trace. It authors no verification evidence: unit, static, integration and validation
execution, the pinned-target assembly, the read-only internal review and terminal author acceptance are
external gates that remain pending.

## 1. Document control

| Field | Value |
| --- | --- |
| Feature / task token | `ARGUS2` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1, `engineering/requirements/ARGUS2-SR-001..012.json` (immutable) |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 rework, [`detailed-design.md`](detailed-design.md) rev 1 rework |
| Adversarial case authority | `architecture.md` §11.1 registry `ARGUS2-ADV-01` … `ARGUS2-ADV-07` (frozen before code) |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 rework, `engineering/unit-specifications/ARGUS2-SR-001-U..012-U.json` |
| Frozen design hand-off authority | `detailed-design.md` §18 (four ARGUS2 measures, adversarial binding and the real fixture) |
| Code links | deferred; planned endpoints in [`planned-trace.json`](planned-trace.json) |
| Verification profile | `generic-explicit-command` (external trusted policy owns the executable commands) |

## 2. Verification strategy and scoping

Four ARGUS2-scoped measure records are frozen, one per trusted measure kind, so the historical protected measure records under `engineering/verification/measures/**` are never rewritten:

| Measure record | Kind | Exact IDs | Purpose |
| --- | --- | --- | --- |
| `ARGUS2-UNIT` | `unit` | 172 | The frozen unit cases of the twelve unit records: 139 preserved pre-rework regression cases plus 33 additive terminal-review repair cases. |
| `ARGUS2-STATIC` | `static_analysis` | 18 | The twelve base per-unit static checks plus six additive terminal-review repair checks over all candidate Python plus the additive-diff scope check. |
| `ARGUS2-INTEGRATION` | `integration` | 9 | Real accepted XDL compiler, real owned C++20 X-COM producer fixture and the offline installed wheel in the assembled pinned target (unchanged by the rework). |
| `ARGUS2-VALIDATION` | `validation` | 30 | The union of the eight ARGUS2-VS scenario test identifiers: 25 preserved plus five additive adversarial (VS-08) cases. |

The trusted host policy binds the executable `unit`, `static_analysis`, `integration` and `validation` commands to these four record identities and re-runs them against the exact sealed candidate revision. This candidate cannot inspect or edit that external policy; the dependency is recorded here so its absence fails the host gates closed rather than being papered over. Whole-system integration is defined only by the trusted policy `system_integration` contract over the pinned platform revision; the candidate-local `command`/`command_runs` descriptors in the measure records are not integration evidence.

A verification identifier is admissible only if it can appear verbatim in the relevant actual log. Every ARGUS2 pytest identifier is a full node identifier of the form `tests/thesis_lite/argus/<module>.py::test_<case>` with no hyphen, so the trusted discovery normalization `test_id.replace('-','_')` is a no-op. The `ARGUS2-STATIC` measure declares structural checks rather than pytest-discovered cases and therefore requires no pytest output; its eighteen identifiers are the declared `static_checks` of the unit records, each bound by an `analyzed_by` link.

### 2.1 Terminal-review repair verification (AR-F01 – AR-F05)

Revision 2 exists to verify the five high findings recorded by the independent terminal review of the unaccepted candidate (`verdict: rework`). Each finding maps to a frozen adversarial case (`architecture.md` §11.1) and to exact identifiers that must be created verbatim by implementation:

| Finding | Adversarial case(s) | Required verified behaviour | Bound at unit | Bound at validation |
| --- | --- | --- | --- | --- |
| `AR-F01` read confinement and resource bounds | `ARGUS2-ADV-01`, `ARGUS2-ADV-02` | Confined regular-file checks (`os.lstat`/`O_NOFOLLOW`) execute **before** any I/O and reject traversal/absolute, symlink (even in-root), and non-regular manifest/stream/artifact paths; manifest/stream/line/event/diagnostic reads are bounded before parsing; the caller `limits` argument is authoritative and a damaged manifest's echoed limits never relax a bound. | 10 cases | `…::test_adversarial_reads_confined_and_bounded_before_io` |
| `AR-F02` assessed completeness reflects corruption | `ARGUS2-ADV-03` | The reader exposes `recorded` and `assessed` status/reasons separately; corrupt/truncated/loss evidence is exported as assessed `incomplete`, never primary `complete`; CLI `verify` exits 0 only on assessed complete. | 5 cases | `…::test_adversarial_corrupt_evidence_assessed_incomplete_never_primary_complete` |
| `AR-F03` strict schemas, identities, stable diagnostics | `ARGUS2-ADV-04`, `ARGUS2-ADV-05` | Complete frozen nested schemas, required run/event/producer identity, per-run `eventId` uniqueness, strictly increasing `ingestionOrdinal`, run-ID consistency and finite values are verified on read; malformed containers/versions/I/O yield bounded stable diagnostics and never an uncaught `TypeError`/`ValueError`. | 9 cases | `…::test_adversarial_strict_schema_and_identities_yield_only_stable_diagnostics` |
| `AR-F04` manifest byte bound at every publication | `ARGUS2-ADV-06` | Every open/finalize/abort publication measures the **actual** canonical serialized bytes against `max_manifest_bytes`; a bound or I/O failure preserves the prior manifest and reports a stable error without claiming `closed`/`complete`. | 3 cases | `…::test_adversarial_manifest_byte_bound_enforced_at_every_publication` |
| `AR-F05` admission snapshot and view isolation | `ARGUS2-ADV-07` | Admitted nested obligations/envelope/digests/clocks/extensions are deep-snapshotted; indexed artifact identity is internally owned; returned views are immutable/defensive, so post-admission caller mutation cannot lower an obligation, rewrite an indexed hash or alter a returned view. | 6 cases | `…::test_adversarial_admission_snapshots_and_views_immune_to_caller_mutation` |

All seven adversarial cases are bound to at least one exact identifier in the `ARGUS2-UNIT` measure and, end to end, in the `ARGUS2-VS-08` scenario of the `ARGUS2-VALIDATION` measure. The pre-rework passing cases are preserved; no case is deleted, renamed or weakened.

## 3. ARGUS2-UNIT measure

`engineering/verification/measures/ARGUS2-UNIT.json` declares exactly the 172 `unit_cases` of the twelve unit records (set equality re-checked when the record was generated). The cases are grouped by module:

| Module | Cases | Owning unit record(s) |
| --- | --- | --- |
| `tests/thesis_lite/argus/test_argus2_admission_unit.py` | 13 | ARGUS2-SR-001-U |
| `tests/thesis_lite/argus/test_argus2_artifacts_unit.py` | 14 | ARGUS2-SR-007-U |
| `tests/thesis_lite/argus/test_argus2_bounds_unit.py` | 15 | ARGUS2-SR-005-U |
| `tests/thesis_lite/argus/test_argus2_clocks_unit.py` | 8 | ARGUS2-SR-004-U |
| `tests/thesis_lite/argus/test_argus2_consumer_unit.py` | 10 | ARGUS2-SR-012-U |
| `tests/thesis_lite/argus/test_argus2_diagnostics_unit.py` | 4 | ARGUS2-SR-005-U |
| `tests/thesis_lite/argus/test_argus2_identity_unit.py` | 17 | ARGUS2-SR-003-U |
| `tests/thesis_lite/argus/test_argus2_observation_unit.py` | 12 | ARGUS2-SR-008-U |
| `tests/thesis_lite/argus/test_argus2_offline_unit.py` | 11 | ARGUS2-SR-011-U |
| `tests/thesis_lite/argus/test_argus2_payload_unit.py` | 13 | ARGUS2-SR-009-U |
| `tests/thesis_lite/argus/test_argus2_reader_unit.py` | 24 | ARGUS2-SR-010-U |
| `tests/thesis_lite/argus/test_argus2_recovery_unit.py` | 3 | ARGUS2-SR-006-U |
| `tests/thesis_lite/argus/test_argus2_stream_unit.py` | 16 | ARGUS2-SR-002-U |
| `tests/thesis_lite/argus/test_argus2_writer_unit.py` | 12 | ARGUS2-SR-006-U |

The set covers every defect class the workflow requires: duplicate event identity, unknown major versions, partial writes and recovery, every exceeded caller bound, source/plan digest mutation, missing causal closure, missing interval closure, payload visibility and loss, unsafe paths and symlinks, installed-wheel consumer compatibility, **and** the five terminal-review repairs (pre-I/O confinement, bounded streaming reads with caller-authoritative limits, recorded-versus-assessed corruption status, strict nested schemas/identities with stable diagnostics, actual manifest byte bound at every publication, and deep admission snapshots with immutable returned views). The `ARGUS2-STATIC` analysis also parses these modules read-only, so a case declared here may additionally appear in the static analysis; every declared identifier must nevertheless appear in the unit execution log it is bound to.

## 4. ARGUS2-STATIC measure

`engineering/verification/measures/ARGUS2-STATIC.json` declares the eighteen per-unit static checks (twelve base plus six additive repair checks). Each parse of the candidate Python (`src/xverse/argus/**` plus the owned `tests/thesis_lite/argus/**`) is read-only and requires no pytest output; the analysis additionally asserts canonical serialization flags, the closed diagnostic catalogue, the absence of ambient clock/random/network calls, the read-only reader and the additive wheel composition, plus a diff/wheel scope check that no accepted XDL, C++ X-COM, legacy/compat/blueprint source or historical record changed.

| Static check | Bound unit | Scope |
| --- | --- | --- |
| `ARGUS2-SR-001-U-STATIC` | `ARGUS2-SR-001-U` | base |
| `ARGUS2-SR-001-U-STATIC-SNAPSHOT` | `ARGUS2-SR-001-U` | repair: deep-snapshot of admitted caller objects, no retained caller reference, defensive accessors (`AR-F05`) |
| `ARGUS2-SR-002-U-STATIC` | `ARGUS2-SR-002-U` | base |
| `ARGUS2-SR-002-U-STATIC-PUBLISH` | `ARGUS2-SR-002-U` | repair: every manifest publication measures actual serialized bytes; prior manifest preserved on failure (`AR-F04`) |
| `ARGUS2-SR-003-U-STATIC` | `ARGUS2-SR-003-U` | base |
| `ARGUS2-SR-004-U-STATIC` | `ARGUS2-SR-004-U` | base |
| `ARGUS2-SR-005-U-STATIC` | `ARGUS2-SR-005-U` | base |
| `ARGUS2-SR-005-U-STATIC-DIAGNOSTICS` | `ARGUS2-SR-005-U` | repair: closed bounded diagnostic catalogue; malformed input yields only stable categorized diagnostics (`AR-F03`) |
| `ARGUS2-SR-006-U-STATIC` | `ARGUS2-SR-006-U` | base |
| `ARGUS2-SR-006-U-STATIC-READBOUND` | `ARGUS2-SR-006-U` | repair: bounded streaming reads; no unbounded `read()`/`read_bytes()` of manifest or stream (`AR-F01`) |
| `ARGUS2-SR-007-U-STATIC` | `ARGUS2-SR-007-U` | base |
| `ARGUS2-SR-007-U-STATIC-CONFINE` | `ARGUS2-SR-007-U` | repair: pre-I/O `lstat`/`O_NOFOLLOW` confinement of manifest/stream/artifact paths (`AR-F01`) |
| `ARGUS2-SR-008-U-STATIC` | `ARGUS2-SR-008-U` | base |
| `ARGUS2-SR-009-U-STATIC` | `ARGUS2-SR-009-U` | base |
| `ARGUS2-SR-010-U-STATIC` | `ARGUS2-SR-010-U` | base |
| `ARGUS2-SR-010-U-STATIC-CONFINE` | `ARGUS2-SR-010-U` | repair: reader resolves and confines recorded paths before I/O; caller limits authoritative (`AR-F01`) |
| `ARGUS2-SR-011-U-STATIC` | `ARGUS2-SR-011-U` | base |
| `ARGUS2-SR-012-U-STATIC` | `ARGUS2-SR-012-U` | base |

## 5. ARGUS2-INTEGRATION measure

`engineering/verification/measures/ARGUS2-INTEGRATION.json` freezes 9 exact identifiers in `tests/thesis_lite/argus/test_argus2_integration.py` (unchanged by the rework; the repaired reader/writer are the same public interfaces the integration cases already exercise). The implementation stage must create each verbatim; renaming, dropping or weakening one requires a reviewed successor candidate.

| Integration case | What it must exercise for real |
| --- | --- |
| `test_real_accepted_xdl_compiler_output_written_and_reconstructed` | The real accepted XDL compiler produces an owned neutral experiment plan; the writer consumes it and the reader reconstructs it. |
| `test_real_owned_cpp_observation_fixture_compiles_and_imports_by_value` | A real C++20 fixture, compiled against the accepted headers/implementation, produces owned `ObservationRecord` values that are serialized to the frozen projection and imported with every accessor preserved. |
| `test_real_owned_cpp_snapshot_fixture_preserves_interval_and_counters` | The same fixture produces an `ObservationSnapshot`; interval provenance, counters, backpressure and validity state are preserved. |
| `test_owned_cpp_projection_roundtrip_with_accepted_xcom_headers` | The projection round-trips values exactly and asserts the upstream contract identity (`kObservationContractVersion`). |
| `test_installed_wheel_imports_xverse_argus_and_xverse_xdl_outside_source_tree` | The offline-built wheel installs; `xverse.argus` and `xverse_xdl` import from outside the source tree. |
| `test_owned_argus_tests_repeat_against_installed_wheel_with_empty_pythonpath` | The owned Argus tests run against the installed wheel with an empty `PYTHONPATH`; no source `sys.path` injection. |
| `test_existing_platform_pytest_regression_unchanged_in_assembled_target` | The full platform pytest suite passes unchanged in the assembled pinned target. |
| `test_existing_xdl_cli_and_public_api_preserved_in_assembled_target` | The existing `xdl` CLI and accepted `xverse_xdl` public API behave as before. |
| `test_gateway_protobuf_observation_not_substituted_for_owned_projection` | The narrower tool-gateway protobuf observation is rejected as the full owned projection. |

### 5.1 Frozen real C++ owned-record fixture

The fixture is owned (never an accepted C++ source edit) and is built outside the source tree under `/tmp`:

| Item | Frozen value |
| --- | --- |
| Fixture source | `tests/thesis_lite/argus/fixtures/argus2_owned_record_producer.cpp` (new, owned) |
| Compiler invocation | `g++ -std=c++20 -I src/xverse/xcom/include -I src/xverse/xcom/src` plus the accepted `src/xverse/xcom/src/observation.cpp` and the accepted `src/xverse/xcom/src/item.cpp`/`value.cpp`/`contract.cpp`/`diagnostic.cpp` translation units it directly requires; build output under `/tmp` |
| Accepted contract | `src/xverse/xcom/include/xverse/xcom/observation.hpp`, `kObservationContractVersion = 1.0.0` |
| Producer path | In-process `ObservationHub` only: `attach(ObservationTapSpec)` → `reserve(item)` → `commit(reservation, ObservationEvent)` → `poll(handle)` for owned records and `snapshot(handle)` for the snapshot. No tap is attached outside the fixture, no hub handle enters Argus, and no delivery behaviour changes. |
| Serialized fields | `ObservationRecord` accessors by value: `contract_id`, `contract_version`, `interface_id`, `endpoint_id`, `schema_id`, `schema_version`, `interaction_kind`, `origin`, `source_timestamp`, `source_clock_domain`, `observation_timestamp`, `observation_clock_domain`, `sequence` (presence preserved), `correlation_id`, `causation_id`, `route_id`, `provider_id`, `source_payload_size`, `provider_outcome`, `payload_view_state`, `payload_schema_state`, `payload_bytes` (visible bytes only), `tap_id`, `counters` |
| Serialized snapshot fields | `ObservationSnapshot`: `queued`, `accepted`, `dropped`, `coalesced`, `backpressure_rejections`, `experiment_validity_degraded`, `declared_tap_id`, `validity_effect`, `validity_state` plus the declared observation interval/stream identity supplied by the test |
| Neutral coverage | metadata-only, redacted, bounded-prefix, complete, dropped/coalesced, degraded and invalid validity states, each with an explicit snapshot |
| Prohibition | No public C++ source or header is changed; no legacy or production workload is executed; the fixture is not an Argus oracle and yields no scientific result. |

### 5.2 Frozen accepted XDL/compiler consumer cases

| Case | Frozen source |
| --- | --- |
| Plan origin | The real accepted XDL compiler (`xverse_xdl` CLI/API at platform main `c1fd213c…`) over an owned neutral experiment fixture under `tests/thesis_lite/argus/fixtures/`. |
| Digest reuse | `xverse_xdl.experiment_plan.plan_matches_digest` / `compute_plan_digest`; Argus never reimplements or rehashes the semantic plan digest. |
| Envelope separation | The run/source-byte envelope is kept as provenance and is never substituted for the semantic plan identity. |
| Version guard | `API_VERSION = xverse.io/xdl/v1alpha1`, `PLAN_VERSION = 1`; an unknown major is rejected, never coerced. |

## 6. ARGUS2-VALIDATION measure and scenarios

`engineering/verification/measures/ARGUS2-VALIDATION.json` declares the union of the eight scenario `test_ids` (30 identifiers, equality re-checked during generation). Every one of the twelve accepted software requirements is validated by at least one scenario.

| Scenario | Intended use | Requirements validated | Cases |
| --- | --- | --- | --- |
| `ARGUS2-VS-01` | Caller opens one run from a real compiled plan and captures a bounded causal evidence stream | ARGUS2-SR-001, ARGUS2-SR-002, ARGUS2-SR-003, ARGUS2-SR-004, ARGUS2-SR-005 | 3 |
| `ARGUS2-VS-02` | Analyst imports an owned X-COM observation projection and preserves visibility, loss and interval facts | ARGUS2-SR-008, ARGUS2-SR-009, ARGUS2-SR-002, ARGUS2-SR-004 | 3 |
| `ARGUS2-VS-03` | Analyst reconstructs evidence read-only with deterministic selection and declared metric-input links | ARGUS2-SR-010, ARGUS2-SR-007, ARGUS2-SR-011 | 3 |
| `ARGUS2-VS-04` | Integrator receives stable categorized diagnostics for every declared rejection class | ARGUS2-SR-001, ARGUS2-SR-003, ARGUS2-SR-004, ARGUS2-SR-005, ARGUS2-SR-007 | 5 |
| `ARGUS2-VS-05` | Operator recovers incomplete or damaged evidence without mutating the originals | ARGUS2-SR-002, ARGUS2-SR-006, ARGUS2-SR-009, ARGUS2-SR-003 | 4 |
| `ARGUS2-VS-06` | Maintainer consumes the installed wheel and the preserved existing contracts | ARGUS2-SR-012, ARGUS2-SR-002, ARGUS2-SR-011 | 3 |
| `ARGUS2-VS-07` | Metamorphic determinism and honest completeness across equivalent inputs | ARGUS2-SR-002, ARGUS2-SR-003, ARGUS2-SR-004, ARGUS2-SR-009, ARGUS2-SR-010 | 4 |
| `ARGUS2-VS-08` | **Adversarial repair validation (AR-F01–AR-F05):** hostile evidence and post-admission caller mutation | ARGUS2-SR-001, ARGUS2-SR-002, ARGUS2-SR-003, ARGUS2-SR-005, ARGUS2-SR-006, ARGUS2-SR-007, ARGUS2-SR-010, ARGUS2-SR-011 | 5 |

### ARGUS2-VS-01 — Caller opens one run from a real compiled plan and captures a bounded causal evidence stream

* **Intended use:** An experiment caller compiles an owned neutral experiment with the real accepted XDL compiler, supplies the resolved plan, run envelope, unique run identity, explicit producer/clock identities, finite limits and capture obligations, and receives exactly one opened run whose verified semantic plan digest is kept separate from source-byte provenance and whose events retain identity, explicit clock domains and causation.
* **Expected outcome:** Exactly one fresh run is opened; the atomic manifest records the accepted API/Profile/plan versions, the verified semantic digest and separate source-byte provenance; appended events retain identity, explicit source/observation clocks and declared causal references; finalization publishes a closed manifest with an explicit status and no invented identity, clock or ordering.
* **Environment:** candidate checkout and the assembled pinned xverse-platform target; offline, Python 3.11+ with the admitted dependencies, C++20 tooling for the owned observation producer fixture and the built-and-installed wheel; bounded neutral fixtures and temporary output roots; no network, production or legacy runtime.
* **Cases:**
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_caller_opens_run_from_real_compiled_plan_and_persists_events`
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_evidence_stream_records_identity_clocks_and_causation`
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_manifest_published_open_then_closed_with_verified_artifacts`

### ARGUS2-VS-02 — Analyst imports an owned X-COM observation projection and preserves visibility, loss and interval facts

* **Intended use:** An analyst supplies a serialized projection produced by a real owned C++ observation producer plus a separately supplied tap snapshot, and expects metadata-only, redacted, bounded-prefix, dropped/coalesced and degraded states to survive import unchanged.
* **Expected outcome:** Every owned accessor value is preserved by value; metadata-only and redacted records carry no payload bytes; bounded prefixes stay truncated; an unclosed, degraded or invalid interval keeps the run incomplete even when counters look benign; no tap is attached, no validity interval is acknowledged and no provider outcome is promoted to experiment validity.
* **Environment:** candidate checkout and the assembled pinned xverse-platform target; offline, Python 3.11+ with the admitted dependencies, C++20 tooling for the owned observation producer fixture and the built-and-installed wheel; bounded neutral fixtures and temporary output roots; no network, production or legacy runtime.
* **Cases:**
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_owned_observation_projection_preserves_visibility_and_loss`
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_metadata_only_redacted_and_truncated_payloads_remain_distinct`
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_snapshot_interval_closure_required_for_completeness`

### ARGUS2-VS-03 — Analyst reconstructs evidence read-only with deterministic selection and declared metric-input links

* **Intended use:** An analyst reads a finalized run with the bounded reader and the read-only CLI, expecting verified manifest/artifact hashes, records in ingestion-ordinal order, declared metric-input links and byte-stable JSON/JSONL export, with no execution of any component or oracle.
* **Expected outcome:** Repeated reads of unchanged inputs return equal content and deterministic selection order; metric inputs link to captured artifacts/events and are never computed; replay performs no execution, fault, lifecycle action, network access or oracle invocation; the run root is left byte-identical.
* **Environment:** candidate checkout and the assembled pinned xverse-platform target; offline, Python 3.11+ with the admitted dependencies, C++20 tooling for the owned observation producer fixture and the built-and-installed wheel; bounded neutral fixtures and temporary output roots; no network, production or legacy runtime.
* **Cases:**
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_reader_reconstructs_evidence_read_only_deterministically`
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_metric_inputs_link_captured_selection_without_computation`
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_replay_never_executes_components_or_oracle`

### ARGUS2-VS-04 — Integrator receives stable categorized diagnostics for every declared rejection class

* **Intended use:** An integrator deliberately supplies a mutated plan digest, an unsupported version, a duplicate identity, a non-finite value, a missing clock domain or unit, an exceeded caller bound, a traversal segment or an escaping symlink, and expects a stable structured diagnostic and no partially accepted state.
* **Expected outcome:** Each defect is rejected with its frozen diagnostic code and category; no run root is created or overwritten, no partially accepted record exists, and no write occurs outside the run root.
* **Environment:** candidate checkout and the assembled pinned xverse-platform target; offline, Python 3.11+ with the admitted dependencies, C++20 tooling for the owned observation producer fixture and the built-and-installed wheel; bounded neutral fixtures and temporary output roots; no network, production or legacy runtime.
* **Cases:**
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_digest_mutation_and_unsupported_versions_rejected_without_partial_state`
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_duplicate_identity_and_nonfinite_values_rejected`
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_missing_clock_domain_and_unit_rejected`
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_exceeded_caller_bounds_rejected_with_stable_diagnostics`
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_unsafe_paths_and_symlink_escapes_rejected`

### ARGUS2-VS-05 — Operator recovers incomplete or damaged evidence without mutating the originals

* **Intended use:** An operator encounters a truncated last record, an interrupted finalization, a known observation loss, an unmet obligation and a missing causal or interval closure, and expects them to remain explicitly incomplete or unresolved.
* **Expected outcome:** None of these conditions is upgraded to complete by finalization alone; the reader reports damage, known loss and unresolved closure with reason/diagnostic evidence and a bounded partial result while leaving the original evidence bytes unchanged.
* **Environment:** candidate checkout and the assembled pinned xverse-platform target; offline, Python 3.11+ with the admitted dependencies, C++20 tooling for the owned observation producer fixture and the built-and-installed wheel; bounded neutral fixtures and temporary output roots; no network, production or legacy runtime.
* **Cases:**
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_truncated_stream_and_interrupted_finalize_report_incomplete`
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_known_loss_and_unmet_obligation_never_become_complete`
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_missing_causal_and_interval_closure_remain_visible`
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_recovery_reads_bounded_prefix_without_mutating_originals`

### ARGUS2-VS-06 — Maintainer consumes the installed wheel and the preserved existing contracts

* **Intended use:** A maintainer builds and installs the additive wheel offline and imports xverse.argus and the existing xverse_xdl API from outside the source tree with an empty PYTHONPATH, while the existing xdl CLI and accepted C++/XDL contracts remain unchanged.
* **Expected outcome:** xverse.argus and xverse_xdl both import from the installed wheel outside the source tree; the xdl console entry point and public API behave as before; additive unknown-field and unknown-major behaviour is explicit; no accepted C++ or XDL source is modified and the C++ X-COM tree is not packaged.
* **Environment:** candidate checkout and the assembled pinned xverse-platform target; offline, Python 3.11+ with the admitted dependencies, C++20 tooling for the owned observation producer fixture and the built-and-installed wheel; bounded neutral fixtures and temporary output roots; no network, production or legacy runtime.
* **Cases:**
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_installed_wheel_imports_argus_and_preserved_xdl_contracts`
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_additive_unknown_field_and_unknown_major_behaviour_explicit`
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_existing_xdl_cli_and_public_api_unchanged`

### ARGUS2-VS-07 — Metamorphic determinism and honest completeness across equivalent inputs

* **Intended use:** An analyst compares repeated reads/exports of the same unchanged run, permuted but equivalent encodings, reordered appends and counter projections that look lossless, and expects canonical, order-stable output that never overstates completeness.
* **Expected outcome:** Repeated reads and exports are byte-equal; canonical serialization does not depend on input key order; ingestion order is never reported as temporal or causal order; retention counters never substitute for interval closure and cannot convert a known-loss or unclosed-interval run to complete.
* **Environment:** candidate checkout and the assembled pinned xverse-platform target; offline, Python 3.11+ with the admitted dependencies, C++20 tooling for the owned observation producer fixture and the built-and-installed wheel; bounded neutral fixtures and temporary output roots; no network, production or legacy runtime.
* **Cases:**
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_repeated_reads_and_exports_are_byte_equal`
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_retention_counters_do_not_substitute_for_interval_closure`
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_ingestion_order_is_not_temporal_or_causal_order`
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_canonical_serialization_independent_of_input_key_order`

### ARGUS2-VS-08 — Adversarial repair validation: confined bounded I/O, assessed corruption, strict schemas, publication byte bound and admission snapshot isolation

* **Intended use:** A security-minded integrator supplies hostile evidence (a traversal/absolute/symlink/non-regular manifest, stream or artifact path, an oversized manifest or event line, a damaged manifest that echoes permissive limits, a manifest that recorded `complete` whose stream is truncated or corrupt, malformed nested containers and unsupported versions) and a caller that mutates admitted obligations and returned views after admission, and expects every terminal-review repair `AR-F01`–`AR-F05` (frozen adversarial cases `ARGUS2-ADV-01`–`ARGUS2-ADV-07`) to hold end to end through the public API and CLI.
* **Expected outcome:** Reads are confined and bounded before I/O and caller limits stay authoritative; corrupt evidence is exported as assessed `incomplete` with recorded facts preserved separately and never as primary `complete`; strict nested schemas/identities/ordinals emit only stable bounded diagnostics with no uncaught `TypeError`/`ValueError`; every manifest publication enforces the actual serialized byte bound and preserves the prior manifest on bound or I/O failure; and post-admission mutation of caller objects or returned views cannot lower an obligation, rewrite an indexed artifact hash or change an exported selection.
* **Environment:** candidate checkout and the assembled pinned xverse-platform target; offline, Python 3.11+ with the admitted dependencies, C++20 tooling for the owned observation producer fixture and the built-and-installed wheel; bounded neutral fixtures, hostile malformed evidence and temporary output roots; no network, production or legacy runtime.
* **Cases:**
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_adversarial_reads_confined_and_bounded_before_io`
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_adversarial_corrupt_evidence_assessed_incomplete_never_primary_complete`
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_adversarial_strict_schema_and_identities_yield_only_stable_diagnostics`
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_adversarial_manifest_byte_bound_enforced_at_every_publication`
  * `tests/thesis_lite/argus/test_argus2_validation.py::test_adversarial_admission_snapshots_and_views_immune_to_caller_mutation`

## 7. Traceability

### 7.1 Requirement, design, unit and measure trace

| Parent (REF-002) | Software | Component | Design elements | Unit | Cases | Static | Verified by | Validated by |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `XVE-SYS-00015` | `ARGUS2-SR-001` | `ARGUS2-SR-001-CMP` | `ARGUS2-ARCH-01, ARGUS2-ARCH-05` (`ARGUS2-XB-01`) | `ARGUS2-SR-001-U` | 13 | `ARGUS2-SR-001-U-STATIC`, `-STATIC-SNAPSHOT` | `ARGUS2-UNIT`, `ARGUS2-INTEGRATION`, `ARGUS2-VALIDATION` | ARGUS2-VS-01, ARGUS2-VS-04, ARGUS2-VS-08 |
| `XVE-SYS-0016` | `ARGUS2-SR-002` | `ARGUS2-SR-002-CMP` | `ARGUS2-ARCH-02, ARGUS2-ARCH-12` (`ARGUS2-XB-06, ARGUS2-XB-08`) | `ARGUS2-SR-002-U` | 16 | `ARGUS2-SR-002-U-STATIC`, `-STATIC-PUBLISH` | `ARGUS2-UNIT`, `ARGUS2-INTEGRATION`, `ARGUS2-VALIDATION` | ARGUS2-VS-01, ARGUS2-VS-02, ARGUS2-VS-05, ARGUS2-VS-06, ARGUS2-VS-07, ARGUS2-VS-08 |
| `XVE-SYS-0179` | `ARGUS2-SR-003` | `ARGUS2-SR-003-CMP` | `ARGUS2-ARCH-03, ARGUS2-ARCH-05` (`ARGUS2-XB-02`) | `ARGUS2-SR-003-U` | 17 | `ARGUS2-SR-003-U-STATIC` | `ARGUS2-UNIT`, `ARGUS2-INTEGRATION`, `ARGUS2-VALIDATION` | ARGUS2-VS-01, ARGUS2-VS-04, ARGUS2-VS-05, ARGUS2-VS-07, ARGUS2-VS-08 |
| `XVE-SYS-0183` | `ARGUS2-SR-004` | `ARGUS2-SR-004-CMP` | `ARGUS2-ARCH-04, ARGUS2-ARCH-03` (`ARGUS2-XB-02`) | `ARGUS2-SR-004-U` | 8 | `ARGUS2-SR-004-U-STATIC` | `ARGUS2-UNIT`, `ARGUS2-INTEGRATION`, `ARGUS2-VALIDATION` | ARGUS2-VS-01, ARGUS2-VS-02, ARGUS2-VS-04, ARGUS2-VS-07 |
| `XVE-SYS-0185` | `ARGUS2-SR-005` | `ARGUS2-SR-005-CMP` | `ARGUS2-ARCH-05, ARGUS2-ARCH-07` (`ARGUS2-XB-05, ARGUS2-XB-01`) | `ARGUS2-SR-005-U` | 19 | `ARGUS2-SR-005-U-STATIC`, `-STATIC-DIAGNOSTICS` | `ARGUS2-UNIT`, `ARGUS2-INTEGRATION`, `ARGUS2-VALIDATION` | ARGUS2-VS-01, ARGUS2-VS-04, ARGUS2-VS-08 |
| `XVE-SYS-0186` | `ARGUS2-SR-006` | `ARGUS2-SR-006-CMP` | `ARGUS2-ARCH-06, ARGUS2-ARCH-02` (`ARGUS2-XB-06`) | `ARGUS2-SR-006-U` | 15 | `ARGUS2-SR-006-U-STATIC`, `-STATIC-READBOUND` | `ARGUS2-UNIT`, `ARGUS2-INTEGRATION`, `ARGUS2-VALIDATION` | ARGUS2-VS-05, ARGUS2-VS-08 |
| `XVE-SYS-0188` | `ARGUS2-SR-007` | `ARGUS2-SR-007-CMP` | `ARGUS2-ARCH-07, ARGUS2-ARCH-06` (`ARGUS2-XB-05`) | `ARGUS2-SR-007-U` | 14 | `ARGUS2-SR-007-U-STATIC`, `-STATIC-CONFINE` | `ARGUS2-UNIT`, `ARGUS2-INTEGRATION`, `ARGUS2-VALIDATION` | ARGUS2-VS-03, ARGUS2-VS-04, ARGUS2-VS-08 |
| `XVE-SYS-0194` | `ARGUS2-SR-008` | `ARGUS2-SR-008-CMP` | `ARGUS2-ARCH-08, ARGUS2-ARCH-09` (`ARGUS2-XB-03, ARGUS2-XB-04`) | `ARGUS2-SR-008-U` | 12 | `ARGUS2-SR-008-U-STATIC` | `ARGUS2-UNIT`, `ARGUS2-INTEGRATION`, `ARGUS2-VALIDATION` | ARGUS2-VS-02 |
| `XVE-SYS-0198` | `ARGUS2-SR-009` | `ARGUS2-SR-009-CMP` | `ARGUS2-ARCH-09, ARGUS2-ARCH-08` (`ARGUS2-XB-04, ARGUS2-XB-06`) | `ARGUS2-SR-009-U` | 13 | `ARGUS2-SR-009-U-STATIC` | `ARGUS2-UNIT`, `ARGUS2-INTEGRATION`, `ARGUS2-VALIDATION` | ARGUS2-VS-02, ARGUS2-VS-05, ARGUS2-VS-07 |
| `XVE-SYS-0201` | `ARGUS2-SR-010` | `ARGUS2-SR-010-CMP` | `ARGUS2-ARCH-10, ARGUS2-ARCH-07` (`ARGUS2-XB-03, ARGUS2-XB-05`) | `ARGUS2-SR-010-U` | 24 | `ARGUS2-SR-010-U-STATIC`, `-STATIC-CONFINE` | `ARGUS2-UNIT`, `ARGUS2-INTEGRATION`, `ARGUS2-VALIDATION` | ARGUS2-VS-03, ARGUS2-VS-07, ARGUS2-VS-08 |
| `XVE-SYS-0203` | `ARGUS2-SR-011` | `ARGUS2-SR-011-CMP` | `ARGUS2-ARCH-11, ARGUS2-ARCH-05` (`ARGUS2-XB-03, ARGUS2-XB-07`) | `ARGUS2-SR-011-U` | 11 | `ARGUS2-SR-011-U-STATIC` | `ARGUS2-UNIT`, `ARGUS2-INTEGRATION`, `ARGUS2-VALIDATION` | ARGUS2-VS-03, ARGUS2-VS-06, ARGUS2-VS-08 |
| `XVE-SYS-0211` | `ARGUS2-SR-012` | `ARGUS2-SR-012-CMP` | `ARGUS2-ARCH-12, ARGUS2-ARCH-06` (`ARGUS2-XB-08`) | `ARGUS2-SR-012-U` | 10 | `ARGUS2-SR-012-U-STATIC` | `ARGUS2-UNIT`, `ARGUS2-INTEGRATION`, `ARGUS2-VALIDATION` | ARGUS2-VS-06 |

Invariant coverage is recorded in `unit-specifications.md` §4 and carried by the unit records (`ARGUS2-INV-01` … `ARGUS2-INV-16`); no invariant is left without a unit case.

### 7.2 Trace relation summary (additive links)

| Relation | Endpoints | Link IDs |
| --- | --- | --- |
| `verified_by` | `ARGUS2-SR-001..012` → `ARGUS2-UNIT` | `ARGUS2-L-301` … `ARGUS2-L-312` |
| `verified_by` | `ARGUS2-SR-001..012` → `ARGUS2-INTEGRATION` | `ARGUS2-L-321` … `ARGUS2-L-332` |
| `verified_by` | `ARGUS2-SR-001..012` → `ARGUS2-VALIDATION` | `ARGUS2-L-341` … `ARGUS2-L-352` |
| `verified_by` | `ARGUS2-SR-001-CMP..012-CMP` → `ARGUS2-UNIT` | `ARGUS2-L-401` … `ARGUS2-L-412` |
| `verified_by` | `ARGUS2-SR-001-CMP..012-CMP` → `ARGUS2-INTEGRATION` | `ARGUS2-L-421` … `ARGUS2-L-432` |
| `verified_by` | `ARGUS2-SR-001-CMP..012-CMP` → `ARGUS2-VALIDATION` | `ARGUS2-L-441` … `ARGUS2-L-452` |
| `verified_by` | `ARGUS2-SR-001-U..012-U` → `ARGUS2-UNIT` | `ARGUS2-L-501` … `ARGUS2-L-512` |
| `analyzed_by` | `ARGUS2-SR-001-U..012-U` → `ARGUS2-STATIC` | `ARGUS2-L-601` … `ARGUS2-L-612` |
| `validates` | `ARGUS2-VS-01..07` → requirements | `ARGUS2-L-701` … `ARGUS2-L-729` |
| `validates` | `ARGUS2-VS-08` → requirements | `ARGUS2-L-901` … `ARGUS2-L-908` |

Inherited relations preserved unchanged: `refines` (`ARGUS2-L-001` … `-012`, requirements stage), `allocated_to` (`ARGUS2-L-101` … `-112`, architecture stage), `decomposes_to` (`ARGUS2-L-201` … `-212`, unit-specification stage) and the implementation-stage `implemented_by` links, all byte-preserved. Revision 2 adds only the eight `validates` links from the new `ARGUS2-VS-08` scenario; no prior link object is rewritten.

### 7.3 Deferred code links

`implemented_by` cannot be created by a design stage: the trusted `code_endpoint` contract resolves a real file (and a real symbol for a `::symbol` endpoint) and binds its SHA-256 as the code-endpoint revision. The exact planned endpoints for each requirement and unit are frozen in [`planned-trace.json`](planned-trace.json); the implementation stage adds or refreshes each `implemented_by` link with the exact current source hash **after** the repaired source exists, and the validation stage refreshes only the mutable current code-endpoint hashes. The inherited pre-rework `implemented_by` hashes are stale once implementation changes `src/**`; they are not carried forward and no supersession waiver is guessed. Until the implementation stage regenerates them, `validate_trace` coverage for the exact candidate is not claimed.

## 8. Evidence binding, manifests and integrity

* Every measure and scenario record is bound to the exact sealed candidate revision; the host evidence bundle retains the command, tool versions, environment identity, exit status, bounded log and content hashes.
* `ARGUS2-UNIT`, `ARGUS2-INTEGRATION` and `ARGUS2-VALIDATION` expect a nonzero pass count and no failure; `ARGUS2-STATIC` is a non-test structural measure.
* A missing, stale, mismatched, skipped or failed evidence item cannot support acceptance. Full-platform pytest is executed from the installed wheel outside the source tree with an empty `PYTHONPATH`; the accepted platform C++ sources and XDL fixtures are resolved from the caller environment `ARGUS_PLATFORM_SOURCE_ROOT=/target` during trusted checks and from the repository root in ordinary local tests.
* Every identifier declared in a measure must appear verbatim in that measure's actual log; a repair that adds a case must also make its identifier appear, and no previously passing case may be removed, skipped or weakened.
* The candidate declares no new dependency, runtime service, metric computation, control path, live tap bridge or oracle; only standard-library Python JSON/JSONL/JSON and hashing is used, with temporary build/output paths under `/tmp` and no network.

## 9. Local worker checks and limitations

Performed in this stage (local worker checks only, no trusted measure and no trusted shim):

* The `ARGUS2-UNIT` identifier set was re-checked for set equality against the twelve unit records (172 identical identifiers, no duplicates; 139 preserved + 33 adversarial repair).
* The `ARGUS2-STATIC` identifier set equals the eighteen declared unit `static_checks` (12 base + 6 repair).
* The `ARGUS2-VALIDATION` identifier set was re-checked for equality against the union of the eight scenario `test_ids` (30 identifiers), every scenario `test_ids` is a subset of the measure, and every one of `ARGUS2-SR-001..012` is named by at least one scenario `validates` list. All seven adversarial cases `ARGUS2-ADV-01`–`ARGUS2-ADV-07` are bound at both the unit measure and the `ARGUS2-VS-08` validation scenario.
* Only the eight additive `ARGUS2-VS-08` `validates` links were appended to `engineering/trace/links.json`; all 3587 inherited link objects and their endpoint revisions are preserved in order and content.
* This stage authors no verification evidence and performs no independent review; the admitted workflow requires a separate read-only internal_review stage after candidate sealing.
* This stage freezes no fresh `implemented_by` hash; the inherited pre-rework `implemented_by` endpoints become stale when implementation modifies `src/**` and must be regenerated with exact current hashes by the implementation stage (and refreshed by validation). No stale hash or supersession waiver is carried forward.
* Inherited limitation: the admitted planning bundle names a required launch-evidence `admission/review.md` that is not an admitted input for this run; it stays an external, unverified later-gate input and is neither fabricated nor substituted.

## 10. Next step and model recommendation

Next stage: **implementation** — create only the frozen Argus design, the exact test identifiers frozen here and in `unit-specifications.md` (including the 33 unit repair cases and the 5 `ARGUS2-VS-08` validation cases), the neutral fixtures (including the real C++20 producer fixture) and the additive wheel packaging; add or refresh the exact source-hash `implemented_by` endpoints. Design changes or independent decisions stop the run.

Model recommendation: the pinned `deepseek-v4-flash` with **high** reasoning remains the most cost-effective and the only authorized route for the deterministic identifier-binding and design-transcription implemented above; Terra/Luna/Sol/Astra are not authorized in this package, no model switch occurred, and no benchmark or exact-cost claim is made. For the implementation stage the same pinned route is still the best expected cost-effectiveness because the contracts are already frozen and the work is bounded transcription plus local tests; escalation would become justified only by a measured, reproducible failure that the pinned route cannot resolve.

Blockers: none for this stage. Implementation cannot start until the four design stages complete and the precode gate passes, and no legacy or production execution is authorized.
