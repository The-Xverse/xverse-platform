# T038 Architecture — Spec Kit and REF-002 Requirements/Design/Code/Test Traceability and Public-Safe Evidence

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T038 (capability 007, slice `T-INTG`/traceability) |
| Stage / role | plan → architecture |
| Revision | 1 (Phase 8 traceability slice) |
| Baseline revision | `d5b9c6399da67a0a028fae21c2f0dcc8da3619bc` |
| Affected paths | `docs/engineering/xcom/t038/**`, `engineering/check_xcom_traceability.py`, `reports/xcom-queue/t038-traceability.json`, `engineering/requirements/T038-*.json`, `engineering/architecture/components/T038-*.json`, `engineering/unit-specifications/T038-*.json`, `engineering/validation/scenarios/T038-VS-ACCUMULATED.json`, `engineering/trace/links.json`, `engineering/project.json`, `reports/review-index.md` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed architecture | `docs/engineering/xcom/t009/architecture-model.json`; `docs/engineering/xcom/t010/unit-design.json`; `docs/engineering/xcom/t008/{requirements-register,traceability-matrix}.json` (`XCOM-SW-ENB-001/002`, `XCOM-SW-INTG-001/002`, `XCOM-SW-ENB-004`, `XCOM-SW-CORE-007`); `specs/007-xcom-core/{spec,plan,tasks,reference-traceability}.md`; `docs/architecture/SADS_REQUIREMENTS_TRACEABILITY.md`; `docs/architecture/sads-requirements-traceability.json`; `scripts/validate_xcom_requirements_traceability.py`; `engineering/trace/links.json`; ADR-0020; Constitution VI, IX, X |
| Classification | Public-safe engineering work product |

## 2. Purpose and position in the delivery graph

T038 is the **traceability-validation** task of the capability-007 `T-INTG` evidence family. T035 executed the
complete verification matrix; T036 measured the observation tap's disabled/enabled overhead; T037 completed the
Doxygen documentation and warning-free generated reference. T038 validates that the Spec Kit and REF-002
requirements/design/code/test/evidence chain is complete and public-safe at one exact candidate revision, and
proves that no allocated or deferred REF-002 SADS target is promoted without source and exact-candidate
evidence. T039–T041 own review and acceptance.

```text
T007 ownership → T008 requirements + REF-002 dispositions → T009 architecture → T010 unit design → T011 admission
   → T012 subtree build/test contract → T013–T016 core + matrix
   → T017–T020 XDL activation plan
   → T021–T024 observation boundary
   → T025–T029 stimulation boundary
   → T030 contract → T031 gateway → T032 client → T033 suites → T034 second provider
   → T035 exact-candidate verification matrix + results (read-only)
   → T036 controlled disabled/enabled-tap benchmark + repository-owned results (read-only)
   → T037 complete Doxygen comments + warning-free generated reference (read-only)
   → T038 Spec Kit + REF-002 traceability validation + public-safe evidence (this slice)
   → T039/T040 review → T041 acceptance
```

T038 adds a task-owned traceability verifier, its exact-candidate evidence report, additive trace links, one
work-product set, one engineering record set, and the current-task pointer. It changes no accepted requirement,
design, code, test, target, label, command, expected value, contract, schema, register, XDL profile, or ADR.

## 3. Boundary and context

### 3.1 System context

