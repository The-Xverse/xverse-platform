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
6. **S1b step 2: the catalog and the schema are implemented (written at 20:09:30 2026-10-23, load about 3.55).**
   - **Catalog (`src/xverse_xdl/catalog.py`).**
     - New `ProcessControls(stop_grace_seconds, stderr_maximum_bytes)`, each `None` when undeclared, bounded to
       (0, 4] s and 1..1048576 bytes. `LifecyclePlan.process_controls` is set for every process plan (an
       undeclared `ProcessControls()` when nothing is declared) and is `None` otherwise.
     - The digest input's `process` object carries `stop {graceSeconds}` and
       `stderr {capture: run-scoped-private, maximumBytes}` only when they are declared.
     - `XVERSE-CATALOG-READINESS-PROBE` is raised, and the entry is not derived, when an observe action declares
       `nonce-marker` for a non-process provider. The probe identity is the observe `condition`, already in the
       digest.
   - **Schema (`runtime-compatibility-v0.2.schema.json`).** Optional `process.stop` (`graceSeconds` in (0, 4],
       no other key) and `process.stderr` (`capture: run-scoped-private`, integer `maximumBytes` in 1..1048576,
       no other key). The `inheritedHandles` description now states that no control descriptor is inherited, that
       fds 0 and 1 are `/dev/null`, and that fd 2 is `/dev/null` or the declared private stderr file. The v0.1
       schema is unchanged.
   - **SD-0001 lock (finding 5).** Only `profileSchema.sha256` is re-pinned, to `cfa7af7f…`. `planDigest`
     `ccab18b9…` is unchanged, and the validator passes.
   - **Tests (`tests/test_m3_catalog_runtime.py`, new class `S1bProcessControlTests`, 5 tests).**
     - A golden check: an undeclared v0.2 process plan keeps the digest `dfdeb5fa…`, computed with the pre-S1b
       `catalog.py` of `fd3579932` (loaded from `git show`) and identical under the new code.
     - Declared `stop`, `stderr`, both, and `nonce-marker` each give a distinct digest and the expected controls.
     - Nine schema rejections (grace 0 and 4.5, an empty `stop`, an extra key, a cap of 0 and 1048577, a wrong
       capture, a missing cap, an extra `path` key); a grace of 4 is valid.
     - The probe diagnostic for a fixture provider, and the direct bounds of `ProcessControls`.
   - **Runs (installed wheel).** Before the re-pin: `tests/test_sd0001_validator.py` 2 failed, 2 passed (finding
     5). After it: `tests/test_m3_catalog_runtime.py`, `tests/test_sd0001_validator.py`, `tests/test_schema.py`
     and `tests/thesis_lite/xdl` gave 182 passed and 39 subtests passed (load 3.7). After the `__main__` guard was
     moved back to the end of the file, `tests/test_m3_catalog_runtime.py` gave 27 passed and 34 subtests passed.
