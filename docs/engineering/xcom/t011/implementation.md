# T011 Implementation Record — Pinned and Admitted Offline X-COM Build and Dependency Environment

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T011 (capability 007, phase 2 repository-owned engineering baseline) |
| Stage / role | implementation → implementation record |
| Revision | 3 (successor candidate repairing the inherited T020 provenance rejected by the delivery-input audit, on top of the rev-2 repair of internal review rev 1 findings `T011-IR-01`/`T011-IR-02`) |
| Authorized baseline | `5050666bf38fc98920dc455a85a88c08c46a2133` |
| Predecessor | T010 reviewed terminal package `abb8168` (`docs/engineering/xcom/t010/`) |
| Candidate state | working tree over the authorized baseline (staged for the deterministic gate; candidate revision assigned when the workflow checkpoints) |
| Work products | [`requirements.md`](requirements.md), [`architecture.md`](architecture.md), [`detailed-design.md`](detailed-design.md), [`unit-specifications.md`](unit-specifications.md), [`verification-plan.md`](verification-plan.md), this record |
| Internal review | [`internal-review.json`](internal-review.json) (separate read-only DeepSeek review of this candidate) |
| Package record | `reports/xcom-queue/t011-package.json` (written by the deterministic package action) |
| Authorization | ACC001–ACC015, ADR-0016, ADR-0018, ADR-0019, ADR-0020; `specs/007-xcom-core/tasks.md` T011 |
| Maturity | Engineering-baseline work product implemented and locally verified; not user-accepted, not externally reviewed |
| Classification | Public-safe engineering work product |

## 2. Candidate summary

T011 implements the bounded, **work-product-only** engineering-baseline slice required by the T011 task entry:
*"Pin and admit the compiler, build, `nlohmann/json`, gRPC/Protocol Buffers, static-analysis, sanitizer, and
Doxygen environment with licenses, hashes, generated-code provenance, and a reproducible/offline strategy."*

The repository baseline already contains an accepted-prototype build/dependency foundation produced under the
earlier `specs/008`–`specs/011` work: `docs/engineering/xcom/build-environment.md`,
`docs/engineering/xcom/dependency-lock.md`, `scripts/xcom_dependency_preflight.py`,
`cmake/XComOfflineDependencies.cmake`, `cmake/XComWarnings.cmake`, `CMakeLists.txt`, `Doxyfile`, and
`scripts/check_doxygen.py`. Under capability 007 those artifacts are **allocated to T011 for admission but are
not yet user-accepted under this capability** (the T007 register records `T011: allocated`). T011 therefore:

1. authors and freezes the capability-007 admission work products (requirements, architecture, detailed design,
   unit specifications, verification plan) that bind the environment to the accepted requirement IDs;
2. **re-validates** the existing foundation against those contracts through the checker's controlled
   document/license/provenance/offline checks and the shared register validators; and
3. records the residual gaps with their owning tasks without editing an artifact owned by another slice.

T011 claims **no** runtime, compatibility, parity, adapter, registry, or production-readiness behavior. The
candidate changes **no** path under `src/`, `tests/`, or `xdl/`, authors no `proto/` definition, adds no CMake
target or runtime artifact, installs/downloads/builds no package, opens no network endpoint, and accepts,
completes, or integrates no other task or software candidate. It compiles, links, and executes no X-COM code:
the admitted-foundation artifacts stay read-only and only the offline admission checker's controlled fixtures
and the register validators run.

## 3. Implemented change

