# T037 Architecture — Complete Doxygen Comments and Warning-Free Generated Reference Documentation

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T037 (capability 007, slice `T-INTG`/documentation) |
| Stage / role | plan → architecture |
| Revision | 1 (Phase 8 Doxygen-completion slice) |
| Baseline revision | `8757a79d4e6b2630124d774fcba2a55d6342a879` |
| Affected paths | `docs/engineering/xcom/t037/**`, `Doxyfile`, `scripts/check_doxygen.py`, `src/xverse/xcom/**` (Doxygen comments only), `engineering/requirements/T037-*.json`, `engineering/architecture/components/T037-*.json`, `engineering/unit-specifications/T037-*.json`, `engineering/validation/scenarios/T037-VS-ACCUMULATED.json`, `engineering/trace/links.json`, `engineering/project.json`, `reports/review-index.md`, `reports/xcom-queue/t037-doxygen.json` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed architecture | `docs/engineering/xcom/t009/architecture-model.json`; `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-022`, doxygen_plan `DOX-GAP-01`/`DOX-GAP-03`); `docs/engineering/xcom/t008/requirements-register.json` (`XCOM-SW-INTG-002`, `XCOM-SW-ENB-004`, `XCOM-SW-CORE-007`, `XCOM-SW-INTG-001`, `XCOM-SW-ENB-001/002`); `docs/engineering/xcom/t011/{build-environment,dependency-lock}.md`; `Doxyfile`; `scripts/check_doxygen.py`; `specs/007-xcom-core/spec.md` FR-029/SC-009; ADR-0020; Constitution VI, IX, X |
| Classification | Public-safe engineering work product |

## 2. Purpose and position in the delivery graph

T037 is the **documentation-completion** task of the capability-007 `T-INTG` evidence family. T035 executed
the complete verification matrix; T036 measured the observation tap's disabled/enabled overhead. T037
completes the Doxygen documentation of the owned C/C++ public interface, configures a strict, warning-free
C++ reference route, and retains the result as repository-owned evidence. T038 owns the traceability
verifier/SADS disposition; T039–T041 own review and acceptance.

```text
T007 ownership → T008 requirements → T009 architecture → T010 unit design (Doxygen plan) → T011 admission
   → T012 subtree build/test contract → T013–T016 core + matrix (documented)
   → T017–T020 XDL activation plan (documented)
   → T021–T024 observation boundary (documented)
   → T025–T029 stimulation boundary (documented)
   → T030 contract → T031 gateway → T032 client → T033 suites → T034 second provider (documented)
   → T035 exact-candidate verification matrix + results (read-only)
   → T036 controlled disabled/enabled-tap benchmark + repository-owned results (read-only)
   → T037 complete Doxygen comments + warning-free generated reference (this slice)
   → T038 traceability/SADS → T039/T040 review → T041 acceptance
```

T037 edits the owned C++ sources, headers, and fixtures for **Doxygen comments only**, the Doxygen
configuration, and the documentation checker; it adds one evidence report, one work-product set, one
engineering record set, and additive trace links. It changes no compiled behavior, signature, type, default,
test, target, label, command, or expected value.

## 3. Boundary and context

### 3.1 System context

