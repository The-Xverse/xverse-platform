# T011 Unit Specifications — Admitted Units and T011 Work-Product Units

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T011 |
| Stage / role | plan → unit specifications |
| Revision | 2 (repair of internal-review rev 1 findings `T011-IR-01`/`T011-IR-02`: completed the requirement-to-unit traceability; no requirement, check, contract, or unit weakened) |
| Baseline revision | `5050666bf38fc98920dc455a85a88c08c46a2133` |
| Requirements authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Implementation artifacts | `docs/engineering/xcom/t011/*.md`; `reports/xcom-queue/t011-package.json`; `internal-review.json` |

## 2. Scope, language, and conventions

T011 has two unit sets:

- **Admitted units** (`T011-U-A01`–`A11`) — the environment components T011 pins and admits. Their realized
  artifacts already exist in the baseline (owned by the `T-INTG` slice and the shared build paths); T011
  specifies their admitted contract and consumes them as read-only evidence.
- **Work-product units** (`T011-U-W01`–`W06`) — the repository-owned artifacts T011 itself authors.

Conventions:

- All identifiers are stable ASCII tokens; ordering is declared and deterministic.
- Languages follow the accepted plan: Markdown/JSON for the T011 work products; the admitted units are the
  existing Python checker, CMake modules, C++ build probes, and documentation.
- **Lifetime** for T011 work-product units is the candidate lifetime; the admitted-unit lifetime is the
  repository/toolchain lifetime described per unit.
- **Thread-safety** for all T011 units is `offline-single-threaded` or `read-only-static`; concurrency is not
  applicable and no unit spawns threads. This is an explicit decision, not a gap.
- **Doxygen** is not applicable to T011's own Markdown/JSON work products; the `XCOM-BLD-DOXYGEN` admitted unit
  carries the configuration contract and the recorded gap.

**Resource and concurrency bounds (T011 units).** Inputs are read-only and located only by the two explicit
absolute environment inputs; the checker reads local files, computes SHA-256, runs bounded local subprocesses,
and uses disposable temporary trees. No network, no package installation, no modification of either explicit
input, no threads. The bounded CMake-invoked check (`--cmake-dependency-check`) has a 120 s timeout; the
`--self-test` suite completes in well under a minute on the admitted host.

## 3. Admitted units

### T011-U-A01 — Package lock (`XCOM-ADM-LOCK`)

- **Responsibility.** Hold the twelve exact package records (filename, size, SHA-256, package, version, source,
  license) and the generated-code provenance entries.
- **Interface.** Compiled-in `PackageSpec` records in `scripts/xcom_dependency_preflight.py`; mirrored in
  `docs/engineering/xcom/dependency-lock.md`.
- **Invariants.** Exactly twelve records; filenames single-segment; digests 64-hex; sizes positive
  (`INV-01`–`INV-03`); each record's license and version present.
- **Failure semantics.** A missing/mismatched record or field is `MANIFEST_INVALID`/`VERSION_MISMATCH`; no
  partial admission.
- **Lifetime/ownership.** `read-only-static`; owned by the `T-INTG` slice; T011 admits it.
- **Requirements.** T011-STK-002, T011-STK-003, T011-SR-002, T011-SR-005.
- **Planned evidence.** CHK-04, CHK-05, CHK-07, NEG-04..NEG-08, NEG-16.

### T011-U-A02 — Package manifest and retained archives (`XCOM-ADM-MANIFEST`)

- **Responsibility.** Supply and validate the twelve-entry JSON manifest and its sibling retained archives.
- **Interface.** `XVERSE_XCOM_PACKAGE_MANIFEST` (absolute file); sibling `.deb` files.
- **Invariants.** Array of exactly twelve objects with exactly `{file, sha256, size}`; unique single-segment
  filenames; sizes and digests match the lock (`INV-01`–`INV-04`).
- **Failure semantics.** Schema/count/field/filename/digest/size defect → `MANIFEST_INVALID` (3); absent
  archive → `PACKAGE_MISSING` (4); size/digest drift → `HASH_MISMATCH` (5).
- **Lifetime/ownership.** Caller-owned external inputs; T011 admits them read-only.
- **Requirements.** T011-SR-002.
- **Planned evidence.** CHK-04, NEG-04..NEG-06, NEG-09, NEG-10.

### T011-U-A03 — Offline admission checker (`XCOM-ADM-CHECKER`)

- **Responsibility.** Implement the ordered, fail-closed admission algorithm and the classified decision.
- **Interface.** `scripts/xcom_dependency_preflight.py` with `--self-test`, `--verify-toolchain`, `--all`,
  `--cmake-dependency-check`.
