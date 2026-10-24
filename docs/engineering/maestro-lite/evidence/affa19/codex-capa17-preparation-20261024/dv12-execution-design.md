# Genuine DV12 execution capture — design before code

Run only after the three post-platform verification queues are terminal and no other pytest is active. This is
an engineering evidence capture, not acceptance. Keep the tested candidate fixed at4bedba9efd21c750b84322e5fc265eb6adf86cc9.

Resolve the repository, affa19 inputs and full-run paths physically on loop10. Refuse pre-existing output files.
Hash the six actual inputs before execution: configuration, wheel receipt, wheel log, G4, allowlist and official
validator. Verify the validator equals the tested Git blob; call its unmodified official code-scope CLI with the
exact reviewed argument list and fixed candidate. Capture stdout and stderr into exclusive files. Use a finite
900-second host watchdog and a fresh process group; on timeout terminate that owned group and bound cleanup.
This watchdog is not a scientific timing limit. Preserve failure output and record actual exit/timeout/error.

Hash those same inputs after the process finishes and hash the actual stdout gate. Record exact command,
physical repo/run, candidate/scope, before/after hashes, actual returncode, timestamps, elapsed time and wrapper
identity. An input change, timeout, nonzero exit, malformed or unaccepted gate fails capture. Never overwrite a
previous receipt or manufacture a success. Do not invoke the builder, alter CAPA, accept or merge from this wrapper.
The independently reviewed builder separately checks exact receipt/gate/count/code/source association.

## Independent findings and repair design before code

Accept the independent review findings: leader-only waiting does not prove descendant cleanup; exceptional/
interrupt exits need finally cleanup; and the consumer must refuse capture failure even if a timed-out leader
races to exit0. Before any execution, repair the wrapper to own a fresh process group, capture BaseException,
handle termination as an interruption, and always bound TERM/KILL/group-disappearance/reap checks in finally.
Record any surviving/unknown group as incomplete and refuse success. Block interruption signals during this
bounded finalization/receipt write. A leader's exit is never the group's completion proof.

Repair the consumer to require explicit timed_out=false, capture_passed=true, failure=null and completed owned
cleanup in addition to actual exit0 and all existing exact association guards. Keep partial outputs exclusive.
If capture/receipt I/O itself fails, preserve whatever was written and fail; a durable receipt cannot be promised
on an unwritable/full filesystem. Never synthesize a missing receipt or retry over partial output. No genuine
validator or builder has run. Independently re-review both resulting scripts before scheduling execution.

Accept the successor review's reproduced spawn-assignment interruption finding. Defer throwing the installed
signal-handler exception while Popen is constructing; retain the actual pending signal, assign the returned
child handle, end the spawn window and then raise. Do not block signals across fork/exec and accidentally leave
the validator inheriting a blocked termination mask. After ownership is established the existing finally cleanup
handles interruption. A failed Popen construction is still a failed capture; it cannot become success. Verify the
exact after-child-creation/before-assignment seam with a genuine tiny subprocess whose handle the harness retains.
