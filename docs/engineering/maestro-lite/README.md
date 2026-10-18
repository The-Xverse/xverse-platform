# Maestro Lite lifecycle component candidates

Status: **implementation candidate; U1/U6 plus partial U2/U3/U4/U5/U7; not accepted; no runtime admission**.
Owning baseline: `c2997c0f810d117cf45b2e34a4011b3ba7219494`.
Authoritative feature: `/home/jefferson/distributed_safety_critical_thesis/specs/024-maestro-lite-lifecycle/`.

## Durable start/probe evidence candidate (OUTCOMES12)

Every ProcessReadiness Query now requires a bounded acknowledgement from the
original isolated persistence worker before it can satisfy readiness. The worker
appends actual M3 records through public FileEvidenceJournal APIs, projects their
exact public hashes, appends accepted Argus annotations and calls flush_buffer.
The first observed running sample records one normal start outcome and a separate
probe observation, with started/probe/ready annotations. Pending exec records a
failed probe without invented start credit. Subsequent samples record health.
Combined-graph predecessor references come from the worker's own latest acknowledged
fresh probes. Original intents, known M3 history and mirrored events are rechecked.

The coordinator performs no storage I/O in this path. It accepts only its exact
current original observation/handle and validates the closed public reply against
claim, run/unit/generation/session, actions, clocks, source references, dependencies,
causation and global ordinals. LifecycleReceipt holds immutable public bytes and
never transfers execution authority or claims complete lifecycle coverage.
Storage failure, hung writes or lost acknowledgements close starts; retained normal
records remain factual partial evidence and C1 cleanup stays independent.

See ADR-ML3-OUTCOMES-0001.md, unit-specification-outcomes12.md,
outcomes-expected.json, review-outcomes12.md and evidence/outcomes12/.
The inherited private framing still caps a session at 128 requests; full scheduling
admission must budget requests and events. Automatic tick/health scheduling, missing-
observation failure/disposition records, normal stop/cleanup and reverse teardown,
restart/recovery, U7 dual coverage/U8, full bootstrap/admission/M1/runtime validation,
independent full review and acceptance remain open. No factory or experiment run.

## Process readiness and dependency candidate (PROVIDER11)

ProcessReadiness composes the original ReleaseOwner with its actual isolated
PersistenceClient, already staged CatalogLauncher handles and one ProbePolicy
per prepared unit. It supports only the exact catalog observe condition `running`:
process existence after observed exec, not application readiness. Plans declaring
other conditions reject. Legacy synchronous-storage owners are not admitted by
this facade; the existing primitive owner API remains compatible.

Call bind(launcher, full_handle) for each original staged resource, then
start(unit_id, original_boundary, original_gate, original_deadline). Prerequisites
come from ancestors in the combined XDL projection, including step dependencies.
Already released units are probed before new work. A private active-operation
guard re-probes all prerequisites before Arm and again immediately before Release;
all replies must match current generation/handle/session and remain fresh together.
Release is single-attempt and never itself ready. Up to three bounded actual
queries can satisfy the declared running condition. Failure/unknown/expiry cancels
further starts; original C1 remains responsible for actual teardown.

check_health(deadline, force=False) samples due units; next_health_deadline exposes
the earliest next cadence. The caller must drive sampling. No autonomous health/
tick scheduler, continuous health guarantee, application probe or full lifecycle
provider compatibility is established. Observations are immutable historical facts,
never transferable release authority. Exposed cached observations become non-ready
when the original latch closes. Bootstrap finding 14 now rejects a changed public
session alias before native dispatch.

See ADR-ML3-PROVIDER-0001.md, unit-specification-provider11.md, provider-expected.json,
review-provider11.md, verify-provider11.py and evidence/provider11/. Source/wheel
verification is component evidence only. Initial-supervisor admission and durable
bootstrap permits, exact environment/dependency admission, normal M3 outcomes,
autonomous scheduling, reverse teardown/restart/recovery, U7/U8, full M1/runtime
cases, independent full review and acceptance remain open. No factory run, main
merge, scientific result or canonical-note edit is implied.

## Supervised helper bootstrap candidate (BOOTSTRAP10)

The externally admitted runner supplies one genuine native bootstrap supervisor,
its private seqpacket socket, sealed input and three sealed helper images. Runtime
BootstrapSession methods create persistence, catalog-launcher and C1-bound gate
helpers through bounded native requests, without coordinator Popen. Each helper
is born frozen in an original, separately registered helper C1. Its actual clone
pidfd and original direct-parent wait authority are retained before a separate
one-use helper activation. Helper activation never thaws the workload C1.

