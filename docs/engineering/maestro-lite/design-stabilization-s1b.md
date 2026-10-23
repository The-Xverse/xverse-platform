# S1b design: graceful stop, private stderr capture, nonce-marker readiness (2026-10-23)

**Status.** Design record, written before any S1b code. The thesis requirements are S1 FR-009 to FR-013
(`specs/029-lite-stabilization`). The amendments of the frozen limits are S1b review-log finding 1. The decisions
D-1 to D-4 below are recorded as the thesis delegated revisions DR-7 to DR-10.

**Origin.** It was produced by a read-only design survey of `d8b44719c`. Each claim about current behaviour
cites file:line at that revision.

**Scope.** Only the AF17 path changes. Every new capability is opt-in. Undeclared units stay byte-identical on
the wire, in digests and in evidence.

## Decisions

- **D-1 (DR-7), the terminal fence.**
  - In lazy mode, `_cleanup` sends `broker.cancel('dispatcher-terminal-fence')` before `teardown.run`
    (dispatcher.py:1403-1410). Every end-of-run stop therefore follows CANCEL's `freeze_all` and is forced.
  - A graceful stop applies only to scenario `stop` steps, which are optional and run through `teardown.phase`
    while the authority is open (projection.py:477-482, dispatcher.py:1394-1399), and to restart stops.
  - Accepted as is. S1c-2 schedules explicit `stop` steps, so that nominal runs exercise TERM.
  - A graceful pre-pass before the fence would change the S1a closure order, and is not done.
- **D-2 (DR-8), LC09 out of scope.**
  - The owned runtime uses only AF17: `runtime_entry` requires `persistence.collection` (runtime_entry.py:60),
    which makes the dispatcher lazy and requires `RunUnitIssuer` (dispatcher.py:455, 487-512).
  - The LC09 catalog launcher is used only by tests (`BootstrapSession.catalog`, bootstrap.py:1134-1165).
  - `make_launch_recipe` refuses any declared control or a non-`running` probe with
    `ML-LAUNCH-CONTROL-UNSUPPORTED`, so a declared capability never silently degrades.
  - This deviates from the plan.md wording "both C launch paths".
- **D-3 (DR-9), stderr is retained, not collected.**
  - It is a private, capped file in a trusted, run-scoped directory outside the collection source root.
  - It is never copied through the public collection, which indexes paths into the public manifest
    (collection_runtime.py:110-114; collection_evidence.py:141-143).
  - This deviates from the plan.md wording "collected artifact".
- **D-4 (DR-10), a two-step TERM.**
  - TERM is a new AF17 request. Python waits out the grace with the exchange lock free, then sends STOP.
  - A grace wait inside STOP would hold the lock for seconds, and a concurrent cancel would revoke after its
    0.5 s S1a-2 wait.

## Paths

| Path | Used by the owned runtime? | S1b |
| --- | --- | --- |
| AF17 run authority (`run_authority.c`, `RunBroker`, `RunUnitIssuer`) | yes, the only one | all three features |
| LC09 catalog launcher (`catalog_launcher.c`, `CatalogLauncher`) | no (tests only) | out of scope; declared controls are refused |
| Python force cleanup (`prbc.terminate`, `teardown._emergency`) | fallback | unchanged (SIGKILL) |
| Native kill paths: `cleanup()`, FAULT_KILL, CANCEL `freeze_all` | yes | unchanged |

## Protocol

### AR17 version 2: a sealed per-unit recipe, emitted only when a feature is declared

| Offset | Size | Field | Rule |
| --- | --- | --- | --- |
| 0 | 4 | "AR17" | |
| 4 | u32 | version = 2 | version 1 keeps today's 16-byte header |
| 8 | u32 | argc | 1..32 |
| 12 | u32 | envc | ≤ 64 |
| 16 | u32 | grace_ms | 0, or 1..4000; nonzero permits TERM |
| 20 | u32 | stderr_max | 0 (`/dev/null`), or 1..1048576 |
| 24 | u32 | probe | 0 = `running`, 1 = `nonce-marker` |
| 28 | u32 | reserved | 0 |
| 32 | u64 | stderr_dev | 0 if and only if `stderr_max == 0` |
| 40 | u64 | stderr_ino | nonzero if and only if `stderr_max != 0` |
| 48 | | strings | unchanged encoding |

Validation is the same in C `recipe()` and in Python `AuthorityRecipe`:
- the version is 1 or 2;
- a version 2 recipe with all features zero is rejected;
- the bounds above apply;
- `reserved == 0`;
- the stderr identity is present if and only if `stderr_max != 0`;
- `offset == size`.

### File descriptors

