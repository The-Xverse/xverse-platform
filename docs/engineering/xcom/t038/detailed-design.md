# T038 Detailed Design — Spec Kit and REF-002 Requirements/Design/Code/Test Traceability and Public-Safe Evidence

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T038 (capability 007, slice `T-INTG`/traceability) |
| Stage / role | plan → detailed design |
| Revision | 1 (Phase 8 traceability slice) |
| Baseline revision | `d5b9c6399da67a0a028fae21c2f0dcc8da3619bc` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Classification | Public-safe engineering work product |

T038 validates the capability-007 traceability chain and the public safety of its retained evidence at one exact
candidate revision, and proves that no allocated or deferred REF-002 SADS target is promoted without source and
exact-candidate evidence. The design is written **before** execution; the implementation must realize it
exactly or record a design change and re-review.

## 2. Design decisions

| ID | Decision | Rationale | Requirement |
| --- | --- | --- | --- |
| `T038-DD-01` | T038 adds a **task-owned** verifier (`engineering/check_xcom_traceability.py`) and additive records; it changes no accepted requirement, design, code, test, target, register, or expected value | Validation must not invalidate the verified object | T038-SR-006 |
| `T038-DD-02` | The verifier validates the full chain `refines`/`allocated_to`/`decomposes_to`/`implemented_by`/`verified_by`/`analyzed_by`/`validates` over `engineering/**` and `engineering/trace/links.json` and rejects any missing or stale edge | Implements the bidirectional traceability obligation (`XCOM-SW-ENB-001`, `SC-009`) | T038-SR-001 |
| `T038-DD-03` | The verifier requires all twenty REF-002 IDs `XVE-SYS-0139`–`0158` to carry an explicit disposition consistent with `specs/007-xcom-core/reference-traceability.md`; the capability disposition stays `unchanged` with an empty `promoted` list | Implements REF-002 accounting without promotion (`XCOM-SW-ENB-002`, `FR-035`) | T038-SR-002 |
| `T038-DD-04` | No allocated, deferred, architectural-target, or superseded ID may be recorded implemented; promotion is impossible without source and exact-candidate executed evidence | Proof-before-promotion rule | T038-SR-003 |
| `T038-DD-05` | The report carries the required `requirements`, `design`, `code`, `tests`, and `evidence` sections plus the environment identity, hashes, and the exact-candidate identity | Implements the repository-owned evidence contract and the Phase 8 gate's required `T038` fields | T038-SR-004 |
| `T038-DD-06` | The verifier enforces the mechanically decidable excluded-content classes (`absolute host path`, `private IPv4 address`, `credential assignment`, `private-key marker`, `unbounded payload token`) over the retained evidence | Public-safety rule (`XCOM-SW-INTG-001`, `FR-027`) | T038-SR-005 |
| `T038-DD-07` | T038 reuses the accepted `scripts/validate_xcom_requirements_traceability.py` semantics as a reference and does not modify or weaken the accepted validator | Additive, non-destructive validation (`T38-XB-7`) | T038-SR-010 |
| `T038-DD-08` | A check whose accepted input or executable is unavailable is recorded `blocked` with its reason; no inferred or stale output is substituted | Honest outcome rule | T038-OPEN-03 |
| `T038-DD-09` | T038 links `implemented_by` to its additive work products and records, refreshes the fifteen `engineering/project.json` pins, and sets the current-task pointer | T038's realized artifacts are the additive records/verifier/report | T038-SR-007, T038-OPEN-02 |
| `T038-DD-10` | T038 does not run, duplicate, or claim the T035 matrix, the T036 benchmark, the T037 Doxygen result, or the T039/T040/T041 deliverables | Scope and maturity separation | T038-SR-007, T038-SR-010 |

## 3. Validation route (exact commands)

The route below is the repository-owned traceability validation. `${XVERSE_FABRIC_ROOT}` and the admitted inputs
are resolved by the trusted policy; the admitted inputs are `XVERSE_XCOM_TOOLCHAIN`,
`XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN`. The implementation records the exact
resolved argv, exit status, and observed outcomes.

