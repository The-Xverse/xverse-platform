# Argus Lite Phase 2 — software requirements

**Feature:** ARGUS2 (Argus Lite Phase 2 — bounded run evidence persistence, X-COM observation import and read-only reconstruction)
**Stage:** requirements (repository-owned Spec Kit work-product workflow, ADR-0020)
**Attempt:** ARGUS2 attempt 1
**Date:** 2026-10-01
**Status:** engineering requirements baseline for the Phase 2 Argus Lite candidate. `accepted` records mean
*internal engineering intent* only. Nothing in this document is implementation satisfaction, runtime
evidence, scientific validity, compatibility/parity, live-readiness, or external delivery acceptance.

## 1. Scope and authority

This document records the bounded software allocation derived from the admitted thesis planning inputs
for **Phase 2 only**: persist a bounded, versioned causal evidence stream plus an atomic run artifact
manifest, consume an owned X-COM observation projection, and reconstruct that evidence read-only.

Authoritative planning remains external to this repository (thesis-owned, per
`docs/adr/ADR-THESIS-LITE-0001.md`). It is **not** copied into the platform specification set. The
inputs below were admitted read-only and are referenced by identity/hash, not reproduced:

| Admitted input identity | SHA-256 |
| --- | --- |
| `specs/023-argus-lite-evidence/spec.md` | `e3d189f4c97667f04d9c3aea23c513ff2e97bdfe8cec503a480bd86a4d3430b4` |
| `specs/023-argus-lite-evidence/plan.md` | `da65f8cce216b665a3b915a460fbc447baeb7cda0b7d55699b9b1353d8c18e18` |
| `specs/023-argus-lite-evidence/research.md` | `02e562313a049256c07209a936391c0070b8c2deed391717f1ba233c06f13241` |
| `specs/023-argus-lite-evidence/data-model.md` | `fcbcb0f5f4d054af57ed380330613eeb7ff2ddc95799e6df3355e21bf6a999d0` |
| `specs/023-argus-lite-evidence/contracts/evidence.md` | `b4347e07796e52449585aad7133912a25a5906b793164ad6086510fbe8ad9ab1` |
| `specs/023-argus-lite-evidence/tasks.md` | `5419524845ef5351151c27e98a262aeef458a70c6cead7cc019fecf7b4d04000` |
| `specs/023-argus-lite-evidence/quickstart.md` | `47fcdaff4c35ff45b2c0cb7ef3881a8e7debc8b04a7c77b1b9a1c106a18bdd6c` |
| `specs/021-thesis-lite-program/backlog.json` | `54fff85d988e7b46eb2546e1ea77c14dc15bd029b738b190e444f56ef0cb6c57` |
| `specs/021-thesis-lite-program/requirements-priorities.json` | `9c3fec63ce6b26ab1aa0d72e901752d0a5f4cc16784add5f30e9052abb36a8d0` |
| `docs/adr/ADR-THESIS-LITE-0001.md` | `fa247b51fd77a55c77d928350e6b1c061f3d2eda2a9963ed2e0b0d22bc05df65` |
| `engineering-instructions.json` (workflow contract) | `27b6392afd0f3e7729303b8ce7904734a8893d1e863ed76769d279d397c91a28` |
| admitted input manifest (`manifest.json`) | `b62e244fdcbf6e4bb8178eaaaf86bc32e0483b85a0bc4c9a8b8298bdee80e6b7` |

**Admitted accepted platform baseline revision:** `c1fd213cd00259b74f8308d8ca58157ea985aaa0`
(Phase 1 XDL Lite accepted and merged; `specs/021-thesis-lite-program/backlog.json` phase 1
`status: accepted_and_merged`, `main_commit` `c1fd213cd00259b74f8308d8ca58157ea985aaa0`).

Local platform source anchors inspected read-only (unchanged by this stage):

* REF-002 SADS allocation register — `docs/architecture/sads-requirements-traceability.json`
  (`d932bea5203166df71273f0216bf50008726a062b4c33e8f6f2678c625660abc`; source document
  `ed99aa6caf1995e70a555edc36fed1938a071e60f3c1f6a4eebaae2c3423cb5a`) and its coverage rule in
  `docs/architecture/SADS_REQUIREMENTS_TRACEABILITY.md`.
