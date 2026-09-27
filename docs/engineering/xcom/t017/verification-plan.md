# T017 Verification Plan — Named Checks, Commands, Negative Cases, and Expected Results (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T017 |
| Stage / role | plan → verification plan (pre-code) |
| Revision | 1 |
| Baseline revision | `a78d6d55dd5a68b1572cf5a594100dfba3be523e` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Check framework | repository-owned Python validator plus the deterministic Fabro gate and the full `pytest` suite; no C++/GTest case is added by T017 |

This plan is written **before** implementation. The implementation must realise every named check with the
stated expected result. Weakening an expected result is a verification-contract change requiring review.

## 2. Deterministic gate (primary)

From the repository root:

```sh
python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T017 a78d6d55dd5a68b1572cf5a594100dfba3be523e
```

For T017 this gate requires:

- `docs/engineering/xcom/t017/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`
  present;
- the T017 checkbox in `specs/007-xcom-core/tasks.md` marked complete (**implementation stage only**; the plan
  stage leaves it unchecked, per the stage instruction);
- a changed-path set containing at least one path under `specs/007-xcom-core/contracts/` **or** `xdl/`;
- a changed-path set containing at least one path under `tests/`;
- `git diff --check <baseline> --` clean;
- the full `pytest` suite passing (`python3 -m pytest -q`).

Supporting commands (same tools, no network):

```sh
python3 scripts/validate_xcom_plan.py --verify
python3 scripts/validate_xcom_plan.py --verify --changed-paths <candidate-changed-paths-file>
python3 scripts/validate_xcom_plan.py --self-test
python3 scripts/validate_xcom_plan.py --check-human
python3 -m pytest -q tests/xcom/activation_plan
python3 -m pytest -q
python3 scripts/validate_xcom_task_ownership.py --verify
git rev-parse a78d6d55dd5a68b1572cf5a594100dfba3be523e
git diff --name-only a78d6d55dd5a68b1572cf5a594100dfba3be523e --
git diff --check a78d6d55dd5a68b1572cf5a594100dfba3be523e --
```

`git rev-parse` for the baseline must print the baseline SHA, proving the binding resolves.

The documented gate invocation path above is workflow infrastructure (an agent instruction), not T017
artifact content, and is out of scope of the public-safety content rule; see `requirements.md` §2.4.

### 2.1 Environment prerequisite (must hold before the implementation gate can pass)

The repository declares Python dependencies (`jsonschema[format]>=4.26,<5`, `referencing`, `ruamel.yaml`) and a
`src/` package layout in `pyproject.toml`, and the existing suite imports `xverse_xdl`. The declared baseline
shell does **not** have those packages importable under the default `python3`. The implementation stage must
run the checks under a Python 3.11+ environment where the declared dependencies are importable and this
repository's `src/` is on `sys.path` (for example the repository's provisioned virtual environment, or an
equivalent environment with the locked versions). This provisioning changes no repository file. If it cannot
be provided, the implementation stage must return a **failed** outcome and must **not** weaken, skip, or edit
an existing test to force the gate to pass.

