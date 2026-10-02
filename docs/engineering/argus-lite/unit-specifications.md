# Argus Lite Phase 2 — unit specifications and planned unit cases

| Field | Value |
| --- | --- |
| Feature | ARGUS2 (Argus Lite Phase 2 — bounded run evidence persistence, X-COM observation projection import and read-only reconstruction) |
| Stage / role | unit_specification (pre-code; repository-owned Spec Kit work-product workflow, ADR-0020) |
| Revision | 1 |
| Revision basis | Revision 1 is the terminal-review rework of the 2026-10-01 revision 1 (run `01M3WW66FB61DKFEPWFEH2BFJE`, candidate `2f7806599e7df6693b9899fb328762728dbf65d5`, verdict `rework`). The rejected candidate was never accepted, so no accepted revision is superseded. All previously frozen cases are retained unchanged; the repair cases are additive. |
| Date | 2026-10-02 (rework of the 2026-10-01 revision) |
| Admitted platform baseline revision | `c1fd213cd00259b74f8308d8ca58157ea985aaa0` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 (`ARGUS2-SR-001` … `ARGUS2-SR-012`) |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 (`f2a44c73…`) |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 (`4f9537d6…`) |
| Component records | `engineering/architecture/components/ARGUS2-SR-001-CMP.json` … `ARGUS2-SR-012-CMP.json` |
| Unit records | `engineering/unit-specifications/ARGUS2-SR-001-U.json` … `ARGUS2-SR-012-U.json` |
| Planned unit cases | 172 exact pytest-discoverable test identifiers (139 inherited + 33 terminal-review repair cases) |
| Adversarial case registry | `ARGUS2-ADV-01` … `ARGUS2-ADV-07` (frozen by `architecture.md` §11.1; each bound to exact identifiers in §7.13) |
| Terminal-review findings repaired | `AR-F01` … `AR-F05` |
| Classification | Public-safe engineering work product |
| Maturity | **Planned / target.** Specification only; no source, schema, packaging, fixture or test code exists in this stage. Nothing here is implementation, verification, runtime, interoperability, readiness, compatibility or delivery evidence. |

## 1. Purpose and method

This work product specifies the smallest verifiable units of the Argus Lite Phase 2 evidence package and their
planned tests. It is a transcription of the frozen contracts in `requirements.md`, `architecture.md` and
`detailed-design.md`; it adds no new behaviour, no scientific value and no implementation. One unit record per
allocation component is used for the same reason as `architecture.md` §5: exactly one owning component per
accepted software requirement keeps the later `decomposes_to`, `implemented_by`, `verified_by` and `analyzed_by`
links unambiguous.

Method: for each of the 12 components the unit interface, state/concurrency, inputs, outputs, errors and
invariants are fixed; every planned case is an independent, table-driven expected outcome (precondition,
stimulus, expected) whose `id` is the exact pytest node identifier the implementation must create; adversarial
and uncertainty-preserving cases are included explicitly; one static check per unit is planned (additional
repair static checks are additive, §9). Test identifiers
are frozen here so the verification-design, implementation and validation stages cannot drift. Every identifier
is a module-level `test_` function under `tests/thesis_lite/argus/` and contains no hyphen, so the trusted
discovery normalization `test_id.replace('-', '_')` is a no-op and each identifier appears verbatim in verbose
pytest output.

The 2026-10-02 rework adds *only new* planned identifiers that repair the terminal-review findings
`AR-F01`–`AR-F05` at specification level: bounded streaming I/O, pre-I/O confined regular-file checks,
closed nested schemas and stable bounded diagnostics, reader-assessed corrupt-evidence status, the actual
serialized byte bound at **every** manifest publication, and deep snapshots of admission facts with
immutable returned views. No inherited case is renamed, deleted, weakened or reinterpreted, and no parent
allocation changes. Every frozen adversarial case `ARGUS2-ADV-01`–`ARGUS2-ADV-07` (`architecture.md` §11.1)
is bound to at least one exact pytest identifier in §7.13; those identifiers are frozen before any code is
written.

## 2. Frozen interface contract

The units are realized inside the additive `xverse.argus` package. The public surface is exactly the
`detailed-design.md` §14 surface; no unit introduces a signature, default, return shape or diagnostic code that
differs from it. The frozen surface is: `EvidenceDiagnostic`, `EvidenceError`, the frozen `EvidenceLimits`
dataclass, `EvidenceStore.open_run`/`read_run`, `EvidenceRun.append_event`/`import_observation`/`import_snapshot`/
`flush_buffer`/`finalize`/`abort`, `EvidenceReader.records`/`metric_inputs`/`export_json`/`export_jsonl`, and the
read-only `xverse-argus verify|export` console entry point with exit status 0/1/2.

Schema and version identities are frozen by `detailed-design.md` §2: `eventSchemaVersion = "1.0"`,
`manifestVersion = "1.0"`, `projectionVersion = "1.0"` with `upstreamContractVersion = "1.0.0"`,
`snapshotVersion = "1.0"`. A non-`1` major is rejected with `ARGUS2-SCHEMA-MAJOR-UNSUPPORTED`; unknown fields are
rejected outside `extensions` and preserved verbatim inside it. `EvidenceLimits` fields are the 11 positive
integers of `detailed-design.md` §10; a non-positive field raises `ValueError` at construction (a library
programming error, not an evidence diagnostic).

Two repair-level interface facts are frozen by `detailed-design.md` §8.5, §11.1 and §12.1/§12.2 and are
part of the contract specified here:

* **Reader I/O discipline.** Every read of `manifest.json`, the evidence stream and an indexed artifact
  resolves the confined real path and applies `os.lstat` **before** any open/parse, opens the confined
  regular file with `O_NOFOLLOW`, and streams it under the caller finite bounds (`max_manifest_bytes`,
  `max_event_bytes`, `max_events`, `max_read_records`, `max_diagnostic_count`). The caller-supplied read
  `limits` are authoritative; the manifest `limits` echo is recorded data only and can never relax a bound.
* **Recorded versus assessed status.** `EvidenceReader` exposes `recordedEvidenceStatus`/
  `recordedEvidenceReasons` (the manifest facts, echoed verbatim and labelled as recorded) separately from
  `assessedEvidenceStatus`/`assessedEvidenceReasons` (the reader's own conclusion from what it verified).
  The assessed value is the primary/exported completeness and the `verify` exit code is `0` only when
  `assessedEvidenceStatus == "complete"`.

All caller-admitted obligations, envelopes, source-byte digests, clocks and extensions are deep-snapshotted
at admission, and every public accessor returns an independent immutable/defensive copy, so post-admission
caller mutation cannot change an admitted fact, an indexed artifact identity or a returned view
(`detailed-design.md` §14.1).

## 3. State, concurrency and determinism

The package is a bounded, single-writer, offline pipeline. The writer owns the run root for its lifetime and
follows `new → open → closed` or `open → failed`; the reader is read-only, re-entrant and holds only a bounded
in-memory export buffer. There is no process, service, daemon, thread pool, retry loop, cache, network access or
background task. Serialization is canonical (sorted keys, compact separators, `allow_nan=False`), selection
order is ingestion-ordinal order, and clocks, identities, limits and obligations are caller inputs only.

The reader never materializes the whole run in memory: the manifest and event stream are read through a
confined `O_NOFOLLOW` descriptor under the caller bounds, and long/oversized inputs stop at the applicable
bound instead of amplifying memory or diagnostics. The writer publishes a manifest only through one
chokepoint that measures the actual canonical serialized bytes against `max_manifest_bytes` before the
atomic replace; the writer's own finalize/abort stream read uses the same bounded helper.

## 4. Invariants

| Invariant | Statement |
| --- | --- |
| `ARGUS2-INV-01` | A rejected append/import/recovery leaves the stream bytes and the writer state unchanged; no partial accepted record exists. |
| `ARGUS2-INV-02` | The verified semantic plan identity is never replaced by, inferred from, or rehashed as source-byte provenance. |
| `ARGUS2-INV-03` | The ingestion ordinal is a local, strictly increasing stream position; it is never presented as temporal or causal order. |
| `ARGUS2-INV-04` | No clock is read from the ambient environment and no unit is inferred; no cross-domain comparison, subtraction, sorting or conversion occurs. |
| `ARGUS2-INV-05` | Exactly one owning writer per run; an existing run root is never reused, reopened for writing or overwritten. |
| `ARGUS2-INV-06` | Stream closure and evidence completeness are independent; complete requires writerState closed, an intact stream and artifacts, every required obligation satisfied and empty reasons. |
| `ARGUS2-INV-07` | Every written or read artifact path is run-relative and confined, verified on the resolved real path; no write occurs outside the run root. |
| `ARGUS2-INV-08` | Payload visibility states never carry bytes their state forbids; bytes are never synthesized, padded or reconstructed from the source size. |
| `ARGUS2-INV-09` | Retention counters never substitute for interval closure; known loss, degradation and unclosed/unavailable intervals remain visible and cannot be upgraded to complete by finalization alone. |
| `ARGUS2-INV-10` | No ambient wall clock, random identity, remote lookup, locale or environment discovery is used; identities, clocks, units, limits and obligations are caller inputs. |
| `ARGUS2-INV-11` | Serialization is canonical (sorted keys, compact separators, allow_nan=False); repeated reads of unchanged inputs are byte-equal. |
| `ARGUS2-INV-12` | Unknown major schema versions are rejected; unknown fields are rejected outside extensions and preserved verbatim inside extensions. |
| `ARGUS2-INV-13` | Every diagnostic is emitted only on a real violation and carries a closed category and code. |
| `ARGUS2-INV-14` | Open-read and recovery never mutate, upgrade or rewrite original evidence bytes. |
| `ARGUS2-INV-15` | No control, actuation, provider-delivery, metric-computation, oracle, network or runtime-service authority is acquired. |
| `ARGUS2-INV-16` | The additive packaging preserves the xverse-xdl name, the xdl CLI and the accepted xverse_xdl/C++ contracts, and packages only the Argus package. |
| `ARGUS2-INV-17` | Every read resolves the confined real path and verifies regular-file/symlink status with `os.lstat` **before** any bytes are consumed; no unbounded `read()`/`read_bytes()` is applied to the manifest or evidence stream. |
| `ARGUS2-INV-18` | The caller-supplied read limits are authoritative; a damaged input's echoed `limits` is recorded data only and can never relax a bound (the effective bound is the stricter of the two). |
| `ARGUS2-INV-19` | The reader's assessed completeness is primary and independent of recorded manifest claims: corruption, truncation, loss, an unsupported version or a shape defect can never yield primary `complete`, and `verify` exits `0` only on assessed `complete`. |
| `ARGUS2-INV-20` | Every manifest publication measures the actual canonical serialized bytes against `max_manifest_bytes` before any replace; a bound or I/O failure preserves the prior manifest bytes and claims no `closed`/`complete` persistence. |
| `ARGUS2-INV-21` | Caller-supplied admitted objects are deep-snapshotted and no caller-owned mutable reference is retained; returned views cannot mutate internal admission facts or index artifact identity. |

## 5. Diagnostic catalogue (closed)

Every diagnostic carries `{code, category, severity, message, pointer?, path?, eventId?, remediation}`. The closed
code list below is frozen by this stage; no unit, implementation or later stage may emit a code outside it, and no
diagnostic is produced without a real violation.

| Category | Code | Emitted when |
| --- | --- | --- |
| `input-rejection` | `ARGUS2-INPUT-FIELD-INVALID` | A present field has a wrong type, pattern or a value outside a frozen closed set. |
| `input-rejection` | `ARGUS2-INPUT-IDENTITY-MISSING` | A required identity field is absent or empty. |
| `input-rejection` | `ARGUS2-INPUT-DUPLICATE-EVENT` | An event id already accepted in the same run. |
| `input-rejection` | `ARGUS2-INPUT-NONFINITE` | A numeric value is not finite or not representable. |
| `input-rejection` | `ARGUS2-INPUT-CLOCK-MISSING` | A declared clock domain or value is missing. |
| `input-rejection` | `ARGUS2-INPUT-UNIT-MISSING` | A clock value carries no caller-declared unit/representation. |
| `input-rejection` | `ARGUS2-INPUT-PROJECTION-INCOMPLETE` | The observation projection envelope or record omits required owned fields (including a gateway substitution). |
| `input-rejection` | `ARGUS2-INPUT-PAYLOAD-LENGTH` | Encoded visible bytes do not match the declared visible byte count. |
| `input-rejection` | `ARGUS2-INPUT-INTERVAL-INCOMPLETE` | An interval declared closed omits its start or end bound. |
| `input-rejection` | `ARGUS2-INPUT-AUTHORITY-MISSING` | A required caller-supplied authority value is absent. |
| `io-failure` | `ARGUS2-IO-FAILURE` | A filesystem or serialization operation failed. |
| `unsupported-schema` | `ARGUS2-SCHEMA-MAJOR-UNSUPPORTED` | The record/manifest/projection major version is not 1. |
| `unsupported-schema` | `ARGUS2-SCHEMA-UNKNOWN-FIELD` | An unknown key or closed-set value appears outside extensions. |
| `corrupt-artifact` | `ARGUS2-CORRUPT-STREAM-TRUNCATED` | The evidence stream ends in a truncated or non-canonical record. |
| `corrupt-artifact` | `ARGUS2-CORRUPT-ARTIFACT-HASH` | An indexed artifact content hash does not match the recorded value. |
| `corrupt-artifact` | `ARGUS2-CORRUPT-ARTIFACT-SIZE` | An indexed artifact byte size does not match the recorded value. |
| `corrupt-artifact` | `ARGUS2-CORRUPT-MANIFEST-SHAPE` | The manifest, or a frozen manifest member (`artifacts`/`obligations`/`metricInputs`/`eventStream`), has the wrong container/type on read. |
| `corrupt-artifact` | `ARGUS2-CORRUPT-EVENT` | An event line is not a JSON object, or a container/version/decode fault makes the record structurally invalid on read. |
| `corrupt-artifact` | `ARGUS2-CORRUPT-RECORD-SHAPE` | A frozen nested event member has the wrong type or key set on read. |
| `corrupt-artifact` | `ARGUS2-CORRUPT-RUN-ID-MISMATCH` | An event `runId` differs from the manifest `runId`. |
| `corrupt-artifact` | `ARGUS2-CORRUPT-DUPLICATE-EVENT` | A duplicate `eventId` occurs within one run on read. |
| `corrupt-artifact` | `ARGUS2-CORRUPT-ORDINAL` | A read `ingestionOrdinal` is not strictly increasing from `1` / has a gap. |
| `missing-evidence` | `ARGUS2-MISSING-ARTIFACT` | An indexed artifact does not exist. |
| `known-observation-loss` | `ARGUS2-LOSS-KNOWN-DROP` | An accepted observation or snapshot declares a drop or coalescing. |
| `known-observation-loss` | `ARGUS2-LOSS-DEGRADED-INTERVAL` | A snapshot declares a degraded validity state. |
| `known-observation-loss` | `ARGUS2-LOSS-INVALID-INTERVAL` | A snapshot declares an invalid validity state. |
| `bounds` | `ARGUS2-BOUND-EXCEEDED` | A caller-configured finite bound was exceeded; the field is named. |
| `path` | `ARGUS2-PATH-ESCAPE` | The resolved confined path lies outside the run root. |
| `path` | `ARGUS2-PATH-SYMLINK` | A path component is a symlink. |
| `path` | `ARGUS2-PATH-UNSAFE` | An artifact/run name is absolute, empty, or contains a forbidden character or segment. |
| `path` | `ARGUS2-PATH-NOT-REGULAR` | The confined artifact path is not a regular file. |
| `state` | `ARGUS2-STATE-RUN-EXISTS` | The run root already exists. |
| `state` | `ARGUS2-STATE-WRITER-CONFLICT` | A second owning writer was requested for the same run. |
| `state` | `ARGUS2-STATE-ILLEGAL-TRANSITION` | A writer-state transition other than the frozen machine was requested. |
| `clock` | `ARGUS2-CLOCK-UNRESOLVED` | A clock relation the caller did not declare remains unresolved. |
| `causal` | `ARGUS2-CAUSAL-UNRESOLVED` | A causation/correlation reference resolves to no accepted event. |
| `plan` | `ARGUS2-PLAN-DIGEST-MISMATCH` | The recorded and recomputed plan body digests differ. |
| `plan` | `ARGUS2-PLAN-VERSION-UNSUPPORTED` | An unsupported plan/Profile/API version was supplied. |
| `plan` | `ARGUS2-PLAN-ENVELOPE-CONFLICT` | The envelope identity conflicts with the declared run identity. |

Evidence reason codes are **manifest facts** in `manifest.evidenceReasons` (not diagnostics). Where a reader
surfaces one, it uses the mapped category:

| Reason code | Mapped category |
| --- | --- |
| `ARGUS2-REASON-TRUNCATED-STREAM` | `corrupt-artifact` |
| `ARGUS2-REASON-MISSING-ARTIFACT` | `missing-evidence` |
| `ARGUS2-REASON-MUTATED-ARTIFACT` | `corrupt-artifact` |
| `ARGUS2-REASON-UNMET-OBLIGATION` | `missing-evidence` |
| `ARGUS2-REASON-KNOWN-LOSS` | `known-observation-loss` |
| `ARGUS2-REASON-DEGRADED-INTERVAL` | `known-observation-loss` |
| `ARGUS2-REASON-INVALID-INTERVAL` | `known-observation-loss` |
| `ARGUS2-REASON-UNRESOLVED-CAUSATION` | `causal` |
| `ARGUS2-REASON-UNCLOSED-INTERVAL` | `known-observation-loss` |
| `ARGUS2-REASON-UNSUPPORTED-SCHEMA` | `unsupported-schema` |
| `ARGUS2-REASON-WRITER-STATE` | `state` |
| `ARGUS2-REASON-CORRUPT-MANIFEST` | `corrupt-artifact` |
| `ARGUS2-REASON-CORRUPT-EVENT` | `corrupt-artifact` |

The last two reason codes are assigned **only** to the reader's assessed reasons (§11.1 of
`detailed-design.md`); the writer never writes them into a manifest. `ARGUS2-REASON-CORRUPT-MANIFEST` /
`ARGUS2-REASON-CORRUPT-EVENT` are the assessed counterparts of the `ARGUS2-CORRUPT-MANIFEST-SHAPE` /
`ARGUS2-CORRUPT-EVENT` diagnostics, so a damaged container forces an assessed `incomplete` even when the
manifest recorded `complete`.

