# T038 delivery envelope — accepted-delivery documentation reconciliation

This is the T038 delivery-envelope successor record for the bounded documentation and evidence
reconciliation authorized after the X-COM gateway delivery was accepted and merged. It reconciles the
current capability 007 task projection and the X-COM subsystem maturity with the real accepted
baseline `48e85051a419fe1c193afaa47cef40b1e7457fdf`, derives a portable projection of the exact sealed
originals, and refreshes the affected current evidence.

It does not reopen the runtime repair, implement an adjacent platform capability, or change any
production source, test, proto, or build input. This successor is itself a candidate: it requires its
own separate review and explicit acceptance, and acceptance of the later documentation successor is a
separate record. Nothing in this record is a fresh execution of the historical baseline runs; the
original evidence stays bound to its own identities.

## 1. Authorization and identity boundary

| Field | Value |
| --- | --- |
| Task | T038 (capability 007, Phase 8 delivery envelope) |
| Admitted baseline (this run) | `48e85051a419fe1c193afaa47cef40b1e7457fdf` |
| Accepted gateway candidate and resulting platform main | `48e85051a419fe1c193afaa47cef40b1e7457fdf` |
| Prior platform main revision | `a9c6e5d41e65625ed2b8c6f5a4457e10c6fcb090` |
| Sealed independent review (T039) | `docs/reviews/t039-r6-independent-review-2026-09-30.md` |
| Sealed terminal inspection (T040) | `docs/reviews/t040-r6-terminal-inspection-2026-09-30.md` |
| Sealed approval receipt (T041) | `automation/reviews/t041-gateway-repair-acceptance-20260930/approval.json` |
| Sealed delivery receipt | `automation/reviews/t041-gateway-repair-acceptance-20260930/delivery/delivery.json` |
| Sealed delivery report | `docs/reviews/t041-gateway-repair-delivery-2026-09-30.md` |
| Repair owner | pinned DeepSeek Flash, high reasoning effort (Fabro stage policy) |
| External T039/T040 review and T041 acceptance of this successor | separate gates; not performed or claimed here |

## 2. BT-01 — capability 007 task projection reconciled

The current projection reconciles the pre-acceptance task state with the sealed approval and the
actual delivered main commit:

- `specs/007-xcom-core/tasks.md` now marks T039, T040, and T041 complete (`- [X]`) for the accepted
  gateway baseline and records a **current status** paragraph naming the approved commit
  `48e85051a419fe1c193afaa47cef40b1e7457fdf`, the sealed originals, and the portable projection.
- The R2–R6 pre-acceptance statements are retained under an explicit **historical** label and are not
  rewritten or relabelled as current; the paragraph is scoped to the R6 checkpoint it describes.
- The record states that the documentation/evidence reconciliation is itself a separate successor
  candidate that still requires its own review and explicit acceptance. It does not imply that this
  successor is accepted or merged, and it does not claim a fresh execution of the historical runs.

## 3. BT-02 — X-COM subsystem maturity corrected

`docs/architecture/PLATFORM_SUBSYSTEMS.md` previously described X-COM as the next platform-first
capability with no runtime. The corrected row records X-COM as an **accepted bounded prototype** in
`src/xverse/xcom` comprising the implemented capability 007 communication, observation, stimulation,
and local-IPC/gRPC tool-gateway boundaries, with the sealed gateway acceptance and the recorded
F01–F09 qualifications and limitations. The generic platform core/runtime, Maestro, Argus,
simulation/FMI, devices, security, results, UI/SDK/CLI, production readiness, and legacy compatibility
remain distinct architectural targets. No package was scaffolded and no REF-002 allocation was
promoted.

## 4. Derived acceptance/delivery projection

A portable, explicitly DERIVED projection of the sealed originals was added at
`docs/engineering/xcom/accepted-delivery-20260930/projection.json` with a `README.md`. The projection
is `schema_version` 1, `kind` `derived_acceptance_delivery_projection`, `derived` true, and
`acceptance_attestation_scope` `accepted_gateway_baseline_only`. It carries the accepted candidate and
resulting main commit, `user_approval` `approved`, the three external-task statuses, and eight
`source_refs` entries that name the original repository, the repository-relative path, and the frozen
SHA-256 of each original. It is a projection only; the originals are not edited or substituted, and
the projection does not attest any later documentation successor.

