# T017 Unit Specifications — Ownership, Lifetime, Thread-Safety, Failure, Bounds

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T017 |
| Stage / role | plan → unit specifications |
| Revision | 1 |
| Baseline revision | `a78d6d55dd5a68b1572cf5a594100dfba3be523e` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Consumed unit design | `docs/engineering/xcom/t010/design-units.md` (`XCOM-DU-009`, `XCOM-DU-010`, `XCOM-DU-011`) |
| Maturity of all T017 units | `allocated` (definition/validation artifacts, not yet implemented at this plan stage) |

The identifiers `T017-U-01`..`T017-U-08` are fixed by this document. `T017-U-01` realises the accepted
`XCOM-DU-009` (Profile schema) and `T017-U-02` realises the accepted `XCOM-DU-010` (activation-plan schema);
T017 does not renumber or edit the T010 design units. Every unit belongs to the `T-XDL` slice and is bound to
baseline `a78d6d55dd5a68b1572cf5a594100dfba3be523e`.

## 2. Vocabulary used below

- **Ownership model** (closed): `task-owns-artifact`, `caller-owns-value`, `platform-owns-shared`.
- **Lifetime model** (closed): `static-immutable`, `process-scoped`, `document-scoped`.
- **Thread-safety model** (closed): `read-only-static`, `offline-single-threaded`.
- **Outcome** (closed): `accepted`, `rejected`, `failed`, `inspectable`, `activatable`.
- **Overflow policy set** (closed): `drop-oldest`, `drop-newest`, `coalesce`, `lossless-backpressure`,
  `reject`, `fail-closed`, `n/a`.

## 3. Unit overview

| Unit | Name | Kind | Language | Realises | Artifact paths |
| --- | --- | --- | --- | --- | --- |
| `T017-U-01` | `io.xverse.xcom` Profile v0.1 schema | derived-artifact | json | `XCOM-DU-009` | `xdl/profiles/xcom-v0.1.schema.json` |
| `T017-U-02` | Activation-plan v1 schema | derived-artifact | json | `XCOM-DU-010` | `src/xverse/xcom/contracts/v1/activation-plan.schema.json` |
| `T017-U-03` | Digest/provenance contract | documentation | markdown | `XCOM-DU-010` | `specs/007-xcom-core/contracts/xdl-profile.md` (new sections) |
| `T017-U-04` | Profile/plan contract recording | documentation | markdown | `XCOM-DU-009`, `XCOM-DU-010` | `specs/007-xcom-core/contracts/xdl-profile.md` |
| `T017-U-05` | Offline plan validator | boundary | python | `XCOM-DU-009`, `XCOM-DU-010` | `scripts/validate_xcom_plan.py` |
| `T017-U-06` | Validation tests | test-fixture | python | `XCOM-DU-010` | `tests/xcom/activation_plan/{test_profile_schema,test_activation_plan_schema,test_digest_contract}.py` |
| `T017-U-07` | Bounded fixtures | test-fixture | json | `XCOM-DU-009`, `XCOM-DU-010` | `tests/xcom/activation_plan/fixtures/` |
| `T017-U-08` | Work products and implementation record | documentation | markdown | `XCOM-DU-009`, `XCOM-DU-010` | `docs/engineering/xcom/t017/` |

## 4. `T017-U-01` — `io.xverse.xcom` Profile v0.1 schema

- **Responsibility.** Define the closed, versioned `io.xverse.xcom` Profile v0.1 payload schema with the five
  permitted attachment forms, the recorded `schemaVersion`/`kind`/decorated identity, and fail-closed
  unknown-field/unknown-kind/unsupported-version behaviour.
- **Ownership.** `task-owns-artifact` — the `T-XDL` slice owns the versioned schema artifact.
- **Lifetime.** `static-immutable` — the schema is immutable once published and superseded additively by a new
  version.
- **Thread-safety.** `read-only-static`; shared state: none; synchronization: none.
- **Bounds.** `bytes` — schema artifact size (declared in the static artifact); `capacity` — number of
  `policy` forms, fixed at 5; overflow policy `reject` (unknown form/field rejected).
- **Failure semantics.** unknown field/kind/version → `rejected`; malformed payload → `rejected`; schema
  artifact unreadable → `failed`.
- **Requirement links.** T017-SR-001, T017-SR-002, T017-SR-003.
- **Component refs.** `XCOM-CMP-001`, `XCOM-CMP-002`.
- **Contract refs.** `XCOM-XLC-005`.
- **Governing ADRs.** ADR-0016, ADR-0018, ADR-0020.
- **Planned evidence.** CHK-01..CHK-04, NEG-P01..P14.

## 5. `T017-U-02` — Activation-plan v1 schema