Build native/bootstrap.c explicitly with C11 and OpenSSL 3 libcrypto; installation
and imports never build or execute it. BC10 binds original run/lifecycle/approval/
environment/supervisor pin and three helper image/argv0 pins. Native initialization
independently verifies image seals and hashes. seal_helper_image, input sealing,
initial native Popen, root registration, interpreter/site/library/environment
admission and exclusive original-parent wait ownership belong to the external
supervised admission path. Approval fields are not an authentication service.

BS10 birth/activation share one original deadline. Cancel bypasses the normal lock;
native expiry/owner loss/EOF prevents further helper insertion, kills exact helper
pidfds and refreezes retained workload C1 after helper exit. Original Python C1
separately terminates/observes/releases workload and helper trees. BootstrapChild
is an original native-issued capability, not a synthetic Popen; client and bootstrap
drain share one actual wait result. Legacy genuine-Popen clients remain supported.
Late genuine birth ACKs retain cleanup-only pidfds. An unrecoverable birth ACK stays
unresolved; no PID/name recovery or broad wait is attempted. External controller
supervision remains required across that gap and arbitrary kernel stalls.

Use BootstrapAdmission/encode_bootstrap only with externally approved, hash-bound
facts. The original C1 manager/latch/run/deadline/approval must match registration.
Pre-register a separate empty frozen helper BoundaryDescriptor before each request.
The fixed role adapters are persistence(config, helper, deadline), catalog(owner,
recipe, helper, deadline), and gate(owner, unit, helper, deadline, lease_ns=...).
Keep request deadlines and gate lease inside the current root lease. Renew before
expiry, within the original generation; renewal cannot revive an expired issuer.
After cancellation, drain typed clients and bootstrap with the original pidfds,
then independently verify C1 cleanup. Preserve unresolved wait/birth/freeze facts.

See ADR-ML3-BOOTSTRAP-0001.md, unit-specification-bootstrap10.md, bootstrap-expected.json,
the separate review, verify-bootstrap10.py and evidence/bootstrap10/. Launcher
finding 10 is corrected: recipe construction observes C1 and is not globally pure.
Full original-owner/guard-loss/M1, provider facade/readiness/dependency scheduling,
reverse lifecycle/recovery/normal outcomes, U7/U8, admission/source gates and all
nine runtime cases remain open. No readiness, acceptance or main merge is implied.

## Catalog launcher candidate (LAUNCHER9)

The successor composes real process-kind XDL/catalog actions, genuine M3/Argus
intent, a native born-frozen child and the original one-use Release gate. Python
retains C1 and an original issuing registry; the native helper copies and hashes
the selected regular ELF into a sealed image, pins the declared cwd and uses only
explicit argv/environment. LC09 authenticates each peer and exact recipe bytes,
sequence, deadline, retained cgroup FD and returned child pidfd. A full issued
OwnedResourceHandle is usable only through its live original registry.

Build the packaged catalog_launcher.c explicitly with OpenSSL 3 libcrypto:
`cc -std=c11 -O2 -Wall -Wextra -Werror catalog_launcher.c -lcrypto -o catalog-launcher`.
The optional RG06 build additionally requires `-DMAESTRO_BOUNDARY_ACK=1`; it returns
its actual cgroup FD during READY. Default RG06/LG05 behavior remains unchanged.
Source and binary pins, explicit artifact/environment/FD admission and trusted
helper bootstrap remain required; imports/installations never build/start helpers.

Before Release, the child stub and workload remain frozen. After Release, an exec
error pipe and original child pidfd distinguish pending exec, alive-after-pipe-EOF,
failed exec and reaped leader. These observations do not establish lifecycle
readiness or a successful normal outcome. Direct-child reap and C1 descendant
kill/empty/release remain separate factual checks. Cancel never waits for Stage's
lock. Closed or removed original boundaries cannot be used for late birth.

See ADR-ML3-LAUNCHER-0001.md, unit-specification-launcher9.md, review-launcher9.md
and evidence/launcher9/. verify-launcher9.py verifies installed source identity,
full/copy regressions and original helper/root receipts. Whole bootstrap/caller
bounds, dependency admission, provider facade/current-generation readiness,
reverse teardown, restart/recovery, full normal M3/evidence/coverage/collection,
independent full review and all nine runtime cases remain open. Full Lite phase 3
is partial; this candidate neither updates accepted main nor admits experiments.