7. **S1b step 3: the broker, the teardown and the schedule are implemented (written at 20:20:07 2026-10-23, load
   about 6.18).**
   - **`run_broker.py`.**
     - `UnitAdmission.stderr_directory` (default `None`, not in `repr`): an absolute path without `.`/`..`
       components or NUL, from the trusted caller.
     - Admission (`_controls` in `_admit_image`): `grace_ms = max(1, round(graceSeconds·1000))`, `stderr_max`
       from the plan, and `probe` from the observe condition, which must be in `READINESS_PROBES`
       (`ML-RUN-PROBE-UNSUPPORTED`). A declared stderr requires a directory, and a directory requires a
       declaration (`ML-RUN-STDERR-ADMISSION`). The directory is opened component by component with
       `O_NOFOLLOW|O_DIRECTORY`. It must be owned by the uid, with `mode & 0o077 == 0`, and empty
       (`ML-RUN-STDERR-DIRECTORY`); not the cwd (`ML-RUN-STDERR-SHARED`); and not inside the collection source
       root, by a `..` walk against `storage.collection.source_identity` (`ML-RUN-STDERR-ROOT`). A probe unit
       needs no stale `.xverse-ready` (`ML-RUN-PROBE-STALE`) and a cwd inside the source root
       (`ML-RUN-PROBE-ROOT`, also when no collection is admitted).
     - Across units (`_admit_distinct`): stderr directories are distinct from each other and from every unit's
       cwd (`ML-RUN-STDERR-SHARED`); a probe unit's cwd is shared with no other unit (`ML-RUN-PROBE-CWD`); and
       Σ coverage artifact `maximumBytes` + Σ `stderr_max` × generations ≤ 16 MiB (`ML-RUN-STDERR-BUDGET`).
     - The AR17 v2 recipe is emitted only for declared controls. REGISTER sends the directory as a fifth fd, which
       is retained in `_Image.stderr_fd`, kept on ADVANCE, and closed by `dispose` or by the admission failure
       path.
     - `stop_owned(handle, deadline, *, grace_until=None)` is two-step. If a grace is declared, `grace_until`
       is set (finite, else `ML-RUN-STOP-GRACE`), no TERM is held, and starts are not closed and the latch is not
       cancelled: TERM is sent with the end `min(deadline, now + 0.5, lease − 1 µs, generation − 2 s − 1 µs)`, and
       its ack is retained in `_term_ack`, pinned in `_identity`. If bit 512 is set, the retained pidfd is
       waited on in steps ≤ 10 ms until `min(t + grace, grace_until)`, an exit, a cancel or closed starts, with
       the exchange lock free. Then STOP as before. A STOPPED with 1024 and without 512 is `ML-RUN-STOP-ACK`.
     - `NativeGenerationClosure.stop_mode` (default `None`): `exited-on-term` or `forced` once an actual
       STOPPED ack is held. The broker projection is unchanged.
     - `observe` sets `ProcessObservation.marker_ready` from bit 2048. The new field defaults to `False` and
       is never set by LC09. New properties: `RunUnitIssuer.stop_grace_seconds` and `readiness_probe`.
   - **`probe_identity.py`** (named in the design for step 4) is added here, because the broker admission needs
     `READINESS_PROBES = ("running", "nonce-marker")`. The probe admission itself is tested in step 4.
   - **`teardown.py`, `service_time.py`, `schedule_plan.py`.**
     - `STOP_FORCE_RESERVE_SECONDS = 0.5`.
     - `_stop` passes `grace_until = deadline − 0.5 − SIZING_MARGIN·record` for a declared grace only.
       `_emergency` passes nothing, so it is always forced.
     - `_need`: `max(SIZING_MARGIN·est('phase:stop'), grace + 0.5) + SIZING_MARGIN·est('phase:cleanup')` when a
       grace is declared and the stop is pending. This is my reading of the design's
       `max(est('phase:stop'), grace + reserve)`: the margin widens the estimate, not the admitted bound. The
       undeclared expression is unchanged.
     - `admit_schedule` rejects `grace + 0.5 > NORMAL_SHARE·per_unit_seconds` (`ML-SCHEDULE-STOP-GRACE`). An
       undeclared schedule keeps its digest.
   - **Tests: new `test_stabilization_s1b_broker.py`, 19 tests on real broker stacks**, with controls declared
     in the actual v0.2 catalog payload:
     - undeclared units keep AR17 v1 and a forced stop;
     - a scenario `stop` with TERM honoured (`exited-on-term`, TERM in the marker, the epoch unchanged, the
       other unit forced);
     - TERM ignored, then forced after the grace;
     - the terminal fence after a cancel is forced with no TERM;
     - the emergency path passes no grace;
     - a non-finite `grace_until` is refused;
     - the `_need` values;
     - the declared stderr end to end (the recipe identity, 5-fd REGISTER, the cut to 1000 bytes, bit 4096,
       mode 0600);
     - nine stderr admission refusals: undeclared, missing, group-readable, not empty, a symlink component,
       absent, shared, the cwd, and the budget with 2 units × 9 generations × 1 MiB;
     - the directory inside the collection source root;
     - the schedule grace bound.
   - **Runs (installed wheel).**
     - Before the new tests: `test_run_broker.py`, `test_run_teardown.py`, `test_teardown.py`,
       `test_schedule_plan.py`, `test_stabilization_cancel_conflict.py`: 99 passed (load 3.8).
     - `test_stabilization_s1b_broker.py`: 17 passed (load 3.4); after the distinct codes and two added cases,
       19 passed (load 4.0).
     - `test_run_broker.py`, `test_run_teardown.py`, `test_teardown.py`, `test_schedule_plan.py`,
       `test_stabilization_cancel_conflict.py`, `test_dv05_dv06_bounds.py`, `test_launcher.py`,
       `test_provider.py`: 163 passed (load 4.0 at start, 6.0 at end).
