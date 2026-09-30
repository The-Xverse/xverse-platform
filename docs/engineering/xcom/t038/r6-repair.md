# T038 delivery envelope — T039 R6 documentation-precision repair

This is the T039 R6 successor repair record for the T038 delivery envelope. It corrects exactly the three
documentation-precision findings that the T039 R5 independent review recorded against the R5 successor candidate,
on the admitted baseline `25a9990b86c39408e75381ed5d4aa3d29fc453a7` (direct parent and protected first-R5
checkpoint `88cf30b16adbe4b48c5c79935dd21af605480c98`; reviewed R4 baseline
`67e38e5974f2dd827b4d7fb902343c347341c796`).

It preserves `T039-F01`–`T039-F08`, the T040 `E01`–`E03` reconciliation, `T037-OPEN-06`, the REF-002
`unchanged` disposition, and the R3/R4/R5 records as historical evidence at their original identities. It does not
mark T039, T040, or T041 complete, accept, or merge anything, and `engineering/project.json` stays at `task_id`
`T038`.

Nothing in this record is a successor execution of the retained R3/R4/R5 inputs. Historical success is not current
execution.

## 1. Authorization and identity boundary

| Field | Value |
| --- | --- |
| Task | T038 (capability 007, Phase 8 delivery envelope) |
| Admitted baseline (this run) | `25a9990b86c39408e75381ed5d4aa3d29fc453a7` |
| Admitted baseline parent / protected checkpoint | `88cf30b16adbe4b48c5c79935dd21af605480c98` |
| Complete reviewed R4 baseline | `67e38e5974f2dd827b4d7fb902343c347341c796` |
| R5 independent review input | `docs/reviews/t039-r5-independent-review-2026-09-30.md` |
| R5 review manifest input | `automation/reviews/t039-r5-independent-review-20260930/manifest.json` |
| R5 terminal inspection input | `docs/reviews/t040-r5-terminal-inspection-2026-09-30.md` |
| Repair owner | pinned DeepSeek Flash, high reasoning effort (Fabro stage policy) |
| External T039/T040 inspection | separate workflow; not performed here |
| T041 user acceptance and merge | separate gates; not authorized or performed here |

The R5 independent review found no new runtime defect; it required three minor documentation-precision corrections
within `T039-F09`: `F09-R5-A` (durable-lease wording), `F09-R5-B` (unqualified bounded shutdown wording), and
`F09-R5-C` (literal no-compiled-token claim). This repair addresses only those three findings.

## 2. Correction F09-R5-A — lease identity is current session state

**Finding.** `QuerySession` documented its response as including a durable lease identity. The implementation
(`GatewaySession::QuerySession` in `src/xverse/xcom/src/tool_gateway.cpp`) reports `lease_id` only from the
in-memory `lease_id_` while `lease_held_` is true; the durable journal lookup in the same function concerns
stimulation intents and outcomes. No lease-identity persistence across session reconstruction exists.

**Correction (documentation comment only).** `src/xverse/xcom/include/xverse/xcom/tool_gateway_grpc.hpp` now
documents, on `GatewayGrpcService::QuerySession`:

- the reported `lease_id` is the current in-memory, session-scoped lease identity, reported only while a lease is
  held, that is not persisted and does not survive session or process termination;
- durable stimulation-outcome reconciliation is described separately, including that an absent durable intent
  leaves the outcome unknown and does not authorize a retry.

No durable lease is claimed and no runtime behavior changed.

## 3. Correction F09-R5-B — shutdown grace is qualified

**Finding.** The generated `tool_gateway_grpc.cpp` file block described an unqualified "bounded server shutdown and
destructor cleanup". The destructor requests gRPC shutdown with a 100 ms grace deadline, then joins the poller,
disconnects the session, and unlinks the socket. That deadline bounds the grace period before forced cancellation,
not completion of arbitrary executing callbacks or of the whole destructor.

**Correction (documentation comments only).**

- `src/xverse/xcom/src/tool_gateway_grpc.cpp` file `@details` now states that the 100 ms deadline bounds only the
  grace period before forced cancellation, does not preempt or bound an executing RPC callback, and that destructor
  completion still requires those callbacks to return.
- `src/xverse/xcom/include/xverse/xcom/tool_gateway_grpc.hpp` qualifies the `GatewayGrpcServer` `@lifetime` clause
  and documents the destructor with the same limitation.