## Native Release gate successor

`ML3-RELEASEGATE6-2026-10-18-v1` extends the packaged native source with an explicit
`-DMAESTRO_RELEASE_GATE=1` build variant. Default LG05 stays freeze-only. The RG06
variant uses a distinct 256-byte protocol and original creation epoch; it owns a
single ticket slot, validates original-parent credentials, exact scope, operation,
three acknowledgement digests, fixed TTL and private nonce, consumes once and
unfreezes the original retained cgroup control FD. Cancel/expiry advances the epoch,
burns the ticket and observes refreeze. Python `xverse.maestro.fence` is an inert
strict codec; importing it performs no bootstrap, clock read or execution.

The trusted original caller must verify actual durable M3, Argus public append+flush
and supervisor Stage acknowledgements. Hash fields cannot prove their truth. The
native gate does not create children, issue ordinary handles or gain C1. A Release
ACK means unfreeze was observed, not lifecycle readiness or a successful M3 outcome.
Actual kernel tests exercise both orderings, replay/TTL denial and a delayed gate
after C1-confirmed removal, including rejection through a retained old freeze FD.
Kernel I/O/scheduling stalls and guard/original-owner loss still require full outer
integration; the nine ML3 runtime cases and complete M1 proof remain pending.
See `ADR-ML3-RELEASEGATE-0001.md`, `unit-specification-releasegate6.md`,
`review-releasegate6.md` and `evidence/releasegate6/`. Pin source, build mode and
executable for any future admitted bootstrap; no runtime bootstrap facade is provided.

## Independent freeze-only lease guard successor

`ML3-LEASEGUARD5-2026-10-18-v1` continues linearly from containment commit
`de6be649b8a633b8f92972b249b03271d11810ea`. The wheel now carries native C11
source `xverse/maestro/native/lease_guard.c`. Build it explicitly with
`cc -std=c11 -O2 -Wall -Wextra -Werror lease_guard.c -o lease-guard`; importing
or installing the Python package does not compile or start it. There is no new
public Python bootstrap or lifecycle facade. The native entry and fixed 64-byte
protocol are defined in `unit-specification-leaseguard5.md`; build/hash-admit the
exact binary before any future owner bootstrap.

The independent process watches its original supervisor pidfd, a private
credential-checked Unix socket and a fixed monotonic lease. Expiry, supervisor
death, channel loss, malformed messages and Cancel request freeze of the exact
retained cgroup and observe the kernel frozen event. Renewal is bounded, scoped,
contiguous and cannot revive an expired lease. It never thaws, spawns workloads,
kills, deletes or obtains C1 cleanup authority. The original external holder
retains C1. Freeze alone is neither termination nor cleanup success.

This is a partial helper component, not the M1 Release/cancel fence. A stopped or
killed guard cannot enforce a lease, and kernel I/O can stall. Real tests expose
those limits explicitly; original-owner loss/guard-loss integration and stale
thaw prevention remain open. All process readiness flags stay false. See the
lease-guard ADR, unit specification, separate review and `evidence/leaseguard5/`.
The older sections below retain the exact earlier component context.

## U4 containment successor

`ML3-CONTAINMENT4-2026-10-18-v4` adds `xverse.maestro.prbc` in
`/home/jefferson/xverse-platform-worktrees/maestro-lite-containment-20261018`.
It creates fresh frozen Linux cgroup-v2 boundaries below an explicit exclusive parent,
retains original directory identity and private C1/reservation provenance, observes
membership independently of leader survival, and confirms exact kill/empty/removal.
Removal is verified through the retained identity's kernel controls and private name;
kernfs link counts are not the removal predicate. Original creation epochs survive
Cancel; lost/copied/forked registries cannot adopt a boundary. The CP-02 reservation
branch is read-only until verified empty removal and never substitutes for lost C1.

Supply explicit `BoundaryAdmission`, `BoundaryLimits(operation_seconds=...)` and
the original CancellationLatch. Admission facts are not authenticated operator approval.
An immutable original generation deadline (within the proposed D3 envelope) is distinct
from each operation's ≤5 s budget. Expiry or unknown observation retains unresolved
accounting. The backend supplies no child insertion, thaw, provider handle, M3 outcome
or workload callback. The closed create_frozen option schema accepts no keywords.
`ready_for_execution` stays false; only factual boundary cleanup may be reported.

