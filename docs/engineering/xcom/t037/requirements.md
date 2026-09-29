# T037 Requirements — Complete Doxygen Comments and Warning-Free Generated Reference Documentation

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T037 (capability 007, slice `T-INTG`/documentation) |
| Task title | Add complete Doxygen comments and generate warning-free reference documentation |
| Stage / role | plan → requirements |
| Revision | 1 (Phase 8 Doxygen-completion slice) |
| Baseline revision | `8757a79d4e6b2630124d774fcba2a55d6342a879` |
| Authorization | capability 007 accepted design and bounded implementation authorization (`ACC012`, `ACC014`, `ACC015`); `ADR-0020` (repository-owned work products and exact-candidate evidence); Constitution VI, IX, X |
| Owning slice | `T-INTG` (T007 ownership register); T037 is the documentation task of the `T-INTG` evidence family and the sole owner of `XCOM-DU-022` and `XCOM-SW-INTG-002` |
| Predecessors | T035 accepted exact-candidate verification matrix and repository-owned results; T036 accepted controlled disabled/enabled-tap benchmark; T030–T034 accepted contract/gateway/client/suite/provider; T026–T029 accepted stimulation boundary; T021–T024 accepted observation boundary; T017–T020 accepted XDL activation plan; T016 accepted core matrix; T011 admitted offline toolchain, Doxygen configuration, and `scripts/check_doxygen.py`; T012 subtree build/CTest contract |
| Successor tasks | T038–T041 (traceability verifier/SADS disposition, external review, acceptance-bundle inspection, user acceptance) |
| Consumed registers | `docs/engineering/xcom/task-ownership.{json,md}` (`T-INTG` slice); `docs/engineering/xcom/t008/requirements-register.json` (`XCOM-SW-INTG-002` — the register row whose `owning_task` is T037; supporting `XCOM-SW-ENB-004`, `XCOM-SW-CORE-007`, `XCOM-SW-INTG-001`, `XCOM-SW-ENB-001`, `XCOM-SW-ENB-002`); `docs/engineering/xcom/t009/architecture-model.json`; `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-022`, Doxygen plan `DOX-GAP-01`/`DOX-GAP-03`); `docs/engineering/xcom/t011/{build-environment,dependency-lock}.md`; `specs/007-xcom-core/spec.md` FR-029/SC-009; `Doxyfile`; `scripts/check_doxygen.py` |
| Classification | Public-safe engineering work product |

This document is a repository-owned work product (ADR-0020). It is written **before** the Doxygen completion
is executed and does not itself execute, accept, or integrate the candidate. The T037 task entry in
`specs/007-xcom-core/tasks.md` is the authorized scope:

> T037 — Add complete Doxygen comments and generate warning-free reference documentation.

