# T017 Implementation Record — Profile v0.1, Activation-Plan v1, Digest/Provenance, and Validator

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T017 (capability 007, phase 4 XDL-derived activation plan) |
| Stage / role | implementation → implementation record |
| Revision | 3 (successor candidate repairing internal review revision 3) |
| Authorized baseline | `a78d6d55dd5a68b1572cf5a594100dfba3be523e` |
| Candidate state | working tree over the authorized baseline (candidate revision assigned when the workflow checkpoints) |
| Predecessor candidate | revision 2 of this record; internal review `internal-review.json` rev 3 (`verdict: fail`) |
| Work products | [`requirements.md`](requirements.md), [`architecture.md`](architecture.md), [`detailed-design.md`](detailed-design.md), [`unit-specifications.md`](unit-specifications.md), [`verification-plan.md`](verification-plan.md), this record |
| Authorization | ACC002, ACC003, ACC013, ACC014, ACC015; ADR-0016, ADR-0018, ADR-0020; `specs/007-xcom-core/tasks.md` T017; `docs/engineering/xcom/task-ownership.json` `T-XDL` |
| Maturity | Definition/validation work products implemented and locally verified; not user-accepted, not externally reviewed |
| Classification | Public-safe engineering work product |

This revision repairs every finding of the read-only internal review revision 3 without weakening an
accepted requirement, checks, test, contract, or boundary. The review is a separate pass; this record
states what changed and the evidence that closes each finding. It accepts and integrates nothing.

## 2. Candidate summary

T017 implements the bounded contract-definition slice required by its task entry: one closed
`io.xverse.xcom` Profile v0.1 payload schema, one closed canonical activation-plan v1 schema, the
digest/provenance contract, an offline deterministic validator with a controlled self-test, and
pytest validation tests. It is a **schema/contract-and-test** change plus one offline script under
`scripts/` and one additive section set in the `T-XDL`-owned `xdl-profile.md`.

The candidate changes **no** path under `src/xverse/xcom/include/`, `src/xverse/xcom/src/`,
`src/xverse_xdl/`, `proto/`, `cmake/`, or `Doxyfile`; adds no CMake target; executes no production
workload; and accepts, completes, or integrates no other task or software candidate. It does not
implement the Python compiler (T018), the C++ decoder (T019), or the T020 regression suite.

Realised design units: `T017-U-01` (`PROFILE_SCHEMA`), `T017-U-02` (`PLAN_SCHEMA`), `T017-U-03`
(digest/provenance contract), `T017-U-04` (contract recording), `T017-U-05` (`PLAN_VALIDATOR`),
`T017-U-06`/`T017-U-07` (`PLAN_TESTS`/`PLAN_FIXTURES`), and `T017-U-08` (this record). `T017-U-01`
realises the accepted `XCOM-DU-009` and `T017-U-02` realises the accepted `XCOM-DU-010`; no accepted
`XCOM-DU-###` or T009 component/contract identity is renumbered or edited.

### 2.1 Design-detail resolutions