| Path | Change | Role |
| --- | --- | --- |
| `docs/engineering/xcom/t011/requirements.md` | add (plan stage, frozen) | T011-STK/T011-SR requirements, scope, authorities, affected paths, REF-002 disposition, gaps, requirement-to-check index |
| `docs/engineering/xcom/t011/architecture.md` | add (plan stage, frozen) | admission boundary, trust boundaries, components, ordered data flow, interfaces, quality attributes, traceability |
| `docs/engineering/xcom/t011/detailed-design.md` | add (plan stage, frozen) | pinned identity model, ordered admission algorithm, build contract, evidence contract, public-safety/error handling |
| `docs/engineering/xcom/t011/unit-specifications.md` | add (plan stage, frozen) | eleven admitted units `T011-U-A01`–`A11` and six work-product units `T011-U-W01`–`W06` |
| `docs/engineering/xcom/t011/verification-plan.md` | add (plan stage, frozen) | deterministic gate, CHK-01–CHK-19, NEG-01–NEG-33, candidate-bound evidence, exit criteria |
| `docs/engineering/xcom/t011/implementation.md` | add (this record) | realized change, commands and observed results, artifact identity, gap/maturity statement |
| `specs/007-xcom-core/tasks.md` | edit (T011 checkbox `[ ]` → `[X]`) | capability task ledger; marked complete only after the authorized work and every required local check passed |
| `engineering/trace/links.json` | edit (3 stale `target_revision` digests) | inherited T020 trace; provenance repair recorded in §3.3 |
| `engineering/stage-results/documentation.json` | edit (4 stale artifact digests) | inherited T020 stage record; provenance repair recorded in §3.3 |
| `engineering/stage-results/implementation.json` | edit (3 stale artifact digests) | inherited T020 stage record; provenance repair recorded in §3.3 |
| `engineering/stage-results/integration.json` | edit (1 stale artifact digest) | inherited T020 stage record; provenance repair recorded in §3.3 |
| `engineering/stage-results/internal-review.json` | edit (1 stale artifact digest) | inherited T020 stage record; provenance repair recorded in §3.3 |

The five `engineering/` rows are **inherited T020 records whose provenance digests were already stale in the
authorized baseline**; the correction is described in §3.3. They are not T011 work products: no relation,
`source`/`target` endpoint, test, source file, or accepted artifact was added, removed, or reworded, and no
T011 work product other than this implementation record is touched.

### 3.1 Detail resolutions

Two implementation decisions reconcile the realized change with the plan package. Neither changes an accepted
requirement, check, contract, boundary, or REF-002 disposition.

1. **`D-01` — the shared ownership reconciliation is a re-validation, not a textual edit.** The plan's
   `requirements.md` §7.1 lists `docs/engineering/xcom/task-ownership.{json,md}` among the paths the candidate
   may change (the scope note likewise names the shared reconciliation). The register remains **unchanged**
   because T011 introduces no new owned path and its reconciliation status must stay `allocated`:
   `scripts/validate_xcom_task_ownership.py` fixes `T011` at `allocated` (it is not in `UNRECONCILED_TASKS` or
   `ACCEPTED_TASKS`), and T011's artifacts are already covered by the `T-ENABLER` exclusive entries
   `docs/engineering/xcom/t011/` and `reports/xcom-queue/t011-package.json`. Every earlier `T-ENABLER` task
   (T008/T009/T010) edited the register only because it **added a new validator script** to the slice's
   exclusive set; T011 adds no script (the checker is T-INTG-owned read-only evidence), so there is nothing to
   declare. The obligation in `T011-SR-013` / `CHK-18` is to *re-validate* the register without weakening it,
   which the commands in §4 do. This resolution is reported to the internal review as a deliberate,
   non-weakening outcome, not a silently dropped path.
2. **`D-02` — the admitted foundation is consumed read-only.** `build-environment.md`, `dependency-lock.md`,
   `scripts/xcom_dependency_preflight.py`, `cmake/XComOfflineDependencies.cmake`, `cmake/XComWarnings.cmake`,
   `CMakeLists.txt`, `Doxyfile`, and `scripts/check_doxygen.py` are owned by the `T-INTG` slice and the shared
   build paths. T011 references them and validates their admitted contract; it edits none of them (`CHK-15`).
   The strict Doxygen configuration (`T011-GAP-01`) and sanitizer opt-in wiring (`T011-GAP-03`) remain open in
   their owning tasks rather than being closed by an unauthorized edit.

### 3.2 Repair of internal review rev 1 findings (`T011-IR-01`, `T011-IR-02`)

Revision 1 of this record was reviewed read-only by DeepSeek (`internal-review.json` rev 1, verdict `fail`). The
deterministic gate and all four register validators passed at rev 1; the sole failures were two traceability
defects in `unit-specifications.md`, now closed by a documentation-only repair of that one work product. No
requirement, check, negative case, contract, boundary, gap, REF-002 disposition, or accepted artifact was
weakened, renumbered, or dropped.

