# Independent review of the Maestro Lite increment17 candidate (committed state b03633329)

Reviewer: separate agent session (Claude, independent of the increment's implementer).
Date: 2026-10-20. Reviewed state: branch `candidate/maestro-lite-affa17-20261018` at HEAD
`b036333291a547e63642806b6d34e00b993fdfc7`. Method: read-only reading of the committed record
and evidence; SHA-256 recomputed with `sha256sum`; the two CAPA validators run with `python3 -I`;
no test run, no compilation, nothing modified or created other than this file and its JSON
companion (`increment17-independent-review-20261020.json`). The uncommitted working tree
(finding 385 in review-affa17.md, the ENVIRONMENT_DIGEST edit of test_runtime_entry.py, the two
untracked test modules and the run-l directory) was read for context only and is not part of the
reviewed state. The brief named findings 357 through 385; the committed log ends at finding 384.

## Verdict counts

38 checks: **30 PASS, 3 FAIL, 5 NOTE**. 3 blocking findings, 9 non-blocking findings.

What passed, in short: every file hash quoted with a prefix in findings 376 through 384 and in
the README recomputes to the quoted value (run i, j, k receipts, logs and triage files; the run-k
register; the helper-bytes review; the lane admission proposal and receipt; the endpoint review,
proposal v2 and re-bound trace; the sign-off and decisions records; the thesis-side source-parent
v4 register; the four helper sources; the git-archive implementation pin; the design manifest; the
environment receipt). The run counts (2096/0, 2096/0, 2 failed/2094 passed), the probe spike
counts (0, 0, 9 with worst 1.1804 s), the GC maxima, the stall correlations, the nested-child
result (3 failed/1809 passed) and the run-k expired-statement timeline (unit-disposition,
0.300 s budget overrun by 0.4 ms, ML-PERSIST-TIMEOUT) all match the record. The run-k register
validates (49 records, 359 bindings; parent run-j 343 bindings preserved, 0 changed, 0 lost);
every state is FIX_CANDIDATE, REJECTED or UNRESOLVED and every effectiveness is
NOT_DEMONSTRATED; all 359 evidence paths exist in HEAD. The product change of finding 379 is a
single hunk in dispatcher.py, clipped by the admitted work window, with no admission constant
changed, and finding 383 bounds its run-k expiry correctly (the expired statement is the
unit-disposition statement, still at the operation budget). The five authority limits
(acceptance, M1, merge, lane activation, scientific claim) are stated consistently across the
README, capa.md, the register, the continuation, the proposal and the thesis tasks.md.

## Blocking findings

**B-01. Finding-384 controls and their fixture edit are absent from the reviewed HEAD.** The
committed record (finding 384, the README run-k section, the commit message and the committed
`lane-admission-20261020b/` evidence) reports 23 passed per phase over
`test_runtime_lane_admission.py` (c7804730…43ca) and `test_affa_release_timeout_fence.py`
(f33d4394…0570) and the ENVIRONMENT_DIGEST edit of `test_runtime_entry.py` (603361be…8e8e), yet
none of the three files is in the commit: two are untracked and one is an uncommitted
modification. The lane-b `frozen-inputs.json` binds their hashes (they equal the working-tree
files), but the evidence directory retains no copy of the bytes, so a reader of HEAD cannot
inspect or reproduce the controls the record cites. The commit message discloses the deferral
("the tests and fixture change of findings 382/384 follow with a clean full run l"), which keeps
the record honest but leaves an acceptance decision on this snapshot resting on evidence whose
producing controls are outside the configuration baseline. Resolution: the fourth checkpoint
commit after run l with the three files at exactly the quoted hashes (any change needs its own
finding and a lane re-run); until then, label finding 384's evidence "controls pending commit".

**B-02. The F-01 owned control does not assert the release-timeout discriminators it is credited
with.** `test_affa_release_timeout_fence.py` asserts that the reply kind is REJECTED, that the
cleanup-only fence released the boundary with termination observed, and that no marker exists
before or after the thaw. It does not assert `reply.reason`, the elapsed time against the 2 s
ticket, or a non-empty residual membership before the fence, which are the facts finding 384(b)
reports and the only facts that distinguish the F-01 path (run_authority.c:358 waits until the
request deadline, then `close_authority` with an elapsed end so `freeze_all` at line 161 skips the
refreeze, then REJECTED with reason 4) from an immediate protocol rejection; reason 4 is
`PROTOCOL`, the generic code emitted after any failed command, not a timeout-specific code. The
retained receipts in lane-b (reply_reason 4, reply_seconds 2.0, members_before_fence one pid,
marker_before_fence false) do support finding 384(b), but the control as written would pass
without exercising F-01, so the finding-382 disposition "documented Python-side precondition
proven by an owned test" is not yet proven by the test itself. Resolution: assert the reason, the
elapsed time against the ticket and the pre-fence membership; re-run the lane driver into a new
evidence directory; only then bind the control to ML-CAPA-381-F01 in the next successor. A
timeout-specific native reason belongs to the queued helper change with new frozen hashes.

**B-03. capa.md attributes the F-01/F-02 disposition to the author although it is an agent
proposal pending author decision.** The run-k paragraph of capa.md reads "author disposition
recorded as documented Python-side preconditions with owned controls (finding 382)". The register
records both corrections as `none_pending_author_disposition`; finding 382 labels the dispositions
as agent proposals under the author's "propose something and go"; the thesis tasks.md states
"Author decisions pending: disposition of the two MEDIUM observations"; the uncommitted finding
385 does not name them. The CAPA narrative therefore overclaims authority provenance on two
UNRESOLVED records that back the IR-ML3-04 prerequisite statement. Resolution: reword to
"agent-proposed disposition (finding 382), pending explicit author confirmation", align the README
sentence ("dispositioned …"), and bind the author's confirmation record when it is given.

## Non-blocking findings

- N-01. Finding 379's statement that the reserve "already counts the terminal step" is true only
  at the operation budget: `schedule_plan.py:161-163` reserves `n·per_unit_seconds` for the
  cleanup and counts the terminal statement among the `(steps + 2n + 2)·operation_seconds` terms;
  after the change the worst-case terminal-section sum exceeds the reserve by
  (per_unit − operation), tolerated only by the `_work_end` clip. Re-derive the reserve under its
  own finding when the 383(d) extension is decided.
- N-02. Finding 374's tolerance of 1e-9 s is tight: with `int(x·1e9)` truncation the bound is
  1 ns + 0.5 ulp(x); a 2·10^6-value scan near 1.05e6 s gave a worst of 9.3e-10 s (no violation),
  but the bound grows with host uptime. Compare at integer-nanosecond resolution or use 2e-9 s;
  the observed 1e-9 s difference is about eight float ulps, not one.
- N-03. The storage-fault expectation of finding 372 is an upper bound (at most one release), so
  a zero-release outcome also passes; the declaration is adequate and the safety property is what
  is asserted, but the docstring "nothing released, nothing fabricated" does not cover the storage
  row.
- N-04. Stale status lines: capa.md's top paragraph still names the reviewer-shape register
  (40/216) as latest; endpoint-reconciliation-gap.md's status line says "author ruling on v2
  pending" while its last section records the acceptance and re-binding; runtime-lane.md's
  IR-ML3-04 section says the MEDIUM observations "await the author's disposition" and the lane
  admission test "remain author decisions" although finding 382 acted; the register's
  ML-CAPA-381-F01 limit "not reproduced at runtime" predates lane-b (09:12 versus 09:14).
- N-05. Finding 381(c) reserved activation of a bounded lane admission test for the author;
  finding 382 activated it as a fail-closed component-harness test under the general proceed
  instruction. The lane-activation limit is respected (no admission performed, execution_approved
  false, `lane_activated` false in both receipts), but the author should explicitly confirm the
  382 dispositions; finding 385 does not.
- N-06. Run k's configuration.json records git_head 1e081a1ba while finding 383 says "snapshot =
  checkpoint 36e6bf13"; content identity is established by the frozen manifest bb80b02c…
  (identical to run j) and the dispatcher.py blob ba8b2eb2… (equal to 36e6bf132); record that the
  git_head field reflects the HEAD at run start.
- N-07. IR-ML3-04 has no located definition in the 024 spec files readable for this review (only
  tasks.md status lines); cite the defining artefact in runtime-lane.md.
- N-08. `verify-capa-register-20261019.py` opens its output with mode `x` and cannot be re-run in
  place once `verification-recheck.json` exists; all assertions passed before the write failed,
  and a print-only re-run reproduced 49/359. Accept an output path so independent re-verification
  needs no mutation or shim.
- N-09. The README header "Product change verified by clean run j" should use the bounded wording
  of its body ("exercised by clean run j; effectiveness NOT_DEMONSTRATED").

## Readiness judgement

In my judgement the increment is **not yet ready for the author's acceptance decision**. The
retained evidence supports every quantitative claim of the record for runs i, j and k, the CAPA
chain is intact with no effectiveness claimed, the product change is correctly scoped and bounded,
and the authority limits are consistently closed. What must be resolved first: the fourth
checkpoint committing the finding-384 controls at their quoted hashes after a clean run l (B-01);
the F-01 control strengthened to assert the timeout discriminators and the lane driver re-run
(B-02); the capa.md attribution corrected and the finding-382 dispositions explicitly confirmed
by the author (B-03, N-05); the authorized 383(d) terminal-section extension applied and verified
under its own finding and full run; and the stale status lines refreshed (N-04). The remaining
acceptance prerequisites recorded by the increment itself (ten unknown-cause CAPA records, the two
helper observations, lane activation, M1, the full 024 scope) are unchanged by this review.

This review is an independent reading of the committed record and neither accepts, admits M1,
activates the lane nor merges anything.