The preserved repair limitations already recorded the same callback-completion qualification; this restores
consistency. No callback preemption and no fixed total destruction bound are promised, and no shutdown runtime test
was added.

## 4. Correction F09-R5-C — change-identity wording is precise

**Finding.** The successor descriptions in `engineering/requirements/T037-SR-001.json` and
`engineering/requirements/T037-SR-002.json` claimed that no compiled token changed. The R5 documentation
completion added 33 parameter identifiers across the eleven adapter RPC declarations (11 `context`, 11 `request`,
nine `response`, two `writer`) so that the required `@param` clauses bind. The declaration clarification was already
disclosed and does not alter a function type, override, ABI, compiled statement, or behavior.

**Correction (documentation text only).** The two successor descriptions and the T037 addendum
`docs/engineering/xcom/t037/implementation.md` now state that no function type, compiled statement, control flow, or
accepted runtime behavior changed, and disclose the 33 inert parameter identifiers. The original requirement
statements, revisions, and historical records are unchanged.

## 5. Change set

| Path | Change |
| --- | --- |
| `src/xverse/xcom/include/xverse/xcom/tool_gateway_grpc.hpp` | Comments only: `QuerySession` response contract; `GatewayGrpcServer` lifetime and destructor qualification. |
| `src/xverse/xcom/src/tool_gateway_grpc.cpp` | Comments only: file `@details` shutdown qualification. |
| `engineering/requirements/T037-SR-001.json`, `T037-SR-002.json` | Successor description corrected; requirement text, revision, and links unchanged. |
| `docs/engineering/xcom/t037/implementation.md` | Additive R6 precision section; the inaccurate blanket phrase in the R5 addendum corrected. |
| `specs/007-xcom-core/tasks.md` | Status paragraph updated to record R4/R5/R6 without changing any task checkbox. |
| `engineering/trace/links.json` | Refreshed `implemented_by` hash pins for the three changed implementation/checker targets. |
| `scripts/check_doxygen.py` | Top-level `BASELINE_REVISION` readmitted to `25a9990b…`; `ADMITTED_INPUTS` unchanged; no logic change. |
| `reports/xcom-queue/t037-doxygen.json`, `t036-benchmark.json`, `t038-traceability.json` | Regenerated exact-candidate evidence. |
| `docs/engineering/xcom/t038/r6-repair.md` | This record. |

No runtime code, compiled declaration, parameter name, CMake, proto, generated service, or test byte changed, and
`tests/xcom/tool_gateway/gateway_support.hpp` remains byte-identical (SHA-256
`2559ead663bb0c25d5190bc949a3fb18b6096a2e49c90512e8a81ba3fa1a3aa5`).

## 6. Focused evidence

All commands below executed in the source worker checkout at `HEAD == 25a9990b86c39408e75381ed5d4aa3d29fc453a7`
with the admitted offline toolchain and no bytecode-cache writes.

| Command (repository-relative or placeholder) | Outcome |
| --- | --- |
| `python3 scripts/check_doxygen.py --strict-cpp` | pass; exit `0`, `35` indexed files, `0` warnings, `0` coverage gaps |
| `python3 scripts/check_doxygen.py --report reports/xcom-queue/t037-doxygen.json` | pass; exit `0`; repository route `173` indexed files, strict route `35`, both `0` warnings; digest `9f63a422…` |
| `python3 ${XVERSE_FABRIC_ROOT}/automation/check_xcom_t039_r6_doxygen.py` | pass; `82` material inputs, digest `9f63a422…`, six negative evidence probes, synthetic omission self-test passed |
| `python3 engineering/run_xcom_benchmarks.py --report reports/xcom-queue/t036-benchmark.json` | pass; digest `a0dfc7d0…`, latency regression `1.7497358072172453%`, throughput regression `1.7196465360189372%` |
| `python3 engineering/run_xcom_benchmarks.py --verify reports/xcom-queue/t036-benchmark.json` | pass; working-tree candidate state |
| `python3 engineering/check_xcom_traceability.py --report reports/xcom-queue/t038-traceability.json` | pass; digest `d22a4aab…` |
| `python3 engineering/check_xcom_traceability.py --verify reports/xcom-queue/t038-traceability.json` | pass; `322` requirements, `2780` resolved edges, `20` REF-002 IDs, `promoted` empty, public-safety verdict `pass` |
| `python3 engineering/check_xcom_traceability.py --self-test` | pass; positive fixture and NEG-01…NEG-07 behave as declared |
| external closure probe `negative_trace_probes()` from `${XVERSE_FABRIC_ROOT}` | pass; predecessor edge rejected (exit `2`), excluded host path rejected (exit `5`) |
| comment-stripped comparison of each changed C++ file against `HEAD` | token-identical; the C++ edits are comments only |