## 3. Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| CHK-01 | Profile schema parses and is closed | `--verify` | exit 0; valid Draft 2020-12; `additionalProperties: false` at every object |
| CHK-02 | Profile discriminator and version | `--verify` | `schemaVersion` const `"0.1"`; `kind` enum equals exactly the five forms; `required` contains `schemaVersion`, `kind`, `target`, `policy` |
| CHK-03 | Per-form payload grammar | `--verify` | all five `policy` forms declared and closed with the required members of `detailed-design.md` §3.2 |
| CHK-04 | Placement and logical-resource safety | `--verify` + contract inspection | no address/credential/permit/handle/session member; contract text states the extension-location rule |
| CHK-05 | Plan schema parses and is closed | `--verify` | exit 0; valid Draft 2020-12; closed at every object |
| CHK-06 | Plan required-content coverage | `--verify` | every required-content group maps to a required member; `planVersion` const `"1"` |
| CHK-07 | Inspectable vs activatable | `--verify` | the conditional rule is present; `activatable` with an unresolved input is rejected; `inspectable` with one is accepted |
| CHK-08 | Deterministic ordering and uniqueness | `--verify` | every identity-bearing array ordered by its declared key with unique keys; `activationOrder` a duplicate-free permutation |
| CHK-09 | Digest/provenance members | `--verify` | `digest`/`provenance` members match `detailed-design.md` §4.1–§4.2; digest value matches `^[0-9a-f]{64}$` |
| CHK-10 | Digest recomputation and drift | `--verify` | recomputed digest over the canonical body equals the recorded digest; a mutated body is rejected |
| CHK-11 | Validator exit classes | `--self-test` | each declared defect yields its declared nonzero exit class with no partial success |
| CHK-12 | Validator offline/bounded | source inspection + over-bound probe | imports limited to stdlib + `jsonschema`/`referencing`; no network/subprocess/write; over-bound input → `IO_ERROR` |
| CHK-13 | Validation tests | `pytest tests/xcom/activation_plan` | Profile, plan, and digest families present; every declared positive/negative case asserted; pass |
| CHK-14 | Additive contract recording | `git diff` inspection | `xdl-profile.md` gains exactly the two new sections; no existing sentence altered |
| CHK-15 | Authorized-path boundary | external `git diff --name-only` inspection; optional `--verify --changed-paths <file>` | changed set ⊆ `detailed-design.md` §2.1 + `docs/engineering/xcom/t017/**` + `reports/xcom-queue/t017-package.json`; no `src/xverse/xcom/{include,src}/**`, `src/xverse_xdl/**`, `proto/**`, CMake, `Doxyfile`. The offline validator cannot start `git`; `--verify` alone consumes no changed set and therefore claims no boundary, while `--verify --changed-paths <file>` re-checks a caller-supplied set |
| CHK-16 | Baseline, authorization, REF-002 | `--verify` + `git rev-parse` + matrix check | baseline binds; authorizations ⊆ accepted set; `XCOM-SW-XDL-001` links resolve; the authoritative REF-002 record (`docs/architecture/sads-requirements-traceability.json`) records every `XVE-SYS-0139`–`0158` target as `allocated`/`deferred` `architectural-target` with none promoted |

## 4. Negative cases (validator self-test fixtures)

Each `NEG-*` injects one controlled defect — into a copy of a schema or a fixture, or by withholding a
dependency — and asserts the declared nonzero exit with **no** partial success and no output claiming a valid
artifact.

### 4.1 Profile payload defects (`PROFILE_INVALID`, exit 3)

| ID | Injected defect |
| --- | --- |
| NEG-P01 | Remove `schemaVersion` |
| NEG-P02 | Set `schemaVersion` to an unsupported value (e.g. `"0.2"`) |
| NEG-P03 | Remove `kind` |
| NEG-P04 | Set `kind` to an unknown token |
| NEG-P05 | Add an unknown top-level field (closed-object violation) |
| NEG-P06 | `interface-policy` missing `interactionKind` |
| NEG-P07 | `flow-policy` with an unknown `overflow` token |
| NEG-P08 | `network-provider` missing `requiredCapabilities` |
| NEG-P09 | `observation-policy` with `payloadAccess: allow-listed` but no allow list/bounds |
| NEG-P10 | `validation-policy` with `serviceEmulation: true` but no `permitPolicyRef` |
| NEG-P11 | Add an unknown field inside a form's `policy` object |
| NEG-P12 | Place a provider address/credential field in the payload |
| NEG-P13 | Place a validation permit or live handle in the payload |
| NEG-P14 | Provide two conflicting payloads for the same decorated identity / illegal attachment location |

### 4.2 Activation-plan defects (`PLAN_INVALID`, exit 4)

| ID | Injected defect |
| --- | --- |
| NEG-A01 | Remove `planVersion` |
| NEG-A02 | Set `planVersion` to `"2"` |
| NEG-A03 | Remove a required content group (e.g. `clockDomains`) |
| NEG-A04 | Add an unknown top-level field |
| NEG-A05 | Remove `routes` |
| NEG-A06 | Remove `activationOrder` |
| NEG-A07 | Remove `policies` |
| NEG-A08 | Remove `diagnostics` |
| NEG-A09 | `status: activatable` with one `inputResolution` member `unresolved` |
| NEG-A10 | `status: inspectable` with one `inputResolution` member `unresolved` (accepted positive case) |
| NEG-A11 | Duplicate a `routeId` |
| NEG-A12 | Store a collection out of its declared order |
| NEG-A13 | Duplicate an `activationOrder` entry / include an undeclared route |
| NEG-A14 | Remove `digest` |
| NEG-A15 | Remove `provenance` |
| NEG-A16 | Remove `provenance.graphDigest` or a resource `sourceDigest` |
| NEG-A17 | `activationOrder` names an id that is not a declared endpoint or route |
| NEG-A18 | Store `diagnostics` out of its declared `(code, targetId)` order |
| NEG-A19 | Store `provenance.resources` out of its declared identity order |
| NEG-A20 | Duplicate a `(code, targetId)` diagnostic entry |
| NEG-A21 | Duplicate a `provenance.resources` identity |
| NEG-A22 | Duplicate a `provenance.resources` identity where one entry omits the optional `version` (mixed present/absent optional member) |