| Finding | Defect | Repair | Closure evidence |
| --- | --- | --- | --- |
| `T011-IR-01` | `unit-specifications.md` §5 mapped only 15 of the 18 requirement ids; §6's universal-coverage claim was false. `T011-STK-001`, `T011-STK-003`, and `T011-SR-006` had no unit binding. | Bound `T011-STK-001` to the pinned-envelope units `T011-U-A06`/`A07`/`A08`; bound `T011-STK-003` (generated-code provenance) to `T011-U-A01`/`A04`; bound `T011-SR-006` to `T011-U-A06`. Added the identifiers to each unit's §3/§4 `- **Requirements.**` line and its §5 table row, and extended each unit's `Planned evidence` with the checks that already carry those requirements in `requirements.md` §10. | Programmatic set extraction (command R-1 below) now prints `declared: 18`, `mapped: 18`, empty `missing`, empty `extra`, and `all per-unit agree`. |
| `T011-IR-02` | §6 asserted `T011-SR-006` was covered by `T011-U-A06`, but `A06`'s §3 requirement line and §5 row listed only `T011-SR-001`. | Added `T011-SR-006` to `T011-U-A06`'s §3 `- **Requirements.**` line and its §5 table row so the authoritative mapping matches the §6 exemption prose. The `T011-SR-006` supporting evidence in `requirements.md` §10 (CHK-03, CHK-07) and gap `T011-GAP-03` are unchanged. | The same R-1 check confirms `T011-U-A06`'s §3 line and §5 row both read `T011-STK-001, T011-SR-001, T011-SR-006`. |

Repair-local verification (offline, no network, no build):