## 5. Change set

| Path | Change |
| --- | --- |
| `specs/007-xcom-core/tasks.md` | T039–T041 checked; current status paragraph added; pre-acceptance statements retained under a historical label. |
| `docs/architecture/PLATFORM_SUBSYSTEMS.md` | X-COM row corrected to the accepted bounded prototype with distinct retained architectural targets. |
| `docs/engineering/xcom/accepted-delivery-20260930/projection.json` | New DERIVED portable projection of the sealed originals. |
| `docs/engineering/xcom/accepted-delivery-20260930/README.md` | New projection README with source references and retained limitations. |
| `reports/review-index.md` | Appended current baseline-delivery projection; earlier sections retained as historical. |
| `docs/engineering/xcom/t037/implementation.md` | Additive successor addendum recording the refreshed T037 evidence identity. |
| `scripts/check_doxygen.py` | Top-level `BASELINE_REVISION` readmitted to `48e8505…`; `ADMITTED_INPUTS` unchanged; no logic change. |
| `engineering/trace/links.json` | Refreshed the six `implemented_by` hash pins for `scripts/check_doxygen.py`; no edge added or removed. |
| `reports/xcom-queue/t037-doxygen.json`, `t036-benchmark.json`, `t038-traceability.json` | Regenerated exact-candidate evidence bound to the successor material identity. |
| `docs/engineering/xcom/t038/delivery-reconciliation.md` | This record. |

## 6. Focused evidence

All commands below executed in the source worker checkout at `HEAD == 48e8505…` with the admitted
offline toolchain, `PYTHONDONTWRITEBYTECODE=1`, and no bytecode-cache writes.

| Command (repository-relative or placeholder) | Outcome |
| --- | --- |
| `python3 scripts/check_doxygen.py --report reports/xcom-queue/t037-doxygen.json` | pass; exit `0`; repository route `173` indexed files, strict route `35`, both `0` warnings; `0` coverage gaps |
| `python3 scripts/check_doxygen.py --strict-cpp` | pass; exit `0`, `35` indexed files, `0` warnings, `0` coverage gaps |
| `python3 ${XVERSE_FABRIC_ROOT}/automation/check_xcom_delivery_reconciliation_doxygen.py` | pass; `82` material inputs, digest `df82b1bb…`, six negative evidence probes, synthetic omission self-test passed |
| `python3 engineering/run_xcom_benchmarks.py --report reports/xcom-queue/t036-benchmark.json` | pass; digest `7b730223…`, latency regression `0.8502644432241802%`, throughput regression `0.8430958985763071%` |
| `python3 engineering/run_xcom_benchmarks.py --verify reports/xcom-queue/t036-benchmark.json` | pass; working-tree candidate state |
| `python3 engineering/check_xcom_traceability.py --report reports/xcom-queue/t038-traceability.json` | pass; digest `ff5f6ed1…` |
| `python3 engineering/check_xcom_traceability.py --verify reports/xcom-queue/t038-traceability.json` | pass; `322` requirements, `2780` resolved edges, `20` REF-002 IDs, `promoted` empty, public-safety verdict `pass` |
| `python3 engineering/check_xcom_traceability.py --self-test` | pass; positive fixture and NEG-01…NEG-07 behave as declared |
| external closure probe `negative_trace_probes()` from `${XVERSE_FABRIC_ROOT}` | pass; predecessor edge rejected (exit `2`), excluded host path rejected (exit `5`) |
| `python3 ${XVERSE_FABRIC_ROOT}/automation/check_xcom_delivery_reconciliation.py` | pass; eight original sources verified, four negative projection probes, runtime/code/tests/build/proto unchanged |
| `git diff --check` | clean |

Report identities bound to the successor material:

