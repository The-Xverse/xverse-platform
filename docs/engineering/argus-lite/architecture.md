# Argus Lite Phase 2 Architecture — bounded run evidence persistence and read-only reconstruction

## 1. Document control

| Field | Value |
| --- | --- |
| Feature | ARGUS2 (Argus Lite Phase 2 — bounded run evidence persistence, X-COM observation projection import and read-only reconstruction) |
| Stage / role | architecture (repository-owned Spec Kit work-product workflow, ADR-0020) |
| Revision | 1 |
| Revision basis | Revision 1 incorporates the terminal-review rework of findings `AR-F01`–`AR-F05` (run `01M3WW66FB61DKFEPWFEH2BFJE`, candidate `2f7806599e7df6693b9899fb328762728dbf65d5`, verdict `rework`). No accepted revision is superseded; the rejected candidate was never accepted. |
| Date | 2026-10-02 (rework of the 2026-10-01 revision) |
| Admitted platform baseline revision | `c1fd213cd00259b74f8308d8ca58157ea985aaa0` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 (`ARGUS2-SR-001` … `ARGUS2-SR-012`) |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Component records | `engineering/architecture/components/ARGUS2-SR-001-CMP.json` … `ARGUS2-SR-012-CMP.json` |
| Admitted planning inputs | `specs/023-argus-lite-evidence/{spec,plan,research,data-model,quickstart,tasks}.md`, `specs/023-argus-lite-evidence/contracts/evidence.md`, `specs/021-thesis-lite-program/{backlog,requirements-priorities}.json`, `docs/adr/ADR-THESIS-LITE-0001.md` |
| Consumed accepted platform anchors | `src/xverse_xdl/experiment_plan.py` (`API_VERSION`, `PROFILE_NAMESPACE`, `PLAN_VERSION`, `compute_plan_digest`, `plan_matches_digest`), `src/xverse/xcom/include/xverse/xcom/observation.hpp` (`kObservationContractVersion = 1.0.0`), `docs/xcom/observation-boundary.md`, `proto/xverse/xcom/v1/tool_gateway.proto`, `pyproject.toml`, `.specify/memory/constitution.md` 2.1.0, `docs/architecture/sads-requirements-traceability.json` |
| Classification | Public-safe engineering work product |
| Maturity | **Planned / target.** Design only. No source, schema, packaging, fixture or test code exists in this stage; nothing here is implementation, runtime, interoperability, compatibility, parity, readiness or delivery evidence. |

## 2. Purpose and position in the delivery graph

ARGUS2 adds one bounded capability: persist a **bounded, versioned, causal run-evidence stream** plus an
**atomic run manifest**, import a documented projection of owned C++ X-COM `ObservationRecord` values and
separately supplied tap snapshots, and reconstruct that evidence **read-only**. It performs no execution,
no control, no metric computation, no network access and no live tap attachment.

```text
admitted thesis Phase 2 planning (read-only, not duplicated) ─┐
accepted XDL resolved-plan public API + digest semantics    ─┤
accepted C++ X-COM observation contract + gateway proto     ─┼─ read-only, unchanged
accepted governance/ADRs/constitution                       ─┘
        │
        ▼  consumed by
ARGUS2 architecture (this stage): frozen event/manifest/projection schemas · public
        │   Python API/CLI · XDL digest reuse · single-writer durability · caller bounds
        │   · confined artifacts · incomplete classification · clocks/causation · payload/
        │   loss/snapshot mapping · read-only replay/export · metric links · wheel packaging
        ▼
ARGUS2 design → unit specification → verification design (precode gate) → implementation
        → integration → validation → documentation → read-only internal review → terminal review/acceptance
```

Argus owns **storage and offline inspection only**. Scenario execution, Maestro lifecycle/control, fault
runtime, safety monitors, adaptation, production integration, automotive protocol values, metrics
computation, dashboards, live tap bridging and campaign results remain outside this slice. Phase 3
(Maestro Lite) and later capabilities are **not started, reserved, or stubbed** here.

### 2.1 Derived-requirement coverage

| Requirement | Architecture element(s) | Component record |
| --- | --- | --- |
| `ARGUS2-SR-001` | `ARGUS2-ARCH-01`, `ARGUS2-ARCH-05` | `ARGUS2-SR-001-CMP` |
| `ARGUS2-SR-002` | `ARGUS2-ARCH-02`, `ARGUS2-ARCH-12` | `ARGUS2-SR-002-CMP` |
| `ARGUS2-SR-003` | `ARGUS2-ARCH-03`, `ARGUS2-ARCH-05` | `ARGUS2-SR-003-CMP` |
| `ARGUS2-SR-004` | `ARGUS2-ARCH-04`, `ARGUS2-ARCH-03` | `ARGUS2-SR-004-CMP` |
| `ARGUS2-SR-005` | `ARGUS2-ARCH-05`, `ARGUS2-ARCH-07` | `ARGUS2-SR-005-CMP` |
| `ARGUS2-SR-006` | `ARGUS2-ARCH-06`, `ARGUS2-ARCH-02` | `ARGUS2-SR-006-CMP` |
| `ARGUS2-SR-007` | `ARGUS2-ARCH-07`, `ARGUS2-ARCH-06` | `ARGUS2-SR-007-CMP` |
| `ARGUS2-SR-008` | `ARGUS2-ARCH-08`, `ARGUS2-ARCH-09` | `ARGUS2-SR-008-CMP` |
| `ARGUS2-SR-009` | `ARGUS2-ARCH-09`, `ARGUS2-ARCH-08` | `ARGUS2-SR-009-CMP` |
| `ARGUS2-SR-010` | `ARGUS2-ARCH-10`, `ARGUS2-ARCH-07` | `ARGUS2-SR-010-CMP` |
| `ARGUS2-SR-011` | `ARGUS2-ARCH-11`, `ARGUS2-ARCH-05` | `ARGUS2-SR-011-CMP` |
| `ARGUS2-SR-012` | `ARGUS2-ARCH-12`, `ARGUS2-ARCH-06` | `ARGUS2-SR-012-CMP` |

