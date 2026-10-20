# Composed authority interruption controls

Status: selected owned native controls verified, full increment17 incomplete.
Capability024 remains governed by the external Spec Kit inputs. These controls
refine existing runtime obligations; they do not create a separate capability.

The original v6 lazy dispatcher now has deterministic tests for five cancellation
windows and four original helper-loss windows. Production Python/C source is
unchanged. Instrumentation pauses the original connection before send, before
receive, after an actual reply, or around actual issuance persistence. It does
not edit frames, handles, registry pins, permissions or admitted deadlines.
The original blocking dispatcher runs on one coordinator thread in its original
process; independent cancellation uses the original latch and authority. Real
helper failure uses the originally retained pidfd, without process discovery.

| Selected window | Original intervention | Observed behavior |
| --- | --- | --- |
| Stage before send | Cancel or authority loss | No workload; attempted issuance remains unknown |
| Stage sent, receive pending | Cancel | Native child exists frozen; in-flight exchange is fenced; no workload; wait unknown |
| Stage sent, receive pending | Authority loss | No workload; a genuine queued ACK can preserve factual issuance; wait unknown |
| Release before send | Cancel | Native Cancel acknowledged; no workload; original STOP/RETIRE waits retained |
| Release sent, receive pending | Cancel | Exactly one EXEC line proves Release won; independent revocation and exact C1 cleanup; wait unknown |
| Actual Release reply before normal outcome | Cancel | Exactly one EXEC line; no normal started record; genuine STOP/RETIRE waits retained |
| Before issuance record | Storage loss | Actual Stage identity retained; no issued persistence receipt or workload; wait unknown |
| After actual issuance record | Storage loss | One genuine issued receipt retained; no ordinary Stage return or workload; wait unknown |

Every case preserves a separate owned active heartbeat scope through runtime
cleanup. Its identity, observed membership, unfrozen state, original parent and a
fresh heartbeat are checked afterward. Test-only descriptor-relative thaw and
final cleanup are explicitly harness stimulation, not runtime Release, provider
admission, adoption or M1 proof. Active membership reads are observations; the
production frozen-membership certification remains unchanged.

Original c execution37147 exited0: **9/9 source and9/9 installed-wheel**. The
read-only audit9139ab exited0:18 distinct native contexts,18 original fixture
waits,18 absent owned roots,62 verified source links and all76 packaged Python/C
source hashes unchanged. Four contexts retain complete factual cleanup;14 keep
unknown direct workload waits despite exact C1 release and helper reaping. All18
independent public-root recomputations remain incomplete. The source pre-send
authority-loss case retains an unmirrored M3 outcome, sequence2; it is not repaired
or counted as complete evidence. Byte-identical public roots and heartbeat
binaries are retained alongside the original receipts.

Evidence: [verification](evidence/affa17/composed-authority-20261019c/verification.json),
[trace](evidence/affa17/composed-authority-partial-traceability-v2.json), and
[CAPA successor](evidence/affa17/capa-20261019-composed-authority/register.json).
The latter validates eight selected records and36 bindings. Every effectiveness
status remains NOT_DEMONSTRATED; no independent root-cause confirmation is claimed.

Failed a/b controls remain immutable. Original a58339 exited1: all18 tests fail
before runtime admission because the active sentinel was incorrectly observed
through a frozen-only API;18 sentinel harnesses were cleaned. Original b45743
exited1:8/9 per phase, with the queued-ACK expectation and a birth-observation
race exposed. It retains17 explicit RunClosure receipts and18 original fixture
waits/snapshots; the missing explicit closure is not reconstructed. Initial audits
also rejected an intentional normal-mirror gap; the corrected audit recomputes
exact missing mirrors and validates every existing reference. Findings249–253
record review before each correction. No unchanged native rerun was used to
replace a failure.

These are partial controls for the named atomic and pre-handle runtime cases.
They do not demonstrate syscall-level CP04 interruption, every CP01–12 branch,
all capability-lifecycle rows, full M1/environment admission, full platform
regression, source-parent semantics, independent candidate review, stable17 or
acceptance. CAPA135/222 remain unresolved. Continue with the unexercised crash
and ownership branches while preserving original table expectations and ends.