* Projection of P2 parents — `specs/021-thesis-lite-program/requirements-priorities.json` (external,
  admitted; `9c3fec63ce6b26ab1aa0d72e901752d0a5f4cc16784add5f30e9052abb36a8d0`).
* Accepted XDL experiment-plan public API and digest semantics — `src/xverse_xdl/experiment_plan.py`
  (`API_VERSION = xverse.io/xdl/v1alpha1`, `PROFILE_NAMESPACE = io.xverse.experiment`,
  `PLAN_VERSION = "1"`, domain-separated `compute_plan_digest` / `plan_matches_digest`).
* Accepted C++ X-COM observation contract — `src/xverse/xcom/include/xverse/xcom/observation.hpp`
  (`kObservationContractVersion = 1.0.0`), `docs/xcom/observation-boundary.md`.
* Distinct narrower gateway schema — `proto/xverse/xcom/v1/tool_gateway.proto` (`ObservationRecord`
  carries `identity`, `route_id`, `contract_id`, `clock_domain`, `sequence`, `outcome`,
  `payload_state`, `payload_view`, `payload_bytes`; it omits the owned record's source/observation
  clock pair, correlation/causation, schema identity/version, provider outcome normalization, tap
  identity and retention counters).
* Additive packaging surface — `pyproject.toml` (`xverse-xdl` wheel packages `src/xverse_xdl` only).

The accepted platform baseline is the last reviewed checkpoint. This stage adds only the ARGUS2
requirements work products named in section 8; it changes no accepted requirement, design, unit,
measure, validation, stage, test, schema, source, or ADR.

Boundary note carried from the program/AGENTS guidance: the older platform capability-scaffolding
boundary is superseded **only** for this explicit, bounded Argus scope, and only to the extent of the
admitted Phase 2 allocation recorded here. No legacy, production, compat or blueprint artifact is
touched, and no runtime execution is authorized.

## 2. Derivation method

1. The admitted program projection selects **12** existing REF-002 target-architecture parents for P2
   (Argus Lite) — `specs/021-thesis-lite-program/backlog.json` phase 2 `source_ids`. The projection
   creates **no new system requirement IDs** (`new_system_requirement_ids: []`) and marks every
   selected parent `allocated` with `planned_extent: bounded_partial` and
   `full_system_requirement_claim: false`.
2. Exactly **one bounded evidence allocation per existing parent** is derived, in the parent order
   fixed by the workflow contract and repeated by `specs/023-argus-lite-evidence/spec.md` (line 6),
   producing `ARGUS2-SR-001` … `ARGUS2-SR-012`. No further ARGUS2 software records were needed.
3. Each `ARGUS2-SR-0nn` is linked to its parent with **one** additive `refines` link
   (`ARGUS2-L-0nn`) in `engineering/trace/links.json`, and carries the parent in its `parents` field.
   Source anchors are existing `XVE-SYS` IDs; no new source ID and no new system requirement is
   created.
4. Parent anchors are recorded allocation-only in `engineering/requirements/XVE-SYS-*.json` using
   their **original** IDs (including the nonstandard zero padding `XVE-SYS-00015`), original
   `disposition: allocated`, `maturity: architectural-target`, section and owner. Internal SADS
   requirement text is **not** reproduced in this repository.
5. No source requirement ID, text, hash, or original disposition is rewritten. No parent is closed;
   each software requirement claims only its bounded Phase 2 evidence contribution.

Parent order and allocation (one software requirement each):

