# Independent frozen-bytes review of the Maestro Lite native helpers (2026-10-20)

Reviewer: separate agent session (Claude, independent of the helper authors). Date: 2026-10-20. Repository: `/home/jefferson/xverse-platform-worktrees/maestro-lite-affa-20261018`.
Method: read-only source reading; SHA-256 verified before reading; nothing compiled, executed or modified. Machine-readable twin: `helper-bytes-independent-review-20261020.json`.

## Frozen inputs (all verified with sha256sum)

| File | Role | SHA-256 | Verified |
| --- | --- | --- | --- |
| `src/xverse/maestro/native/bootstrap.c` | supervisor | `21c2f70f6fbb1dec66fca39c9a44e4086f4496d46d30f28671ecd31f007cc38b` | yes |
| `src/xverse/maestro/native/catalog_launcher.c` | catalog | `8616a088a3b56a25888129729bcf0771d39f71ddb3a8f79f5affa22665445289` | yes |
| `src/xverse/maestro/native/lease_guard.c` | gate (RG06) | `5bddac9e336ff82e9ad2fd41f234230573c955646b740df66372dc9a5c2485d6` | yes |
| `src/xverse/maestro/native/run_authority.c` | authority (AF17) | `2a2ee8306a7f45186355b548888d00e3df9fd22f20fd9fbe9435afa718874563` | yes |

## Property verdicts

| Property | Verdict | Helpers | Decisive evidence |
| --- | --- | --- | --- |
| frozen-before-child | ENFORCED | authority, catalog, supervisor, gate | run_authority.c:339 (STAGE precondition: exact identity, frozen==1, populated==0, nr_descendants==0 on the retained boundary fd); run_authority.c:343-346 (clone3 CLONE_INTO_CGROUP targets that retained fd; enabled() re-checked immediately before clone3); run_authority.c:351 (post-clone re-check frozen==1 && pidfd alive; failure rejects and closes the authority) |
| pre-registered-exact-c1 | ENFORCED | authority, supervisor, catalog, gate | run_authority.c:284-293 (sealed AC17 config pins per-unit boundary st_dev/st_ino, cwd identity, unique bindings and identities); run_authority.c:306-319 (REGISTER: identity(fds[0],device,inode) && cgroup(fds[0],1) frozen/empty/leaf, then F_DUPFD_CLOEXEC retention; parent dir retained); run_authority.c:399-402 (no unit operation until every configured unit is registered) |
| atomic-release-cancel-epoch | ENFORCED | authority, gate | run_authority.c:424-428 (ARM: epoch equality e->epoch==g->epoch, ticket_state==0, fresh 32-byte random ticket, ticket_end = request deadline); run_authority.c:430-442 (RELEASE: enabled, epoch equality, ticket_state==1, exact ticket, deadline<=ticket_end, now<ticket_end, frozen, alive; ticket_state=2/released=1 set BEFORE write_freeze('0')); run_authority.c:172-179 (close_authority: closed=1, epoch++, every ticket burned, freeze_all) and 104-108 (enabled() false once closed) |
| original-pidfd-waits | ENFORCED | authority, catalog, supervisor | run_authority.c:343-350 (CLONE_PIDFD; e->pidfd retained), 128-146 (state(): waitpid by the parent-of-record with EINTR retry; liveness via poll on pidfd), 436-440 and 464-487 (release wait and cleanup use the retained pidfd), 474 (kill via pidfd_send_signal); catalog_launcher.c:221-227 (CLONE_PIDFD retained), 90-109 (waitpid by parent-of-record + pidfd liveness), 231-243 (cleanup kills and waits on the retained pidfd); bootstrap.c:237-246 (CLONE_PARENT|CLONE_PIDFD; pidfd retained in the slot and transferred once at 305), 258-268 (death observed on retained pidfds, independent of Python reaping), 287-288 (authority/storage liveness on retained pidfds) |
| independent-watchdog | PARTIALLY_ENFORCED | supervisor, gate, authority | bootstrap.c:284-291 (10 ms loop: lease, generation-2s, parent pidfd, channel hangup checked without any Python request), 287-288 (BS17: authority death before terminal and storage death trigger cleanup); bootstrap.c:258-279 (cleanup: SIGKILL every issued helper by retained pidfd, wait for death, freeze each unit boundary, then freeze every watched workload boundary, all within min(generation, now+2s); unresolved -> exit 70); bootstrap.c:157-173 (terminal_fence: irreversible freeze of the watched set), 91-95 (enabled() combines deadline, lease, generation and parent liveness) |
| late-request-fenced | ENFORCED | supervisor, catalog, gate, authority | bootstrap.c:296-302 (every frame: sequence==previous+1, scope, reserved zero, until in (now, now+5s], until<=lease, until<=generation-2s; invalid -> cleanup, not drop), 210/236/251 (enabled() before and after clone; failure kills), 254-256 (activate: enabled before thaw and during the wait; failure -> cleanup refreezes), 300 (terminal mode accepts only kind 6); catalog_launcher.c:255-259 (same window checks; invalid -> cleanup), 228 (post-clone enabled/frozen/alive); run_authority.c:508-516 (window, epoch, sequence cap; invalid -> cleanup), 339/345/351 (STAGE), 425-432 (ARM/RELEASE deadlines bound by ticket_end), 436-441 (release wait bounded), 355/358 (STOP bounded by deadline) |
| unrelated-scope-isolation | ENFORCED | supervisor, catalog, gate, authority | bootstrap.c:70-90 (field/write_freeze use openat on retained fds only), 176-178 (parent opened read-only for identity comparison), 260 (kills only retained pidfds), 265-276 (freezes only retained unit/watched fds); catalog_launcher.c:63-69 (openat on g->cg only), 233 (kill via retained pidfd only), 184 (the only path-based open is the image file, which is copied and hashed); run_authority.c:76-96 (openat on retained fds), 120-125 (removal probe through the retained fd), 316/370-371 (parent opened read-only), 356-357 and 471-474 (cgroup.kill only on the registered boundary; pidfd kill), 311 (registration requires populated==0 and no descendants) |