```text
   ┌────────────── accepted capability-007 anchors (read-only) ──────────────┐
   │  FR-027/028/029/030/035 · SC-009 · plan traceability/public-safe step    │
   │  t008 XCOM-SW-ENB-001/002, XCOM-SW-INTG-001/002, XCOM-SW-ENB-004,        │
   │       XCOM-SW-CORE-007 · 20 REF-002 dispositions XVE-SYS-0139–0158       │
   │  t009 XCOM-CMP-* · t010 XCOM-DU-* · specs/007-xcom-core/**               │
   │  specs/007-xcom-core/reference-traceability.md · t008 matrix              │
   └──────────────────────────────────┬──────────────────────────────────────┘
                                      │ validates (read-only)
   ┌──────── owned records + code (read-only semantics) ──────────────────────┐
   │  engineering/requirements/** · architecture/components/**                 │
   │  engineering/unit-specifications/** · validation/scenarios/**            │
   │  engineering/verification/measures/** · engineering/trace/links.json      │
   │  src/xverse/xcom/** · tests/** · proto/** · xdl/**                        │
   └──────────────────────────────────┬──────────────────────────────────────┘
                                      │ consumed by
   ┌────────────── T038 owned artifacts (this slice) ─────────────────────────┐
   │  engineering/check_xcom_traceability.py (fail-closed verifier)            │
   │  reports/xcom-queue/t038-traceability.json                                │
   │      requirements · design · code · tests · evidence · environment        │
   │  engineering/trace/links.json (additive T038 links)                       │
   │  engineering/project.json (current-task pointer)                          │
   │  guarantee : complete chain, all 20 REF-002 dispositions, none promoted,  │
   │      exact-candidate binding, public-safe bounded evidence, no change     │
   └──────────────────────────────────┬───────────────────────────────────────┘
                                      ▼
                           T039–T041 review/acceptance
```

### 3.2 Trust boundaries

| Boundary | Inside | Outside | Rule |
| --- | --- | --- | --- |
| `T38-XB-1` Traceability evidence vs accepted artifacts | additive T038 links, records, verifier, and report | any accepted requirement, design, code, test, register, schema, or ADR | T038 adds no accepted change; the chain is validated read-only (`T038-SR-006`). |
| `T38-XB-2` Disposition vs promotion | the twenty accepted REF-002 dispositions at `architectural-target` | any promoted/implemented disposition without proof | No allocated, deferred, architectural-target, or superseded ID is promoted (`T038-SR-003`). |
| `T38-XB-3` Exact candidate vs stale evidence | the report bound to the candidate revision and artifact hashes | a report generated from another revision, run, or host | Stale or foreign results fail the task-owned verifier (`T038-SR-004`, `T038-SR-009`). |
| `T38-XB-4` Public summary vs host data | requirement IDs, tool identities, hashes, outcomes, bounded output | host-specific absolute paths, credentials, payloads, proprietary excerpts | The committed report contains none of the excluded content (`T038-SR-005`). |
| `T38-XB-5` Offline/local vs external resources | admitted offline toolchain and the owned records | any TCP listener, `AF_INET`/`AF_INET6` socket, DNS, resolver, TLS, external peer, legacy binary, or production workload | No T038 command contacts a network or legacy resource; no dependency is added (`T038-SR-008`). |
| `T38-XB-6` T038 scope vs successor scope | the traceability validation and its evidence | the T039–T041 review/acceptance deliverables and the whole-system integration measure | T038 neither duplicates nor claims a successor deliverable (`T038-GAP-04`). |
| `T38-XB-7` Task-owned verifier vs accepted validator | the additive `engineering/check_xcom_traceability.py` | the accepted `scripts/validate_xcom_requirements_traceability.py` | T038 reuses the accepted semantics and does not modify or weaken the accepted validator (`T038-OPEN-05`). |

### 3.3 Prohibited elements (must remain absent)

No compiled-behavior, signature, type, default, contract, schema, register, XDL profile, accepted requirement,
test, target, label, command, or expected-value change; no new admitted dependency, runtime library, or
compiled symbol; no compiled or linked gRPC runtime; no TCP listener or `AF_INET`/`AF_INET6` socket, DNS,
resolver, or TLS use; no external network peer; no legacy binary, legacy repository, or production workload; no
review or acceptance artifact; no payload, permit, secret, private address, or host path in a committed file or
log; no production-readiness claim; no REF-002 promotion; no rewrite or weakening of an accepted ADR,
requirement, contract, schema, register, or test; no acceptance or integration of the candidate.