8. **S1b step 4: readiness, evidence, coverage and the LC09 refusal are implemented (written at 20:39:21 2026-10-23,
   load about 7.67).**
   - **`providers.py`.**
     - Admission accepts `READINESS_PROBES`.
     - `bind` refuses a `CatalogLauncher` for a non-`running` probe (`ML-PROBE-BINDING`).
     - During `start()`, the unit whose readiness attempts are in progress is marked (`_readying`). Its samples
       carry the declared probe id, and they are ready only when the unit is running and, for `nonce-marker`,
       `marker_ready` is set. Every other sample, including the health checks and the dependency checks, stays
       `running`.
     - Marker attempts are spaced at `t0 + k·W/A`, with `W = min(policy timeout, observe timeout)` and `t0`
       taken after RELEASE; an attempt that would fall after the deadline is not made. The result is otherwise
       `ML-PROBE-NOT-READY`.
     - **Interpretations.** The `running` probe keeps its existing 5 ms yield, so undeclared units keep their
       timing. The readiness mode is a marker on the facade rather than a new `_query` parameter, because an
       existing test (`test_dispatch_observe.py`) wraps `_query(self, unit, until)`. The new parameter broke it
       (1 failed, 143 passed in the first run), and the marker keeps that contract.
   - **`lifecycle_evidence.py` (worker and receipt check).** `probe` and `ready` annotations carry the
     declared observe condition; `health` and `health-loss` carry `running`. The worker derives the identity
     from the sealed plan, never from the client. `validate_receipt` expects the same.
   - **`coverage.py`.**
     - Admission accepts `READINESS_PROBES`, otherwise `ML-COVERAGE-PROBE` as before. A unit row gets
       `readinessProbe` only for a non-`running` probe, so undeclared admission bytes and digests are unchanged.
     - Validation accepts that optional key only with the value `nonce-marker`.
     - `_payload` requires `probeId == readinessProbe` for unit-scope `probe` and `ready` annotations, and
       `running` for `health`, `health-loss` and step-scope probes. The scenario observe steps stay liveness:
       `dispatcher.py` and `schedule_evidence.py` are unchanged.
   - **`launcher.py`.** `make_launch_recipe` refuses any declared control or a non-`running` probe with
     `ML-LAUNCH-CONTROL-UNSUPPORTED` (D-2).
   - **Tests.**
     - `catalog_workload.c` `stderr-flood` now writes a generated canary (an LCG over 16 KiB), so no literal of
       the content exists in the image. The native cap test checks the first 1000 bytes of the same sequence.
     - New `test_stabilization_s1b_readiness.py`, 15 tests:
       - marker readiness on real broker stacks with an admitted collection: the coverage row, probe and ready
         `nonce-marker`, health `running`, the other unit `running`;
       - marker late within the window, ready on a spaced attempt;
       - marker never: `ML-PROBE-NOT-READY` after exactly three failed `nonce-marker` probes spaced ≥ 0.45 s,
         with the latch cancelled;
       - five probe admission refusals: no collection, a shared cwd, a stale directory, a cwd outside the root,
         and an unsupported condition (the last without collection, because an admitted coverage refuses it
         earlier with `ML-COVERAGE-PROBE`);
       - the LC09 refusal through `launch_stack`;
       - the privacy canary: a declared stderr of 4096 bytes on a real run with teardown and collection. Every
         file under the test directory except the private stderr directory, the broker projection, the
         collection receipt and the public M3 records contain neither the content windows, nor the directory's
         random name, nor its path;
       - synthetic, labelled coverage acceptance (`test_coverage.Fixture` with one unit admitted as
         `nonce-marker`): complete with matching annotations, not complete with `running` ones;
       - the payload identity rules;
       - the admission rejection of `running`, `http-ok` and `1` as `readinessProbe`.
   - **Runs (installed wheel, load 7.9–8.6 from other host users).**
     - First run of `test_provider.py`, `test_coverage.py`, `test_launcher.py`,
       `test_readiness_dispositions.py`, `test_dispatch_observe.py` and `test_coverage_producers.py`: 1 failed,
       143 passed (above). After the fix, `test_dispatch_observe.py` and `test_provider.py` gave 37 passed.
     - `test_stabilization_s1b_readiness.py`: first 13 passed and 2 failed (the test's own projection
       serialization, and the unsupported case reaching coverage first); after the fixes, 15 passed.
     - Batch 1: the three S1b files, `test_provider`, `test_coverage`, `test_coverage_native`,
       `test_coverage_producers`, `test_readiness_dispositions`, `test_dispatch_observe`,
       `test_collection_runtime` and `test_outcomes`: 238 passed.
     - Batch 2: `test_launcher`, `test_runtime_entry`, `test_affa_native`, `test_affa_config`,
       `test_affa_client`, `test_run_broker`, `test_run_teardown`, `test_teardown`, `test_dv05_dv06_bounds`,
       `test_stabilization_cancel_conflict` and `tests/test_m3_catalog_runtime.py`: 200 passed and 34 subtests
       passed.
     - Batch 3: `test_schedule_plan`, `test_lazy_dispatcher`, `test_generation_restart`, `test_recovery` and
       `tests/test_sd0001_validator.py`: 97 passed.
   - **Open for the owner.**
     - `stop_mode` is exposed in `NativeGenerationClosure` and in the native STOPPED bits, but no public
       evidence carries it yet (the broker projection and the teardown records are unchanged, so that undeclared
       bytes stay identical). If S1c-2 or S1d needs it in `maestro-run.json`, that is a harness capture.
     - The authority binary digest changed with `run_authority.c`, so S1c re-pins it (design risk 1).
     - The full suite and DV12 have not been run here; per the instructions, they belong to the owner.
