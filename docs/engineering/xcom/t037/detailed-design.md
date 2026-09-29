# T037 Detailed Design — Complete Doxygen Comments and Warning-Free Generated Reference Documentation

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T037 (capability 007, slice `T-INTG`/documentation) |
| Stage / role | plan → detailed design |
| Revision | 1 (Phase 8 Doxygen-completion slice) |
| Baseline revision | `8757a79d4e6b2630124d774fcba2a55d6342a879` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Classification | Public-safe engineering work product |

T037 completes the Doxygen documentation of the owned C/C++ public interface at one exact candidate revision
and generates the reference warning-free. The design is written **before** execution; the implementation
must realize it exactly or record a design change and re-review.

## 2. Design decisions

| ID | Decision | Rationale | Requirement |
| --- | --- | --- | --- |
| `T037-DD-01` | T037 edits owned C++ inputs for **Doxygen comments only**; no compiled token, signature, type, default, control-flow decision, contract, or expected value changes | Documentation must not invalidate the verified object | T037-SR-006 |
| `T037-DD-02` | Every owned public declaration carries `@brief` plus the applicable `@param`/`@return`/`@retval` and the applicable ownership/lifetime/thread-safety/failure clauses; every owned C++ file carries the mandatory file block (`@file`, `@brief`, `@ingroup`) | Implements the T010 `doxygen_plan` coverage rule and the `XCOM-DU-022` obligation | T037-SR-001 |
| `T037-DD-03` | `Doxyfile` defines every command used by the admitted inputs (notably the `bounds` alias) so the repository-wide route is warning-free under `WARN_AS_ERROR = YES` | The accepted inputs use `@bounds`, which has no alias today; the repository route must not abort | T037-SR-003 |
| `T037-DD-04` | The strict declaration-level coverage is exercised by a **C++-scoped** configuration: `INPUT = src/xverse/xcom`, `EXTRACT_ALL = NO`, `EXTRACT_PRIVATE = NO`, `EXTRACT_STATIC = NO`, `WARN_IF_UNDOCUMENTED = YES`, `WARN_NO_PARAMDOC = YES`, `WARN_AS_ERROR = YES`, with the admitted exclusion list | Ledger `DOX-GAP-01`/`DOX-GAP-03` target "the owned C++ inputs"; the repository route also covers out-of-scope Python/test inputs | T037-SR-002 |
| `T037-DD-05` | `scripts/check_doxygen.py` gains a strict C++ mode and fails closed on an undocumented declaration, a missing mandatory tag, or any warning | A single auditable, deterministic documentation gate | T037-SR-010 |
| `T037-DD-06` | The report carries `command`, `warnings`, `output`, environment, hashes, and the exact-candidate identity | Implements the repository-owned evidence contract and the Phase 8 gate's required `T037` fields | T037-SR-005 |
| `T037-DD-07` | The public report records tool identities and hashes, not host-specific absolute prefix, manifest, temporary, or evidence-store paths | Public-safety rule and reviewer expectation | T037-SR-007 |
| `T037-DD-08` | A check whose admitted input or executable is unavailable is recorded `blocked` with its reason; no inferred or stale output is substituted | Honest outcome rule | T037-OPEN-04 |
| `T037-DD-09` | T037 links `implemented_by` to its documented owned C++ surface and to `Doxyfile`/`scripts/check_doxygen.py`, and refreshes every edited-artifact pin (and the inherited `engineering/project.json` pins) at implementation | T037's realized artifacts are documentation comments and the Doxygen route | T037-SR-009, T037-OPEN-03 |
| `T037-DD-10` | T037 does not run, duplicate, or claim the T035 matrix, the T036 benchmark, or the T038/T039/T040/T041 deliverables; the inherited Python docstring findings are preserved as a limitation | Scope and maturity separation | T037-SR-009, T037-OPEN-06 |

## 3. Documentation route (exact commands)

The route below is the repository-owned documentation completion. `${XVERSE_FABRIC_ROOT}` and the admitted
inputs are resolved by the trusted policy; the admitted inputs are `XVERSE_XCOM_TOOLCHAIN`,
`XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN`. The implementation records the exact
resolved argv, exit status, and observed warnings.

| # | Purpose | Command (portable descriptor) | Expected |
| --- | --- | --- | --- |
| B-1 | repository-wide warning-free generation | `doxygen Doxyfile` (with `WARN_AS_ERROR = YES`) | exit `0`; no warning in the warning log; HTML and XML indexes generated |
| B-2 | strict C++ coverage and zero-warning generation | `python3 scripts/check_doxygen.py --strict-cpp` | exit `0`; zero warnings and zero coverage gaps over the owned C++ inputs |
| B-3 | checker self-test | `python3 scripts/check_doxygen.py --self-test --coverage-only` | exit `0`; the coverage gate rejects the synthetic undocumented symbol |
| B-4 | write the evidence report | `python3 scripts/check_doxygen.py --report reports/xcom-queue/t037-doxygen.json` | exit `0`; the report carries the required fields and the exact-candidate identity |
| B-5 | trusted full-suite regression context | `python3 ${XVERSE_FABRIC_ROOT}/automation/run_xcom_phase8_tests.py unit` | `100% tests passed` |

