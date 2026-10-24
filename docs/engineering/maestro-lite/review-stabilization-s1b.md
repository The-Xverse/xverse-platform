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
18. **Independent review of S1a-5 (`563223f8b`, `b049585bf`; written at 23:55:55 2026-10-24): PASS, LOW only.**
    - **Confirmed.**
      - The exemption grants nothing: CANCEL only runs `close_authority`, with its freeze bounded by `close_end`, and
        it never touches the lease.
      - The other bounds still apply, the watchdog is single-threaded, and the replay after close is unchanged.
      - No other frame kind can exceed the open lease: QUERY, STOP, RETIRE, TERM, REGISTER and RENEW are clamped by
        `_until`. Only K.CANCEL, from `RunBroker.cancel` and `run_closure._fence`, can, and the exemption now covers it.
      - The reproduction test discriminates. The ADR came before the code, and the diff is one line.
    - **Dispositions.** A full run was already in progress on this head, so no test or code is changed after it:
      - **LOW-1 (no native-level test of the exemption and its limits): carried.** The end-to-end reproduction
        covers the case. The native test is to be added with the next platform change in this area. It should
        assert: a CANCEL past an open lease is answered CANCELLED and leaves the lease unchanged; a non-CANCEL kind
        past the lease still makes the helper exit; ARM, RELEASE and RENEW are refused afterwards.
      - **LOW-2 (the expired-lease residual stays reachable, through `ML-SCHEDULE-LEASE-EXHAUSTED` or a cancel
        after an attempt capped at the lease): the owner decision is recorded here.** The residual is accepted as
        fail-safe: workloads are killed natively and only the evidence closure is lost.
        - R1-epoch−1 (accepting a CANCEL carrying the epoch before a watchdog close) is not adopted.
        - R3 (renew before a long start step) is not adopted.
        - S1c records `connection._lease` at cancel time and the helpers' return codes, so that a recurrence is
          attributable (0 means it exited by itself; −9 means revoked).
      - **LOW-3 (ADR completeness):** after a CANCEL past the lease, `g->deadline` is briefly past it. Its uses
        (`enabled`, the ARM ticket end, the stage wait) all require an open authority. The next frame resets it, and
        `cleanup` and `close_end` do not use it. This note completes the S1a-5 safety reasoning.
19. **The S1a-5 repair: decisive full installed-wheel run and DV12 (written at 00:38:58 2026-10-24).**
    - **Erratum to finding 18.** It was written at 23:55 on 2026-10-23, not on the 24th.
    - **Run.** `evidence/affa19/stabilization-s1a3/platform-regression-20261024e-1`, head `5ae2a3da3` (code equals
      `b049585bf`).
      - Triggered at 22:55:44Z at load 3.68, on the first attempt.
      - **Clean:** 2890 passed, 1 skipped (lane admission), 39 subtests, in 2482 s.
      - The maximum sampled load was 5.29.
    - **DV12** (`--scope code`, candidate `a486717d9`): accepted, with no blockers. The code is `a970c8d5…`.
    - **This run supersedes `platform-regression-20261023d-1`** as the decisive run for the stack head. CAPA step 13
      follows, built after this log is committed.
20. **CAPA successor step 13 (written at 00:39:14 2026-10-24), built after finding 19 was committed (`b06a628f4`).**
    - **Location.** `evidence/affa19/capa-20261024-stabilization-s1a5-step13/`, built by
      `build-capa-20261024-stabilization-s1a5-step13.py`.
    - **Additive over step 12 (`d095ac07…`).** Register `cdbb1506b655708857ee920e0ef968bd2c263ef62e9bda056920edce228284e7`:
      56 records and 724 bindings.
    - **Verifier:** rc 0. **Parent preservation:** `true`; all 718 parent bindings were checked and none changed.
    - **The stack head is ready for the author's acceptance**, with the S1a-5 repair included. The order stays S1a-2,
      then S1b, then S1a-3 (now including S1a-5).
21. **Two failures on the stack `b049585bf` under load 8.4–8.7 (S1c finding 45; written at 00:53:35 2026-10-24, recorded
    before diagnosis).**
    - **(A) Start-up readiness against the start deadline and the lease** (`runs/…/s1c2-part2-dev2-20261024/…-004408-freeze-vcu`).
      - The harness declared a 3.5 s window for the owned units (`ProbePolicy` timeout) inside a 4 s observe budget.
      - lite-driver's attempts came at 3.41 s and 5.04 s; the third was dropped because the outer start deadline cut
        it short. Result: `ML-PROBE-NOT-READY`.
      - Then `ML-PERSIST-CHILD` at validation, the cancel revoked (`issuer_dead`, no native confirmation), and the
        closure incomplete.
      - Hypothesis: the start step runs past the authority lease, which is never renewed during one step. That is the
        declared S1a-5 expired-lease residual (finding 18, LOW-2), now reachable. Recording the lease and helper
        return codes would decide it.
    - **(B) A persistence failure at a cancel** (`…-004728-cancel-paused`).
      - `ML-PERSIST-CLOSED` at `validation` for a `schedule` request at the exact cancel time.
      - The broker cancel was confirmed natively, yet no terminal or closure events follow. `cleanupComplete` is false
        and the native facts are unattested.
      - The plain `PersistenceError` path (`persistence.py:745-746`) requires `_failed` already set. Which path set
        `_failed` at the cancel is unknown. Earlier cancel runs on this stack closed cleanly.
    - **Next.** Diagnosis with deterministic reproductions where possible, then ADR notes, then repairs. The stack
      acceptance is blocked again until both are understood.
22. **Diagnosis of finding 21 (written at 01:06:17 2026-10-24, load about 3.5-3.8; before any repair; no `src/` change).**
    Times are relative to each record's `monotonicStartNs`. Reproductions:
    `tests/thesis_lite/maestro/test_stabilization_stack_load_failures.py`, on the installed wheel `2efbd893…`, built
    from `c769a2692`. Every test asserts the correct behaviour. **Last result: 4 failed, 1 passed (the control), in
    16.89 s.**
    - **(B) Cause (high confidence): a check-then-act race in `PersistenceClient._live`, a residual of S1a-1.**
      - `_live` reads the cancel latch twice. The first read (`persistence.py:726-728`) raises the healthy
        `PersistenceCancelled`. The final check (`persistence.py:745-746`) re-reads the latch. When that read
        sees a cancel and the kind does not allow one, it raises a plain `PersistenceError("ML-PERSIST-CLOSED")`.
        Finding 21 assumed this path needs `_failed` already set. It does not: the second operand is the race.
      - A cancel landing between the two reads is therefore reported as a storage failure. `_rpc`'s generic
        handler records it as `rpc_failure`, at stage `validation`, and calls `_fail()` (`persistence.py:851-871`).
        `_fail()` sets `_failed`, shuts the socket and SIGTERMs the storage worker. Every later terminal record,
        including `close_incomplete`, is then refused. Teardown cannot record, so no TERM runs. The issuers'
        `direct_child_reaped` stays unknown. Results: `ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN`, writer `rpc-unresolved`
        and `open`, and no terminal events. This happens although the native CANCEL was confirmed.
      - **A second window in the same function.** `check_child(..., live=True)` (`persistence.py:731`) runs with
        the stale snapshot, and its root check `_live` refuses a cancelled run with `ML-BOOT-CLOSED`
        (`bootstrap.py:583`). That error takes the same failing path.
      - **Not the dispatcher's cancel handling, `_available`, S1b's TERM or stop path, or the readiness
        probes.** The live call was the dispatcher's ordinary `schedule` statement. The cancel came from the
        harness's canceller thread through `entry.stop`, which cancels the latch first (`runtime_entry.py:191`).
        `_available` already re-raises `PersistenceCancelled`. It is not involved here.
      - **Evidence (`…-004728-cancel-paused`).**
        - The RPC started at 15.48391 s, 0.17 ms before `cancelRequestedMonotonicNs` (15.48408 s). It failed at
          15.48439 s, 0.31 ms after. So the first latch read saw a live run, and the final check saw the cancel.
        - The record shows `sequence: null` and `operation: null`, so nothing was sent. `brokerCancelResult` shows
          `native_epoch_confirmed: true` and `issuer_dead: false`.
        - The diagnostic code rules out the other `ML-PERSIST-CLOSED` source: a `PersistenceCancelled` at
          `validation` is re-raised unrecorded (`persistence.py:847-850`).
      - **Reproduction (deterministic), `test_a_cancel_between_the_live_checks_is_not_a_storage_failure`.** It
        uses the composed runtime and targets the second `tick-complete` statement. `entry.stop` is called from
        another thread inside the `validation` `_live`, at one of two points: after the first latch read, or
        before the child check.
        - **`control-before-live` (the S1a pre-send case): passes.**
        - **`before-final-check`: fails.** It gives the live signature exactly: `('ML-PERSIST-CLOSED', 'schedule',
          'validation')`, storage `_failed`, writer `open`, `ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN` and cleanup
          incomplete.
        - **`before-child-check`: fails** in the same way, with `('ML-BOOT-CLOSED', 'schedule', 'validation')`.
      - **Proposed repair** (an amendment to the S1a-1 note of ADR-ML3-PERSISTENCE-0001 first):
        - **RB1 (recommended).** In `_live`, a cancel observed with `not self._failed`, on a kind that does not
          allow cancel and is not in flight, always raises `PersistenceCancelled`, wherever it is observed. That
          means re-checking the latch after `check_child` and in the final check, and mapping a root
          `ML-BOOT-CLOSED` to `PersistenceCancelled` when the latch is cancelled and the child is still alive.
          Child exit and identity failures stay `PersistenceError`. Regression: this file.
        - **RB2 (narrower).** Take one latch snapshot at entry, use it for every decision, and recheck it once at
          the end. A late change becomes `PersistenceCancelled`. This only works if `check_child` receives
          `live=False` when the snapshot differs, so it is equivalent to RB1 in effect.
        - **RB3 (alternative).** In `_rpc`, while the stage is `validation`, classify any `PersistenceError`
          raised while the latch is cancelled and `_failed` is false as a cancel (no record, no `_fail()`). This
          is broader: it would also mask a genuine child failure that coincides with a cancel. Not recommended.
    - **(A) Cause (medium-high confidence; the lease value is not in the record): the start step outlives the
      unrenewed bootstrap lease, and the run-bootstrap root's own lease expiry kills the authority and the storage
      worker during the readiness-failure cancel.** This is the S1a-5 LOW-2 residual, but not by the
      native-epoch path assumed in finding 21.
      1. **The lease.** The harness creates it at `now + 4.8 s`. The same value is the bootstrap root lease and the
         native authority lease (`AuthorityConfig(session._generation, session._lease, …)`,
         `run_broker.py:471-473`). Renewal happens only at a statement boundary (`_service`,
         `dispatcher.py:1204-1205`), and only when at most `renew_margin` = 4 × 0.38 + 0.38 = 1.9 s remains. It
         renews to at most `now + 5 s`, which is the native maximum (`bootstrap.c:136,338`). Nothing renews inside
         `facade.start`. The schedule admission never compares W with the lease (`schedule_plan.py:79-130`).
      2. **The outer deadline was the bootstrap lease.** The start step's end is
         `min(active_end, now + start timeout 5, bootstrap._lease)` (`dispatcher.py:1084-1088`). Health was `None`
         before the first release. The start timeout end was about 8.1 s and the active window was larger. The
         candidates in finding 21 resolve as follows:
         - the start action timeout: not binding (8.1 s);
         - the health deadline (`_end` health term): absent;
         - the owner's start deadline: it is this same `until`;
         - the lease: binding.
      3. **Why 2 of 3 attempts.** `readiness_offsets(3.5, 3)` = 0, 1.625 and 3.25 s. With t0 = 3.41 s, the
         attempts were at 3.41 s and 5.04 s. The third, due at 6.66 s, was dropped because `at >= deadline`
         (`providers.py:434-435`). So L < 6.66 s. The plan was written at 0.644 s, before the lease was created,
         so L ≥ 5.44 s. No renewal ran: L − 3.1 s was more than 1.9 s at both step dispatches. The readiness
         failure and its cancel came at about 5.05 s (the last event write was at 5.047 s), with L − t between
         0.40 and 0.87 s.
      4. **Why the cancel revoked.** The run-bootstrap root ends at its own lease (`bootstrap.c:314`:
         `now>=s.lease` → `cleanup`). That cleanup SIGKILLs every helper, including the authority and the storage
         worker. Nothing extends the root lease until the terminal fence puts the root into terminal mode. The
         CANCEL was sent at about 5.05 s, and its exchange failed only at L or later, 0.39 s or more after it was
         sent. The authority was killed under it (EOF, then the revoke), giving `issuer_dead: true` and
         `issuer_reaped: true`. The storage worker died with it, so the dispatcher's next call (the `schedule`
         failure statement, which allows cancel, at 5.919 s) found the child gone: `ML-PERSIST-CHILD` at
         `validation`. That bounds L ≤ 5.92 s.
         - A client-side revoke after a CANCEL timeout would come at the CANCEL deadline, about 6.05 s, after the
           storage loss. A conflict cannot explain it: nothing else holds the connection in the start step.
           The root's lease is the earliest event that fits.
      5. **Why the cancel ran so long, and why the driver did not announce (medium confidence; inferred from file
         state).**
         - `stderr-g1` is empty, so the driver had no exception or traceback. It was not slow to import: by
           3.762 s, 0.42 s after release, it had opened its link and its zenoh session and started its Argus
           flow run.
         - `driver/argus-flows/manifest.json.tmp-1` (1150 bytes of valid JSON, mtime 3.762 s) was never replaced
           by `manifest.json`, and `events.jsonl` is empty. The driver was therefore still inside the manifest
           publication (`writer.py:1113-1118`: write, `fsync`, `os.replace`) when it was killed. That was 1.7 s or
           more later. It never reached `announce_ready()` (`driver.py:118`).
         - The run directory is on `/dev/loop10`, an ext4 image on an external drive that is 97% full. A task
           blocked in `fsync` (uninterruptible) cannot be frozen by cgroup v2. So the native CANCEL's
           `freeze_all` (`run_authority.c:180-201`) waits up to `close_end` (2 s) before it replies, which
           explains a CANCEL still open at L. The host has 32 CPUs, so load 8.4 alone is unlikely to delay a
           CANCEL by 0.39 s.
         - In `…-cancel-paused`, the same driver announced after 0.467 s.
      6. **Latent and related residuals (not reproduced).**
         - **A-ii:** the expired-lease epoch path of finding 15 is still reachable if a CANCEL is first read after
           a native lease close (`run_authority.c:652`).
         - **A-iii:** the client's CANCEL deadline is `now + 1 s` (`run_broker.py:1056`), shorter than the native
           close bound (`now + 2 s`, `run_authority.c:212`). A freeze stalled for 1 to 2 s therefore times out on
           the client and revokes even with ample lease left.
      - **Reproductions** (the `long_window_runtime` fixture: composed runtime, sink `nonce-marker` in
        `marker-never` mode, W = 3.5 s, the live action timeouts with `use_action_timeouts`). The sink's start step
        is placed at 2.8 s of lease left. That is above this fixture's 2.5 s renewal margin, so there is no renewal
        (0 renewals recorded), and below W. This placement is a wait only.
        - **`test_a_declared_readiness_window_is_not_silently_cut_by_the_lease`: fails** (deterministic). The
          queries were at +0 and +1.626 s; the third was dropped; the cancel came with 1.09 s of lease left. It
          passes if the schedule is refused at admission or all 3 attempts are made.
        - **`test_a_readiness_failure_cancel_that_takes_longer_than_the_lease_left_still_closes`: fails** in both
          runs. The readiness-failure cancel completes 1.5 s after the failure, which is below the native 2 s close
          bound (a wait before the cancel, so A-iii is not exercised). The result is the live signature:
          - `('ML-PERSIST-CHILD', 'schedule', 'validation')`;
          - `issuer_dead: true`;
          - CANCEL exchange errors `Broken pipe`, then `ML-AFFA-CLOSED`;
          - `ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN`, writer `open`;
          - the bootstrap root's own exit `si_code=1, si_status=0`: it ended by itself at its lease, not by a
            SIGKILL.
        - **Limit.** The live CANCEL was sent before L and stalled natively. The test issues it after L, so the
          first error is `Broken pipe` instead of EOF. Both reach the same root-lease teardown. A native freeze
          stall (a unit in uninterruptible sleep) is not reproducible without privileges and is not attempted.
      - **Proposed repairs** (an ADR-ML3-AFFA-0001 or ADR-ML3-PROBE-0001 note first). The invariant: a readiness
        start step must leave, after its last attempt, the cancel close bound (2 s) plus the terminal fence
        reserve inside the bootstrap lease. With a 5 s maximum lease and no renewal inside a step, that requires
        W + release + 2 s + reserve ≤ 5 s.
        - **RA1 (recommended): Maestro computes the readiness window against the lease.** In
          `ProcessReadiness.start`, space the attempts over `min(W, D − t0 − close bound − reserve)`, where D is
          the step end (already capped at the lease). The last attempt is then always made, and the cancel always
          has its close bound. Add an admission check in `admit_schedule` that refuses a W that cannot fit even a
          fresh 5 s lease (`ML-SCHEDULE-READINESS-WINDOW`; W ≤ about 2.5 s with the live budgets).
          - Regression: the two (A) tests. The first passes by refusal or by 3 attempts. The second passes once
            the cancel has 1.5 s or more left.
        - **RA2: R3, renew immediately before a readiness start step** when L − now < W + 2 s + reserve. This
          is necessary but not sufficient for W = 3.5 s: after a fresh 5 s renewal, the third attempt at
          t0 + 3.25 s leaves about 1.6 s, which is less than the 2 s close bound. It must be combined with RA1's
          cap, or with RA3.
        - **RA3: renew between marker attempts inside `facade.start`.** This keeps W unchanged. It needs the
          dispatcher's renewal service in the facade thread, under the same lock order (owner, then broker). This
          is the largest change.
        - **RA4 (for A-iii): give K.CANCEL a client deadline of at least the native close bound.** For example
          `min(now + 2 + reply margin, generation − 2, limit)` in `RunBroker.cancel`, or make the native freeze
          wait no longer than the request deadline. Either way, a stalled freeze yields a CANCELLED reply with
          `FREEZE_FAILED`, not a revoke.
        - **Harness-side options (S1c; these do not repair the platform):**
          - **H1:** reduce `OWNED_READINESS_TIMEOUT_S` so that it fits the lease: W ≤ 2.0-2.5 s. Earlier S1c runs
            measured marker writes 0.24-1.26 s after release at load 6.3-8.5, and W = 2.0 puts the last attempt at
            1.75 s.
          - **H2:** place the run directory, or at least the driver's `argus-flows` root, on tmpfs (`/dev/shm`) and
            copy it afterwards, so that no unit blocks in `fsync` on loop10 before it announces readiness.
          - **H3:** record `bootstrap._lease`, `connection._lease` at each step and at cancel, and the root's and
            each helper's `waitid` result in `maestro-run.json`, as finding 15 proposed. The root's exit (0 means
            its lease expired; −9 means revoked) would have decided (A) directly.
    - **Effect.** Both causes are understood and reproduced. The stack acceptance stays blocked until RB1 and one of
      RA1, RA2+RA1 or RA3 are decided and pass this file. RA4 and H1-H3 are recommended alongside.