**frozen-before-child** (ENFORCED): The decisive checks are the identity+frozen+empty+leaf predicate evaluated on the retained descriptor immediately before clone3 and the frozen re-check immediately after, inside single-threaded helpers that are the sole thaw writers of their own boundary. Two things are not visible from source: (a) that the kernel freezes a task cloned into a frozen cgroup before it executes any user-space instruction (the post-clone re-check reads cgroup.events, i.e. cgroup state, not per-task state); (b) exclusive write access to cgroup.freeze, which rests on Python C1 ownership (prbc.py:628-692 creates, freezes and retains the boundary before any insertion; prbc never writes '0'). Finding F-03 records the catalog's wider check-to-clone window.

**pre-registered-exact-c1** (ENFORCED): Boundaries are bound by sealed-config (st_dev, st_ino) identity, received only as descriptors, and retained; Stage is refused unless the exact retained descriptor still carries that identity and is frozen/empty/leaf. Identity is dev/ino plus retained fd, so a recreated directory cannot substitute. The native authority does not check that an ADVANCE'd boundary is in the supervisor watch inventory (finding F-02); that precondition is Python-only (affa_client.py:273-274 -> _watched 229-240; bootstrap.py:1075-1081 for the initial set).

**atomic-release-cancel-epoch** (ENFORCED): Validation, ticket consumption and the unfreeze write happen in one single-threaded transition; Cancel/expiry/ADVANCE advance the epoch and burn tickets in the same loop, so interleaving inside a helper is impossible; replayed or stale frames fail closed (cleanup or freeze) rather than being dropped. Caveat (finding F-01): the refreeze that accompanies a close may be skipped when the close deadline has already elapsed; the epoch advance itself is unconditional, so no new Release can follow.

**original-pidfd-waits** (ENFORCED): Every child is created with CLONE_PIDFD and its pidfd is retained by the creating helper; liveness and kill use only that pidfd; reaping is done by the parent-of-record (waitpid in authority/catalog; waitid(P_PIDFD) in Python for CLONE_PARENT supervisor children). No helper discovers PIDs or paths. The waitpid(pid) calls are PID-based but safe because the caller is the parent and the PID cannot be recycled before reaping.