## 4. Components

`T38-*` names are local to this document. The T038 requirement components are `T038-SR-###-CMP` (one per
requirement) and the units `T038-SR-###-U`, consistent with the accepted capability-007 record convention.

### 4.1 T038 components

- **`T38-CMP-VERIFIER`** (`engineering/check_xcom_traceability.py`): the task-owned, deterministic, offline
  verifier that validates the traceability chain, the REF-002 disposition table, the exact-candidate binding,
  and public safety, and fails closed.
- **`T38-CMP-REPORT`** (`reports/xcom-queue/t038-traceability.json`): the evidence carrying `requirements`,
  `design`, `code`, `tests`, and `evidence` results plus the environment identity, hashes, and the
  exact-candidate identity.
- **`T38-CMP-REGISTER`** (`docs/engineering/xcom/t008/{requirements-register,traceability-matrix}.json`,
  `specs/007-xcom-core/reference-traceability.md`): the accepted Spec Kit register, matrix, and REF-002
  disposition table consumed read-only.
- **`T38-CMP-TRACE`** (`engineering/trace/links.json`, `engineering/project.json`): additive T038
  requirement/component/unit/measure/code/validation links and the current-task pointer.
- **`T38-CMP-SPEC`** (`specs/007-xcom-core/**`): the accepted Spec Kit specification, plan, and tasks consumed
  read-only.
- **`T38-CMP-WP`**: the T038 repository-owned work-product set and the T038 package record.

### 4.2 Consumed components (read-only)

- **`T38-CMP-T013…T037`** — accepted core value types, diagnostics, endpoint/route lifecycle, provider
  boundary/composition, owned loopback provider, XDL activation plan, observation boundary, stimulation
  boundary, contract, gateway, client, suites, second provider, matrix, benchmark, and Doxygen reference.
  Validated; no accepted change.
- **`T38-CMP-T008…T012`** — the accepted register/matrix, architecture model, unit design, admitted offline
  envelope, and subtree build/test contract. Consumed; no rule is weakened and no dependency is added.
- **`T38-CMP-T035/T036/T037`** — the accepted verification matrix, benchmark, and Doxygen reference. Consumed
  read-only; not re-run, re-claimed, or re-documented as if new.

## 5. Data flow (ordered)

1. **Admission.** The admitted offline toolchain and the Python runtime identity are resolved; no network
   access is used.
2. **Load.** The accepted `engineering/**` records, `engineering/trace/links.json`, the T008 register/matrix,
   and `specs/007-xcom-core/reference-traceability.md` are read read-only.
3. **Validate chain.** The verifier resolves every requirement → component → unit → code → test/measure →
   evidence → validation edge and rejects any missing or stale edge.
4. **Account dispositions.** The verifier checks all twenty REF-002 IDs against the accepted allocation/
   deferment table and rejects any promoted or incomplete disposition.
5. **Scan public safety.** The verifier scans the retained evidence for the excluded-content classes.
6. **Record.** `reports/xcom-queue/t038-traceability.json` is written with the `requirements`, `design`,
   `code`, `tests`, and `evidence` results, the environment identity, hashes, and the exact-candidate identity.
7. **Bind the trace.** Additive T038 links connect each requirement to its component, unit, measure,
   code artifact, and validated scenario; the fifteen `engineering/project.json` pins are refreshed.

## 6. Interfaces

### 6.1 Task-owned traceability verifier (`engineering/check_xcom_traceability.py`)

| Invocation | Contract |
| --- | --- |
| `python3 engineering/check_xcom_traceability.py --verify` | validate the complete traceability chain, the REF-002 dispositions, and public safety; exit `0` only when the chain is complete and nothing is promoted |
| `python3 engineering/check_xcom_traceability.py --verify reports/xcom-queue/t038-traceability.json` | validate the chain and additionally verify the evidence report fields and the exact-candidate binding; exit `0` only for a complete, public-safe, exactly-bound pass |
| `python3 engineering/check_xcom_traceability.py --self-test` | prove the verifier rejects a missing edge, a stale hash pin, a promoted disposition, and an excluded-content match |

