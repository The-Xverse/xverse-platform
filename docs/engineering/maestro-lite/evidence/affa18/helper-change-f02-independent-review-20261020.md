# F-02 native watch token: independent review (2026-10-20)

Reviewer: separate agent session (Claude, independent of the change author).
Repository: `/home/jefferson/xverse-platform-worktrees/maestro-lite-affa18-20261020`,
branch `candidate/maestro-lite-affa18-20261020`. The change is uncommitted on top of HEAD
`18547fd6c51dbd023e6290502dff31b4c59887ff`. Machine-readable record:
`helper-change-f02-independent-review-20261020.json`.

## Frozen inputs (sha256 verified)

| File | sha256 |
|---|---|
| src/xverse/maestro/native/bootstrap.c | 83b10177ad792bf6ebda663ce11bcc07bff17fb9eb2807aa5270f0a02c2849f0 |
| src/xverse/maestro/native/run_authority.c | 5938cd01dcd46669ec91de942fdf6df39d53802b3ac329eb3eaf58d9a3e00932 |
| src/xverse/maestro/affa_protocol.py | 4c0e8eb0a10cdcf9316e1ca4cda1c8daccc2e3746cf1aa255d409feeb2aaaca5 |
| src/xverse/maestro/bootstrap.py | 48e38bec9f9f339d12f0fe287c295e5809d2f73cea793eedb132aae224f40046 |
| src/xverse/maestro/affa_client.py | f88a4bc9e9f7a877997de5e50ec372d3022cc8b5136a4a141ede1277cf161299 |
| src/xverse/maestro/run_broker.py | 29ebeba8ab61ecb80e9db625a69fe3b38c29a35dacb9195202fa9c5383071211 |

Method: read-only source reading. Both supervisor variants and the authority were compiled
in /dev/shm with the requested flags. All three builds were clean, and none of them was
executed. No pytest was run and no existing file was modified.

## Verdict: F-02 addressed

A Python caller holds tokens but not the key. It cannot get a valid token for a boundary
the supervisor did not WATCH, and it cannot replay one boundary's token for another. The
reasons:

- The token is HMAC-SHA256(per-supervisor key, "MLWT" || st_dev || st_ino). It is computed
  only over a descriptor that the supervisor has just validated and retained
  (bootstrap.c:183-197).
- The authority recomputes the token over `fstat` of the same open fd that it checks,
  duplicates and admits (run_authority.c:385-404). All checks come before the first state
  change, so there is no TOCTOU gap on identity.
- A token for a removed and reused identity cannot arise while the supervisor lives. The
  supervisor never closes the watched fds, which pins the kernfs node id.

Checks: 22 PASS, 0 FAIL, 3 NOTE.

## Findings by severity

- HIGH: none.
- MEDIUM: none.
- LOW
  - F02R-01: The watch key is readable by the same-uid parent between `execveat` and
    `PR_SET_DUMPABLE(0)` (run_authority.c:287-288, 316). The authority is a CLONE_PARENT
    child of the Python peer, and ptrace_scope is 1. Recommendation: make the process
    non-dumpable first thing in `main`, and state that confidentiality against a hostile
    same-uid peer is not claimed.
  - F02R-02: The relaxed kind-20 BootstrapPacket rule (bootstrap.py:264, 269) has no unit
    test.
  - F02R-03: The client-side `ML-AFFA-WATCH-TOKEN` check (affa_client.py:283-284) is not
    exercised by any test.
- NOTE
  - F02R-04: The token proves the boundary was watched by this supervisor instance, not
    that it is still watched. The fix depends on the supervisor pinning the kernfs node and
    staying alive. The authority has no native link to supervisor liveness.
  - F02R-05: The late STAGE rejection does not independently show non-admission, because
    any REJECTED reply closes the authority. Non-admission follows from the code path. No
    negative control runs through a supervisor-born authority.
  - F02R-06: Finding 403 is accurate but incomplete. It omits the zero-key check, the
    seal/size checks, the forged-token control, and the F02R-01 and F02R-04 qualifications.
  - F02R-07: The token is bound to the run, not to a unit, slot or generation. This is
    within the F-02 scope.

This review is an independent source reading and neither activates the lane, admits M1 nor accepts anything.