Fixed C component tests exercise clone3 into a frozen boundary, leader death with a
live descendant, scoped force with an untouched sentinel, and rejected insertion
through a deleted retained FD. They are not an admitted launcher or full ML3 runtime
proof. Actual M1/AFFA fencing, supervisor-loss lease, bounded helper creation,
authenticated original-owner/run/store binding, broker/proxy/FixtureBoundaryOps,
U5 orchestration and evidence/coverage remain pending. See the containment ADR,
unit specification, review and `evidence/containment4/` for exact verification.

Stable increments are committed after verification under the author's 18 October
instruction. Prior PREP1/U2/U3 snapshots are committed on separate candidate branches;
their immutable manifests remain valid. A commit does not imply acceptance or main merge.

## U3 successor

Current overlay: `ML3-SUPERVISION3-2026-10-18-v3` in
`/home/jefferson/xverse-platform-worktrees/maestro-lite-supervision-20261018`.
The preceding PREP1/U2 worktrees and their hash-bound evidence remain unchanged.
`xverse.maestro.supervisor` supplies an original-parent Linux direct-child monitor:
strict finite host limits, irreversible independent cancellation, retained pidfd,
TERM/KILL escalation, nonblocking exact-child reaping and immutable observations.
It invokes no provider, tick, persistence, output-reader or Popen wait/poll callback.
Registration snapshots limits and freezes deadlines. Uncertain observation closes
the latch and retains identity; copied/forked holders cannot use the registry.

The original trusted owner must supply the actual Popen child before operation
dispatch and prevent concurrent reaping. Registration is not authenticated bootstrap
approval. The component creates no child and does not bound helper creation or its
own registration. It proves no descendant containment, C1, launcher fence or
supervisor-loss lease. A userspace deadline guard is not atomic kernel enforcement.
Every observation retains `cleanup_complete=False` and `ready_for_execution=False`;
exit/reaping is direct-worker evidence only. Cached uncertainty stays uncertainty.
See `ADR-ML3-SUPERVISION-0001.md`, `unit-specification-supervision3.md`,
`review-supervision3.md` and the distinct `evidence/supervision3/` bundle.

The sections below retain the earlier component context. Full lifecycle APIs,
U4 exact containment/M1/C1, independent helper supervision, U5 orchestration,
Argus coverage, restart, actual-runtime admission and acceptance remain pending.

## U2 successor

The successor at `/home/jefferson/xverse-platform-worktrees/maestro-lite-admission-20261018`
preserves the PREP1 worktree and adds `xverse.maestro.admission`. Use
`validate_permits` for pure exact-set validation and `PermitSession` only for
coordinator-side intent persistence through the actual M3 FileEvidenceJournal.
Every unit is validated before the session is returned; validity and source bindings
are checked again for all initial units at the first claim, then for the selected unit
at each subsequent use. Expiry of an already-used start permission does not widen or
invalidate a different unit's fresh permit. A persistence/read failure permanently
closes the original session's claims; fresh permit identities cannot adopt unresolved
prior intents in a selected scope. Generation zero is supported here; resource restart
requires confirmed-release evidence and the later coordinator implementation.

`PermitApproval` represents private input facts from the future trusted admission
owner. The module cannot authenticate human approval or confer authority from those
fields. A returned `IntentReceipt` confirms a journal operation and always retains
`ready_for_execution=False`; it is neither a permit, an AFFA ticket nor lifecycle success.
The module provides no provider or workload callback.

The additive M3 `claim_intent` checks history and persists one intent under the same
thread/process locks. A small identity marker in the existing private lock file binds
the journal, lock and parent plus the retained byte prefix and minimum sequence.
Journal loss, replacement, truncation, malformed history and uncertain marker publication
cannot silently reset consumed permits. The marker contains no permit database.
These are journal-scoped guarantees for cooperating claim users, not a security boundary
against an actor able to rewrite both private files. Existing ordinary M3 append/read and
controller APIs retain their behavior; legacy check-then-append clients gain no implicit
cross-process atomicity guarantee.

Recognized exclusions are `legacy-execution` and closed `operation:`, `provider:` and
`realization:` values described in the code/design. Unknown or conflicting exclusions
reject. Exact approval bindings cover run/unit/execution/generation, full prepared value,
M3 plan, provider artifact/environment, artifact digests and private permit content.
Approval-owner binding to the actual admitted run/store, file rehash at launch, bootstrap,
C1 containment, deadlines, Argus flush and ticket issuance remain pending G1/G3/G4/G5 work.