## 6. Unit inventory

| Unit | Owning component | Requirement | Cases | Planned test files |
| --- | --- | --- | --- | --- |
| `ARGUS2-SR-001-U` | `ARGUS2-SR-001-CMP` | `ARGUS2-SR-001` | 13 | `test_argus2_admission_unit.py` |
| `ARGUS2-SR-002-U` | `ARGUS2-SR-002-CMP` | `ARGUS2-SR-002` | 16 | `test_argus2_stream_unit.py` |
| `ARGUS2-SR-003-U` | `ARGUS2-SR-003-CMP` | `ARGUS2-SR-003` | 17 | `test_argus2_identity_unit.py` |
| `ARGUS2-SR-004-U` | `ARGUS2-SR-004-CMP` | `ARGUS2-SR-004` | 8 | `test_argus2_clocks_unit.py` |
| `ARGUS2-SR-005-U` | `ARGUS2-SR-005-CMP` | `ARGUS2-SR-005` | 19 | `test_argus2_bounds_unit.py`, `test_argus2_diagnostics_unit.py` |
| `ARGUS2-SR-006-U` | `ARGUS2-SR-006-CMP` | `ARGUS2-SR-006` | 15 | `test_argus2_writer_unit.py`, `test_argus2_recovery_unit.py` |
| `ARGUS2-SR-007-U` | `ARGUS2-SR-007-CMP` | `ARGUS2-SR-007` | 14 | `test_argus2_artifacts_unit.py` |
| `ARGUS2-SR-008-U` | `ARGUS2-SR-008-CMP` | `ARGUS2-SR-008` | 12 | `test_argus2_observation_unit.py` |
| `ARGUS2-SR-009-U` | `ARGUS2-SR-009-CMP` | `ARGUS2-SR-009` | 13 | `test_argus2_payload_unit.py` |
| `ARGUS2-SR-010-U` | `ARGUS2-SR-010-CMP` | `ARGUS2-SR-010` | 24 | `test_argus2_reader_unit.py` |
| `ARGUS2-SR-011-U` | `ARGUS2-SR-011-CMP` | `ARGUS2-SR-011` | 11 | `test_argus2_offline_unit.py` |
| `ARGUS2-SR-012-U` | `ARGUS2-SR-012-CMP` | `ARGUS2-SR-012` | 10 | `test_argus2_consumer_unit.py` |

Total: 172 exact identifiers (139 inherited + 33 terminal-review repair cases), all unique and well formed.

## 7. Unit case catalogue

Each `id` is the exact planned pytest node identifier. `precondition` describes the frozen starting state,
`stimulus` the single operation under test and `expected` the observable outcome (diagnostic code and/or state).
All cases use bounded neutral fixtures and temporary run roots; none contains a scientific protocol number.

### 7.1 `ARGUS2-SR-001-U` — Run admission and verified plan binding

**Owning component:** `ARGUS2-SR-001-CMP`; **requirement:** `ARGUS2-SR-001`; **invariants:** `ARGUS2-INV-02`, `ARGUS2-INV-05`, `ARGUS2-INV-10`, `ARGUS2-INV-13`.