## 3. Boundary and context

### 3.1 System context

```text
   ┌──────────────── admitted external planning (read-only, not duplicated) ────────────────┐
   │ 023-argus-lite-evidence spec/plan/research/data-model/contract/tasks/quickstart        │
   │ 021 phase-2 allocation projection · REF-002 SADS register (no new system IDs)          │
   └─────────────────────────────────────────┬──────────────────────────────────────────────┘
                                             │ derived into (this repository)
   ┌──────── accepted platform assets (read-only, byte-preserved) ─────────────────────────┐
   │ xverse_xdl.experiment_plan (public API + digest semantics) — consumed, not reimplemented│
   │ C++ X-COM observation.hpp / observation-boundary.md — contract consumed, not modified   │
   │ proto/xverse/xcom/v1/tool_gateway.proto — distinct, narrower schema (not substituted)   │
   │ pyproject.toml (xverse-xdl wheel) · accepted test suite                                 │
   └─────────────────────────────────────────┬──────────────────────────────────────────────┘
                                             │ extended additively by
   ┌──────── ARGUS2 owned additions (design now, code later) ──────────────────────────────┐
   │ src/xverse/__init__.py · src/xverse/argus/**          (offline evidence package)        │
   │ tests/thesis_lite/argus/**                            (owned fixtures/tests)           │
   │ pyproject.toml additive wheel configuration + one additive console entry point          │
   └─────────────────────────────────────────┬──────────────────────────────────────────────┘
                                             ▼
       run root: versioned JSONL evidence stream + atomic JSON manifest — no execution
```

### 3.2 Trust boundaries

| Boundary | Inside | Outside | Rule |
| --- | --- | --- | --- |
| `ARGUS2-XB-01` Semantic plan identity vs source-byte provenance | accepted `compute_plan_digest`/`plan_matches_digest` semantic plan identity, Profile/API/plan versions | YAML/JSON source bytes, envelope `runId`, generation time, file names | The semantic digest (verified through the accepted public API) is the plan identity; source-byte digests live only in run provenance and are never substituted (`ARGUS2-SR-001`). |
| `ARGUS2-XB-02` Ingestion order vs temporal/causal order | deterministic local `ingestionOrdinal`, explicit causal references, explicit per-domain clocks | a global timeline, cross-domain comparison, inferred causality | Ingestion order is a local stream position only; ordering never implies time or causation, and no cross-domain sort is performed (`ARGUS2-SR-003`, `ARGUS2-SR-004`). |
| `ARGUS2-XB-03` Stored evidence vs control/actuation/analysis authority | bounded offline records, diagnostics, metric-**input** references | orchestration, actuation, provider delivery, live taps, metric computation, evaluation oracles | Argus acquires no control authority and computes no metric; replay is evidence reconstruction only (`ARGUS2-SR-008`, `ARGUS2-SR-010`, `ARGUS2-SR-011`). |
| `ARGUS2-XB-04` Owned observation record vs narrower gateway schema | documented versioned projection of owned C++ `ObservationRecord` accessors | tool-gateway protobuf `ObservationRecord` (missing fields; `route_id`/`contract_id`/`clock_domain`/`sequence`/`outcome`/`payload_state`/`payload_view`/`payload_bytes` only) | The gateway message is rejected as the full owned projection unless an explicitly versioned separate mapping records every missing field as unavailable; missing metadata is never fabricated (`ARGUS2-SR-008`). |
| `ARGUS2-XB-05` Run root confinement vs caller filesystem | run-relative safe artifact paths under one explicit run root | absolute paths, `..` traversal, escaping symlinks, unsafe names, files outside the run root | Every write/read resolves the confined real path and rejects escape; no write outside the run root occurs (`ARGUS2-SR-007`). |
| `ARGUS2-XB-06` Declared completeness vs inferred success | caller-declared obligations and integrity checks | scientific validity, safety, compatibility, parity, readiness, provider success | Stream closure and evidence completeness are separate facts; a closed stream alone cannot establish complete evidence (`ARGUS2-SR-002`, `ARGUS2-SR-009`). |
| `ARGUS2-XB-07` Caller-supplied authority vs ambient environment | caller-supplied run ID, clock identities/units, finite limits, obligations | ambient wall clock, random identity, remote lookup, cross-clock conversion, environment discovery | No ambient clock, random ID, network, or cross-domain conversion is used (`ARGUS2-SR-011`); all scientific numbers remain caller inputs (Constitution IX). |
| `ARGUS2-XB-08` Additive Argus package vs accepted platform artifacts | `src/xverse/__init__.py`, `src/xverse/argus/**` and additive wheel configuration | accepted `xverse_xdl` API/schemas/CLI, accepted C++ X-COM source/contracts, existing tests, historical records | Additive only; installed `xverse_xdl` imports, the existing `xdl` CLI and accepted C++ contracts are preserved (`ARGUS2-SR-012`). |
| `ARGUS2-XB-09` Read confinement and bounded reader I/O | run-relative confined regular files (`manifest.json`, `events.jsonl`, indexed artifacts) checked **before** any open or parse; caller-supplied authoritative reader limits | unbounded `read()`, symlink-followed paths, non-regular files, traversal/escape, and limits echoed by a damaged manifest | Every read resolves the confined real path and applies `os.lstat` **before** I/O, opens with `O_NOFOLLOW`, and streams at most the applicable finite bound; a path, type or bound violation yields a stable diagnostic and never a trusted partial parse (`ARGUS2-SR-005`, `ARGUS2-SR-007`, `ARGUS2-SR-010`; `ARGUS2-ADV-01`, `ARGUS2-ADV-02`). |
| `ARGUS2-XB-10` Recorded manifest facts vs reader-assessed completeness | the manifest's recorded `writerState`/`evidenceStatus`/`evidenceReasons`, echoed verbatim as *recorded* facts | the reader's independently *assessed* status from actually re-verifying manifest shape, stream integrity, artifacts and obligations | Reconstruction reports both facts separately; the primary/exported completeness is the assessed status, which can never be `complete` when corruption, truncation, a missing/mutated artifact, an unsupported version or a shape defect is detected (`ARGUS2-SR-002`, `ARGUS2-SR-010`; `ARGUS2-ADV-03`). |
| `ARGUS2-XB-11` Strict reader schema/identity vs tolerant parsing | the complete closed frozen nested schema, required run/event/producer identities, per-run ID uniqueness, monotonic ingestion ordinals, run-ID consistency and finite values | uncaught `TypeError`/`ValueError`, missing-field indexing, unknown nested keys, non-finite numbers, and silently accepted duplicate or out-of-order records | Malformed container types, versions, values and I/O are converted into bounded stable categorized diagnostics; no exception escapes the reader (`ARGUS2-SR-003`, `ARGUS2-SR-005`, `ARGUS2-SR-010`; `ARGUS2-ADV-04`, `ARGUS2-ADV-05`). |
| `ARGUS2-XB-12` Manifest byte bound at every publication vs post-hoc checking | one publication chokepoint that measures the **actual** canonical serialized bytes (including artifact index, obligations and finalize/abort metadata) against `max_manifest_bytes` | a bound checked only on some publications, a bound silently skipped because of growth, or a completed atomic replace after an exceeded bound | No manifest bytes are published unless the actual serialized size is within bound; on an exceeded bound or I/O failure the prior manifest bytes are preserved and no `closed`/`complete` persistence is claimed (`ARGUS2-SR-002`, `ARGUS2-SR-005`, `ARGUS2-SR-006`; `ARGUS2-ADV-06`). |
| `ARGUS2-XB-13` Admitted snapshot vs caller-owned mutable objects | deep canonical snapshots taken at admission of caller-supplied obligations, run envelope, source-byte digests, clocks and extensions; immutable internally owned artifact identity | aliasing the caller's nested objects or dict values, and mutable returned views that can rewrite internal admission facts or indexed file hashes | Mutating a caller object after admission cannot change any admitted fact or indexed artifact hash; every returned view is an independent immutable/defensive copy (`ARGUS2-SR-001`, `ARGUS2-SR-006`, `ARGUS2-SR-007`, `ARGUS2-SR-011`; `ARGUS2-ADV-07`). |

