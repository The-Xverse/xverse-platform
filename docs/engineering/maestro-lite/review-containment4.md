# U4 boundary-component review

Candidate: ML3-CONTAINMENT4-2026-10-18-v1. Separate same-agent read-only review;
not independent full-candidate review. Findings recorded before repairs.

1. **CG-REV-01, MAJOR:** real kernel checks disprove the assumed `st_nlink == 0`
   removal predicate for retained cgroup directory descriptors. Successful rmdir
   stayed unresolved and fixture disposal failed too. First run: 19 passed,
   7 failed, 7 teardown errors. Use successful exact rmdir plus absence of the
   private name and kernel control files beneath the retained original FD; retain
   stable original identity through confirmation. Test clone3 rejection using the
   retained deleted FD. Do not substitute a missing path for original ownership.
2. **CG-REV-02, MAJOR:** the CP-02 reservation-only branch froze the allocation
   before checking it was empty. Reservation authority is only for verified empty,
   never-started allocation release, not freezing or terminating live members.
   Observe the original allocation without mutation first; reject any live/unknown
   membership without C1. Bound and retain this branch separately from full C1.
3. **CG-REV-03, MINOR:** huge integer time limits can raise OverflowError rather
   than the closed admission diagnostic. Validate positive finite limits without
   allowing bools or raw arithmetic exceptions.
4. **CG-REV-04, MAJOR:** the test harness did not persist a root allocation inventory
   before effects, and its teardown repeated the same incorrect removal predicate.
   Retain exact parent/root identity and source/command provenance in a fixture receipt,
   and make cleanup independent of library success. Missing ordinary C1 must remain
   unresolved; external component-test maintenance is not normal C1 recovery or a
   full ML3 runtime measure. Account for the first failed harness's empty roots.
5. **CG-REV-05, MAJOR:** the final Stage cancellation check and returned frozen
   commitment were not serialized with the short independent latch transition.
   Make that final commitment atomic with Cancel without holding the latch across I/O.
6. **CG-REV-06, MAJOR:** losing a registered C1 could fall back to the original
   empty-allocation reservation. CP-02 authority is only for the pre-C1 window;
   after C1 registration, losing it must remain unresolved even for an empty scope.
7. **CG-REV-07, MAJOR:** boundary errors retained unresolved accounting but did not
   close the shared start latch. Close it on partial/unknown failure, while allowing
   original valid cleanup to address its unchanged creation epoch.
8. **CG-REV-08, MAJOR:** a write used a deadline checked before identity/open calls;
   those calls can return after the bound. Recheck immediately before mutation and
   membership commitment. This is still not an atomic kernel lease across preemption.

After repairs, real kernel checks pass 38 cases with two test-assumption failures:
copy.copy is already denied by serialization refusal, and this kernel rejects cgroup
directory rename. Exercise copy refusal explicitly plus a fields-only forged holder;
use actual removal/recreation for the name-substitution fault. These are test repairs,
not permission to change the authority or kernel contract. Repaired harness receipts
show complete root removal and worker reaping for this run.

Next read-only pass: 40 component checks pass, including actual frozen birth,
leader-independent descendant scope, exact kill/remove and rejected clone through
the deleted retained descriptor. Two additional issues require successor repair:

9. **CG-REV-09, MAJOR:** parent validation preceded dup of the caller's FD number.
   Duplicate once first, validate that retained descriptor and close it on rejected
   admission. Future authenticated root binding remains G5; a raw FD is not approval.
10. **CG-REV-10, MINOR:** bounded control-file bytes still permitted a single numeric
    token longer than Python's integer conversion limit, escaping the closed error
    path. Bound token lengths/ranges and keep parse failures explicit/unresolved.

After those repairs, 49 component checks pass; 32 durable harness receipts confirm
root removal and helper reaping. Final read-only review identifies two remaining
component corrections before full verification:

11. **CG-REV-11, MAJOR:** idempotent create revalidation was outside the retained
    error handler. A lost capability or unreadable membership could reject that
    call without closing later Stage admission. Handle failures on that path too.
12. **CG-REV-12, MINOR:** constructor filesystem validation did not check parent
    domain/control-file support before fresh allocation, and record() could sample
    a transitioning entry without its registry lock. Reject unsupported parents
    before effects and serialize private snapshots. Cancellation remains separate.

Version 3 passes 221 source feature checks (51 boundary cases). Final budget audit:

13. **CG-REV-13, MAJOR:** admission conflated the per-operation five-second cap
    with the lifetime of the original C1 lease. A generation may remain active for
    300 seconds and must retain cleanup through the original teardown reserve.
    Separate an explicit operation budget (≤5 s) from the immutable original lease.
    The maximum proposed design envelope is 300 + 16×5 + 10 + 2 + 2 = 394 s;
    it is an engineering cap derived from D3, not a measured guarantee. Test a lease
    longer than five seconds and a shorter exhausted cleanup operation without
    extending that lease or losing original cleanup authority.

## Final read-only disposition

Candidate ML3-CONTAINMENT4-2026-10-18-v4 repairs the thirteen recorded component
findings. Final verification passes 801 platform Python tests plus 24 subtests,
222 source-excluded wheel checks and 52 focused source boundary checks. Nine
installed module hashes match source. All 26 frozen source/test/verifier inputs
are unchanged. Ruff and 133 partial endpoint/hash/AST checks pass. Three pre-review
archives verify byte-for-byte. No independent full-candidate review is claimed.

The final full run generated 70 owned test-root receipts, including nested consumer
checks, and the isolated consumer generated 35. All 105 confirm exact root removal
and helper reaping; fixed native source/binary hashes verify. Earlier repaired runs
also retain completed harness receipts. The first failed run's seven empty test roots
were removed through separately recorded, identity-checked external test maintenance,
without signals or pretending to reconstruct ordinary C1. Initial failures and that
maintenance record remain immutable evidence. No component test scope remains live.

The actual kernel checks establish this component's frozen birth, leader-independent
membership, scoped force and deleted-boundary rejection on the recorded host. They
do not establish M1/AFFA Release/cancel ordering, an authenticated bootstrap, a
supervisor-loss lease, arbitrary-workload escape prevention, bounded kernel I/O,
ordinary provider ownership, broker/FixtureBoundaryOps integration or any of the
nine full-ML3 runtime cases. Exclusive parent ownership is a required assumption.
All 24 ML-SR requirements and 18 unvalidated/allocation-only/null-mapped REF-002
parents remain. Whole-project trace, C++, Argus lifecycle coverage, U5, acceptance
and main merge remain pending. Process readiness stays false.

The author now requires commits after stable increments. Commit this exact verified
snapshot on a candidate branch and record its Git identity additively; preserve the
older manifests and main at c2997c0. Sol/high is recommended next for independent
helper supervision and M1/AFFA/broker integration. No model switch, factory admission,
scientific experiment, canonical-note edit or acceptance follows from this record.

Open scope: authenticated bootstrap/original-owner admission, fixed exclusive root,
actual bounded helper supervision, M1/AFFA atomic Release/cancel and supervisor-loss
lease, U5 readiness/teardown, Argus evidence and full runtime/trace/acceptance. Freeze
alone is not a launch fence; model or component tests cannot close those gates.