| Case id | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/argus/test_argus2_admission_unit.py::test_fresh_run_opens_with_verified_plan_and_separated_provenance` | accepted resolved plan whose recorded digest matches its recomputed body digest; fresh empty run root; caller-supplied unique run id and source-byte digests | EvidenceStore.open_run(root, run_id=..., plan=plan, source_byte_digests={'scenario.xdl': <sha256>}) | exactly one run opened; run.run_id equals the caller value; manifest.plan.semanticDigest equals the plan body digest; manifest.sourceByteProvenance is a separate map and is not equal to or derived from the semantic digest |
| `tests/thesis_lite/argus/test_argus2_admission_unit.py::test_plan_digest_mutation_rejected` | plan body mutated after the recorded digest was computed | EvidenceStore.open_run(root, run_id=..., plan=mutated_plan) | rejected; ARGUS2-PLAN-DIGEST-MISMATCH; the run root is not created and nothing is overwritten |
| `tests/thesis_lite/argus/test_argus2_admission_unit.py::test_plan_matches_digest_api_is_reused_not_reimplemented` | accepted xverse_xdl.experiment_plan.plan_matches_digest patched to return False; otherwise valid plan | EvidenceStore.open_run(root, run_id=..., plan=plan) | rejected; ARGUS2-PLAN-DIGEST-MISMATCH; the decision follows the accepted public API and no private digest reimplementation is used |
| `tests/thesis_lite/argus/test_argus2_admission_unit.py::test_unsupported_plan_major_version_rejected` | resolved plan whose apiVersion/planVersion major is outside the accepted XDL v1alpha1/plan '1' contract | EvidenceStore.open_run(root, run_id=..., plan=unsupported_plan) | rejected; ARGUS2-PLAN-VERSION-UNSUPPORTED; no run root is created |
| `tests/thesis_lite/argus/test_argus2_admission_unit.py::test_envelope_run_id_conflict_rejected` | run_envelope.runId differing from the declared run id | EvidenceStore.open_run(root, run_id='run-a', plan=plan, run_envelope={'runId': 'run-b'}) | rejected; ARGUS2-PLAN-ENVELOPE-CONFLICT; no run root is created |
| `tests/thesis_lite/argus/test_argus2_admission_unit.py::test_existing_run_root_rejected_without_overwrite` | run root already exists containing a sentinel artifact | EvidenceStore.open_run(existing_root, run_id=..., plan=plan) | rejected; ARGUS2-STATE-RUN-EXISTS; the sentinel bytes are unchanged and no existing file is created or overwritten |
| `tests/thesis_lite/argus/test_argus2_admission_unit.py::test_unsafe_run_id_rejected` | run id failing the frozen identity pattern (empty, separator-laden or over max_id_length) | EvidenceStore.open_run(root, run_id='../escape', plan=plan) | rejected; ARGUS2-INPUT-FIELD-INVALID; no run root is created |
| `tests/thesis_lite/argus/test_argus2_admission_unit.py::test_open_records_accepted_api_profile_and_plan_versions` | accepted resolved plan carrying apiVersion, Profile version and plan version | EvidenceStore.open_run(root, run_id=..., plan=plan) | manifest.plan.apiVersion/profileVersion/planVersion equal the accepted declared values and are not inferred |
| `tests/thesis_lite/argus/test_argus2_admission_unit.py::test_source_byte_digests_never_substitute_semantic_identity` | source_byte_digests values chosen deliberately different from the semantic plan digest | EvidenceStore.open_run(root, run_id=..., plan=plan, source_byte_digests={'plan.src': <different sha256>}) | manifest.plan.semanticDigest still equals the accepted plan body digest; the differing source-byte value appears only under sourceByteProvenance |
| `tests/thesis_lite/argus/test_argus2_admission_unit.py::test_no_ambient_clock_or_random_identity_at_open` | identical caller inputs except the run root location; no caller clock supplied | EvidenceStore.open_run(root_a, ...); EvidenceStore.open_run(root_b, ...) | both manifests carry the identical caller run id and equal plan blocks; manifest.openedAt is absent; no random identity or wall-clock value appears |
| `tests/thesis_lite/argus/test_argus2_admission_unit.py::test_nested_obligation_detail_deep_snapshotted_against_caller_mutation` | an admitted required min-observations obligation whose nested detail.minimum is a caller-owned mutable value; a fresh run root | open_run(root, ..., obligations=obligations); then set obligations[0]['detail']['minimum'] = 0 and finalize() | the admitted obligation is an independent deep snapshot; its evaluated minimum is unchanged by the caller mutation and the mutation can neither lower nor drop the obligation (`ARGUS2-ADV-07`) |
| `tests/thesis_lite/argus/test_argus2_admission_unit.py::test_non_json_encodable_or_nonfinite_obligation_detail_rejected_at_admission` | an obligation whose nested detail carries a non-JSON-encodable object or a non-finite number | open_run(root, ..., obligations=[{'obligationId': 'o1', 'kind': 'min-observations', 'required': True, 'detail': {'minimum': float('nan')}}]) | rejected; ARGUS2-INPUT-FIELD-INVALID; no run root is created and no caller-owned object is retained (`ARGUS2-ADV-07`) |
| `tests/thesis_lite/argus/test_argus2_admission_unit.py::test_envelope_digests_clocks_and_extensions_deep_snapshotted` | caller-supplied run_envelope, source_byte_digests, clocks and extensions objects | open_run(...); mutate every caller object after admission; inspect the published manifest | the manifest records the admission-time snapshot; later caller mutation changes no admitted fact because no caller-owned reference is retained (`ARGUS2-ADV-07`) |

### 7.2 `ARGUS2-SR-002-U` — Versioned event stream and atomic run manifest

**Owning component:** `ARGUS2-SR-002-CMP`; **requirement:** `ARGUS2-SR-002`; **invariants:** `ARGUS2-INV-01`, `ARGUS2-INV-06`, `ARGUS2-INV-11`, `ARGUS2-INV-14`.

| Case id | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/argus/test_argus2_stream_unit.py::test_append_event_writes_one_canonical_jsonl_line` | an open run and one valid event | run.append_event(event_id='e1', producer_id='p1', event_kind='annotation', annotation={'text': 'n'}) | events.jsonl contains exactly one line terminated by a single \n; the line is canonical JSON (sorted keys, compact separators, allow_nan=False); eventCount is 1 |
| `tests/thesis_lite/argus/test_argus2_stream_unit.py::test_open_manifest_published_with_open_state_before_appends` | a freshly opened run | inspect root/manifest.json immediately after open_run | manifest.json parses; writerState is 'open'; evidenceStatus is 'unassessed'; eventStream bytes/sha256 equal the current events.jsonl |
| `tests/thesis_lite/argus/test_argus2_stream_unit.py::test_finalize_satisfied_obligations_publishes_complete_manifest` | a run whose declared required obligations are all satisfied and whose indexed artifacts verify | run.finalize() | manifest.writerState is 'closed'; evidenceStatus is 'complete'; evidenceReasons is empty; artifact index, byte sizes and content hashes verify against the stream |
| `tests/thesis_lite/argus/test_argus2_stream_unit.py::test_finalize_unmet_required_obligation_classified_incomplete` | a run with a required causal-closure obligation left unmet | run.finalize() | writerState is 'closed'; evidenceStatus is 'incomplete'; evidenceReasons contains ARGUS2-REASON-UNMET-OBLIGATION and ARGUS2-REASON-UNRESOLVED-CAUSATION |
| `tests/thesis_lite/argus/test_argus2_stream_unit.py::test_closed_stream_with_missing_artifact_classified_incomplete` | an indexed artifact deleted after finalize began | run.finalize() | evidenceStatus is 'incomplete'; evidenceReasons contains ARGUS2-REASON-MISSING-ARTIFACT; a diagnostic with code ARGUS2-MISSING-ARTIFACT is reported |
| `tests/thesis_lite/argus/test_argus2_stream_unit.py::test_truncated_last_record_classified_incomplete` | the final JSONL line left without its terminating newline | run.finalize() then EvidenceStore.read_run(root) | ARGUS2-CORRUPT-STREAM-TRUNCATED; evidenceReasons contains ARGUS2-REASON-TRUNCATED-STREAM; evidenceStatus stays 'incomplete'; the truncated record is not counted as an accepted event |
| `tests/thesis_lite/argus/test_argus2_stream_unit.py::test_known_loss_never_upgraded_to_complete_by_finalize` | an imported observation whose counters.dropped is greater than zero | run.finalize() | evidenceStatus is 'incomplete'; evidenceReasons contains ARGUS2-REASON-KNOWN-LOSS; finalization alone never yields 'complete' |
| `tests/thesis_lite/argus/test_argus2_stream_unit.py::test_stream_closure_and_evidence_completeness_are_separate_facts` | an incomplete run finalized cleanly | run.finalize() | writerState is 'closed' while evidenceStatus is 'incomplete'; both facts are reported independently and no success, validity or readiness claim follows |
| `tests/thesis_lite/argus/test_argus2_stream_unit.py::test_artifact_index_entry_carries_frozen_fields` | a run that records one owned artifact | inspect manifest.artifacts[0] | entry carries run-relative path, mediaType, schemaVersion, integer bytes, lowercase sha256 and role; entries are unique by path |
| `tests/thesis_lite/argus/test_argus2_stream_unit.py::test_event_count_and_stream_hash_match_file_on_finalize` | a run with several appended events | run.finalize() | manifest.eventCount equals the accepted line count; eventStream.bytes equals the file size; eventStream.sha256 equals the recomputed SHA-256 |
| `tests/thesis_lite/argus/test_argus2_stream_unit.py::test_unsupported_manifest_major_version_rejected_on_read` | a manifest whose schemaVersion major is not 1 | EvidenceStore.read_run(root) | ARGUS2-SCHEMA-MAJOR-UNSUPPORTED with a bounded partial result; the original manifest bytes are unchanged |
| `tests/thesis_lite/argus/test_argus2_stream_unit.py::test_extensions_namespaces_are_preserved_verbatim` | an event carrying extensions {'argus.note': {...}} | append then EvidenceReader.export_json() | the unknown extensions namespace is echoed verbatim and never interpreted, and it does not affect status, ordering or obligations |
| `tests/thesis_lite/argus/test_argus2_stream_unit.py::test_reader_exposes_recorded_and_assessed_status_separately` | an intact finalized run whose manifest recorded evidenceStatus 'complete' | EvidenceStore.read_run(root) and EvidenceReader.export_json() | recordedEvidenceStatus/recordedEvidenceReasons echo the manifest verbatim, assessedEvidenceStatus/assessedEvidenceReasons are computed by the reader and reported as the primary status, and the two are never conflated (`ARGUS2-ADV-03`) |
| `tests/thesis_lite/argus/test_argus2_stream_unit.py::test_manifest_recorded_complete_with_corrupt_stream_assessed_incomplete` | a manifest that recorded 'complete' whose stream tail was truncated after finalize | EvidenceStore.read_run(root); export_json() | recorded status stays 'complete' only as a recorded fact while assessedEvidenceStatus is 'incomplete' with ARGUS2-REASON-TRUNCATED-STREAM/ARGUS2-REASON-CORRUPT-EVENT; the export never presents primary complete (`ARGUS2-ADV-03`) |
| `tests/thesis_lite/argus/test_argus2_stream_unit.py::test_corrupt_manifest_never_exported_as_primary_complete` | a structurally invalid manifest (or one with a wrong-typed frozen member) that also claims 'complete' | EvidenceStore.read_run(root); export_json() | assessedEvidenceStatus is 'incomplete' with ARGUS2-REASON-CORRUPT-MANIFEST; recorded claims are carried only as recorded facts and the primary status is never complete (`ARGUS2-ADV-03`) |
| `tests/thesis_lite/argus/test_argus2_stream_unit.py::test_manifest_bound_measured_on_actual_serialized_bytes_at_open_finalize_and_abort` | a caller max_manifest_bytes sized so the open manifest fits but the finalize manifest (artifact index, obligations and finalized metadata) exceeds it | open_run; append/record; run.finalize() | the finalize publication is refused with ARGUS2-BOUND-EXCEEDED naming max_manifest_bytes; the prior open manifest bytes remain on disk; the writer does not report 'closed'/'complete' (`ARGUS2-ADV-06`) |

### 7.3 `ARGUS2-SR-003-U` — Event identity, producer sequence and causal references

**Owning component:** `ARGUS2-SR-003-CMP`; **requirement:** `ARGUS2-SR-003`; **invariants:** `ARGUS2-INV-01`, `ARGUS2-INV-03`, `ARGUS2-INV-11`, `ARGUS2-INV-12`.