### 4.3 Canonical serialization and digest defects (`DIGEST_INVALID`, exit 5)

| ID | Injected defect |
| --- | --- |
| NEG-D01 | A plan body digest is computed over a non-canonical (reversed key-order, whitespace) serialization of the same body |
| NEG-D02 | Digest computed without the domain separator / with the wrong domain separator |
| NEG-D03 | Recorded digest does not match the recomputed digest of the body (drift) |
| NEG-D04 | Digest region includes the `digest` member itself (self-reference) |

### 4.4 Validator and bound defects (`SCHEMA_INVALID`/`IO_ERROR`, exit 2/6)

| ID | Injected defect |
| --- | --- |
| NEG-V01 | A schema is not valid Draft 2020-12 |
| NEG-V02 | A schema is not closed (`additionalProperties` not `false` at an object) |
| NEG-V03 | Validator source imports a network module / attempts a subprocess |
| NEG-V04 | Over-5-MiB supplied document (size bound) |
| NEG-V05 | A document repeats an object member name (duplicate-member rejection) |
| NEG-V06 | A Profile fixture exceeds the 1 MiB per-fixture bound |
| NEG-V07 | An input exceeds the declared nesting-depth bound |
| NEG-V08 | A run exceeds the declared wall-clock bound |

### 4.5 Boundary and governance defects (`BOUNDARY_INVALID`/`failed`, exit 7)

| ID | Injected defect |
| --- | --- |
| NEG-G01 | Candidate changed a path outside the authorized set (e.g. `src/xverse_xdl/xcom_plan.py`) |
| NEG-G02 | Candidate changed `src/xverse/xcom/include/**` or `src/xverse/xcom/src/**` |
| NEG-G03 | A REF-002 target is recorded as promoted/implemented |
| NEG-G04 | A schema/fixture/evidence contains a credential, private address, or absolute host path |
| NEG-G05 | The T017 checkbox is marked complete in the plan stage |

## 5. Determinism checks

| ID | Check | Expected |
| --- | --- | --- |
| DET-01 | `--verify` run twice on the real artifacts | byte-identical output and exit status |
| DET-02 | Canonical serialization of a reordered-but-equivalent body | identical canonical bytes and digest |
| DET-03 | `--check-human` against the committed expectation | exact match |

## 6. Bound checks

| ID | Bound | Expected |
| --- | --- | --- |
| BND-01 | Per-document input size | fixtures ≤ 1 MiB and a supplied document ≤ 5 MiB, applied to every parsed document (Profile payloads, plans, and both schemas); over-bound → `IO_ERROR` |
| BND-02 | Aggregate input size | ≤ declared aggregate bound |
| BND-03 | Nesting depth / JSON node count | ≤ declared depth/node bounds, enforced for every parsed document; over-bound → `IO_ERROR` |
| BND-04 | Wall clock / no network / no subprocess / no write | `run_checks` enforces the declared wall bound (`check_wall_bound`) and is observed externally with `/usr/bin/time`; no network, subprocess, or write attempted |

## 7. Exact planned tests (implementation stage)