### 3.3 Prohibited elements (must remain absent)

No change to `src/xverse_xdl/**`, `xdl/**`, `src/xverse/xcom/**`, `proto/xverse/xcom/v1/**`,
`tests/xcom/**`, existing XDL tests, `docs/engineering/xcom/**`, `engineering/verification/measures/**`,
or any historical accepted record/ADR. No network, socket, subprocess, service, daemon, database, extra
dependency, live tap attach/pull, provider delivery change, stimulation, fault activation, metric
computation, dashboard, oracle, or legacy/production execution. No ambient clock, random identity,
locale, environment, user or home-directory lookup. No credential, private address, proprietary payload
or host-specific absolute path in any committed artifact.

## 4. Logical architecture

`ARGUS2-ARCH-*` names are local to this work-product set; each maps to one allocation component record
(`ARGUS2-SR-###-CMP`) in §5. The package is a bounded, single-writer, offline Python pipeline.

| Logical element | Responsibility | Realized in (planned) | Records |
| --- | --- | --- | --- |
| `ARGUS2-ARCH-01` Run admission and plan binding | Reject reuse/digest mismatch/unsupported version/envelope conflict; open exactly one fresh run bound to the verified semantic plan identity | `argus/planbinding.py`, `argus/api.py` | CMP-001, CMP-005 |
| `ARGUS2-ARCH-02` Event stream and manifest persistence | Append validated events to versioned JSONL; publish open/closed/failed manifests atomically with artifact index, event count/hash, obligations and explicit status | `argus/writer.py`, `argus/schema.py` | CMP-002, CMP-006, CMP-012 |
| `ARGUS2-ARCH-03` Event identity and causal model | Freeze event record identity, producer identity, ingestion ordinal, kind, optional sequence and correlation/causation references; index causal links without invention | `argus/schema.py`, `argus/causation.py` | CMP-003, CMP-004 |
| `ARGUS2-ARCH-04` Clock-domain model | Retain explicit source/observation clock domains and caller-declared unit/representation per value; never convert or compare across domains | `argus/clocks.py` | CMP-004 |
| `ARGUS2-ARCH-05` Validation and finite bounds | Fail-closed validation of every value against the frozen contract and the caller-configured finite limits, with a stable diagnostic category | `argus/limits.py`, `argus/diagnostics.py` | CMP-001, CMP-003, CMP-005, CMP-011 |
| `ARGUS2-ARCH-06` Single-writer state and durability/recovery | Enforce one owning writer, the `new → open → closed`/`open → failed` machine, documented flush/fsync/rename boundaries, bounded non-mutating recovery | `argus/writer.py`, `argus/recovery.py` | CMP-002, CMP-006, CMP-007, CMP-012 |
| `ARGUS2-ARCH-07` Confined artifact store | Enforce run-relative safe paths, regular confined files, size/content-hash verification, traversal/symlink escape rejection | `argus/artifacts.py` | CMP-005, CMP-007, CMP-010 |
| `ARGUS2-ARCH-08` X-COM observation projection import | Map owned `ObservationRecord` accessors by value from a documented versioned projection; reject the narrower gateway schema as the full projection | `argus/observation.py` | CMP-008 |
| `ARGUS2-ARCH-09` Payload/loss/snapshot semantics | Preserve visibility, visible bytes, source size, schema state, declared loss and explicit interval/validity provenance; never synthesize unobserved payload | `argus/observation.py`, `argus/snapshot.py` | CMP-008, CMP-009 |
| `ARGUS2-ARCH-10` Read-only replay/export and metric links | Verify manifest/artifact hashes; return records, diagnostics and declared metric-input links deterministically via JSON/JSONL export | `argus/reader.py`, `argus/cli.py` | CMP-007, CMP-010 |
| `ARGUS2-ARCH-11` Caller authority and offline envelope | Consume only caller-supplied identity/clocks/limits/obligations; no ambient clock/random/network/cross-clock conversion | `argus/api.py`, `argus/limits.py` | CMP-005, CMP-011 |
| `ARGUS2-ARCH-12` Packaging and consumer compatibility | Additive `xverse` namespace/package wheel configuration, one frozen additive consumer entry point, preserved `xverse_xdl` API/CLI | `pyproject.toml`, `src/xverse/__init__.py`, `argus/__init__.py`, `argus/cli.py` | CMP-002, CMP-006, CMP-007, CMP-012 |