The verifier is deterministic: the input set, relation set, disposition table, and excluded-content classes are
fixed for the exact candidate revision. It does not depend on ambient wall-clock time for its verdict.

### 6.2 Evidence report (`reports/xcom-queue/t038-traceability.json`)

| Field | Contract |
| --- | --- |
| `schema_version` | `1` |
| `task_id` | `T038` |
| `capability` | `007` |
| `baseline_revision` | the accepted baseline commit |
| `candidate_revision` | `null` in a committed report; the candidate commit is the direct child of the baseline carrying the recorded material |
| `candidate_identity` | the sorted material-input inventory, the material digest, the per-file SHA-256 hashes, the revision-binding rule, and the generation time |
| `requirements` | the requirement-chain result: counts of requirements/components/units and the resolved/unresolved edge count |
| `design` | the design-chain result: the component → unit decomposition result and the resolution status |
| `code` | the code-chain result: the `implemented_by` resolution and per-artifact hash status |
| `tests` | the test/measure-chain result: the `verified_by`/`analyzed_by` resolution and the selected case inventory |
| `evidence` | the evidence/validation-chain result: the `validates` resolution, the retained-evidence hashes, and the public-safety verdict |
| `environment` | Python version, the admitted-input identities and hashes, and the target identity, excluding host-specific absolute paths |
| `ref002` | the twenty dispositions, the `unchanged` capability disposition, and the empty `promoted` list |
| `hashes` | SHA-256 of the retained evidence and referenced candidate artifacts |
| `limitations` | explicit non-production and scope limitations |
| `blockers` | any unavailable input recorded as `blocked` with its reason |

### 6.3 Consumed contracts (read-only, unchanged)

| Interface | Contract consumed |
| --- | --- |
| `docs/engineering/xcom/t008/{requirements-register,traceability-matrix}.json` | the accepted Spec Kit register/matrix schema and REF-002 disposition vocabulary |
| `scripts/validate_xcom_requirements_traceability.py` | the accepted requirement-traceability validator semantics (reused as a reference, not modified) |
| `engineering/trace/links.json` | the accepted link model: `refines`, `allocated_to`, `decomposes_to`, `implemented_by`, `verified_by`, `analyzed_by`, `validates` |
| `specs/007-xcom-core/reference-traceability.md` | the accepted REF-002 allocation/deferment table |
| `docs/engineering/xcom/build-environment.md` | the repository-owned evidence contract (exact environment, candidate revision, bounded public-safe logs) |
| the accepted CMake/CTest subtree | the admitted offline build and the preserved discovered case inventory |

## 7. Concurrency and resource bounds

| Aspect | T038 decision |
| --- | --- |
| Production footprint | none; T038 adds no runtime source, test target, compiled symbol, or dependency |
| Build inventory | the accepted build is unchanged; T038 registers no new accepted test target |
| Processes | one bounded verification process per run; no legacy, external, or production process |
| Threads | validation tooling is single-threaded |
| Storage | one bounded JSON report plus bounded excerpts; no unbounded log retention |
| Transport | none |
| Determinism | the input set, relation set, disposition table, and excluded-content classes are fixed for the exact candidate revision |
| Time | no T038 verdict depends on ambient wall-clock time beyond the recorded generation time |

## 8. Quality attributes