| Case id | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_valid_event_persists_all_declared_identity_fields` | an open run and a fully declared event | run.append_event(event_id='e7', producer_id='p7', event_kind='annotation', producer_sequence=3, correlation_id='c7', causation_id='e6', annotation={'text': 'n'}) | one accepted record with schemaVersion '1.0', runId, eventId, producerId, ingestionOrdinal, eventKind and every declared optional field preserved exactly |
| `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_ingestion_ordinal_follows_append_order_not_clock_order` | three appended events whose caller clock values descend | append e1, e2, e3 then read | ingestionOrdinal is 1, 2, 3 in append order; the reader returns records in ordinal order and never reorders by clock value |
| `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_duplicate_event_identity_rejected_without_partial_record` | an event id already accepted in the same run | run.append_event(event_id='e1', producer_id='p1', event_kind='annotation') | rejected; ARGUS2-INPUT-DUPLICATE-EVENT; no second JSONL line is written and the writer state and stream bytes are unchanged |
| `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_missing_required_identity_field_rejected` | an append whose run id, event id or producer id is absent or empty | run.append_event(event_id='', producer_id='p1', event_kind='annotation') | rejected; ARGUS2-INPUT-IDENTITY-MISSING; no partial accepted record is retained |
| `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_unknown_event_schema_major_version_rejected` | a persisted JSONL line carrying schemaVersion '2.0' | EvidenceStore.read_run(root) | ARGUS2-SCHEMA-MAJOR-UNSUPPORTED; the line is not silently accepted, upgraded or dropped |
| `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_causation_reference_indexed_without_invention` | event e2 declaring causationId equal to the accepted event id e1 and a required causal-closure obligation | run.append_event(... e2 ...); run.finalize() | the reference resolves to the accepted event id; the causal-closure obligation is satisfied; the index holds no invented predecessor |
| `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_unresolved_causation_remains_visible` | event e2 declaring causationId 'e9' which was never appended | run.append_event(... e2 ...); run.finalize() | ARGUS2-CAUSAL-UNRESOLVED reported; evidenceReasons contains ARGUS2-REASON-UNRESOLVED-CAUSATION; the missing predecessor is never repaired or invented |
| `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_unknown_event_kind_rejected` | an event kind outside the closed set | run.append_event(event_id='e1', producer_id='p1', event_kind='telemetry') | rejected; ARGUS2-INPUT-FIELD-INVALID; no line is written |
| `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_caller_may_not_append_writer_emitted_kind` | an event kind reserved for the writer | run.append_event(event_id='e1', producer_id='p1', event_kind='run-opened') | rejected; ARGUS2-INPUT-FIELD-INVALID; the writer-emitted kinds remain writer-only |
| `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_annotation_text_bound_enforced` | annotation text longer than the caller max_text_length | run.append_event(event_id='e1', producer_id='p1', event_kind='annotation', annotation={'text': 'x' * (max_text_length + 1)}) | rejected; ARGUS2-BOUND-EXCEEDED naming max_text_length; no line is written |
| `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_unknown_top_level_field_rejected` | a raw JSONL line carrying an additional key outside extensions | EvidenceStore.read_run(root) | ARGUS2-SCHEMA-UNKNOWN-FIELD; the unknown key is neither silently ignored nor discarded |
| `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_producer_sequence_is_not_used_for_ordering` | events appended with producer_sequence values out of append order | append e1(seq=5), e2(seq=1), e3(seq=3) then read | records are returned in ingestion-ordinal order and the declared producer sequences are preserved unchanged and never presented as temporal or causal order |
| `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_reader_rejects_event_missing_required_identity` | a persisted stream line whose event omits runId, eventId or producerId | EvidenceStore.read_run(root) | ARGUS2-INPUT-IDENTITY-MISSING; the record is excluded from the trusted result and the run is assessed incomplete; no TypeError/KeyError escapes the reader (`ARGUS2-ADV-04`) |
| `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_reader_rejects_duplicate_event_id_within_run` | a stream carrying the same eventId twice within one run | EvidenceStore.read_run(root) | ARGUS2-CORRUPT-DUPLICATE-EVENT; the duplicate is excluded from the trusted result and the run is assessed incomplete (`ARGUS2-ADV-04`) |
| `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_reader_rejects_nonmonotonic_ingestion_ordinal` | a stream whose ingestionOrdinal repeats, skips a value or does not start at 1 | EvidenceStore.read_run(root) | ARGUS2-CORRUPT-ORDINAL; the out-of-sequence record is excluded and the ordinal is never presented as temporal or causal order (`ARGUS2-ADV-04`) |
| `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_reader_rejects_event_runid_mismatch_with_manifest` | a stream event whose runId differs from the manifest runId | EvidenceStore.read_run(root) | ARGUS2-CORRUPT-RUN-ID-MISMATCH; the mismatched record is excluded and the run is assessed incomplete (`ARGUS2-ADV-04`) |
| `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_reader_rejects_nonfinite_clock_value_on_read` | a persisted stream clock value of NaN/Infinity, or a non-numeric clock value | EvidenceStore.read_run(root) | ARGUS2-INPUT-NONFINITE (or ARGUS2-CLOCK-UNRESOLVED for a non-numeric clock); the value never enters the trusted result and no uncaught ValueError escapes (`ARGUS2-ADV-04`) |

### 7.4 `ARGUS2-SR-004-U` — Explicit source and observation clock domains

**Owning component:** `ARGUS2-SR-004-CMP`; **requirement:** `ARGUS2-SR-004`; **invariants:** `ARGUS2-INV-04`, `ARGUS2-INV-10`.

| Case id | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/argus/test_argus2_clocks_unit.py::test_source_and_observation_clocks_stored_with_declared_units` | an imported observation declaring distinct source and observation clock domains and caller units | run.import_observation(projection); EvidenceStore.read_run(root) | both clock values reconstruct with their exact domain, unit and value, unchanged by the read |
| `tests/thesis_lite/argus/test_argus2_clocks_unit.py::test_clock_value_without_domain_rejected` | a clock value object with no domain identity | run.append_event(..., clocks={'source': {'unit': 'ns', 'value': 1}}) | rejected; ARGUS2-INPUT-CLOCK-MISSING; the value is not defaulted to an implicit domain |
| `tests/thesis_lite/argus/test_argus2_clocks_unit.py::test_clock_value_without_unit_rejected` | a clock value object with a domain but no declared unit/representation | run.append_event(..., clocks={'source': {'domain': 'd1', 'value': 1}}) | rejected; ARGUS2-INPUT-UNIT-MISSING; no unit is inferred |
| `tests/thesis_lite/argus/test_argus2_clocks_unit.py::test_nonfinite_clock_value_rejected` | a clock value of NaN or Infinity | run.append_event(..., clocks={'source': {'domain': 'd1', 'unit': 'ns', 'value': float('nan')}}) | rejected; ARGUS2-INPUT-NONFINITE; allow_nan=False canonical serialization is never bypassed |
| `tests/thesis_lite/argus/test_argus2_clocks_unit.py::test_no_cross_domain_conversion_or_sorting` | two records whose source and observation domains differ in unit and magnitude | read_run(root) | records are returned in ingestion-ordinal order; neither timestamp is rescaled, subtracted, compared or sorted across domains |
| `tests/thesis_lite/argus/test_argus2_clocks_unit.py::test_undeclared_clock_mapping_reported_unresolved` | a record requiring a clock mapping the caller did not declare | run.finalize() then EvidenceStore.read_run(root) | ARGUS2-CLOCK-UNRESOLVED reported; the unmapped relation stays explicit and is never inferred |
| `tests/thesis_lite/argus/test_argus2_clocks_unit.py::test_observation_event_requires_declared_clocks` | an observation-kind event appended with no clocks | run.append_event(event_id='e1', producer_id='p1', event_kind='observation', observation=<valid projection record>) | rejected; ARGUS2-INPUT-CLOCK-MISSING; absent means not declared and is never inferred |
| `tests/thesis_lite/argus/test_argus2_clocks_unit.py::test_missing_opened_at_clock_is_absent_not_ambient` | open_run called with no caller clock | inspect manifest.openedAt | openedAt is absent (never an ambient wall-clock value); when the caller supplies a clock it is stored verbatim |

### 7.5 `ARGUS2-SR-005-U` — Fail-closed validation and caller-configured finite bounds

**Owning component:** `ARGUS2-SR-005-CMP`; **requirement:** `ARGUS2-SR-005`; **invariants:** `ARGUS2-INV-01`, `ARGUS2-INV-12`, `ARGUS2-INV-13`.

| Case id | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/argus/test_argus2_bounds_unit.py::test_evidence_limits_requires_positive_integers` | an EvidenceLimits field set to 0 or a negative value | EvidenceLimits(max_event_bytes=0, ...) | ValueError raised at construction (library programming error, not an evidence diagnostic); no run is created |
| `tests/thesis_lite/argus/test_argus2_bounds_unit.py::test_max_event_bytes_at_bound_accepted_and_over_rejected` | one canonical event exactly at max_event_bytes and one one byte larger | append the at-bound event, then the over-bound event | the at-bound event is accepted with no diagnostic; the over-bound event is rejected with ARGUS2-BOUND-EXCEEDED naming max_event_bytes and no line is written |
| `tests/thesis_lite/argus/test_argus2_bounds_unit.py::test_max_events_at_bound_accepted_and_over_rejected` | max_events accepted events then one more | append max_events events, then one additional event | the run accepts exactly max_events events; the additional append is rejected with ARGUS2-BOUND-EXCEEDED naming max_events |
| `tests/thesis_lite/argus/test_argus2_bounds_unit.py::test_max_id_length_at_bound_accepted_and_over_rejected` | an event id exactly at max_id_length and one character longer | append both events | the at-bound id is accepted; the over-bound id is rejected with ARGUS2-BOUND-EXCEEDED naming max_id_length |
| `tests/thesis_lite/argus/test_argus2_bounds_unit.py::test_max_text_length_at_bound_accepted_and_over_rejected` | annotation text exactly at max_text_length and one character longer | append both events | the at-bound text is accepted; the over-bound text is rejected with ARGUS2-BOUND-EXCEEDED naming max_text_length |
| `tests/thesis_lite/argus/test_argus2_bounds_unit.py::test_max_payload_bytes_at_bound_accepted_and_over_rejected` | an observation whose visible bytes equal max_payload_bytes and one whose visible bytes exceed it | import both projections | the at-bound observation is accepted; the over-bound observation is rejected with ARGUS2-BOUND-EXCEEDED naming max_payload_bytes |
| `tests/thesis_lite/argus/test_argus2_bounds_unit.py::test_max_artifacts_at_bound_accepted_and_over_rejected` | an artifact index exactly at max_artifacts and one entry more | record the at-bound set, then one additional artifact | the at-bound index is accepted; the additional entry is rejected with ARGUS2-BOUND-EXCEEDED naming max_artifacts |
| `tests/thesis_lite/argus/test_argus2_bounds_unit.py::test_max_obligations_at_bound_accepted_and_over_rejected` | a declared obligation set exactly at max_obligations and one obligation more | open_run with the at-bound set, then with one additional obligation | the at-bound set is accepted; the additional obligation is rejected with ARGUS2-BOUND-EXCEEDED naming max_obligations |
| `tests/thesis_lite/argus/test_argus2_bounds_unit.py::test_max_diagnostic_count_bounds_returned_diagnostics` | an input violating more distinct rules than max_diagnostic_count | trigger the violations and count reported diagnostics | the returned diagnostics list length is at most max_diagnostic_count; no unbounded diagnostic list is produced |
| `tests/thesis_lite/argus/test_argus2_bounds_unit.py::test_max_manifest_bytes_at_bound_accepted_and_over_rejected` | a manifest exactly at max_manifest_bytes and one whose canonical bytes exceed it | open_run under both limits | the at-bound manifest is published; the over-bound manifest is rejected with ARGUS2-BOUND-EXCEEDED naming max_manifest_bytes and no run is opened |
| `tests/thesis_lite/argus/test_argus2_bounds_unit.py::test_max_causal_index_entries_at_bound_accepted_and_over_rejected` | distinct causal references exactly at max_causal_index_entries and one reference more | append the at-bound set, then one additional distinct reference | the at-bound index is accepted; the additional entry is rejected with ARGUS2-BOUND-EXCEEDED naming max_causal_index_entries |
| `tests/thesis_lite/argus/test_argus2_bounds_unit.py::test_max_read_records_bounds_reader_result` | a run holding more accepted records than max_read_records | EvidenceStore.read_run(root, limits=...).records() | at most max_read_records records are returned, ARGUS2-BOUND-EXCEEDED is reported and the result is a bounded partial result rather than silent truncation |
| `tests/thesis_lite/argus/test_argus2_bounds_unit.py::test_each_exceeded_bound_produces_exactly_one_diagnostic` | one value violating exactly one declared bound | append/import the value | exactly one ARGUS2-BOUND-EXCEEDED diagnostic naming that field; no diagnostic is produced without an actual violation |
| `tests/thesis_lite/argus/test_argus2_bounds_unit.py::test_nonfinite_value_rejected_not_truncated` | a payload or clock number that is NaN or Infinity | append/import the value | rejected; ARGUS2-INPUT-NONFINITE; the value is never truncated, rounded or repaired |
| `tests/thesis_lite/argus/test_argus2_diagnostics_unit.py::test_diagnostic_categories_are_distinguishable` | one input defect per required diagnostic category | trigger each defect and collect the reported diagnostics | the six required categories (input-rejection, io-failure, unsupported-schema, corrupt-artifact, missing-evidence, known-observation-loss) are present, each diagnostic carries a code whose family prefix matches its category and no two categories share a code |
| `tests/thesis_lite/argus/test_argus2_diagnostics_unit.py::test_no_diagnostic_without_actual_violation` | a valid run inside every declared bound | open, append, import, finalize and read | diagnostics is empty; no diagnostic code is emitted without an actual violation |
| `tests/thesis_lite/argus/test_argus2_bounds_unit.py::test_max_diagnostic_count_caps_damaged_input_diagnostics` | a damaged input (many malformed lines and unknown keys) violating more rules than the caller max_diagnostic_count | EvidenceStore.read_run(root, limits=limits) | at most max_diagnostic_count diagnostics are returned and a single ARGUS2-BOUND-EXCEEDED naming max_diagnostic_count records the cap; damaged input cannot amplify diagnostics without limit (`ARGUS2-ADV-02`) |
| `tests/thesis_lite/argus/test_argus2_diagnostics_unit.py::test_truncated_json_and_unknown_nested_key_yield_stable_bounded_diagnostics` | an event line that is truncated JSON and another carrying an unknown nested key outside extensions | EvidenceStore.read_run(root) | bounded stable categorized diagnostics (corrupt-event / unknown-field) are returned as data; no TypeError, ValueError or json.JSONDecodeError escapes the reader or the CLI (`ARGUS2-ADV-05`) |
| `tests/thesis_lite/argus/test_argus2_diagnostics_unit.py::test_no_uncaught_typeerror_or_valueerror_from_malformed_input` | a matrix of malformed containers, wrong-typed members and unsupported version text across the manifest and event lines | EvidenceStore.read_run(root) and the CLI verify/export paths | every case returns an assessed-incomplete bounded result with a stable diagnostic from the closed catalogue; no exception type escapes the reader or CLI (`ARGUS2-ADV-05`) |

### 7.6 `ARGUS2-SR-006-U` — Single-writer state, durability and non-mutating recovery

**Owning component:** `ARGUS2-SR-006-CMP`; **requirement:** `ARGUS2-SR-006`; **invariants:** `ARGUS2-INV-05`, `ARGUS2-INV-06`, `ARGUS2-INV-14`.

| Case id | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/argus/test_argus2_writer_unit.py::test_writer_state_transitions_from_open_to_closed` | a freshly opened run that finalizes cleanly | read run.writer_state before and after finalize() | writer_state is 'open' before finalize and 'closed' after; no other transition occurs |
| `tests/thesis_lite/argus/test_argus2_writer_unit.py::test_append_after_finalize_is_illegal_transition` | a finalized run | run.append_event(event_id='e1', producer_id='p1', event_kind='annotation') | ARGUS2-STATE-ILLEGAL-TRANSITION; the closed stream and manifest are unchanged |
| `tests/thesis_lite/argus/test_argus2_writer_unit.py::test_second_in_process_writer_for_same_run_conflict` | an open run and a second writer opened on the same run root | EvidenceStore.open_run(root, run_id=..., plan=plan) a second time | ARGUS2-STATE-WRITER-CONFLICT; only one owning writer holds the run |
| `tests/thesis_lite/argus/test_argus2_writer_unit.py::test_existing_run_root_rejected_before_any_write` | a pre-existing run root | open_run(existing_root, ...) | ARGUS2-STATE-RUN-EXISTS; no new file is created inside or outside the root |
| `tests/thesis_lite/argus/test_argus2_writer_unit.py::test_flush_buffer_is_the_appended_line_durability_point` | appended events not yet flushed | run.flush_buffer() then inspect events.jsonl on disk | the appended lines are present on disk after the documented flush+fsync point; flush_buffer is recorded as the only appended-line durability boundary |
| `tests/thesis_lite/argus/test_argus2_writer_unit.py::test_finalize_replaces_manifest_atomically_without_residue` | a run finalized normally | run.finalize() then inspect the run root | manifest.json is the complete closed manifest, no manifest.json.tmp-* residue remains and the stream is internally consistent |
| `tests/thesis_lite/argus/test_argus2_writer_unit.py::test_interrupted_finalize_publishes_failed_state` | os.replace patched to raise during the finalize manifest replacement | run.finalize() | writer_state becomes 'failed'; the previous manifest bytes remain; a diagnostic ARGUS2-IO-FAILURE is reported; the stream bytes are unchanged |
| `tests/thesis_lite/argus/test_argus2_writer_unit.py::test_abort_publishes_failed_state_and_best_effort_event` | an open run aborted by the caller | run.abort(reason='caller-stop') | writerState is 'failed'; a best-effort run-failed record is appended when the stream is usable; evidenceStatus is not 'complete' |
| `tests/thesis_lite/argus/test_argus2_recovery_unit.py::test_truncated_last_jsonl_record_detected_without_recount` | the trailing newline removed from the last JSONL line | EvidenceStore.read_run(root) | ARGUS2-CORRUPT-STREAM-TRUNCATED; the damaged line is not counted as an accepted event and is never repaired |
| `tests/thesis_lite/argus/test_argus2_recovery_unit.py::test_recovery_reads_a_bounded_prefix_and_writes_nothing` | a run root containing a truncated tail and several valid records | EvidenceStore.read_run(root) | valid records up to the damage are returned, the damage is reported, and every original file byte (stream and manifest) is unchanged after the read |
| `tests/thesis_lite/argus/test_argus2_writer_unit.py::test_reopen_for_writing_is_refused` | a finalized run root | EvidenceStore.open_run(root, run_id=..., plan=plan) | ARGUS2-STATE-RUN-EXISTS; the reader path remains the only re-open and it is read-only |
| `tests/thesis_lite/argus/test_argus2_writer_unit.py::test_only_manifest_and_stream_are_written_by_the_writer` | an open run with appended events | enumerate the run root after flush_buffer | only the versioned JSONL stream and the JSON manifest are created by the writer; no lock file, database, temporary residue or index is left behind |
| `tests/thesis_lite/argus/test_argus2_recovery_unit.py::test_recovery_uses_nofollow_and_bounded_reads_without_unbounded_read` | a stream/manifest path that is a symlink, and a stream larger than the caller event bound | recovery helper and EvidenceStore.read_run under the caller limits | the symlink is rejected before I/O with ARGUS2-PATH-SYMLINK and the oversized stream with ARGUS2-BOUND-EXCEEDED naming max_event_bytes/max_events; no unbounded read()/read_bytes() of the stream occurs (`ARGUS2-ADV-01`, `ARGUS2-ADV-02`) |
| `tests/thesis_lite/argus/test_argus2_writer_unit.py::test_finalize_manifest_bound_exceeded_preserves_prior_manifest` | an open run with a valid open manifest and a caller max_manifest_bytes such that the closed manifest (with artifact index, obligations and finalized metadata) exceeds it | run.finalize() | ARGUS2-BOUND-EXCEEDED naming max_manifest_bytes; the on-disk manifest bytes remain the prior open manifest; the writer is not reported 'closed' and no complete persistence is claimed (`ARGUS2-ADV-06`) |
| `tests/thesis_lite/argus/test_argus2_writer_unit.py::test_abort_manifest_bound_exceeded_preserves_prior_manifest` | an open run and a caller max_manifest_bytes such that the abort/failed manifest exceeds it | run.abort(reason='caller-stop') | ARGUS2-BOUND-EXCEEDED naming max_manifest_bytes; the prior manifest bytes remain and no closed/complete claim is made (`ARGUS2-ADV-06`) |