23. **DR-15 repairs RB1, RA1 and RA4 (written at 01:25:05 2026-10-24, load about 4.0-4.5).** ADR notes first
    (`3504b06d4`, written at 01:13:21-01:13:50): ADR-ML3-PERSISTENCE-0001 "S1a-1 revision (RB1)",
    ADR-ML3-PROBE-0001 "S1b-1 revision (RA1)" and ADR-ML3-AFFA-0001 "S1a-6 (RA4)". Implementation and tests
    `399283515`. Installed wheel `4c664da7…` (built from the implementation; the earlier wheel `2efbd893…`
    from `c769a2692` reproduced the 4 failures again at 01:12, load 4.0-4.5).
    - **RB1** (`persistence.py` `_live`). The order of the failure checks is kept. If the ordinary
      (`live=True`) child check is refused while the latch is cancelled and storage has not failed, the child
      is re-checked with `live=False` (holder and capability only) and the checks continue. The final check
      raises `PersistenceError` for `_failed` first, and `PersistenceCancelled` for a cancel on a kind that
      neither allows one nor is in flight. Exit, pid/socket identity, holder failures and a refusal without a
      cancel still fail closed.
    - **RA1** (`providers.py`, `schedule_plan.py`).
      - `CANCEL_CLOSE_RESERVE_SECONDS` = `NATIVE_CANCEL_CLOSE_SECONDS` (2 s) + 0.25 s = 2.25 s.
      - Run time: for a marker unit (always a `RunUnitIssuer`, by `bind`), `start` reads at t0 L = min(bootstrap
        root lease, authority lease) through the issuer's broker, and spaces the attempts over
        `W' = max(0, min(W, L − 2.25 − t0, D − t0))` (`capped_readiness_window`).
      - Admission: `ML-SCHEDULE-READINESS-WINDOW` when a marker unit's min(policy timeout, observe timeout)
        exceeds `readiness_window_bound(operation_seconds)` = `LEASE_MAX_SECONDS` (5 s, native renewal maximum)
        − 2.25 s − `operation_seconds` (one round trip for the pre-release work after a fresh lease). Live
        (0.38 s): 2.37 s. Fixture (0.5 s): 2.25 s. No schedule version or digest change. `decode_schedule`
        re-derives it.
    - **RA4** (`run_broker.py`). `CANCEL_REQUEST_SECONDS` = 2 + `CANCEL_LOCK_WAIT_SECONDS` (0.5) +
      `CANCEL_REPLY_MARGIN_SECONDS` (0.25) = 2.75 s, in `min(now + 2.75, generation − 2, limit)`. The S1a-3
      wait and its 0.25 s reap reserve are unchanged. Cost: an unresponsive authority now holds an undeadlined
      cancel up to 2.75 s instead of 1 s before the revoke.
    - **Adjusted test expectations** (`test_stabilization_stack_load_failures.py`; the assertions on behaviour
      are unchanged otherwise).
      - The (A) fixture is now parametrized, `live-window` (W = 3.5 s) and `admitted-window` (W = 2.0 s, the
        DR-15 H1 value, under the fixture bound of 2.25 s).
      - `live-window`: both (A) tests now assert the admission refusal `ML-SCHEDULE-READINESS-WINDOW` instead of
        returning silently on any `ScheduleError`.
      - `admitted-window`: the start step is still placed at 2.8 s of lease left, without renewal. The tests
        assert 3 queries, the last one at least 2.25 s before the lease, and more than 2 s of lease at the
        readiness-failure cancel. The second test keeps its 1.5 s cancel delay and its full closure assertions.
      - (B) gains `in-flight-child-check`: the same window in the first in-flight `_live` of the targeted call.
        It failed without RB1 (checked on a wheel with the old `persistence.py`: 3 failed, the control passed),
        so RB1 covers it. Same expected outcome as the other windows.
    - **Unit tests added.**
      - `test_schedule_plan.py::test_ra1_a_marker_window_that_cannot_fit_a_fresh_lease_is_refused`: the bound
        values, refusal above it, the observe timeout bounding W, and running units unaffected.
      - `test_stabilization_s1b_readiness.py::test_ra1_the_marker_window_is_capped_…`: the cap (lease-bound,
        deadline-bound, never negative) and the last offset inside the reserve.
      - `test_stabilization_s1b_start_failure.py::test_ra4_the_cancel_deadline_covers_…`: the K.CANCEL frame
        deadline on a real broker stack.
    - **Results** (installed wheel `4c664da7…`, one pytest process at a time, 01:19:40-01:24:23, load 3.97-4.51).
      All passed, none failed or skipped:

      | Suite | Passed | Time |
      | --- | --- | --- |
      | `test_stabilization_*` (all 9 files) | 468 | 101.0 s |
      | `test_persistence*` | 29 | 28.1 s |
      | `test_provider.py` | 35 | 20.6 s |
      | `test_run_broker.py` | 11 | 12.5 s |
      | `test_affa_*` | 124 | 12.4 s |
      | `test_runtime_entry.py` | 8 | 8.6 s |
      | `test_run_teardown.py` | 9 | 10.9 s |
      | `test_teardown.py` | 27 | 24.8 s |
      | `test_closure.py` | 31 | 23.5 s |
      | `test_shared_closure.py` | 10 | 11.4 s |
      | `test_schedule_plan.py` | 47 | 14.1 s |
      | `test_dv05_dv06_bounds.py` | 7 | 12.0 s |

      Total: 806. The reproduction file alone: 8 passed in 17.10 s at load 3.4-4.0.
    - **Deviations and residuals.**
      - **RB1 includes the in-flight variant** of the child-check window. It is not named in finding 22, but it is
        the same race and the same fail-closed signature. It does not raise `PersistenceCancelled`, because the
        request was already sent. It continues under the S1a-1 grace.
      - **RA4 uses 2.75 s, not 2 s + margin alone.** The frame deadline is fixed before the S1a-3 lock wait, so the
        0.5 s wait is part of the budget. This supersedes S1a-3's "inside the 1 s cancel end" cost statement.
      - **The RA1 residual band (declared in the ADR note).** Renewal happens only at a statement boundary with at
        most `renew_margin` left (1.9 s live). A marker start step dispatched with between that margin and about
        2.25 s plus its pre-release work of lease left gets W' = 0: the attempts are back to back at t0, and less
        than the full reserve is kept. RA2 would close the band. It is not in DR-15.
      - **The cap is silent in the evidence.** W' is not recorded, which overlaps H3.
      - **The live S1c harness's W = 3.5 s is now refused at admission.** DR-15 H1 (W ≤ 2.37 s live) must land
        before the next live run. H1-H3 are harness-side and not touched here.
    - **Effect.** `test_stabilization_stack_load_failures.py` passes, so finding 21 is repaired at the platform
      level. Stack acceptance still needs an independent review of `3504b06d4`..`399283515`, then the decisive
      full installed-wheel run and DV12, then the S1c live re-run with H1.