**independent-watchdog** (PARTIALLY_ENFORCED): What is enforced: the supervisor polls parent pidfd, lease, generation and (BS17) authority/storage pidfds without Python involvement and on loss kills issued helpers first, observes death, then freezes unit and watched boundaries inside a 2 s budget. What is missing natively: (1) watchdog coverage equals the WATCH inventory, and the authority admits ADVANCE'd fresh-generation boundaries without any proof that the supervisor watches them (finding F-02; Python-only precondition affa_client.py:273-274); (2) terminal_fence freezes the watched set without first terminating the still-live authority (finding F-07; ordering is Python-side, bootstrap.py:853-862); (3) nothing guards the supervisor itself (a stopped supervisor fences nothing; only Python's prbc fallback remains) and freeze completion is a bounded best-effort observation.

**late-request-fenced** (ENFORCED): Each request carries an absolute monotonic end that must lie in (now, now+5 s], within lease and generation-2 s; helpers re-check before and after the irreversible act (clone or thaw) and undo by kill/refreeze on failure; out-of-sequence or replayed frames cause cleanup/freeze. Caveat: finding F-01 (authority refreeze skipped when the close deadline has elapsed) and F-05 (consumed Release reported REJECTED).

**unrelated-scope-isolation** (ENFORCED): All cgroup reads and writes go through openat on retained directory descriptors; kills go through retained pidfds or the registered boundary's own cgroup.kill; no helper enumerates PIDs, walks paths or accepts a caller-supplied cgroup name. Registration demands empty leaf boundaries, so cgroup-wide operations cannot reach foreign tasks. The sentinel observation in runtime-lane.md is Python-side empirical evidence, not native code.

## Findings (sorted by severity)

### F-01 [MEDIUM] Authority refreeze is skipped when the close deadline has already elapsed

`src/xverse/maestro/native/run_authority.c` line(s) 161 (freeze_all), 391, 517, 498. freeze_all() writes cgroup.freeze only while now_ns()<end; close_authority(g,until) at 517 and close_authority(g,g->deadline) at 391 use the just-processed request's own deadline as end. In the release-timeout case this is guaranteed to trigger: RELEASE consumes the ticket, writes '0' (435), then waits while enabled()&&now<ticket_end (436); the loop can only exit by exec completing or by now>=deadline, so on timeout close_authority(g,until) is called with end already passed, every freeze write is skipped, freeze_failed=1 and the reply is REJECTED(reason=PROTOCOL) without the freeze mask. Once closed, the lease-expiry path at 498 never retries. The thawed workload keeps running until Python reacts to REJECTED (affa_client.py:288/408-447 revoke -> SIGKILL -> supervisor cleanup) or the generation ends. The same skip can occur on a CANCEL that arrives with little remaining time, which is then acknowledged CANCELLED(reason=6) with a partial mask. Recommendation: Always issue the cgroup.freeze write regardless of end (as bootstrap.c:265/271 do) and bound only the frozen==1 wait; give close_authority an independent budget (min(generation, now+2s)) instead of the request deadline; report the mask and FREEZE_FAILED on REJECTED; let the closed loop retry pending freezes.

### F-02 [MEDIUM] ADVANCE admits a fresh-generation boundary with no proof it is in the supervisor watch inventory

`src/xverse/maestro/native/run_authority.c` line(s) 365-385 (advance_unit). advance_unit checks identity, frozen/empty/leaf, same parent and uniqueness, but the native authority cannot know whether bootstrap.c watches the new leaf; only affa_client.py:273-274 (_watched, 229-240) enforces that before sending. If that Python precondition is bypassed or regresses, a released workload of the advanced generation lies outside the supervisor's freeze set: on authority death the supervisor kills the authority (its only thaw writer) and freezes only watched leaves (bootstrap.c:270-276), so that workload stays running unfenced until Python C1 cleanup or generation end. Recommendation: Make the precondition native: have the supervisor's WATCH ACK return a token that ADVANCE must echo and the authority verify (or route ADVANCE descriptors through the supervisor), so the authority refuses unwatched boundaries without trusting the Python caller.

### F-03 [LOW] Frozen/empty check precedes the image copy; no re-check immediately before clone3

`src/xverse/maestro/native/catalog_launcher.c` line(s) 217-223. The frozen==1/populated==0/descendants==0 reads at 217-218 are evaluated before prepare_image() copies and hashes up to 8 MiB; enabled() at 219 checks only time, parent, socket and identity. Any thaw during the copy would let clone3 create the child into a running cgroup; the child could execute until the post-clone check at 228 fails and cleanup kills it. In the composed system no legitimate writer thaws an empty boundary (the gate needs populated==1), so this is a latent window rather than a reachable path. Recommendation: Run prepare_image() before the boundary predicate, or repeat the predicate directly before clone3.