| Attribute | Architectural decision | Evidence |
| --- | --- | --- |
| Complete traceability chain | every requirement → component → unit → code → test/measure → evidence → validation edge resolved | `T038-SR-001`; CHK-01 |
| Explicit REF-002 accounting | all twenty IDs with dispositions; capability `unchanged`, nothing promoted | `T038-SR-002`, `T038-SR-003`; CHK-02, CHK-07 |
| Exact-candidate binding | report bound to the baseline, the material digest/inventory, and artifact hashes | `T038-SR-004`; CHK-03, CHK-04 |
| Public-safe evidence | requirement IDs, tool identities, hashes, outcomes, bounded excerpts only | `T038-SR-005`; CHK-05 |
| Behavior preservation | additive records/verifier/report only; no accepted change | `T038-SR-006`; CHK-08 |
| Governance honesty | registers reconciled; current-task pointer; successors allocated; REF-002 `unchanged` | `T038-SR-007`; CHK-09, CHK-10 |
| Offline honesty | no network, DNS, TLS, legacy, or production resource; no new dependency | `T038-SR-008`; CHK-06 |
| Fail-closed checking | the verifier exits nonzero on any missing edge, stale pin, promoted disposition, or unsafe content | `T038-SR-009`; CHK-11 |
| Preserved suites | the accepted unit/integration/validation/static/conformance/sanitizer measures are unchanged | `T038-SR-010`; CHK-12, CHK-13 |

## 9. Consistency and constraints

- **Dependency direction preserved.** T038 consumes the accepted T007–T037 design and code; it introduces no
  dependency on a later slice, an external peer, or a legacy repository, and adds no admitted dependency.
- **Domain neutrality preserved.** Only generic traceability and evidence vocabulary appears (requirement,
  component, unit, measure, evidence, disposition, hash); no automotive, product, protocol, or configuration
  primitive is introduced.
- **XDL centrality preserved.** T038 neither parses nor authors XDL; it validates the accepted logical
  identities and dispositions.
- **Logical/physical separation preserved.** No address, port, or physical transport enters the evidence.
- **Ownership preserved.** Only the declared T038 paths change; every accepted artifact is preserved.
- **Maturity preserved.** The slice records prototype traceability evidence only; review and acceptance remain
  T039–T041.

## 10. Traceability

| Architecture element | T038 requirements |
| --- | --- |
| `T38-XB-1`, `T38-CMP-TRACE` | T038-SR-001, T038-SR-006, T038-SR-007 |
| `T38-XB-2`, `T38-CMP-REGISTER` | T038-SR-002, T038-SR-003 |
| `T38-XB-3`, `T38-CMP-REPORT` | T038-SR-004, T038-SR-010 |
| `T38-XB-4` | T038-SR-005 |
| `T38-XB-5` | T038-SR-008 |
| `T38-XB-6`, `T38-CMP-WP` | T038-SR-007 |
| `T38-XB-7`, `T38-CMP-VERIFIER` | T038-SR-009, T038-SR-010 |
| `T38-CMP-T013…T037` | T038-SR-001, T038-SR-006 |
| `T38-CMP-SPEC` | T038-SR-002, T038-SR-004 |

## 11. Negative cases (architecture view)

Every boundary has a declared fail-closed behaviour and a negative-case owner; the executable cases are listed
in `verification-plan.md` §5.

| Boundary | Injected defect | Negative case |
| --- | --- | --- |
| `T38-XB-1` | change an accepted requirement, design, code, test, register, or expected value | NEG-01, NEG-08 |
| `T38-XB-2` | promote an allocated/deferred REF-002 ID without proof, or record an incomplete disposition | NEG-02, NEG-03 |
| `T38-XB-3` | present stale, foreign, or mismatched output as current | NEG-04, NEG-05 |
| `T38-XB-4` | commit a credential, payload, private address, or host path | NEG-06 |
| `T38-XB-5` | use TCP/`AF_INET`, DNS, TLS, a legacy/external peer, or add a dependency | NEG-07 |
| `T38-XB-6` | claim a T039/T040/T041 result or a production-readiness claim | NEG-08 |
| `T38-XB-7` | weaken or replace the accepted validator instead of adding an additive verifier | NEG-09 |
| Governance | mark the T038 checkbox at the plan stage or omit the required report | NEG-10 |
| Trace | omit a required requirement/component/unit/measure/code/validation edge, or leave a stale hash pin | NEG-11 |