| # | Command | Exit | Result |
| ---: | --- | ---: | --- |
| R-1 | `python3 - <<'EOF'` (extract `T011-STK-###`/`T011-SR-###` from `requirements.md` §3-§4 and `unit-specifications.md` §5; set-difference; compare each unit's §3/§4 `- **Requirements.**` line with its §5 row) | 0 | `declared: 18`, `mapped: 18`, `missing from section5: []`, `extra: []`, `all per-unit agree` — both findings closed. |
| R-2 | `git diff --check 5050666bf38fc98920dc455a85a88c08c46a2133 --` | 0 | Empty output; the repaired candidate stays whitespace-clean (CHK-19). |
| R-3 | `git diff --name-only 5050666bf38fc98920dc455a85a88c08c46a2133 --` | 0 | The same seven T011 paths as rev 1; the path set is unchanged and no `src/`/`tests/`/`xdl/`/`proto/` path appears (CHK-15). |

The repair is documentation-only within `docs/engineering/xcom/t011/`; the deterministic verification gate and
the four shared validators in §4.1 are re-run unchanged on the successor candidate.

### 3.3 Repair of inherited stale T020 provenance (`delivery-input audit`)

After the rev-2 candidate had passed unit, static analysis, target-repository integration, and validation, the
deterministic delivery-input audit (`/home/jefferson/x-verse_fabric/.fabro/workflows/xcom-t011-checkpoint-flash/audit_delivery_inputs.py`,
which invokes the **unchanged** core `validate_project`, `validate_trace`, and `validate_stage` functions) rejected
the inherited T020 provenance carried over the authorized baseline. The stale fields are real: the accepted
T007–T020 terminal repair (`c4b8225`, findings R-01…R-05) revised the T020 work products and test sources
**after** the T020 trace links and stage records were written, and did not refresh the recorded digests. The
T011 candidate authors none of these files, so nothing in T011 weakens or masks the mismatch.

Two classes of stale digest were corrected, and only these digests changed:

1. **Three `implemented_by` endpoint revisions** in `engineering/trace/links.json`:
   `T020-L-037` and `T020-L-042` (both `target`
   `tests/xcom/activation_plan/t020_malformed_plan_tests.cpp`) and `T020-L-047` (`target`
   `docs/engineering/xcom/t020/requirements.md`).
2. **Nine stage-record artifact digests**, six of them named by the read-only audit plus three that the trace
   correction itself makes stale (because repairing the trace rewrites `engineering/trace/links.json`, whose
   digest is pinned by three inherited records):
   - `engineering/stage-results/documentation.json` — `docs/engineering/xcom/t020/requirements.md`,
     `verification-plan.md`, `implementation.md`, and the `engineering/trace/links.json` self-reference;
   - `engineering/stage-results/implementation.json` — `tests/xcom/activation_plan/t020_support.hpp`,
     `t020_malformed_plan_tests.cpp`, and `docs/engineering/xcom/t020/implementation.md`;
   - `engineering/stage-results/integration.json` and `engineering/stage-results/internal-review.json` — the
     `engineering/trace/links.json` self-reference only.

| Field | Before (stale) | After (actual) |
| --- | --- | --- |
| `links.json` `T020-L-037`, `T020-L-042` `target_revision` | `38e60e613fae4316f7536c7e774dc0046133d963b0b80ca566de36d50b9b5bef` | `75046040c1f06655ba34bee851f7044cd4f8cef8190a30ff5850775dbddbde22` |
| `links.json` `T020-L-047` `target_revision` | `1aa7920c3c433664b41d5cd8773a07905a30bc030f3662ffbca34b09a66ec0c6` | `2e9ca0ef48d25aa4ca90ef5635557f7e9f6bd76161eb6a83aa315a6696c3967a` |
| `documentation.json` `docs/engineering/xcom/t020/requirements.md` | `1aa7920c3c433664b41d5cd8773a07905a30bc030f3662ffbca34b09a66ec0c6` | `2e9ca0ef48d25aa4ca90ef5635557f7e9f6bd76161eb6a83aa315a6696c3967a` |
| `documentation.json` `docs/engineering/xcom/t020/verification-plan.md` | `d4d51bfc4ca511f577bad6380fe766e18d3ab4a7be65f73e3b3c18f5965d3194` | `af04bbbd02b8737e689d7b510f50661bf9cecbdcf76296edf6af3db4dea5efa5` |
| `documentation.json` `docs/engineering/xcom/t020/implementation.md` | `bd7eadd5a491ede1144b430695a3792bbe255ad2225c485ecf282777f627dcdb` | `5484618d1dde3fa2d9cdba090781c092f6dd01182669240f1b2983670f461f9a` |
| `implementation.json` `tests/xcom/activation_plan/t020_support.hpp` | `2f46864d8f486c0ef15467ab29fef22b3c031cf1a65341550fbf1759fd92d657` | `0bae1f8178b2788fa1c8b6c4803a19dd6ec1b49a7e887f4c51bb7537a37b75da` |
| `implementation.json` `tests/xcom/activation_plan/t020_malformed_plan_tests.cpp` | `38e60e613fae4316f7536c7e774dc0046133d963b0b80ca566de36d50b9b5bef` | `75046040c1f06655ba34bee851f7044cd4f8cef8190a30ff5850775dbddbde22` |
| `implementation.json` `docs/engineering/xcom/t020/implementation.md` | `bd7eadd5a491ede1144b430695a3792bbe255ad2225c485ecf282777f627dcdb` | `5484618d1dde3fa2d9cdba090781c092f6dd01182669240f1b2983670f461f9a` |
| `documentation.json`, `integration.json`, `internal-review.json` `engineering/trace/links.json` | `5cf8b39c91af651fa664158be96617b65d1b6ad2a81391e40a9ae1910eb57e34` | `fa0dd2f757587de53066864ceaf64989a09fd3287aafa473de18a5bd1c105dd8` |

Only the digest strings above changed. Every recorded `relation`, `source`, `source_revision`, `target`, test
file, source file, and T011 engineering work product is byte-identical to the reviewed baseline; the inherited
T020 stage records keep their `role`, `status`, `inputs`, findings, assumptions, notes, and model identity.

Repair-local verification (offline, no network, no build):

| # | Command | Exit | Result |
| ---: | --- | ---: | --- |
| R-4 | `python3 /home/jefferson/x-verse_fabric/.fabro/workflows/xcom-t011-checkpoint-flash/audit_delivery_inputs.py` | 0 | `{"ok": true, "stage_results": 8}` — the unchanged core trace and stage validators accept every inherited T020 record. |
| R-5 | programmatic sweep of all `engineering/trace/links.json` `implemented_by` links and all `engineering/stage-results/*.json` artifact digests against `sha256sum` | 0 | Zero mismatches; the only rewritten digests are the nine rows above, each equal to the actual file hash. |
| R-6 | `git diff --check 5050666bf38fc98920dc455a85a88c08c46a2133 --`; `git diff --name-only 5050666bf38fc98920dc455a85a88c08c46a2133 --`; `git ls-files --others --exclude-standard` | 0 | Whitespace-clean; the baseline diff is the six T011 work products, `specs/007-xcom-core/tasks.md`, and the five inherited T020 provenance paths, with no `src/`, `tests/`, `xdl/`, or `proto/` path; the only untracked entries are `docs/engineering/xcom/t011/internal-review.json` and `reports/xcom-queue/t011-package.json` (both regenerated by the later review and package stages). |

The rev-2 candidate's evidence (`R-1`–`R-3`, §4.1) remains valid; this repair changes no requirement, check,
contract, boundary, gap, or REF-002 disposition, and the deterministic verification gate and the four shared
validators in §4.1 are re-run unchanged on this successor candidate.

## 4. Verification method and evidence

Environment for this record: Python 3.13.13 (`sys.version_info >= (3, 11)` holds); repository checkout at the
authorized baseline `5050666bf38fc98920dc455a85a88c08c46a2133`. No C++/CMake/CTest target is configured,
built, or run: T011 verification is the offline admission self-test plus read-only inspections and the shared
register validators.

### 4.1 Commands and observed results

| # | Command | Exit | Result |
| ---: | --- | ---: | --- |
| 1 | `git rev-parse 5050666bf38fc98920dc455a85a88c08c46a2133` | 0 | Prints `5050666bf38fc98920dc455a85a88c08c46a2133`; the baseline binding resolves (CHK-01/CHK-19). |
| 2 | `python3 scripts/xcom_dependency_preflight.py --self-test` | 0 | `Ran 39 tests ... OK`; every controlled positive and negative fixture passed (CHK-04…CHK-12, NEG-02..NEG-23). |
| 3 | `python3 scripts/validate_xcom_task_ownership.py --verify` | 0 | `X-COM task-ownership validation passed`; register re-validated unchanged (CHK-18). |
| 4 | `python3 scripts/validate_xcom_task_ownership.py --check-human` | 0 | `X-COM task-ownership validation passed`; the Markdown projection still matches the JSON model (CHK-18). |
| 5 | `python3 scripts/validate_xcom_requirements_traceability.py --verify` | 0 | `X-COM requirements/traceability validation passed`; T008 register/matrix intact (CHK-18). |
| 6 | `python3 scripts/validate_xcom_architecture_contracts.py --verify` | 0 | `X-COM architecture/contracts validation passed`; T009 model intact (CHK-18). |
| 7 | `python3 scripts/validate_xcom_unit_design.py --verify` | 0 | `X-COM unit-design validation passed`; T010 model intact, `XCOM-DU-029` still allocated (CHK-18). |
| 8 | `git diff --name-only 5050666bf38fc98920dc455a85a88c08c46a2133 --` (after staging) | 0 | Exactly the seven-path T011 candidate below; no `src/`, `tests/`, `xdl/`, or `proto/` path (CHK-15). |
| 9 | `git diff --check 5050666bf38fc98920dc455a85a88c08c46a2133 --` | 0 | Empty output; the candidate diff is whitespace-clean (CHK-19). |
| 10 | `grep -nE "^(import|from) " scripts/xcom_dependency_preflight.py` | 0 | Imports are `argparse, hashlib, json, os, re, shlex, shutil, stat, subprocess, sys, tempfile, unittest, collections.abc, dataclasses, enum, pathlib, unittest.mock`; **no** `socket`/`urllib`/`request`/`http`/`threading`/`Thread` (CHK-09, NEG-31, NEG-33). |
| 11 | `grep -n "FETCHCONTENT\|NO_PACKAGE_REGISTRY\|NO_SYSTEM_PACKAGE_REGISTRY" cmake/XComOfflineDependencies.cmake` | 0 | `CMAKE_FIND_PACKAGE_NO_PACKAGE_REGISTRY ON`, `CMAKE_FIND_PACKAGE_NO_SYSTEM_PACKAGE_REGISTRY ON`, `FETCHCONTENT_FULLY_DISCONNECTED ON` (CHK-06). |
| 12 | `grep -n "Ninja\|CMAKE_CXX_STANDARD\|BUILD_TESTING" CMakeLists.txt` | 0 | Ninja-only generator guard, `CMAKE_CXX_STANDARD 20`, `CMAKE_CXX_STANDARD_REQUIRED ON`, `BUILD_TESTING` required (CHK-02). |
| 13 | `grep -n "WARN_IF_UNDOCUMENTED\|WARN_NO_PARAMDOC\|WARN_AS_ERROR" Doxyfile` | 0 | `WARN_AS_ERROR = YES`, `WARN_IF_UNDOCUMENTED = NO`, `WARN_NO_PARAMDOC = NO`; the strict configuration remains gap `T011-GAP-01` (CHK-10, NEG-16). |
| 14 | `python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T011 5050666bf38fc98920dc455a85a88c08c46a2133` | 0 | `{"ok": true, "task_id": "T011", "changed_paths": 7, "checks": []}` — the deterministic gate accepts the staged candidate (T011-SR-012, CHK-16/CHK-17/CHK-19). |
| 15 | `git ls-files --others --exclude-standard` at the reviewed candidate | 0 | Exactly `docs/engineering/xcom/t011/internal-review.json`; `reports/xcom-queue/t011-package.json` is produced by the later package stage and is absent at review time. Both are excluded from `reviewed_paths`. |

The checker's document checks (`CHK-10`–`CHK-12`) are carried by the self-test itself, whose 39 cases include:

- `test_repository_documents_satisfy_independent_contracts` — "Accept each authoritative document without
  borrowing peer content": validates `dependency-lock.md` and `build-environment.md` through independent
  contracts;
- `test_empty_repository_documents_are_rejected_independently` — "One populated peer cannot mask an empty
  required document";
- `test_reject_removal_of_every_exact_lock_and_provenance_section` — the twelve package rows, generated-code
  provenance markers (`input schema identity`, `generation command`, the `protobuf-compiler` and
  `protobuf-compiler-grpc` filenames/hashes, and the `grpc_cpp_plugin` no-version-flag statement), and the
  archive-versus-payload section markers are all required;
- `test_reject_removal_of_every_environment_failure_and_trace_section` — the two explicit inputs, host
  envelope, offline reconstruction (`dpkg-deb -x`, no APT), ABI limits, classified failure semantics,
  `XCOM-BLD-001`–`005`, and the five `VM-BLD-*` measures are all required;
- `test_reject_package_provenance_reconstruction_abi_and_variable_drift` — an admitted package identity,
  reconstruction, ABI, or explicit-input-variable change is rejected.

Together these are the task's **document, dependency, license, provenance, and offline-strategy checks**:
`dependency-lock.md` carries the twelve exact package records with Debian package/version/source and primary
license and their public retrieval coordinates; `build-environment.md` carries the explicit inputs, the
extraction-only reconstruction, the environment/ABI limits, the classified decision semantics, and the
`VM-BLD-*` evidence contract.

### 4.2 Admitted-environment source inspections (read-only)

| # | Inspection | Observed |
| ---: | --- | --- |
| 16 | `docs/engineering/xcom/dependency-lock.md` §"Exact Jammy package records and retrieval coordinates" | Exactly twelve rows: nlohmann/json 3.10.5 (MIT), Protocol Buffers 3.12.4 (BSD-3-Clause), gRPC 1.30.2 (Apache-2.0), clang-tidy/LLVM 14.0.0 (Apache-2.0 WITH LLVM-exception; GPL-2.0-or-later metapackage), each with bytes, SHA-256, source package, and pool coordinate (CHK-04). |
| 17 | `docs/engineering/xcom/dependency-lock.md` §"Admitted component and generated-code provenance" | `protobuf-compiler_3.12.4-1ubuntu7.22.04.6_amd64.deb` / `a124cc30…b61ce7` and `protobuf-compiler-grpc_1.30.2-3build6_amd64.deb` / `79debaed…05331` recorded with the input-schema/generation-command requirement; `grpc_cpp_plugin` has no supported version flag (CHK-07). |
| 18 | `docs/engineering/xcom/dependency-lock.md` §"Archive identity versus extracted payload identity" | Archive identity and prefix payload identity are distinct; `dpkg-deb -f` control metadata plus `dpkg-deb -x` node-by-node comparison (file type, content, symlink text, reached target); no archive-only admission (CHK-05, NEG-29). |
| 19 | `docs/engineering/xcom/build-environment.md` §"Deterministic offline prefix reconstruction" | Extraction-only (`dpkg-deb -x`), ordered, no APT/maintainer scripts/network, stale-prefix discard (CHK-11). |
| 20 | `docs/engineering/xcom/build-environment.md` §"Repository-owned host verification evidence" | Five measures `VM-BLD-UNIT/LINT/STATIC/INTEGRATION/VALIDATION`, network-disabled isolation, per-measure `command_argv`/`exit_code`/`outcome`, bounded log and private raw manifest with hashes, repository `index.json` (CHK-12). |
| 21 | `cmake/XComOfflineDependencies.cmake` | Both explicit inputs required and normalized; `--cmake-dependency-check` invoked (120 s timeout); registries and FetchContent disabled; imported targets resolved beneath the admitted prefix (CHK-06). |
| 22 | `CMakeLists.txt` | Ninja-only, C++20 without extensions, `BUILD_TESTING=ON`, `xverse_xcom_policy_probe`, `xverse_xcom_warning_rejection_probe` (`EXCLUDE_FROM_ALL`, must fail), `xcom-build-policy.json` evidence (CHK-02, CHK-03). |
| 23 | `cmake/XComWarnings.cmake` | `xverse::xcom_warnings` interface target carries the warning option list and rejects negating/suppressing forwarded options (CHK-02). |

### 4.3 Negative-case coverage

`NEG-02..NEG-23` are exercised by the checker's controlled fixtures in command 2 (the "policy", "package",
"payload", "document", and "temporary/IO" families: wrong lock count/duplicate names, shape/field/digest/size
defects, missing/mismatched archives, payload type/link/content drift, missing prefix artifacts, missing
inputs, read/permission/UTF-8 failures, extraction failures, warning-as-error rejection, and policy-evidence
drift). `NEG-01`, `NEG-24..NEG-30` and `NEG-31..NEG-33` are documentation/governance and source inspections
commands 9–13 and the register validators in §4.1. No negative case returns a pass or reports `admitted`.