### 7.7 `ARGUS2-SR-007-U` — Confined artifacts, safe run-relative paths and integrity verification

**Owning component:** `ARGUS2-SR-007-CMP`; **requirement:** `ARGUS2-SR-007`; **invariants:** `ARGUS2-INV-07`, `ARGUS2-INV-14`.

| Case id | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/argus/test_argus2_artifacts_unit.py::test_safe_run_relative_artifact_paths_are_indexed` | a recorded artifact with a safe run-relative POSIX path | inspect the manifest artifact index entry | the entry carries a safe run-relative path, mediaType, schemaVersion, integer bytes, sha256 and role and re-verifies on read |
| `tests/thesis_lite/argus/test_argus2_artifacts_unit.py::test_traversal_segment_rejected` | an artifact path containing a '..' segment | record the artifact | rejected; ARGUS2-PATH-ESCAPE; no file is created outside the run root |
| `tests/thesis_lite/argus/test_argus2_artifacts_unit.py::test_absolute_artifact_path_rejected` | an absolute artifact path | record the artifact | rejected; ARGUS2-PATH-UNSAFE; no file is created outside the run root |
| `tests/thesis_lite/argus/test_argus2_artifacts_unit.py::test_unsafe_artifact_name_rejected` | an artifact name containing a backslash, NUL, empty segment or a character outside the frozen pattern | record the artifact | rejected; ARGUS2-PATH-UNSAFE; nothing is written |
| `tests/thesis_lite/argus/test_argus2_artifacts_unit.py::test_escaping_symlink_rejected` | an artifact path whose parent or final component is a symlink resolving outside the run root | record the artifact | rejected; ARGUS2-PATH-SYMLINK; the link target is never followed and nothing outside the run root is written |
| `tests/thesis_lite/argus/test_argus2_artifacts_unit.py::test_symlink_resolving_inside_run_root_still_rejected` | an artifact path whose final component is a symlink resolving inside the run root | record the artifact | rejected; ARGUS2-PATH-SYMLINK; symlinks are rejected regardless of resolution target and the check uses the confined real path, not caller text |
| `tests/thesis_lite/argus/test_argus2_artifacts_unit.py::test_non_regular_file_rejected` | an artifact path occupied by a directory or special file | record the artifact | rejected; ARGUS2-PATH-NOT-REGULAR; nothing is written |
| `tests/thesis_lite/argus/test_argus2_artifacts_unit.py::test_missing_indexed_artifact_reported` | an indexed artifact deleted after indexing | EvidenceStore.read_run(root) | ARGUS2-MISSING-ARTIFACT reported and the evidence is classified incomplete; the missing file is never created |
| `tests/thesis_lite/argus/test_argus2_artifacts_unit.py::test_byte_mutated_artifact_hash_mismatch` | an indexed artifact whose bytes were changed without changing its size | EvidenceStore.read_run(root) | ARGUS2-CORRUPT-ARTIFACT-HASH reported; the recorded content hash is not updated |
| `tests/thesis_lite/argus/test_argus2_artifacts_unit.py::test_size_mutated_artifact_size_mismatch` | an indexed artifact whose byte length changed | EvidenceStore.read_run(root) | ARGUS2-CORRUPT-ARTIFACT-SIZE reported; the recorded size is not updated |
| `tests/thesis_lite/argus/test_argus2_artifacts_unit.py::test_no_write_occurs_outside_the_run_root` | a sequence of rejected traversal, absolute and symlink artifact attempts | attempt each unsafe artifact record, then enumerate the parent directory | each attempt is rejected and no file or directory is created outside the run root |
| `tests/thesis_lite/argus/test_argus2_artifacts_unit.py::test_artifact_reverification_is_read_only` | an intact finalized run | EvidenceStore.read_run(root) twice | both reads verify the same recorded size/hash and leave every file byte unchanged |
| `tests/thesis_lite/argus/test_argus2_artifacts_unit.py::test_mutating_returned_artifact_view_cannot_rewrite_indexed_hash` | a recorded artifact whose index entry is returned to the caller | record_artifact(...); mutate the returned dict (path/bytes/sha256/role) and any nested value; re-read the manifest | the indexed artifact identity (bytes/sha256/role) is unchanged because the returned view is an independent defensive copy and the identity is internally owned (`ARGUS2-ADV-07`) |
| `tests/thesis_lite/argus/test_argus2_artifacts_unit.py::test_reader_artifact_path_confinement_checked_before_read` | an indexed artifact path that is a symlink or resolves outside the run root | EvidenceStore.read_run(root) | rejected before I/O with ARGUS2-PATH-SYMLINK / ARGUS2-PATH-ESCAPE; no bytes are read from the link target and no file is created (`ARGUS2-ADV-01`) |

### 7.8 `ARGUS2-SR-008-U` — X-COM owned observation projection import

**Owning component:** `ARGUS2-SR-008-CMP`; **requirement:** `ARGUS2-SR-008`; **invariants:** `ARGUS2-INV-08`, `ARGUS2-INV-15`.

| Case id | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/argus/test_argus2_observation_unit.py::test_real_owned_projection_preserves_every_accessor_value` | a versioned projection serialized by the real owned C++ producer fixture over accepted X-COM headers | run.import_observation(projection) then read back | every mapped accessor value (contract/interface/endpoint/schema ids and versions, interaction, origin, clocks, sequence, correlations, route/provider, source payload size, provider outcome, payload view/schema state, visible bytes, tap id, counters) is preserved by value |
| `tests/thesis_lite/argus/test_argus2_observation_unit.py::test_projection_requires_upstream_contract_identity` | a projection envelope omitting projectionVersion/upstreamContractVersion | run.import_observation(projection) | rejected; ARGUS2-INPUT-PROJECTION-INCOMPLETE; no record is appended |
| `tests/thesis_lite/argus/test_argus2_observation_unit.py::test_unknown_projection_major_version_rejected` | a projection whose projectionVersion major is not 1 | run.import_observation(projection) | rejected; ARGUS2-SCHEMA-MAJOR-UNSUPPORTED; no record is appended |
| `tests/thesis_lite/argus/test_argus2_observation_unit.py::test_narrower_gateway_record_rejected_as_full_projection` | a gateway-shaped observation record carrying only the narrower protobuf field set | run.import_observation(gateway_shaped_projection) | rejected; ARGUS2-INPUT-PROJECTION-INCOMPLETE, unless an explicitly versioned separate mapping records each missing field as unavailable; missing metadata is never fabricated |
| `tests/thesis_lite/argus/test_argus2_observation_unit.py::test_import_exposes_no_callback_hub_or_delivery_authority` | an imported observation run | inspect the run object and module surface | no callback, mutable hub handle, provider handle, tap handle or delivery method is reachable; import only copies immutable values |
| `tests/thesis_lite/argus/test_argus2_observation_unit.py::test_provider_outcome_is_not_promoted_to_experiment_validity` | an imported observation with providerOutcome 'accepted' | run.finalize() | the provider outcome is stored verbatim and does not by itself change evidenceStatus or create any experiment-validity claim |
| `tests/thesis_lite/argus/test_argus2_observation_unit.py::test_visible_byte_count_mismatch_rejected` | a projection whose visibleBytesHex decodes to a byte count other than visibleByteCount | run.import_observation(projection) | rejected; ARGUS2-INPUT-PAYLOAD-LENGTH; bytes are never synthesized, padded or truncated to fit |
| `tests/thesis_lite/argus/test_argus2_observation_unit.py::test_payload_schema_state_other_than_undecoded_rejected` | a projection declaring payloadSchemaState 'decoded' | run.import_observation(projection) | rejected with the ARGUS2-SCHEMA-UNKNOWN-FIELD class; this slice never claims decoder success |
| `tests/thesis_lite/argus/test_argus2_observation_unit.py::test_unknown_nested_projection_field_rejected` | a projection record carrying an additional nested key outside extensions | run.import_observation(projection) | rejected; ARGUS2-SCHEMA-UNKNOWN-FIELD; the unknown key is neither ignored nor silently discarded |
| `tests/thesis_lite/argus/test_argus2_observation_unit.py::test_projection_record_missing_required_identity_rejected` | a projection record with no contractId or schemaId | run.import_observation(projection) | rejected; ARGUS2-INPUT-IDENTITY-MISSING; no partial accepted record is retained |
| `tests/thesis_lite/argus/test_argus2_observation_unit.py::test_import_attaches_no_live_tap_and_performs_no_io` | an import performed with socket/subprocess access made unavailable | run.import_observation(projection) | import succeeds without any socket, network, subprocess or live tap attach/pull/acknowledge operation |
| `tests/thesis_lite/argus/test_argus2_observation_unit.py::test_projection_roundtrip_preserves_values_exactly` | a frozen owned projection imported and exported once | run.import_observation(projection); finalize; read_run(root).export_json() | the reconstructed record values equal the projected values exactly; no field is defaulted, reordered or normalized |

