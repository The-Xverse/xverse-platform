# T033 Verification Plan — Reusable Provider, Observer, Stimulation-Tool, and Gateway Contract Suites

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T033 (capability 007, slice `T-CORE`/GW) |
| Stage / role | plan → verification design |
| Revision | 1 (reusable contract-suite slice) |
| Baseline revision | `2fd395e39e44e1f6fe9547998b47499d996b1756` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Classification | Public-safe engineering work product |

"Verified" means the named suite check or inspection exists, is deterministic, and passes at the recorded
candidate revision. It is not a deployed-service, remote-tool, compatibility, or production-readiness claim.

## 2. Verification environment

- Offline admitted X-COM build envelope (T011): admitted `protoc` 3.12.4, admitted GTest prefix, admitted
  standard library and in-process libraries; no network, DNS, TLS, legacy binary, or production workload.
- C++20, warning-as-error (T012), Ninja build, GoogleTest discovery per `t033-<kind>` label.
- CTest cases are executed twice-per-suite through the four drivers; the provider suite additionally runs against
  two independently implemented providers.

## 3. Requirements-to-check matrix

| Requirement | Primary checks | Verification measure |
| --- | --- | --- |
| T033-STK-001 | CHK-01, CHK-03, CHK-05 | unit / integration / validation |
| T033-STK-002 | CHK-06, CHK-07, CHK-08 | unit / integration / validation |
| T033-STK-003 | CHK-09, CHK-10 | unit / integration / validation |
| T033-STK-004 | CHK-11, CHK-12, CHK-13, CHK-14 | unit / integration / validation |
| T033-STK-005 | CHK-15, CHK-16, CHK-21, CHK-22 | unit / validation / gate |
| T033-SR-001 | CHK-01, CHK-02 | unit |
| T033-SR-002 | CHK-04 | unit |
| T033-SR-003 | CHK-05 | unit |
| T033-SR-004 | CHK-06, CHK-07 | unit |
| T033-SR-005 | CHK-08 | unit |
| T033-SR-006 | CHK-07, CHK-08 | unit |
| T033-SR-007 | CHK-09 | unit |
| T033-SR-008 | CHK-10 | unit |
| T033-SR-009 | CHK-11, CHK-12 | unit |
| T033-SR-010 | CHK-12 | unit |
| T033-SR-011 | CHK-13 | unit |
| T033-SR-012 | CHK-14 | unit |
| T033-SR-013 | CHK-11, CHK-14 | unit |
| T033-SR-014 | CHK-15 | unit |
| T033-SR-015 | CHK-16, CHK-19, CHK-20 | validation |
| T033-SR-016 | CHK-03, CHK-21, CHK-22 | validation / gate |

## 4. Named checks