- **Invariants.** Ordered phases; both explicit inputs absolute; no network, no install, no input writes; the
  decision is deterministic and sorted (`INV-06`–`INV-10`).
- **Failure semantics.** Every class in `detailed-design.md` §5.1; success only `XCOM-BLD-I000`.
- **Lifetime/ownership.** Process lifetime of one invocation; owned by the `T-INTG` slice; T011 admits it.
- **Thread-safety/bounds.** `offline-single-threaded`; bounded reads/subprocesses/temporary trees.
- **Requirements.** T011-STK-004, T011-SR-007, T011-SR-008.
- **Planned evidence.** CHK-08, CHK-09, NEG-11..NEG-33.

### T011-U-A04 — Bounded admission probes (`XCOM-ADM-PROBE`)

- **Responsibility.** `dpkg-deb -f` control metadata, executable/header/library/pkg-config probes, extracted
  payload comparison, and the disposable CMake/Ninja compile-only policy probe.
- **Interface.** Internal probe helpers invoked by `XCOM-ADM-CHECKER`.
- **Invariants.** Bounded local execution; deterministic ordering; no network.
- **Failure semantics.** Missing/drifting tool/header/library/metadata → classes 6–10; payload drift → 15;
  failed probe → 13; over-bound → 14.
- **Lifetime/ownership.** Per-invocation; `T-INTG`-owned; T011 admits it.
- **Requirements.** T011-STK-003, T011-SR-003, T011-SR-005, T011-SR-008.
- **Planned evidence.** CHK-05, CHK-07, NEG-07, NEG-08, NEG-12..NEG-15, NEG-16.

### T011-U-A05 — Admission decision (`XCOM-ADM-DECISION`)

- **Responsibility.** Serialize `admitted`, sorted diagnostics, and the stable exit class.
- **Interface.** JSON decision on stdout; process exit code.
- **Invariants.** Byte-stable serialization; lowest applicable class; `unknown` never maps to admitted
  (`INV-06`, `INV-07`).
- **Failure semantics.** Any prior-phase failure yields `admitted: false` and never a pass.
- **Lifetime/ownership.** Per-invocation; `T-INTG`-owned; T011 admits it.
- **Requirements.** T011-STK-004, T011-SR-007.
- **Planned evidence.** CHK-08, NEG-11..NEG-15.

### T011-U-A06 — Root build contract (`XCOM-BLD-ROOT`)

- **Responsibility.** Enforce Ninja-only, C++20, `BUILD_TESTING=ON`, warnings-as-errors; define the compile-only
  probes; publish `xcom-build-policy.json`.
- **Interface.** `CMakeLists.txt`; targets `xverse_xcom_policy_probe`,
  `xverse_xcom_warning_rejection_probe`; evidence `xcom-build-policy.json`.
- **Invariants.** The warning-rejection probe must fail to build; the policy evidence records the compiler,
  generator, standard, warning options, and both inputs.
- **Failure semantics.** Non-Ninja generator, disabled testing, or missing warning options is a configuration
  error (`POLICY_INVALID`).
- **Lifetime/ownership.** Repository build lifetime; shared (serialized) path; T011 admits it.
- **Requirements.** T011-STK-001, T011-SR-001, T011-SR-006.
- **Planned evidence.** CHK-01, CHK-02, CHK-03, CHK-07, CHK-11, CHK-16, NEG-01..NEG-03.

### T011-U-A07 — Warning policy module (`XCOM-BLD-WARN`)

- **Responsibility.** Publish and apply `-Wall -Wextra -Wpedantic -Werror` via `xverse::xcom_warnings`.
- **Interface.** `cmake/XComWarnings.cmake`: `xverse_xcom_configure_warnings()`,
  `xverse_xcom_apply_warnings(<target>)`.
- **Invariants.** The interface target always publishes the admitted option list.
- **Failure semantics.** Empty compile options is `POLICY_INVALID`.
- **Lifetime/ownership.** Repository build lifetime; shared path; T011 admits it.
- **Requirements.** T011-STK-001, T011-SR-001.
- **Planned evidence.** CHK-01, CHK-02, CHK-11, CHK-16, NEG-02, NEG-03.

### T011-U-A08 — Offline dependency admission module (`XCOM-BLD-DEPS`)

- **Responsibility.** Enforce the two explicit inputs, invoke the checker, disable registries/FetchContent, and
  define the imported dependency targets.
