# Independent DV12 capture review — 2026-10-24

Scope: the staged `dv12-execution-design.md`, `capture-dv12.py`, and the execution-receipt consumer in the staged CAPA17 builder. These are preparation files on loop10, not installed execution evidence. No official validator, wrapper main, CAPA builder, schema verifier, pytest, framework, or live simulator was executed. No platform/thesis/Git files were changed. This review neither accepts evidence nor authorizes a merge.

## Finding 1 — original source review: changes requested

The original wrapper waited for its leader after TERM and escalated only when that leader's wait timed out. A descendant could remain after leader exit, including retaining captured output descriptors. Non-timeout post-spawn exceptions and interruption also lacked unconditional owned-process cleanup. Finally, builder `407a4fabb65c41235e816f0053fae977c06e86e1eb963f04d629eb7239a4b645` checked actual exit0 and exact command/hash association but omitted `timed_out`, `capture_passed`, and `failure`: a timeout racing an otherwise successful exit0 could still satisfy its guards. These findings were reported before repair. Root disposition and repair design were recorded in the design's “Independent findings and repair design before code” section.

Spawn failure itself was already caught when output files could be opened and subsequent capture I/O succeeded. No durable receipt can be promised if its storage fails. A pre-launch exclusive-open refusal is distinct from an uncleaned post-launch child. Preserve partial files and refuse retries over them.

## Finding 2 — successor independent review: changes requested

Reviewed identities:

| File | SHA-256 |
| --- | --- |
| `capture-dv12.py` | `b7d094b6cfdc5fbdd9079103ac82534c2e5a862d6d33a0be2b469244b2a5f870` |
| `dv12-execution-design.md` | `7652bb693db71069f2f8d09b65a8fc6676833f47b762c23bc21249a0af46e685` |
| `build-capa-20261024-simtime-step17.py` | `1e2d6f3412e217d61b0bd4f308f230b784f28e00c3617e28e4b704871bb28bf5` |

### R17c-1 — blocking: interruption can precede ownership assignment

`capture-dv12.py:90–107` installs a throwing signal handler before `process = subprocess.Popen(...)`. An interrupt after subprocess creation but before `Popen` returns leaves the local `process` equal to `None`. Its `finally` consequently calls `cleanup_group(None)`, which returns `complete=True` at lines38–40, despite the newly created process group still running. Catching `BaseException` does not recover the missing handle. The captured failure refuses successful evidence, but the actual invocation can continue and mutate its outputs after the failed wrapper returns; cleanup evidence is incorrect.

A deterministic tiny stdlib probe delivered the actual installed handler using `sys.settrace` at a real `subprocess.Popen` construction boundary after `_child_created=True` with a valid PID. It observed `CaptureInterrupted(2)`, no completed assignment, cleanup reported complete, and the retained actual child still running. The independent harness retained the in-construction object exclusively to terminate and reap the test child afterward. It invoked no wrapper main or official validator and created no run receipt.

Recommended resolution: establish a cancellation-safe spawn ownership boundary. Defer throwing interruption until the returned child handle has been assigned, or use another explicitly demonstrated ownership protocol. If signals are blocked around spawn, account for the child's inherited signal mask; do not silently make the validator ignore TERM/INT. Finalization must not claim cleanup complete when spawn ownership is unresolved. Record the repair design before editing, then regress interruption during actual construction as well as after assignment.

### Repairs independently confirmed

`cleanup_group` now checks group existence independently of leader completion, sends TERM, escalates to KILL for a remaining group, reaps the leader, bounds disappearance checks, and reports errors/incomplete cleanup. `finally` invokes it after normal completion, timeout, and caught exceptions. Signals are blocked during finalization. Success additionally requires complete cleanup and no TERM intervention.

The builder's lines41–50 now require exact integer exit0, `timed_out is False`, `capture_passed is True`, `failure is None`, and `cleanup.complete is True`, while retaining candidate/run/repo/scope, six before/after/current input hashes, gate hash, exact command, actual wheel counts, tested code identity, and tested source-blob association. The earlier `407a4f...` builder identity is superseded. This closes the prior timeout/exit0 consumer gap for honest receipts emitted by the wrapper. It does not establish acceptance or authenticate arbitrary externally fabricated receipts.

Source inspection also confirms fixed candidate `4bedba9efd21c750b84322e5fc265eb6adf86cc9`, exact official code-scope command, tested validator blob comparison, exclusive output creation, input hashes before/after, actual stdout/stderr hashes, actual returncode, external scratch/cache, and refusal on drift, malformed/rejected gate, timeout or failure. Capture I/O failures leave a failed invocation/partial files; no missing receipt is synthesized. The execution queue precondition remains root's operational admission responsibility.