### 4.4 Artifact identity at this candidate state

| Artifact | SHA-256 | Bytes |
| --- | --- | ---: |
| `docs/engineering/xcom/t011/requirements.md` | `9e2d8da09f7f289991b338af5a9e6b0f7cbd5337efc574f34b1240a9873184d0` | 27808 |
| `docs/engineering/xcom/t011/architecture.md` | `d30a122e383af06ed7489363bfa03a1073c478eee60f9acede49638a4cceb52d` | 15354 |
| `docs/engineering/xcom/t011/detailed-design.md` | `ad021bb8d85d5aa2d7ace14d7ff0f8875f8427df76b18e2c6e99873214cfd7f5` | 15015 |
| `docs/engineering/xcom/t011/unit-specifications.md` | `e3d236b7988c33cea29fae1687ec811036b82735912ad42587cf0de751309b29` | 16665 |
| `docs/engineering/xcom/t011/verification-plan.md` | `01c0f9607d3c50453b40beb061bbc62b3c5828ec4b7d44d84d07fbffd4ebf290` | 13646 |
| `specs/007-xcom-core/tasks.md` | `59f95a5cbb3ba875c3619e7545995655c60a3033d4d2f82db7f723bf65919a36` | — |

`docs/engineering/xcom/t011/implementation.md` and `reports/xcom-queue/t011-package.json` are bound by the
package record (the package action recomputes every changed path's SHA-256 after the deterministic gate and
review pass). The admitted-foundation artifacts listed in §3.1 `D-02` are unchanged and their baseline hashes
are not re-declared here. A successor candidate (a repair or a later authorized slice) must record its own
exact revision and repeat every affected check.