- **Interface.** `cmake/XComOfflineDependencies.cmake`: `xverse_xcom_admit_offline_dependencies()`.
- **Invariants.** No ambient discovery; admitted targets only beneath the prefix (`INV-08`, `INV-09`).
- **Failure semantics.** A failed `--cmake-dependency-check` fails configuration with the checker detail;
  missing inputs fail configuration (`INPUT_MISSING`).
- **Lifetime/ownership.** Configure lifetime; shared path; T011 admits it.
- **Requirements.** T011-STK-001, T011-SR-003, T011-SR-004.
- **Planned evidence.** CHK-01, CHK-06, CHK-11, CHK-16, NEG-09, NEG-10.

### T011-U-A09 — Admission documentation (`XCOM-ADM-DOC`)

- **Responsibility.** Record admitted identity, licenses, retrieval coordinates, offline reconstruction,
  environment/ABI limits, package-versus-payload semantics, and requirement-to-check traceability.
- **Interface.** `docs/engineering/xcom/build-environment.md`, `docs/engineering/xcom/dependency-lock.md`.
- **Invariants.** Public-safe; states prototype-only maturity; documents both inputs, generated-code
  provenance, and limitations.
- **Failure semantics.** A missing required field or an unsupported claim fails the document validation
  (`POLICY_INVALID`).
- **Lifetime/ownership.** Repository documentation; `T-INTG`-owned; T011 admits and references it.
- **Requirements.** T011-STK-005, T011-SR-009.
- **Planned evidence.** CHK-10, CHK-13.

### T011-U-A10 — Host verification-evidence contract (`XCOM-ADM-EVIDENCE`)

- **Responsibility.** Define the five-measure, network-disabled, hashed evidence contract and the repository
  `index.json` record.
- **Interface.** Documented contract in `build-environment.md`; `index.json` per candidate.
- **Invariants.** Five revision-matching records; log/manifest hashes; network-disabled isolation recorded.
- **Failure semantics.** Missing/stale/mismatched/skipped/failed evidence cannot support admission or
  acceptance; isolation that cannot be enforced fails closed.
- **Lifetime/ownership.** Per-candidate; `T-INTG`-owned; T011 defines the contract (no run in T011).
- **Requirements.** T011-SR-010.
- **Planned evidence.** CHK-12.

### T011-U-A11 — Doxygen configuration contract (`XCOM-BLD-DOXYGEN`)

- **Responsibility.** Hold the Doxygen configuration and coverage/HTML check; state the strict C++ admission
  contract and gap.
- **Interface.** `Doxyfile`, `scripts/check_doxygen.py`.
- **Invariants.** `WARN_AS_ERROR = YES`; the strict undocumented/param-doc configuration is the recorded gap
  `T011-GAP-01` until admitted.
- **Failure semantics.** Not executed by T011; warning-free generation is T037's claim.
- **Lifetime/ownership.** Repository documentation/config; `T-INTG`-owned; T011 records the contract.
- **Requirements.** T011-SR-009; gaps `T011-GAP-01`, `T011-GAP-02`.
- **Planned evidence.** CHK-10, CHK-13.

## 4. T011 work-product units

### T011-U-W01 — Requirements work product

- **Responsibility.** Register the T011 stakeholder/engineering requirements, scope, authorities, affected
  paths, REF-002 disposition, gaps, and requirement-to-check index.
- **Interface.** `docs/engineering/xcom/t011/requirements.md`.
- **Invariants.** Every requirement has an accepted anchor and at least one named check; no accepted intent is
  weakened; T011 identifies itself and the baseline revision.
- **Failure semantics.** A dangling anchor or an unmapped requirement fails the consistency check (CHK-17).
- **Lifetime/ownership.** Candidate lifetime; T-ENABLER (T011).
- **Requirements.** T011-SR-011, T011-SR-012, T011-SR-013.
- **Planned evidence.** CHK-16, CHK-17, CHK-18.

### T011-U-W02 — Architecture work product

- **Responsibility.** Specify the admission boundary, trust boundaries, components, data flow, interfaces,
  quality attributes, and traceability.
- **Interface.** `docs/engineering/xcom/t011/architecture.md`.
- **Invariants.** No prohibited element; dependency direction and domain neutrality preserved.
- **Failure semantics.** A reverse dependency or a prohibited element fails CHK-15/CHK-18.
- **Lifetime/ownership.** Candidate lifetime; T-ENABLER (T011).
- **Requirements.** T011-SR-011, T011-SR-013.
- **Planned evidence.** CHK-15, CHK-18.

### T011-U-W03 — Detailed-design work product

- **Responsibility.** Specify the pinned identity model, the admission algorithm, the build contract, the
  evidence contract, and public-safety/error handling.
