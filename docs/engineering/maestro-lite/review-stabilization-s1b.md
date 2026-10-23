# Review log: Thesis Lite stabilization S1b (graceful stop, stderr capture, marker readiness probe)

The thesis increment is S1, `specs/029-lite-stabilization` (FR-009 to FR-013; tasks S1-T07 to S1-T12; author
decision S-D2, approved on 2026-10-23).
- **Branch.** `candidate/lite-stabilization-s1b-20261023`, from the S1a-2 candidate head `d8b44719c`. That head
  is not merged; S1b is rebased onto the merged S1a-2 before its own acceptance.
- **CAPA.** S1b is CAPA step 11, because S1a-2 takes step 10. Each finding is recorded here before its repair or
  implementation.

1. **S1-T07: the amended as-built limits (FR-012, S-D2). Written at 19:35:53 2026-10-23, before any S1b code.** The
   frozen texts stay as written. Each is superseded here and in the thesis record
   `specs/024-maestro-lite-lifecycle/review/amendment-s1b-as-built-limits-20261023.md`, from the S1b merge on.
   - **A1, DV04 n0.**
     - Frozen text (as-built reconciliation 2026-10-21, line 55, and C4 in `review-affa19.md`): "no
       application-level probe exists".
     - Amendment: an observe action may declare one admitted application probe, the nonce marker probe (FR-011,
       S-D3). `running` remains the default. Periodic health stays liveness-only, and unchanged units stay
       liveness-only.
     - DV04 n0 then becomes a positive case for a marker that never appears (`ML-PROBE-NOT-READY`), and a negative
       case for a marker that appears late but within the bound.
   - **A2, DV06 n5.**
     - Frozen text (line 57, C4, and `review-affa19.md` about line 565): "no SIGTERM is delivered to workloads".
       Workload teardown goes straight to `cgroup.kill`.
     - Amendment: a unit stop on the owned path may send SIGTERM through the pidfd before the freeze, wait up to an
       admitted grace inside the existing ≤ 5 s per-unit budget, and then freeze and kill as before (FR-009). The
       STOPPED record states whether the unit exited on TERM or was forced.
     - DV06 n5 then becomes the case of a unit that ignores TERM and is forced.
     - The cancel path, the Phase 5 `crash` fault, the emergency path and the cleanup path stay SIGKILL.
   - **A3, `ADR-ML3-TEARDOWN-0001` line 15.**
     - Frozen text: "This component does not add an arbitrary graceful application stop callback."
     - Amendment: there is still no arbitrary callback. The only addition is the admitted, bounded SIGTERM grace
       of A2, with no application code run by Maestro.
   - **A4, `ADR-ML3-LAUNCHER-0001` lines 42–43.**
     - Frozen text: the stub "redirects standard streams".
     - Amendment: stdin and stdout stay on `/dev/null`. fd 2 may be a declared, run-scoped, size-capped stderr
       file, created `O_CREAT|O_EXCL` without following links (FR-010). It is a private artifact, not exported.
     - `inheritedHandles: closed` means that no control descriptor is inherited.
   - **A5, `ADR-ML3-PERSISTENCE-0001` lines 31–35 (in-flight cancel).** Already amended as S1a-1, which is merged.
     It is listed here for completeness and gets no further change.
   - **The design decisions follow as ADR amendments, before the code:** the protocol and recipe form, the
     paths covered, the cap mechanism and the probe placement.
2. **S1-T10a: the Phase 7 start-up `ML-CONTROLLER-TIMEOUT` (GA-10), diagnosed from its saved evidence (written at
   19:37:06 2026-10-23).**
   - **Run.** `runs/xverse-lite-live-20261022/lite-20261023T010731-nominal` on loop10. Platform main `8b3d8c8e8`,
     before S1a; compat `6fd7f28`, blueprints `085983b`.
   - **Facts.**
     - `diagnostics: [ML-CONTROLLER-TIMEOUT]`, dispatch null, persistence `ML-PERSIST-RPC-FAILED` at 2.98 s after
       the run record started.
     - No unit was issued, and the cleanup is complete.
     - The Maestro Argus stream has one event, "original prepared inputs validated". The M3 journal was never
       written: only its lock exists.
   - **Code path.**
     - `ML-CONTROLLER-TIMEOUT` at start-up comes only from `controller._receive`, called by
       `ControllerClient._ready` in `admit_controller`. That waits for the controller worker's `hello`, within
       the admission deadline (`controller.py` about 88–95 and 198–202, 326–383).
     - The owned harness passes a start-up scope of `HostDeadline("host-session", now + 2)`
       (`test_live_closed_loop.py`, `RuntimeScope`).
   - **Most likely cause (not proven).** The controller worker is a Python process released from a frozen
     boundary. It did not finish starting and send `hello` within the harness's 2 s start-up deadline. That run
     was at host load about 9–10 (Phase 7 log). The worker's own stderr was discarded: Maestro helper streams are
     not covered by FR-010, which captures unit stderr. So the delay cannot be attributed further.
   - **Since S1a.** In about 40 post-S1a live runs (load 4–8) it has not recurred.
   - **Disposition: carried explicitly. GA-10 is narrowed, not closed.**
     - S1c-2 records the start-up time to `hello` in `maestro-run.json`.
     - S1c-2 gives the harness start-up scope an admitted margin (proposed 5 s, inside the platform's existing
       admission limits).
     - The S1d soak treats any recurrence as a P1 failure, with a finding.
     - No platform change in S1b.