24. **Independent review of DR-15 (`3504b06d4`..`4eb51406d`; written at 01:34:33 2026-10-24, load about 3.0-4.0):
    PASS WITH NOTES (no HIGH; three MEDIUM, six LOW).** The diff was read in full against the native sources
    (`bootstrap.c`, `run_authority.c`), `bootstrap.py`, `child.py`, `dispatcher.py` and `run_broker.py`. The
    installed wheel `4c664da7…` was checked to equal the head for the four changed modules. Rerun, one pytest
    process at a time: `test_stabilization_stack_load_failures.py` 8 passed (16.9 s);
    `test_schedule_plan.py`, `test_stabilization_s1b_readiness.py`, `test_stabilization_s1b_start_failure.py` and
    `test_stabilization_cancel.py` 75 passed (52.9 s). The claim that the old wheel failed `in-flight-child-check`
    was not re-verified (no rebuild).
    - **Confirmed.**
      - **RB1 keeps every real storage failure fail-closed, and checks it before the cancel.** After the re-check,
        the pidfd, pid and socket identity checks (`persistence.py:740-751`) and `_failed` (`:752-753`) still run
        before the cancel classification (`:754-756`). Child exit, identity change and a prior failure still
        raise `PersistenceError`. The re-check (`:733-739`) runs only when `live` is true, the latch is cancelled
        and `_failed` is false. Otherwise the original error propagates. The `live=False` re-check repeats the
        holder and capability checks (`child.py:82-92`), so those failures still raise.
      - **Concurrency.** `_fail()` sets `_failed` before it cancels the latch (`persistence.py:780-782`). The
        re-check reads the latch first, then `_failed`. A latch cancelled by `_fail()` is therefore never taken
        as a cancel. If `_fail()` lands after that read, the final `_failed` check still catches it. The only
        remaining window lies between the final `_failed` read and the final latch read. It has the same shape
        as the S1a-1 first read and is benign: `_failed` is sticky, and every later call refuses.
      - **The in-flight variant is sound.** It changes nothing that the S1a-1 in-flight path did not already
        allow when the cancel was seen at the first read: `live=False`, then the unchanged grace in `_rpc.check`.
        The grace starts at the next poll. A post-ack cancel no longer fails a request that storage already
        acknowledged.
      - **RA1 constants match the native code.**
        - The 5 s lease maximum applies to the initial lease and to every renewal (`bootstrap.c:136,338`; the
          terminal renewal is at `:345`).
        - The 2 s close bound is `run_authority.c:212` `close_end`. CANCEL uses it at `:527-530`.
      - **RA1 admission.**
        - The bound applies to every unit whose first observe condition is not `running`
          (`schedule_plan.py:136-141`). That is the same identity that `ProcessReadiness._probe` uses
          (`providers.py:279-281`).
        - It uses W = min(policy timeout, observe timeout), as at run time (`providers.py:444`).
        - `decode_schedule` re-derives the bound.
        - `ML-SCHEDULE-READINESS-WINDOW` is unique in `src/`, is documented in the ADR note, and is raised
          before any run.
      - **RA1 run time.**
        - L is read through `RunUnitIssuer.broker`. `bind` guarantees that type for marker units
          (`providers.py:303-319`).
        - The units are consistent: ns divided by 1e9 against `time.monotonic()` and `monotonic_seconds`.
        - Both leases only grow (`bootstrap.py:843`; `run_authority.c:534`), and only the dispatcher thread
          renews them, at statement boundaries. A stale read is therefore conservative.
        - The attempt times are at most `D − min(0.25, W'/A)`, so the `at >= deadline` drop
          (`providers.py:457-459`) cannot fire unless t0 is already at or past D.
        - When W' = 0, the three QUERYs run back to back at t0, inside the native limit of 3. A marker never
          seen still ends in `ML-PROBE-NOT-READY`, then `readiness-start-failed`, which fails closed.
        - The cap never declares a unit ready without a verified marker. It changes only when the attempts
          are made. Readiness still comes only from the native QUERY reply.
      - **RA4 timing.**
        - The deadline `min(now + 2.75, generation − 2, limit)` stays inside the native `until − now ≤ 5 s` and
          `until ≤ generation − 2 s` checks (`run_authority.c:666`).
        - The S1a-3 wait `min(now + 0.5, end, limit − 0.25)` and the revoke deadline are unchanged
          (`run_broker.py:1025`, `:1072-1077`).
        - After a full 0.5 s wait, 2.25 s remain: the native close bound plus 0.25 s.
      - **Process and tests.**
        - The ADR notes come before the code, by commit order and by their written-at times.
        - The `live-window` branch now asserts the specific refusal code instead of returning on any
          `ScheduleError`.
        - The `admitted-window` assertions follow the criterion that finding 22 fixed before the repair:
          refusal, or every attempt "spaced inside the lease it actually has". They discriminate: without the
          cap, the last attempt (t0 + 1.75 s, with about 2.6 s left) would fail `lease − last ≥ 2.25`.
    - **MEDIUM-1 (the declared window is usually cut, and the cut is silent): `providers.py:444-450`.**
      - Renewal happens only when at most `renew_margin` is left, and to at most 5 s. A start step therefore
        usually meets L − t0 well below W + 2.25 s, so W' < W is the common case, not only the W' = 0 band
        that the ADR declares.
      - **The live timeline of finding 22.** L ∈ [5.44, 5.92] s and t0 = 3.41 s give
        W' = max(0, L − 2.25 − t0) ≈ 0–0.26 s for any W ≥ 0.26 s, including the DR-15 H1 value W = 2.0 s. The
        S1c marker writes were measured at 0.24–1.26 s after release; the driver in `…-cancel-paused`
        announced after 0.467 s. The S1c re-run with H1 is therefore predicted to end the first owned start
        step in `ML-PROBE-NOT-READY` in that placement.
      - The fixture shows the same effect: placed at 2.8 s, W = 2.0 s is spent as about 0.3–0.5 s. The test
        asserts the attempt count, not the window actually spent.
      - `ML-PROBE-NOT-READY` cannot tell "not ready within the declared W" from "Maestro shortened W to W'".
        That weakens any attribution of a readiness failure to the unit.
      - Finding 23 records the cap as silent, but it understates how often it applies.
      - **Repair.**
        - Record W, W', L and t0 for each marker start step in the readiness evidence (this overlaps H3).
          Give a capped window that ends not ready its own diagnostic, or a field on the not-ready row.
        - Amend the ADR residual to cover the general case.
        - Before the S1c re-run, put back to the author the choice of RA2+RA1, which finding 22 listed and
          DR-15 rejected only as "insufficient alone".
    - **MEDIUM-2 (the 2.25 s reserve does not cover the work between the cancel and the terminal fence):
      `providers.py:31`, `dispatcher.py:1644-1669`, `persistence.py:1268-1277`.**
      - The reserve is the close bound plus 0.25 s "for the cancel's reply and the terminal fence". The root
        lease is extended only by `_service_terminal`, which the first teardown record calls.
      - Before that record, the readiness-failure path runs:
        - the undeadlined `owner.cancel` (up to the 2 s native close);
        - the `failure` statement, a full storage RPC;
        - `_close_restarts`;
        - the start of `teardown.run`.
      - **Effect.**
        - Under the live mechanism, a unit blocked in `fsync` on loop10, the freeze consumes the full 2 s. The
          storage worker's own RPC then also writes to the stalled device, with about 0.25–0.5 s of lease left.
          The root can still end at L and give the finding 21 (A) signature.
        - RA1 removes the case from finding 22, a cancel that completes 1.5 s after the failure. It does not
          show the close bound actually used: `CANCEL_COMPLETION_SECONDS = 1.5`
          (`test_stabilization_stack_load_failures.py:150`), and the assertions only check `cancel_left > 2.0`
          (`:252`, `:273`).
        - This stays fail-safe under the owner decision recorded in finding 18 (LOW-2), but it is not the
          stated invariant.
      - **Repair** (one of the following, with the ADR note amended first):
        - service the terminal fence immediately after a confirmed native cancel, before the `failure`
          statement;
        - or add the failure statement's and the terminal RPC's budgets to the reserve, and lower the
          admission bound to match.
        - In either case, add an (A) case whose cancel completes at the 2.0 s bound, or state this as a
          declared residual.
    - **MEDIUM-3 (no test pins the fail-closed side of RB1).** Nothing in `tests/` asserts `ML-PERSIST-CHILD`,
      or any fail-closed `PersistenceError`, from `_live` when the latch is cancelled. The new branch
      (`persistence.py:734-739`) is covered only by its positive windows.
      - **Repair (tests only).** Add the RB1 negatives in the four windows:
        - cancel plus a storage worker killed before the child wait → `PersistenceError("ML-PERSIST-CHILD")`,
          recorded, and `_fail()`;
        - cancel plus `_failed` set → `ML-PERSIST-CLOSED` as `PersistenceError`, not `PersistenceCancelled`;
        - cancel plus a replaced socket identity → `ML-PERSIST-CHILD`;
        - a root refusal without a cancel → still fails closed.
    - **LOW-1 (root-level faults that coincide with a cancel are reported late): `persistence.py:733-739`,
      `bootstrap.py:578-592`.** With the latch cancelled, root lease expiry, root exit, `_closed` and a terminal
      mismatch are no longer refused at this call. A storage worker killed by the root may not yet be visible
      to the pidfd check, so the call can raise `PersistenceCancelled`. The next terminal call then reports the
      fault. This matches the S1a-1 first read and the terminal kinds, so it adds no new class. Also, the latch
      reason is never consulted: a latch cancelled by `bootstrap-uncertain` or `bootstrap-helper-failed` is
      taken as a cancel. **Repair:** state both in the RB1 note.
    - **LOW-2 (RA4 covers only undeadlined cancels).** A caller deadline still bounds K.CANCEL, so a stalled
      freeze still ends in a revoke for:
      - the lazy terminal fence (`dispatcher.py:1405-1407`, `now + operation_seconds`);
      - teardown emergencies (`teardown.py:465`);
      - controller cancels.

      A-ii also compounds: if CANCEL is read just after the native watchdog lease close (`run_authority.c:652`),
      the two freezes can take up to 4 s, which is more than 2.75 s. **Repair:** list both in the S1a-6
      residuals.
    - **LOW-3 (the RA4 cost is not checked against the outer budgets).** An undeadlined cancel may now take
      about 3.75 s. The readiness-failure path runs it before the `failure` statement, whose deadline is
      `min(_work_end, …)` (`dispatcher.py:1644-1655`). No admitted budget has a cancel term. DV05/DV06 pass,
      but they use their own deadlines.
      - The live harness's stop call (`runtime_entry.stop` → `RunUnitIssuer.cancel`, `run_broker.py:1507`) is
        also synchronous and undeadlined.
      - **Repair:** one sentence in the S1a-6 note bounding the effect on `_work_end`, the S1c canceller and the
        closure budget.
    - **LOW-4 (the RA4 test only restates the constant): `test_stabilization_s1b_start_failure.py:145`.** A
      behavioural test needs no privileges: delay the K.CANCEL exchange by 1.5 s and assert CANCELLED with no
      revoke. It would fail at `now + 1 s`. **Repair:** add it with the next change in this area.
    - **LOW-5 (the admission rationale understates the pre-release work).** "One round trip" stands for
      `commit_intent`, ARM, RELEASE and the prerequisite and health QUERYs (`providers.py:426-440`). The bound
      is declared necessary, not sufficient, so this changes no safety claim. **Repair:** reword in the ADR
      note.
    - **LOW-6 (records outside this repository).** The thesis record
      `specs/024-maestro-lite-lifecycle/review/amendment-s1a-3-cancel-busy-connection-20261023.md:23` still
      says "within the 1 s cancel end", which S1a-6 supersedes. The canonical thesis note does not yet mention
      DR-15. **Repair:** a traceable amendment and a proposed note update, for the author.
    - **Effect.** The stack acceptance can proceed to the decisive full installed-wheel run and DV12 once the
      MEDIUM-3 tests are added and MEDIUM-1 and MEDIUM-2 have recorded dispositions (an ADR amendment, or a
      declared residual accepted by the author). The S1c live re-run with H1 should wait for the MEDIUM-1
      disposition, because the current cap is predicted to shorten the H1 window to about 0–0.3 s in the
      finding 21 placement.