### 7.9 `ARGUS2-SR-009-U` — Payload visibility, loss and interval/snapshot semantics

**Owning component:** `ARGUS2-SR-009-CMP`; **requirement:** `ARGUS2-SR-009`; **invariants:** `ARGUS2-INV-06`, `ARGUS2-INV-08`, `ARGUS2-INV-09`.

| Case id | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/argus/test_argus2_payload_unit.py::test_metadata_only_omitted_carries_no_payload_bytes` | an imported observation with payloadViewState 'omitted' | read back the record | visibleByteCount is 0 and visibleBytesHex is ''; sourcePayloadSize still records the complete source byte count |
| `tests/thesis_lite/argus/test_argus2_payload_unit.py::test_redacted_carries_no_payload_bytes` | an imported observation with payloadViewState 'redacted' | read back the record | visibleByteCount is 0 and visibleBytesHex is ''; no withheld content is reconstructed |
| `tests/thesis_lite/argus/test_argus2_payload_unit.py::test_truncated_retains_explicit_bounded_prefix` | an imported observation with payloadViewState 'truncated' and 0 < visibleByteCount < sourcePayloadSize | read back the record | the bounded prefix is retained with its exact visibleByteCount and remains explicitly truncated |
| `tests/thesis_lite/argus/test_argus2_payload_unit.py::test_complete_visibility_equals_source_payload_size` | an imported observation with payloadViewState 'complete' | read back the record | visibleByteCount equals sourcePayloadSize and the visible bytes decode exactly |
| `tests/thesis_lite/argus/test_argus2_payload_unit.py::test_visibility_states_remain_distinguishable_after_read` | a run importing one omitted, one redacted, one truncated and one complete observation | read_run(root).records() | the four visibility states reconstruct distinctly with their own visible byte counts; complete and omitted are never conflated |
| `tests/thesis_lite/argus/test_argus2_payload_unit.py::test_snapshot_counters_backpressure_and_validity_preserved` | a separately supplied snapshot with queued/accepted/dropped/coalesced, backpressureRejections, validityEffect and validityState | run.import_snapshot(snapshot) then read back | every declared snapshot value reconstructs exactly and its intervalProvenance is preserved |
| `tests/thesis_lite/argus/test_argus2_payload_unit.py::test_closed_interval_without_bounds_rejected` | a snapshot declaring intervalProvenance.closure 'closed' with start/end absent | run.import_snapshot(snapshot) | rejected; ARGUS2-INPUT-INTERVAL-INCOMPLETE; the interval is never completed by inference |
| `tests/thesis_lite/argus/test_argus2_payload_unit.py::test_unclosed_interval_recorded_and_forces_incomplete` | a snapshot declaring intervalProvenance.closure 'unclosed' | run.finalize() | evidenceStatus is 'incomplete'; evidenceReasons contains ARGUS2-REASON-UNCLOSED-INTERVAL and the unresolved interval stays visible |
| `tests/thesis_lite/argus/test_argus2_payload_unit.py::test_known_drop_remains_visible_after_stream_closure` | an imported observation with counters.dropped greater than zero | run.finalize() then read_run(root) | ARGUS2-LOSS-KNOWN-DROP reported; evidenceReasons contains ARGUS2-REASON-KNOWN-LOSS and finalization cannot make the run complete |
| `tests/thesis_lite/argus/test_argus2_payload_unit.py::test_degraded_validity_interval_forces_incomplete` | a snapshot declaring validityState 'degraded' | run.finalize() | ARGUS2-LOSS-DEGRADED-INTERVAL reported; evidenceStatus is 'incomplete' and the degraded interval is not acknowledged away |
| `tests/thesis_lite/argus/test_argus2_payload_unit.py::test_invalid_validity_interval_forces_incomplete` | a snapshot declaring validityState 'invalid' | run.finalize() | ARGUS2-LOSS-INVALID-INTERVAL reported; evidenceStatus is 'incomplete' |
| `tests/thesis_lite/argus/test_argus2_payload_unit.py::test_retention_counters_do_not_substitute_for_interval_closure` | benign counters (dropped 0, coalesced 0) with no snapshot and a required interval-closure obligation | run.finalize() | the interval-closure obligation remains unsatisfied; evidenceReasons contains ARGUS2-REASON-UNMET-OBLIGATION and no lossless capture is claimed from counters alone |
| `tests/thesis_lite/argus/test_argus2_payload_unit.py::test_no_unobserved_payload_is_synthesized` | an omitted/redacted record whose sourcePayloadSize is large | read back the record | no bytes are generated from sourcePayloadSize and no unobserved content appears |

### 7.10 `ARGUS2-SR-010-U` — Bounded read-only replay/export and metric-input links

**Owning component:** `ARGUS2-SR-010-CMP`; **requirement:** `ARGUS2-SR-010`; **invariants:** `ARGUS2-INV-11`, `ARGUS2-INV-15`.

| Case id | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_read_run_returns_records_in_ingestion_ordinal_order` | a finalized run with events appended out of clock order | EvidenceStore.read_run(root).records() | records are returned in strictly increasing ingestionOrdinal order, deterministically |
| `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_repeated_json_export_is_byte_equal` | an unchanged finalized run | export_json() twice | the two exports are byte-equal canonical JSON |
| `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_repeated_jsonl_export_is_byte_equal` | an unchanged finalized run | export_jsonl() twice | the two exports are byte-equal canonical JSONL with identical record ordering |
| `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_reader_verifies_manifest_and_artifact_hashes` | an intact finalized run with an indexed artifact | EvidenceStore.read_run(root) | the manifest and every indexed artifact size/hash verify and no diagnostic is produced |
| `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_corrupt_artifact_yields_diagnostic_and_bounded_partial_result` | an indexed artifact whose bytes were mutated | EvidenceStore.read_run(root) | ARGUS2-CORRUPT-ARTIFACT-HASH plus a bounded partial result of the records read so far; no invented data and no silent truncation |
| `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_reader_bound_exceeded_yields_bounded_partial_result` | a run holding more records than the caller max_read_records | EvidenceStore.read_run(root, limits=...) | ARGUS2-BOUND-EXCEEDED plus the first max_read_records records; the run root is not written |
| `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_metric_inputs_link_to_captured_selection_without_computation` | a plan body declaring metrics with observer references | EvidenceReader.metric_inputs() | each entry carries metricId, observerIds, calculationRef, unitSemantics, timeDomainIds and a declared selection of artifact paths/event ids; no metric value is computed |
| `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_incomplete_metric_selection_is_reported_not_filled` | a declared metric observer reference with no matching captured selection | EvidenceReader.metric_inputs() | the incomplete selection is reported explicitly and never filled in or guessed |
| `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_replay_performs_no_execution_or_oracle_invocation` | a finalized run read with socket/subprocess access made unavailable | EvidenceStore.read_run(root) and both exports | no component, fault, lifecycle action, metric computation, evaluation oracle, subprocess or network call is invoked |
| `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_cli_verify_reports_json_and_exit_status` | a complete run and an incomplete/corrupt run | xverse-argus verify <root> for each | usage-free JSON summary is printed; exit 0 for complete, exit 1 for incomplete/corrupt, exit 2 for a usage/input error |
| `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_cli_export_matches_api_export` | a finalized run | xverse-argus export <root> --format json|jsonl vs EvidenceReader.export_json()/export_jsonl() | stdout bytes equal the corresponding API export |
| `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_reader_leaves_the_run_root_byte_identical` | a finalized run | record every file hash, read and export, then re-hash | every run-root file hash is unchanged after the read/export |
| `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_reader_rejects_traversal_or_absolute_recorded_path_before_io` | a manifest field (manifest/eventStream/artifact path) containing a '..' segment, an absolute path or a drive-like prefix | EvidenceStore.read_run(root) | ARGUS2-PATH-ESCAPE before any open or parse; no bytes are read from outside the run root and the original bytes are unchanged (`ARGUS2-ADV-01`) |
| `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_reader_rejects_symlink_manifest_stream_or_artifact_before_io` | the manifest.json, stream or indexed artifact path is a symlink, including one resolving inside the run root | EvidenceStore.read_run(root) | ARGUS2-PATH-SYMLINK before any read; the link target is never followed and no O_NOFOLLOW-refused file is parsed (`ARGUS2-ADV-01`) |
| `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_reader_rejects_nonregular_manifest_stream_or_artifact_before_io` | the manifest, stream or indexed artifact path is a directory, FIFO, device or socket | EvidenceStore.read_run(root) | ARGUS2-PATH-NOT-REGULAR before any parse; nothing is read and no partial record is trusted (`ARGUS2-ADV-01`) |
| `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_reader_manifest_read_rejected_over_max_manifest_bytes_before_parse` | a manifest file larger than the caller max_manifest_bytes | EvidenceStore.read_run(root, limits=caller_limits) | ARGUS2-BOUND-EXCEEDED naming max_manifest_bytes; the partial bytes are not parsed and the original manifest bytes are unchanged (`ARGUS2-ADV-02`) |
| `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_reader_event_line_rejected_over_max_event_bytes_before_parse` | a stream line longer than the caller max_event_bytes | EvidenceStore.read_run(root, limits=caller_limits) | ARGUS2-BOUND-EXCEEDED naming max_event_bytes; the over-long line is not parsed and the records before it form a bounded partial result (`ARGUS2-ADV-02`) |
| `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_reader_stream_rejected_over_max_events_total_bound` | a stream whose byte length exceeds the derived total bound max_events * max_event_bytes | EvidenceStore.read_run(root, limits=caller_limits) | ARGUS2-BOUND-EXCEEDED naming max_events; the read stops at the derived total stream bound and the run root is not written (`ARGUS2-ADV-02`) |
| `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_reader_caller_limits_authoritative_over_damaged_manifest_echo` | a damaged manifest echoing a huge limits object while the caller passes small explicit limits | EvidenceStore.read_run(root, limits=caller_limits) | the caller limits govern verification; the echoed limits are recorded data only and never relax a bound, and an unparseable echo is a diagnostic rather than a new limit set (`ARGUS2-ADV-02`) |
| `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_manifest_wrong_container_shape_yields_stable_corrupt_manifest_diagnostic` | a manifest that is not a JSON object, or whose artifacts/obligations/eventStream member has a scalar/array type where the frozen type requires another shape | EvidenceStore.read_run(root) | ARGUS2-CORRUPT-MANIFEST-SHAPE as a stable bounded diagnostic; the container is never coerced, iterated or indexed assuming the wrong type and the assessed status is incomplete (`ARGUS2-ADV-05`) |
| `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_event_line_not_a_json_object_yields_stable_corrupt_event_diagnostic` | a stream line that parses to a JSON array, scalar, string or null | EvidenceStore.read_run(root) | ARGUS2-CORRUPT-EVENT as a stable bounded diagnostic; the record is excluded and the assessed status is incomplete (`ARGUS2-ADV-05`) |
| `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_cli_verify_exit_zero_requires_assessed_complete` | a manifest that recorded 'complete' while verification detects corruption, and a genuinely complete run | xverse-argus verify <root> for each | exit 1 with an output carrying both recorded and assessed facts for the corrupt run; exit 0 only when assessedEvidenceStatus is 'complete' (`ARGUS2-ADV-03`) |
| `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_unreadable_manifest_returns_assessed_incomplete_without_fabrication` | a manifest that cannot be read or parsed at all | EvidenceStore.read_run(root) | an assessed incomplete result with no records and a bounded stable diagnostic; no manifest is synthesized and the original bytes are unchanged (`ARGUS2-ADV-03`) |
| `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_mutating_returned_records_cannot_change_subsequent_read_or_export` | an intact finalized run read twice | mutate any nested object reachable from records()/manifest/metric_inputs() returned by the first read, then export again | internal admission facts and the second read/export are unchanged because every returned view is an independent defensive copy (`ARGUS2-ADV-07`) |

### 7.11 `ARGUS2-SR-011-U` — Caller authority, offline operation and absence of control authority

**Owning component:** `ARGUS2-SR-011-CMP`; **requirement:** `ARGUS2-SR-011`; **invariants:** `ARGUS2-INV-10`, `ARGUS2-INV-15`.