| Test | Family | Asserts |
| --- | --- | --- |
| `tests/xcom/activation_plan/test_profile_schema.py::test_valid_profile_payload_accepted` | positive | CHK-01..CHK-04 |
| `tests/xcom/activation_plan/test_profile_schema.py::test_profile_schema_is_closed_and_discriminated` | positive | CHK-01..CHK-03 |
| `tests/xcom/activation_plan/test_profile_schema.py::test_profile_negatives` | negative | NEG-P01..P14 |
| `tests/xcom/activation_plan/test_profile_schema.py::test_unknown_field_and_kind_rejected_explicitly` | negative | NEG-P04, NEG-P05 |
| `tests/xcom/activation_plan/test_activation_plan_schema.py::test_valid_plan_accepted` | positive | CHK-05..CHK-09 |
| `tests/xcom/activation_plan/test_activation_plan_schema.py::test_inspectable_plan_accepted` | positive | CHK-07, NEG-A10 |
| `tests/xcom/activation_plan/test_activation_plan_schema.py::test_plan_schema_closed_and_covers_required_content` | positive | CHK-05, CHK-06 |
| `tests/xcom/activation_plan/test_activation_plan_schema.py::test_plan_negatives` | negative | NEG-A01..A09, A11..A22 |
| `tests/xcom/activation_plan/test_activation_plan_schema.py::test_ordering_uniqueness_branches_exercised_directly` | negative | NEG-A17..A21 |
| `tests/xcom/activation_plan/test_activation_plan_schema.py::test_ordering_totality_over_optional_version` | negative | T017-IR-008 closure (NEG-A22) |
| `tests/xcom/activation_plan/test_activation_plan_schema.py::test_activatable_with_unresolved_input_rejected` | negative | NEG-A09 |
| `tests/xcom/activation_plan/test_digest_contract.py::test_canonical_bytes_and_digest_are_key_order_stable` | positive | CHK-10, DET-02 |
| `tests/xcom/activation_plan/test_digest_contract.py::test_digest_round_trip` | positive | CHK-10 |
| `tests/xcom/activation_plan/test_digest_contract.py::test_digest_region_excludes_digest_member` | positive | NEG-D04 guard |
| `tests/xcom/activation_plan/test_digest_contract.py::test_canonical_bytes_normalize_integral_numbers` | positive | T017-IR-001 closure (CHK-10) |
| `tests/xcom/activation_plan/test_digest_contract.py::test_digest_negatives` | negative | NEG-D01..D04 |
| `tests/xcom/activation_plan/test_digest_contract.py::test_validator_and_governance_negatives` | negative | NEG-V01..V08, NEG-G01..G05 |
| `tests/xcom/activation_plan/test_digest_contract.py::test_duplicate_json_member_rejected` | negative | T017-IR-002 closure (NEG-V05) |
| `tests/xcom/activation_plan/test_digest_contract.py::test_declared_bounds_enforced` | negative | T017-IR-005 closure (NEG-V06..V08, BND-01/BND-03/BND-04) |
| `tests/xcom/activation_plan/test_digest_contract.py::test_authorized_path_boundary_consumes_changed_set` | negative | T017-IR-003 closure (CHK-15) |
| `tests/xcom/activation_plan/test_digest_contract.py::test_ref002_authoritative_record_not_promoted` | negative | T017-IR-004 closure (CHK-16) |
| `tests/xcom/activation_plan/test_digest_contract.py::test_self_test_entry_point_passes` | tool | CHK-11, CHK-13 |
| `tests/xcom/activation_plan/test_digest_contract.py::test_verification_plan_lists_every_implemented_test` | traceability | T017-IR-007 closure (plan/test identifier agreement) |
| `scripts/validate_xcom_plan.py --verify` / `--self-test` / `--check-human` | tool | CHK-01..CHK-12, DET-01..DET-03, BND-01..BND-04 |
| `python3 -m pytest -q` | gate | full suite passes |

## 8. Expected results and limitations

- All checks and negative cases are deterministic and offline; the validator exits with exactly one class per
  failure family and never reports a passing result for a partial check.
- The tests prove that the **contracts** are well formed and internally consistent. They do **not** prove that
  a compiler or decoder implements them correctly; that evidence belongs to T018/T019/T020.
- No runtime, throughput, timing, availability, compatibility, or production claim is made.
- The plan-stage candidate changes only documentation; the deterministic gate cannot pass until the
  implementation stage supplies the schemas, contract sections, validator, tests, and implementation record
  and marks the T017 checkbox.

## 9. Traceability of checks

| Requirement | Checks | Negative cases |
| --- | --- | --- |
| T017-SR-001 | CHK-01, CHK-02 | NEG-P01..P05 |
| T017-SR-002 | CHK-03 | NEG-P06..P11 |
| T017-SR-003 | CHK-04 | NEG-P12..P14 |
| T017-SR-004 | CHK-05, CHK-06 | NEG-A01..A08 |
| T017-SR-005 | CHK-07 | NEG-A09, NEG-A10 |
| T017-SR-006 | CHK-08 | NEG-A11..A13, NEG-A17..A22 |
| T017-SR-007 | CHK-09, CHK-10, DET-01..DET-03 | NEG-A14..A16, NEG-D01..D04 |
| T017-SR-008 | CHK-11, CHK-12, BND-01..BND-04 | NEG-V01..V08 |
| T017-SR-009 | CHK-13 | (positive and negative via tests) |
| T017-SR-010 | CHK-14 | NEG-G01..G05 |
| T017-SR-011 | CHK-15, CHK-16 | NEG-G01..G05 |