### F-04 [LOW] ADVANCE strands every other unit's un-released generation; the next ARM closes the authority

`src/xverse/maestro/native/run_authority.c` line(s) 379, 411, 425, 431. e->epoch is fixed at INTENT (411); ADVANCE increments g->epoch (379). Afterwards ARM/RELEASE for any other unit's staged-but-unreleased generation fails e->epoch!=g->epoch (425/431), and because any rejected command runs close_authority (517) the whole run is closed. INTENT cannot be repeated (409: e->intent already set). Safe direction, but a single restart of one unit makes the remaining staged units unreleasable. Recommendation: Confirm this is the intended semantics; if not, bind the epoch to the ticket (ARM) rather than to the intent, or permit a re-INTENT under the new epoch.

### F-05 [LOW] A consumed Release that times out before exec completes is reported as REJECTED

`src/xverse/maestro/native/run_authority.c` line(s) 434-441, 517. After ticket consumption and the thaw write, the wait loop returns -1 when now reaches ticket_end before the exec pipe closes; main treats this like any rejection (close_authority + REJECTED/PROTOCOL). The reply cannot distinguish 'never released' from 'released, ran briefly, (maybe) refrozen'. Python handles it conservatively (revoke and SIGKILL), and the state flags are still queryable, but the native receipt misdescribes the transition. Combined with F-01 the refreeze in exactly this path is skipped. Recommendation: Return a distinct reason (e.g. RELEASE_TIMEOUT) with the state flags, and perform the refreeze with its own budget.

### F-06 [LOW] exec_closed flag conflates successful exec with death before exec; authority reports no wait status

`src/xverse/maestro/native/run_authority.c` line(s) 137-143 (also catalog_launcher.c:98-104). Bit 2 is set when the error pipe reaches EOF without an errno write. A child killed (SIGKILL/OOM) after thaw but before execveat also closes the pipe by exit, so RELEASE at 438 would reply RELEASED with the 'executed' bit even though no workload instruction ran. catalog_launcher additionally exports the wait status (status<<32) so Python can see WIFSIGNALED; run_authority exports no status, so the evidence cannot disambiguate. Recommendation: Export the reaped wait status in the authority's state word, or write a success marker from the child only immediately before execveat cannot be done (exec replaces the image), so use the status.

### F-07 [LOW] terminal_fence freezes the watched set without first terminating the still-live authority

`src/xverse/maestro/native/bootstrap.c` line(s) 157-173 (terminal_fence). cleanup() (258-279) kills issued helpers before freezing, so no thaw writer survives the fence; terminal_fence() does not: it requires only that an authority was born (159) and freezes the watched leaves while the authority may still be alive and, after the transition, its death is tolerated (287). A RELEASE serviced by a live authority after terminal entry would thaw an 'irreversibly' fenced leaf. The ordering is enforced only in Python (bootstrap.py:853-862 requires a CANCELLED receipt or observed authority death, and the exchange lock serializes CANCEL and RELEASE), not natively. Recommendation: Require !alive(authority pidfd) or kill the authority and observe death inside terminal_fence before the freeze loop, mirroring cleanup().

### F-08 [NOTE] clone3 exit_signal=0 relies on CLONE_PARENT inheritance of the supervisor's SIGCHLD

`src/xverse/maestro/native/bootstrap.c` line(s) 237. clone3 rejects CLONE_PARENT with a nonzero exit_signal, and with CLONE_PARENT the child inherits the caller's exit_signal. Python's ordinary waitid(P_PIDFD) without __WALL works only because the supervisor's own exit_signal is SIGCHLD. Removing CLONE_PARENT without setting exit_signal would silently make the children un-waitable (ECHILD). Recommendation: Record the dependency in a comment and keep CLONE_PARENT and exit_signal coupled.

### F-09 [NOTE] Supervisor-born helpers have no exec error pipe

`src/xverse/maestro/native/bootstrap.c` line(s) 243. Unlike catalog_launcher and run_authority, an execveat failure is only visible as exit code 127, indistinguishable from a helper that exited 127 after exec. Python observes the helper's death and fails closed, so no fence impact. Recommendation: Optional: add the same errno pipe for diagnosability.