```text
   ┌────────────── accepted capability-007 anchors (read-only) ──────────────┐
   │  SC-009 · FR-026/027/028/029/030/035 · plan Doxygen-warning-as-error step │
   │  t008 XCOM-SW-INTG-002, XCOM-SW-ENB-004, XCOM-SW-CORE-007,                │
   │       XCOM-SW-INTG-001, XCOM-SW-ENB-001/002                              │
   │  t009 XCOM-CMP-* · t010 XCOM-DU-022 · doxygen_plan DOX-GAP-01/03          │
   │  build-environment.md / dependency-lock.md; T011 admitted Doxygen 1.9.1  │
   └──────────────────────────────────┬──────────────────────────────────────┘
                                      │ documents
   ┌──────── owned C/C++ public surface (read-only semantics, comment-only) ──┐
   │  src/xverse/xcom/include/xverse/xcom/*.hpp                              │
   │  src/xverse/xcom/src/*.cpp   ·   src/xverse/xcom/fixtures/*              │
   └──────────────────────────────────┬──────────────────────────────────────┘
                                      │ consumed by
   ┌────────────── T037 owned artifacts (this slice) ─────────────────────────┐
   │  Doxyfile (aliases, scope, exclusions)                                   │
   │  scripts/check_doxygen.py (strict C++ mode; fail-closed)                  │
   │  reports/xcom-queue/t037-doxygen.json                                    │
   │      command · warnings · output · environment · hashes · candidate id    │
   │  engineering/trace/links.json (additive T037 links)                      │
   │  docs/engineering/xcom/t037/** work products                             │
   │  guarantee : complete owned public documentation, strict zero-warning     │
   │      C++ reference, warning-free repository route, exact-candidate        │
   │      binding, public-safe bounded evidence, no compiled-behavior change   │
   └──────────────────────────────────┬───────────────────────────────────────┘
                                      ▼
                           T038–T041 traceability/review/acceptance
```

### 3.2 Trust boundaries

| Boundary | Inside | Outside | Rule |
| --- | --- | --- | --- |
| `T37-XB-1` Documentation vs compiled behavior | Doxygen comments, file blocks, and comments group membership | any compiled statement, signature, type, default, control-flow decision, or expected value | T037 adds no compiled change; `git diff` over the owned sources is Doxygen-comment-only (`T037-SR-006`). |
| `T37-XB-2` Repository route vs strict C++ scope | the repository-wide `doxygen Doxyfile` route the trusted validation measure runs, and the strict C++-scoped configuration over the owned inputs | out-of-scope Python/test inputs that cannot be forced to declaration-level strictness without out-of-scope edits | The repository route stays warning-free; the strict declaration-level coverage is scoped to the owned C++ inputs (`T037-SR-002`, `T037-SR-003`, `T037-GAP-02`). |
| `T37-XB-3` Generated output vs versioned artifacts | the HTML/XML reference under `build/` and bounded public-safe excerpts | any committed generated tree, host-specific path, or private log | Generated output is not versioned; only identities, hashes, and bounded excerpts are retained (`T037-SR-004`, `T037-SR-007`). |
| `T37-XB-4` Exact candidate vs stale evidence | the report bound to the candidate revision and artifact hashes | a report generated from another revision, run, or host | Stale or foreign results fail the task-owned checker (`T037-SR-005`, `T037-SR-010`). |
| `T37-XB-5` Public summary vs host data | tool identities, hashes, the command, the warning count, and bounded output | host-specific absolute paths, credentials, payload bytes, proprietary excerpts | The committed report contains none of the excluded content (`T037-SR-007`). |
| `T37-XB-6` Offline/local vs external resources | admitted offline toolchain and the owned sources | any TCP listener, `AF_INET`/`AF_INET6` socket, DNS, resolver, TLS, external peer, legacy binary, or production workload | No T037 command contacts a network or legacy resource; no dependency is added (`T037-SR-008`). |
| `T37-XB-7` T037 scope vs successor scope | the documentation completion and its evidence | the T038 traceability/SADS, T039–T041 review/acceptance deliverables | T037 neither duplicates nor claims a successor deliverable (`T037-GAP-04`). |

### 3.3 Prohibited elements (must remain absent)

No compiled-behavior, signature, type, default, contract, schema, register, XDL profile, accepted test,
target, label, command, or expected-value change; no new admitted dependency, runtime library, or compiled
symbol; no compiled or linked gRPC runtime; no TCP listener or `AF_INET`/`AF_INET6` socket, DNS, resolver,
or TLS use; no external network peer; no legacy binary, legacy repository, or production workload; no
committed generated HTML/XML tree; no traceability-verifier, review, or acceptance artifact; no payload,
permit, secret, private address, or host path in a committed file or log; no production-readiness claim; no
rewrite or weakening of an accepted ADR, requirement, contract, schema, register, or test; no REF-002
promotion; no acceptance or integration of the candidate.

## 4. Components

`T37-*` names are local to this document; the accepted `XCOM-DU-022` identifier is the authorized design
unit. The T037 requirement components are `T037-SR-###-CMP` (one per requirement) and the units
`T037-SR-###-U`.