The trusted Phase 8 `validation` measure for T037 reads `Doxyfile`, appends
`OUTPUT_DIRECTORY = <build>/doxygen`, `WARN_AS_ERROR = YES`, and `QUIET = YES`, and runs `doxygen` with a
nonzero-exit-on-warning contract (see `run_xcom_phase8_tests.py`, `mode == "validation" and task == "T037"`).
B-1/B-2 are therefore the same warning-free obligation the trusted route enforces; B-4 produces the report
the deterministic `verify` gate requires; B-5 preserves the accepted suite.

## 4. Evidence report schema (`reports/xcom-queue/t037-doxygen.json`)

```json
{
  "schema_version": 1,
  "task_id": "T037",
  "capability": "007",
  "baseline_revision": "<40-hex accepted baseline>",
  "candidate_revision": null,
  "candidate_identity": {
    "material_digest": "<sha256>", "material_inputs": ["<relative path>", "..."],
    "revision_binding": "<baseline plus material-digest/hash binding rule>",
    "generated_at": "<iso-8601>"
  },
  "command": {
    "repository_route": "doxygen Doxyfile",
    "strict_cpp_route": "python3 scripts/check_doxygen.py --strict-cpp",
    "resolved_argv": ["doxygen", "Doxyfile"]
  },
  "warnings": {"count": "<int>", "log": "<bounded public-safe warning text, empty when zero>"},
  "output": {
    "repository_exit_code": "<int>",
    "strict_cpp_exit_code": "<int>",
    "indexed_files": "<int>",
    "html_index": "build/doxygen/html/index.html",
    "xml_index": "build/doxygen/xml/index.xml",
    "bounded_stdout": "<public-safe, size-bounded excerpt>"
  },
  "environment": {
    "doxygen": "<version>", "compiler": "<identity>", "cxx_standard": "c++20",
    "cmake": "<version>", "ninja": "<version>", "python": "<version>", "target": "linux-x86_64",
    "admitted_inputs": {
      "XVERSE_XCOM_TOOLCHAIN": {"kind": "directory", "sha256": "<sha256>", "files": "<int>"},
      "XVERSE_XCOM_PACKAGE_MANIFEST": {"kind": "file", "sha256": "<sha256>", "files": 1},
      "XVERSE_XCOM_T025_TEST_TOOLCHAIN": {"kind": "directory", "sha256": "<sha256>", "files": "<int>"}
    }
  },
  "strict_cpp": {
    "scope": "src/xverse/xcom", "exclusions": ["<admitted exclusion pattern>", "..."],
    "extract_all": false, "extract_private": false, "extract_static": false,
    "warn_if_undocumented": true, "warn_no_paramdoc": true,
    "warning_count": "<int>", "coverage_gap_count": "<int>"
  },
  "hashes": {"<artifact path>": "<sha256>"},
  "limitations": ["documentation-only prototype evidence; not a production-readiness claim", "..."],
  "blockers": []
}
```

- `command`, `warnings`, and `output` are the Phase 8-gate-required fields; `strict_cpp` and `environment`
  are the repository-owned evidence-contract fields.
- `warnings.count` is `0` and `warnings.log` is empty for a passing candidate; a nonzero count or a
  non-empty log yields a failed outcome and a nonzero checker exit.
- `hashes` records SHA-256 of the retained evidence and the referenced T037 artifacts; it never records a
  host-specific absolute path.
- `environment` records identities and admitted-input digests by name, not host paths.
- `candidate_revision` is `null`: a committed report cannot contain the hash of the commit that contains it.
  The exact candidate is bound by `baseline_revision` plus the `candidate_identity.material_inputs`
  inventory, `material_digest`, and per-file `hashes`.

## 5. Comment obligations (owned C++ surface)

The plan-stage strict probe isolated the following public-surface gaps. The implementation completes these
and re-checks the whole owned surface so no gap remains.