9. **Independent review 1 of S1b at `41a6aa866` (written at 20:57:34 2026-10-23): PASS for the full run and DV12,
   no HIGH, 1 MEDIUM and 4 LOW. Recorded before any repair.**
   - **Confirmed.**
     - Native fd, symlink and TOCTOU safety.
     - TERM only through the pidfd, never to a frozen, unreleased, stopped or retired unit, or after CANCEL.
     - The stderr cap and the bounded, non-blocking, latched marker check.
     - STAGED stays 37, and undeclared units are byte-identical.
     - The exchange lock is free during the grace (D-4).
     - Privacy: the canary is complete.
     - Finding 5 is legitimate. No gate pins the old schema hash; the historical `affa17/*/frozen-inputs.json`
       records keep it.
     - 92 and 232 targeted tests passed at load 4–6.5.
   - **MEDIUM-1.** `stop_mode` (`exited-on-term`/`forced`) exists only natively and in the in-memory
     `NativeGenerationClosure`. No persisted or public evidence carries it (FR-009, A2).
   - **LOW-1.** Marker attempts at `t0 + k·W/A` never probe the last `W/A` of the window. A marker written at
     1.1 s of a 1.5 s window is missed.
   - **LOW-2.** A cancel during the grace makes the scenario stop an emergency result through the existing
     `ML-TEARDOWN-TERMINAL-SCOPE` refusal of the outcome record. It is fail-safe, but untested, and S1b widens
     the window to the grace.
   - **LOW-3.** The stale check at admission covers `.xverse-ready` only. An existing `.xverse-ready.g<N>` aside
     name fails late, at the restart STAGE.
   - **LOW-4.** The widened state mask (`~8191`) applies to undeclared units too. A native regression setting
     2048 or 4096 there would be accepted.
   - **Planned dispositions.**
     - MEDIUM-1: the owned harness records `nativeUnits` (the `stop_mode` field), and S1c-2 part 2 asserts it.
       S1b persists nothing new. This is recorded for the author at acceptance.
     - LOW-1: space the marker attempts so that the last one probes the end of the window, keeping a round-trip
       reserve.
     - LOW-2: add a test, and declare the result as expected.
     - LOW-3: reject any `.xverse-ready*` entry in the cwd at admission.
     - LOW-4: per-issuer check that no reply carries a bit for a control the unit did not declare.
10. **Repair of independent review 1, the finding 9 dispositions (written at 21:04:53 2026-10-23, load about 3.86).**
    - **LOW-1, repaired.**
      - `providers.readiness_offsets(W, A)` spaces the marker attempts at `t0 + k·(W − reserve)/(A − 1)`, with
        `reserve = min(0.25, W/A)`, and makes a single attempt at `t0` when `A = 1`. The last attempt now probes
        the end of the window less one round trip (W = 1.5 s, A = 3: 0, 0.625 and 1.25 s).
      - Tests:
        - pure offsets for A = 3, 2 and 1, and for a window below the reserve;
        - on a real broker stack, a marker written 0.9 s after exec with A = 2 and W = 1.5 s, which is after
          (A − 1)/A·W = 0.75 s, the old last attempt. It is found by the second attempt at t0 + 1.25 s: probe
          failed, probe succeeded, ready.
      - A = 2 was chosen for this test because it gives a 0.35 s margin. With A = 3, a marker after 1.0 s
        leaves at most 0.15 s before the attempt at 1.25 s.
      - New workload mode `marker-after-<ms>`. In the marker-never test, the spacing bound is now ≥ 0.6 s and
        the elapsed bound ≥ 1.25 s.
    - **LOW-2, test added; the behaviour is expected (fail-safe), with one addition to the reviewer's
      expectation.**
      - **Common to every run.**
        - A cancel 0.4 s into a 2 s grace is confirmed natively in a few ms, with no revoke, because the exchange
          lock is free during the grace (D-4).
        - The grace wait ends at the cancel, and the phase takes under 2 s.
        - The forced STOP succeeds with bit 512 and without 1024 (`stop_mode = forced`).
        - The phase returns the existing emergency result `ML-TEARDOWN-NORMAL-INCOMPLETE`, with the leader
          reaped and C1 empty and released.
      - **Usual path (7 of 8 local runs), as the reviewer reproduced.** The STOP follows the completed CANCEL, and
        the storage client refuses the normal outcome record with `PersistenceError('ML-TEARDOWN-TERMINAL-SCOPE')`.
      - **Second path, observed once in 8 runs.**
        - `RunBroker.cancel` sets the latch before its CANCEL exchange. The grace wait can therefore see the
          cancel while the CANCEL still holds the connection lock. The STOP is then refused before send
          (`ML-AFFA-CONFLICT`, no effect and no revoke), and `_emergency` makes the forced STOP after the cancel
          completes. The final result is the same emergency result.
        - A second test makes this path deterministic, by holding the CANCEL exchange 0.15 s under its lock, and
          passed 3 of 3 runs.
      - **Disposition, for the reviewer.** Both paths are fail-safe and declared expected here. No code changed for
        LOW-2.
      - **An optional tightening, not made.** The grace wait could end on `_starts_closed` only, or a pre-send
        `ML-AFFA-CONFLICT` on STOP could be retried within the S1a-3 bound. The phase would still be an
        emergency result, because the outcome record is refused after a cancel.
    - **LOW-3, repaired.** Admission scans the pinned cwd fd with `os.scandir`, which never follows a link. Any
      entry named `.xverse-ready` or starting with `.xverse-ready.g` is `ML-RUN-PROBE-STALE`. Tests: an aside
      directory `.xverse-ready.g1` and a dangling symlink `.xverse-ready.g7`, beside the existing
      `.xverse-ready` case.
    - **LOW-4, repaired.**
      - `RunUnitIssuer._declared` checks every reply of `_native` and the INTENT reply in `stage`. It fails
        closed with `ML-RUN-STATE-UNDECLARED` when the state carries:
        - 512 or 1024 without a declared grace;
        - 2048 for a unit that is not a nonce-marker unit;
        - 4096 without a declared stderr.
      - Tests, with crafted replies through a wrapped `AuthorityConnection._exchange`:
        - each of the four bits on an undeclared unit's QUERY is refused;
        - on a unit with a grace and a stderr declared, 512|1024|4096 is accepted and 2048 is refused.
    - **MEDIUM-1, no S1b code change.** `NativeGenerationClosure.stop_mode` is recorded by the owned harness
      through `nativeUnits`, and S1c-2 part 2 asserts it. S1b persists nothing new, so undeclared evidence bytes
      stay identical. This is recorded for the author at acceptance.
    - **Runs (installed wheel, rebuilt; one pytest process at a time).**
      - First, `test_stabilization_s1b_broker.py` and `test_stabilization_s1b_readiness.py`: 43 passed and 1
        failed. The LOW-2 assertion expected a `TeardownError`, but the refusal is a `PersistenceError` (load 3.9).
      - The LOW-2 test alone: 1 failed, the second path above (`ML-AFFA-CONFLICT`); then 6 of 6 runs on the usual
        path (load about 4.5).
      - Both LOW-2 tests: 2 passed in each of 3 runs (load 3.8).
      - The requested set, `test_stabilization_s1b_native.py` (34), `test_stabilization_s1b_broker.py` (26),
        `test_stabilization_s1b_readiness.py` (19), `test_provider.py` (35), `test_run_teardown.py` (9),
        `test_teardown.py` (27), `test_affa_client.py` (22), `test_run_broker.py` (11) and
        `test_stabilization_cancel_conflict.py` (6): 189 passed in 131 s (load 4.1 at start, 4.2 at end).