| Report | Baseline | Material digest | Material inputs | Report SHA-256 |
| --- | --- | --- | --- | --- |
| `reports/xcom-queue/t037-doxygen.json` | `48e8505…` | `df82b1bb979da4cfacdc1d739d143b56c88e5a53364323e087d00d77462d44bd` | `82` | `09738efacdd94d0278c1ffa5c15aa64f867ffe0dda29506c406ae60b3647e93b` |
| `reports/xcom-queue/t036-benchmark.json` | `48e8505…` | `7b7302239b3be2bec97ee3b814fb7141a25baa149cf4a35cb5d7893c3b28910c` | `53` | `443bf40d02e8e6c2deb929b50c9fd8d2ec0548ee4e0576f2f67064033552afb4` |
| `reports/xcom-queue/t038-traceability.json` | `48e8505…` | `ff5f6ed1425000d296ea2d859d93659035596a2c1730cc4a7a6d8c6f8eb0fcf3` | `54` | `ce16cdcf8dc4db9efa025cc7450206e5208ea26e30fddfe67c85cc3ce1d5022a` |

Each report records `candidate_revision` `null` and binds the exact candidate by `baseline_revision`
plus the sorted material inventory, the material digest, and the per-file hashes; each `--verify`
accepts `HEAD == baseline_revision` or `HEAD` as the direct child of `baseline_revision` and rejects
every other revision. The enabled-tap benchmark observation (latency `55.628583601934324%`, throughput
`35.744451510411935%`) remains ungated and is not a production timing claim.

## 7. Refreshed trace pins

The changed checker pin was refreshed to the exact successor file digest; no edge was removed and no
predecessor scope was weakened:

| Target | Refreshed SHA-256 | Edges |
| --- | --- | --- |
| `scripts/check_doxygen.py` | `bc13518d8915be5e32ebc670b7665f0df613a684ea1f2008c732291cb47c8796` | 6 |

## 8. Preserved boundaries

- **Runtime, code, tests, proto, and build unchanged.** `src/**`, `tests/**`, `proto/**`,
  `CMakeLists.txt`, `cmake/**`, the `Doxyfile`, and the generated services are byte-identical to the
  accepted baseline. No validator, gate, or negative check was weakened, and no exclusion was widened.
- **Historical evidence preserved.** The accepted gateway reports, packages, review/repair records,
  and the historical SESN-generated specs 008–020 retain their original identities and are not
  relabelled as current or relaunched from unchecked task counts.
- **REF-002 preserved.** The capability disposition remains `unchanged` with an empty `promoted` list;
  the twenty allocated/deferred targets are unchanged.
- **Generated-service provenance preserved.** Both protos and the generated service outputs remain
  reproducible from unchanged inputs.
- **Limitations retained.** Logical watch association rather than OS peer authentication;
  callback-dependent shutdown after the 100 ms grace; volatile lease identity versus durable recorded
  stimulation outcomes; unknown absent outcome with no implicit retry; full owned compiler sanitizer
  coverage with the admitted prebuilt gRPC ABI qualification; the `T037-OPEN-06` global Python
  docstring limitation; the qualified predecessor conformance replay; and the measured
  disabled/enabled-tap benchmark scope.

## 9. Provenance and limitations

This record declares the focused source-checkout results above; it does not claim the downstream
trusted measures. Of the candidate measures, only the integration measure assembles and executes in
the declared isolated target-repository worktree; the unit, validation, static-analysis, conformance,
and sanitizer measures execute in the source worker checkout and are run by the successor workflow.
Host checker commands are named through the `${XVERSE_FABRIC_ROOT}` placeholder and no absolute host
path is recorded.

The global Python `--self-test --coverage-only` limitation (`T037-OPEN-06`) remains open and is not
claimed as passing. This successor makes no production-readiness, deployed-service,
legacy-compatibility, parity, or certification claim. It does not accept or merge itself: a separate
review and explicit acceptance are required, and the accepted gateway delivery remains the accepted
baseline at `48e85051a419fe1c193afaa47cef40b1e7457fdf`.
