# Independent review of the F-01 change to run_authority.c (2026-10-20)

Reviewer: separate agent session (Claude, independent of the change author). Date: 2026-10-20. Repository: `/home/jefferson/xverse-platform-worktrees/maestro-lite-affa18-20261020`, branch `candidate/maestro-lite-affa18-20261020` (change uncommitted). Machine-readable twin: `helper-change-f01-independent-review-20261020.json`.

Method: read-only source reading of the diff, the old and new helper, review-affa18.md findings 394-395, the affa17 independent review, and the Python protocol, client and CANCEL/REJECTED consumers. Both sources were compiled in /dev/shm (never executed); the harness-named build reproduces binary `40fa39ee34d96c93555a8daf88e52d14a62e1ba52abc2e05bb9173535a92dcbf` (finding 395). No existing file was modified and pytest was not run.

## Frozen inputs

| Version | SHA-256 | Verified |
| --- | --- | --- |
| HEAD `src/xverse/maestro/native/run_authority.c` | `2a2ee8306a7f45186355b548888d00e3df9fd22f20fd9fbe9435afa718874563` | yes |
| working tree `src/xverse/maestro/native/run_authority.c` | `7fde44db52c661d7c27b21986ca63e7185cab40d824c74869dd0c0a1c2acece0` | yes |

## Verdict: F-01 addressed

The cgroup.freeze write is issued for every live generation regardless of budget (162), the wait is bounded (164-167), and the rejection path (520) and CANCEL (394) use an independent min(generation, now+2 s) budget; cleanup() and the lease-expiry path already used fresh budgets. Residual items are LOW/NOTE and conservative in direction; the REJECTED freeze mask remains deferred with F-05.

Checks: 16 PASS, 0 FAIL, 4 NOTE. Deferred items F-02, F-05 and F-07 in finding 394 are described accurately against the code. One wording point: the 0..7 reason bound is `affa_protocol.py:87`; line 108 enforces a non-zero reason and zero state on REJECTED. The REJECTED reason is not read by `affa_client.py:288-289`, so the new reason 6 does not change client behaviour.

## Findings by severity

HIGH: 0. MEDIUM: 0. LOW: 3. NOTE: 5.

- **F01R-01 [LOW]** CANCEL (and REJECTED) reply can now arrive after the caller's receive deadline when freezing is slow (`src/xverse/maestro/native/run_authority.c`:182, 394 (callers: src/xverse/maestro/run_broker.py:884, src/xverse/maestro/affa_client.py:156-158, 338-341, 388-401)). Record the trade-off in the review log, or bound the CANCEL wait by the request deadline (now sufficient for F-01 because the write is unconditional) while keeping close_end for the rejection path; in either case state which reply-timing guarantee the CANCEL receipt carries.
- **F01R-02 [LOW]** Freeze writes are serialised behind each unit's wait; units after an exhausted budget are never read (`src/xverse/maestro/native/run_authority.c`:155-172). Use two passes: issue every cgroup.freeze write first, then wait for frozen==1 under the shared budget, reading each unit at least once (do-while) so the mask is not under-reported.
- **F01R-03 [LOW]** Prior F-01 recommendation to retry pending freezes in the closed loop is neither implemented nor recorded as deferred (`src/xverse/maestro/native/run_authority.c`:499-521). Either implement a bounded retry for units not in the last mask or record the item as deferred/declined with rationale in review-affa18.md.
- **F01R-04 [NOTE]** A failed reply send can now trigger up to three successive 2 s close budgets (`src/xverse/maestro/native/run_authority.c`:394-395, 520, 467-469). Optional: return cleanup(g) directly when a reply send fails, or skip the re-close when the authority is already closed and the last mask was complete.
- **F01R-05 [NOTE]** Close activity can extend into the last 2 s of the generation and leave cleanup() an elapsed budget (`src/xverse/maestro/native/run_authority.c`:182, 468-489, 500). None required; document that the authority's close and the supervisor cleanup may overlap in [generation-2 s, generation].
- **F01R-06 [NOTE]** write_freeze()==1 (ENOENT/ENODEV) counted as freeze failure, unlike bootstrap.c (`src/xverse/maestro/native/run_authority.c`:93-96, 113-127, 162). Optional: treat write_freeze()==1 as removed (set the mask bit) for consistency with bootstrap.c, or record the stricter semantics.
- **F01R-07 [NOTE]** Fence-control docstring is stale and the control cannot exercise the new FREEZE_FAILED or bounded-wait branches (`tests/thesis_lite/maestro/test_affa_release_timeout_fence.py`:3-12, 64, 84). Update the docstring; record that the FREEZE_FAILED branch and the bounded wait are untested, or add a control for them.
- **F01R-08 [NOTE]** Pre-existing timing details in the close paths (not introduced by this diff) (`src/xverse/maestro/native/run_authority.c`:55, 166, 182, 501-504). Optional hardening: treat now_ns()==0 as budget exhausted inside the wait loops; recompute now after the lease-expiry close.

## Authority limits

activation_approved: false; m1_admission: false; acceptance: false.

This review is an independent source reading and neither activates the lane, admits M1 nor accepts anything.