The T037 report binds `baseline_revision` `25a9990b…` and `candidate_revision` `null`, the sorted 82-input material
inventory, and the material digest `9f63a422a224b1036422f1b824b11e1227a327d8d219d68b1f73b0d0349dcfd9`. The T036 report
digest is `a0dfc7d0b739f3cda69c4d2ebf725b6ec17b728a7899b3e97b7c760fcbe33353`; the T038 report digest is
`d22a4aab8ccadca586d977a72678fc2b6455aed12ca93c6a48d5298ee189e997`. All three accept `HEAD == baseline_revision`
or `HEAD` as the direct child of `baseline_revision` and reject every other revision.

The admitted-input identity records the linked-gRPC prefix, the package manifest (SHA-256 `9879911b…`), and the
GTest prefix by name only. `T037-OPEN-06` remains open: the exploratory global `--self-test --coverage-only` route
is not claimed passing, and no global Python docstring coverage is asserted.

## 7. Refreshed trace pins

The changed `implemented_by` hash pins were refreshed to the exact successor file digests; no edge was removed and
no predecessor scope was weakened:

| Target | Refreshed SHA-256 | Edges |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/tool_gateway_grpc.hpp` | `20b98a454a3b930fcaf03f3954a5adf8fd09607c22ce9ac3a44e322bb7fbf0d0` | 4 |
| `src/xverse/xcom/src/tool_gateway_grpc.cpp` | `bb4f5a5db894c3bb785f34bf0698d365f74fb82d20345ca775ec7970f621acc6` | 4 |
| `scripts/check_doxygen.py` | `59f55c7a45ec2d0a395e5686b421b3759dd4e6c02a75743d1de874133640152c` | 6 |

## 8. Preserved boundaries

- **F01–F08 preserved.** Sanitizer instrumentation with `GRPC_ASAN_SUPPRESSED=1` and no `-fno-sanitize` site (F01);
  the single-matching-watch logical-owner boundary (F02); post-commit reconciliation and pre-dispatch transport
  probes (F03); signed deadline saturation (F04); explicit transport status for rejected observation reads (F05);
  live-watch shutdown (F06); the single-owned-lease boundary with the retained original identity (F07); and the
  session-scoped strictly monotonic non-aliasing allocation identity with the `gw.lease.exhausted` exhaustion
  decline (F08). `src/xverse/xcom/src/tool_gateway.cpp`, `tests/`, `proto/`, and the CMake inputs are byte-unchanged.
- **REF-002 dispositions preserved.** The REF-002 capability disposition remains `unchanged` with `promoted` empty;
  no allocated or deferred target is promoted.
- **Generated-service provenance preserved.** Both generated services remain reproducible from unchanged inputs:
  `proto/xverse/xcom/v1/tool_gateway.proto` SHA-256
  `90e56f82d1251f04732dfaa5003597dfc43b7cfe3212e33b5507cd9e04cf289f` and
  `proto/xverse/xcom/v1/gateway_liveness.proto` SHA-256
  `a649602b5de394da89eebdd1135f67583ff76a24c11ad86f9a1060f25f1da527`.
- **Historical records preserved.** The R3/R4/R5 review, repair, and package records keep their original identities
  and are not relabelled as current.

## 9. Provenance and limitations

Only the deterministic `verify`/`closure_gate` nodes and the trusted measures run by the successor workflow
re-execute the strict documentation route, the current-evidence verifier, and the suites after packaging; this
record declares their locations and does not claim their outcomes. Of the candidate measures, only the integration
measure assembles and executes in the declared isolated target-repository worktree; the other measures, including
the ones recorded above, execute in the source worker checkout. Host checker commands are named through the
`${XVERSE_FABRIC_ROOT}` placeholder and no absolute host path is recorded.

This repair addresses `T039-F09` precision only. It does not complete T039 or T040, does not perform the external
T039/T040 inspection or the T041 acceptance, does not accept or merge the candidate, and makes no
production-readiness, compatibility, parity, deployed-service, or certification claim. External T039/T040 review
and T041 user acceptance remain separate and open.