3. **The S1b design is recorded before any code (written at 19:54:08 2026-10-23):**
   `design-stabilization-s1b.md`.
   - It covers the AF17 path only, with every capability opt-in and byte-identical when undeclared.
   - It defines AR17 version 2, the TERM and TERM_SENT kinds, and state bits 512, 1024, 2048 and 4096.
   - It specifies the two-step TERM, the private capped stderr file and the native nonce-marker probe.
   - Its decisions D-1 to D-4 are recorded in the thesis as the delegated revisions DR-7 to DR-10 and are flagged
     for the author at acceptance:
     - D-1: the terminal-fence stops stay forced; S1c-2 schedules `stop` steps.
     - D-2: LC09 is out of scope and refuses the new declarations.
     - D-3: stderr is retained privately, not collected.
     - D-4: TERM is two-step, with the lock free during the grace.
   - The ADR amendments follow in the next commit, before the code.
4. **S1b step 1: the protocol and the native authority are implemented (written at 20:05:47 2026-10-23, load
   about 4.2).**
   - **Protocol (`affa_protocol.py`).** `TERM = 31`, `TERM_SENT = 32`, the state bits 512/1024/2048/4096 and
     `STATE_MASK = 8191`. `AuthorityRecipe` gains `grace_ms`, `stderr_max`, `probe`, `stderr_device` and
     `stderr_inode` (all default 0). It emits AR17 version 2 (the 48-byte header of the design) only when a
     control is declared; otherwise the version 1 bytes are unchanged. Decode accepts versions 1 and 2 and
     rejects an all-zero v2, a nonzero reserved word, out-of-bound controls, a stderr identity without a cap
     (or the reverse), a short v2 header and trailing bytes. TERM is a request kind (state and reason 0).
   - **Client (`affa_client.py`).** `_REPLIES[TERM] = TERM_SENT`, TERM stays out of `_CLEANUP`, the state mask
     is `~8191`, and a REGISTER may carry 4 or 5 fds. The count is bound by the native side to the sealed recipe.
   - **Native (`run_authority.c`).**
     - `recipe()` parses v1 and v2 with the design's rules.
     - REGISTER requires exactly 5 fds when `stderr_max != 0` and 4 otherwise. The fifth must match the sealed
       dev/ino, and is dup'd `F_DUPFD_CLOEXEC` ≥ 3.
     - STAGE, before `clone3`: `stderr-g<N>` is created `O_WRONLY|O_APPEND|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC`,
       0600. For a probe unit, the earlier `.xverse-ready` is moved to `.xverse-ready.g<N-1>` with
       `RENAME_NOREPLACE` (N > base), then `.xverse-ready` is created 0700, opened `O_NOFOLLOW|O_DIRECTORY`,
       checked (directory, own uid, mode 0700), and `challenge` is written: 64 lowercase hex characters from
       `getrandom`, `O_EXCL|O_NOFOLLOW`, mode 0400.
     - `child_exec`: after the unchanged `close_range`, fds 0 and 1 are `/dev/null` and fd 2 is the stderr file
       or `/dev/null`. A declared-grace unit gets SIGTERM set to `SIG_DFL` and unblocked before exec.
     - TERM: SIGTERM through the pidfd to the leader only, latched in bit 512, idempotent.
     - `stop_child`: `exited_on_term` (1024) is set before the freeze only if TERM was sent and the leader is
       reaped with the boundary empty. On success the stderr file is capped by `ftruncate` (bit 4096) and closed,
       and the probe fd is closed. `cleanup()` caps as a best effort once the leader is reaped and the boundary
       is empty.
     - QUERY runs the bounded marker check: `ready` is opened `O_RDONLY|O_NOFOLLOW|O_NONBLOCK`, must be a
       regular 64-byte file and equal to the nonce under `CRYPTO_memcmp`; bit 2048 latches.
     - The main loop accepts `kind <= 15 || kind == TERM`. New descriptors are `O_CLOEXEC` and ≥ 3 (a helper
       moves any lower one up). No signal by PID number is added.
   - **Interpretations within the design, recorded here (not deviations).**
     - TERM refusals. A TERM for a unit without a declared grace, or for a superseded generation, is a protocol
       error (REJECTED, which closes the authority); Python never sends it. A TERM whose runtime conditions fail
       (not released, not alive, frozen, stop already saved, retired, or the authority closed) changes nothing
       and is answered TERM_SENT without bit 512, so Python goes straight to the forced STOP (step 3 of the
       design's Python side).
     - Every marker check on QUERY counts toward the cap of 3, including a check that finds no `ready` file.
     - The rename aside accepts `ENOENT`, because a unit may have removed its own earlier directory; an occupied
       aside name fails STAGE.
     - The native REGISTER also checks that the stderr directory is owned by the uid with `mode & 0o077 == 0`
       (defence in depth for the Python admission check of step 3).
     - A failed cap (`fstat`/`ftruncate`) fails the STOP, and therefore closes the authority (fail-closed).
   - **Tests.**
     - `catalog_workload.c` gains the modes `term` (a handler writes `TERM` and exits 0), `ignore-term`,
       `marker`, `marker-late` (answers after 0.4 s), `marker-wrong`, `marker-never`, `stderr-flood` (16 KiB on
       fd 2) and `streams`. The mode `marker` (an immediate answer) is an addition to the design's list. The
       existing modes are unchanged.
     - New `test_stabilization_s1b_native.py`, 34 tests: the FR-013 cases (TERM honoured with
       `exited-on-term`; TERM ignored, then forced; marker never; marker late within the bound; stderr cap
       overflow); cancel, then a forced stop with no TERM; a frozen unit is not sent TERM; TERM rejected without a
       declared grace; TERM before release signals nothing; the latch; the cap of 3 checks; a wrong nonce, a
       symlink to the challenge, a FIFO, an oversized file and a directory, none matching and none blocking; the
       per-generation rename aside; an occupied aside name; a stale directory and a symlinked directory
       rejecting STAGE; an existing stderr file or symlink rejecting STAGE without touching its target; streams
       and handles with and without stderr; the REGISTER fd count and directory identity and mode; native
       rejection of invalid v2 recipes; and the AR17 v1 bytes of an undeclared recipe.
     - `test_affa_config.py`: the v2 layout bytes, the bounds and the untrusted v2 bytes (+3 tests, 21 cases).
       `test_affa_client.py`: TERM refused after a cancel before it is sent. The existing case
       `dict(state=512)` of `test_uncorrelated_real_reply_revokes_original_issuer` becomes `state=8192`: 512 is now
       a valid bit, so the first unknown bit under the widened mask is tested instead.
   - **Runs (installed wheel, one pytest process at a time).**
     - `test_stabilization_s1b_native.py`: 34 passed (load 4.8 at start).
     - `test_affa_config.py`, `test_affa_protocol.py`, `test_affa_client.py`, `test_affa_native.py`,
       `test_dv05_dv06_bounds.py`: 113 passed and 1 failed (the `state=512` case above, load 3.9); after the
       update, `test_affa_client.py` 22 passed (load 4.3).
5. **S1b step 2: the schema change breaks the SD-0001 candidate lock; the design does not cover it (written at
   20:07:42 2026-10-23, load about 3.01, before the re-pin).**
   - **Fact.** `xdl/candidates/sd0001/candidate.lock.json` pins `profileSchema.sha256` of
     `xdl/profiles/runtime-compatibility-v0.2.schema.json` (`4aa1c811…`). `scripts/validate_sd0001.py` compares it.
     With the S1b schema (`process.stop`, `process.stderr`, the `inheritedHandles` description) on the
     installed wheel, `tests/test_sd0001_validator.py` gives 2 failed and 2 passed:
     `test_reviewed_candidate_passes_but_remains_unplannable` and
     `test_resource_digest_drift_fails_before_xdl_validation` (a schema mismatch is reported first).
   - **The design is not wrong, but incomplete here.** It requires the schema change and does not name the lock.
     The SD-0001 graph declares no S1b control, so its plan digest (`ccab18b9…`, pinned in the lock and in
     `test_m3_catalog_runtime.py`) must stay unchanged.
   - **Correction.** Re-pin only `profileSchema.sha256` in the lock to the new schema hash. Every other lock field,
     including `planDigest`, stays as is, and the validator must pass unchanged. The historical review records
     `docs/engineering/{argus,xdl}-lite/internal-review.json` keep the old hash, because they record their own
     revision. This is implemented in the step 2 commit, and recorded there.