REGISTER carries 5 fds when `stderr_max != 0`: cg, image, cwd, recipe and the stderr directory. Today it carries
4. The fifth fd must match `stderr_dev`/`stderr_ino`. It is dup'd with `F_DUPFD_CLOEXEC` to an fd ≥ 3. No fd is
passed at STAGE.

### Kinds and state bits

- **Kinds.** `TERM = 31` (request) and `TERM_SENT = 32` (reply).
  - TERM is not in `_CLEANUP`, so it is refused after a cancel, before it is sent.
  - C accepts `kind<=15||kind==TERM`.
- **State bits.**
  - 512 = term-sent;
  - 1024 = exited-on-term, which requires 512;
  - 2048 = marker-ready, latched;
  - 4096 = stderr-truncated.
- **Masks.** The affa_client state mask widens from `~511` to `~8191`. STAGED stays 37.

## Graceful stop (FR-009)

**Native side.**
- The TERM handler applies only to the latest generation, while open, released, alive, not frozen, not stopped
  and not retired, and only when `grace_ms` is set. It sends SIGTERM through the pidfd to the leader only (the
  DV06-N guard forbids signals by PID number), latches `term_sent`, and replies TERM_SENT. It is idempotent.
- `stop_child` does this, then the unchanged freeze, `cgroup.kill` and wait for `8|32|64`:
  - if `term_sent` and the leader was reaped with the cgroup unpopulated before the freeze, it sets
    `exited_on_term`;
  - on success it caps the stderr file and closes the probe fd.
- In `child_exec`, a unit with a declared grace gets `SIGTERM` unblocked and set to `SIG_DFL` before exec.

**Python side, `RunUnitIssuer.stop_owned(handle, deadline, *, grace_until=None)`.**
1. If the grace is declared, `grace_until` is set, no TERM has been acked, starts are not closed and the latch
   is not cancelled, send TERM with deadline `min(deadline, now + 0.5, lease)`.
2. Retain the ack in `_term_ack` and pin it in `_identity`.
3. If `ack.state & 512`, wait on the retained pidfd in steps of 10 ms or less, until `min(t + grace,
   grace_until)`, or until the latch is cancelled or starts are closed.
4. Send STOP as today.
5. Check: `1024` without `512` is `ML-RUN-STOP-ACK`.
6. Expose `stop_mode` (`exited-on-term`/`forced`) in `NativeGenerationClosure`.

**Budget.**
- `teardown._stop` passes `grace_until = deadline − STOP_FORCE_RESERVE_SECONDS (0.5) − SIZING_MARGIN·record`.
  `_emergency` passes nothing, so it is always forced.
- `teardown._need` uses `max(est('phase:stop'), grace + reserve)`.
- `admit_schedule` rejects `grace + 0.5 > NORMAL_SHARE·per_unit_seconds` with `ML-SCHEDULE-STOP-GRACE`.

## stderr capture (FR-010)

**Declaration.**
- Catalog: `process.stderr {capture: "run-scoped-private", maximumBytes ≤ 1048576}`.
- Runtime: `UnitAdmission.stderr_directory`, supplied by the trusted caller, never in the catalog or a public blob.

**Admission.** The directory is opened component by component with `O_NOFOLLOW|O_DIRECTORY`. It must be:
- owned by the uid, with `mode & 0o077 == 0`;
- empty;
- distinct per unit;
- not the cwd;
- not inside the collection source root (an `..` walk against `storage.collection.source_identity`).

**File creation.** STAGE creates `stderr-g<N>` with `openat(..., O_WRONLY|O_APPEND|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,
0600)`. `EEXIST` fails STAGE. The child gets fd 0 and fd 1 as `/dev/null` and fd 2 as the file, after the
unchanged `close_range`.

**Cap.** At STOP success, with no writers alive: `fstat`, and if the size exceeds the cap, `ftruncate` to the cap
and set bit 4096. `cleanup()` does the same as a best effort.
- `RLIMIT_FSIZE` is rejected, because it applies to every file the unit writes and raises SIGXFSZ.
- A pipe relay is rejected, because then fd 2 is not the file.
- Declared limitation: while the unit runs, the file is bounded only by the filesystem.

**Budget.** `RunBroker.admit` checks Σ public coverage artifact maxima + Σ units stderr_max × generations
≤ 16 MiB (`ML-RUN-STDERR-BUDGET`). `CollectionPlan` bytes are unchanged.

**Handles.** `inheritedHandles: closed` means that no control descriptor is inherited. fds 0 and 1 are
`/dev/null`; fd 2 is `/dev/null` or the declared private file.

## Marker probe (FR-011)

