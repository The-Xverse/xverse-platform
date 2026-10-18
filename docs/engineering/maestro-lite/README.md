# Maestro Lite lifecycle component candidates

Status: **implementation candidate; U1/U6 plus partial U2/U3/U4; not accepted; no runtime admission**.
Owning baseline: `c2997c0f810d117cf45b2e34a4011b3ba7219494`.
Authoritative feature: `/home/jefferson/distributed_safety_critical_thesis/specs/024-maestro-lite-lifecycle/`.

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