| Input | Observed strict-C++ gap (plan probe) | Obligation |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/activation_plan.hpp` | 86 undocumented plan-struct members | document every public struct member with `@brief`; group under `xcom_xdl` |
| `src/xverse/xcom/include/xverse/xcom/tool_gateway.hpp` | 20 missing `@param`/`@return` on session methods | document every parameter and return value; group under `xcom_gw` |
| `src/xverse/xcom/include/xverse/xcom/stimulation_actions.hpp` | 2 (`journal_and_emit` `lock` parameter; one other) | document the `lock` parameter and re-check the file |
| `src/xverse/xcom/include/xverse/xcom/validation_session.hpp` | 2 | document the flagged declarations |
| `src/xverse/xcom/fixtures/synthetic_tool.cpp` | 1 | document the flagged declaration |
| every other owned header/source/fixture | 0 at the plan probe | add the mandatory file block and contract clauses where missing; keep at zero gaps |

The mandatory public tags are `brief`, `ownership`, `lifetime`, `thread_safety`, and `failure`; the
conditional tags are `param`, `return`, `retval`, `note`, `pre`, and `post` (T010 `doxygen_plan`). The groups
are `xcom_core`, `xcom_xdl`, `xcom_obs`, `xcom_stim`, `xcom_gw`, `xcom_intg`, and `xcom_enb`.

## 6. Failure semantics

| Condition | Outcome |
| --- | --- |
| an owned public declaration is undocumented or a mandatory tag is absent | the strict checker exits nonzero; the report records `strict_cpp.coverage_gap_count > 0` |
| the repository route or the strict route emits a warning | the route exits nonzero; the report records `warnings.count > 0` and does not claim pass |
| the generated HTML/XML index is absent | the checker exits nonzero |
| an admitted input or the Doxygen executable is unavailable | the check is `blocked` with its reason; the candidate does not claim a pass (`T037-DD-08`) |
| a committed artifact or excerpt would contain private content | the content is redacted/omitted before commit (`T037-SR-007`) |
| a compiled token, signature, type, default, or expected value would change | the change is rejected; `T037-DD-01` fails closed |

## 7. Determinism and safety

- The input set, exclusion list, warning treatment, and generated-output locations are fixed and recorded;
  no T037 verdict depends on ambient wall-clock time beyond the recorded generation time.
- Documentation tooling is single-threaded.
- No T037 command opens a network listener or socket, resolves a name, or contacts a legacy or external
  resource; no dependency is added.
- Committed files and excerpts contain no credential, private address, real or proprietary payload, or
  host-specific absolute path.

## 8. Public-safety and information classification

- Only tool identities, admitted-input digests, the command, the warning count, bounded public-safe output,
  and hashes are committed.
- Host-specific absolute prefix, manifest, temporary, and evidence-store paths are excluded from the report;
  the raw generation logs, if retained, live outside the public report.
- No payload byte, permit content, credential, private address, or proprietary source excerpt enters a
  committed artifact.

## 9. Traceability and digest refresh

| Design element | Requirement | Checks |
| --- | --- | --- |
| `T037-DD-02`/`-03` complete comments and aliases | T037-SR-001, T037-SR-003 | CHK-01, CHK-03 |
| `T037-DD-04`/`-05` strict C++ scope and fail-closed checker | T037-SR-002, T037-SR-010 | CHK-02, CHK-08 |
| `T037-DD-06`/`-07` report fields and public safety | T037-SR-005, T037-SR-007 | CHK-05, CHK-06 |
| `T037-DD-08` unavailable-input honesty | T037-SR-005 | CHK-05, CHK-09 |
| `T037-DD-09`/`-10` evidence trace and unchanged scope | T037-SR-006, T037-SR-009 | CHK-10, CHK-11 |

**Digest refresh obligation (`T037-OPEN-03`).** Because T037 edits the owned C++ inputs, `Doxyfile`, and
`scripts/check_doxygen.py`, the implementation stage **must** recompute the `implemented_by` `target_revision`
pins for every edited artifact in `engineering/trace/links.json` (and the inherited `engineering/project.json`
pins) so no stale hash remains. The plan-stage records pin plan-time hashes and are refreshed at
implementation.

## 10. Doxygen and documentation

T037 is the documentation task; its Doxygen obligation is the task itself. The generated HTML/XML reference
is deliberately not versioned (it lives under `build/`), so the versioned evidence is the report, the
configuration, and the source comments. The T037 work-product set documents the route, the report schema,
and the coverage rule.

## 11. Compatibility contract and generated-code provenance

- T037 adds **no** generated code and **no** admitted dependency. It does not touch
  `proto/xverse/xcom/v1/tool_gateway.proto` or any `XCOM-XLC-002` message and links no transport runtime.
- **Generated-code provenance (`DOX-GAP-02`).** Generated protobuf C++ and system/third-party headers remain
  out of the owned documentation scope and are handled by the admitted exclusion list; T037 documents only
  the owned hand-written public surface.
- **Compatibility contract.** T037 defines no competing interface, contract, or configuration language; it
  documents the accepted one and promotes no REF-002 target.