### F-10 [NOTE] Slot descriptors duplicated before the remaining birth validations

`src/xverse/maestro/native/bootstrap.c` line(s) 219-236. c->cg/c->unit are retained at 219; a later pre-clone failure (role-2 config at 226-228, getrandom/enabled at 236) returns -1 leaving an open pair in a slot with pid==0 that cleanup ignores. Harmless because every birth failure exits via cleanup. Recommendation: Duplicate after all validations, or close on the failure paths.

### F-11 [NOTE] Two separate now_ns() samples in the deadline window test

`src/xverse/maestro/native/bootstrap.c` line(s) 298, 309, 316 (also catalog_launcher.c:258). until>now_ns()&&until-now_ns()<=5*NS samples the clock twice; if the clock passes until between the calls the unsigned subtraction wraps, the frame is rejected and cleanup runs. Conservative outcome only. Recommendation: Use the single now sample already taken at 285/296.

### F-12 [NOTE] recvmsg EINTR mapped to CONTROL failure instead of retry

`src/xverse/maestro/native/lease_guard.c` line(s) 215-216. Other helpers retry on EINTR; the gate freezes and exits. With MSG_DONTWAIT and no signal handlers EINTR is practically unreachable, and the outcome is conservative. Recommendation: Treat EINTR like EAGAIN for consistency.

### F-13 [NOTE] Unchecked returns are confined to best-effort terminal actions

`src/xverse/maestro/native/bootstrap.c; catalog_launcher.c; lease_guard.c` line(s) bootstrap.c:260; catalog_launcher.c:233, 263, 267; lease_guard.c:180, 199, 205. pidfd_send_signal and reply sends in cleanup/freeze paths ignore their result; the subsequent bounded observation (pidfd readable, reaped, frozen==1) supplies the verdict and unresolved exits with 70. No decision-bearing syscall return is unchecked; run_authority.c:474 checks the kill and tolerates only ESRCH. Recommendation: None required.

### F-14 [NOTE] Read end of the exec pipe retained after a failed clone3

`src/xverse/maestro/native/run_authority.c` line(s) 341-349. On clone3 failure errors[0] stays open as e->errorfd; attempted=1 prevents repetition and the rejection closes the authority, so at most one descriptor is leaked per unit. Recommendation: Close errors[0] on the child<0 path.

### F-15 [NOTE] A birth whose ACK never reaches Python leaves a zombie that only Python can reap

`src/xverse/maestro/native/bootstrap.c` line(s) 238-251, 283, 305. If the post-clone check (251) or respond(17) fails, cleanup kills the child, but its parent-of-record is Python, which never received the pidfd; it stays a zombie until the Python process exits (bootstrap.py:902-923 recovers only late-delivered ACKs). The cgroup becomes empty at exit, so no fence impact. Recommendation: Document as an accepted resource effect of the CLONE_PARENT design.

### F-16 [NOTE] Any rejected command irreversibly closes the run; the 8193rd frame triggers full cleanup

`src/xverse/maestro/native/run_authority.c` line(s) 510, 517. A single well-formed but refused request (e.g. a QUERY for an unknown generation) advances the epoch and freezes everything; g->sequence<8192 in the validity test turns the 8193rd request into cleanup. Fail-closed, but liveness is fragile. Recommendation: Confirm intended; consider distinguishing benign observation rejections from authority-closing ones.

### Categories with no finding