## 5. Component allocation

One allocation component record per software requirement (`ARGUS2-SR-001-CMP` … `ARGUS2-SR-012-CMP`),
each linked by one additive `allocated_to` trace link (`ARGUS2-L-101` … `ARGUS2-L-112`). Allocation is
1:1 so later `decomposes_to` (component → unit), `implemented_by` (requirement/component/unit → code
endpoint), and `verified_by`/`analyzed_by`/`validates` links stay unambiguous and every accepted
software requirement keeps exactly one owning allocation.

| Requirement | Component record | Logical elements |
| --- | --- | --- |
| `ARGUS2-SR-001` | `ARGUS2-SR-001-CMP` | `ARGUS2-ARCH-01`, `ARGUS2-ARCH-05` |
| `ARGUS2-SR-002` | `ARGUS2-SR-002-CMP` | `ARGUS2-ARCH-02`, `ARGUS2-ARCH-12` |
| `ARGUS2-SR-003` | `ARGUS2-SR-003-CMP` | `ARGUS2-ARCH-03`, `ARGUS2-ARCH-05` |
| `ARGUS2-SR-004` | `ARGUS2-SR-004-CMP` | `ARGUS2-ARCH-04`, `ARGUS2-ARCH-03` |
| `ARGUS2-SR-005` | `ARGUS2-SR-005-CMP` | `ARGUS2-ARCH-05`, `ARGUS2-ARCH-07` |
| `ARGUS2-SR-006` | `ARGUS2-SR-006-CMP` | `ARGUS2-ARCH-06`, `ARGUS2-ARCH-02` |
| `ARGUS2-SR-007` | `ARGUS2-SR-007-CMP` | `ARGUS2-ARCH-07`, `ARGUS2-ARCH-06` |
| `ARGUS2-SR-008` | `ARGUS2-SR-008-CMP` | `ARGUS2-ARCH-08`, `ARGUS2-ARCH-09` |
| `ARGUS2-SR-009` | `ARGUS2-SR-009-CMP` | `ARGUS2-ARCH-09`, `ARGUS2-ARCH-08` |
| `ARGUS2-SR-010` | `ARGUS2-SR-010-CMP` | `ARGUS2-ARCH-10`, `ARGUS2-ARCH-07` |
| `ARGUS2-SR-011` | `ARGUS2-SR-011-CMP` | `ARGUS2-ARCH-11`, `ARGUS2-ARCH-05` |
| `ARGUS2-SR-012` | `ARGUS2-SR-012-CMP` | `ARGUS2-ARCH-12`, `ARGUS2-ARCH-06` |

## 6. Ownership and change boundary

| Path | Change |
| --- | --- |
| `src/xverse/__init__.py` | **new** additive `xverse` package marker; imports nothing from `xcom` |
| `src/xverse/argus/**` | **new** offline evidence package |
| `tests/thesis_lite/argus/**` | **new** owned neutral fixtures and tests (fixtures only; no production C++ edits) |
| `pyproject.toml` | **additive** wheel configuration and one additive console entry point; no rename of `xverse-xdl` and no change to the `xdl` script |
| `docs/engineering/argus-lite/**` | **new** work-product set |
| `engineering/architecture/components/ARGUS2-*.json` | **new** allocation records |
| `engineering/trace/links.json` | **additive** `allocated_to` links only; every inherited link preserved in order and content |
| `engineering/stage-results/argus2-*.json`, `reports/argus-lite/**`, `reports/review-index.md` | **new** stage and report artifacts |