| # | Purpose | Command (portable descriptor) | Expected |
| --- | --- | --- | --- |
| B-1 | task-owned traceability validation and report | `python3 engineering/check_xcom_traceability.py --verify reports/xcom-queue/t038-traceability.json` | exit `0`; the chain is complete, all twenty dispositions are unchanged, nothing is promoted, and the report carries the required fields and the exact-candidate identity |
| B-2 | verifier self-test | `python3 engineering/check_xcom_traceability.py --self-test` | exit `0`; the verifier rejects a missing edge, a stale hash pin, a promoted disposition, and an excluded-content match |
| B-3 | accepted register/matrix validator | `python3 scripts/validate_xcom_requirements_traceability.py --verify` | exit `0`; the accepted Spec Kit register and matrix validate unchanged |
| B-4 | accepted human projection check | `python3 scripts/validate_xcom_requirements_traceability.py --check-human` | exit `0`; the register/matrix projections are byte-stable |
| B-5 | trusted full-suite regression context | `python3 ${XVERSE_FABRIC_ROOT}/automation/run_xcom_phase8_tests.py unit` | `100% tests passed` |

The trusted Phase 8 `validation` measure for T038 invokes B-1 directly (`run_xcom_phase8_tests.py`,
`mode == "validation" and task == "T038"`), so the task-owned verification route is exercised by the trusted
gate. B-3/B-4 consume the accepted validator without modifying it; B-5 preserves the accepted suite.

## 4. Evidence report schema (`reports/xcom-queue/t038-traceability.json`)

```json
{
  "schema_version": 1,
  "task_id": "T038",
  "capability": "007",
  "baseline_revision": "<40-hex accepted baseline>",
  "candidate_revision": null,
  "candidate_identity": {
    "material_digest": "<sha256>", "material_inputs": ["<relative path>", "..."],
    "revision_binding": "<baseline plus material-digest/hash binding rule>",
    "generated_at": "<iso-8601>"
  },
  "requirements": {
    "requirements": "<int>", "components": "<int>", "units": "<int>",
    "resolved_edges": "<int>", "unresolved_edges": ["<id>", "..."], "verdict": "pass"
  },
  "design": {
    "decomposed_components": "<int>", "orphan_units": ["<id>", "..."], "verdict": "pass"
  },
  "code": {
    "implemented_by_links": "<int>", "stale_hash_pins": ["<id>", "..."], "verdict": "pass"
  },
  "tests": {
    "verified_by_links": "<int>", "analyzed_by_links": "<int>",
    "selected_cases": ["<case id>", "..."], "verdict": "pass"
  },
  "evidence": {
    "validates_links": "<int>", "public_safety": "pass",
    "excluded_content_classes": ["absolute host path", "private IPv4 address", "credential assignment",
      "private-key marker", "unbounded payload token"],
    "hashes": {"<artifact path>": "<sha256>"}, "verdict": "pass"
  },
  "environment": {
    "python": "<version>", "target": "linux-x86_64",
    "admitted_inputs": {
      "XVERSE_XCOM_TOOLCHAIN": {"kind": "directory", "sha256": "<sha256>", "files": "<int>"},
      "XVERSE_XCOM_PACKAGE_MANIFEST": {"kind": "file", "sha256": "<sha256>", "files": 1},
      "XVERSE_XCOM_T025_TEST_TOOLCHAIN": {"kind": "directory", "sha256": "<sha256>", "files": "<int>"}
    }
  },
  "ref002": {
    "capability_disposition": "unchanged",
    "promoted": [],
    "ids": {"XVE-SYS-0139": "allocated", "XVE-SYS-0141": "deferred", "...": "..."},
    "architectural_target_count": 20
  },
  "hashes": {"<artifact path>": "<sha256>"},
  "limitations": ["validation-only prototype evidence; not a production-readiness claim", "..."],
  "blockers": []
}
```

- `requirements`, `design`, `code`, `tests`, and `evidence` are the Phase 8-gate-required fields; `ref002`
  and `environment` are the repository-owned evidence-contract fields.
- A non-empty `unresolved_edges`, `stale_hash_pins`, `orphan_units`, or `promoted` list, a `public_safety`
  value other than `pass`, or a non-`pass` `verdict` yields a failed outcome and a nonzero verifier exit.
- `hashes` records SHA-256 of the retained evidence and the referenced T038 artifacts; it never records a
  host-specific absolute path.
- `candidate_revision` is `null`: a committed report cannot contain the hash of the commit that contains it.
  The exact candidate is bound by `baseline_revision` plus the `candidate_identity.material_inputs` inventory,
  `material_digest`, and per-file `hashes`.

## 5. Verification obligations (chain and dispositions)

The plan-stage probe established the accepted baseline. The implementation completes these and re-checks the
whole model so no obligation remains.

