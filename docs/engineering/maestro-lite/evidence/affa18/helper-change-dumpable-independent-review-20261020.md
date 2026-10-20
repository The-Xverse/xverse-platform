# Early non-dumpable helpers (finding 406): independent review (2026-10-20)

Reviewer: separate agent session (Claude, independent of the change author).
Repository: `/home/jefferson/xverse-platform-worktrees/maestro-lite-affa18-20261020`, uncommitted on HEAD
`18547fd6c`. Machine-readable record: `helper-change-dumpable-independent-review-20261020.json`.

## Frozen inputs (sha256 verified)

| File | sha256 |
|---|---|
| src/xverse/maestro/native/run_authority.c | ffdc632ed58b796031d25eac0dfe739cf3ba151344d91dc60ed4be27cc2a5344 |
| src/xverse/maestro/native/bootstrap.c | c1f2885db167852b93d207b1051421e44610efa2f88bfe45309f4a944e8dfe05 |
| tests/thesis_lite/maestro/test_affa_watch_token.py | 5880f335ae8e7603edd5158e9d771d50f938dded0e98296152bcd4a52774c6d4 |

Delta: deleting the comment and the `prctl(PR_SET_DUMPABLE,0,0,0,0)` line at the start of each
`main` (run_authority.c:510-511, bootstrap.c:308-309) reproduces the F-02-reviewed blobs
(5938cd01..., 83b10177...) byte for byte. All three builds were warning-free in /dev/shm. The authority
and RUN_BOOTSTRAP binary hashes match finding 406. Nothing was executed and no pytest was run.

## Verdict: partially addressed

- **F02R-01, supervisor: closed.** `prctl` runs at bootstrap.c:309, before the only key generation
  (bootstrap.c:133). The process inherits no secret across its own exec.
- **F02R-01, authority: narrowed, not closed.** The key bytes now enter memory only after the process
  is non-dumpable (run_authority.c:511 before :287). However, the key memfd is inherited
  across `execveat` (CLOEXEC cleared at bootstrap.c:267), and the image is a readable memfd, so exec
  resets the authority to dumpable until main runs. During ld.so loading of libcrypto/libc, a
  same-uid process can open `/proc/<pid>/fd/<argv[3]>`, a READ-mode check that Yama does not restrict.
  The ancestor peer can also ptrace or pidfd_getfd the process. The peer controls the timing: it gets
  the pid while the child is still frozen before exec, it triggers the thaw, and it owns the cgroup's
  `cgroup.freeze`. The memfd's CLOEXEC and seals confine the fd to one process and protect its
  integrity, but they do not limit this window.
- **F02R-02, F02R-03: addressed.** The two new tests assert what finding 406 claims. The kind-4
  request is rejected by the CHILD rule before the WATCH rule. The client raises `ML-AFFA-WATCH-TOKEN`
  in `_validate`, before `sent=True`, with sequence unchanged and no revoke.
- **Side effects:** nothing in src/ or tests reads a helper's /proc, ptraces it, uses pidfd_getfd or
  relies on core dumps. pidfd and SO_PEERCRED use is unaffected.

Checks: 7 PASS, 1 FAIL, 2 NOTE.

## Findings

- HIGH: none.
- MEDIUM: none.
- LOW
  - F02D-01: The authority is dumpable from execveat until the first statement of main, while it
    holds the inherited watch-key memfd. Recommendations:
    - Make the exec non-dumpable. One way is an owner-unreadable authority image (for example,
      fchmod 0111 before sealing), with the supervisor rejecting a readable image 4. Exec then
      applies ENFORCE_NONDUMP; with fs.suid_dumpable=2 this denies same-uid access.
    - Otherwise, record the hostile same-uid peer non-claim that F02R-01 recommended.
- NOTE
  - F02D-02: Finding 406 and the comment at run_authority.c:510 say "before any secret exists".
    That holds for the key bytes, not for the key-bearing descriptor. 406 also omits the non-claim.
  - F02D-03: The v1 kind-20 case is matched only as a bare ValueError, and no kind-20 case with
    pid != 0 is tested.
  - F02D-04: The supervisor side of F02R-01 is fully closed.

This review is an independent source reading and neither activates the lane, admits M1 nor accepts anything.