## 5. Requirement-to-evidence traceability

| Requirement | Primary check(s) | Evidence |
| --- | --- | --- |
| T011-STK-001 | CHK-01, CHK-11, CHK-16 | cmd 1, 19, 14 |
| T011-STK-002 | CHK-04, CHK-05, NEG-04..NEG-10 | cmd 16, 18, 2 |
| T011-STK-003 | CHK-07, NEG-16 | cmd 17, 13 |
| T011-STK-004 | CHK-08, NEG-11..NEG-30 | cmd 2, 9–13 |
| T011-STK-005 | CHK-13, CHK-14 | §6; public-safety scan of the work products and the two T-INTG documents |
| T011-SR-001 | CHK-02, CHK-03, NEG-01..NEG-03 | cmd 12, 22, 23, 2 |
| T011-SR-002 | CHK-04, NEG-04..NEG-06 | cmd 16, 2 |
| T011-SR-003 | CHK-05, NEG-07, NEG-08, NEG-17 | cmd 18, 2 |
| T011-SR-004 | CHK-06, CHK-11, NEG-09, NEG-10 | cmd 11, 19, 2 |
| T011-SR-005 | CHK-07, NEG-16 | cmd 17, 13 |
| T011-SR-006 | CHK-03, CHK-07 | cmd 22, 17; sanitizer execution is T035's (gap `T011-GAP-03`) |
| T011-SR-007 | CHK-08, NEG-11..NEG-30 | cmd 2, 9–13 |
| T011-SR-008 | CHK-09, NEG-31..NEG-33 | cmd 10, 11 |
| T011-SR-009 | CHK-10, CHK-13, CHK-14 | cmd 2, 16–20; §6 |
| T011-SR-010 | CHK-12 | cmd 20 (contract only; execution is T035–T038) |
| T011-SR-011 | CHK-15, CHK-16 | cmd 8, 14; §3.1 `D-01`/`D-02` |
| T011-SR-012 | CHK-16, CHK-17, CHK-19 | cmd 8, 9, 14, 15 |
| T011-SR-013 | CHK-18, CHK-19 | cmd 3–7, 14; REF-002 unchanged (no promotion) |