| # | Parent (original ID) | SADS section | SADS owner | Original disposition | Projection extent | ARGUS2 software requirement |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `XVE-SYS-00015` | Scenario management | Maestro / Blueprints / UI / SDK | allocated | bounded_partial | `ARGUS2-SR-001` |
| 2 | `XVE-SYS-0016` | Scenario management | Maestro / Blueprints / UI / SDK | allocated | bounded_partial | `ARGUS2-SR-002` |
| 3 | `XVE-SYS-0179` | Monitoring, logging, and observability | Argus | allocated | bounded_partial | `ARGUS2-SR-003` |
| 4 | `XVE-SYS-0183` | Monitoring, logging, and observability | Argus | allocated | bounded_partial | `ARGUS2-SR-004` |
| 5 | `XVE-SYS-0185` | Monitoring, logging, and observability | Argus | allocated | bounded_partial | `ARGUS2-SR-005` |
| 6 | `XVE-SYS-0186` | Monitoring, logging, and observability | Argus | allocated | bounded_partial | `ARGUS2-SR-006` |
| 7 | `XVE-SYS-0188` | Monitoring, logging, and observability | Argus | allocated | bounded_partial | `ARGUS2-SR-007` |
| 8 | `XVE-SYS-0194` | Monitoring, logging, and observability | Argus | allocated | bounded_partial | `ARGUS2-SR-008` |
| 9 | `XVE-SYS-0198` | Results management and export | Results / Argus / SDK | allocated | bounded_partial | `ARGUS2-SR-009` |
| 10 | `XVE-SYS-0201` | Results management and export | Results / Argus / SDK | allocated | bounded_partial | `ARGUS2-SR-010` |
| 11 | `XVE-SYS-0203` | Results management and export | Results / Argus / SDK | allocated | bounded_partial | `ARGUS2-SR-011` |
| 12 | `XVE-SYS-0211` | Results management and export | Results / Argus / SDK | allocated | bounded_partial | `ARGUS2-SR-012` |

Parent-order normalization: the admitted allocation order is **order-fixed**, not numerically sorted
(`XVE-SYS-00015` precedes `XVE-SYS-0016`; the four Results parents follow the six Observability
parents). The table above is the authoritative allocation order and is the order used for
`ARGUS2-SR-001..012`.

Each allocation covers only the **evidence slice** of its parent's section: the two Scenario-management
parents contribute run identity/plan binding and stream/manifest persistence; the six Observability
parents contribute event identity, clock/causation uncertainty, validation and bounds, single-writer
durability/recovery, confined artifacts and the owned X-COM observation projection; the four
Results-management parents contribute payload/loss/interval semantics, read-only replay/export with
metric-input links, the absence of control/actuation/oracle authority, and the additive consumer
packaging compatibility that later phases must not break. No parent scope beyond that bounded evidence
slice is claimed.

## 3. Software requirements

Every record below: `id: ARGUS2-SR-0nn`, `revision: 1`, `level: software`, `status: accepted`
(internal intent), `disposition: allocated`, `planned_extent: bounded_partial`,
`full_system_requirement_claim: false`, `phase: P2`. Record files:
`engineering/requirements/ARGUS2-SR-0nn.json`.

### ARGUS2-SR-001 — Run identity, verified plan binding and separated source-byte provenance

*Refines `XVE-SYS-00015`.* The Phase 2 Argus evidence writer shall create one fresh run bound to an
explicitly supplied run identity, an accepted resolved experiment plan and run envelope verified
through the accepted `xverse_xdl.experiment_plan` public API, using the accepted semantic
`plan_matches_digest`/`compute_plan_digest` semantics; it shall keep the semantic plan identity
separate from source-byte provenance and shall reject a plan-digest mismatch, an unsupported
plan/Profile/API version, a conflicting envelope identity, or an already-existing output run root
before overwriting anything.

Acceptance criteria:

* Positive: an accepted resolved plan whose recorded digest matches its recomputed body digest, with
  one caller-supplied unique run identity and a fresh output root, opens exactly one run that records
  the plan version, Profile/API version, semantic plan digest and the separate source-byte digests.
* Negative: a mutated plan digest, an unsupported major version, an envelope identity conflicting with
  the declared run identity, or an existing run root is rejected with a stable structured diagnostic
  and no run is opened or overwritten.
* Source-byte provenance is never used as, or substituted for, the semantic plan identity, and no
  configuration dialect is reparsed and no accepted plan is executed.

### ARGUS2-SR-002 — Bounded versioned event stream and atomic run manifest with explicit completeness

*Refines `XVE-SYS-0016`.* Argus shall append validated owned events to a versioned JSONL evidence
stream and publish an atomic JSON run manifest carrying artifact identities, sizes and content hashes,
the writer state, the event count/hash, the caller-declared evidence obligations and an explicit
evidence status; finalization shall claim complete evidence only when every declared obligation and
the integrity checks pass, and shall otherwise classify the run explicitly as incomplete.

Acceptance criteria:

* Positive: a run whose declared obligations are satisfied finalizes with an atomically published
  manifest whose artifact index, byte sizes and content hashes verify against the stream on close.
* Negative: a closed stream with a truncated last record, a missing artifact, a declared observation
  loss, or an unmet obligation is reported explicitly as incomplete and never becomes complete by
  finalization alone.
* Stream closure and evidence completeness are reported as separate facts; no automatic success,
  scientific-validity, safety, or readiness claim follows.

### ARGUS2-SR-003 — Versioned event identity, producer sequence and correlation/causation links

*Refines `XVE-SYS-0179`.* Argus shall persist a versioned event record schema that carries a schema
  version, the owning run identity, a unique event identity, a producer identity, the local ingestion
  ordinal and the event kind, together with an optional producer sequence and optional
  correlation/causation references, and shall reject an event that does not satisfy the frozen
  versioned record contract.

Acceptance criteria:

* Positive: a valid event is persisted once with its schema version, unique event identity, producer
  identity, ingestion ordinal, kind and any declared sequence/correlation/causation references
  preserved exactly.
* Negative: an unknown event-schema major version, a duplicate event identity within one run, or a
  record missing a required identity field is rejected with a stable structured diagnostic and no
  partial accepted record is retained.
* Ingestion ordinal is a local deterministic stream position; it is never presented as temporal or
  causal order.

### ARGUS2-SR-004 — Explicit source and observation clock domains without inferred conversion

*Refines `XVE-SYS-0183`.* Argus shall retain both clock domains and timestamps where a record declares
  them — an explicit clock-domain identity plus a declared unit/representation per value — and shall
  distinguish ingestion order from temporal and causal order; it shall make no implicit wall-clock
  read, no inferred unit, no random identity and no cross-clock-domain comparison or conversion, and
  shall keep an unknown clock mapping, a missing predecessor and an unobserved interval explicit
  rather than repaired.

Acceptance criteria:

* Positive: source and observation clock domains and their values are stored with their caller-declared
  units and survive read-only reconstruction unchanged.
* Negative: a clock value without an explicit domain/unit, or a record requiring a clock mapping the
  caller did not declare, is rejected or reported as unresolved with a stable structured diagnostic.
* Unknown mappings, unresolved causal references and unobserved intervals remain visible as
  uncertainty; no global timeline is fabricated by sorting timestamps across domains.

### ARGUS2-SR-005 — Fail-closed validation with stable diagnostics and caller-configured finite bounds

*Refines `XVE-SYS-0185`.* Argus shall reject malformed or non-finite values, duplicate identities,
  unsupported versions, unsafe or oversized inputs and any violated caller-configured finite bound
  with a stable structured diagnostic that distinguishes input rejection, I/O failure, unsupported
  schema, corrupt artifact, missing evidence and known observation loss; it shall not silently
  discard a record, repair a timestamp, guess a producer, substitute an unknown version or accept a
  partial record.

Acceptance criteria:

* Positive: every accepted event and artifact is inside every applicable caller-configured finite
  bound (bytes, events, identities, diagnostics, manifest size, causal-index size, streaming reads)
  and produces no diagnostic.
* Negative: each declared finite bound has at least one independent negative case that exceeds it and
  observes the bound-exceeded diagnostic; each diagnostic category is distinguishable from the
  others.
* Bounds are caller-supplied implementation limits, not scientific, safety or performance thresholds,
  and no diagnostic is produced without an actual violation.

### ARGUS2-SR-006 — Single-writer state, documented durability and non-mutating recovery

*Refines `XVE-SYS-0186`.* Argus shall enforce exactly one owning writer per run and a writer state
  machine (`new` → `open` → `closed`, or `open` → `failed`), reject reuse or overwrite of an existing
  run, and document its flush/fsync/rename boundaries and partial-write handling; recovery shall
  reopen only bounded prefixes and report incomplete or damaged evidence **without** rewriting,
  upgrading or mutating the original evidence files.

Acceptance criteria:

* Positive: a single writer appends, flushes at the documented boundaries and finalizes by atomic
  replacement, leaving the stream and manifest internally consistent.
* Negative: a second concurrent or repeated writer for the same run, an interrupted finalization, or a
  truncated last JSONL record is detected and reported as failed/incomplete; reopening the damaged run
  leaves every original byte unchanged.