### 4.1 T037 components

- **`T37-CMP-SOURCE`** (owned `src/xverse/xcom` C++ inputs): the file-block and declaration-level Doxygen
  comments, including the ownership/lifetime/thread-safety/failure contract clauses, with no compiled change.
- **`T37-CMP-CONFIG`** (`Doxyfile`): the repository Doxygen configuration, the alias definitions (including
  `bounds`), and the admitted exclusion list; the C++-scoped strictness is derived from it by the checker.
- **`T37-CMP-CHECKER`** (`scripts/check_doxygen.py`): the documentation coverage/HTML checker extended with a
  strict C++ mode that fails closed on an undocumented declaration, a missing mandatory tag, or a warning.
- **`T37-CMP-REPORT`** (`reports/xcom-queue/t037-doxygen.json`): the Doxygen evidence carrying `command`,
  `warnings`, `output`, the environment identity, hashes, and the exact-candidate identity.
- **`T37-CMP-TRACE`** (`engineering/trace/links.json`, `engineering/project.json`): additive T037
  requirement/component/unit/measure/config/code/validation links and the current-task pointer.
- **`T37-CMP-WP`**: the T037 repository-owned work-product set and the T037 package record.

### 4.2 Consumed components (read-only)

- **`T37-CMP-T013…T034`** — accepted core value types, diagnostics, endpoint/route lifecycle, provider
  boundary/composition, owned loopback provider, XDL activation plan, observation boundary, stimulation
  boundary, contract, gateway, client, suites, and second provider. Documented; no compiled change.
- **`T37-CMP-T011`/`T012`** — the admitted offline envelope, Doxygen 1.9.1, the coverage checker, and the
  subtree build/test contract. Consumed; no rule is weakened and no dependency is added.
- **`T37-CMP-T035`/`T036`** — the accepted verification matrix and benchmark. Consumed read-only; not
  re-run, re-claimed, or re-documented as if new.

## 5. Data flow (ordered)

1. **Admission.** The admitted offline toolchain and the Doxygen executable identity are resolved; no
   network access is used.
2. **Comment.** The owned C++ sources carry the complete file-block and declaration-level comments
   (implementation stage); no compiled token changes.
3. **Configure.** `Doxyfile` defines every command used by the admitted inputs and the owned-C++
   strictness/exclusions.
4. **Check.** The checker runs the repository-wide route warning-free and the strict C++-scoped configuration
   to zero warnings and zero coverage gaps.
5. **Generate.** The HTML/XML reference is generated warning-free under `build/`; no generated tree is
   committed.
6. **Record.** `reports/xcom-queue/t037-doxygen.json` is written with `command`, `warnings`, `output`, the
   environment identity, hashes, and the exact-candidate identity; no host path, credential, payload, or
   proprietary excerpt is committed.
7. **Bind the trace.** Additive T037 links connect each requirement to its component, unit, measure,
   configuration/code artifacts, and validated scenario, and the edited-artifact digests are refreshed.

## 6. Interfaces

### 6.1 Task-owned documentation checker (`scripts/check_doxygen.py`)

| Invocation | Contract |
| --- | --- |
| `python3 scripts/check_doxygen.py --coverage-only` | check Python and owned-C++ documentation coverage without invoking Doxygen; exit `0` only when the selected scope is complete (the inherited Python findings remain reported, not hidden) |
| `python3 scripts/check_doxygen.py --strict-cpp` | run the strict C++-scoped configuration over the owned C++ inputs and exit `0` only when it emits zero warnings and zero coverage gaps |
| `python3 scripts/check_doxygen.py` | run the repository-wide coverage check and warning-free generation; exit `0` only when both the coverage and the generation pass |
| `python3 scripts/check_doxygen.py --self-test --coverage-only` | prove the coverage gate rejects a synthetic undocumented symbol |

The checker is deterministic: the input set, exclusion list, and warning treatment are fixed for the exact
candidate revision. It does not depend on ambient wall-clock time for its verdict.

### 6.2 Doxygen configuration (`Doxyfile`)