| Obligation | Observed baseline | Required result |
| --- | --- | --- |
| requirement chain | 786 inventoried artifacts, 2855 links; T037 added 139 `T037-L-*` links | every accepted software requirement resolves to component, code, and measure; no missing edge |
| design chain | components and units present for T012–T037 | every unit has its owning component and a `decomposes_to` link |
| code chain | `implemented_by` pins resolve; fifteen pin `engineering/project.json` | every pin matches the candidate artifact hash; the fifteen project.json pins refreshed |
| test/measure chain | unit/integration/validation/static_analysis measures present | every `verified_by`/`analyzed_by` link resolves to a declared measure |
| evidence chain | accepted T035/T036/T037 evidence consumed read-only | every intended-use validation scenario has a `validates` link; T038-VS-ACCUMULATED resolves |
| REF-002 dispositions | 20 IDs: 10 allocated, 10 deferred, all `architectural-target`; none implemented | all twenty explicit; capability `unchanged`; `promoted` empty |
| public safety | the accepted validator's `--verify` scan classes | no excluded-content match in any retained T038 file |

## 6. Failure semantics

| Condition | Outcome |
| --- | --- |
| a required requirement/component/unit/measure/code/validation edge is missing or stale | the verifier exits nonzero and records the unresolved edge |
| an allocated/deferred/architectural-target/superseded ID is recorded implemented, or the capability disposition changes | the verifier exits nonzero and records the promoted ID |
| a retained file or excerpt matches an excluded-content class | the verifier exits nonzero and records the class |
| the evidence report lacks a required field or is not bound to the exact candidate | the verifier exits nonzero |
| an accepted input or the Python runtime is unavailable | the check is `blocked` with its reason; the candidate does not claim a pass (`T038-DD-08`) |
| an accepted requirement, code, test, register, or expected value would change | the change is rejected; `T038-DD-01` fails closed |

## 7. Determinism and safety

- The input set, relation set, disposition table, excluded-content classes, and retained-evidence locations
  are fixed and recorded; no T038 verdict depends on ambient wall-clock time beyond the recorded generation
  time.
- Validation tooling is single-threaded.
- No T038 command opens a network listener or socket, resolves a name, or contacts a legacy or external
  resource; no dependency is added.
- Committed files and excerpts contain no credential, private address, real or proprietary payload, or
  host-specific absolute path.

## 8. Public-safety and information classification

- Only requirement IDs, tool identities, admitted-input digests, outcomes, warning-free bounded output, and
  hashes are committed.
- Host-specific absolute prefix, manifest, temporary, and evidence-store paths are excluded from the report;
  raw validation logs, if retained, live outside the public report.
- No payload byte, permit content, credential, private address, or proprietary source excerpt enters a
  committed artifact.

## 9. Traceability and digest refresh

| Design element | Requirement | Checks |
| --- | --- | --- |
| `T038-DD-02` chain validation | T038-SR-001 | CHK-01, CHK-09 |
| `T038-DD-03`/`-04` REF-002 accounting and no promotion | T038-SR-002, T038-SR-003 | CHK-02, CHK-07 |
| `T038-DD-05` report fields and candidate binding | T038-SR-004 | CHK-03, CHK-04 |
| `T038-DD-06` public safety | T038-SR-005 | CHK-05 |
| `T038-DD-07`/`-10` additive scope and preserved suites | T038-SR-006, T038-SR-010 | CHK-08, CHK-12, CHK-13 |
| `T038-DD-08` unavailable-input honesty | T038-SR-004 | CHK-03 |
| `T038-DD-09` evidence trace and current-task pointer | T038-SR-007 | CHK-09, CHK-10 |

**Digest refresh obligation (`T038-OPEN-02`).** Because T038 edits `engineering/project.json`, the
implementation stage **must** recompute the `implemented_by` `target_revision` pins for the fifteen links that
target it in `engineering/trace/links.json`, and any further edited-artifact pins, so no stale hash remains.

## 10. Doxygen and documentation

T038 is a traceability/evidence task; its public interfaces are the task-owned verifier CLI and the report
schema documented in this work-product set. The verifier does not change any documented C/C++ public interface
and adds no Doxygen obligation beyond the additive Python docstrings of the task-owned script.

## 11. Compatibility contract and generated-code provenance

- T038 adds **no** generated code and **no** admitted dependency. It does not touch
  `proto/xverse/xcom/v1/tool_gateway.proto` or any `XCOM-XLC-002` message and links no transport runtime.
- **Generated-code provenance.** Generated protobuf C++ and system/third-party headers remain out of the
  owned documentation scope and are handled by the admitted T011 exclusion list; T038 validates only the
  owned record/report chain and the accepted hand-written surface.
- **Compatibility contract.** T038 defines no competing interface, contract, or configuration language; it
  validates the accepted one and promotes no REF-002 target.