* No power-loss durability is claimed beyond the explicitly documented and verified filesystem
  contract; the claim is stated as a bounded local guarantee, not a distributed or hardware guarantee.

### ARGUS2-SR-007 — Confined artifacts, safe run-relative paths and integrity verification

*Refines `XVE-SYS-0188`.* Argus shall keep every written artifact inside the explicit run root,
  reject path traversal, escaping symlinks and unsafe artifact names, verify that an indexed artifact
  is a regular confined file, and detect a missing artifact or a mutated artifact by comparing its
  recorded size and content hash.

Acceptance criteria:

* Positive: every artifact is indexed with a run-relative safe path, media/schema version, byte size,
  content hash and role, and re-verifies on read.
* Negative: a traversal segment, a symlink escaping the run root, an unsafe artifact name, a missing
  artifact and a byte-mutated artifact are each rejected or reported with a stable structured
  diagnostic and no write outside the run root ever occurs.
* File and symlink checks are performed on the confined path rather than on caller-supplied text.

### ARGUS2-SR-008 — X-COM owned observation projection import with preserved accessor semantics

*Refines `XVE-SYS-0194`.* Argus shall consume a documented, versioned serialized projection of the
owned C++ X-COM `ObservationRecord` values, mapping its accessors by value — logical contract/interface/
endpoint/schema identities and versions, interaction/origin, source and observation clocks/timestamps,
optional sequence, correlation/causation, route/provider, source payload size, normalized provider
outcome, payload view/schema state, visible bytes, declared tap identity and retention-time counters —
and shall not attach or pull a live tap, acknowledge a validity interval, change provider delivery,
reserve lossless capacity, dispatch messages, or interpret a provider success outcome as experiment
success.

Acceptance criteria:

* Positive: an imported projection produced by a real owned C++ producer fixture preserves every
  listed accessor value, and the importing process holds no callback, mutable hub handle or delivery
  authority.
* Negative: the narrower tool-gateway protobuf observation is rejected as the full owned projection
  unless an explicitly versioned separate mapping records each missing field as unavailable; missing
  metadata is never fabricated.
* No tap is attached or polled, no validity interval is acknowledged, no delivery behaviour changes,
  and no provider outcome is promoted to an experiment-validity claim.

### ARGUS2-SR-009 — Payload visibility, loss and interval/snapshot semantics preserved honestly

*Refines `XVE-SYS-0198`.* Argus shall preserve payload visibility exactly as projected — metadata-only
  and redacted records contain no payload bytes, a bounded prefix remains explicitly truncated,
  complete and omitted states stay distinguishable, and the schema state remains undecoded — and shall
  import separately supplied tap snapshots carrying final counters, backpressure and the declared
  validity effect/state with explicit interval provenance; retention-time counters shall not stand in
  for absent interval closure.

Acceptance criteria:

* Positive: a metadata-only, a redacted, a bounded-prefix-truncated and a complete-payload record each
  reconstruct with the same visibility state, visible byte count and source payload size as projected;
  snapshots reconstruct with their counters, backpressure and validity state.
* Negative: a run whose interval closure is unavailable or whose known drops/coalescing/degraded
  intervals remain is reported as incomplete or degraded and cannot be made complete by finalization
  alone.
* Loss and coalescing remain visible even after stream closure, and no unobserved payload is
  synthesized.

### ARGUS2-SR-010 — Bounded read-only replay/export with deterministic selection and metric-input links

*Refines `XVE-SYS-0201`.* Argus shall provide a bounded read-only reader that verifies manifest and
artifact hashes and returns records, diagnostics and declared metric-input links through JSON/JSONL
export; repeated reads of unchanged inputs shall yield equal content and a deterministic selection
order, and replay shall be evidence reconstruction only, never component, fault, lifecycle or
evaluation-oracle execution.

Acceptance criteria:

* Positive: two consecutive exports of an unchanged run produce byte-equal content and identical
  record ordering, and declared metric/observer references link to captured artifact/event selections
  without computing any metric.
* Negative: a corrupt artifact, a hash mismatch or an exceeded reader bound is reported with a stable
  structured diagnostic and a bounded partial result rather than silent truncation or invented data.
* No evaluation oracle is invoked, no metric value is computed, and no control or actuation output is
  produced.