Consumed read-only and byte-preserved: `src/xverse_xdl/**`, `xdl/**`, `src/xverse/xcom/**`,
`proto/xverse/xcom/v1/**`, existing XDL/C++ tests, `docs/engineering/xcom/**`,
`engineering/verification/measures/**`, all historical `engineering/**` records (other than the
additive `engineering/trace/links.json` links) and the accepted requirements-stage artifacts.

## 7. Data flow (ordered, fail-closed)

1. **Admit inputs.** The caller supplies an explicit fresh output run root, a unique run identity, an
   accepted resolved experiment plan and run envelope, explicit source-byte digests, explicit clock
   identities/units, finite limits and evidence obligations. Nothing is discovered from the environment.
2. **Verify plan binding.** `plan_matches_digest` (verified through the accepted
   `xverse_xdl.experiment_plan` public API) must confirm the recorded digest equals the recomputed body
   digest; the plan/Profile/API versions must be accepted; the envelope identity must not conflict with
   the declared run identity; the run root must not already exist. Any failure rejects before writing.
3. **Open.** The run root is created exclusively and the open manifest is published atomically
   (temporary file → flush/fsync → atomic rename). A `run-opened` event is appended.
4. **Validate and append.** Every appended event is validated against the frozen versioned record
   contract and the caller bounds; a rejected record leaves no partially accepted JSONL line.
5. **Import observations and snapshots.** A documented versioned projection of owned C++
   `ObservationRecord` accessors and separately supplied tap snapshots are imported by value; payload
   visibility, visible bytes, source size, schema state, loss counters, validity state and interval
   provenance are preserved exactly. No tap is attached or polled.
6. **Finalize.** The stream is flushed/fsynced; the event count and stream hash are recomputed; every
   indexed artifact is re-verified; every declared obligation is evaluated; the manifest is replaced
   atomically with the closed state and an explicit `complete`/`incomplete` status. A closed stream that
   fails any check is `incomplete` with reason codes and never upgraded by finalization alone.
7. **Reconstruct read-only.** A bounded reader verifies the manifest and artifact hashes and returns
   records (in ingestion-ordinal order), diagnostics and declared metric-input links as byte-stable
   JSON/JSONL. A corrupt artifact, hash mismatch or exceeded reader bound yields a stable diagnostic and
   a bounded partial result, never silent truncation or invented data.

### 7.1 Read and publication path (terminal-review repair `AR-F01`–`AR-F04`)

The reader is a bounded, fail-closed verifier, not a tolerant parser, and the writer has exactly one
audited manifest-publication point:

1. **Pre-I/O confinement (`AR-F01`).** Before opening anything, resolve the run-root real path and apply
   `os.lstat` to the manifest and stream paths. A traversal/absolute path, an escaping or in-root
   symlink, and a non-regular file are rejected with `ARGUS2-PATH-ESCAPE`, `ARGUS2-PATH-SYMLINK` and
   `ARGUS2-PATH-NOT-REGULAR` respectively, before any byte is read.
2. **Bounded reads before parsing (`AR-F01`).** The manifest is read with an `O_NOFOLLOW` open limited to
   `max_manifest_bytes`; the stream and each line are streamed under `max_event_bytes`, `max_events` and
   `max_read_records` without loading the whole file into memory. Exceeding any bound aborts the read
   with `ARGUS2-BOUND-EXCEEDED` naming the field; an over-long or truncated read is never parsed as
   trusted evidence.
3. **Caller limits are authoritative (`AR-F01`).** The `limits` argument supplied to the read operation
   governs verification. The manifest `limits` echo is *recorded data only* and is never trusted to
   relax a bound; it can only be used as an additional, never-looser, constraint.
4. **Strict full-schema verification (`AR-F03`).** Every event is validated against the complete closed
   nested schema (event, clock, observation, snapshot, manifest `§3`/`§5`/`§6`) including required
   `runId`/`eventId`/`producerId`, per-run `eventId` uniqueness, a strictly increasing
   `ingestionOrdinal` from `1`, `runId` equality with the manifest, and finite values. Malformed
   container types/versions and I/O are converted to bounded stable categorized diagnostics; no
   `TypeError`/`ValueError` escapes.
5. **Assessed completeness (`AR-F02`).** The reader computes `assessedEvidenceStatus` and
   `assessedEvidenceReasons` from what it actually verified; the manifest's recorded `evidenceStatus`
   and `evidenceReasons` are exposed separately as recorded facts. Export reports both and never
   presents `complete` as the primary status when corruption, truncation, loss, an unsupported version
   or an unmet obligation remains.
6. **Single publication chokepoint (`AR-F04`).** Every manifest publication — open, finalize, failure
   and abort — serializes the candidate manifest, measures the actual canonical byte length against
   `max_manifest_bytes`, and only then performs temp-file + flush + `fsync` + atomic replace. On an
   exceeded bound or I/O failure the prior manifest bytes remain and the operation reports a stable
   diagnostic without claiming that `closed`/`complete` state was persisted.
7. **Admission snapshot isolation (`AR-F05`).** Caller-supplied obligations, envelope, source-byte
   digests, clocks and extensions are deep-snapshotted into immutable structures at admission, and
   indexed artifact identity is owned internally; returned views are independent immutable/defensive
   copies, so later caller mutation cannot lower an obligation or rewrite a file hash.

## 8. Quality attributes