| Case id | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/argus/test_argus2_offline_unit.py::test_caller_supplied_run_identity_is_required` | open_run called with no run id | EvidenceStore.open_run(root, run_id=None, plan=plan) | rejected; ARGUS2-INPUT-AUTHORITY-MISSING; no identity is generated |
| `tests/thesis_lite/argus/test_argus2_offline_unit.py::test_caller_supplied_limits_are_echoed_not_defaulted` | a caller limit set supplied explicitly | open_run(root, ..., limits=limits) then inspect manifest.limits | the effective caller limits are echoed into the manifest so the reader verifies under the same bounds |
| `tests/thesis_lite/argus/test_argus2_offline_unit.py::test_caller_supplied_obligations_are_taken_verbatim` | a caller obligation set | open_run(root, ..., obligations=obligations) then inspect manifest.obligations | the declared obligations are recorded verbatim; no obligation is invented, defaulted or removed |
| `tests/thesis_lite/argus/test_argus2_offline_unit.py::test_unknown_obligation_kind_rejected` | an obligation whose kind is outside the closed set | open_run(root, ..., obligations=[{'obligationId': 'o1', 'kind': 'best-effort', 'required': True}]) | rejected; ARGUS2-INPUT-FIELD-INVALID; only the four frozen obligation kinds exist |
| `tests/thesis_lite/argus/test_argus2_offline_unit.py::test_no_network_access_during_open_append_finalize` | socket creation made to raise | open_run, append_event, finalize | the whole lifecycle completes with no socket or network access |
| `tests/thesis_lite/argus/test_argus2_offline_unit.py::test_no_subprocess_or_service_is_started` | subprocess creation made to raise | open_run, import, finalize, read_run | no subprocess, service, daemon or background worker is started |
| `tests/thesis_lite/argus/test_argus2_offline_unit.py::test_no_metric_computation_or_oracle_capability_is_exposed` | the public xverse.argus surface | inspect the exported names | no metric-computation or evaluation-oracle entry point is exposed or importable |
| `tests/thesis_lite/argus/test_argus2_offline_unit.py::test_no_control_or_actuation_output_is_produced` | a full lifecycle | enumerate run-root artifacts and return values | only JSON/JSONL evidence artifacts are produced; no control, actuation or provider-delivery output exists |
| `tests/thesis_lite/argus/test_argus2_offline_unit.py::test_only_json_and_jsonl_artifacts_are_written` | a run with events plus an imported observation and snapshot | enumerate the run root | every written artifact is JSON or JSONL; no database, socket, binary blob, parquet or side-channel file appears |
| `tests/thesis_lite/argus/test_argus2_offline_unit.py::test_no_remote_lookup_or_environment_discovery` | an environment with proxy/user/home variables set | open_run and read_run | no remote lookup, locale, environment or home-directory value influences identity, clocks, limits or verdicts |
| `tests/thesis_lite/argus/test_argus2_offline_unit.py::test_admitted_caller_objects_are_not_aliased_after_admission` | caller-supplied run_envelope, source_byte_digests, clocks, extensions and obligations objects | open_run(...); mutate every caller-owned object after admission; inspect the manifest and the evaluated obligations | no admitted fact changes and the writer holds no reference to a caller-owned mutable object; admission deep-snapshots every caller value (`ARGUS2-ADV-07`) |

### 7.12 `ARGUS2-SR-012-U` — Additive packaging, installed-wheel compatibility and preserved contracts

**Owning component:** `ARGUS2-SR-012-CMP`; **requirement:** `ARGUS2-SR-012`; **invariants:** `ARGUS2-INV-12`, `ARGUS2-INV-16`.

| Case id | Precondition | Stimulus | Expected |
| --- | --- | --- | --- |
| `tests/thesis_lite/argus/test_argus2_consumer_unit.py::test_xverse_argus_imports_from_installed_wheel` | the built wheel installed into an isolated target with an empty PYTHONPATH outside the source tree | import xverse.argus | the module resolves inside the installed target, not the source tree |
| `tests/thesis_lite/argus/test_argus2_consumer_unit.py::test_xverse_xdl_imports_from_installed_wheel` | the built wheel installed into an isolated target | import xverse_xdl.experiment_plan | the accepted plan API still resolves inside the installed target and is unchanged |
| `tests/thesis_lite/argus/test_argus2_consumer_unit.py::test_existing_xdl_console_entry_point_preserved` | the installed distribution metadata | inspect console entry points and distribution name | the 'xdl' entry point and the 'xverse-xdl' distribution name are unchanged |
| `tests/thesis_lite/argus/test_argus2_consumer_unit.py::test_additive_xverse_argus_console_entry_point_present` | the installed distribution metadata | inspect the 'xverse-argus' entry point | xverse-argus = xverse.argus.cli:main is present as the one additive consumer entry point |
| `tests/thesis_lite/argus/test_argus2_consumer_unit.py::test_wheel_does_not_package_the_xcom_cpp_tree` | the built wheel contents | enumerate wheel members | no src/xverse/xcom C++ header or source member is packaged; only the additive Argus package enters the wheel |
| `tests/thesis_lite/argus/test_argus2_consumer_unit.py::test_unknown_major_schema_rejected_from_installed_wheel` | a run whose manifest/event schemaVersion major is not 1, read via the installed wheel | read_run(root) via the installed import | ARGUS2-SCHEMA-MAJOR-UNSUPPORTED with a bounded partial result |
| `tests/thesis_lite/argus/test_argus2_consumer_unit.py::test_additive_unknown_field_behaviour_is_explicit` | a record with an unknown key outside extensions and a record with an unknown extensions namespace | append/read both via the installed wheel | the outside-extensions key is rejected with ARGUS2-SCHEMA-UNKNOWN-FIELD; the extensions namespace is preserved verbatim and never interpreted |
| `tests/thesis_lite/argus/test_argus2_consumer_unit.py::test_owned_argus_tests_run_against_installed_wheel_with_empty_pythonpath` | the owned test directory copied outside the source tree and run with PYTHONPATH resolving only to the installed target | pytest the copied owned Argus tests | the owned Argus tests pass against the installed wheel; no source-tree sys.path entry is injected |
| `tests/thesis_lite/argus/test_argus2_consumer_unit.py::test_no_accepted_cpp_or_xdl_source_is_modified` | the additive implementation diff | repository static inspection of the changed path set | no file under src/xverse/xcom, src/xverse_xdl, xdl, proto or an existing test is modified |
| `tests/thesis_lite/argus/test_argus2_consumer_unit.py::test_xdl_cli_behaviour_is_preserved` | the installed 'xdl' console script | invoke the existing xdl version/validate behaviour | the accepted xdl CLI behaviour is unchanged by the additive packaging |

### 7.13 Frozen adversarial case registry binding (`ARGUS2-ADV-01` … `ARGUS2-ADV-07`)

The adversarial cases below are frozen by `architecture.md` §11.1 before any code is written. Each is bound
here to at least one exact pytest-discoverable identifier; the verification-design stage must ensure every
listed identifier appears in the relevant actual measure log, and the implementation stage must create each
identifier verbatim. No binding may be removed or weakened.

| Adv. case | Terminal finding / reproduction | Bound exact identifiers |
| --- | --- | --- |
| `ARGUS2-ADV-01` | `AR-F01` / `AR-F01-path` | `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_reader_rejects_traversal_or_absolute_recorded_path_before_io`; `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_reader_rejects_symlink_manifest_stream_or_artifact_before_io`; `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_reader_rejects_nonregular_manifest_stream_or_artifact_before_io`; `tests/thesis_lite/argus/test_argus2_recovery_unit.py::test_recovery_uses_nofollow_and_bounded_reads_without_unbounded_read`; `tests/thesis_lite/argus/test_argus2_artifacts_unit.py::test_reader_artifact_path_confinement_checked_before_read` |
| `ARGUS2-ADV-02` | `AR-F01` / `AR-F01-bounds` | `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_reader_manifest_read_rejected_over_max_manifest_bytes_before_parse`; `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_reader_event_line_rejected_over_max_event_bytes_before_parse`; `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_reader_stream_rejected_over_max_events_total_bound`; `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_reader_caller_limits_authoritative_over_damaged_manifest_echo`; `tests/thesis_lite/argus/test_argus2_bounds_unit.py::test_max_diagnostic_count_caps_damaged_input_diagnostics`; `tests/thesis_lite/argus/test_argus2_recovery_unit.py::test_recovery_uses_nofollow_and_bounded_reads_without_unbounded_read` |
| `ARGUS2-ADV-03` | `AR-F02` / `AR-F02` | `tests/thesis_lite/argus/test_argus2_stream_unit.py::test_reader_exposes_recorded_and_assessed_status_separately`; `tests/thesis_lite/argus/test_argus2_stream_unit.py::test_manifest_recorded_complete_with_corrupt_stream_assessed_incomplete`; `tests/thesis_lite/argus/test_argus2_stream_unit.py::test_corrupt_manifest_never_exported_as_primary_complete`; `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_cli_verify_exit_zero_requires_assessed_complete`; `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_unreadable_manifest_returns_assessed_incomplete_without_fabrication` |
| `ARGUS2-ADV-04` | `AR-F03` / `AR-F03-identities` | `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_reader_rejects_event_missing_required_identity`; `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_reader_rejects_duplicate_event_id_within_run`; `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_reader_rejects_nonmonotonic_ingestion_ordinal`; `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_reader_rejects_event_runid_mismatch_with_manifest`; `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_reader_rejects_nonfinite_clock_value_on_read` |
| `ARGUS2-ADV-05` | `AR-F03` / `AR-F03-malformed` | `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_manifest_wrong_container_shape_yields_stable_corrupt_manifest_diagnostic`; `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_event_line_not_a_json_object_yields_stable_corrupt_event_diagnostic`; `tests/thesis_lite/argus/test_argus2_diagnostics_unit.py::test_truncated_json_and_unknown_nested_key_yield_stable_bounded_diagnostics`; `tests/thesis_lite/argus/test_argus2_diagnostics_unit.py::test_no_uncaught_typeerror_or_valueerror_from_malformed_input` |
| `ARGUS2-ADV-06` | `AR-F04` / `AR-F04` | `tests/thesis_lite/argus/test_argus2_stream_unit.py::test_manifest_bound_measured_on_actual_serialized_bytes_at_open_finalize_and_abort`; `tests/thesis_lite/argus/test_argus2_writer_unit.py::test_finalize_manifest_bound_exceeded_preserves_prior_manifest`; `tests/thesis_lite/argus/test_argus2_writer_unit.py::test_abort_manifest_bound_exceeded_preserves_prior_manifest` |
| `ARGUS2-ADV-07` | `AR-F05` / `AR-F05` | `tests/thesis_lite/argus/test_argus2_admission_unit.py::test_nested_obligation_detail_deep_snapshotted_against_caller_mutation`; `tests/thesis_lite/argus/test_argus2_admission_unit.py::test_non_json_encodable_or_nonfinite_obligation_detail_rejected_at_admission`; `tests/thesis_lite/argus/test_argus2_admission_unit.py::test_envelope_digests_clocks_and_extensions_deep_snapshotted`; `tests/thesis_lite/argus/test_argus2_artifacts_unit.py::test_mutating_returned_artifact_view_cannot_rewrite_indexed_hash`; `tests/thesis_lite/argus/test_argus2_offline_unit.py::test_admitted_caller_objects_are_not_aliased_after_admission`; `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_mutating_returned_records_cannot_change_subsequent_read_or_export` |

## 8. Required defect-class coverage

| Required class | Frozen cases |
| --- | --- |
| Duplicate event identifiers (ARGUS2-SR-003-U) | `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_duplicate_event_identity_rejected_without_partial_record` |
| Unknown schema/version handling (ARGUS2-SR-003-U, ARGUS2-SR-008-U, ARGUS2-SR-012-U) | `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_unknown_event_schema_major_version_rejected`, `tests/thesis_lite/argus/test_argus2_observation_unit.py::test_unknown_projection_major_version_rejected`, `tests/thesis_lite/argus/test_argus2_consumer_unit.py::test_unknown_major_schema_rejected_from_installed_wheel` |
| Partial writes and recovery (ARGUS2-SR-006-U) | `tests/thesis_lite/argus/test_argus2_recovery_unit.py::test_truncated_last_jsonl_record_detected_without_recount`, `tests/thesis_lite/argus/test_argus2_recovery_unit.py::test_recovery_reads_a_bounded_prefix_and_writes_nothing`, `tests/thesis_lite/argus/test_argus2_writer_unit.py::test_interrupted_finalize_publishes_failed_state` |
| Exceeded caller bounds (ARGUS2-SR-005-U) | `tests/thesis_lite/argus/test_argus2_bounds_unit.py::test_max_event_bytes_at_bound_accepted_and_over_rejected` plus the remaining per-field bound negatives in the same unit |
| Source digest mutation (ARGUS2-SR-001-U) | `tests/thesis_lite/argus/test_argus2_admission_unit.py::test_plan_digest_mutation_rejected`, `tests/thesis_lite/argus/test_argus2_admission_unit.py::test_source_byte_digests_never_substitute_semantic_identity` |
| Missing causal closure (ARGUS2-SR-003-U) | `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_unresolved_causation_remains_visible` |
| Missing interval closure (ARGUS2-SR-009-U) | `tests/thesis_lite/argus/test_argus2_payload_unit.py::test_unclosed_interval_recorded_and_forces_incomplete`, `tests/thesis_lite/argus/test_argus2_payload_unit.py::test_retention_counters_do_not_substitute_for_interval_closure` |
| Payload visibility and loss (ARGUS2-SR-009-U) | `tests/thesis_lite/argus/test_argus2_payload_unit.py::test_metadata_only_omitted_carries_no_payload_bytes`, `tests/thesis_lite/argus/test_argus2_payload_unit.py::test_redacted_carries_no_payload_bytes`, `tests/thesis_lite/argus/test_argus2_payload_unit.py::test_truncated_retains_explicit_bounded_prefix`, `tests/thesis_lite/argus/test_argus2_payload_unit.py::test_known_drop_remains_visible_after_stream_closure` |
| Unsafe paths and symlinks (ARGUS2-SR-007-U) | `tests/thesis_lite/argus/test_argus2_artifacts_unit.py::test_traversal_segment_rejected`, `tests/thesis_lite/argus/test_argus2_artifacts_unit.py::test_escaping_symlink_rejected`, `tests/thesis_lite/argus/test_argus2_artifacts_unit.py::test_symlink_resolving_inside_run_root_still_rejected`, `tests/thesis_lite/argus/test_argus2_artifacts_unit.py::test_unsafe_artifact_name_rejected` |
| Installed-wheel consumer compatibility (ARGUS2-SR-012-U) | `tests/thesis_lite/argus/test_argus2_consumer_unit.py::test_xverse_argus_imports_from_installed_wheel`, `tests/thesis_lite/argus/test_argus2_consumer_unit.py::test_xverse_xdl_imports_from_installed_wheel`, `tests/thesis_lite/argus/test_argus2_consumer_unit.py::test_owned_argus_tests_run_against_installed_wheel_with_empty_pythonpath` |
| Pre-I/O confined regular-file checks and symlink rejection (`AR-F01`, `ARGUS2-ADV-01`) | `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_reader_rejects_traversal_or_absolute_recorded_path_before_io`, `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_reader_rejects_symlink_manifest_stream_or_artifact_before_io`, `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_reader_rejects_nonregular_manifest_stream_or_artifact_before_io`, `tests/thesis_lite/argus/test_argus2_artifacts_unit.py::test_reader_artifact_path_confinement_checked_before_read` |
| Bounded streaming I/O and caller-authoritative limits (`AR-F01`, `ARGUS2-ADV-02`) | `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_reader_manifest_read_rejected_over_max_manifest_bytes_before_parse`, `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_reader_event_line_rejected_over_max_event_bytes_before_parse`, `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_reader_stream_rejected_over_max_events_total_bound`, `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_reader_caller_limits_authoritative_over_damaged_manifest_echo`, `tests/thesis_lite/argus/test_argus2_recovery_unit.py::test_recovery_uses_nofollow_and_bounded_reads_without_unbounded_read` |
| Assessed corrupt-evidence completeness (`AR-F02`, `ARGUS2-ADV-03`) | `tests/thesis_lite/argus/test_argus2_stream_unit.py::test_reader_exposes_recorded_and_assessed_status_separately`, `tests/thesis_lite/argus/test_argus2_stream_unit.py::test_manifest_recorded_complete_with_corrupt_stream_assessed_incomplete`, `tests/thesis_lite/argus/test_argus2_stream_unit.py::test_corrupt_manifest_never_exported_as_primary_complete`, `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_cli_verify_exit_zero_requires_assessed_complete`, `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_unreadable_manifest_returns_assessed_incomplete_without_fabrication` |
| Closed nested-schema identity/ordinal/run-id validation (`AR-F03`, `ARGUS2-ADV-04`) | `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_reader_rejects_event_missing_required_identity`, `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_reader_rejects_duplicate_event_id_within_run`, `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_reader_rejects_nonmonotonic_ingestion_ordinal`, `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_reader_rejects_event_runid_mismatch_with_manifest`, `tests/thesis_lite/argus/test_argus2_identity_unit.py::test_reader_rejects_nonfinite_clock_value_on_read` |
| Stable bounded malformed-input diagnostics without uncaught exceptions (`AR-F03`, `ARGUS2-ADV-05`) | `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_manifest_wrong_container_shape_yields_stable_corrupt_manifest_diagnostic`, `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_event_line_not_a_json_object_yields_stable_corrupt_event_diagnostic`, `tests/thesis_lite/argus/test_argus2_diagnostics_unit.py::test_truncated_json_and_unknown_nested_key_yield_stable_bounded_diagnostics`, `tests/thesis_lite/argus/test_argus2_diagnostics_unit.py::test_no_uncaught_typeerror_or_valueerror_from_malformed_input` |
| Manifest actual-byte bound at every publication (`AR-F04`, `ARGUS2-ADV-06`) | `tests/thesis_lite/argus/test_argus2_stream_unit.py::test_manifest_bound_measured_on_actual_serialized_bytes_at_open_finalize_and_abort`, `tests/thesis_lite/argus/test_argus2_writer_unit.py::test_finalize_manifest_bound_exceeded_preserves_prior_manifest`, `tests/thesis_lite/argus/test_argus2_writer_unit.py::test_abort_manifest_bound_exceeded_preserves_prior_manifest` |
| Deep admission snapshots and immutable returned views (`AR-F05`, `ARGUS2-ADV-07`) | `tests/thesis_lite/argus/test_argus2_admission_unit.py::test_nested_obligation_detail_deep_snapshotted_against_caller_mutation`, `tests/thesis_lite/argus/test_argus2_admission_unit.py::test_non_json_encodable_or_nonfinite_obligation_detail_rejected_at_admission`, `tests/thesis_lite/argus/test_argus2_admission_unit.py::test_envelope_digests_clocks_and_extensions_deep_snapshotted`, `tests/thesis_lite/argus/test_argus2_artifacts_unit.py::test_mutating_returned_artifact_view_cannot_rewrite_indexed_hash`, `tests/thesis_lite/argus/test_argus2_offline_unit.py::test_admitted_caller_objects_are_not_aliased_after_admission`, `tests/thesis_lite/argus/test_argus2_reader_unit.py::test_mutating_returned_records_cannot_change_subsequent_read_or_export` |

## 9. Static checks

Each unit plans at least one static check consumed by the trusted `ARGUS2-STATIC` analysis. Static checks parse
the candidate Python (planned source plus owned tests) and assert structural facts; they require no pytest output
and perform no writes. The per-unit rules and expectations are recorded in the corresponding unit record's
`static_checks` array; they cover canonical serialization flags, exclusive creation, path confinement, the closed
diagnostic catalogue, the absence of ambient clock/random/network calls, the read-only reader and the additive
wheel composition.

The terminal-review rework adds, additively, one repair static check to each of the affected units; the
inherited static checks are unchanged and no rule is weakened:

| Repair static check | Unit | Asserts (structural) |
| --- | --- | --- |
| `ARGUS2-SR-001-U-STATIC-SNAPSHOT` | `ARGUS2-SR-001-U` | Admission deep-snapshots (canonical round-trip) every caller obligation/envelope/digest/clock/extension and retains no caller-owned reference; `record_artifact` owns its size/hash identity; accessors return copies. |
| `ARGUS2-SR-002-U-STATIC-PUBLISH` | `ARGUS2-SR-002-U` | Exactly one publication chokepoint measures the actual canonical manifest bytes against `max_manifest_bytes` before temp-file + `fsync` + `os.replace`; open/finalize/abort all route through it. |
| `ARGUS2-SR-005-U-STATIC-DIAGNOSTICS` | `ARGUS2-SR-005-U` | Container/type/version/decode/bound/I/O faults are converted to closed-catalogue diagnostics; no uncaught `TypeError`/`ValueError`/JSON error; diagnostics are capped by `max_diagnostic_count`. |
| `ARGUS2-SR-006-U-STATIC-READBOUND` | `ARGUS2-SR-006-U` | No unbounded `read()`/`read_bytes()` on the manifest or stream; recovery and the writer's finalize/abort stream read share an `O_NOFOLLOW` bounded helper. |
| `ARGUS2-SR-007-U-STATIC-CONFINE` | `ARGUS2-SR-007-U` | `os.lstat`, `O_NOFOLLOW` and an `fstat` device/inode comparison precede any parse on the confined path; returned artifact views are copies. |
| `ARGUS2-SR-010-U-STATIC-CONFINE` | `ARGUS2-SR-010-U` | The reader checks confinement before I/O, streams under caller bounds without materializing the file, treats caller limits as authoritative, and exposes recorded and assessed status separately with defensive copies. |

## 10. Traceability

| Relation | Links |
| --- | --- |
| `decomposes_to` (component → unit) | `ARGUS2-L-201` … `ARGUS2-L-212` (one per unit, additive) |
| `refines` (requirement → REF-002 parent) | `ARGUS2-L-001` … `ARGUS2-L-012` (requirements stage, preserved) |
| `allocated_to` (requirement → component) | `ARGUS2-L-101` … `ARGUS2-L-112` (architecture stage, preserved) |
| `implemented_by`, `verified_by`, `analyzed_by` | owned by the implementation and verification-design stages; not claimed here |

## 11. Limitations, maturity and next step

* Maturity of every item in this document is **planned / target**: not implemented, not verified and not accepted
  for delivery. Source and design inspection does not demonstrate runtime success.
* These identifiers are frozen contracts. The implementation stage must create each one verbatim; the
  verification-design stage must bind the `ARGUS2-UNIT` measure to them; the validation stage confirms the printed
  names match. Renaming, dropping or weakening a case requires a reviewed successor candidate.
* No code, fixture, schema, packaging change or test is written by this stage; the precode gate requires the
  verification-design stage to complete before implementation.
* No source requirement ID is created, no REF-002 parent disposition is promoted or closed, and no historical
  accepted requirement, design, unit, measure, validation or stage record is rewritten; only additive `decomposes_to`
  links were appended to the mutable `engineering/trace/links.json`.
* The local checks performed here are worker checks only; the trusted unit/static/integration/validation measures,
  the pinned target assembly, the built-and-installed wheel check, independent internal review and terminal user
  acceptance are external gates and are not claimed.
* Terminal-review repair: this rework adds 33 new planned identifiers (139 inherited + 33 = 172) that bind
  `ARGUS2-ADV-01`–`ARGUS2-ADV-07` (§7.13) to bounded streaming I/O, pre-I/O confined regular-file checks, closed
  nested schemas with stable bounded diagnostics, reader-assessed corrupt-evidence status, the actual
  serialized byte bound at every manifest publication, and deep admission snapshots with immutable returned
  views. No inherited case, diagnostic, invariant, allocation or parent disposition is removed, renamed or
  weakened; the five findings are repaired at specification level only and no source, test or packaging byte
  is changed by this stage.
* Precode-gate boundary: the unit-specification and verification-design stages must both complete before any
  implementation; from the precode gate on, these planned document bytes and their bound unit records are
  immutable except through a reviewed successor candidate.
* Inherited limitation: the admitted planning bundle names a required launch-evidence `admission/review.md` that is
  not an admitted input for this run; it remains an external, unverified later-gate input and is neither
  fabricated nor substituted.

Next stage: **verification_design** — bind the four ARGUS2 measures (`ARGUS2-UNIT`, `ARGUS2-STATIC`,
`ARGUS2-INTEGRATION`, `ARGUS2-VALIDATION`) to exact test identifiers from this document (including every
`ARGUS2-ADV-01`–`ARGUS2-ADV-07` binding in §7.13), freeze the real C++ owned-record fixture and the accepted
XDL compiler consumer cases, and complete the requirement/component/unit/test/measure trace. Every declared
identifier must appear in the relevant actual measure log, and `ARGUS2-STATIC` must consume the additive repair
static checks in §9. Model recommendation: the pinned `deepseek-v4-flash` with **high** reasoning remains the most
cost-effective and the only authorized route for that deterministic contract-binding work; no model switch is
claimed or performed and no benchmark or exact-cost claim is made. Blocker: none; no code may be written until
all four design stages complete and the precode gate passes.