11. **Independent re-review of the finding-10 repair at `23d781ca2` (written at 21:13:20 2026-10-23): PASS. No HIGH or MEDIUM;
    3 informational LOW items.**
    - **Tests.** The s1b broker and readiness tests gave 45 passed in each of 3 runs. native, provider, run_broker,
      teardown, run_teardown, affa_native and dv05_dv06 gave 140 passed, at load 3.6–4.8.
    - **Confirmed.**
      - The readiness offsets are correct across A = 1–3 and windows from 1e-9 s to 5 s, within the native cap of 3.
      - Both LOW-2 endings are fail-safe and asserted: no revoke, the cancel confirmed, the stop forced.
      - The stale scan follows no links and leaks no fd.
      - `_declared` covers every `_native` and INTENT reply and never rejects a legitimate declared reply.
    - **LOW notes, accepted as is.**
      - ADVANCED and REGISTERED replies are not passed through `_declared`. Nothing reads that state, and STAGE
        requires exactly 37.
      - The scan rule is exactly `.xverse-ready` and `.xverse-ready.g*`, which matches the native aside name.
      - Under a tight outer deadline, the later final readiness attempt is dropped more often. It fails closed with
        `ML-PROBE-NOT-READY`.
    - **Next.** The decisive full installed-wheel run, DV12 and CAPA step 11.
12. **S1b: the decisive full installed-wheel run and the DV12 gate (written at 22:00:48 2026-10-23).**
    - **Rebase.** Before the run, the branch was rebased onto the S1a-2 candidate head `6f669ec4e`. The commits there
      after `d8b44719c` are evidence and logs only, so the code did not change; this gives CAPA its step-10 parent.
      The sparse checkout was widened to the affa19 driver scripts, the inputs, the step-10 register and the affa17
      tooling.
    - **Run.** `evidence/affa19/stabilization-s1b/platform-regression-20261023c-1`, head `78ed2f0e6`, driven by
      `run-z-quiet-loop.sh`.
      - Triggered at 20:17:51Z at load 3.46, on the first attempt.
      - **Clean:** 2524 passed, 1 skipped (lane admission, as before), 39 subtests, in 2478 s.
      - The maximum sampled load was 6.31.
    - **DV12 gate.** `--scope code`: `accepted_as_evidence: true`, with no blockers. The run and candidate code
      are both `2d17c186…`.
    - **Next.** CAPA step 11 (parent step 10, `4b04cb4a…`), built after this log is committed.