| Attribute | Architectural decision | Records |
| --- | --- | --- |
| Fail-closed rejection | Every stage rejects with a stable categorized diagnostic and no partial accepted record; no silent discard, timestamp repair, producer guess or version substitution | CMP-005 and every CMP |
| Determinism | Canonical JSON (sorted keys, compact separators, `allow_nan=False`); ingestion-ordinal selection order; caller-supplied clocks only; no ambient clock/random/locale/environment | CMP-003, CMP-010, CMP-011 |
| Honest completeness | Stream closure and evidence completeness are separate; `complete` requires all declared obligations and integrity checks; loss/degradation/unavailable closure remain visible | CMP-002, CMP-009 |
| Single-writer durability | One owning writer per run; documented flush/fsync/rename boundaries and bounded local (not power-loss, not distributed) guarantee | CMP-006 |
| Confinement | Run-relative safe paths verified on the resolved confined path; traversal, escaping symlink, unsafe name, missing and mutated artifacts rejected | CMP-007 |
| Interoperability without source change | Owned C++ observation projection import plus accepted XDL compiler output; no C++ API/source change and no gateway substitution | CMP-008, CMP-012 |
| Offline neutrality | Standard-library JSON/hash/filesystem only; no network, service, daemon, dashboard, dependency or oracle; caller supplies all numbers | CMP-011 |
| Additive compatibility | Additive `xverse` namespace/entry point; `xverse-xdl` name, `xdl` CLI and `xverse_xdl` imports preserved; installed-wheel consumer verified later | CMP-012 |
| Bounded streaming I/O | Reader/recovery resolve and `lstat` the confined path before I/O, open with `O_NOFOLLOW`, and stream under caller finite bounds; no unbounded `read()` of the manifest or stream | CMP-005, CMP-007, CMP-010; `ARGUS2-ADV-01`, `ARGUS2-ADV-02` |
| Assessed completeness | Reader exposes recorded manifest facts separately from its own assessed status; corruption/truncation/loss is never exported as primary `complete` | CMP-002, CMP-010; `ARGUS2-ADV-03` |
| Strict reader fidelity | Complete closed nested-schema, identity, uniqueness, monotonic-ordinal and finiteness checks; only stable categorized diagnostics, never an uncaught parse exception | CMP-003, CMP-005, CMP-010; `ARGUS2-ADV-04`, `ARGUS2-ADV-05` |
| Publication-bound integrity | Every manifest publication measures the actual serialized bytes; a bound or I/O failure preserves the prior manifest and never claims closure | CMP-002, CMP-006, CMP-012; `ARGUS2-ADV-06` |
| Admission snapshot isolation | Deep snapshot of caller-admitted objects at admission; immutable internal artifact identity; immutable/defensive returned views | CMP-001, CMP-006, CMP-007, CMP-011; `ARGUS2-ADV-07` |

### 8.1 Python language rationale (recorded before implementation)

Python 3.11+ is selected for `src/xverse/argus/**` because the module is an offline, bounded, JSON/JSONL
evidence store whose decisive quality attributes are correctness, determinism, auditable validation and
standard-library portability — not data-plane latency or throughput. The admitted program allocation
places Argus (offline evidence and inspection) in Python and the X-COM communication data plane in
C++20; this slice therefore consumes the accepted C++ observation contract across a versioned
serialized projection rather than linking C++. Python's standard library supplies the required JSON,
SHA-256 and filesystem primitives without a new dependency; the accepted `xverse_xdl` Python API is
already the plan-verification dependency. Memory and concurrency scope are explicitly bounded by the
caller limits and one owning writer, so no throughput-motivated language change is required. Hexagonal
boundary: the owned C++ observation producer is a fixture that serializes the frozen projection; Argus
holds no callback, hub handle or delivery authority.

## 9. Consistency and constraints (constitution check, repeated before design freeze)

- **Production safety (I).** No legacy/compat/blueprint repository, artifact or workload is read,
  executed or changed; all C++/XDL/test/historical files remain byte-preserved. Public evidence uses
  repository-relative paths only.
- **Domain neutrality (II).** Only generic vocabulary appears: run, event, producer, clock domain,
  observation, snapshot, artifact, manifest, obligation, diagnostic, metric input.
- **XDL centrality (III).** The run binds to the accepted resolved plan through the accepted public
  digest API; no competing configuration language is introduced or reparsed.
- **Standards interoperability (IV).** No standard is reimplemented; the accepted X-COM observation
  contract is consumed through a documented projection.
- **Logical/physical separation (V).** Logical observation identities and endpoint/route/provider
  identities are preserved as declared; no physical realization is inferred or attached.
- **Physical hardware (VI).** No device, provider handle, live tap or execution contract is created,
  started, probed or connected.
- **Foundations before compatibility (VII).** A platform capability baseline is extended; no legacy
  adapter, parity or migration work is performed.
- **Repository boundaries (VIII).** Dependencies flow from the admitted planning inputs and accepted
  platform APIs into additive ARGUS2 artifacts; no accepted module depends on Argus.
- **Explicit fidelity and maturity (IX).** Every claim is labelled planned/target; no runtime,
  interoperability, compatibility or readiness claim is made from source or design inspection.
- **Reproducibility and traceability (X).** Requirement→component allocation is 1:1, inputs are
  identified by hash, and facts are separated from inference and unknowns.
- **Capability acceptance gates.** Acceptance criteria, failure semantics, observable behavior,
  compatibility impact, REF-002 dispositions and an accurate maturity label are recorded; the
  SADS register remains target input, and no parent is marked implemented, partial-by-evidence or closed.
- **Scientific values are caller inputs.** No protocol threshold, tolerance, deadline, repetition,
  margin, seed or bound is invented, defaulted or narrowed by this architecture (Constitution IX).

## 10. Traceability