### ARGUS2-SR-011 — Explicit caller authority, offline operation and absence of control authority

*Refines `XVE-SYS-0203`.* The caller shall supply the run identity, clock identities/units, finite
limits and evidence obligations; Argus shall operate offline on JSON/JSONL only, with no implicit wall
clock, no random identity, no remote lookup and no cross-clock conversion, and shall acquire no
network service, dashboard, extra dependency or runtime service, no metrics computation, no control
or actuation authority, no live tap bridge and no evaluation oracle.

Acceptance criteria:

* Positive: a run created with explicit caller-supplied identity, clocks, limits and obligations
  performs no network access, starts no service and produces only JSON/JSONL evidence inside the run
  root.
* Negative: an attempt to rely on an implicit clock/identity/limit, a remote lookup, or a control,
  metric-computation or oracle capability is rejected or absent with a stable structured diagnostic.
* The Phase 2 slice adds no dependency and no runtime service beyond the accepted standard-library and
  admitted packaging surface.

### ARGUS2-SR-012 — Additive packaging, installed-wheel consumer compatibility and preserved contracts

*Refines `XVE-SYS-0211`.* Argus shall be delivered as an additive `xverse` namespace/package wheel
configuration that does not rename `xverse-xdl`, change the existing `xdl` CLI or break installed
imports, shall expose one frozen additive consumer entry point, and shall preserve the accepted XDL
plan/Profile/API versions, the accepted XDL digest reuse and the accepted C++ X-COM implementation,
namespaces and contracts without any existing C++ API or source edit.

Acceptance criteria:

* Positive: the built wheel installs offline and, outside the source tree, imports both `xverse.argus`
  and the existing `xverse_xdl.experiment_plan` from the installed wheel only, and the owned Argus
  tests run against that installed wheel with an empty `PYTHONPATH`.
* Negative: an unknown major schema version is rejected, additive unknown-field behavior is defined
  explicitly rather than silently accepted, and no installed `xverse_xdl` import, CLI entry point or
  accepted C++ contract is broken by the additive packaging change.
* The additive entry point is frozen by the design stage; no existing C++ API/source and no accepted
  XDL/X-COM validation is relaxed.

## 4. Global constraints (apply to every ARGUS2 software requirement)

* **No fallback** and no alternative model or route is authorized for this work.
* **No runtime, live or production execution**: no legacy or production workload, no live tap
  attachment, no fault/lifecycle action, no metrics computation, no dashboard and no oracle access.
* **No control authority**: Argus owns storage and offline inspection only; it acquires no
  orchestration, actuation or provider-delivery authority.
* **Caller-supplied authority**: clock identities/units, run ID, finite limits and evidence
  obligations are caller inputs; no scientific protocol number, threshold, deadline or seed is
  invented.
* **No new system ID and no parent closure**: no REF-002 system requirement ID is created, and no
  parent disposition is promoted, reclassified or closed by this slice.
* **No production change**: no legacy, compat, blueprint, accepted C++ X-COM or accepted
  assurance/oracle artifact is modified, and no historical accepted requirement/design/unit/measure/
  validation/stage record or ADR is rewritten.
* **Preserve accepted inputs**: the accepted XDL plan/Profile/API versions and digest semantics and
  the accepted C++ X-COM observation contract remain authoritative; the narrower gateway protobuf is
  never substituted for the owned record.
* **No next phase**: Phase 3 (Maestro Lite) and beyond are out of scope and are not started.

## 5. Traceability

* Forward: each `ARGUS2-SR-0nn` refines its parent anchor through one additive `refines` link
  (`ARGUS2-L-0nn`) in `engineering/trace/links.json`.
* Backward: the same link set supports parent → refining-child traversal (the traceability-matrix
  lineage/ancestor walk); anchors are `engineering/requirements/XVE-SYS-*.json`.
* For 11 parents a fresh allocation-only anchor record is added by this stage. The
  `XVE-SYS-0016` anchor already exists from the accepted Phase 1 stage and is **preserved
  byte-identically** (it is bound by the `xdl1-requirements` stage artifact hash), so its inherited
  `refined_by` array still names only `XDL1-SR-007`; the ARGUS2 backward relation for that parent is
  carried instead by the additive `refines` link `ARGUS2-L-002` and by the `parents` field of
  `ARGUS2-SR-002`. This is a deliberate immutability choice, not a missing relation.