- **Responsibility.** Define the closed canonical activation-plan v1 schema covering every required-content
  group, the digest/provenance members, deterministic ordering/uniqueness, and the
  inspectable-versus-activatable rule.
- **Ownership.** `task-owns-artifact` — the `T-XDL` slice owns the versioned schema artifact.
- **Lifetime.** `static-immutable` — immutable once published; superseded additively by a new plan version.
- **Thread-safety.** `read-only-static`; shared state: none; synchronization: none.
- **Bounds.** `bytes` — schema artifact size; `capacity` — declared plan entity collections (finite, declared
  in the activation plan); `depth` — nested structure depth (declared in the activation plan); overflow
  policy `fail-closed`.
- **Failure semantics.** missing required group/unknown field/wrong version → `rejected`; duplicate id or
  out-of-order collection → `rejected` (the ordering/uniqueness check is total and reports `rejected` even
  when a resource identity mixes present and absent optional members, e.g. the optional `version`);
  `activatable` with unresolved input → `rejected`; malformed digest → `rejected`; schema artifact unreadable
  → `failed`.
- **Requirement links.** T017-SR-004, T017-SR-005, T017-SR-006, T017-SR-007.
- **Component refs.** `XCOM-CMP-003`.
- **Contract refs.** `XCOM-XLC-001`.
- **Governing ADRs.** ADR-0016, ADR-0018, ADR-0020.
- **Planned evidence.** CHK-05..CHK-10, NEG-A01..A22.

## 6. `T017-U-03` — Digest/provenance contract

- **Responsibility.** State the canonical serialization, domain-separated SHA-256 digest, digested region,
  digest field form, provenance members, and reproducibility rule that bind a plan to its exact input.
- **Ownership.** `task-owns-artifact` — the normative text is owned by the `T-XDL` slice in the T-XDL-owned
  Profile contract.
- **Lifetime.** `document-scoped` — valid for the v1 plan version and superseded additively.
- **Thread-safety.** `read-only-static`; shared state: none; synchronization: none.
- **Bounds.** `bytes` — contract text size; `capacity` — digest algorithms, fixed at 1 (`sha256`); overflow
  policy `n/a`.
- **Failure semantics.** malformed/self-referential digest region → `rejected`; recomputed digest mismatch →
  `rejected`; non-deterministic serialization → `failed`.
- **Requirement links.** T017-SR-007.
- **Component refs.** `XCOM-CMP-003`.
- **Contract refs.** `XCOM-XLC-001`.
- **Governing ADRs.** ADR-0018, ADR-0020.
- **Planned evidence.** CHK-09, CHK-10, DET-01..DET-03, NEG-A14..A16, NEG-D01..D04.

## 7. `T017-U-04` — Profile/plan contract recording

- **Responsibility.** Record the Profile v0.1 payload grammar, the extension-location/safety rule, and the
  digest/provenance contract additively in `specs/007-xcom-core/contracts/xdl-profile.md`.
- **Ownership.** `task-owns-artifact` — the file is a `T-XDL` exclusive path; the change is additive and
  T017-scoped.
- **Lifetime.** `document-scoped` — valid for the v0.1/v1 contract versions.
- **Thread-safety.** `read-only-static`; shared state: none; synchronization: none.
- **Bounds.** `bytes` — document size; `capacity` — appended sections, fixed at 2; overflow policy `n/a`.
- **Failure semantics.** rewritten accepted statement or weakened requirement → `failed`; missing recording →
  `rejected`.
- **Requirement links.** T017-SR-003, T017-SR-010, T017-SR-011.
- **Component refs.** `XCOM-CMP-001`, `XCOM-CMP-003`.
- **Contract refs.** `XCOM-XLC-001`, `XCOM-XLC-005`.
- **Governing ADRs.** ADR-0016, ADR-0018, ADR-0020.
- **Planned evidence.** CHK-04, CHK-14, NEG-P12..P14, NEG-G01..G05.

## 8. `T017-U-05` — Offline plan validator

- **Responsibility.** Check both schemas, the closed/discriminator/coverage/ordering/digest rules, and the
  bounded fixtures; provide `--verify`, `--self-test`, and `--check-human`; expose one distinct nonzero exit
  class per failure family.
- **Ownership.** `caller-owns-value` — the validator returns an exit status/result and retains no shared state.
- **Lifetime.** `process-scoped` — the validator runs as a bounded, offline process and keeps no state after
  exit.
- **Thread-safety.** `offline-single-threaded`; shared state: none; synchronization: none.
- **Bounds.** `bytes` — per-document input (declared), aggregate input (declared), `depth` and `capacity`
  (node count) — declared; `timeout` seconds — declared; overflow policy `fail-closed`.