| Architecture element | Requirements |
| --- | --- |
| `ARGUS2-XB-01`, `ARGUS2-ARCH-01`, `ARGUS2-ARCH-05` | `ARGUS2-SR-001`, `ARGUS2-SR-005` |
| `ARGUS2-XB-02`, `ARGUS2-ARCH-03`, `ARGUS2-ARCH-04` | `ARGUS2-SR-003`, `ARGUS2-SR-004` |
| `ARGUS2-XB-03`, `ARGUS2-ARCH-08`, `ARGUS2-ARCH-10` | `ARGUS2-SR-008`, `ARGUS2-SR-010`, `ARGUS2-SR-011` |
| `ARGUS2-XB-04` | `ARGUS2-SR-008`, `ARGUS2-SR-009` |
| `ARGUS2-XB-05`, `ARGUS2-ARCH-07` | `ARGUS2-SR-005`, `ARGUS2-SR-007` |
| `ARGUS2-XB-06`, `ARGUS2-ARCH-02`, `ARGUS2-ARCH-09` | `ARGUS2-SR-002`, `ARGUS2-SR-009` |
| `ARGUS2-XB-07`, `ARGUS2-ARCH-11` | `ARGUS2-SR-011` |
| `ARGUS2-XB-08`, `ARGUS2-ARCH-12` | `ARGUS2-SR-012` |
| `ARGUS2-ARCH-06` | `ARGUS2-SR-006`, `ARGUS2-SR-007` |
| `ARGUS2-ARCH-09` | `ARGUS2-SR-008`, `ARGUS2-SR-009` |

Each `ARGUS2-SR-###-CMP` record lists its owning `ARGUS2-SR-###`, its boundaries, interfaces,
dependencies, planned paths and error conditions, so the unit-specification stage can attach one or more
units per component with `decomposes_to` links without ambiguity. `implemented_by`, `verified_by` and
`analyzed_by` relations are owned by later stages and are not claimed here.

## 11. Negative cases (architecture view)

Executable cases and exact test identifiers are frozen in the unit-specification and verification-design
stages; this table fixes only the architecture-level behaviour of each boundary.

| Boundary / element | Injected defect | Required behaviour |
| --- | --- | --- |
| `ARGUS2-XB-01`, `ARGUS2-ARCH-01` | mutated plan digest, unsupported major version, envelope identity conflicting with the run identity, or an already-existing run root | reject with a stable structured diagnostic; no run opened and nothing overwritten |
| `ARGUS2-XB-02`, `ARGUS2-ARCH-03` | duplicate event identity, unknown event-schema major, required identity field missing, or an out-of-order producer sequence presented as order | reject or retain exactly as declared; ingestion ordinal never presented as temporal/causal order |
| `ARGUS2-XB-02`, `ARGUS2-ARCH-04` | clock value without an explicit domain/unit, or a record requiring an undeclared clock mapping | reject/report unresolved; no implicit wall-clock read, inferred unit, or cross-domain comparison |
| `ARGUS2-XB-05`, `ARGUS2-ARCH-07` | traversal segment, escaping symlink, unsafe artifact name, missing artifact, or byte-mutated artifact | reject or report; no write outside the run root, hash/size verification fails closed |
| `ARGUS2-XB-06`, `ARGUS2-ARCH-02` | truncated last JSONL record, interrupted finalization, unmet obligation, declared loss, or unavailable interval closure | classify the run `incomplete` with reason codes; never upgrade to `complete` by finalization alone |
| `ARGUS2-XB-04`, `ARGUS2-ARCH-08` | gateway protobuf `ObservationRecord` supplied as the full owned projection | reject unless a versioned separate mapping records every missing field as unavailable; no fabricated metadata |
| `ARGUS2-ARCH-09` | metadata-only/redacted record with bytes, prefix truncation, or a snapshot whose interval is unclosed while counters look benign | preserve visibility exactly; counters never stand in for interval closure; known loss stays visible |
| `ARGUS2-ARCH-10` | corrupt artifact, hash mismatch, or exceeded reader bound | stable diagnostic plus a bounded partial result; no silent truncation and no invented data |
| `ARGUS2-ARCH-11` | reliance on an implicit clock/identity/limit, a remote lookup, or a control/metric/oracle capability | rejected or absent with a stable structured diagnostic; no network/service is acquired |
| `ARGUS2-XB-08`, `ARGUS2-ARCH-12` | an accepted `xverse_xdl` import, `xdl` CLI entry point, accepted C++ contract, or required artifact would change | additive-only rule fails closed; installed-wheel consumer compatibility is verified later |
| `ARGUS2-XB-09`, `ARGUS2-ARCH-05`, `ARGUS2-ARCH-07`, `ARGUS2-ARCH-10` | traversal/absolute manifest or stream path, escaping or in-root symlink, non-regular file, oversized/truncated manifest or stream, or a damaged manifest that echoes a huge `limits` value | reject **before** I/O with `ARGUS2-PATH-*` / `ARGUS2-BOUND-EXCEEDED`; caller limits stay authoritative and no bound is relaxed by recorded data |
| `ARGUS2-XB-10`, `ARGUS2-ARCH-10` | a manifest declares `complete` while the reader detects a truncated line, missing/mutated artifact, unsupported version or malformed shape | export an assessed status of `incomplete` (never primary `complete`); recorded manifest facts are preserved separately as recorded facts |
| `ARGUS2-XB-11`, `ARGUS2-ARCH-03`, `ARGUS2-ARCH-05`, `ARGUS2-ARCH-10` | missing `runId`/`eventId`/`producerId`, duplicate `eventId`, non-monotonic `ingestionOrdinal`, event `runId` differing from the manifest, non-finite clock value, JSON scalar/array where an object is required, or unknown nested key | reject with a stable bounded diagnostic and a bounded partial result; no uncaught `TypeError`/`ValueError` and no silently accepted record |
| `ARGUS2-XB-12`, `ARGUS2-ARCH-02`, `ARGUS2-ARCH-06` | a manifest whose finalize/abort publication grows past `max_manifest_bytes` from artifacts, obligations or finalized metadata, or whose replace raises `OSError` | refuse to publish; the prior manifest bytes are preserved; a stable `ARGUS2-BOUND-EXCEEDED`/`ARGUS2-IO-FAILURE` diagnostic is returned with no `closed`/`complete` persistence claim |
| `ARGUS2-XB-13`, `ARGUS2-ARCH-01`, `ARGUS2-ARCH-06`, `ARGUS2-ARCH-11` | caller mutates an admitted nested `detail` object (e.g. lowering `min-observations.minimum`) or mutates a returned artifact/index/record view after admission | admitted snapshot and indexed file hashes are unchanged; returned views cannot rewrite internal facts |