| Field | Contract |
| --- | --- |
| `INPUT` | the admitted repository inputs (`docs/doxygen/mainpage.md`, `docs/xcom/*.md`, `src/xverse/xcom`, `src/xverse_xdl`, `scripts`, `tests`) |
| `ALIASES` | the contract aliases (`ownership`, `lifetime`, `thread_safety`, `failure`, `unitspec`) plus every other command used by the admitted inputs (including `bounds`) so that no unknown command is emitted |
| `WARN_AS_ERROR` | `YES`: a warning fails the generation |
| `WARN_IF_UNDOCUMENTED` / `WARN_NO_PARAMDOC` | `NO` for the repository-wide route (out-of-scope Python/test inputs cannot be forced strict); `YES` in the derived strict C++-scoped configuration |
| `EXCLUDE_PATTERNS` | the admitted exclusion list; system and generated headers are out of scope (`DOX-GAP-02`) |
| `OUTPUT_DIRECTORY` | `build/doxygen` (not versioned); the trusted validation measure overrides it per measure |

### 6.3 Evidence report (`reports/xcom-queue/t037-doxygen.json`)

| Field | Contract |
| --- | --- |
| `schema_version` | `1` |
| `task_id` | `T037` |
| `capability` | `007` |
| `baseline_revision` | the accepted baseline commit |
| `candidate_revision` | `null` in a committed report; the candidate commit is the direct child of the baseline carrying the recorded material |
| `candidate_identity` | the sorted material-input inventory, the material digest, the per-file SHA-256 hashes, the revision-binding rule, and the generation time |
| `command` | the exact resolved argv of the repository route and the strict C++ route |
| `warnings` | the observed warning count and the empty (or bounded) warning text |
| `output` | the bounded public-safe stdout/stderr summary, the generated HTML/XML index locations, and the indexed-file count |
| `environment` | Doxygen version, compiler, C++ standard, CMake, Ninja, Python, and admitted-input identities and hashes, excluding host-specific absolute paths |
| `strict_cpp` | the strict C++-scoped result: warning count, coverage-gap count, scope, and exclusion list |
| `hashes` | SHA-256 of the retained evidence and referenced candidate artifacts |
| `limitations` | explicit non-production and scope limitations |
| `blockers` | any unavailable input recorded as `blocked` with its reason |

### 6.4 Consumed contracts (read-only, unchanged)

| Interface | Contract consumed |
| --- | --- |
| the accepted `src/xverse/xcom` C++ surface | the public declarations documented by T037; no signature, type, or behavior change |
| the T010 `doxygen_plan` | the mandatory file block, mandatory public tags, coverage rule, groups, and `DOX-GAP-01..03` |
| `docs/engineering/xcom/build-environment.md` | the repository-owned evidence contract (exact environment, candidate revision, bounded public-safe logs) |
| the accepted CMake/CTest subtree | the admitted offline build and the preserved discovered case inventory |

## 7. Concurrency and resource bounds

| Aspect | T037 decision |
| --- | --- |
| Production footprint | none; T037 adds no runtime source, test target, compiled symbol, or dependency |
| Build inventory | the accepted build is unchanged; T037 registers no new accepted test target |
| Processes | one bounded documentation process per run; no legacy, external, or production process |
| Threads | documentation tooling is single-threaded |
| Storage | one bounded JSON report plus bounded excerpts and the non-versioned `build/doxygen` output; no unbounded log retention |
| Transport | none |
| Determinism | the input set, exclusion list, warning treatment, and statistics are fixed for the exact candidate revision |
| Time | no T037 verdict depends on ambient wall-clock time beyond the recorded generation time |

## 8. Quality attributes