It realizes the accepted delivery-phase documentation step of `specs/007-xcom-core/plan.md` ("Doxygen
warning-as-error validation"), the measurable outcome `SC-009` ("Every requirement traces to design units and
automated evidence, and public interfaces generate warning-free Doxygen output"), the accepted
`XCOM-SW-INTG-002` software requirement ("Generate warning-free Doxygen for every public C/C++ interface and
changed unit and validate that every requirement traces to design units and automated evidence"), the
`XCOM-SW-ENB-004` admitted-Doxygen-environment obligation, the `XCOM-SW-CORE-007`/`XCOM-SW-INTG-001`
public-safe and owned-only obligations, and the `XCOM-DU-022` `DOX-GAP-01`/`DOX-GAP-03` strict-C++ gaps. It
does not perform, duplicate, or claim the T038 traceability-verifier/SADS-disposition, T039 external review,
T040 acceptance-bundle inspection, or T041 user acceptance work.

### 1.1 Authority statement

T037 owns the **complete Doxygen documentation of the owned X-COM C/C++ public interface and the
warning-free generation and retention of that reference**. It provides:

- complete file-block and declaration-level Doxygen comments across the owned `src/xverse/xcom` C++ sources,
  headers, and fixtures, including the `ownership`, `lifetime`, `thread_safety`, and `failure` contract
  clauses required by the T010 Doxygen plan;
- the repository Doxygen configuration (`Doxyfile`) and coverage/HTML checker (`scripts/check_doxygen.py`)
  extended so that (a) the repository-wide route the trusted Phase 8 validation measure runs stays
  warning-free under `WARN_AS_ERROR = YES`, and (b) a strict C++-scoped configuration over the owned C++
  inputs returns zero warnings and zero coverage gaps;
- the repository-owned evidence report `reports/xcom-queue/t037-doxygen.json` carrying `command`, `warnings`,
  `output`, the resolved environment identity, artifact hashes, and the exact-candidate identity;
- the T037 engineering records and work products that trace every T037 requirement to an accepted anchor,
  component, unit, measure, and named executed case or inspection.

The `T008` requirements register allocates `XCOM-SW-INTG-002` (`owning_task` T037) as the accepted software
anchor this task realizes, together with the supporting anchors above. The register rows are not edited
(T026–T036 precedent).

**Recorded design decision (`T037-DD-01`).** T037 changes **no runtime behavior**: its source edits are
Doxygen comments only, plus the Doxygen configuration and the documentation checker. It adds no accepted
CTest target, no compiled symbol, no admitted dependency, and no runtime library. The trace's `implemented_by`
edges point at the documented C++ public surface and at the Doxygen configuration/checker; the executed cases
are named by the accepted suites' existing discovered IDs plus the Doxygen generation route.

**Documentation-only, behavior-preserving boundary.** T037 authors Doxygen comments in the owned
`src/xverse/xcom` C++ inputs, edits `Doxyfile` and `scripts/check_doxygen.py`, adds the T037 work-product set
and engineering records, and adds additive trace links. It authors no change to any compiled statement,
control-flow decision, signature, type, default value, contract, schema, register, or expected value.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, plan, contracts, data
model, the T007 ownership register, the T008 register, the T009 architecture model, the T010 unit design, the
constitution, or an accepted ADR is resolved in favour of the accepted source. A material gap is reported
rather than guessed. Unresolved items are recorded in §8.

## 2. Scope

### 2.1 Plan-stage baseline measurement (Doxygen gap inventory)

The plan stage executed read-only probes (Doxygen 1.9.1, output written outside the candidate tree) to size
the work honestly. No generated documentation or warning log is committed by the plan stage.

- **Repository-wide trusted route** (`doxygen` over the accepted `Doxyfile` with `WARN_AS_ERROR = YES`):
  **fails closed** at the baseline with diagnostics, dominated by `warning: Found unknown command '@bounds'`
  (104 occurrences across 49 admitted input files, of which one is
  `src/xverse/xcom/include/xverse/xcom/stimulation_actions.hpp` and the rest are accepted `tests/xcom/**`
  inputs) plus a duplicated `journal_and_emit` parameter warning for the undocumented `lock` parameter.
  The `bounds` command has no `ALIASES` definition in `Doxyfile`.
- **Strict C++-scoped probe** (`EXTRACT_ALL = NO`, `EXTRACT_PRIVATE = NO`, `EXTRACT_STATIC = NO`,
  `WARN_IF_UNDOCUMENTED = YES`, `WARN_NO_PARAMDOC = YES`, `INPUT = src/xverse/xcom`): **111 warning lines**
  concentrated on the owned C++ public surface — `activation_plan.hpp` (86, undocumented plan struct
  members), `tool_gateway.hpp` (20, missing `@param`/`@return`), `stimulation_actions.hpp` (2),
  `validation_session.hpp` (2), and `fixtures/synthetic_tool.cpp` (1).
- **Inherited Python coverage limitation.** `scripts/check_doxygen.py --coverage-only` fails **pre-existing**
  on Python-module/function docstrings in unchanged files (accepted `scripts/validate_*.py` and
  `src/xverse_xdl/xcom_plan.py`), as already recorded by T013/T022/T023 (`T013-LIM-02`, `T022-LIM-08`,
  `T023-LIM-08`). Those files are outside T037's owned change set; T037 preserves that finding as an
  inherited limitation and does not silently rewrite out-of-scope sources to hide it.

### 2.2 In scope (bounded T037)

1. **Complete owned C++ Doxygen comments.** Every public declaration in the owned `src/xverse/xcom` C++
   headers, sources, and fixtures is documented with `@brief`, the applicable `@param`/`@return`/`@retval`,
   and the ownership/lifetime/thread-safety/failure contract clauses; every owned C++ file carries the
   mandatory file block (`@file`, `@brief`, `@ingroup`).
2. **Repository Doxygen configuration.** `Doxyfile` defines every command used by the admitted inputs
   (notably the `bounds` alias) so the repository-wide generation route is warning-free under
   `WARN_AS_ERROR = YES`, and the owned C++ inputs are documented to the strict target.
3. **Strict C++ check.** A strict C++-scoped configuration (owned C++ inputs only, `EXTRACT_ALL = NO`,
   public declarations only, `WARN_IF_UNDOCUMENTED = YES`, `WARN_NO_PARAMDOC = YES`, `WARN_AS_ERROR = YES`,
   with an admitted exclusion list for generated/system headers) is exercised by the T037 checker and
   returns zero warnings.
4. **Warning-free generation.** The reference documentation (HTML and XML) is generated warning-free; the
   generated output lives under `build/` and is intentionally not versioned.
5. **Task-owned checker.** `scripts/check_doxygen.py` gains a strict C++ mode that fails closed on a missing
   declaration comment, a missing mandatory contract tag, or any Doxygen warning.
6. **Repository-owned report.** `reports/xcom-queue/t037-doxygen.json` exists and carries `command`,
   `warnings`, `output`, the resolved environment identity, artifact hashes, and the exact-candidate identity.
7. **Exact-candidate binding.** Every result is bound to the accepted baseline revision and the exact
   candidate material (a sorted material-input inventory, a material digest, and per-file SHA-256 hashes).
8. **Public safety.** The report, logs, and excerpts exclude credentials, private addresses, unrestricted
   payloads, proprietary source excerpts, and host-specific absolute paths.
9. **Traceability.** Every applied T037 requirement traces to its accepted X-COM anchor and is verified by a
   named executed command, case, or inspection.
10. **Owned/local execution.** The documentation route uses only the admitted offline toolchain and the
    owned sources; it opens no network, DNS, TLS, legacy, or production resource.
11. **No accepted change beyond documentation.** No compiled behavior, signature, type, default, test,
    target, label, command, or expected value changes.
12. **Governance honesty.** The T007–T010 models are reconciled without rewrite; the REF-002 disposition
    stays `unchanged` with an empty `promoted` list; T037 is recorded implemented while T038–T041 remain
    allocated.
13. The T037 repository-owned work products and the T037 package record.

### 2.3 Explicit exclusions (must remain absent from the T037 candidate)

No modification of any compiled behavior, signature, type, default value, contract, schema, register, XDL
profile, accepted test, target, label, command, or expected value; no new admitted dependency; no new runtime
library or compiled symbol; no compiled or linked gRPC runtime; no TCP listener or `AF_INET`/`AF_INET6`
socket, DNS, resolver, or TLS use; no external network peer; no legacy binary, legacy repository, or
production workload execution; no rewrite of an accepted source outside documentation comments and the
Doxygen configuration/checker; no re-run or re-claim of the T035 verification matrix or the T036 benchmark;
no traceability-verifier or REF-002/SADS promotion (T038); no external review record (T039); no
acceptance-bundle inspection record (T040); no user acceptance or platform-main merge (T041); no
ambient/secret access or dynamic load; no committed generated HTML/XML tree under version control; no claim
of production, deployed-service, network, transport, compatibility, or timing fidelity; no rewrite or
weakening of an accepted ADR, requirement, contract, schema, register, or test; no promotion of any REF-002
SADS ID beyond its recorded disposition; no acceptance or integration of the candidate.

### 2.4 Delegated to other tasks (not performed or decided here)

| Area | Owner | Disposition in T037 |
| --- | --- | --- |
| Complete exact-candidate verification matrix and repository-owned results | T035 | accepted; consumed read-only, not re-run or re-claimed by T037 |
| Controlled disabled/enabled-tap benchmark and repository-owned results | T036 | accepted; consumed read-only, not re-run or re-claimed by T037 |
| Spec Kit + REF-002 traceability verifier, public-safe log validation, SADS disposition proof | T038 | allocated; not run or reported by T037 |
| Independent read-only review | T039 | allocated; deferred until the ordered backlog `xcom-t030-t034-20260928` completes |
| Acceptance-bundle assembly and inspection | T040 | allocated |
| Explicit user acceptance and platform-main delivery | T041 | allocated |

## 3. Stakeholder requirements (`T037-STK-###`)

- **T037-STK-001**: Before any capability-007 documentation claim, the program **shall** record complete,
  warning-free generated Doxygen reference documentation for the owned public C/C++ interface together with
  the exact command, the observed warnings, the tool output, and the resolved environment.
- **T037-STK-002**: Every retained documentation result **shall** be bound to the accepted baseline revision
  and the exact candidate material (a sorted material-input inventory, a material digest, and per-file
  SHA-256 hashes) and **shall** identify its command, warnings, output, and artifact hashes. Because a
  committed report cannot contain the hash of the commit that contains it, the candidate commit is identified
  as the direct child of the accepted baseline carrying that material.
- **T037-STK-003**: Documentation evidence and logs **shall** be repository-owned, bounded, and public-safe,
  and **shall** exclude credentials, private addresses, unrestricted payloads, proprietary source excerpts,
  and host-specific or sensitive deployment values.
- **T037-STK-004**: Every applied T037 requirement **shall** trace to its accepted X-COM system/software
  anchor and **shall** be verified by a named executed command, case, or inspection, not by source inspection
  alone.
- **T037-STK-005**: T037 **shall** preserve accepted intent and report maturity honestly: it changes no
  compiled behavior or accepted test, keeps the accepted registers and the REF-002 disposition `unchanged`
  with an empty `promoted` list, and leaves T038–T041 allocated.

## 4. Software/engineering requirements (`T037-SR-###`)

Each requirement is written in EARS style, carries a stable verification intent, and links to an accepted
anchor. "Verified" means the named command, case, or inspection exists, is deterministic, and passes at the
recorded candidate revision; it is not a deployed-service, compatibility, or production-readiness claim.

### 4.1 Complete comments and strict configuration

- **T037-SR-001 [ubiquitous]**: Every public declaration in the owned `src/xverse/xcom` C++ headers, sources,
  and fixtures **shall** carry a Doxygen `@brief` and the applicable `@param`/`@return`/`@retval`, and every
  owned declaration **shall** carry the applicable ownership, lifetime, thread-safety, and failure contract
  clauses; every owned C++ file **shall** carry the mandatory file block (`@file`, `@brief`, `@ingroup`).
  - Refines: `T037-STK-001`; anchors `XCOM-SW-INTG-002`; `XCOM-SYS-FR-029`, `XCOM-SYS-SC-009`.
  - Verification intent: `T033ObserverContractSuite.AcceptedObservationHubConforms`.
- **T037-SR-002 [event-driven]**: When the strict C++-scoped Doxygen configuration runs over the owned C++
  inputs (`EXTRACT_ALL = NO`, public declarations only, `WARN_IF_UNDOCUMENTED = YES`,
  `WARN_NO_PARAMDOC = YES`, `WARN_AS_ERROR = YES`, admitted exclusion list), it **shall** exit zero with zero
  warnings and zero coverage gaps.
  - Refines: `T037-STK-001`, `T037-STK-004`; anchors `XCOM-SW-INTG-002`, `XCOM-SW-ENB-004`;
    `XCOM-SYS-FR-029`, `XCOM-SYS-SC-009`.
  - Verification intent: `T033ProviderContractSuite.AcceptedLoopbackProviderConforms`.
- **T037-SR-003 [ubiquitous]**: `Doxyfile` **shall** define every command used by the admitted inputs
  (including the `bounds` alias), and the repository-wide generation route that the trusted Phase 8
  validation measure runs **shall** complete warning-free under `WARN_AS_ERROR = YES`.
  - Refines: `T037-STK-001`; anchors `XCOM-SW-INTG-002`, `XCOM-SW-ENB-004`; `XCOM-SYS-FR-029`.
  - Verification intent: `T20OrderingEquivalence.ReorderedDocumentSameOutcomeAndDecodedValue`.
- **T037-SR-004 [ubiquitous]**: The task **shall** generate the HTML and XML reference documentation
  warning-free; the generated output **shall** live outside version control under `build/`, and the retained
  evidence **shall** record only public-safe identities and hashes, never a host-specific absolute path.
  - Refines: `T037-STK-001`, `T037-STK-003`; anchors `XCOM-SW-INTG-002`; `XCOM-SYS-FR-029`.
  - Verification intent: `T033GatewayContractSuite.AcceptedGatewaySessionConforms`.

### 4.2 Evidence, exact binding, and public safety

- **T037-SR-005 [ubiquitous]**: `reports/xcom-queue/t037-doxygen.json` **shall** record `command`,
  `warnings`, `output`, the resolved Doxygen/toolchain environment identity, retained-evidence hashes, and the
  exact-candidate identity, and **shall** be bound to the accepted baseline revision and the exact candidate
  material (inventory, digest, and per-file SHA-256 hashes).
  - Refines: `T037-STK-002`; anchors `XCOM-SW-INTG-002`, `XCOM-SW-INTG-001`; `XCOM-SYS-FR-027`,
    `XCOM-SYS-FR-029`.
  - Verification intent: `XcomToolGatewayBounds.MessageSizeBoundEnforced`.
- **T037-SR-006 [unwanted]**: T037 **shall** change no compiled statement, control-flow decision, signature,
  type, default value, contract, schema, register, XDL profile, or test byte; every additive work product
  **shall** preserve every accepted target, label, command, and expected value.
  - Refines: `T037-STK-005`; anchors `XCOM-SW-INTG-002`, `XCOM-SW-ENB-004`; `XCOM-SYS-FR-029`.
  - Verification intent: `T034SecondProviderSuite.ReusedProviderContractSuitePasses`.
- **T037-SR-007 [ubiquitous]**: The committed report, logs, work products, and excerpts **shall** contain no
  credential, private address, unrestricted payload, proprietary source excerpt, or host-specific absolute
  path.
  - Refines: `T037-STK-003`; anchors `XCOM-SW-INTG-001`; `XCOM-SYS-FR-027`.
  - Verification intent: `XcomToolGatewayNegative.NoTcpOrAddressPrimitive`.
- **T037-SR-008 [unwanted]**: No T037 command **shall** open a TCP listener or `AF_INET`/`AF_INET6` socket,
  use DNS, a resolver, or TLS, contact an external peer, execute a legacy binary or production workload, or
  add an admitted dependency.
  - Refines: `T037-STK-003`; anchors `XCOM-SW-CORE-007`; `XCOM-SYS-FR-026`, `XCOM-SYS-FR-028`.
  - Verification intent: `T034VersionRejection.RejectionEmitsNothing`.

### 4.3 Governance, traceability, and fail-closed checking

- **T037-SR-009 [ubiquitous]**: T037 **shall** reconcile with the T007 ownership register, the T008
  register, the T009 architecture model, and the T010 unit design without rewriting or weakening them;
  **shall** keep the REF-002 disposition `unchanged` with an empty `promoted` list; **shall** record T037 as
  implemented while T038–T041 remain allocated; and **shall** satisfy the deterministic Phase 8 gate and the
  required trace links.
  - Refines: `T037-STK-004`, `T037-STK-005`; anchors `XCOM-SW-ENB-001`, `XCOM-SW-ENB-002`;
    `XCOM-SYS-FR-030`, `XCOM-SYS-FR-035`.
  - Verification intent: `CoreMatrixRecovery.Reconcile_MismatchReportsInterruptedResource`.
- **T037-SR-010 [event-driven]**: The task-owned documentation checker **shall** fail closed (nonzero) when
  an owned public declaration is undocumented, a mandatory contract tag is absent, or the strict generation
  emits a warning; it **shall** exit zero only for a complete, warning-free result.
  - Refines: `T037-STK-004`; anchors `XCOM-SW-INTG-002`; `XCOM-SYS-FR-029`, `XCOM-SYS-SC-009`.
  - Verification intent: `CoreMatrixNegative.Neg09_UnsupportedContractVersion_RejectedBeforeDispatch`.

## 5. Requirement-to-accepted-anchor traceability

| T037 requirement | Accepted software req | System req | Spec anchor | Success criterion / constitution |
| --- | --- | --- | --- | --- |
| T037-STK-001 | `XCOM-SW-INTG-002` | `XCOM-SYS-FR-029`, `XCOM-SYS-SC-009` | FR-029, SC-009, plan documentation step | IX, X |
| T037-STK-002 | `XCOM-SW-INTG-002`, `XCOM-SW-ENB-004` | `XCOM-SYS-FR-029` | FR-029 | X |
| T037-STK-003 | `XCOM-SW-INTG-001` | `XCOM-SYS-FR-027` | FR-027 | VII, X |
| T037-STK-004 | `XCOM-SW-ENB-001` | `XCOM-SYS-FR-030`, `XCOM-SYS-SC-009` | FR-030, SC-009 | IX, X |
| T037-STK-005 | `XCOM-SW-ENB-002` | `XCOM-SYS-FR-027/029/035` | FR-027, FR-029, FR-035 | VII, IX, X |
| T037-SR-001 | `XCOM-SW-INTG-002` | `XCOM-SYS-FR-029`, `XCOM-SYS-SC-009` | FR-029, SC-009 | IX, X |
| T037-SR-002 | `XCOM-SW-INTG-002`, `XCOM-SW-ENB-004` | `XCOM-SYS-FR-029`, `XCOM-SYS-SC-009` | FR-029, SC-009 | VI, X |
| T037-SR-003 | `XCOM-SW-INTG-002`, `XCOM-SW-ENB-004` | `XCOM-SYS-FR-029` | FR-029 | X |
| T037-SR-004 | `XCOM-SW-INTG-002` | `XCOM-SYS-FR-029` | FR-029 | X |
| T037-SR-005 | `XCOM-SW-INTG-002`, `XCOM-SW-INTG-001` | `XCOM-SYS-FR-027/029` | FR-027, FR-029 | VII, X |
| T037-SR-006 | `XCOM-SW-ENB-004`, `XCOM-SW-INTG-002` | `XCOM-SYS-FR-029` | FR-029 | VI, X |
| T037-SR-007 | `XCOM-SW-INTG-001` | `XCOM-SYS-FR-027` | FR-027 | VII, X |
| T037-SR-008 | `XCOM-SW-CORE-007` | `XCOM-SYS-FR-026/028` | FR-026, FR-028 | VII, IX |
| T037-SR-009 | `XCOM-SW-ENB-001/002` | `XCOM-SYS-FR-030/035` | FR-030, FR-035 | VII, IX, X |
| T037-SR-010 | `XCOM-SW-INTG-002` | `XCOM-SYS-FR-029` | FR-029, SC-009 | IX, X |

Each accepted T037 software requirement refines at least one `T037-STK-###` stakeholder requirement through
an explicit `refines` link in `engineering/trace/links.json`. `T037-VS-ACCUMULATED` validates
`T037-SR-001`…`-010` and names the executed Doxygen route and inherited matrix cases that the trusted
measures select.

## 6. REF-002 disposition

T037 owns no REF-002 SADS ID and promotes none. Complete Doxygen documentation and warning-free generation
are recorded as a **partial contribution** to the already-**allocated** `XVE-SYS-0139`–`0158` targets through
their accepted dispositions, and are **not** promoted. `XVE-SYS-0141` remains **deferred**; `XVE-SYS-0143`/
`0157` remain deferred to registry/reconfiguration; `XVE-SYS-0144`/`0153`/`0155` remain deferred to
Security/deployment; `XVE-SYS-0148`/`0150`/`0151` remain deferred to record/replay, edge/cloud, and Argus
adapters; the automatic recovery portion of `XVE-SYS-0158` remains deferred to Faults/Runtime. The capability
`ref002.disposition` stays `unchanged` (T037-SR-009). No allocated, deferred, architectural-target, or
superseded SADS requirement is reported as implemented.

## 7. Affected paths

### 7.1 Paths the T037 candidate changes

| Path | Change | Notes |
| --- | --- | --- |
| `docs/engineering/xcom/t037/{requirements,architecture,detailed-design,unit-specifications,verification-plan}.md` | add (plan stage) | this work-product set |
| `docs/engineering/xcom/t037/{implementation.md,internal-review.json}` | add (implementation/review stages) | not produced by the plan stage |
| `engineering/project.json` | edit (plan stage) | current task T037 and accepted baseline `8757a79d4e6b2630124d774fcba2a55d6342a879` |
| `engineering/requirements/T037-STK-00{1..5}.json`, `T037-SR-0{01..10}.json` | add (plan stage) | current-task requirement records |
| `engineering/architecture/components/T037-SR-0{01..10}-CMP.json` | add (plan stage) | current-task component allocations |
| `engineering/unit-specifications/T037-SR-0{01..10}-U.json` | add (plan stage) | current-task unit specifications |
| `engineering/validation/scenarios/T037-VS-ACCUMULATED.json` | add (plan stage) | current-task validation scenario |
| `engineering/trace/links.json` | edit (plan stage; refreshed at implementation) | additive T037 trace links and the inherited `implemented_by` digest refresh |
| `reports/review-index.md` | edit (plan stage) | T037 plan-stage candidate section appended |
| `Doxyfile` | edit (implementation stage) | add the missing alias(es) so the repository route is warning-free |
| `scripts/check_doxygen.py` | edit (implementation stage) | strict C++ mode: coverage + zero-warning generation, fail closed |
| `src/xverse/xcom/include/xverse/xcom/*.hpp`, `src/xverse/xcom/src/*.cpp`, `src/xverse/xcom/fixtures/*` | edit (implementation stage) | Doxygen comments only; no compiled behavior change |
| `reports/xcom-queue/t037-doxygen.json` | add (implementation stage) | the exact-candidate Doxygen evidence report (`command`, `warnings`, `output`) |
| `specs/007-xcom-core/tasks.md` | edit (implementation stage only) | one-line T037 checkbox |
| `reports/xcom-queue/t037-package.json` | add (implementation stage) | package record |

### 7.2 Consumed read-only (not changed by T037)

Every accepted `src/xverse/xcom/**` declaration is documented, but no compiled statement, signature, type,
default, or contract is changed; the accepted `tests/xcom/**` and `tests/test_xcom_plan.py` inputs are
preserved (they are Doxygen inputs but not re-authored except where a Doxygen-only comment is required — see
§8.3 `T037-OPEN-05`); `docs/engineering/xcom/task-ownership.*`; `docs/engineering/xcom/t00{7,8,9}/**` and
`docs/engineering/xcom/t010/**`; `docs/engineering/xcom/t0{11..36}/**`;
`docs/engineering/xcom/{build-environment,dependency-lock}.md`; `engineering/verification/measures/**`; and
`specs/007-xcom-core/**` other than the T037 checkbox.

### 7.3 Explicitly not implemented by T037

The T035 verification matrix and T036 benchmark (accepted; consumed read-only), the T038 traceability
verifier and SADS disposition proof, the gRPC transport runtime linkage (`T032-GAP-01`), and any change to
compiled behavior, an accepted test, target, label, command, or expected value. External Codex review and
user acceptance remain T039/T041 and are deferred until the ordered backlog `xcom-t030-t034-20260928`
completes.

## 8. Gaps, risks, and open items

### 8.1 Recorded limitations

- **T037-GAP-01 — documentation only.** T037 records complete documentation and warning-free generation; it
  makes no compiled-behavior, deployed-service, compatibility, or production-readiness claim.
- **T037-GAP-02 — inherited strict-C++ strictness.** The accepted configuration keeps
  `WARN_IF_UNDOCUMENTED = NO` and `WARN_NO_PARAMDOC = NO` for the repository-wide route (whose inputs include
  out-of-scope Python and test sources); the strict declaration-level coverage is exercised by the T037
  C++-scoped configuration (`XCOM-DU-022` `DOX-GAP-01`, `DOX-GAP-03`).
- **T037-GAP-03 — DOX-GAP-02 provenance.** Generated protobuf C++ provenance and its documentation policy
  remain admitted by T011 (`DOX-GAP-02`); T037 documents only the owned hand-written C++ surface and defers
  generated/system headers to the admitted exclusion list.
- **T037-GAP-04 — no successor claim.** The traceability verifier/SADS disposition (T038), review
  (T039/T040), and acceptance (T041) remain allocated.

### 8.2 Gaps with owning tasks

| Gap | Owner |
| --- | --- |
| Traceability verifier and REF-002/SADS disposition | T038 |
| Independent review, acceptance-bundle inspection, user acceptance | T039/T040/T041 |
| Generated protobuf C++ documentation policy (`DOX-GAP-02`) | T011 |
| Inherited Python docstring coverage findings (`T013-LIM-02`, `T022-LIM-08`, `T023-LIM-08`) | preserved limitation; no current owner (outside capability-007 change set) |

### 8.3 Open items

- **T037-OPEN-01 — report is implementation-stage.** `reports/xcom-queue/t037-doxygen.json` is produced only
  at the implementation stage from the executed generation; the plan stage records the required schema
  (`command`, `warnings`, `output`, environment, hashes, candidate identity) and the exact route rather than
  fabricating results.
- **T037-OPEN-02 — source comments are implementation-stage.** The Doxygen comments, the `Doxyfile` alias
  addition, and the strict checker mode are authored at the implementation stage; the plan records the exact
  measured gap inventory and the required obligations.
- **T037-OPEN-03 — trace digest refresh.** T037 edits C++ headers and the Doxygen configuration/checker, so
  the implementation stage **must** refresh the `implemented_by` pins for every edited artifact (and the
  inherited `engineering/project.json` pins) so that no stale hash remains in `engineering/trace/links.json`.
- **T037-OPEN-04 — unavailable inputs are blockers.** If the admitted offline input, the Doxygen executable,
  or the generation environment is unavailable at the candidate revision, the affected check is recorded as
  `blocked` (with the reason) and the candidate does not claim a pass; the plan does not substitute inferred
  or stale output.
- **T037-OPEN-05 — Doxygen-only comments in admitted test inputs.** The repository-wide route treats
  `tests/xcom/**` as Doxygen inputs. If the only warning-free remedy requires a change to an admitted test
  input, the implementation may add a Doxygen-confined alias definition to `Doxyfile` (preferred, zero
  admitted-input change) or, where unavoidable, a comment-only edit; any compiled test behavior and every
  accepted expected value remain unchanged.
- **T037-OPEN-06 — Python coverage remains inherited.** The pre-existing Python docstring findings in
  `scripts/**` and `src/xverse_xdl/**` are preserved as an inherited limitation; T037 does not claim to fix
  them and does not report the Python coverage check as passing.
- **T037-OPEN-07 — no T010 path-status reconciliation required.** Unlike `docs/engineering/xcom/t036/`,
  `docs/engineering/xcom/t037/` was **not** declared as a planned artifact path in the T010 unit design, so
  no planned→established path-status reconciliation is performed. If a reviewer requires the directory to be
  modeled, that is a T010/T008 register action, not a T037 change.

## 9. Definition of done (requirements view)

T037 is done for a candidate revision when: every §4 requirement has at least one named executed command,
case, or inspection; every owned public C/C++ declaration carries complete Doxygen comments and every owned
file carries the mandatory file block; the strict C++-scoped configuration returns zero warnings and zero
coverage gaps; the repository-wide `Doxyfile` route is warning-free under `WARN_AS_ERROR = YES`;
`reports/xcom-queue/t037-doxygen.json` carries `command`, `warnings`, `output`, the environment identity,
hashes, and the exact-candidate identity; no compiled behavior or accepted test changes; every retained
artifact is public-safe; the accepted registers are reconciled with the REF-002 disposition `unchanged` and
nothing promoted; the deterministic Phase 8 gate passes; and a separate DeepSeek internal review records its
findings before any repair. This does not constitute user acceptance, which remains T041.

## 10. Requirement-to-check index (realized in `verification-plan.md`)

| Requirement | Primary checks |
| --- | --- |
| T037-STK-001 | CHK-01, CHK-02, CHK-03 |
| T037-STK-002 | CHK-04, CHK-05 |
| T037-STK-003 | CHK-06, CHK-07 |
| T037-STK-004 | CHK-08, CHK-09 |
| T037-STK-005 | CHK-10, CHK-11 |
| T037-SR-001 | CHK-01, CHK-08 |
| T037-SR-002 | CHK-02 |
| T037-SR-003 | CHK-03 |
| T037-SR-004 | CHK-04 |
| T037-SR-005 | CHK-05, CHK-09 |
| T037-SR-006 | CHK-10 |
| T037-SR-007 | CHK-06 |
| T037-SR-008 | CHK-07 |
| T037-SR-009 | CHK-09, CHK-11 |
| T037-SR-010 | CHK-08, CHK-09 |