- **Failure semantics.** schema/profile/plan/digest defect → distinct nonzero class; over-bound or unreadable
  input → `IO_ERROR`; unauthorized path change / REF-002 promotion → `BOUNDARY_INVALID`; no partial success.
- **Requirement links.** T017-SR-007, T017-SR-008, T017-SR-011.
- **Component refs.** `XCOM-CMP-002`, `XCOM-CMP-003`.
- **Contract refs.** `XCOM-XLC-001`, `XCOM-XLC-005`.
- **Governing ADRs.** ADR-0018, ADR-0020.
- **Planned evidence.** CHK-11, CHK-12, BND-01..BND-04, NEG-V01..V08.

## 9. `T017-U-06` — Validation tests

- **Responsibility.** Exercise the Profile, activation-plan, and digest positive/negative cases through the
  validator/schema in pytest modules under `tests/xcom/activation_plan/`.
- **Ownership.** `task-owns-artifact` — the `T-XDL` slice owns the T017 test modules (shared slice path, so
  T018/T020 add distinct files without collision).
- **Lifetime.** `static-immutable` — the test modules are fixed for the candidate.
- **Thread-safety.** `offline-single-threaded`; shared state: none; synchronization: none.
- **Bounds.** `timeout` seconds — test-suite wall bound; `capacity` — fixture count (declared); overflow
  policy `fail-closed`.
- **Failure semantics.** an unexpected pass/fail → `failed`; a missing fixture → `failed`; no partial success.
- **Requirement links.** T017-SR-009.
- **Component refs.** `XCOM-CMP-002`, `XCOM-CMP-003`.
- **Contract refs.** `XCOM-XLC-001`, `XCOM-XLC-005`.
- **Governing ADRs.** ADR-0020.
- **Planned evidence.** CHK-13, `pytest` gate.

## 10. `T017-U-07` — Bounded fixtures

- **Responsibility.** Provide the small, public-safe positive and negative Profile/plan/digest JSON fixtures
  the validator and tests consume.
- **Ownership.** `task-owns-artifact` — the `T-XDL` slice owns the T017 fixture set.
- **Lifetime.** `static-immutable` — fixtures are fixed for the candidate.
- **Thread-safety.** `read-only-static`; shared state: none; synchronization: none.
- **Bounds.** `bytes` — per-fixture size (≤ declared per-file bound); `capacity` — fixture count (declared);
  overflow policy `fail-closed`.
- **Failure semantics.** over-bound or malformed fixture → `failed`; fixture containing a prohibited value →
  `failed`.
- **Requirement links.** T017-SR-009, T017-SR-011.
- **Component refs.** `XCOM-CMP-002`, `XCOM-CMP-003`.
- **Contract refs.** `XCOM-XLC-001`, `XCOM-XLC-005`.
- **Governing ADRs.** ADR-0020.
- **Planned evidence.** CHK-13, NEG-P01..P14, NEG-A01..A22, NEG-D01..D04.

## 11. `T017-U-08` — Work products and implementation record

- **Responsibility.** Maintain the five plan work products and the implementation record for the exact
  candidate.
- **Ownership.** `task-owns-artifact` — `docs/engineering/xcom/t017/` is exclusive to T017.
- **Lifetime.** `document-scoped` — valid for the candidate revision.
- **Thread-safety.** `read-only-static`; shared state: none; synchronization: none.
- **Bounds.** `bytes` — document size; `capacity` — work-product count, fixed at 5 + implementation record;
  overflow policy `n/a`.
- **Failure semantics.** missing work product → `failed`; inconsistent/unsupported claim → `failed`; no
  acceptance claim.
- **Requirement links.** T017-SR-011.
- **Component refs.** (cross-cutting).
- **Contract refs.** (cross-cutting).
- **Governing ADRs.** ADR-0020.
- **Planned evidence.** CHK-15, CHK-16, NEG-G01..G05.

## 12. Unit-to-requirement coverage

| Requirement | Units |
| --- | --- |
| T017-SR-001 | `T017-U-01` |
| T017-SR-002 | `T017-U-01` |
| T017-SR-003 | `T017-U-01`, `T017-U-04` |
| T017-SR-004 | `T017-U-02` |
| T017-SR-005 | `T017-U-02`, `T017-U-05` |
| T017-SR-006 | `T017-U-02`, `T017-U-05` |
| T017-SR-007 | `T017-U-02`, `T017-U-03`, `T017-U-05` |
| T017-SR-008 | `T017-U-05` |
| T017-SR-009 | `T017-U-06`, `T017-U-07` |
| T017-SR-010 | `T017-U-04` |
| T017-SR-011 | `T017-U-04`, `T017-U-08` |

Every `T017-SR-###` is covered by ≥ 1 unit; every unit maps to ≥ 1 requirement. No accepted `XCOM-DU-###`
design unit is renamed or edited.