## 6. Public safety

The T011 work products contain repository-relative paths, package filenames, versions, licenses, SHA-256
values, public retrieval coordinates, diagnostic codes, and pass/fail outcomes only. They contain no
credential, private address, unrestricted payload, proprietary source excerpt, or sensitive deployment
value; `D-01`/§4 use the repository-relative `docs/engineering/xcom/t011/` form and the checker's own
diagnostic vocabulary, and no host prefix, package manifest, temporary extraction, or private-store absolute
path is recorded. The single non-repository absolute path is the workflow's own deterministic-gate automation
invocation in command 14 and `verification-plan.md` §2
(`/home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py`), retained exactly as in the accepted T009
and T010 records; it is the workflow tool path, not a sensitive deployment value. `CHK-13` and `CHK-14` are
satisfied by inspection on that reading.

## 7. Limitations, gaps, and maturity

Recorded from the requirements package and **not** resolved by T011:

- `LIM-01` — transitive host libraries are not locked; the envelope is limited to Linux x86-64 on an
  ABI-compatible Jammy-derived host. `LIM-02` — the imported targets are compile-only top-level locators, not a
  hermetic runtime link. `LIM-03` — T011 admits the sanitizer/static/Doxygen toolchain **contract**; the
  executed evidence is T035–T037's.
