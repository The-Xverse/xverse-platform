# U3 worker-monitor review

Revision under review: ML3-SUPERVISION3-2026-10-18-v1, uncommitted overlay on c2997c0.
Same-agent separate read-only review; not an independent agent or factory review.
First verification: 48 component tests passed. No full ML3 runtime case executed.

Findings recorded before repair:

1. **SUP-REV-01, MAJOR:** `waitid` or select failure before the deadline returned
   unresolved without closing the shared latch. A second worker could therefore
   remain active in the same monitor context. Every uncertain monitoring outcome
   must fail close independently of journal/provider work. Add a direct counterexample.
2. **SUP-REV-02, MAJOR:** the retained slot kept the caller's `WatchLimits` object.
   Frozen dataclasses discourage mutation but do not snapshot caller state; an altered
   poll/TERM value could affect later monitoring. Reconstruct and privately retain
   validated immutable values at registration; test post-registration replacement.
3. **SUP-REV-03, MINOR:** `dispose_reaped` only checked pidfd exit readiness. A still
   unreaped zombie could lose its retained descriptor. Confirm nonblocking reaping
   (or exact exit plus no remaining parent wait record) before disposing. Cached
   unresolved observations must never be promoted or rewritten as normal success.
4. **SUP-REV-04, MINOR:** the ADR initially listed ML-SR-007/008 as implemented scope.
   Worker exit observation does not implement live generation probes/readiness or
   health cadence. Link this increment only as partial ML-SR-009/011/023/024 work;
   retain ownership/cleanup requirements as constraints and all full closures open.

Runtime limitations remain material: no helper-creation bound, actual launch fence,
supervisor-loss lease, C1, descendant containment, admitted bootstrap artifacts,
authenticated owner approvals, U5 integration, Argus coverage or full runtime proof.
Kernel calls and host scheduling are not hard-real-time bounded by Python. The
owner must supply an actual original child before dispatch, prevent competing waiters
and keep its private registry; type checks are not authenticated origin evidence.

Second read-only pass, after the first repairs: 55 component checks pass. SUP-REV-01
and 03 have recorded failing counterexamples; SUP-REV-02 has snapshot/wait checks,
and SUP-REV-04 is corrected in the ADR. These repairs are component changes only.

5. **SUP-REV-05, MAJOR:** the cancellation loop sampled host time before nonblocking
   waitid and reused it for the signal deadline check. A descheduled/delayed observer
   could therefore send TERM after the retained final bound. Recheck monotonic time
   after observation and immediately before the signal guard; test delay across the
   whole lease. Userspace guards still cannot make a kernel-enforced lease guarantee
   across preemption after the final check. That guarantee remains an explicit M1/U4
   admission gate, never evidence supplied by this worker-only component.

## Final read-only disposition

Candidate: ML3-SUPERVISION3-2026-10-18-v3. All five recorded component findings
are repaired within the stated worker-only scope. SUP-REV-05's delayed-observer
counterexample failed before repair and passes afterward. Pre-review v1/v2 archives
and their file manifests verify; the original 76-file U2 worktree is unchanged.
The successor changes its copied engineering README deliberately; 75 other inherited
files remain exact. No independent full-candidate review or acceptance is inferred.

Final checks: 749 platform Python tests and 24 subtests; 170 source-excluded wheel
checks; eight installed module hashes match. The 170 source feature checks include
56 new worker-monitor cases. Ruff and partial endpoint/hash/AST checks pass. All
22 frozen source/test/verifier inputs match before and after verification. All 24
software requirements and 18 unvalidated allocation-only/null-mapped parents remain.
No full requirement closure, complete engineering trace or C++ run is claimed.

The verification launcher initially resolved a virtualenv symlink to the host Python;
the installed-identity assertion stopped before tests. Its correction preserves the
virtualenv entry path. The first broad run then exposed a missing `build` dependency
in the new verification environment: 13 predecessor Argus wheel-build checks failed,
while 736 tests and 24 subtests passed. `environment-attempt1/` retains that exact
source, command, environment and failure record. Installing the predecessor's pinned
build tools required no software-source repair; the repeated exact run passes.

The full runtime limitations listed above remain open. Main's tracked revision is
unchanged at c2997c0; unrelated untracked main review files are preserved. No factory
run, scientific experiment, canonical-note edit, acceptance, commit or merge occurred.
Next: actual U3 helper/fence supervision and U4 descriptor/C1 containment under fresh
admission, retaining the original-holder and kernel-enforcement gates. Sol/high is
recommended for that authority/concurrency work; it is not a claimed model switch.