### 11.1 Frozen adversarial case registry (freeze before code)

These architecture-level adversarial case identities are **frozen now**; later stages must bind each to
at least one exact pytest-discoverable test identifier (unit and, where applicable, integration and
validation), and must not weaken or delete the case. They encode the terminal-review findings and their
reproduction labels exactly.

| Adv. case | Terminal finding / reproduction | Boundary and element | Required architecture behaviour |
| --- | --- | --- | --- |
| `ARGUS2-ADV-01` | `AR-F01` / `AR-F01-path` | `ARGUS2-XB-09`, `ARGUS2-XB-05`, `ARGUS2-ARCH-07`, `ARGUS2-ARCH-10` | Confined regular-file checks (`os.lstat`, `O_NOFOLLOW`) occur **before** any I/O for the manifest and stream; traversal, escaping/in-root symlink and non-regular paths are rejected with stable diagnostics and no read occurs. |
| `ARGUS2-ADV-02` | `AR-F01` / `AR-F01-bounds` | `ARGUS2-XB-09`, `ARGUS2-ARCH-05`, `ARGUS2-ARCH-10` | Manifest/stream/line/event/diagnostic reads are bounded before parsing; the caller `limits` argument is authoritative and limits echoed by a damaged manifest cannot relax a bound; `ARGUS2-BOUND-EXCEEDED` names the field. |
| `ARGUS2-ADV-03` | `AR-F02` / `AR-F02` | `ARGUS2-XB-10`, `ARGUS2-ARCH-10` | The reader exposes `recorded` and `assessed` evidence status/reasons separately; corrupt/truncated/loss evidence is exported as assessed `incomplete`, never primary `complete`. |
| `ARGUS2-ADV-04` | `AR-F03` / `AR-F03-identities` | `ARGUS2-XB-11`, `ARGUS2-ARCH-03`, `ARGUS2-ARCH-05`, `ARGUS2-ARCH-10` | Required run/event/producer identity, per-run `eventId` uniqueness, strictly increasing `ingestionOrdinal`, run-ID consistency and finite values are all verified on read. |
| `ARGUS2-ADV-05` | `AR-F03` / `AR-F03-malformed` | `ARGUS2-XB-11`, `ARGUS2-ARCH-03`, `ARGUS2-ARCH-05`, `ARGUS2-ARCH-10` | Malformed container types, unsupported versions and I/O faults produce bounded stable diagnostics; no `TypeError`/`ValueError` escapes and no partial record is trusted. |
| `ARGUS2-ADV-06` | `AR-F04` / `AR-F04` | `ARGUS2-XB-12`, `ARGUS2-ARCH-02`, `ARGUS2-ARCH-06` | Every manifest publication enforces the actual serialized `max_manifest_bytes` bound; bound/I/O failure preserves prior manifest bytes and reports a stable error without claiming closure. |
| `ARGUS2-ADV-07` | `AR-F05` / `AR-F05` | `ARGUS2-XB-13`, `ARGUS2-ARCH-01`, `ARGUS2-ARCH-06`, `ARGUS2-ARCH-11` | Admitted nested obligations/envelope/digests/clocks/extensions are deep-snapshotted; mutation after admission cannot lower an obligation or alter an indexed artifact hash; returned views are immutable/defensive copies. |

## 12. Next step and model recommendation

Next stage: **unit_specification** — freeze interfaces, state/concurrency, inputs/outputs/errors/
invariants, planned paths, table-driven expected outcomes, adversarial/metamorphic cases, exact
pytest-discoverable test identifiers (including duplicate IDs, unknown versions, partial writes/
recovery, exceeded bounds, source digest mutation, missing causal/interval closure, payload
visibility/loss, unsafe paths/symlinks and installed-wheel consumer compatibility) and static checks
against this architecture and `detailed-design.md`. Each frozen adversarial case
`ARGUS2-ADV-01`–`ARGUS2-ADV-07` (§11.1) must be bound to at least one exact pytest identifier, and no
existing regression case may be removed or weakened while the five findings are repaired.

Model recommendation: the pinned `deepseek-v4-flash` with **high** reasoning remains the most
cost-effective and the only authorized route for that work, because it is deterministic contract
transcription over already-frozen architecture/design inputs and the accepted XDL/X-COM source
contracts, with no stronger-reasoning need. There is no new Terra/Luna/Sol/Astra engineering route in
this package, no fallback and no subagent; no model switch is claimed or performed, and no benchmark or
exact-cost claim is made. Blocker: none at this stage; no source, packaging or test code may be written
until the four design stages complete and the precode gate passes, and legacy/production execution
remains unauthorized.