| Check | Description | Requirement |
| --- | --- | --- |
| CHK-01 | `ProviderContractSuite` subject seam exists and `P-01`…`P-03` pass on the loopback provider | T033-SR-001 |
| CHK-02 | the provider suite names no concrete provider type (source inspection) | T033-SR-001 |
| CHK-03 | each suite header and driver carries the `xcom` file block (`@file`, `@brief`, `@ownership`, `@lifetime`, `@thread_safety`, `@failure`, `@par Traceability`) | T033-SR-016 |
| CHK-04 | `P-04` rejects an unsupported contract version before dispatch | T033-SR-002 |
| CHK-05 | `P-05`…`P-13` pass: activate, accepted, saturation, FIFO receive, drain, close, reconcile | T033-SR-003 |
| CHK-06 | `O-01`…`O-03` attach a bounded metadata-only tap and compose a hub-enabled route | T033-SR-004 |
| CHK-07 | `O-04`/`O-07` publish and poll one metadata-only record with identity preservation | T033-SR-004, T033-SR-006 |
| CHK-08 | `O-05`/`O-06`/`O-08`…`O-11` prove overflow counters, exact drain, detach, and isolation | T033-SR-005, T033-SR-006 |
| CHK-09 | `S-01`, `S-02-0`…`S-02-3`, `S-05` prove four action emissions, provenance, and journal ordering | T033-SR-007 |
| CHK-10 | `S-03`/`S-04` prove out-of-window and non-active zero emission | T033-SR-008 |
| CHK-11 | `G-02`/`G-10`/`G-11` prove the ten-operation surface, bounded framing, and counters | T033-SR-009, T033-SR-013 |
| CHK-12 | `G-03`/`G-04`/`G-05`/`G-08` prove version negotiation, arming, and unarmed zero emission | T033-SR-009, T033-SR-010 |
| CHK-13 | `G-09` proves bounded metadata-only observation | T033-SR-011 |
| CHK-14 | `G-01`/`G-06`/`G-07` prove the opened path, four action emissions, and the lease round trip | T033-SR-012, T033-SR-013 |
| CHK-15 | every suite is instantiated at least twice through a distinct subject without editing the suite; the provider suite passes two provider implementations | T033-SR-014 |
| CHK-16 | the build registers four additive `t033-<kind>` targets; no existing target/label/value changes; the runtime-target inventory is unchanged | T033-SR-015 |
| CHK-17 | the suites and committed evidence contain no payload byte, permit content, secret, private address, or host path | T033-SR-015 |
| CHK-18 | the suite checks use only stable codes, logical identity, size, timing, and outcome | T033-SR-015 |
| CHK-19 | `git diff --check` is clean and the changed-path set is exactly the declared T033 paths | T033-SR-015 |
| CHK-20 | the full inherited suite (`ctest -L "t0(20|2[6-9]|3[0-4])-"`) and the Python suite still pass | T033-SR-015 |
| CHK-21 | the T007–T010 register validators pass; REF-002 stays `unchanged` with an empty `promoted` list | T033-SR-016 |
| CHK-22 | `xcom_phase7_gate.py verify T033 <baseline>` passes with a `t033-`-labelled discovered case; the T033 checkbox is marked complete only at implementation | T033-SR-016 |

## 5. Executable suites and negative cases

| Suite (`t033-<kind>`) | Cases | Negative cases |
| --- | --- | --- |
| provider | `AcceptedLoopbackProviderConforms`, `SuiteIsReusableAcrossProviderImplementations` | NEG-02 |
| observer | `AcceptedObservationHubConforms`, `SuiteIsReusableAcrossHubInstances` | NEG-03 |
| stimulation-tool | `AcceptedStimulationPathConforms`, `SuiteIsReusableAcrossFixtures` | NEG-04 |
| gateway | `AcceptedGatewaySessionConforms`, `SuiteIsReusableAcrossFixtures` | NEG-03, NEG-04 |

- **NEG-01** — a TCP/`AF_INET`/DNS/TLS/legacy/external token in a suite or a runtime-target inventory change:
  the forbidden-API/public-safety inspection and CHK-16 fail closed.
- **NEG-02** — a suite names a concrete implementation or copies itself per implementation: CHK-02 and CHK-15
  fail closed.
- **NEG-03** — an unarmed/out-of-window observer or gateway request emits: `S-03`/`S-04`/`G-04`/`G-08` fail.
- **NEG-04** — a non-active session or expired request emits: `S-04`/`G-08` fail.
- **NEG-05** — a payload, permit, secret, private address, or host path is committed: CHK-17 fails.
- **NEG-06** — an existing target/label/value changes or the checkbox is marked in the plan stage: CHK-16 and
  CHK-22 fail closed.
- **NEG-07** — a second provider is added or T034 is pre-empted: the changed-path inspection fails.
- **NEG-08** — a missing suite check is silently skipped: `SuiteReport::ok()` is false and the case fails.

## 6. Traceability to the accepted anchors

| T033 check | Accepted anchor |
| --- | --- |
| CHK-01/CHK-02/CHK-04/CHK-05 | `XCOM-SW-CORE-007`, `XCOM-SW-CORE-009`, `XCOM-DU-007` |
| CHK-06/CHK-07/CHK-08 | `XCOM-SW-OBS-001`…`-004`, FR-011–FR-014 |
| CHK-09/CHK-10 | `XCOM-SW-STIM-001/003/004/007`, FR-015–FR-021 |
| CHK-11…CHK-14 | `XCOM-SW-GW-002`, FR-022/032/034 |
| CHK-15 | User Story 4 independent test; ADR-0020 |
| CHK-16 | T012 build contract; FR-030 |
| CHK-17/CHK-18/CHK-19/CHK-20 | FR-027; ADR-0020 |
| CHK-21/CHK-22 | Constitution VII/IX/X; ADR-0020 |