25. **DR-16 repairs: RA2, RA5, the window record, the RB1 negatives and the LOW dispositions (written at 02:02:52
    2026-10-24, load about 3.7-4.7).**
    - **Commits.**
      - ADR notes first: `4840afccb`, written at 01:47:51-01:48:16. They are ADR-ML3-PROBE-0001 "S1b-1
        revision (RA2, RA5, the window record)", ADR-ML3-AFFA-0001 "S1a-6 residuals and the outer budgets (L2,
        L3)" and ADR-ML3-PERSISTENCE-0001 "S1a-1 revision (RB1) residual L1".
      - Implementation and tests: `e593bd5c2`.
      - Installed wheel: `36894fab…`, built at 01:52 from the working tree that `e593bd5c2` commits.
    - **RA2** (`dispatcher.py` `_renew_before_marker_start`, called from `_effect` for a `start` step after
      `_service()` and before `_end`).
      - **When it renews.** For a `nonce-marker` unit on the native path, it renews through the unchanged
        `_renew_service(active end)` when `min(lease ends) − now < readiness_lease_need(W, op) = op + W +
        cancel_close_reserve(op)`.
      - **When it does not.** If `min(now + 5 s, generation − 2 s)` is not above both leases, it does not renew,
        and the cap records the cut.
      - **Leases.** The renewal moves both leases together: the root lease (`session.renew`) and the authority
        lease (K.RENEW), to one target, after one storage audit.
      - **Requests.** `admit_schedule` adds one request per marker unit to `required_requests`. That changes the
        schedule bytes only for schedules with marker units. The version is unchanged.
    - **RA5** (`providers.py`).
      - `cancel_close_reserve(op) = NATIVE_CANCEL_CLOSE_SECONDS (2) + op + CANCEL_FENCE_MARGIN_SECONDS (0.25)`.
        It replaces the constant `CANCEL_CLOSE_RESERVE_SECONDS`.
      - `readiness_window_bound(op) = 5 − cancel_close_reserve(op) − op = 2.75 − 2·op`.
      - Run time takes `op` from the persistence client's schedule; it is 0 with no schedule, where there is no
        dispatcher and no failure statement.
    - **The final live admission bound for W is 1.99 s.**
      - Derivation: 5 s (native lease maximum) − (2 s close + 0.38 s failure statement + 0.25 s reply and fence)
        − 0.38 s (pre-release allowance).
      - The fixture bound (op 0.5 s) is 1.75 s.
      - **Harness H1** must be re-derived to W ≤ 1.99 s, for example 1.9 s. The DR-15 H1 value of 2.0 s is now
        refused with `ML-SCHEDULE-READINESS-WINDOW`.
    - **The window record** (`providers.ReadinessWindow`: `unit_id`, `generation`, `declared_seconds` (W),
      `window_seconds` (W'), `lease_end` (L), `began` (t0), `cut`).
      - One record is appended per marker start step, including a restart's, at t0.
      - It is exposed as `ProcessReadiness.readiness_windows` and `DispatchResult.readiness_windows`, and so
        reaches `RuntimeResult.dispatch`.
    - **The cut diagnostic.** A cut window (W' < W) that ends not ready raises **`ML-PROBE-WINDOW-CUT`**.
      - It appears in `DispatchResult.diagnostic` and in the Argus `failure` event's `diagnosticCode`, with
        `cause: deadline-exceeded`, through the dispatcher's existing `WINDOW` mapping.
      - A field on the probe row was not used because the v2.0 payload is closed. The ADR note gives the
        reasons.
    - **Tests added or changed** (`test_stabilization_stack_load_failures.py` unless named).
      - **M3:** `test_rb1_a_real_storage_fault_with_or_without_a_cancel_still_fails_closed`, four cases:
        - `child-killed`: `ML-PERSIST-CHILD`;
        - `failed-set`, in the final-check window: `ML-PERSIST-CLOSED`;
        - `socket-replaced`: the channel fd `dup2`'d to another socket, `ML-PERSIST-CHILD`;
        - `root-refusal-without-cancel`: `ML-BOOT-CLOSED`.

        In each, `_live` raised exactly that class, `PersistenceError` (`BootstrapError` for the root case),
        never `PersistenceCancelled`. Each was recorded as the RPC failure `(code, schedule, validation)`, with
        `_failed` set. The first three run with the latch cancelled from another thread inside the RB1 windows.
      - **M1:**
        - `test_a_declared_readiness_window_is_not_silently_cut_by_the_lease` (admitted W = 1.5 s, placed at
          2.8 s, which is below the 4.75 s need): RA2 renews, the record shows W' = W and not cut, and L − t0 ≥
          W + 2.75 s. There are 3 attempts spanning W − 0.25 s, the last at least 2.75 s before L, and the Argus
          failure event reads `ML-PROBE-NOT-READY`.
        - `test_a_forced_cut_window_is_recorded_and_diagnosed` (RA2 disabled): no renewal, the record is cut
          with W' = max(0, L − 2.75 − t0), there are 3 attempts, and the result is `ML-PROBE-WINDOW-CUT` with
          `deadline-exceeded` in Argus.
      - **M2:** `test_a_cut_window_cancel_that_takes_the_full_native_close_still_reaches_the_fence`.
        - Setup: RA2 disabled and placed at 3.6 s, so 0 < W' < W and the reserve binds. The client reads the
          K.CANCEL reply 2.0 s after the send.
        - At the first `service_terminal`, the root and the authority were both unexited, with lease left.
        - Results: native confirmation, no revoke, no exchange error, no persistence failure, cleanup complete,
          and the writer closed.
        - The renewed-path test, `…takes_longer_than_the_lease_left_still_closes`, now delays its cancel by the
          full 2.0 s (it was 1.5 s).
      - **L4** (`test_stabilization_s1b_start_failure.py`):
        `test_ra4_a_cancel_whose_native_reply_takes_1_5_s_is_confirmed_not_revoked`. The K.CANCEL reply is read
        1.5 s late: with RA4 the cancel is confirmed with no errors. The control restores `now + 1 s` and gets
        `ML-AFFA-TIMEOUT` and an unconfirmed cancel, so the test discriminates.
      - **Unit tests.** `test_schedule_plan.py`: the RA1 test is moved to 1.99 and 1.75 s, and DR-15 H1's 2.0 s
        is refused. A new test checks one extra request per marker unit, with the event count unchanged.
        `test_stabilization_s1b_readiness.py`: the cap test now uses the reserve function.
      - **Regression adjustment** (`test_stabilization_s1b_start_failure.py`
        `test_a_never_ready_marker_unit_at_start_up_closes_its_evidence`, both cases).
        - The composed fixture has no action timeouts, so its start step ends at `now + operation_seconds`
          (0.5 s). That 0.5 s also holds the pre-release work, so W = 0.5 s is always cut by the step deadline D.
          The record now shows the cut, and the diagnostic is `ML-PROBE-WINDOW-CUT`.
        - Before this change the cut was silent and was reported as `ML-PROBE-NOT-READY`. This is MEDIUM-1 seen
          in an existing fixture.
        - The closure assertions are unchanged and pass.
      - Admitted fixture window: `ADMITTED_WINDOW_SECONDS` 2.0 → 1.5 s (bound 1.75 s).
    - **Results** (wheel `36894fab…`, one pytest process at a time, 01:54:57-02:01:54, load 3.78-4.73). All
      passed, none failed or skipped:

      | Suite | Passed | Time |
      | --- | --- | --- |
      | `test_stabilization_*` (all 9 files) | 478 | 121.8 s |
      | `test_persistence*` | 29 | 28.3 s |
      | `test_provider.py` | 35 | 20.8 s |
      | `test_run_broker.py` | 11 | 12.7 s |
      | `test_affa_*` | 124 | 12.4 s |
      | `test_runtime_entry.py` | 8 | 9.1 s |
      | `test_run_teardown.py` | 9 | 10.1 s |
      | `test_teardown.py` | 27 | 25.1 s |
      | `test_closure.py` | 31 | 23.4 s |
      | `test_shared_closure.py` | 10 | 11.8 s |
      | `test_schedule_plan.py` | 48 | 14.6 s |
      | `test_dv05_dv06_bounds.py` | 7 | 12.2 s |
      | `test_dispatcher.py`, `test_dispatch_diagnostics.py`, `test_dispatch_observe.py` | 22 | 34.0 s |
      | `test_lazy_dispatcher.py` | 13 | 19.7 s |
      | `test_shared_dispatcher.py` | 3 | 10.5 s |
      | `test_service_order.py`, `test_load_aware_budgets.py` | 11 | 12.6 s |
      | `test_run_renewal.py` | 9 | 15.3 s |
      | `test_leaseguard.py`, `test_releasegate.py` | 68 | 3.7 s |
      | `test_schedule_worker.py` | 15 | 14.4 s |

      Total: 958. The reproduction file alone (16 tests) passed in 33.9 s at load 3.6-4.0, on the first run.
    - **L3 numbers.** For the 2-unit, 2-step lifecycle with `per_unit_seconds` = 1, `terminal_reserve_seconds` is
      8.0 s at op 0.5 and 7.04 s at op 0.38. After a worst-case 3.75 s undeadlined cancel at the active end,
      4.25 s and 3.29 s remain, plus collection and terminal time minus the drain. The S1c join margin is about
      1.25 s or more. The closure window is unaffected. The reasoning is in the S1a-6 note.
    - **Deviations.**
      - **Window record location.** It is in the result objects, not on the Argus probe row: the lifecycle payload
        v2.0 is closed. The cut does reach Argus, as the `ML-PROBE-WINDOW-CUT` diagnostic. W, W', L and t0 do not.
      - **RA2 adds request accounting** (+1 per marker unit). DR-16 does not name this, but without it a renewal
        could exceed an admitted request limit. It changes the schedule bytes for marker schedules only.
      - **`CANCEL_CLOSE_RESERVE_SECONDS` is removed** in favour of `cancel_close_reserve(op)`, so that no stale
        constant remains.
      - **M2's discrimination is limited.** With fast fixture storage the failure statement takes milliseconds, so
        the M2 case would also pass with the old 2.25 s reserve. It shows the invariant at the full 2.0 s close.
        It does not show that the `op` term is necessary, which a stalled storage device would.
      - **L6 is not done here.** The thesis record `amendment-s1a-3-…` and the canonical note are outside this
        repository and this task's scope.
    - **Residuals.**
      - RA2 is not applied to restarts (`_restart_unit`); a restart keeps the cap and the record.
      - The `failure` statement's own deadline is still `per_unit_seconds`, so a storage stall longer than op
        can pass L. The fence's `now + op` deadline is covered only by the 0.25 s margin. Both fail closed.
      - A cut by the step deadline D (not only by the lease) is now visible, but admission does not relate W to the
        start budget. With `use_action_timeouts` off, the start step's budget is op, which cuts any W ≥ op.
      - L1 and L2 are declared in the ADR notes.
    - **Effect.** Every finding 24 MEDIUM now has an implemented disposition, and the LOWs have recorded
      dispositions (except L6, which is the author's). The stack acceptance still needs an independent review of
      `4840afccb`..`e593bd5c2`, then the decisive full installed-wheel run and DV12, then the S1c live re-run
      with H1 at W ≤ 1.99 s.
26. **Independent review of DR-16 (`4840afccb`..`a134fd47b`; written at 02:14:21 2026-10-24, load about 4.0-4.2):
    PASS WITH NOTES (no HIGH; one MEDIUM, six LOW).** The diff `4840afccb~1..a134fd47b -- src tests` was read in
    full, together with the ADR notes in `4840afccb`, the thesis DR-16 entry, and the code paths it touches:
    `_service`, `_renew_service`, `_end`, `_effect`, `_cleanup`, the failure path, `_restart_unit` and
    `_commit_controller_view` (`dispatcher.py`); `RunBroker.renew`, `RunBroker.cancel` and `service_terminal`;
    `owner._check`, `persistence._available` and `_live`; `recovery.py:436`; `run_closure._fence`; and the
    native RENEW, CANCEL and lease checks (`run_authority.c:125,525-535,640-672`; `bootstrap.c:136,314,338`).
    - **Wheel.** `36894fab145ff790…` is the only wheel in the cache (built at 01:52). All 85 `xverse/` files in it
      are byte-identical to `e593bd5c2:src/`, and `e593bd5c2..a134fd47b` changes no file under `src/`.
    - **Rerun** (installed wheel, one pytest process at a time, no CARLA, zenohd or live runs):
      - `test_stabilization_stack_load_failures.py`: 16 passed (33.5 s).
      - `test_schedule_plan.py`, `test_stabilization_s1b_readiness.py`, `test_stabilization_s1b_start_failure.py`
        and `test_provider.py`: 110 passed (71.8 s).
      - The other suites in finding 25's table were not rerun.
    - **Confirmed.**
      - **RA2 bounds.** The renewal goes through the unchanged `_renew_service`. Its target is
        `next_end = min(now + 5, generation − 2)`, fixed before the heartbeat. So it is within the native
        `end − now ≤ 5 s` and `end ≤ generation − 2 s` checks (`run_authority.c:533-534`; `bootstrap.c:338`) when they
        are evaluated later.
      - **One target for both leases.** `RunBroker.renew` moves the root lease (`session.renew`) and the
        authority lease (K.RENEW) to the same target after one audit. On the native path, `gates` is
        `broker.connection` (`runtime_entry.py:152`). RA2's lease view, `bootstrap._lease` plus `gate.lease_ns`
        (`dispatcher.py:1377-1378`), is therefore the providers' L = min(root, authority).
      - **The skip test agrees with the broker's refusal.** RA2 does not renew when the target is not above
        `max(leases)` (`dispatcher.py:1381`). The broker refuses exactly that case (`target <= max(...)`), so the
        skip adds no `ML-SCHEDULE-LEASE-EXHAUSTED` path. When the lease is short and cannot be extended, the cap
        gives W' < W and `cut: true`. A cut window that is not ready raises `ML-PROBE-WINDOW-CUT`. The cut is
        recorded, never silent.
      - **No renewal for a cancelled run.** RA2 cannot extend the lease of a cancelled run:
        - `_service()` raises `ML-SCHEDULE-CANCELLED` first;
        - `RunBroker.renew` calls `owner._check`, and therefore `persistence._available` (`ML-PERSIST-NOT-OPEN`
          on a cancelled latch), before and after it takes the locks;
        - the audit is refused under a cancel;
        - natively, RENEW needs `enabled(g)`, which is `!closed` (`run_authority.c:125-127`). A RENEW after a
          CANCEL is rejected and fails closed through `run-renew-uncertain`.

        The only window is between the post-lock audit and `session.renew`, the same as every `_service`
        renewal. It grants no start authority. Stopped units' gates are excluded, as in `_service`.
      - **Request accounting.** A renewal costs one storage request (`revalidate_run`). The heartbeat and the
        root and authority renewals are not storage requests. `+1` per marker unit is a conservative upper bound,
        because RA2 runs at most once per start step and restarts do not use it. `persistence_worker.py:112` and
        `persistence.py:232,486` re-derive the value through the same `admit_schedule`.
      - **No pinned schedule bytes.** No test, DV12 allowlist (`scripts/validate_maestro_acceptance_evidence.py`
        allowlists `-ra` skip and xfail lines only) or golden digest pins the bytes of a marker schedule or its
        `required_requests`. Only `test_schedule_plan.py:29,172,183`, which are running-only and unchanged, pin
        values.
      - **RA5 arithmetic.** `readiness_window_bound(0.38)` = 1.9900000000000002, so a live W of 1.99 s is
        admitted and 2.0 s is refused. The fixture bound is 1.75. `readiness_lease_need(bound, op)` = 5.0, so an
        admitted W always fits a fresh lease. The bound and the cap now share `cancel_close_reserve`; no use of
        the old constant remains in `src/` or `tests/`. Run time takes `op` from `owner.persistence.schedule`,
        the same object as the dispatcher's `self.plan` (`dispatcher.py:457`).
      - **The diagnostic.**
        - `ML-PROBE-WINDOW-CUT` is raised inside the same `try`, so it takes the same
          `cancel("readiness-start-failed")` path as `ML-PROBE-NOT-READY`.
        - It maps to `deadline-exceeded` through the existing `WINDOW` test (`dispatcher.py:1686`), the same as
          `ML-SCHEDULE-WINDOW-MISSED`.
        - It matches the `diagnosticCode` pattern `^ML-[A-Z-]+$` in both payload schemas, and no allowlist of
          codes exists.
        - It is documented in the ADR note.
        - A cut window whose marker is found still succeeds.
      - **The record.** `ReadinessWindow` is public-safe: a catalog unit id, the descriptor's integer generation,
        two durations, two host-monotonic times and a boolean. It reaches `RuntimeResult.dispatch` through the
        single `DispatchResult` construction (`dispatcher.py:1820-1833`), in field order.
      - **Tests.**
        - **M3.** The four cases raise the stated class and code from the targeted `_live`, never
          `PersistenceCancelled`, and record `(code, schedule, validation)`. The latch is cancelled from another
          thread inside the hooked call, after `_live`'s first read.
        - **M1.** The renewed test and the forced-cut test discriminate each other: same placement, with and
          without RA2.
        - **L4.** The control (`CANCEL_REQUEST_SECONDS = 1.0`) gets `ML-AFFA-TIMEOUT` and an unconfirmed cancel,
          so the RA4 case is behavioural.
        - **The regression adjustment** to `test_a_never_ready_marker_unit_at_start_up_closes_its_evidence` is
          justified. With no action timeouts, the start step's D is `now + op` = 0.5 s, and that 0.5 s also
          holds the pre-release work, so D − t0 < W = 0.5 s holds by construction. The new expectation,
          `cut: true` and `ML-PROBE-WINDOW-CUT`, is the M1 fix made visible. The closure assertions are
          unchanged.
        - **M2's limited reach** is declared honestly in finding 25.
      - **L3 numbers.** The 2-unit, 2-step fixture (`prepared()`: 2 units, 2 start steps) gives
        `terminal_reserve_seconds` = 2·1 + (2 + 4 + 2)·op + 2 = 8.0 s at op 0.5 and 7.04 s at op 0.38. After the
        3.75 s worst case (the 2.75 s frame plus the 1 s revoke), 4.25 s and 3.29 s remain.
        - The lazy fence's broker cancel returns the cached result.
        - `run_closure._fence` skips K.CANCEL when the last epoch is CANCELLED (`run_closure.py:183`).
        - `stop` is local up to `RunBroker.cancel`.

        The S1c join margin of at least about 1.25 s and the unchanged closure window follow.
    - **MEDIUM-1 (RA5 reserves the nominal `operation_seconds`, not the failure statement's bound, and the ADR
      calls it "the admitted budget"): `providers.py:42-46`, `dispatcher.py:1667-1676`.**
      - The `failure` statement on the readiness-failure path is sent with
        `min(_work_end, now + per_unit_seconds)`. The code comment says "Terminal-section statement: per-unit
        budget like run-terminal". That is its admitted bound: 1 s in the fixture, up to 5 s by admission
        (`schedule_plan.py:105`).
      - The ADR S1b-1 revision note says that the reserve's middle term is "the admitted budget of one
        terminal-section statement". That is not what the code does. `cancel_close_reserve` uses
        `operation_seconds` (0.38 s live) as a nominal allowance.
      - DR-16 asks that the reserve "include the bounded budget of the failure-statement RPC". The
        implementation covers only the nominal case.
      - **The case that motivated finding 24 M2 is still open:** a unit frozen in `fsync` on loop10, and then
        the storage worker's own `failure` write to the same stalled device. That write may take up to
        `per_unit_seconds`, and in that time the root still ends at L. It is the finding 21 (A) signature,
        fail-closed.
      - The fence's own `now + op` deadline is also not in R; only the 0.25 s margin covers it.
      - Finding 25 declares both points as a residual. The residual contradicts the decision text, and the ADR
        wording misdescribes the term.
      - **Repair** (the author chooses; amend the ADR note first):
        - (a) Accept op as a nominal allowance, as a declared deviation from DR-16. Correct the ADR sentence to
          "a nominal one-RPC allowance, not the statement's bound".
        - (b) Bound the readiness-failure `failure` statement to `min(_work_end, now + per_unit_seconds,
          bootstrap lease − CANCEL_FENCE_MARGIN_SECONDS)`. A stalled statement then fails, is recorded, and
          leaves the fence reachable. This changes evidence completeness under a stall, so the closure tests must
          show the outcome.
        - (c) Reserve `per_unit_seconds`. The live bound becomes `2.75 − op − per_unit`, which is about 1.37 s
          at per_unit 1 and infeasible for larger values, so (c) is probably not workable.
    - **LOW-1 (records lost across a controller recovery): `dispatcher.py:792`, `recovery.py:436`.**
      `_commit_controller_view` replaces `self.facade` with the recovery view, a new `ProcessReadiness` whose
      `_windows` is empty. `DispatchResult.readiness_windows` (`dispatcher.py:1832`) then drops every record
      made before the recovery. The claim "one record per marker start step, in order" fails without any sign.
      Argus is unaffected (the cut is a diagnostic). **Repair:** carry the records into the view in
      `_commit_controller_view`, or keep them in the dispatcher. Add a recovery-case assertion.
    - **LOW-2 (the reserve is not kept when W' is clamped to 0, so restarts still carry the (A) signature):
      `providers.py:38`, `dispatcher.py:897-924`.**
      - The cap guarantees R only from `t0 + W'`. The last QUERY keeps `min(0.25, W'/A)`, so for W' < 0.75 s
        part of the last round trip is charged to R.
      - When `L − t0 < R`, `max(0, …)` gives W' = 0. All three QUERYs then run back to back with less than R
        left, and the cancel can outlive L.
      - RA2 removes this for normal start steps. It remains for restarts (no RA2; `_service` renews only below
        `renew_margin` = 1.9 s live, which is less than R = 2.63 s) and for a start step that the generation end
        prevents from renewing.
      - Finding 25 says only "a restart keeps the cap and the record".
      - **Repair:** state in the ADR residual that a marker restart, or a generation-limited start, can still end
        with the root's lease expiring under the cancel, with an incomplete closure that fails closed. Or apply
        `_renew_before_marker_start` in `_restart_unit` before `_restart_end`, with one extra request counted per
        admitted restart.
    - **LOW-3 (cut sources that admission does not check): `dispatcher.py:1081-1098`.** D is
      `min(active end, now + start budget, lease, next health − scan)`.
      - Finding 25 declares the start-budget source. Without action timeouts, any W ≥ op is cut.
      - The health term is not declared. A marker unit whose start step follows another unit's first observation
        has D ≤ `observed_at + cadence − health_scan_seconds`. A cadence shorter than about W plus the
        pre-release work therefore cuts W on every such start.
      - Both outcomes are now diagnosed, not silent, but admission accepts schedules that can never spend W.
      - **Repair:** declare the health term. Optionally refuse at admission when
        `W + op > start budget` (op without action timeouts, otherwise the start action timeout), or when
        `W + op > cadence − scan` for a non-first marker unit. Such a refusal would also refuse the composed
        never-ready fixture, so it is an author choice.
    - **LOW-4 (the H1 headroom is thin): `dispatcher.py:1229-1245`.**
      - After RA2, `L − t0 = 5 − (the renewal time after next_end is fixed) − (the pre-release work)`. W' = W
        needs that sum to be at most `5 − R − W`.
      - At the suggested H1 value W = 1.9 s, that is op + (1.99 − 1.9) = 0.47 s.
      - Finding 22 measured about 0.31 s of pre-release work at load 8.4 (dispatch about 3.1 s, t0 = 3.41 s),
        before the RA2 heartbeat, audit, root renewal and K.RENEW were added.
      - A cut in the S1c re-run is therefore plausible. It would now be visible as `ML-PROBE-WINDOW-CUT`, but the
        declared W would not be delivered.
      - **Repair (harness, S1c):** choose H1 with measured headroom (for example W ≤ 1.5-1.7 s), and report
        `cut` from the H3 record of every run.
    - **LOW-5 (test reach).**
      - `failed-set`: `assert entry._storage._failed` (`test_stabilization_stack_load_failures.py:235`) is
        vacuous, because the fault itself sets `_failed` (`:196-197`). That case shows the classification, not
        that `_fail()` ran.
      - The generation-limited skip branch of `_renew_before_marker_start` (`dispatcher.py:1381-1382`) has no
        test. The forced-cut test replaces the whole method.
      - `_delay_cancel_reply` (`test_stabilization_s1b_start_failure.py:65-89`) delays only the client's read.
        The native authority has already frozen and closed, so M2 shows the root-lease timing, not a slow native
        close.
      - M2 does not discriminate the `op` term (declared).
      - **Repair** (with the next change in this area):
        - assert that `_fail()` ran, for example by its SIGTERM or a spy;
        - add a skip-branch case near `generation − 2 s`;
        - add an M2 variant that delays the `failure` statement's RPC by about `op − 0.05 s`. It would fail
          with the old 2.25 s reserve.
    - **LOW-6 (open records).**
      - DR-16's L6 (a dated correction to the thesis `amendment-s1a-3-…` record) is not done. DR-16 assigns it,
        so it stays open on the thesis side.
      - DR-16 says "records … in its evidence", but W, W', L and t0 reach only the result objects. The reason is
        sound: the payload v2.0 is closed, with `additionalProperties: false`, the key set checked by
        `validate_receipt`, and re-acceptance needed for a change. The result-only record is acceptable as an
        interim measure only if the S1c harness (H3) persists it in a hash-bound run record. It is not covered by
        the writer's integrity chain.
      - `design-stabilization-s1b.md:187` still gives `ML-PROBE-NOT-READY` as the only outcome.
      - `CANCEL_CLOSE_RESERVE_SECONDS` was removed without a shim. Any harness import of it, outside this
        repository and not checked here, would break.
      - **Repair:** the author acknowledges the evidence-location deviation. The thesis-side L6 correction is
        made. One line is added to the design note. The harness imports are checked before the S1c re-run.
    - **Effect.** No `src/` or `tests/` change is required to start the decisive full installed-wheel run and DV12
      on `a134fd47b` (wheel `36894fab…`). Stack acceptance needs two things:
      - an author disposition of MEDIUM-1, (a) or (b), with the ADR sentence corrected in either case;
      - LOW-1 and LOW-2, repaired or declared.

      The S1c live re-run should use an H1 value with headroom (LOW-4) and confirm that H3 persists the window
      record (LOW-6).
27. **DR-17 repairs: M1 (the failure-statement cap), L1, the L5 tests, L6 and the L2/L3 residuals (written at 02:39:56
    2026-10-24, load about 3.6-4.7).**
    - **Process.** The ADR note came first: `4f0034079` (ADR-ML3-PROBE-0001, "S1b-1 revision (M1 …; L1, L2, L3, L6)",
      written at 02:24:57), before any `src/` change. Implementation and tests are in `c6bdfcf01`. The installed
      wheel is `9aea0c00241a5b44614d4ede58660c265c9012245b19adfca56db3a7e13f7cfc`, built at 02:28 from the working
      tree that `c6bdfcf01` commits. Every installed `xverse/` file is identical to `src/xverse` (`diff -rq`; the
      unpackaged `xcom/` is the only difference, as before).
    - **M1 (`dispatcher.py` `_fence_cap`; the `failure` statement; `_FaultStatements.decision`).**
      - **Rule.** In the lazy (root-fenced) profile, the readiness-, start- and every other failure-path `failure`
        statement gets `min(work end, now + per_unit_seconds, L_root − (C + 0.25 s))`.
        - L_root is `bootstrap._lease`, the lease `service_terminal` must find alive.
        - C = `NATIVE_CANCEL_CLOSE_SECONDS` (2.0 s) while `RunBroker._cancel_result is None`, and 0 once it exists.
      - **Fault statements.** The best-effort fault statements of `_cancel_faults` that are sent while the latch is
        already cancelled get the same cap on their `_end()`.
      - **Outcome.** A statement still unanswered at the cap ends in `ML-PERSIST-TIMEOUT` at `receive`. `_rpc`
        records it and calls `_fail()`, which fails closed. The fence then runs. The swallow of the statement's
        exception and the dispatch diagnostic are unchanged.
      - **Other paths checked.**
        - Every failure-branch entry sends its `failure` statement after `owner.cancel`: readiness and start
          failures, other failures, a fault crash and an external cancel.
        - The normal-completion path sends nothing between a cancel and the fence.
        - The statements after the fence run in terminal mode.
        - Fault statements sent before the dispatcher's own cancel without a prior cancel are not capped
          (declared in the ADR).
        - The non-lazy profile is unchanged.
    - **L1** (`_commit_controller_view`). `view._windows[:0] = self.facade._windows` before the facade swap, so
      `DispatchResult.readiness_windows` keeps every record across a recovery, including a cleanup-only view.
    - **L6.** `design-stabilization-s1b.md:187` now names `ML-PROBE-WINDOW-CUT`. The ADR note acknowledges the
      window record's location: result objects plus the S1c harness's hash-bound `maestro-run.json`.
      - **Harness imports.** A read-only `git grep` of `CANCEL_CLOSE_RESERVE` over every compat and blueprints
        worktree, and the two main checkouts, finds no importer. The only hit is a mention in compat
        `stabilization-s1c2-20261023` `review-s1c.md:1149`, which records the same check.
    - **L2 and L3** are declared residuals in the ADR note:
      - W′ = 0 for a marker restart or a generation-limited start (the root may end under the cancel;
        fail-closed);
      - the start-budget and health-scan cut sources;
      - admission does not compare W with the start budget or the cadence.
    - **Tests** (`test_stabilization_stack_load_failures.py` unless named).
      - **L5 `failed-set` (all four RB1 cases).** `_fault_in_the_targeted_live` now spies `_fail()`. Each case
        asserts exactly one `_fail()` inside the targeted call, made before any SIGTERM (`failed == [False]`), and
        `_term_sent` afterwards. The `failed-set` fault sets only `_failed`, so these assertions are not vacuous.
        The killed (unreaped) worker also accepts the SIGTERM.
      - **L5 RA2 skip:** `test_a_generation_limited_marker_start_is_not_renewed_and_its_cut_is_recorded`.
        - Setup: the renewed test's placement (below the need), with RA2's view of `_generation` lowered so that
          generation − 2 s = max(leases). The view is a `_GenerationView` proxy for that one decision only; the
          native generation and all requests and replies are unchanged.
        - Results: no renewal, `lease_renewals` unchanged, a record with `cut: true` and W′ = max(0, L − R − t0),
          and `ML-PROBE-WINDOW-CUT` with `deadline-exceeded` in Argus.
        - The renewed test is the control.
      - **L5 M2 variant:**
        `test_a_stalled_failure_statement_after_the_full_native_close_still_leaves_the_fence[fence-cap|control-uncapped]`.
        - Setup: the M2 placement (RA2 off, cut window, K.CANCEL reply read after 2.0 s). The storage worker is then
          SIGSTOPped for the `failure` RPC and SIGCONTed after it.
        - Precondition: the per-unit deadline lies past L_root.
        - `fence-cap`: the deadline is L_root − 0.25 s, the error is `ML-PERSIST-TIMEOUT`, and the persistence
          failure is `(ML-PERSIST-TIMEOUT, schedule, receive)`. `service_terminal` finds the root and the authority
          alive with lease left, and the native cancel is confirmed without `issuer_dead`.
        - `control-uncapped` (`_fence_cap` patched to the identity): the deadline is past L_root, and the fence does
          not find the root alive inside its lease. The test therefore discriminates. This replaces finding 26's
          suggested `op − 0.05 s` delay, which fast fixture storage could not make bind.
      - **L1** (`test_active_controller_recovery.py`):
        `test_readiness_window_records_survive_an_active_controller_recovery`.
        - Scenario: the planned recovery after the third observation.
        - The stack declares `running` probes only, so the test appends one `ReadinessWindow` per original-facade
          start. The carrying does not depend on how a record was made.
        - Asserted: the recovery completed and the view was committed (`driver.facade is
          driver._controller._view`). The ≥ 2 records are in `DispatchResult.readiness_windows` and the view, in
          order, with no extra record, and the closure is complete. Without the carry, the result would be empty.
      - **Regressions.** No existing expectation changed. The RB1 helper's return value grew by one list; its only
        caller was updated.
    - **Results** (wheel `9aea0c00…`, one pytest process at a time, 02:30:21-02:39:40, load 3.59-4.68). All passed,
      none failed or skipped. Before the run, `test_stabilization_stack_load_failures.py` alone passed 22 in 46.9 s,
      and the new recovery test passed in 6.2 s.

      | Suite | Passed | Time |
      | --- | --- | --- |
      | `test_stabilization_*` (all files) | 484 | 136.1 s |
      | `test_persistence*` | 29 | 29.1 s |
      | `test_provider.py` | 35 | 19.9 s |
      | `test_run_broker.py` | 11 | 12.4 s |
      | `test_affa_*` | 124 | 12.3 s |
      | `test_runtime_entry.py` | 8 | 9.2 s |
      | `test_run_teardown.py` | 9 | 10.3 s |
      | `test_teardown.py` | 27 | 24.8 s |
      | `test_closure.py` | 31 | 23.2 s |
      | `test_shared_closure.py` | 10 | 11.6 s |
      | `test_schedule_plan.py` | 48 | 14.9 s |
      | `test_dv05_dv06_bounds.py` | 7 | 12.3 s |
      | `test_dispatcher.py`, `test_dispatch_diagnostics.py`, `test_dispatch_observe.py` | 22 | 33.6 s |
      | `test_lazy_dispatcher.py` | 13 | 19.8 s |
      | `test_shared_dispatcher.py` | 3 | 10.7 s |
      | `test_service_order.py`, `test_load_aware_budgets.py` | 11 | 12.0 s |
      | `test_run_renewal.py` | 9 | 15.2 s |
      | `test_leaseguard.py`, `test_releasegate.py` | 68 | 3.7 s |
      | `test_schedule_worker.py` | 15 | 14.1 s |
      | `test_recovery.py`, `test_active_controller_recovery.py`, `test_terminal_controller_inventory.py`, `test_controller.py` | 55 | 96.0 s |
      | `tests/thesis_lite/faults` (fault-statement path) | 55 | 33.3 s |

      Total: 1074.
    - **Deviations.**
      - **The fixed 2.0 s term of DR-17 (flagged for the author).** DR-17 writes the cap as
        `L − (2.0 s + 0.25 s)`.
        - On the readiness and start paths the native close has already been spent before the `failure` statement:
          the cancel in `ProcessReadiness.start` and `owner.cancel` are synchronous. RA5 then leaves only
          `op + 0.25 s`, so a fixed `L − 2.25 s` would be in the past.
        - The statement would then be refused before the send (F-08) whenever the cancel took longer than about
          `op` (0.38 s live). The failure event would be lost with no storage stall, contrary to DR-17's
          "a storage stall then costs the failure record" and to RA5.
        - The term is therefore 2.0 s only while a close can still be ahead of the fence (no broker cancel result:
          an external canceller mid-exchange during `_cancel_faults`), and 0 after it.
        - On the readiness and start paths the cap is `L − 0.25 s`, which is finding 26's option (b) as written.
          The literal fixed term is a one-line change in `_fence_cap`.
      - **The cap also covers the post-cancel best-effort fault statements**, the one other reachable path to the
        fence after a cancel. Fault statements before any cancel are not capped (declared).
      - **The L1 test uses synthetic records** on a running-only recovery stack (above).
      - **The L5 M2 variant uses a SIGSTOP stall**, not a fixed RPC delay (above).
    - **Residuals.**
      - L2 and L3 as declared.
      - A cancel that overruns its own bound, so that `L_root − 0.25 s` is already past, makes F-08 refuse the
        `failure` statement before the send. Nothing is recorded as a persistence failure, and the run-terminal
        `failed` record follows without the failure event.
      - The fence's own `service_terminal` deadline is still covered only by the 0.25 s margin.
      - Uncapped pre-cancel fault statements.
      - Harness H1 (1.7 s, DR-17) is an S1c item and is not changed here.
    - **Effect.** Every finding 26 note has an implemented or declared disposition. The stack acceptance still needs:
      - the author's confirmation of the C-term interpretation;
      - an independent review of `4f0034079`..`c6bdfcf01`;
      - the decisive full installed-wheel run and DV12;
      - the S1c live re-run with H1 = 1.7 s and the H3 window record.
28. **Independent review of `4f0034079`..`49d411c31` (DR-17: M1 fence cap, L1, L5 tests, L6) (written at 02:51:33
    2026-10-24, load about 3.6-4.1). Verdict: PASS WITH NOTES.**
    - **Scope and build.** The diff `4f0034079~1..49d411c31` was read in full. That covers `dispatcher.py`, the two
      test files, the ADR note, the design line and finding 27. The installed wheel is
      `9aea0c00241a5b44614d4ede58660c265c9012245b19adfca56db3a7e13f7cfc` (02:28:39).
      - `diff -rq` finds the installed `xverse/` identical to `src/xverse`; only the unpackaged `xcom/` differs.
      - `git diff c6bdfcf01 49d411c31 -- src` is empty and the worktree is clean, so the wheel is the source of
        `c6bdfcf01`.
    - **Tests rerun** (installed wheel, one pytest process at a time):
      - `test_stabilization_stack_load_failures.py`, the new L1 recovery test, `test_dv05_dv06_bounds.py` and
        `test_lazy_dispatcher.py`: 43 passed in 83.4 s;
      - `tests/thesis_lite/faults`, `test_stabilization_s1b_start_failure.py` and `test_run_broker.py`: 73 passed in
        65.0 s;
      - a reviewer probe, kept outside the repository (below): passed. None failed or skipped.
    - **M1, `_fence_cap` (`dispatcher.py:1389-1398`).**
      - **The C term cannot race unsafely.**
        - `RunBroker._cancel_result` moves only from None to a value (`run_broker.py:506`, `:1087`). Reading None
          gives the larger term (C = 2.0 s). Reading a value means the close is spent, whether the K.CANCEL reply
          came or the revoke did.
        - If another thread sets the result between the cap and the send, the cap is only 2 s too strict. At worst
          that costs one best-effort `fault` statement; it never lets a statement run into the fence.
        - On the `failure` statement C is always 0. `owner.cancel` (`owner.py:761-765`) reaches `RunBroker.cancel`
          synchronously, and that call writes `_cancel_result` before it returns. This holds even with an
          external canceller mid-exchange: the dispatcher's own call waits on `ML-AFFA-CONFLICT`, and on its expiry
          `BootstrapError` (a `ValueError`) takes the revoke path. So C = 2.0 is reachable only for the
          `fault` statements of `_cancel_faults`, as the ADR says.
        - Lazy implies native (`dispatcher.py:491-495`), so `self._broker` is never None there.
        - The cap is an absolute time, so several capped statements in a row cannot together pass
          `L_root − 0.25 s`.
      - **Where the cap applies.**
        - The `failure` statement (`:1684-1694`).
        - Best-effort `fault` statements while the latch is cancelled (`:1914-1916`).
        - Nothing after the fence, and nothing in the non-lazy profile.
        - The statements after the fence (`step-disposition`, `unit-disposition`, `run-terminal`) are uncapped.
          No required record is newly dropped by design.
        - The only records that can be lost are the failure event and best-effort fault events, and only in the
          bands below.
      - **A cap that has passed** is refused by F-08 before the send. The refusal is swallowed (`:1712`), and the
        dispatch diagnostic keeps the code.
        - The schedule evidence does not require a failure event for a failed run (`schedule_evidence.py:683`).
        - `run-terminal` carries no diagnostic code.
        - In that band the cause (`ML-PROBE-WINDOW-CUT` or `ML-PROBE-NOT-READY`) is therefore visible only in
          `DispatchResult.diagnostic` and the window record (result objects, and `maestro-run.json` through the
          harness), not in Argus. That is fail-closed and diagnosable outside Argus, as finding 27 declares.
      - **The uncapped pre-cancel fault statements are acceptable.**
        - Each is bounded by `_end()`: at most `now + op`, and at most the root lease.
        - A stall costs at most one `op` before `_fail()`. Every later statement then fails fast, or is capped with
          C = 2.0 because the latch is now cancelled.
      - **The C-term interpretation is supported.** Under RA5, after the last attempt the lease left is
        `2 + op + 0.25`. A cancel of duration d then leaves `op + 0.25 − d`. A literal `L − 2.25 s` cap would be
        `now + op − d`, which is past for every d > op (0.38 s live). The interpretation still needs the author's
        confirmation, as finding 27 records.
    - **L1 (`dispatcher.py:795`).** Carrying the records into one fresh view is correct.
      - Each recovery builds a new `ProcessReadiness` (`recovery.py:436,465`). The prepend keeps the order, and a
        later recovery chains the records through the facade of the one before.
      - The prepend comes after every check in `_commit_controller_view`, so a refused commit loses nothing.
      - The re-commit case of LOW-1 below is the exception.
    - **Tests.**
      - **M2 SIGSTOP variant: discriminates.**
        - The same placement passes with the cap and fails without it, because the identity patch flips the fence
          outcome.
        - `deadline == root_lease − 0.25` (1e-6) pins C = 0 on the readiness path.
        - The `per_unit > root_lease` precondition makes sure the control is meaningful.
        - The K.CANCEL delay is still only the client's read (finding 26 LOW-5, declared).
      - **The `_fail` spy: meaningful.**
        - `failed == [False]` needs exactly one `_fail()` in the targeted call, made before any SIGTERM.
        - A misclassification as `PersistenceCancelled` makes no `_fail()` call, so it would give `[]`.
      - **The generation-limited skip: real.**
        - RA2's own code runs with only `_generation` lowered.
        - If the skip branch were missing, `_renew_service` would renew through the real session's bound methods
          and `renewed` would be True.
        - The float comparison `(x + 2e9)/1e9 − 2 ≤ x/1e9` fails about 1.5e-5 of the time on random `x`, a
          negligible flake.
      - **L1 with synthetic records: adequate** for the loss that finding 26 found. It does not cover a re-commit or
        a second recovery (LOW-1, LOW-4).
    - **Regressions.**
      - Untouched by this diff: `persistence.py` (S1a-1 RB1), `run_broker.py` (S1a-3/S1a-6 cancel bounds), the
        S1b TERM/stop grace and the non-lazy profile.
      - Run in this review: DV05/DV06 bounds, the lazy dispatcher, the fault path and the S1b start-failure suites.
      - Finding 27's table (1074; the sum checks) covers the rest. No regression found.
    - **LOW-1 (the L1 carry duplicates every record when the same view is committed twice):
      `dispatcher.py:795`, `:846-855`.**
      - In `_drain_controller_recovery`, `_commit_controller_view(successor, ticket)` can succeed and the
        request-cost check (`:847`) can then raise `ML-SCHEDULE-RECOVERY-INCOMPLETE`. If so, the `except` cancels and
        commits `successor._recovery._view` again, cleanup-only (`:855`). That view is now `self.facade`, so
        `view._windows[:0] = self.facade._windows` is `x[:0] = x`, and it doubles the list.
      - **Reviewer probe.** The probe is `test_l1_recommit.py` in the reviewer's scratchpad, not committed. It is
        the L1 test with the post-commit check forced to raise. Its output was `commits [(False, id, 4), (True, id,
        8)]`: 4 records became 8, with the same view object both times.
      - This contradicts the ADR sentence "no record is lost or duplicated" (`ADR-ML3-PROBE-0001.md:252`).
      - The impact is limited:
        - only `DispatchResult.readiness_windows`, through the harness `readinessWindows`, is affected; Argus is
          not;
        - the path is a failed recovery whose ordinary commit succeeded;
        - the trigger is a request-cost overrun guard.
      - **Repair (one line):** `if view is not self.facade: view._windows[:0] = self.facade._windows`, with the probe
        as a regression test.
      - **Disposition: can be declared** for the decisive run. Fold the repair into the next `src/` change. If it is
        made now, the wheel must be rebuilt and the decisive run must use the new wheel.
    - **LOW-2 (a cap shorter than one round trip fails the storage channel with no stall):
      `dispatcher.py:1069-1071`, `:1689`; ADR `:241-245`.**
      - F-08 refuses only when `deadline − now < est(kind)`. `failure` is sent once per run, so `est("failure")` is
        always 0.
      - A cap that is in the future but shorter than one RPC round trip is therefore sent. It times out
        (`ML-PERSIST-TIMEOUT`/`-LATE`), and `_fail()` loses every later terminal record, so the closure is
        incomplete.
      - This band is about one RTT wide, just before the past-cap band. In it a run with healthy storage, which the
        uncapped deadline would have recorded completely, becomes a recorded persistence failure. That is
        fail-closed and recorded, but the ADR residual describes only the past-cap outcome (F-08 refusal, channel
        kept).
      - **Repair (optional):** refuse before the send when the cap leaves less than a floor, for example `op`. This
        trades a stalled-statement timeout for a refusal.
      - **Disposition: declare.** Add one sentence to the ADR residual.
    - **LOW-3 (residual and comment wording).**
      - **ADR `:244` "This band is the cancel exceeding its own bound".** The past-cap band also contains cancels
        that stay inside their admitted bounds:
        - the S1a-3 busy-connection wait (`CANCEL_LOCK_WAIT_SECONDS` = 0.5 s);
        - the K.CANCEL frame (`CANCEL_REQUEST_SECONDS` = 2.75 s, `run_broker.py:45-51`);
        - the revoke fallback (1 s).

        The band is "the cancel exceeding the 2.0 s native close the reserve assumes", not its own bound.
      - **ADR `:236-239` (not capped).**
        - The fence exposure is not specific to pre-cancel fault statements. On every non-marker lazy failure path,
          `_service` keeps only `renew_margin = (service_calls + 1)·op` (1.52-1.9 s live, `dispatcher.py:1185-1211`)
          of lease. That is less than `C + 0.25 s`, so a full 2.0 s close can outlive the root whatever the fault
          statements do. The pre-cancel fault statements add at most `op` to this existing exposure.
        - Its outcome is the root lease ending before the fence (the finding 21 (A) signature: closure incomplete,
          fail-closed). "An unconfirmed cancel is revoked" does not describe that outcome.
      - **ADR `:219`.** "At least the 0.25 s margin left" is the margin less the time of `_fail()` (SIGTERM,
        shutdown) and `_close_restarts`.
      - **ADR `:138-141`.** The S1b-1 RA5 residual "the `failure` statement's own deadline stays `min(work end, now +
        per_unit_seconds)` … can still pass L" is superseded by M1 but has no correction mark, unlike `:122-124`.
      - **`providers.py:44`.** The `cancel_close_reserve` docstring still says "one admitted statement budget", the
        wording that DR-17 corrected. It is in `src/`, so changing it changes the wheel.
      - **Disposition: declare, then correct.** Correct the ADR lines now; they are docs and do not affect the wheel.
        Correct the docstring with the next `src/` change.
    - **LOW-4 (test reach): `dispatcher.py:1394`, `:1914-1916`.**
      - No test makes the cap bind on a `fault` statement, and no test reaches the C = 2.0 branch (an external
        canceller still inside K.CANCEL during `_cancel_faults`). The only reference to `_fence_cap` in the tests
        is the M2 control's identity patch.
      - The L1 test covers neither the re-commit of LOW-1 nor a second recovery.
      - **Disposition: declare.** Add the tests with the next change in this area.
    - **Effect.** No issue blocks the decisive full installed-wheel run and DV12 on `c6bdfcf01` (wheel
      `9aea0c00…`).
      - Stack acceptance still needs the author's confirmation of the C-term interpretation (finding 27, deviation
        1).
      - LOW-1 to LOW-4 must be declared or repaired. If LOW-1 is repaired before the run, the wheel and the
        decisive run move to the new commit.
      - The S1c live re-run items (H1 = 1.7 s, the H3 window record) are unchanged.

29. **Dispositions of finding 28 (written at 02:53:08 2026-10-24, before the repair; thesis DR-17, delegated).**
    - **LOW-1, repaired.** The L1 carry in `_commit_controller_view` is guarded: `if view is not self.facade`.
      The cleanup-only re-commit of the same view then carries nothing, and the records are not duplicated. The
      reviewer's probe becomes a regression test in `test_active_controller_recovery.py`, which asserts exactly
      one record per marker start after a failed recovery is re-committed cleanup-only.
    - **LOW-3, repaired (wording only).**
      - The `providers.py` `cancel_close_reserve` docstring now says "a nominal one-RPC allowance".
      - ADR-ML3-PROBE-0001:
        - The DR-16 residual (`:138-141`) gets a mark that it is superseded by the DR-17 cap.
        - The stall outcome (`:219`) no longer guarantees "at least 0.25 s": it names the time spent in `_fail()`
          and `_close_restarts`.
        - The "not capped" bullet (`:236-239`) states that every non-readiness failure path keeps only
          `renew_margin` (1.52–1.9 s live), and that the outcome is the root lease ending before the fence,
          fail-closed.
        - The expired-cap residual (`:244`) now reads "a cancel longer than the 2.0 s close the reserve assumes",
          which includes cancels that stay within their own bounds.
    - **LOW-2, declared.** A cap that is still in the future but shorter than one round trip is still sent, because
      F-08 has no estimate for the once-per-run `failure` statement. The statement then times out and `_fail()`
      loses the later terminal records, without any storage stall. This is fail-closed, and it is recorded in the ADR.
    - **LOW-4, declared.** No test makes the cap bind on a fault statement or reaches the C = 2.0 branch, and the
      L1 test does not cover a second recovery. These are recorded as test-reach residuals.
    - **The decisive full run** is moved to the repair commit.
    - **Result (03:05:13).**
      - Wheel `a54844d3f07c5b3a…`.
      - The new regression test passes. The reviewer's probe, which asserts the old doubled count, now fails on that
        assertion: 4 records, not 8.
      - The full related list (`dr17-suites.sh`, 21 groups) ran from 02:55:42 to 03:05:03 at load 3.9–5.1: 1075
        passed, none failed or skipped.

30. **Diagnosis: an adapter health slot due inside its Stop bracket is `unverifiable` (S1c live; written at 05:25:19
    2026-10-24, load about 3.6-4.2, before any repair; no `src/` change).**
    - **Symptom.** In 2 of the 71 runs that got past start-up, both in the newest run set, execution succeeds but
      the run ends `ML-SCHEDULE-EVIDENCE-INCOMPLETE`. The Maestro Argus writer is `failed`, and the terminal-report
      blockers are `normal-records`, `required-coverage` and `uncertain-applicability`
      (`terminal_runtime.py:136-140`).
      - Exactly one `lifecycle-coverage.json` row causes this. It is the `normal-record` row `…g1.health.5` of
        `carla-adapter-instance`, with `applicable: null`, `status: unverifiable` and the diagnostic "Applicability
        is not established by original retained facts." (`coverage.py:774`).
      - The row still lists a `-health` event in `evidenceIds`.
    - **Evidence (read-only).** Under `.x-verse-build/runs/lite-stabilization-s1/s1c2-part2-dev7-20261024/`:
      - **Failing runs:** `dev-s1c2p1-20261024T051109-freeze-vcu` and `dev-s1c2p1-20261024T051454-nominal`. The
        files are `maestro-tmp/test_live_closed_loop0/argus-maestro/{lifecycle-coverage.json, broker-projection.json,
        events.jsonl}`, with these sha256 prefixes:
        - `T051109`: coverage `0e646507…`, broker `310df44d…`;
        - `T051454`: coverage `df90dd09…`, broker `fd155871…`.
      - **Passing comparisons:** `T050838-nominal`, `T051014-freeze-vcu` and `T051653-long-run`, and the sets
        `s1c2-part2-dev5-20261024` and `s1c2-part2-dev6-20261024`.
      - **Harness:** blueprints `test_live_closed_loop.py:460-468`. The `ProbePolicy(unit, 5, 5, …)` gives cadence
        5 s and freshness 5 s, and `admit_coverage` uses `health_policies = (cadence, freshness)`.
    - **Recorded facts.** These are the adapter's generation-1 broker row and its annotations. All times are relative
      to its Release-ACK (the anchor), in host seconds.

      | run | Stop request | Stop ACK | Stop duration | slot-5 end − Stop request | latest slot-5 sample | result |
      |---|---|---|---|---|---|---|
      | T051109 freeze | 24.924 | 25.024 | 0.101 | +0.076 | 24.542 | `None` → unverifiable |
      | T051454 nominal | 24.979 | 25.013 | 0.034 | +0.021 | 24.425 | `None` → unverifiable |
      | T051014 freeze | 25.080 | 25.220 | 0.140 | −0.080 | 24.763 | slot 5 `True`, slot 6 `False` |
      | T050838 nominal | 24.415 | 24.567 | 0.153 | +0.585 | 23.639 | slot 5 `False` |

      - In both failing runs, slot 5 is [20, 25] s and holds three valid health samples. In T051109 they are at
        21.255, 22.871 and 24.542 s, all before the Stop request. The Stop outcome annotation is at 25.025 s, at the
        ACK.
      - The adapter's Stop request comes 24.4–26.3 s after its Release-ACK in the nominal and freeze runs of
        dev5–dev7. That is close to the 25 s slot boundary.
        - In dev5, four of the five nominal and freeze runs place it 0.30–0.51 s before 25 s. The ACK also comes
          before 25 s, so slot 5 is `False`. The fifth places it at 25.446 s.
        - In dev7 the placements are 24.415, 24.924, 24.979 and 25.080 s. Two of them land inside the bracket.
      - A hit needs the slot end to fall in (Stop request, Stop ACK]. The bracket is 0.03–0.21 s wide, against a 5 s
        cadence, so whether a run hits is decided by start-up and tick jitter.
      - No other unit's slot end fell inside its bracket in dev5–dev7.
    - **Mechanism.**
      - `health_window` (`coverage.py:795-805`) sets slot N to [A + (N−1)c, A + Nc], where A is the Release-ACK and c
        the cadence. It returns:
        - `True` if the slot ends at or before the Stop request;
        - `False` if it ends after the Stop ACK;
        - otherwise `None` (`:805`).
      - `assess` first computes the status from the in-window samples (`:770-772`), and gets `satisfied`. That is
        why `evidenceIds` lists the first sample. It then overwrites the status with `unverifiable` because
        `applicable is None` (`:773-774`).
      - `terminal_runtime.py:140` adds `uncertain-applicability` for any `applicable is None` row, whatever its
        status. `_aggregate` (`coverage.py:830-833`) makes `normalRecordStatus` `unverifiable`, hence
        `normal-records` and `required-coverage`.
      - The closure's "normal records complete" and "cleanup complete" are separate harness and closure facts. I did
        not trace them.
    - **Classification (confidence high).**
      - **Not an implementation bug against the contract.** The code implements `coverage-assessment.md:28-34`
        exactly: "Due before Stop-request is applicable, after Stop-ACK is inactive, and inside an uncertain Stop
        bracket is unverifiable."
      - **Not a missing retained fact.** All four bounds are present, ordered, and within the terminal end.
      - **Not an inclusive/exclusive comparison slip.** The bracket has positive width (34–101 ms), so changing `<=`
        or `>` cannot remove the case.
      - **The applicability uncertainty is genuine.** The unit's active end lies somewhere inside the bracket, so
        whether the full slot was owed is unknown. The rule that bracket uncertainty must not be rounded into an
        inactive slot (`review-affa17.md` finding 96, `:846`) therefore still holds.
      - **But it is immaterial when a valid in-slot sample is retained.** If the slot is applicable, the sample
        satisfies it. If it is not, the row is not-applicable. Both outcomes are accepted by `_aggregate` and by the
        terminal report.
      - **Defect.** This is a specification-level gap in the outcome rule (design defect). The contract makes "due
        inside the Stop bracket" unverifiable even when the evidence discharges the obligation either way. It
        manifests at a timing boundary. Without an in-slot sample, the case is a true uncertainty (missing vs.
        inactive) and must stay fail-closed.
    - **Reproduction.** `tests/thesis_lite/maestro/test_stabilization_coverage_health_boundary.py`, run on the
      installed wheel `a54844d3…` (= `ee91697a4` `src`): **1 failed, 12 passed**.
      - **RED (fails by design):** `test_red_slot_due_inside_stop_bracket_with_in_slot_sample_is_satisfied`.
        - It uses the neutral `Fixture` with unit a, cadence 1 s, Release-ACK 0.2 s and slot 3 = [2.2, 3.2] with a
          sample at 3.0 s. Its Stop bracket is set to [3.15, 3.25], the live geometry.
        - Observed: `(None, 'unverifiable', 'Applicability is not established…')` on exactly that one row, with
          `normalRecordStatus` `unverifiable`.
        - Expected after the repair: `applicable True`, `satisfied`, the 3.0 s sample as evidence, `health.4`
          not-applicable, `normalRecordStatus` complete, and no `applicable is None` row.
      - **Controls (pass now, and must still pass after the repair):**
        - the same bracket with the in-slot sample deleted stays `None`/`unverifiable`;
        - a slot due before the Stop request is `True`/`satisfied`;
        - a slot due after the Stop ACK is `False`/`not-applicable`;
        - the default Fixture is `True`/`satisfied`;
        - a missing `stopAcknowledgedAt` with a sample present stays `unverifiable` (CV07);
        - the recorded live brackets, as constants, give through `health_window` slot 5 `None` for T051109 and
          T051454, `True` for T051014 and `False` for T050838. This is white-box; the admitted active end is taken
          to be generous.
    - **Repair options** (all fail-closed, none needs M1):
      - **A (recommended): discharge the bracket case by an observation.**
        - Only when all Release and Stop bounds are present and consistent and Stop request < slot end ≤ Stop ACK,
          and at least one health event for that unit and generation is valid, passes `source_ok`, and lies in
          [slot start, min(slot end, Stop request)]: report `applicable True` and `satisfied` with that sample.
        - Otherwise the row keeps `None`/`unverifiable`.
        - Change: `coverage.py:795-805` and `:770-774` only. No producer, schema, terminal-report or M1 change.
          `verify_closed` recomputes with the same code, so pre-closure and offline stay consistent.
        - `True` is a conservative superset: it holds the slot to the stricter standard, which the sample meets. It
          never marks a missing check satisfied, and the no-sample and missing-bound cases keep failing closed.
        - Bounding the sample by the Stop request is stricter than the spec's "in that slot". It costs nothing
          live: the latest samples precede the request by 0.38 s and 0.55 s.
        - Trade-offs:
          - the spec text must change;
          - `expectedObligationsDigest` and the report core change only for runs that hit the bracket;
          - the two recorded failing reports would recompute differently, but they stay failed as recorded.
      - **B: treat the bracket as applicable.** A sample gives `satisfied`; no sample gives `missing`, not
        `unverifiable`. This is fail-closed and simpler, but it asserts a gap that may not exist and changes the
        diagnostic class. The no-sample control would change.
      - **C (rejected): end the obligation at the Stop request** (slot end > request → not-applicable). This rounds
        the bracket into inactive, against finding 96 and the contract. It would also make a nearly complete slot
        without a sample not-applicable.
      - **D (rejected): keep `applicable None` but let `satisfied` pass** (`terminal_runtime.py:140`). This spans two
        modules and weakens what `uncertain-applicability` means.
      - **E (workaround only): move the stop or observe ticks** in blueprints so the adapter's stop is far from a
        multiple of 5 s after Release-ACK. Jitter keeps the probability nonzero, so it is not a repair.
      - **F (rejected): narrow the Stop bracket at the producer** (`evidence.py:326`, `collection_evidence.py:52-68`).
        This lowers the probability but cannot remove the case, and the producer verification changes.
    - **Documents a repair touches.**
      - `coverage-assessment.md:28-34` (the coverage contract, `README.md:438`) needs a "discharged bracket" clause.
        CV07 is unchanged.
      - The health-slot paragraph of `affa-coverage-runtime-composition.md:29-35`.
      - An amendment section in ADR-ML3-EVIDENCE-0001, which carries the coverage and runtime-scope decisions
        (`:105-115`). It is the nearest coverage ADR; there is no separate ADR-ML3-COVERAGE.
    - **Out of scope, noted.** Separate `…g1.ready` rows are `unverifiable` in the no-carla runs of dev6 and dev7
      (adapter) and in dev5 `T044245-cancel-paused` (lite-driver). These are start-up paths and were not examined.

31. **S1a-6 repair of finding 30 per thesis DR-20, option A (written at 05:40:42 2026-10-24, load about 4.4-4.7).**
    - **Contract first.** `33486ad22` (written at 05:27:51) was committed before any `src/` change. It updates:
      - `coverage-assessment.md`, the health-slot paragraph: a "discharged bracket" clause;
      - `affa-coverage-runtime-composition.md`, the health-slot paragraph;
      - ADR-ML3-EVIDENCE-0001, with a new "Amendment S1a-6" section.
    - **Code (`59a130f73`, `src/xverse/maestro/coverage.py` only).**
      - `health_window` now returns (applicability, window, cut). The cut is the Stop request, and it is set only on
        the final bracket branch. That branch is reached only after every existing check has passed:
        - Release observed and ordered within the admitted interval;
        - a non-empty slot inside the admitted end;
        - Release ACK ≤ Stop request ≤ Stop ACK ≤ terminal end;
        - Stop request < slot end ≤ Stop ACK.

        Every other return carries no cut, and the classification is unchanged.
      - In `assess`, the health branch runs only when applicability is `None` and a cut is set. It reruns the
        existing `one(..., many=True, source=source_ok observe/observation running|not-ready)` on the in-window
        events whose host time is ≤ the cut. Only a `satisfied` result sets applicability `True` and the status
        `satisfied`, with that evidence. Otherwise the row falls through to the unchanged `unverifiable` overwrite.
      - The expected-obligation entry keeps the fact-derived `None` for a discharged slot. `expectedObligationsDigest`
        is therefore unchanged by the repair for every run, and it does not depend on arrived samples.
        - **This corrects finding 30**, which expected the digest to change for runs that hit the bracket.
      - Not changed:
        - `terminal_runtime.py`, including the `uncertain-applicability` blocker;
        - the schema, the broker projection and its producers, and the slot arithmetic;
        - CV07, and M1.
      - The offline `verify_closed` recomputes through the same `_Assessment.assess`.
    - **Tests (`test_stabilization_coverage_health_boundary.py`, 19 tests).**
      - The finding-30 RED test is now green, and its 12 controls still pass.
      - New fail-closed controls, all passing:
        - a sample after the Stop request but before the slot end (Stop [2.95, 3.25], sample at 3.0 s) stays
          `unverifiable`, while slot 2 stays `satisfied`;
        - a hash-valid sample re-pointed at the start-outcome M3 record fails `source_ok`. It is not `satisfied` in
          an applicable geometry, and it stays `unverifiable` in the bracket;
        - three inconsistent bound orders stay `unverifiable`: ACK before request, ACK beyond the terminal end, and
          Stop request before Release ACK;
        - deleting the discharging sample turns the row `unverifiable` and leaves `expectedObligationsDigest`
          unchanged.
      - The recorded-bracket control now also asserts that the cut is exposed only for the `None` slots.
    - **Wheel and suites.**
      - The wheel was rebuilt from the working tree that `59a130f73` commits: `cea5ced404c27715…`
        (`cea5ced404c277157df9496086fd4a0a8f011c58e01c8e7d659fc2fb5b53cddf`).
      - The related suites ran one pytest process at a time on that installed wheel, from 05:29:42 to 05:40:31 at
        load 3.3–5.0, in 14 groups and 54 files:
        - every `tests/thesis_lite/maestro` file that imports `xverse.maestro.coverage`, `terminal_runtime` or
          `verify_closed`;
        - `test_stabilization_*`, `test_closure.py`, `test_shared_closure.py`, `test_dv05_dv06_bounds.py` and
          `test_affa_*`.
      - **Result: 1083 passed, none failed, skipped or errored.** The log is in the session scratchpad,
        `f30/dr20-suites.log`.
    - **Residuals.**
      - **Not replayed on the live retained inputs.** The two failing dev7 runs were not reassessed with the new
        code. Their admission is not retained beside the run in a form this session could reuse without the
        harness.
        - Their recorded samples precede the Stop request by 0.38 s and 0.55 s, so a discharge is expected.
        - Confirming it needs a live S1c run or an admission-capable offline replay, and neither is authorized here.
      - **The rule is stricter than "in that slot".** A slot whose only samples come between the Stop request and
        the slot end still fails closed. That is by design (DR-20).
      - **No change to the rate.** About 1–4 % of runs per unit can still hit the bracket. Those runs now pass only
        when a pre-request sample exists. Given the ~1.6 s live health interval, that is expected whenever the slot
        is healthy.
      - **The `ready` rows** noted at the end of finding 30 remain out of scope.