- `T011-GAP-01` — strict Doxygen C++ configuration not admitted (`WARN_IF_UNDOCUMENTED`/`WARN_NO_PARAMDOC` are
  `NO`); owner T011 (admission)/T037 (execution), allocated.
- `T011-GAP-02` — generated protobuf/gRPC C++ documentation/provenance policy admitted but no generated C++
  exists yet; owner T011 (policy)/T030–T032 (source), allocated.
- `T011-GAP-03` — sanitizer opt-in flags not yet wired for runtime targets; owner T012/T035, allocated.
- `T011-GAP-04` — the admitted foundation was produced under the earlier `specs/008`–`011` work and is not yet
  user-accepted under capability 007; owner T039/T041, allocated.

Maturity: engineering-baseline work product, **prototype-only**, locally verified, exposing **no X-COM runtime
behavior, no compatibility, and no production-readiness**. It is not user-accepted (T041) and not externally
reviewed (Codex review deferred until this ordered backlog completes). No REF-002 target requirement is
promoted to implemented; the T008 disposition stays `unchanged` with an empty `promoted` set.

## 8. Definition-of-done status (requirements view)

- (a) The six named work products exist under `docs/engineering/xcom/t011/` and are mutually consistent. ✔
- (b) Every requirement in `requirements.md` §3–§4 maps to ≥ 1 named check in `verification-plan.md`. ✔
- (c) The machine checks pass at the candidate revision: the deterministic gate, the offline admission
  self-test, and the four register validators (commands 2–14). ✔
- (d) The gap register is complete and no gap is silently closed (§7; `D-02`). ✔
- (e) The T011 checkbox is marked complete and the package record is written by the package action. ✔
- (f) A separate DeepSeek internal review records a passing verdict with no findings
  (`docs/engineering/xcom/t011/internal-review.json`). ◐ — internal review rev 1 returned `fail` with findings
  `T011-IR-01`/`T011-IR-02`; both are closed by the §3.2 repair of `unit-specifications.md`. The passing verdict
  must be recorded by a fresh read-only review of this successor candidate (rev 2) and is not self-declared here.

This does **not** constitute external review or user acceptance, which remain deferred to the backlog and to
T041 respectively.