**Identity.** The probe identity is the observe `condition`: `running` or `nonce-marker`. It is already in the
plan digest (catalog.py:434-435). `src/xverse/maestro/probe_identity.py` defines
`READINESS_PROBES = ("running", "nonce-marker")`.

**Catalog.**
- Optional `process.stop {graceSeconds ∈ (0, 4]}` and `process.stderr`.
- `LifecyclePlan.process_controls`.
- The digest input carries `stop`/`stderr` only when they are declared.
- `XVERSE-CATALOG-READINESS-PROBE` is raised for a non-process provider.

**Admission.**
- providers accept `READINESS_PROBES`; a `CatalogLauncher` bind is refused.
- `_admit_image` requires the cwd to be inside the collection source root, no stale `.xverse-ready`, and a
  distinct cwd.

**Challenge (native, in STAGE, before `clone3`).**
1. For generation N > base, rename an earlier `.xverse-ready` to `.xverse-ready.g<N-1>` with `RENAME_NOREPLACE`.
2. `mkdirat(cwd, ".xverse-ready", 0700)`; `EEXIST` fails STAGE.
3. Open it as `e->probe` and check it: a directory, own uid, mode 0700.
4. Generate 32 random bytes and encode them as 64 lowercase hex characters.
5. Write `challenge` with `O_EXCL|O_NOFOLLOW`, mode 0400, 64 bytes, no newline.

The unit is frozen until RELEASE, so it cannot read a partial file.

**Check (native, on QUERY).** It runs only while open, released, not retired, not latched and with fewer than 3
checks for this generation:
1. Open `ready` with `O_RDONLY|O_NOFOLLOW|O_NONBLOCK`.
2. The file must be regular and exactly 64 bytes, and equal to the nonce under `CRYPTO_memcmp`.
3. On a match, latch bit 2048.

The directory fd is pinned. FIFOs, symlinks and oversized files are rejected without blocking.

**Readiness (`providers.py`).**
- `ProcessObservation.marker_ready` comes from `flags & 2048`.
- `start()` queries with `readiness=True`: ready means running and, for `nonce-marker`, the marker is ready.
- Attempts are spaced at `t0 + k·W/A` within `W = min(policy, observe timeout)`.
- Otherwise the result is `ML-PROBE-NOT-READY`.
- Health stays liveness-only (`probe_id = "running"`).

**Evidence and coverage.**
- `probe` and `ready` annotations carry the declared identity; `health` and `health-loss` stay `running`.
- Coverage unit rows get an optional `readinessProbe` key, present only for non-`running` probes, so existing
  bytes and digests are unchanged.
- `ready` requires `probeId == unit.readinessProbe`.

## Tests

These are plain pytest. The C code is compiled by the existing fixtures. No gtest is needed, because no C++
boundary changes.

- **`catalog_workload.c` modes:**
  - `term`;
  - `ignore-term`;
  - `marker-late`;
  - `marker-wrong`;
  - `marker-never`;
  - `stderr-flood`;
  - `streams`.
- **New `test_stabilization_s1b_native.py`.**
  - The FR-013 cases:
    - TERM honoured;
    - TERM ignored, then forced;
    - marker never;
    - marker late but within the bound;
    - stderr cap overflow.
  - Further cases:
    - cancel, then a forced stop with no TERM;
    - a frozen unit is not sent TERM;
    - TERM is refused without a declared grace;
    - a wrong nonce, a symlink or a FIFO;
    - the per-generation rename aside;
    - a stale directory rejects STAGE;
    - `O_EXCL` without following links;
    - streams and handles.
- **Other suites:**
  - `test_affa_config.py`: AR17 version 2 bytes and the rejections;
  - readiness through the RunBroker fixtures;
  - coverage acceptance;
  - teardown `stop_mode`;
  - privacy canary;
  - catalog and schema;
  - `test_dv05_dv06_bounds.py` stays unchanged and must pass.

## Risks

1. **Sealing.** Digests are unchanged when nothing is declared. The authority binary digest is pinned, so S1c
   must re-pin it.
2. **Descriptors.** New fds are `CLOEXEC` and ≥ 3; only `dup2` onto fd 2 creates an inheritable one.
3. **Cancellation latency.** It is preserved only by D-4.
4. **Teardown budget.** The grace stays inside the normal share.
5. **Kill paths.** SIGKILL paths are unchanged.
6. **The terminal fence (D-1).**
7. **State bits.** The exact bit checks are kept.
8. **Authority I/O on unit-controlled files.** It is bounded. A FUSE or NFS cwd remains a risk.
9. **Filesystems.** `renameat2` needs filesystem support.
10. **Stale or shared directories.** They fail closed.
11. **stderr at rest.** It is capped only after the cgroup is empty.
12. **Gates.** DV12 runs on the final head. CAPA is step 11.
