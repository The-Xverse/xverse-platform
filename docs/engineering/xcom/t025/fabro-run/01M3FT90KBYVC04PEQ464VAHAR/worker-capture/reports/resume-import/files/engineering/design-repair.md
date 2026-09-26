# T025 Design Repair Note

- Source run: `01M3EYZ3203P78PJKG8HXCX6T3`
- Source candidate identity SHA-256: `bde5d11c16cb577882d118f3913b10bee0f0b7325b2f1c763f0223dd8e6c6a57`
- Terminal review SHA-256: `3aad4d719ef7ac46c7d7dc7171539406b55bd80968c4e1d6067579a1ad78b82b`
- Failed gate: independent terminal review (disposition `changes required`)
- Route: `design_repair`
- Findings resolved: `R1`, `R2`, `R3`, `R4` (the four reproduced probes in `terminal-review.json`).
  `R5` (terminal export omitted candidate files) is a terminal-collection/handoff defect, not a
  design defect; it is recorded here and resolved in the terminal-collection stage, not in this
  design stage.

## Scope of this repair

This stage repairs the **design and verification intent** only. Source (`src/...`) and tests
(`tests/...`) are **not** edited here; the implementation stage realises these changes and
reconciles the test fixtures. Accepted requirement IDs and behavior, all REF-002 dispositions,
the no-emission boundary, and the protected-check limitations are preserved.

## Findings and design resolutions

### R1 — same-domain lifecycle transitions bypass the time authority (T025-SR-005)

- Rejected state: `SessionManager::transition` initialised `resolved` from the caller's timestamp
  and consulted the authority only for a different domain, so same-domain operations never checked
  domain registration, source availability, bounds, regression, or actual current time. Design
  §7.4/§7.5 previously permitted the direct comparison.
- Resolution: `design.md` §7.5 now defines the time-claim contract. `now_domain`/`now_value` is a
  caller-supplied **claim**, never trusted directly. The manager always (a) obtains the authority's
  authoritative reading via `now(now_domain)` — including the same-domain case — (b) cross-checks
  the claim against that reading (full-range unsigned distance must be zero, else
  `ToleranceExceeded`), (c) maps the authoritative reading to the validity domain when needed, and
  (d) compares the authoritative time against `[valid_from, valid_until)`. This is the API semantic
  that prevents a caller-supplied stale time from authorizing an action: the authority's reading is
  authoritative, and a claim that disagrees with it cannot pass.

### R2 — independent managers issue identical controller identities (T025-SR-011)

- Rejected state: controller identity was derived from the controller name plus a per-manager
  sequence starting afresh in each manager, so two managers (or a recreated manager) issued
  identical identities and generation 1; a handle from one manager was accepted by another.
- Resolution: `design.md` §3 and §7.1 introduce a host-issued, non-zero **`ManagerScope`**
  (fresh per instance and per recreation) and require a host-issued, globally unique
  **`ControllerId`** at registration. The manager never derives identity from a name or a
  per-manager counter, so a per-manager counter is never assumed globally unique. Handles bind
  `{scope, controller, generation, session}` and validate the scope first, so a foreign or
  recreated manager's handle is `ForeignHandle` before any session is addressed. A zero or
  duplicate identity is rejected with `InvalidController` (`design.md` §8.1 rank 25).

### R3 — tolerance arithmetic admits maximally separated timestamps (T025-SR-003)

- Rejected state: `convert` subtracted timestamps modulo 2^64 and used the unsigned result's top
  bit as a sign bit, returning `Ok` for `INT64_MIN`/`INT64_MAX` with tolerance 1 when the true
  distance is `UINT64_MAX`.
- Resolution: `design.md` §4.3 computes the full-range unsigned distance from the ordering of the
  original signed values (`candidate >= dst_now ? (uint64_t)candidate − (uint64_t)dst_now :
  (uint64_t)dst_now − (uint64_t)candidate`), exact over the entire signed 64-bit domain with
  maximum `UINT64_MAX`, and without wraparound or sign-bit interpretation.

### R4 — a rejected conversion advances the monotonic baseline (T025-SR-015)

- Rejected state: public `convert` committed the destination baseline before the tolerance check,
  so a rejected conversion advanced the baseline (100 → 200) and later operations observed
  `ClockRegression` solely due to the rejected operation.
