# Bounded runtime lane: the nine actual process cases

Status: **implementation candidate; owned component boundaries only; not an admitted M1 run,
not acceptance, not a scientific result.** 2026-10-20.

The 024 validation matrices and `xverse.maestro.runtime_admission.RUNTIME_CASES` name nine
runtime case identifiers: `test_affa`, `test_trusted_launcher`, `test_prbc`,
`test_bounded_bootstrap`, `test_atomic_release_cancel_stage`, `test_lease_loss`,
`test_pre_handle_crash_survival`, `test_residual_membership`, `test_unrelated_sentinel`.
Their historical definitions (queue `maestro-queue-20261003-r4`, run
`01M40T958E94TJX2M2ZEHR3F9J`, module `test_runtime_actual.py`, verdict rework) were written
against a superseded API (`FenceAuthority`, `TrustedLauncher`, `Broker`). This candidate
re-implements them against the current composition.

## Allocation

| Identifier | Module | Real children and helper path | Observation that closes the case |
| --- | --- | --- | --- |
| test_affa | tests/thesis_lite/maestro/test_runtime_actual.py | two frozen units staged/armed through the native AFFA authority (`run_authority.c`), one released | Release executes exactly once (`EXEC`), explicit Cancel advances the epoch, later and replayed Releases are REJECTED with no second workload |
| test_trusted_launcher | same | native release gate (`lease_guard.c`, RG06) over a frozen child | boundary stays frozen until the one-use gate Release; Cancel refreezes (epoch 8); a replayed ticket cannot reach the gate; certified membership unchanged; force cleanup observed |
| test_prbc | same | frozen child with no acknowledged handle; a reservation without child | cleanup-only authority terminates the never-thawed child (no `M` byte ever written); reservation releases without a termination claim |
| test_bounded_bootstrap | same | original bootstrap launcher (`bootstrap.c`) supervisor | registered, drained and reaped within the finite deadline; inert joint pins keep `ready_for_execution` false; a foreign facility pin is rejected |
| test_atomic_release_cancel_stage | tests/thesis_lite/maestro/test_composed_authority_interruptions.py | whole original lifecycle, cancel at five Stage/Release windows | at most one workload release, never both outcomes; exact closure facts (unchanged, see composed-authority-interruptions.md) |
| test_lease_loss | test_runtime_actual.py | release gate with a 0.4 s lease, armed ticket | native expiry (kind 18, reason LEASE=1, epoch 8) with no Python service; the armed ticket is dead; membership preserved; force cleanup observed |
| test_pre_handle_crash_survival | test_composed_authority_interruptions.py | authority/storage helper killed before handle acknowledgement | no fabricated handle, cleanup-only closure (unchanged) |
| test_residual_membership | test_runtime_actual.py | boundary fixture in `descendant` mode: leader forks a descendant and exits | certified membership after refreeze equals the live descendant set, excludes the dead leader; force cleanup observes termination; descendants gone |
| test_unrelated_sentinel | test_runtime_actual.py | sentinel heartbeat in a separate boundary for every case, plus a thawed target | target teardown observed; sentinel members, boundary identity and fresh heartbeat unchanged; sentinel PIDs alive |

Every lane case runs the unrelated heartbeat sentinel before and after and retains a
JSON receipt `runtime-actual-<case>.json` under `MAESTRO_BOUNDARY_RECEIPTS` with the
sentinel observations, the retained records projected to JSON (bytes as hex) and explicit
`admitted_m1_run=false`, `full_runtime_lane_complete=false`, `accepted=false` flags.

## What the lane establishes and what it does not

- Established: each named behaviour is exercised with real owned child processes inside
  private frozen cgroup boundaries through the reviewed native helpers, with the sentinel
  as the unintended-target control, repeatable in the component harness.
- Not established: the IR-ML3-04 activation prerequisites (independent frozen review of
  the exact helper bytes and a separately admitted bounded trusted runtime lane with pinned
  image/helper/provider identities), actual M1 admission, whole-platform acceptance,
  kernel-level containment guarantees under uninterruptible failure, or any thesis claim.
  The facility attestation still carries synthetic `SYNTHETIC-NOT-EXECUTED` receipts for the
  nine cases in the admission tests; binding real lane receipts into an admission is a
  separate, author-gated step.

## Verification evidence

Component verification of this module runs in the source phase (candidate `src` on
`PYTHONPATH`) and the installed-wheel phase (the exact candidate wheel in the prepared
verification environment, tests copied outside the source tree). See
`evidence/affa17/runtime-lane-20261020a/` when present; counts there are the authority,
not this page. Scratch iterations before integration are not evidence.

## IR-ML3-04 prerequisites: status 2026-10-20 (finding 381)

- Independent frozen review of the exact helper bytes: **recorded**,
  `evidence/affa17/helper-bytes-independent-review-20261020.{json,md}` (separate agent session,
  read-only; six properties ENFORCED, independent-watchdog PARTIALLY_ENFORCED; 0 HIGH, 2 MEDIUM,
  5 LOW, 9 NOTE). The two MEDIUM observations (authority refreeze skipped once the request
  deadline elapsed; ADVANCE without native watch proof) await the author's disposition.
- Separately admitted bounded lane with pinned identities: **proposed, not activated**,
  `evidence/affa17/lane-admission-proposal-20261020.json` carries real helper digests, the nine
  case receipts (two as composed-case indexes), environment/implementation/design pins, the
  kernel identity and both review digests through the product's own canonicalisation; it calls no
  admission function and keeps execution_approved false. Activating a bounded lane admission
  test, M1 admission and acceptance remain author decisions.