See `ADR-ML3-ADMISSION-0001.md`, `unit-specification-admission2.md`,
`review-admission2.md` and `evidence/admission2/`. Earlier PREP1 records copied below
remain historical evidence for their exact subject; current U2 evidence is separate.
Current revision 2 evidence is under `evidence/admission2/revision2/`; its predecessor
archive retains the exact earlier passing source, tests and review before the last repairs.

This increment implements the pure preparation and clock-validation parts of Phase 3.
It consumes an actual accepted `ExperimentPlanResult`, recompiles the immutable normalized
resources and compares the complete semantic plan, derives actual M3 catalog plans, and
projects a combined lifecycle graph. A rehashed caller modification is still rejected
when it does not reproduce the resources. No Scenario command becomes executable.

```python
from xverse.maestro import Limits, ProviderDescriptor, prepare

prepared = prepare(
    compiler_result,
    normalized_resources,
    provider_descriptors=provider_pins,
    limits=Limits(horizon_ticks=100),
)
assert prepared.ready_for_execution is False
```

The horizon in this example is an engineering input, not an AEB protocol threshold.
Provider descriptors require a closed provider ID/kind, explicit environment identity
and a SHA-256 artifact pin. Preparation never opens or verifies an executable artifact;
the pin is declared input identity, not artifact availability or provider admission.

## Implemented boundary

- One executable unit per bound component instance; unbound logical nodes remain containers.
- Exact catalog/provider/environment/artifact matching, duplicate and ambiguous selection rejection.
- Typed full resource/collection/element identities; source pointers resolve original XDL arrays.
- Start/Release/probe/readiness/completion joins, flow-owner readiness dependencies, explicit
  step completion dependencies, reverse teardown and impossible-window rejection.
- Deterministic, immutable preparation bytes and a SHA-256 digest. The increment uses its own
  `xverse.maestro.preparation.increment1` domain; it does not impersonate the complete v2
  lifecycle digest, whose admission, evidence obligations and helper pins are not implemented.
- Static eligible-step queries. Caller-supplied completed step IDs are scheduling input only;
  this function does not establish live readiness, health, ownership or permit validity.
- Integer-only simulation progression with zero/pauses, explicit horizon and rewind rejection;
  separate session-qualified host deadlines and UTC arithmetic. No host clock is read.

Finite proposed caps are 16 units, 128 steps, 128 distinct resource dependency pairs,
16,384 combined edges and a 10,000-tick horizon. The combined-edge cap bounds expansion of
phase and step dependencies; it is distinct from the resource-pair cap. Callers can narrow
these caps but cannot enlarge them. No measured timing or physical simulation fidelity is claimed.

## Pending boundary

There is no `start`, `stop`, `restart`, `reconcile`, `collect` or lifecycle-assessment API in
this increment. Actual process/simulated-provider orchestration, authenticated run/store
admission, descriptor/C1 containment, complete watchdogs, current-generation readiness, emergency
teardown, Argus lifecycle obligations and offline coverage remain pending. A graph node
named `ready` describes a required predecessor; its existence is not evidence of readiness.

All 24 ML-SR requirements remain in scope. ML-SR-001–004 and ML-SR-015 receive partial
code/test evidence; ML-SR-023 receives additive packaging/regression evidence only. No
REF-002 parent is semantically validated or closed. See the thesis continuation record
and `review-increment1.md`; the complete P3 task list stays open.

The historical rejected candidate's false-success facade and process helper are excluded.
No historic admission, expired queue window, provider pin or fixture grants execution authority.
Any future factory run must originate in `/home/jefferson/x-verse_fabric` through
`automation/factory_start.py` with fresh controls, external supervision and the current
Sol/high/no-fallback model policy. Direct implementation does not create a factory run.

## Verification and maintenance

Run feature tests from this owning checkout with current source imports:

```bash
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/thesis_lite/maestro -q
python -m ruff check src/xverse/maestro tests/thesis_lite/maestro
```

For wheel verification use a fresh wheel build and an isolated environment with empty
PYTHONPATH, outside the checkout. Compare installed module bytes with source before
running copied tests. Hatchling force-includes `xverse` subpackages, so an editable
installation can retain a stale copy after source edits; it is insufficient by itself.
Existing XDL/M3/Argus consumers must pass from the exact source/wheel candidate.

Evidence logs and the final verification record identify actual checks and failures.
The initial full-suite environment failures and earlier review failures are retained.
No principal experiment, thesis result, PDF/DOCX generation, main update or external
publication occurs in this increment. Acceptance and merge require explicit author action.

