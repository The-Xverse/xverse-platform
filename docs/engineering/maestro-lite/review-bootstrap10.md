# Separate bootstrap source review before successor repairs

Same-agent read-only component pass, 18 October 2026. No independent full review,
acceptance, run admission or complete M1 proof. First native bytes are retained as
native-first-pass.c before changes.

1. MAJOR: return on failed receive before decoding any packet fields. recvmsg errors
   leave no valid packet and must never expose uninitialized bytes to decoding.
2. MINOR: strict compilation finds six misleading-indentation diagnostics in the
   compact C statements. Split the independent statements before continuing.

All full Lite/runtime/acceptance obligations remain binding.

Separate Python/native integration read-only pass, before execution or repair:

3. MAJOR admission metadata: bind the externally admitted supervisor artifact pin
   explicitly as well as the three helper images. The trusted external runner still
   authenticates the initial executable/environment; a context digest is not proof.
4. MAJOR late acknowledgement: a genuine Born reply received after its deadline must
   retain its actual pidfd for cleanup-only accounting before rejecting activation.
   Closing that received pidfd would unnecessarily turn known exact ownership into
   an unresolved birth. Keep malformed/foreign reply FDs rejected and closed.

5. MAJOR integration: bounded persistence Abort is cleanup, not ordinary start
   authority. Preserve healthy Abort after the shared latch is cancelled, using the
   retained original child/channel and actual liveness checks. Bootstrap issuer
   liveness must not prevent cleanup-only Abort or exact shared wait accounting.

6. MAJOR contract mismatch: PreparedLifecycle.lifecycle_digest is canonical raw
   SHA-256 hex, whereas artifact pins use sha256:. Accept/validate the original raw
   lifecycle identity without renaming it or treating it as an artifact URI. The
   first integration setup rejected that real accepted preparation before spawning.

7. MAJOR native ABI: clone3 with CLONE_PARENT requires exit_signal=0. SIGCHLD
   produces EINVAL, so the first birth is rejected before child creation. The
   original-parent relationship supplies the inherited parent notification/wait
   semantics; use the documented clone3 combination and verify real P_PIDFD waits.
   Integration2 retained one conservatively unresolved dispatched birth; external
   fixture cleanup removed its empty C1. This is not a successful bootstrap result.

8. MAJOR original registry identity: pin the actual child/pending/deadline dictionaries.
   Replacing the child registry with an empty dictionary must not let drain report
   a vacuous complete result. Ordinary capability checks must reject replaced
   registries; retained original accounting is not reconstructed from field values.

9. MINOR resource accounting: on initial supervisor registration failure, close its
   private duplicate pidfd after cancelling the channel. The external original Popen
   owner still retains exact root wait authority; no helper birth can be dispatched
   before registration. Do not leak an unreachable local FD in a failed constructor.

10. MINOR test harness: the short-lease expiry fixture used a 3-second registration
    deadline outside its 0.3-second lease, so setup correctly rejected before the
    expiry case ran. Supply an in-lease registration deadline and retain external
    root/image cleanup even if setup fails. Nineteen expanded cases passed.

Finding 10 follow-up: the active-workload expiry case also needs its storage
initialization deadline inside the same short lease. Expanded2 passed 21 cases;
that case rejected the out-of-lease storage request before helper dispatch.

11. MINOR diagnostic separation: if the bootstrap supervisor was killed, exact
    registered-child reaping can still be confirmed, but the final workload-freeze
    acknowledgement is absent. Return an explicit supervisor/freeze unresolved
    diagnostic rather than None; do not conflate that with child reaping or C1
    cleanup. Expanded3 passed all 22 component cases before this refinement.

12. MAJOR kernel identity (actual negative control): Linux 6.8 pidfds share one
    anonymous inode. Replacing the supervisor pidfd with a registered helper's
    pidfd passes the old liveness check; the expected rejection probe fails. Child
    inode checks have the same weakness and must not authorize signals/reaping.
    Retain a distinct original private duplicate and use exact open-file-description
    equality (KCMP_FILE on this admitted host), never inode/PID equality. Signal,
    wait and duplicate only the private original capability. Unsupported comparison
    must reject admission, not fall back to a weaker predicate. Verify root, child
    and supplied wait-FD replacement, including an unrelated owned sentinel.
    Current host supports own-process KCMP_FILE; F_DUPFD_QUERY returns EINVAL here.
    Preserve v2's full source/evidence in pre-repair-v3.tar.gz (1014 platform +24
    subtests, 435 wheel tests passed, but the identity probe refutes this boundary).
    Repeat full source/wheel verification after repair; v2 is not a stable checkpoint.

13. MAJOR borrowed signal path (actual negative control): PersistenceClient._fail
    and its drain escalation still signal the client's borrowed pidfd. Replacing
    that FD with an unrelated owned sentinel's pidfd causes the failure path to
    terminate the sentinel, even though exact wait validation rejects the alias.
    For native-issued children, route all signals through the privately retained
    original child capability, never the borrowed alias. Preserve legacy actual
    Popen semantics. The new permanent sentinel control must fail before this
    repair and pass after it. Preserve complete v3 source/evidence in
    pre-repair-v4.tar.gz (1018 platform +24 subtests and 439 wheel tests passed;
    the separate signal probe refutes the missing boundary). Repeat both full
    regressions for the successor. No v3 stable checkpoint/acceptance is claimed.