* The remaining relations required of accepted software requirements — `allocated_to`,
  `implemented_by`, `verified_by` — are owned by the architecture, verification-design and
  implementation stages and are **not** claimed here. Until they exist, the ARGUS2 requirements are
  intentionally untraced downstream and no completeness claim is made.

## 6. Maturity and limitations

* Maturity of every item in this document: **planned / target** — not implemented, not verified, not
  accepted for delivery. Source inspection, and any local check, does not demonstrate runtime success.
* `status: accepted` on these records means internal engineering intent only.
* The SADS register is target input, not evidence that any capability exists. No REF-002 parent is
  marked implemented, partial-by-evidence, or closed by this stage.
* Known limitation: the accepted Phase 2 planning bundle (`specs/023-argus-lite-evidence/spec.md`,
  "Scope, compatibility and authority"; `specs/023-argus-lite-evidence/plan.md`, "Verification and
  launch controls") names a required launch-evidence `admission/review.md` that is **not** among the
  inputs admitted for this run. It is recorded as an external, unverified, later-gate input rather
  than fabricated or substituted, and it is not a blocker for this requirements baseline.
* Known limitation: the 12 new accepted software requirements have no
  `allocated_to`/`implemented_by`/`verified_by` links yet, so `validate_trace` cannot pass until the
  architecture, implementation and verification-design stages add them. No completeness is claimed.
* Known scheduled refresh: updating the current pointer `engineering/project.json` changes its bytes
  and therefore makes the 21 pre-existing `implemented_by` code-endpoint links that target
  `engineering/project.json` stale. Following the admitted workflow, the requirements stage records
  this finding and leaves the inherited trace bytes intact; refreshing exactly those mutable
  `engineering/trace/links.json` code endpoints is assigned to the validation stage.
* Inputs recorded above are the exact admitted identities; no absolute worker path and no credential
  is recorded.

## 7. Next step and model recommendation

Next stage: **architecture** — freeze the versioned event/manifest/projection schemas, the public
Python API/CLI and additive consumer entry point, XDL digest reuse, single-writer state and durability
steps, caller bounds, confined-artifact path rules, incomplete classification, clock/causation
representation, payload/loss/snapshot mapping, read-only replay/export, metric-input links and the
additive namespace/wheel packaging, and record the Python language rationale with a repeated
constitution check.

Model recommendation: the pinned `deepseek-v4-flash` with **high** reasoning is the most
cost-effective and the only authorized route for that contract-freezing work, because it is
deterministic contract transcription over the already-admitted Phase 2 planning inputs plus the
accepted XDL/X-COM source contracts, with no need for a stronger reasoning tier; no Terra/Luna/Sol/
Astra route is authorized in this package, no model switch is claimed or performed, and no benchmark
or exact-cost claim is made. Blocker: none for this stage; implementation cannot start until the four
design stages complete and the precode gate passes, and autonomous legacy/production execution remains
unauthorized.

## 8. Stage artifacts

This stage adds exactly:

* `docs/engineering/argus-lite/requirements.md` (this document).
* `engineering/requirements/ARGUS2-SR-001.json` … `ARGUS2-SR-012.json` (12 software records).
* `engineering/requirements/XVE-SYS-00015.json`, `XVE-SYS-0179.json`, `XVE-SYS-0183.json`,
  `XVE-SYS-0185.json`, `XVE-SYS-0186.json`, `XVE-SYS-0188.json`, `XVE-SYS-0194.json`,
  `XVE-SYS-0198.json`, `XVE-SYS-0201.json`, `XVE-SYS-0203.json`, `XVE-SYS-0211.json`
  (11 allocation-only anchors; `XVE-SYS-0016.json` is preserved unchanged).
* 12 additive `refines` links (`ARGUS2-L-001` … `ARGUS2-L-012`) appended to
  `engineering/trace/links.json`; every inherited link object is preserved in order and content and
  the file is re-serialized with its existing deterministic format.
* The current pointer `engineering/project.json` set to feature ARGUS2 on the admitted accepted
  baseline.
* `engineering/stage-results/argus2-requirements.json` (this stage's record).

No source, test, schema, packaging or other code is added or changed by this stage.