13. **CAPA successor step 11 for S1b (written at 22:01:43 2026-10-23), built after finding 12 was committed (`681a2d01d`).**
    - **A process slip, corrected.**
      - The first attempt to commit finding 12 was refused for paths outside the sparse checkout. A step-11 register
        had already been built over the uncommitted log; it was deleted unused, before any verification passed.
      - The sparse checkout was then widened, finding 12 was committed, and the register was rebuilt.
      - The sparse checkout is now disabled: the verifier needs the bound files of earlier steps.
    - **Location.** `evidence/affa19/capa-20261023-stabilization-s1b-step11/`, built by
      `build-capa-20261023-stabilization-s1b-step11.py` over `platform-regression-20261023c-1`.
    - **Additive over step 10 (`4b04cb4a…`).** No record was opened, changed or closed.
    - **Register `3eb39cda32a0376eefe44099e4eff3c573f1d26253986627bde697b0d2ea99d5`:** 56 records and 712 bindings. The 25
      new bindings cover:
      - this log, the design record and the three ADRs;
      - the changed native and Python sources, the schema and the SD-0001 lock;
      - the four test files;
      - the run's `SHA256SUMS` and its DV12 verdict.
    - **Successor verifier:** rc 0, with 56 records and 712 bindings verified.
    - **Parent preservation:** `parent_preserved: true`. All 687 parent bindings were checked, and none changed or
      was lost.
    - **S1b is ready for the author's acceptance.** Delegated revisions DR-7 to DR-10 and the MEDIUM-1 disposition
      (`stop_mode` carried through the harness's `nativeUnits`) are flagged in the thesis package.
14. **Post-candidate live observation on the platform stack (S1a-2 → S1b → S1a-3 at `d747f1e0c`): a start-up
    readiness failure ends in a revoke and an incomplete closure (written at 23:34:03 2026-10-23; recorded before
    any diagnosis or repair).**
    - **Run.** The S1c-2 part 2 development run `runs/lite-stabilization-s1/s1c2-part2-dev-20261023/dev-…-233239-no-carla`
      (compat finding 42). No simulator was running, so the owned adapter, which declares `nonce-marker`, never
      wrote its ready file.
    - **Observed.**
      - `ML-PROBE-NOT-READY` after 3 attempts.
      - `persistenceFailure: ML-PERSIST-CHILD` (kind `schedule`, stage `receive`, sequence 29).
      - The broker cancel result: `native_epoch_confirmed: false`, `issuer_dead: true`, `issuer_reaped: true`.
      - The closure: `ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN`, `cleanupComplete: false`, writer `rpc-unresolved`, and the
        Maestro root `open`.
      - In the same run set, five successful runs and one cancel run closed normally.
    - **Contrast.** Before S1b, the same case ended `ML-RUN-CHILD-EXIT` with a clean `failed` writer (S1a-2 runs).
    - **Not yet known.**
      - Which path revoked the authority:
        - a conflict longer than the 0.5 s S1a-3 wait;
        - a non-conflict refusal;
        - an authority or worker death before the cancel.
      - Whether S1b's readiness path (marker QUERYs, `ML-RUN-STATE-UNDECLARED`, the issuer `_declared` check)
        contributes.
    - **Effect.** This blocks the S1b and S1a-3 acceptances until it is diagnosed: a start-up failure must still close
      its evidence (P4). Next: a deterministic reproduction in the composed runtime, with a marker unit that never
      becomes ready, and capture of the revoke cause.
15. **Diagnosis of finding 14: a K.CANCEL whose deadline passes the unrenewed authority lease makes the native
    authority exit, and the client revokes (written at 23:44:00 2026-10-23, load about 3.7; before any repair).**
    - **Cause (high confidence).** This is case (e) of the finding-14 list. It is a latent increment-17 defect,
      and S1b's marker readiness exposes it.
      1. The last marker attempt fails, and `ProcessReadiness.start` raises `ML-PROBE-NOT-READY`
         (`providers.py:454`). Its handler cancels (`providers.py:456` → `providers.py:579` → `owner.py:763-765`),
         so `RunBroker.cancel(reason)` is called with **no deadline**.
      2. `RunBroker.cancel` sets the CANCEL end to `min(now + 1, generation − 2, limit)` (`run_broker.py:1056`).
         It is never clamped to `connection._lease`, although the authority is still open. The client-side check
         exempts the cleanup kinds, CANCEL included, from the lease (`affa_client.py:275-278`), so the frame is
         sent.
      3. The native authority admits a frame on an open authority only when `until <= g->lease`, for every kind,
         CANCEL included (`run_authority.c:666`, unchanged since `1e081a1ba`). It answers an invalid frame with
         `cleanup` and exit (`run_authority.c:670`). The workloads are killed and waited natively, and the helper
         exits with status 0.
      4. The client receives EOF without credentials (`ML-AFFA-SENDER`, `affa_client.py:200`). The error comes
         after send, so `_exchange` revokes (`affa_client.py:408-421`). `_cancel_exchange` re-raises a
         non-conflict error, and `cancel` revokes again (`run_broker.py:1067-1083`), giving
         `native_epoch_confirmed=False, issuer_dead=True, issuer_reaped=True, diagnostic=None`.
      5. The run-bootstrap root sees that the authority helper is gone outside terminal mode and runs its
         cleanup, which SIGKILLs every helper, the storage worker included (`bootstrap.c:316`, `bootstrap.c:287`).
         Any persistence RPC in flight then fails `ML-PERSIST-CHILD` at `receive`. The revocation carries
         `workload_waits_known=False`, so the closure ends `ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN` with
         `cleanupComplete=False`.
    - **Why S1b exposes it.**
      - Before S1b, a start-up failure was a child exit. The `running` probe saw it within milliseconds of
        RELEASE (5 ms yields), while the lease still had seconds left.
      - A `nonce-marker` start spends up to the window W inside one start step. The step's end is capped at the
        bootstrap lease (`dispatcher.py:1088`), and no renewal runs inside `facade.start`. The failure, and its
        cancel, therefore land near the end of the lease.
      - The defect does not depend on S1b. Any deadline-free `RunBroker.cancel` in the last second of an
        unrenewed lease revokes. Every `owner.cancel` reason reaches it this way (for example
        `readiness-health-failed`, `dispatcher-failed`, `gate-uncertain`), as does `run-release-uncertain`
        (`run_broker.py:696`).
      - The dispatcher's terminal fence is not affected, because it clamps its end to the lease
        (`dispatcher.py:1405-1407`). Here it returns the already revoked `_cancel_result`.
    - **Evidence from the run record (`dev-s1c2p1-20261023T233239-no-carla`).** Times are relative to
      `monotonicStartNs`.
      - `carla-adapter` issued at 2.811 s, with `nonce-marker` probes failed at 2.872, 3.748 and 4.623 s. These
        are t0 + `readiness_offsets(2.0, 3)` = 0, 0.875 and 1.75 s.
      - The persistence `schedule` RPC, sequence 29, started at 4.637 s and failed at 4.642 s. That is 14 ms
        after the last probe and far below the 0.5 s conflict wait, so a K.CANCEL conflict is ruled out.
      - The authority lease was created between the plan write (`experiment-plan.json` mtime, 0.284 s) and
        `entry.start` (first event, 1.274 s), as `now + 4.8 s`. Its end was therefore at 5.08–6.07 s, and the
        CANCEL deadline of about 5.62 s is past it whenever the lease was created before about 0.82 s.
      - The record does not hold the lease value or the authority helper's return code, so the live run alone does
        not pin the mechanism. The reproduction below gives the same signature.
      - The empty `stderr-g1` files and the challenge with no `ready` in `carla-adapter/.xverse-ready` agree with a
        unit that ran and was killed. They do not agree with an S1b staging fault.
    - **Ruled out.**
      - **(a) A conflict longer than 0.5 s.** The 14 ms timing above. The start step runs in the dispatcher
        thread, and nothing else holds the connection lock there.
      - **(b) A native REJECTED.** Native CANCEL refuses only a non-zero slot, generation, body or lease field
        (`run_authority.c:527-530`), and the client frame has none. A REJECTED reply would also leave the helper
        alive until the client's SIGKILL. In the reproduction it exits by itself with status 0.
      - **(d) An S1b post-send check.** `_declared` runs after `_exchange` returns (`run_broker.py:1252`, `1290`),
        outside its revoke-on-error block, and is not applied to CANCEL. The marker unit declares a probe, so bit
        2048 is legitimate. The dispatch diagnostic was `ML-PROBE-NOT-READY`, not `ML-RUN-STATE-UNDECLARED`. The
        state mask (`~8191`) admits every S1b bit.
    - **Reproduction: `tests/thesis_lite/maestro/test_stabilization_s1b_start_failure.py`.** The tests run on the
      installed wheel (`d0fed3d1…`, built from `34d45f642`). They assert the correct behaviour, so the defect
      cases fail. The only test-side change is a wait that places the cancel 0.6 s before the lease end. A
      test-only wrapper records each `_exchange` error as (kind, code, `deadline_ns − lease_ns`).
      - **Broker level, `broker_stack`, no S1b control declared.** `RunBroker.cancel('readiness-start-failed')`:
        - with more than 1 s of lease left (control): **passes**;
        - 0.6 s before the lease end: **fails** in each of 4 runs. The recorded error is
          `('CANCEL', 'ML-AFFA-SENDER', +0.400 s)`, and the result is `native_epoch_confirmed=False`,
          `issuer_dead=True`. The authority helper's own exit is `waitid` `si_code=1` (exited), `si_status=0`.
      - **Composed runtime, the `test_runtime_entry.runtime` fixture through `_OriginalRuntimeRun.start`.** The
        sink declares `nonce-marker` in `marker-never` mode.
        - early cancel (control): **passes**. The cancel is confirmed natively, there is no persistence failure,
          cleanup is complete and the writer is `failed` or `closed`, so the expected outcome is reachable on this
          stack;
        - cancel in the last second of the lease: **fails** in each of 6 runs, with `ML-PROBE-NOT-READY`, the
          revoke as above and `ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN`.
        - Five of these runs printed the persistence outcome. In 3 of them the live signature is reproduced in
          full: `ML-PERSIST-CHILD` (kind `schedule`, stage `receive`), storage helper return code −9, and writer
          `rpc-unresolved`/`open`. In the other 2 the writer ended `failed`. The probable reason (an inference,
          not instrumented) is that the dispatcher's terminal service put the root into terminal mode before
          its 10 ms poll saw the helper's exit. The persistence loss is a race; the revoke is deterministic.
      - **Last result:** 2 failed, 2 passed in 14.46 s. Temporary RPC-timing instrumentation, used once in the
        test file, was removed before commit. No `src/` change.
    - **Proposed repair** (an ADR-ML3-AFFA-0001 amendment first, as for S1a-3):
      - **R1 (recommended): native.** Admit a CANCEL whose deadline passes the lease:
        `(g->closed || kind == CANCEL || until <= g->lease)` at `run_authority.c:666`.
        - CANCEL only closes and freezes, and can never extend the authority. This matches the client's existing
          exemption of the cleanup kinds, and the native `close_end` already ignores the request deadline.
        - The authority digest changes and must be re-pinned (S1c re-pins anyway, design risk 1).
        - Regressions: this file, plus a native test of a CANCEL past the lease on an open authority.
      - **R2: client only, no re-pin.** Clamp the CANCEL end to `connection._lease − 1 µs` while
        `_starts_closed` is false, as `_until` (`run_broker.py:595-605`) and the terminal fence already do.
        - The window shrinks but does not close. A cancel issued a few milliseconds before the lease end gets a
          deadline shorter than the native freeze and reply, so it times out and revokes.
        - It changes the bounded-wait arithmetic of `_cancel_exchange` (`wait_until`).
      - **R3: scheduling, complementary.** Renew before, or cap the end of, a start step whose declared readiness
        window plus one cancel (1 s) and a reserve does not fit inside the lease. This removes only the start-up
        trigger, not the health or release triggers.
      - **Residual in every option: an already expired lease.** At its lease the native authority closes itself
        and advances its epoch (`run_authority.c:652`). A later CANCEL carries the old epoch, is invalid, and
        again makes the authority exit. Covering that case needs, for example, a native acceptance of a CANCEL
        at epoch − 1 after a lease close, answered as CANCELLED at the current epoch, which the client already
        expects (`affa_client.py:300-304`). This is for the owner to decide with R1.
    - **Harness (S1c, evidence only).** Record `connection._lease` at cancel time and the closure helpers'
      return codes in `maestro-run.json`. The helper return code separates a native self-exit (0) from a revoke
      (−9).
    - **Effect.** The S1b and S1a-3 acceptances stay blocked until a repair is chosen and passes this file.
      Finding 18 of the S1a log (persistence child exits after a cancel, 2 of 10 runs) was attributed to the
      busy-connection conflict, which S1a-2 repaired. This lease mechanism gives the same signature, but this
      diagnosis does not show that it took part there.
16. **Repair of finding 15 per ADR-ML3-AFFA-0001 amendment S1a-5 (thesis DR-13; written at 23:49:11 2026-10-23).**
    - **Code.** `run_authority.c` main-loop validity: `(g->closed||kind==CANCEL||until<=g->lease)`. One line. Every
      other frame check is unchanged.
    - **Tests** (installed wheel rebuilt from the repair, load 3.7–4.1):
      - `test_stabilization_s1b_start_failure.py`: 4 passed. The broker-level and composed-runtime last-second-of-lease
        cases now pass: the cancel is confirmed, there is no revoke, cleanup is complete and the writer is
        `failed`/`closed`. They failed before the repair (finding 15).
      - Related suites: 234 passed. They cover affa native, client, config and protocol, run_broker, both cancel suites,
        the three S1b suites, runtime_entry, run_teardown and dv05/dv06.
      - Further suites: epoch, release-timeout fence, watch token, fenced teardown, leaseguard and fence codec. The
        result is in this log's next update.
17. **Verification additions to finding 16 (written at 23:51:43 2026-10-23).**
    - The epoch, release-timeout fence, watch-token, fenced-teardown, leaseguard and fence-codec suites gave 101
      passed.
    - **Live development no-carla runs** on `b049585bf` (two runs; compat finding 43):
      - the cancel was confirmed natively, with no revoke;
      - no persistence failure, and cleanup complete;
      - the Maestro writer `failed`, with WRITER-STATE only;
      - no residue.
    - **Next.** An independent review of S1a-5, then the full installed-wheel run, DV12 and CAPA step 13 on this head.