1. **Closed-object check applies to complete object definitions.** `detailed-design.md` §3.1 models the
   discriminated `policy` member as `{"type": "object"}` whose closedness comes from the per-`kind`
   `allOf`/`if`/`then` selection, and the plan's `status = activatable` conditional narrows
   `inputResolution` without redeclaring a full object. `check_schema_structure` therefore requires
   `additionalProperties: false` on every schema node that declares both `"type": "object"` and a
   `properties` map, and treats a partial `if`/`then` sub-schema as an application of an already-closed
   definition. This keeps the requirement's "closed at every object" intent (each effective object is
   closed) while not misclassifying a narrowing sub-schema as an open object. The profile `policy`
   member is nevertheless effectively closed because each `kind` selects exactly one closed form
   definition; NEG-P11 (unknown member inside a form's `policy`) proves it.
2. **Boundary check consumes a caller-supplied changed set (repair).** The offline validator starts no
   child process, so it cannot derive the Git diff itself. `run_checks(root, changed_paths=...)` checks
   the authorized-path boundary only against a set the caller supplies (`--verify --changed-paths
   <file>`); `--verify` alone no longer asserts a vacuous boundary, and the deterministic gate performs
   the same check externally with `git diff --name-only`. `verification-plan.md` CHK-15 records this.
3. **REF-002 promotion is read from the authoritative record (repair).** The check now reads
   `docs/architecture/sads-requirements-traceability.json`, requires all twenty direct communication
   IDs `XVE-SYS-0139`–`0158`, and rejects any whose `disposition`/`maturity` leaves the accepted
   `allocated`/`deferred` `architectural-target` state, instead of validating a validator-local constant.

### 2.2 Repair closure of the internal review findings

| Finding | Severity | Closure in this revision | Evidence |
| --- | --- | --- | --- |
| T017-IR-001 | medium | `canonical_bytes` now normalizes every mathematically integral number to its integer form before encoding, so `100` and `100.0` share one canonical byte string and digest; the normative contract text and design rule state exactly how this is achieved and bind T019 to the same rule. | `scripts/validate_xcom_plan.py` `_normalize_numbers`/`canonical_bytes`; `xdl-profile.md` "Canonical serialization"; `detailed-design.md` §5.1; `test_canonical_bytes_normalize_integral_numbers` |
| T017-IR-002 | medium | `load_json` parses with an `object_pairs_hook` that raises `IO_ERROR` on a repeated member name, so a duplicate-member document is rejected fail-closed instead of collapsing last-wins; a declared negative case and a test exercise it. | `parse_json_text`/`_pairs_without_duplicates`; NEG-V05; `test_duplicate_json_member_rejected` |
| T017-IR-003 | medium | The vacuous self-check was removed. The repository-level path checks the authorized boundary only against a supplied changed set; the closure test drives `run_checks` with `src/xverse_xdl/xcom_plan.py` and gets `BOUNDARY_INVALID`. | `run_checks`/`load_changed_paths`; `--verify --changed-paths`; `test_authorized_path_boundary_consumes_changed_set` |
| T017-IR-004 | low | REF-002 is now read from the authoritative program record and rejects a promoted target; a test asserts a promoted entry yields `BOUNDARY_INVALID`. | `check_ref002`/`REF002_RECORD_REL`; NEG-G03; `test_ref002_authoritative_record_not_promoted` |
| T017-IR-005 | low | `check_input_bounds` is applied to every parsed document (both schemas, all Profile payloads, all plans) with the 1 MiB fixture bound and the 5 MiB supplied-document bound, plus the depth/node bounds; the wall bound is enforced by `check_wall_bound` inside `run_checks` and observed externally. | `check_input_bounds`/`check_wall_bound`; NEG-V06..V08; `test_declared_bounds_enforced`; `verification-plan.md` §6 |
| T017-IR-006 | low | Five declared negative cases (`NEG-A17`..`NEG-A21`) cover the activationOrder-undeclared-id, diagnostics uniqueness/order, and provenance-resource uniqueness/order branches, and a test asserts each branch directly. | NEG-A17..A21; `test_ordering_uniqueness_branches_exercised_directly` |
| T017-IR-007 | low | The verification-plan test table now uses the implemented identifiers and lists every test; `NEG-D01` exercises the declared non-canonical key-ordering/whitespace defect (correct domain separator); a traceability test asserts the plan and modules agree exactly. | `verification-plan.md` §4.3/§7; `test_verification_plan_lists_every_implemented_test`; `reordered_copy`/NEG-D01 |
| T017-IR-008 | medium | The ordering/uniqueness check is now total over an absent optional member. `_order_token` normalises each identity element (`None` → `(0, "")`, a string → `(1, value)`) before `sorted`, so a schema-valid `provenance.resources` duplicate that omits the optional `version` on exactly one entry yields a `PLAN_INVALID` finding instead of an uncaught `TypeError`. The same guard covers the diagnostics and collection key lists and the `activationOrder` undeclared-id diagnostic. A new declared negative case `NEG-A22` and the closure test `test_ordering_totality_over_optional_version` assert the rejection and exit class directly. | `_order_token`/`_is_sorted`/`check_ordering`; NEG-A22; `test_ordering_totality_over_optional_version`; `unit-specifications.md` §5; `verification-plan.md` §4.2/§7 |

No accepted requirement, contract statement, check, or test was weakened: the repair adds enforcement
and coverage where the review found the previous wiring vacuous or incomplete.

## 3. Changed artifacts and symbols

| Artifact | Change | Symbols / structure |
| --- | --- | --- |
| `xdl/profiles/xcom-v0.1.schema.json` | new | Closed Draft 2020-12 payload schema; `$defs.kind` (five forms), `$defs.target`, and the five closed form definitions `interfacePolicy`, `flowPolicy`, `networkProviderPolicy`, `observationPolicy`, `validationPolicy`; conditional `allOf` selects the form by `kind`. |
| `src/xverse/xcom/contracts/v1/activation-plan.schema.json` | new | Closed Draft 2020-12 plan schema; 16 required members; `$defs` for `digest`, `generator`, `resourceRef`, `provenance`, `contract`, `endpoint`, `route`, `provider`, `policies`, `observationPoint`, `stimulation`, `clockDomain`, `diagnostic`, `inputResolution`; conditional `status = activatable` ⇒ all six `inputResolution` states `resolved`. |
| `specs/007-xcom-core/contracts/xdl-profile.md` | modified (additive) | Two appended normative sections: "Profile v0.1 payload grammar" and "Activation-plan v1 digest and provenance"; the canonical-serialization paragraph now states the single integral-number form, duplicate-member rejection, and the T019 obligation. 73 added lines, 0 deleted lines, no existing sentence altered. |
| `scripts/validate_xcom_plan.py` | new | `Finding` (`NamedTuple`), `PlanError`, `read_text_bounded`, `_pairs_without_duplicates`, `parse_json_text`, `load_json`, `measure_shape`, `check_input_bounds`, `check_wall_bound`, `_normalize_numbers`, `canonical_bytes`, `canonical_body`, `reordered_copy`, `compute_digest`, `check_digest`, `_closed_findings`, `check_schema_structure`, `check_profile_contract`, `check_plan_contract`, `_json_schema_findings`, `validate_profile_payload`, `_target_identity`, `validate_profile_set`, `_order_token`, `_is_sorted`, `check_ordering`, `validate_plan_structure`, `check_authorized_paths`, `load_changed_paths`, `check_ref002`, `check_public_safety`, `check_offline_source`, `check_stage`, `run_checks`, `exit_code`, `verify_summary`, `parse_probe`, `deep_probe_value`, `negative_cases`, `self_test`, `human_summary`, `check_human`, `main`; constants `PROFILE_KINDS`, `PROFILE_FORM_DEFS`, `REQUIRED_PLAN_MEMBERS`, `COMMUNICATION_PLAN_GROUPS`, `COLLECTION_KEYS`, `AUTHORIZED_PATH_PREFIXES`, `REF002_RECORD_REL`, `REF002_DIRECT_IDS`, `REF002_PROMOTION_TOKENS`, `FORBIDDEN_SOURCE_IMPORTS`, `PUBLIC_SAFETY_PATTERNS`, `DOMAIN_SEPARATOR`, `MAX_FIXTURE_BYTES`; exit classes `OK`(0), `SCHEMA_INVALID`(2), `PROFILE_INVALID`(3), `PLAN_INVALID`(4), `DIGEST_INVALID`(5), `IO_ERROR`(6), `BOUNDARY_INVALID`(7); CLI `--verify`, `--self-test`, `--check-human`, `--verify --changed-paths <file>`. |
| `tests/xcom/activation_plan/test_profile_schema.py` | new | 4 test functions: positive payloads (all five forms), closed/discriminated schema, NEG-P01..P14, explicit unknown-kind/field rejection. |
| `tests/xcom/activation_plan/test_activation_plan_schema.py` | new | 7 test functions: valid plan, inspectable plan, closed/coverage schema, NEG-A01..A22, direct ordering/uniqueness branch checks, ordering totality over a mixed optional-member identity (T017-IR-008), explicit activatable-with-unresolved rejection. |
| `tests/xcom/activation_plan/test_digest_contract.py` | new | 12 test functions: key-order/whitespace-stable canonical bytes, integral-number normalization, digest round-trip and drift, digested region excludes `digest`, NEG-D01..D04, NEG-V01..V08/NEG-G01..G05, duplicate-member rejection, declared bounds, changed-path boundary, REF-002 authoritative record, plan/test traceability, `--self-test`/`run_checks` entry points. |
| `tests/xcom/activation_plan/fixtures/profile/valid/*.json` | new (5) | One accepted payload per permitted form, each decorating a distinct logical identity. |
| `tests/xcom/activation_plan/fixtures/plan/valid/plan-activatable.json` | new | Canonical activatable plan with its computed domain-separated digest. |
| `tests/xcom/activation_plan/fixtures/plan/valid/plan-inspectable.json` | new | Canonical inspectable plan with one unresolved input and its computed digest. |
| `tests/xcom/activation_plan/fixtures/expected-summary.txt` | new | The committed deterministic human summary checked by `--check-human`. |
| `docs/engineering/xcom/t017/implementation.md` | new | This record. |
| `specs/007-xcom-core/tasks.md` | modified | T017 checkbox marked complete; no other task line changed (marked after this record exists, per NEG-G05). |

The candidate diff contains no `src/xverse/xcom/include/`, `src/xverse/xcom/src/`, `src/xverse_xdl/`,
`proto/`, CMake, or `Doxyfile` path and changes no accepted ADR, accepted requirement, accepted contract
statement, other task's work product, or existing test. No production numeric bound value is fixed;
every bound in the schemas is a finite declared maximum, and the validator's own bounds are
non-production offline-input bounds.

## 4. Requirement-to-evidence trace

| Requirement | Evidence |
| --- | --- |
| T017-SR-001 | `check_profile_contract`; CHK-01/CHK-02; NEG-P01..P05 |
| T017-SR-002 | five closed form definitions; CHK-03; NEG-P06..P11 |
| T017-SR-003 | closed objects + appended placement/safety contract text; CHK-04; NEG-P12..P14 |
| T017-SR-004 | `check_plan_contract`; 16 required members; CHK-05/CHK-06; NEG-A01..A08 |
| T017-SR-005 | schema conditional + validator; CHK-07; NEG-A09, NEG-A10 |
| T017-SR-006 | `check_ordering`/`_order_token`; CHK-08; NEG-A11..A13, NEG-A17..A22 |
| T017-SR-007 | `canonical_bytes`/`compute_digest`/`check_digest`; CHK-09/CHK-10/DET-01..DET-03; NEG-A14..A16, NEG-D01..D04 |
| T017-SR-008 | `run_checks`/`self_test`/`check_human`/`check_input_bounds`/`check_wall_bound`; CHK-11/CHK-12/BND-01..BND-04; NEG-V01..V08 |
| T017-SR-009 | `tests/xcom/activation_plan/` (22 tests); CHK-13; full `pytest` gate |
| T017-SR-010 | additive `xdl-profile.md` sections; CHK-14 (73 additions, 0 deletions) |
| T017-SR-011 | `check_authorized_paths`/`check_ref002`/`check_public_safety`; CHK-15/CHK-16; NEG-G01..G05 |

REF-002: no direct communication requirement `XVE-SYS-0139`–`0158` and no shared requirement is
implemented or promoted. `check_ref002` reads the authoritative
`docs/architecture/sads-requirements-traceability.json` and confirms all twenty direct IDs remain
`allocated`/`deferred` `architectural-target`; no disposition record is rewritten.

## 5. Commands, results, and evidence

Environment (provisioned, changes no repository file): Python 3.13.13; `jsonschema` 4.26.0,
`referencing` 0.37.0, `ruamel.yaml` 0.19.1 importable; this checkout's `src/` installed editable so
the existing suite imports `xverse_xdl`. All commands run from the repository root at baseline
`a78d6d55dd5a68b1572cf5a594100dfba3be523e`.

| # | Command | Exit | Result |
| ---: | --- | ---: | --- |
| 1 | `python3 -m py_compile scripts/validate_xcom_plan.py` | 0 | Validator compiles. |
| 2 | `python3 scripts/validate_xcom_plan.py --verify` | 0 | `X-COM activation-plan validation passed: profileKinds=5 planMembers=16 collections=6 digestVectors=2 exitClasses=6` (CHK-01..CHK-12, CHK-14..CHK-16). |
| 3 | `python3 scripts/validate_xcom_plan.py --self-test` | 0 | Positive artifacts pass; NEG-P01..P14 → 3, NEG-A01..A09/A11..A22 → 4, NEG-A10 → 0, NEG-D01..D04 → 5, NEG-V01..V03 → 2, NEG-V04..V08 → 6, NEG-G01..G05 → 7; `cases=53 OK=1 SCHEMA_INVALID=3 PROFILE_INVALID=14 PLAN_INVALID=21 DIGEST_INVALID=4 IO_ERROR=5 BOUNDARY_INVALID=5` (CHK-11). |
| 4 | `python3 scripts/validate_xcom_plan.py --check-human` | 0 | `human summary: consistent` (DET-03). |
| 5 | `git diff --name-only a78d6d55… -- > /tmp/t017-changed.txt; python3 scripts/validate_xcom_plan.py --verify --changed-paths /tmp/t017-changed.txt` | 0 | The real 22-path candidate set is inside the authorized boundary (CHK-15, closure of T017-IR-003). |
| 6 | `printf 'src/xverse_xdl/xcom_plan.py\n' > /tmp/chg.txt; python3 scripts/validate_xcom_plan.py --verify --changed-paths /tmp/chg.txt` | 7 | `BOUNDARY_INVALID: candidate path is not authorized for T017: src/xverse_xdl/xcom_plan.py` (negative control for CHK-15). |
| 7 | two `--verify` runs piped to `sha256sum` | 0 | Byte-identical `0813cd170f68a57247c75d00b444fcbf2f4d745c53288d9a78fb0ec7fb9f7c43` (DET-01). |
| 8 | two `--self-test` runs piped to `sha256sum` | 0 | Byte-identical `426d7752ef1e8002515974786cbb7532f177a64dd5cfd096b6c638bee011cef3` (DET-01). |
| 9 | `python3 -m pytest -q tests/xcom/activation_plan` | 0 | 23 passed. |
| 10 | `python3 -m pytest -q` | 0 | 113 passed, 24 subtests passed (baseline was 90 passed, 24 subtests; T017 adds 23 tests, none removed or weakened). |
| 11 | `python3 scripts/validate_xcom_task_ownership.py --verify` | 0 | T007 register valid (CHK-16). |
| 12 | `git rev-parse a78d6d55dd5a68b1572cf5a594100dfba3be523e` | 0 | Prints the baseline SHA (binding resolves). |
| 13 | `git diff --numstat a78d6d55… -- specs/007-xcom-core/contracts/xdl-profile.md` | 0 | `73  0` additions; no deleted line (CHK-14). |
| 14 | `git diff --name-only a78d6d55… --` | 0 | 22 paths, all inside the T017-authorized prefixes; no untracked file in the changed set. |
| 15 | `git diff --check a78d6d55… --` | 0 | Clean. |
| 16 | `/usr/bin/time -f 'wall=%es' python3 scripts/validate_xcom_plan.py --verify` | 0 | `wall=0.25s` (BND-04, ≤ 60 s and enforced in-process). |
| 17 | `python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T017 a78d6d55…` | 0 | `{"ok": true, "task_id": "T017", "changed_paths": 22, "checks": ["pytest"]}`. |

Self-test detail (command 3, condensed):

```
positive artifacts: passed
NEG-P01..NEG-P14: PROFILE_INVALID (exit 3)
NEG-A01..NEG-A09, NEG-A11..NEG-A22: PLAN_INVALID (exit 4)
NEG-A10: OK (exit 0)
NEG-D01..NEG-D04: DIGEST_INVALID (exit 5)
NEG-V01..NEG-V03: SCHEMA_INVALID (exit 2)
NEG-V04..NEG-V08: IO_ERROR (exit 6)
NEG-G01..NEG-G05: BOUNDARY_INVALID (exit 7)
X-COM activation-plan self-test passed
```

Artifact identity at this candidate state (sha256):

| Artifact | sha256 |
| --- | --- |
| `xdl/profiles/xcom-v0.1.schema.json` | `2a39f350be9f8d65bff283648d6392d049f35f89ead1cbd3e972edbc2a62b307` |
| `src/xverse/xcom/contracts/v1/activation-plan.schema.json` | `afc3d8b647be101c23f8a40782c6c1ed7361d22964c1c526181a3037bbf2ab45` |
| `specs/007-xcom-core/contracts/xdl-profile.md` | `123629b42c435ee4f79d263a951097fe94d4ae6e3e723b14cd0a0859393859ec` |
| `scripts/validate_xcom_plan.py` | `921b8fe8b7ad5f5342bd1da64852e112c2f75f0d177b98bb7318e1f12393f64b` |
| `tests/xcom/activation_plan/test_profile_schema.py` | `5b5a4005adaac012debcfc695b4626d47cdfdf487c23e0bbe182a3775ae81fdc` |
| `tests/xcom/activation_plan/test_activation_plan_schema.py` | `88935c31273308b4ec9d82aef1c5c76a8ae9ee0d89c60077ee2f3a7d399c4dc4` |
| `tests/xcom/activation_plan/test_digest_contract.py` | `187719cfdb72c285078c7cbfa470f648aa8c416a5cc6bddbc9c9aa4704fb6ee4` |
| `tests/xcom/activation_plan/fixtures/expected-summary.txt` | `22577e446c63fe05203398ed9268ff90636de9d53ef03b5591ab8c1ab2a4b797` |
| `tests/xcom/activation_plan/fixtures/plan/valid/plan-activatable.json` | `8f32193b5fe9ad3546cbc291eaa276ffae6e41297fa8d990e26997f5c8bc0790` |
| `tests/xcom/activation_plan/fixtures/plan/valid/plan-inspectable.json` | `48be9d195ed0f324ad497437faeef6f34f6cc6a083989bf7ce3a800e4ec84cd1` |
| `tests/xcom/activation_plan/fixtures/profile/valid/interface-policy.json` | `ea2161dd5232b50efe0d715237ce65c25b451e3e3914342d16fd04f9fe7708e3` |
| `tests/xcom/activation_plan/fixtures/profile/valid/flow-policy.json` | `92f460382e86c3af57294556e327c98f83aae1c46f6e27a039f90703d78bb8d2` |
| `tests/xcom/activation_plan/fixtures/profile/valid/network-provider.json` | `d7fe8595be7205c0473b4aab864f9f3f1e4aa8b91cfe03f2783c9e344fa381ff` |
| `tests/xcom/activation_plan/fixtures/profile/valid/observation-policy.json` | `d56befa0457c0b9ec5d95d52ed3238a8286e8556f7b7a06acae547fa6ae8707c` |
| `tests/xcom/activation_plan/fixtures/profile/valid/validation-policy.json` | `3d7b814ab7924e26dc6dcbbbf816d03d82667fb4ea108ee2cbb141fa1d9fc840` |
| `docs/engineering/xcom/t017/requirements.md` | `c1a8a772bb045c9e39c7dcf544b946c67ec1bf75e61df7c616b133c1879d4d34` |
| `docs/engineering/xcom/t017/architecture.md` | `c16cb7db5bc24cbf0cef415ca053c41cb21f52f567bd7ed8e6492d9cf7cf022e` |
| `docs/engineering/xcom/t017/detailed-design.md` | `960bb63c151762cb946bea51f3445fdf7c11ba4cc99cb04fc026d22197eee810` |
| `docs/engineering/xcom/t017/unit-specifications.md` | `48b974e712a98d61fcccb2500a670ed343aae51ac814ffdf45c2d6739859dd10` |
| `docs/engineering/xcom/t017/verification-plan.md` | `fd2f9aac069a34466929a0be621c1d504582b4254e3a53cec67fbaa582cb9c51` |
| `specs/007-xcom-core/tasks.md` | `7ef37d266d72f46b721623ced68309e5026b9af97c30fe544bccdf0921b92141` |

Hashes are bound to this candidate state; `implementation.md` and the post-record `tasks.md` checkbox
line are not self-hashed. A successor candidate (for example a repair after a further review) must
record its own exact revision and repeat the affected checks.

## 6. Bounds and negative-case coverage

- **Profile defects (`PROFILE_INVALID`, 3):** NEG-P01..NEG-P14 (14 cases).
- **Plan defects (`PLAN_INVALID`, 4):** NEG-A01..NEG-A09 and NEG-A11..NEG-A22 (21 cases); NEG-A10 is
  the accepted inspectable control. NEG-A11..A13 and NEG-A17..A22 cover every implemented
  ordering/uniqueness branch of `check_ordering` (collection key uniqueness/order,
  activationOrder duplicates and undeclared ids, diagnostics uniqueness/order, provenance-resource
  uniqueness/order, and a mixed present/absent optional-member identity — T017-IR-008).
- **Canonical/digest defects (`DIGEST_INVALID`, 5):** NEG-D01..NEG-D04 (4 cases); NEG-D01 exercises the
  declared non-canonical key-ordering/whitespace defect with a correct domain separator.
- **Validator/bound defects:** NEG-V01..NEG-V03 (`SCHEMA_INVALID`, 2); NEG-V04..NEG-V08 (`IO_ERROR`, 6) —
  over-5-MiB document, duplicate member, over-1-MiB fixture, over-depth payload, and over-wall-bound run.
- **Boundary/governance defects (`BOUNDARY_INVALID`, 7):** NEG-G01..NEG-G05 (5 cases); NEG-G03 injects a
  promoted REF-002 entry into the authoritative record.

Validator bounds: per-fixture input ≤ 1 MiB, a supplied document ≤ 5 MiB, aggregate fixture input
≤ 16 MiB, nesting depth ≤ 100, node count ≤ 100 000, wall clock ≤ 60 s enforced in-process and observed
externally, no network, no subprocess, no filesystem write, byte-stable output. The declared negative
set is exactly the `verification-plan.md` §4 set; no case is skipped, weakened, or renumbered.

## 7. Limitations and honesty notes

1. **No acceptance or integration claim.** T017 implements and locally verifies only its own bounded
   work products. It does not accept or integrate any candidate, including itself, and it claims no
   external review or user acceptance. The internal review is a separate read-only stage; external
   Codex review is deferred until the `xcom-t007-t010-t017-t020` backlog completes.
2. **Contracts, not a runtime.** The schemas and validator prove that the Profile/plan contracts are
   well formed and internally consistent. They do **not** prove that a compiler or decoder implements
   them; that evidence belongs to T018/T019/T020. No availability, throughput, timing, compatibility,
   or production claim is made.
3. **No production numeric bound is fixed.** Every schema maximum (`deadlineMs`, `retry`, `queueDepth`,
   payload/rate bounds, quotas) is a finite declared ceiling, not a production value; runtime values
   come from the activation plan or unit configuration (FR-007).
4. **Environment identity is recorded, not pinned.** The gate's Python environment was provisioned
   outside the repository (declared dependency versions + editable `src/`); that provisioning changes
   no repository file and is not a T017 product artifact. Compiler/dependency admission with hashes and
   licenses remains T011.
5. **Public-safety scan scope.** The validator mechanically detects absolute host paths, private IPv4
   ranges, credential-assignment tokens, and private-key markers in the schemas and fixtures. The
   non-mechanical classes (proprietary excerpts, unrestricted payloads) are assessed by the review
   stage; inspection finds none. The documented workflow gate path in `verification-plan.md` §2 is
   workflow infrastructure, not artifact content.
6. **Boundary and REF-002 checks need repository evidence.** The authorized-path check consumes an
   explicit changed set supplied by the caller (the deterministic gate supplies the real
   `git diff --name-only` set externally); it makes no claim when no set is supplied. The REF-002 check
   reads `docs/architecture/sads-requirements-traceability.json`; it is evidence-bound, not a
   self-declared constant.
7. **Not-yet-present successor artifacts.** `src/xverse_xdl/xcom_plan.py` (T018),
   `src/xverse/xcom/include/xverse/xcom/activation_plan.hpp` and `src/xverse/xcom/src/activation_plan.cpp`
   (T019), and the ordering/malformed/drift/bound/regression suites (T020) are absent; T017 defines the
   contracts they consume and does not create, read, or reconcile them. The SESN-era artifacts already
   present under `src/xverse/xcom/**` are unreconciled and untouched.
8. **Work-product boundary.** The candidate diff contains no unauthorized path and no `src/xverse/xcom/`
   production path; it changes no `Doxyfile`/CMake/build file, accepted ADR, accepted contract statement,
   accepted requirement, or existing test.