| Attribute | Architectural decision | Evidence |
| --- | --- | --- |
| Complete owned documentation | every public declaration documented with `@brief`/params/returns and the contract clauses; mandatory file block on every owned file | `T037-SR-001`; CHK-01 |
| Strict zero-warning C++ reference | strict C++-scoped configuration (`EXTRACT_ALL = NO`, public only, strict warnings, `WARN_AS_ERROR = YES`) | `T037-SR-002`; CHK-02 |
| Warning-free repository route | every admitted-input command defined; repository route under `WARN_AS_ERROR = YES` | `T037-SR-003`; CHK-03 |
| Generated reference honesty | HTML/XML generated warning-free under `build/`; only identities/hashes retained | `T037-SR-004`; CHK-04 |
| Exact-candidate binding | report bound to the baseline, the material digest/inventory, and artifact hashes | `T037-SR-005`; CHK-05, CHK-09 |
| Behavior preservation | Doxygen-comment/config/checker-only change; no compiled token changes | `T037-SR-006`; CHK-10 |
| Public-safe evidence | identities, hashes, command, warning count, bounded excerpts only | `T037-SR-007`; CHK-06 |
| Offline honesty | no network, DNS, TLS, legacy, or production resource; no new dependency | `T037-SR-008`; CHK-07 |
| Governance honesty | registers reconciled; REF-002 `unchanged`; successors allocated | `T037-SR-009`; CHK-11 |
| Fail-closed checking | the checker exits nonzero on any missing comment or warning | `T037-SR-010`; CHK-08, CHK-09 |

## 9. Consistency and constraints

- **Dependency direction preserved.** T037 consumes the accepted T007–T036 design and code; it introduces
  no dependency on a later slice, an external peer, or a legacy repository, and adds no admitted dependency.
- **Domain neutrality preserved.** Only generic documentation vocabulary appears (file block, brief, param,
  return, group, warning); no automotive, product, protocol, or configuration primitive is introduced.
- **XDL centrality preserved.** T037 neither parses nor authors XDL; it documents accepted logical
  identities.
- **Logical/physical separation preserved.** No address, port, or physical transport enters the evidence.
- **Ownership preserved.** Only the declared T037 paths change; every compiled behavior and existing test is
  preserved.
- **Maturity preserved.** The slice records prototype documentation evidence only; traceability, review,
  and acceptance remain T038–T041.

## 10. Traceability

| Architecture element | T037 requirements |
| --- | --- |
| `T37-XB-1`, `T37-CMP-SOURCE` | T037-SR-001, T037-SR-006 |
| `T37-XB-2`, `T37-CMP-CONFIG` | T037-SR-002, T037-SR-003 |
| `T37-XB-3`, `T37-CMP-CHECKER` | T037-SR-004, T037-SR-010 |
| `T37-XB-4`, `T37-CMP-REPORT` | T037-SR-005 |
| `T37-XB-5` | T037-SR-007 |
| `T37-XB-6` | T037-SR-008 |
| `T37-XB-7`, `T37-CMP-TRACE`, `T37-CMP-WP` | T037-SR-009 |
| `T37-CMP-T013…T034` | T037-SR-001, T037-SR-006 |
| `T37-CMP-T011`/`T012` | T037-SR-003, T037-SR-008 |

## 11. Negative cases (architecture view)

Every boundary has a declared fail-closed behaviour and a negative-case owner; the executable cases are
listed in `verification-plan.md` §5.

| Boundary | Injected defect | Negative case |
| --- | --- | --- |
| `T37-XB-1` | change a compiled token, signature, type, default, or expected value under the banner of documentation | NEG-01, NEG-06 |
| `T37-XB-2` | enable strictness over out-of-scope Python/test inputs and hide the resulting warnings, or leave an owned declaration undocumented | NEG-02 |
| `T37-XB-3` | commit a generated tree or a host path, or claim warning-free when a warning exists | NEG-03, NEG-07 |
| `T37-XB-4` | present stale, foreign, or mismatched output as current | NEG-04, NEG-05 |
| `T37-XB-5` | commit a credential, payload, private address, or host path | NEG-07 |
| `T37-XB-6` | use TCP/`AF_INET`, DNS, TLS, a legacy/external peer, or add a dependency | NEG-07 |
| `T37-XB-7` | claim a T038/T039/T041 result, or a production-readiness claim | NEG-08 |
| Governance | mark the T037 checkbox at the plan stage or omit the required report | NEG-09 |
| Trace | omit a required requirement/component/unit/measure/code/validation edge, or leave a stale hash pin | NEG-10 |