## Original-owner integration candidate (OWNER7)

The isolated successor composes real generation-one PermitSession claims, actual
M3 public projection hashes, accepted Argus append_event/flush_buffer, original C1
frozen membership and credential-checked native RG06 Arm/Release. Default generation
zero admission remains compatible. Full XDL unit references remain logical data in
BoundaryDescriptor, never cgroup paths. See ADR-ML3-OWNER-0001.md,
unit-specification-owner7.md, review-owner7.md and evidence/owner7/.

The private claim retains its original host deadline; later calls cannot extend
that operation. The public evidence source hash covers the actual redacted M3
record using accepted canonical JSON bytes. Copied/terminal/replaced claims,
persistence failures, late acknowledgements and cancellation cannot register or
revive launch authority. Public ReleaseObservation always reports readiness false.

Trusted bootstrap still supplies the actual native child/socket/artifact pin and
exclusive wait ownership. Synchronous M3/Argus/kernel operations are not whole-call
bounded: disposable I/O workers and independently supervised bootstrap/launcher
remain required. No ordinary handles, full readiness, reverse lifecycle teardown,
restart/recovery, complete evidence assessment/collection or nine-case runtime
acceptance is supplied. Prior component evidence is preserved; main is unchanged.
Use verify-owner7.py with a newly built installed wheel, never stale editable imports.

## Single-process persistence candidate (PERSISTENCE8)

PersistenceClient and persistence_worker isolate the actual original M3/Argus owner
in one child process. ReleaseOwner.from_persistence keeps C1, frozen Stage and RG06
in the original supervisor. The RPC path performs no supervisor-side storage I/O.
Actual RegisterIntent and journal revalidation acknowledgements, original receipt
identity and the original deadline gate Release. Storage timeout/cancellation closes
starts and permits exact pidfd termination/reaping; it creates no replacement writer.
Healthy cancellation still permits bounded Abort. Abort records failure, not complete
lifecycle evidence. The local owner API remains available for regression comparison.

The private sealed input contains XDL declarations and original pins, not executable
code/callbacks. Its scope does not authenticate a helper executable/environment or
operator approval. Trusted helper creation, artifact/FD admission and exclusive wait
ownership remain bootstrap obligations. Parent-death signaling is a best-effort
creating-thread mechanism, not full owner-loss/kernel-stall proof. Kernel/scheduling
stalls can leave explicit unresolved retained ownership. The bounded RPC tests cover
interruptible storage stalls, not production real-time guarantees.

See ADR-ML3-PERSISTENCE-0001.md, unit-specification-persistence8.md, separate review
and evidence/persistence8/. verify-persistence8.py checks the exact installed wheel,
full platform suite, copied consumers, all recorded helper/peer groups and partial
trace. Full bootstrap/launcher, ordinary handles/readiness, reverse lifecycle teardown,
restart/recovery, complete U7/U8 and the nine actual-runtime cases remain open.

BOOTSTRAP10 v3 requires own-process KCMP_FILE for exact pidfd open-file-description
checks. The registered root/child keeps a distinct private original duplicate; all
signals/waits/duplicates use it. Inode equality is not a pidfd identity check on
Linux 6.8. Comparison denial/unsupported hosts reject admission without fallback.
This bundle tests x86-64; other architecture/environment admission remains external.

Reverse unit teardown increment 13 (partial, not accepted):
[ADR](ADR-ML3-TEARDOWN-0001.md), [unit contract](unit-specification-teardown13.md),
[tasks](tasks-teardown13.md), [read-only findings](review-teardown13.md), and
[evidence](evidence/teardown13/). Original C1 termination now retains an observed
empty frozen boundary for a separate original release. ReverseTeardown serializes
with the original owner/facade, closes starts locally, and records normal stop and
cleanup intent/outcome through the original isolated M3/Argus writer. Actual native
leader reaping, C1 empty/release facts and missing normal evidence remain separate.
Storage/identity faults use original cleanup-only authority under the original end;
manager conflicts report unknown facts without blocking. Same-controller matching
stop calls return retained facts. Full helper/global cancellation, automatic health/
tick scheduling, recovery, coverage/collection and admission/runtime remain pending.
All seven full P3 tasks, 24 ML-SR, 18 allocation-only source parents, 30 scenario
pairs/90 declared endpoints and nine full runtime cases remain open. No factory
run, main merge, canonical-note edit, scientific protocol or result change.