- integer parsing without bounds: None found: decimal() bounds length and value (bootstrap.c:53, catalog_launcher.c:51-56, lease_guard.c:70-81, run_authority.c:59); field() guards value>(UINT64_MAX-9)/10 before multiplying (bootstrap.c:76, catalog_launcher.c:77, run_authority.c:82) and lease_guard.c:148-151 uses the overflow-safe decimal(); all wire integers are fixed-width get32/get64; string tables check length, terminator and remaining size (catalog_launcher.c:145-150, run_authority.c:255-260, bootstrap.c:140-147).
- descriptor leaks across fork/exec: None found: every retained descriptor is CLOEXEC (F_DUPFD_CLOEXEC, O_CLOEXEC, MSG_CMSG_CLOEXEC, CLONE_PIDFD, MFD_CLOEXEC, pipe2 O_CLOEXEC) and every child calls close_range(3, UINT_MAX, CLOSE_RANGE_CLOEXEC) before selectively clearing CLOEXEC on the admitted descriptors (bootstrap.c:240-241: only channel/input and, for roles 1-2, the unit boundary; catalog_launcher.c:207; run_authority.c:331); stdio is redirected to /dev/null; environment is empty for supervisor children.
- reuse of a one-use ticket: None found: run_authority ticket_state 0->1->2 (424-434) with released/retired guards and burns on close/ADVANCE/RETIRE (176, 381, 456); lease_guard single slot, ticket_state 0->1->2 (325, 335), nonce zeroed on consumption and all bytes zeroed on freeze (176, 336).
- lease/epoch comparisons that could wrap or be bypassed: None found: epoch headroom checked at admission (run_authority.c:295; lease_guard.c:241), ADVANCE guard g->epoch>=UINT64_MAX-1 (368), close_authority guards UINT64_MAX (173); sequence capped (run_authority.c:510; lease_guard.c:383); every subtraction is preceded by the corresponding ordering check (bootstrap.c:128, 298; run_authority.c:280-281, 396, 512; lease_guard.c:283-285, 401-402); monotonic clock failure (0) is treated as expiry everywhere.
- late or replayed request reaching a child (native level): None found beyond F-01/F-05: sequence must be exactly previous+1 and the request epoch must equal the live epoch; replays and stale frames cause cleanup/freeze, and every thaw requires a pid/token or ticket that exists only after the corresponding native ACK.

## Counts

Verdicts: {'ENFORCED': 6, 'PARTIALLY_ENFORCED': 1, 'NOT_FOUND': 0, 'DELEGATED_TO_PYTHON': 0}. Severities: {'HIGH': 0, 'MEDIUM': 2, 'LOW': 5, 'NOTE': 9}.

## Limits

- Kernel behaviour was not verified: that a task cloned with CLONE_INTO_CGROUP into a frozen cgroup is trapped before executing any user-space instruction; how cgroup.events 'frozen' accounts for a just-forked task; that cgroup v2 kernfs (st_dev, st_ino) identity is not recycled while a descriptor is retained; that writes through a retained cgroup.freeze descriptor fail after rmdir; execveat(AT_EMPTY_PATH) of a CLOEXEC memfd (ELF only; scripts would fail after exec); CLONE_PARENT exit_signal inheritance; cgroup.kill semantics.
- Build and deployment were not verified: which preprocessor variants are deployed (RUN_BOOTSTRAP for BS17; MAESTRO_RELEASE_GATE=1 and optionally MAESTRO_BOUNDARY_ACK=1 for RG06; the default LG05/BS10 builds behave differently), compiler flags (tests pass -std=c11 -O2 -Wall -Wextra -Werror -Wconversion -Wshadow but nothing was compiled here), OpenSSL version, and the hash pins of the produced binaries.
- Nothing was executed: no test suite, no compilation, no kernel probe. All timing statements (10 ms poll, 2 s cleanup budget, <=5 s leases, <=1 s gate reserve) are source constants, not measured bounds; uninterruptible or stalled tasks, scheduler starvation, or a stopped supervisor are outside what the source can bound.
- Exclusive ownership assumptions were not verified: that no other process holds or writes the boundary cgroups, that the Python parent is the only peer on each SEQPACKET channel (credentials are checked, but the peer's own correctness is assumed), seccomp/capabilities, and that the storage (role 3) and controller (role 5) Python workers do not acquire thaw capability; those modules were not reviewed.
- Python callers were read only to locate delegated checks (affa_client.py, affa_protocol.py, owner.py, bootstrap.py, launcher.py, prbc.py, fence.py, child.py); they were not independently reviewed for correctness, and the nine runtime case receipts cited by runtime_admission.py were neither inspected nor reproduced.
- This review did not perform the thesis repository Git freshness check or read the canonical dynamic note: the task is a read-only review inside a different repository and the brief forbids state-changing git commands; no thesis content was changed.

## Authority limits

activation_approved: false; m1_admission: false; acceptance: false.

This review is an independent source reading of frozen bytes and neither activates the lane nor admits M1 nor accepts anything.