## 7. Measurement plan and evidence binding

- The trusted `unit` measure builds the isolated target checkout and runs the eight `t033-` cases with the
  preserved `T020`/`T026`–`T032` suites; the trusted `integration`/`validation` measures assemble the pinned
  target revision and run the full CTest and Python suites.
- Evidence is bound to the exact T033 candidate revision; commands, tool/environment identity, exit status,
  bounded logs, and hashes are retained in the repository-owned or referenced evidence bundle (T035).
- No stale, skipped, mismatched, or failed evidence supports acceptance; whole-system integration and static
  analysis run separately from the isolated checkout.

## 8. Definition of done (verification view)

T033 is verified for a candidate revision when all eight `t033-` cases pass under the admitted offline build,
the preserved `T020`/`T026`–`T032` suites still pass, `git diff --check` is clean, the changed-path set is
exactly the declared T033 paths, the T007–T010 register validators pass with REF-002 `unchanged`, and
`xcom_phase7_gate.py verify T033 <baseline>` passes. User acceptance remains T041.

## 9. Repair-pass re-verification (successor)

The separate read-only DeepSeek internal review recorded `verdict: fail` with `REV-T033-001` (medium) and
`REV-T033-002` (low): an off-by-one shift in the `@par Traceability` requirement ranges of the four reusable suite
headers and four drivers, and bare SESN-era observation and undefined stimulation requirement anchors. Both are
annotation-only. The
successor (`implementation.md` §13) corrects every range to the authoritative
`engineering/requirements/T033-SR-*.json` mapping, replaces every anchor with its accepted
`docs/engineering/xcom/t008/requirements-register.json` id, adds the nine `implemented_by` links needed to keep the
corrected driver ranges truthful, and removes the unused `XCOM_T033_SUITE_HEADER_ROOT` compile definition.

The affected verification is repeated on the successor: `ctest --test-dir build/fabro-t030-t034-system-unit -L t033-`
(8/8, unchanged behavior), the `sha256`/`target_revision` integrity of the edited `tests/xcom/contract_suites/*` and
T033 work products in `engineering/trace/links.json`, the T007–T010 register validators, and the deterministic gate
`xcom_phase7_gate.py verify T033 <baseline>`. ADR-0020 requires a fresh independent review of the successor; no check
or measure is weakened, and user acceptance remains T041.

## 10. Repair-pass re-verification 2 (successor)

The second read-only DeepSeek internal review recorded `verdict: fail` with four low documentation-consistency
findings (`REV-T033-003`…`REV-T033-006`): a truncated context-diagram label, an unreproducible full-discovery count,
a `T033-SR-007` check range that overlapped `T033-SR-008`, and a `T033-SR-009-U` input not consumed by `G-02`. Each
correction is recorded in `implementation.md` §14. The corrections are documentation-only and change no check,
expected value, test, target, label, or measure.

The affected verification is repeated on this successor:

- `ctest --test-dir build/fabro-t030-t034-system-unit -L t033-` — 8/8 pass, unchanged behavior.
- `ctest --test-dir build/fabro-t030-t034-system-unit -N` — `Total Tests: 483`, matching the corrected
  `reports/review-index.md` value.
- Every T033 `implemented_by` `target_revision` in `engineering/trace/links.json` equals the current bytes of its
  target, including the refreshed `T033-L-0189`…`T033-L-0192` work-product pins.
- The T007–T010 register validators pass, and `xcom_phase7_gate.py verify T033 <baseline>` passes with a
  `t033-`-labelled discovered case.

ADR-0020 requires a fresh independent review of the successor; no check or measure is weakened, and user acceptance
remains T041.