- Resolution: `design.md` §4.3 and §9.1 specify transactional authority state. The destination
  read is performed without committing the baseline; the baseline is committed only after overflow,
  bounds, and tolerance all pass, inside the same critical section. Every failed conversion
  preserves the baseline, the output value, and all authority state, and leaves session state,
  counters, and permit bookkeeping unchanged.

## Changed files

- `engineering/design.md` — revision 2; §3 vocabulary (`ManagerScope`, host-issued `ControllerId`),
  §4.3 distance arithmetic and transactional baseline, §7.1 controller identity/scope, §7.2 handle
  scope check, §7.5 time-claim contract, §8.1 `InvalidController`, §9.1 transactional note, §11
  D-9/D-10.
- `engineering/verification-plan.md` — revision 2; §2 scope/identity fixtures, CLK-13..CLK-17
  (full-range distance and baseline preservation), HND-08..HND-11 (cross-manager, recreation,
  duplicate/zero identity), NOMUT-07 (failed-conversion transactional state), and §15 adversarial
  cases ADV-R1..ADV-R4 reproducing every `terminal-review.json` probe with the exact rejected
  state and the subsequent required observation.
- `engineering/architecture/components/validation_time_authority.json` — corrected distance
  arithmetic and added the commit-only-after-all-checks responsibility.
- `engineering/architecture/components/validation_session_manager.json` — host-issued identity and
  uniqueness scope, scope-first handle validation, time-through-authority responsibility, and
  `register_controller(ControllerId, ControllerName)` plus `InvalidController`.
- `engineering/architecture/components/validation_types.json` — added `ManagerScope` to the core
  vocabulary.

Diagrams (`engineering/architecture/diagrams/*`) are unchanged: no component was added, removed,
or renamed, and the component labels and dependency edges are unchanged by this repair.

## Preserved artifacts (unchanged)

- `engineering/requirements.md`, every `engineering/requirements/T025-*.json`, the ReqIF export,
  and the requirements inspection report are unchanged.
- `engineering/architecture/components/validation_diagnostic.json`,
  `validation_permit.json`, `validation_permit_registry.json`, and `validation_session.json` are
  unchanged.
- REF-002 dispositions (`XVE-SYS-0144`, `-0147`, `-0152`, `-0154`), the FR-015–FR-020/FR-033
  anchor-preservation note, the zero normal-route emission boundary, and the protected-check
  limitations are preserved verbatim.

## Verification performed

- Re-read the rejected `terminal-review.json` and `terminal-review.md` and confirmed every
  reproduced probe is now covered by an explicit adversarial case (ADV-R1..ADV-R4) with the exact
  rejected state and the subsequent required observation.
- Confirmed `design.md` §7.5 no longer contains any same-domain direct-comparison path; every
  time-dependent decision resolves through the authority.
- Confirmed §4.3 no longer relies on two's-complement wraparound or a sign bit.
- Confirmed the destination baseline commit is deferred until all conversion checks pass.
- Confirmed the controller identity is host-issued and scoped; no per-manager counter is assumed
  globally unique.
- Recalculated the SHA-256 of every changed artifact (see `stage-results/design.json`).

## Required follow-up at implementation

- Realise the revised API semantics in `src/xverse/xcom/include/xverse/xcom/validation_session.hpp`
  and `src/xverse/xcom/src/validation_session.cpp` without weakening SR-005, SR-003, SR-011, or
  SR-015.
- Reconcile the test fixtures: declare the clock domain used by every nominal transition, drive
  the injected source so the claim equals the authority reading, supply a non-zero `ManagerScope`
  and a host-issued `ControllerId`, and add the ADV-R1..ADV-R4 cases.
- Reconcile the downstream unit-specification (`engineering/unit-specifications/T025-U-MANAGER.json`)
  and maintenance notes (`engineering/maintenance.md`), which still record the pre-repair
  `register_controller(name)` signature; these belong to the implementation and maintenance stages
  and are intentionally not edited in this design stage.
- Re-run the internal inspection gates; earlier pass reports are not reused as proof for these
  challenged contracts, and a new successful workflow still requires independent terminal review.