- **Interface.** `docs/engineering/xcom/t011/detailed-design.md`.
- **Invariants.** Every phase maps to a stable class; success only `XCOM-BLD-I000`.
- **Failure semantics.** An undocumented class or a claim beyond the design fails CHK-08.
- **Lifetime/ownership.** Candidate lifetime; T-ENABLER (T011).
- **Requirements.** T011-SR-007, T011-SR-009.
- **Planned evidence.** CHK-08, CHK-10.

### T011-U-W04 — Unit-specifications work product

- **Responsibility.** Specify the admitted units and T011 work-product units with responsibility, interface,
  invariants, failure semantics, lifetime/ownership, thread-safety/bounds, requirements, and evidence.
- **Interface.** `docs/engineering/xcom/t011/unit-specifications.md`.
- **Invariants.** Every unit names its owners, bounds, requirements, and planned evidence.
- **Failure semantics.** A unit without bounds or evidence fails CHK-17.
- **Lifetime/ownership.** Candidate lifetime; T-ENABLER (T011).
- **Requirements.** T011-SR-011, T011-SR-013.
- **Planned evidence.** CHK-17, CHK-18.

### T011-U-W05 — Verification-plan work product

- **Responsibility.** Name the deterministic gate, nominal checks, negative cases, evidence, and exit criteria
  before implementation.
- **Interface.** `docs/engineering/xcom/t011/verification-plan.md`.
- **Invariants.** Every requirement maps to ≥ 1 check; every check states an expected result; negative cases
  fail closed.
- **Failure semantics.** A missing check or an unstated expectation fails CHK-16.
- **Lifetime/ownership.** Candidate lifetime; T-ENABLER (T011).
- **Requirements.** T011-SR-012.
- **Planned evidence.** CHK-16, CHK-17.

### T011-U-W06 — Implementation record and package

- **Responsibility.** Record the realized change and evidence, and write the exact-candidate package record.
- **Interface.** `docs/engineering/xcom/t011/implementation.md`, `reports/xcom-queue/t011-package.json`.
- **Invariants.** The package lists changed paths and hashes and binds the baseline revision; the record claims
  no acceptance.
- **Failure semantics.** A package that omits a changed path or binds a stale revision fails CHK-16.
- **Lifetime/ownership.** Candidate lifetime; T-ENABLER (T011); produced in the implementation stage.
- **Requirements.** T011-SR-012, T011-SR-013.
- **Planned evidence.** CHK-16, CHK-17.

## 5. Requirement-to-unit traceability

| Unit | Requirement(s) |
| --- | --- |
| T011-U-A01 | T011-STK-002, T011-STK-003, T011-SR-002, T011-SR-005 |
| T011-U-A02 | T011-SR-002 |
| T011-U-A03 | T011-STK-004, T011-SR-007, T011-SR-008 |
| T011-U-A04 | T011-STK-003, T011-SR-003, T011-SR-005, T011-SR-008 |
| T011-U-A05 | T011-STK-004, T011-SR-007 |
| T011-U-A06 | T011-STK-001, T011-SR-001, T011-SR-006 |
| T011-U-A07 | T011-STK-001, T011-SR-001 |
| T011-U-A08 | T011-STK-001, T011-SR-003, T011-SR-004 |
| T011-U-A09 | T011-STK-005, T011-SR-009 |
| T011-U-A10 | T011-SR-010 |
| T011-U-A11 | T011-SR-009 (gaps `T011-GAP-01`, `T011-GAP-02`) |
| T011-U-W01 | T011-SR-011, T011-SR-012, T011-SR-013 |
| T011-U-W02 | T011-SR-011, T011-SR-013 |
| T011-U-W03 | T011-SR-007, T011-SR-009 |
| T011-U-W04 | T011-SR-011, T011-SR-013 |
| T011-U-W05 | T011-SR-012 |
| T011-U-W06 | T011-SR-012, T011-SR-013 |

## 6. Coverage and exemptions

- Every T011 requirement in `requirements.md` §3–§4 is covered by ≥ 1 admitted or work-product unit.
- `T011-SR-006` (sanitizer capability) is covered by `T011-U-A06` and `detailed-design.md` §4.5 as a probed
  compiler capability; executed sanitizer evidence is exempt from T011 and owned by T035 (`T011-GAP-03`).
- `T011-SR-010` (host evidence) is covered as a **contract** by `T011-U-A10`; the executed, candidate-bound
  evidence is exempt from T011 and owned by T035–T038 (`T011-GAP-04` records the pending acceptance).
- No unit is exempt without a reason and an owning task, and no exemption closes a gap silently.