### Checks actually performed

Both Python files parse with stdlib AST. The helper-only script at `../../scratch/review_wp15/dv12-helper-probes.py` extracts only `CaptureInterrupted`, `interrupt`, `group_exists`, and `cleanup_group` by AST; it never imports or executes wrapper main. Four isolated controls ran using `/usr/bin/python3.13 -S -s -B`, with scratch/TMPDIR on loop10:

1. Normal tiny subprocess exit0: cleanup complete, no TERM/KILL, no errors.
2. Throwing interruption after ownership assignment: TERM sent, child reaped, cleanup complete.
3. A real tiny leader and descendant both ignoring TERM: bounded grace, KILL sent, leader and adopted descendant reaped, group absent. The isolated harness became a Linux child subreaper and reaped its test descendant, leaving no orphaned test process.
4. Interruption during actual `Popen` construction: reproduces R17c-1 as described above; the harness independently cleans the retained child.

No entire wheel log or all757 evidence bindings were hashed for this review. Actual official DV12 result/receipt, post-execution evidence checks, CAPA generation and acceptance remain pending. The successful platform regression is separate evidence and does not substitute for these gates.

## Finding 3 — deferred-interruption successor: source review passes

Root accepted R17c-1 and recorded the appended spawn-ownership design amendment before editing. Independently re-reviewed identities:

| File | SHA-256 |
| --- | --- |
| `capture-dv12.py` | `e388ee9a468bc73375a03def17fc28c708856971d66afee234e6200af02b09d4` |
| `dv12-execution-design.md` | `ec131a2a66b83866e6f346239c380bc6b17946a5f24482e2638595dbca3307e3` |
| `build-capa-20261024-simtime-step17.py` | `1e2d6f3412e217d61b0bd4f308f230b784f28e00c3617e28e4b704871bb28bf5` (unchanged) |

The installed handler now retains interruption while `SPAWNING=True` without raising during construction. The returned child handle is assigned before that flag is cleared; a retained signal then raises into existing owned cleanup. A signal after clearing the flag raises directly with ownership already established. No termination signal mask is blocked across fork/exec. This repairs the reproduced seam. There are no remaining source blockers within the reviewed trusted engineering-capture scope.

Five genuine tiny stdlib controls in `../../scratch/review_wp15/dv12-successor-probes.py` extract the exact current ownership `try` block and helper definitions by AST. They supply only a tiny Python command or a deliberately missing executable, external temporary output descriptors, and harness globals; they never call wrapper main, its official command, or a CAPA builder:

1. Normal subprocess exit0: no failure or TERM, complete cleanup. The actual child asserts that SIGINT/SIGTERM/SIGHUP are not inherited as blocked.
2. Installed SIGINT handler delivered after actual child creation but before completed `Popen` assignment: retained, then raised with a valid owned handle; actual returncode `-15`, failure `CaptureInterrupted(2)`, group absent and cleanup complete.
3. SIGTERM after handle assignment and before the spawn flag is reset: same owned refusal, actual returncode `-15`, recorded signal15, cleanup complete.
4. SIGINT after the flag is reset: immediate owned refusal, actual returncode `-15`, recorded signal2, cleanup complete.
5. Actual missing-executable spawn failure: `FileNotFoundError`, no child, no returncode, cleanup complete; the capture cannot pass.

All five passed. The same trace seam failed in finding2, so the regression distinguishes the repaired behavior. The earlier failing source was reconstructed byte-for-byte and verified against its previously recorded `b7d094b6...` SHA before preservation at `../../scratch/review_wp15/capture-dv12.failed-b7d094b6.py`; it is historical source, not executable run evidence. The original failing helper-probe script and findings remain intact.

AST comparison confirms both group-cleanup helpers are unchanged from finding2; its real TERM-ignoring-descendant/KILL/reap/group-disappearance result therefore remains applicable. Five additional isolated AST controls against the builder's exact capture-state assertions admit matching flags and refuse timeout, failed capture, recorded failure, and incomplete cleanup independently. Both current Python files parse. No official execution or fabricated run receipt occurred.

This is a preparation source verdict, not DV12 success or CAPA acceptance. Root must still satisfy queue/admission preconditions, execute the exact reviewed wrapper once into fresh outputs, inspect its actual terminal receipt and gate, and complete subsequent evidence review before any separately authorized generation or acceptance. Failed/partial outputs remain preserved; no retry over them is implied.
