# Independent review of the two-pass freeze_all change to run_authority.c (2026-10-20)

Reviewer: separate agent session (Claude, independent of the change author). Date: 2026-10-20. Repository: `/home/jefferson/xverse-platform-worktrees/maestro-lite-affa18-20261020`, branch `candidate/maestro-lite-affa18-20261020` (change uncommitted). Machine-readable twin: `helper-change-twopass-independent-review-20261020.json`.

Method: read-only source reading of the full diff against HEAD (not only the delta from 7fde44db), review-affa18.md findings 394-397, the prior independent review, and the Python consumers (affa_protocol.py, affa_client.py, run_broker.py CANCEL). Both sources compiled in /dev/shm with the harness flags (never executed). No existing file was modified and pytest was not run.

## Frozen inputs

| Version | SHA-256 | Verified |
| --- | --- | --- |
| HEAD `src/xverse/maestro/native/run_authority.c` | `2a2ee8306a7f45186355b548888d00e3df9fd22f20fd9fbe9435afa718874563` | yes |
| working tree `src/xverse/maestro/native/run_authority.c` | `b29a5239345354c4758f22203c7d38d557596bb2d743e826fa89825bdd60a09f` | yes |
| harness-flag build (not executed) | `17f2476a2d4138415f8563dc41f47bf73501b28b005aede2e640b9c78a5c4af5` | matches finding 397 |

## Verdict: F-01 and F01R-02 addressed

Every live generation's cgroup.freeze write is issued before any wait and regardless of budget (163); one bounded wait reads each pending unit at least once (166-174); still-pending units set freeze_failed (175); CANCEL and the rejection path use close_end = min(generation, now+2 s) (187, 399, 525). The returned mask keeps HEAD's meaning and satisfies affa_client.py:303. No regression on CANCEL, rejection, lease-expiry or cleanup paths beyond the recorded F01R-01 timing trade-off. Residual items are one LOW (sticky reason-6 semantics versus the wording of findings 395/397) and NOTEs, all conservative in direction.

Checks: 19 PASS, 0 FAIL, 4 NOTE. Findings 394, 396 and 397 describe the code accurately, including the deferrals of F-02, F-05, F-07 and F01R-03; finding 395's description of reason 6 is narrower than the code (TPR-01).

## Findings by severity

HIGH: 0. MEDIUM: 0. LOW: 1. NOTE: 5.

- **TPR-01 [LOW]** freeze_failed is sticky, so reason 6 reports any earlier unconfirmed freeze, not only the current refreeze (`src/xverse/maestro/native/run_authority.c`:34, 51, 163, 175, 400, 525 (consumer run_broker.py:902)). Either record in the review log that reason 6 (on REJECTED and CANCELLED) and cleanup's exit 70 reflect a sticky, authority-lifetime freeze failure, or have freeze_all report a per-call failure for the reply reason while keeping the sticky flag for cleanup(). Do not clear the sticky flag without a recorded rationale.
- **TPR-02 [NOTE]** A generation removed after its freeze write stays pending, consumes the budget and is reported unfrozen (`src/xverse/maestro/native/run_authority.c`:162, 167-175). Optional: when field() fails in the wait loop, test removed(e) and, if true, set the mask bit and clear the pending bit; otherwise record the conservative behaviour.
- **TPR-03 [NOTE]** Units whose freeze write fails are never read or retried (`src/xverse/maestro/native/run_authority.c`:93-96, 163). Optional: read cgroup.events once for write-failed units too (or retry the write inside the wait loop) and keep freeze_failed for them; or keep as is and note it alongside F01R-06.
- **TPR-04 [NOTE]** Pre-existing: the wait is unbounded if the monotonic clock fails, and busy-spins when the parent has exited (`src/xverse/maestro/native/run_authority.c`:55, 172-173, 187, 473). Optional hardening: treat now_ns()==0 as budget exhausted in the exit test at 172; consider a sleep that does not depend on g->parent (e.g. poll(NULL,0,1)) when the parent pidfd is already readable.
- **TPR-05 [NOTE]** Rejection-path wait can be shorter than in HEAD (`src/xverse/maestro/native/run_authority.c`:525 (HEAD:520)). None required; mention in the review log that the rejection-path confirmation window is capped at 2 s.
- **TPR-06 [NOTE]** Close-budget formula is written three times (`src/xverse/maestro/native/run_authority.c`:187, 473, 506). Optional: call close_end(g) from cleanup() and the lease-expiry path.

## Authority limits

activation_approved: false; m1_admission: false; acceptance: false.

This review is an independent source reading and neither activates the lane, admits M1 nor accepts anything.
