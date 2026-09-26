# T025 Requirements — Explicit Time Authority, Local Validation Permit, and Bounded Validation-Session Lifecycle

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T025 |
| Stage / role | requirements |
| Revision | 1 |
| Classification | SANITIZED |
| Requirement ID family | `T025-STK-###` (stakeholder), `T025-SR-###` (software) |
| Canonical records | `engineering/requirements/T025-*.json` |
| Predecessor baseline | accepted commit `d244eeb3aa26f1b27d23d75fabc750380405269f` |
| Admitted inputs | `packet.md`, `interface-bridge.md` (hashes in §3) |
| Next deterministic gate | export of the canonical records to ReqIF 1.2 (`engineering/exports/requirements.reqif`) |

### 1.1 Authority statement

This document and its canonical JSON records are an internal, source-free engineering
candidate produced by a worker in a restricted sandbox. They **do not** establish accepted
X-COM delivery, do not claim predecessor regression, exact source compatibility, repository
integration, protected verification, stakeholder acceptance, or production readiness. Those
remain external protected review steps performed after Codex review of the terminal package.

The restricted predecessor checkout is unavailable to the worker. Where an authoritative
predecessor identifier or statement would be required, this document preserves the identifier
as a trace anchor and explicitly records the limitation rather than inventing content
(see §8 and §11).

### 1.2 Decision rule

Any conflict between this candidate and the accepted predecessor or admitted packet is
resolved in favour of the authoritative source. On a material gap the worker returns
`blocked` with the exact decision needed instead of guessing.

## 2. Scope

### 2.1 In scope (bounded T025 foundation)

A C++20, domain-neutral foundation for three capabilities, implemented with the C++20 standard
library only, with public types in `xverse::xcom::validation`:

1. **Explicit time authority** — identifies clock domains, obtains bounded current time, and
   maps between domains only under declared source, destination, and tolerance rules.
2. **Host-controlled local validation permit** — an immutable permit binding exactly one
   validation session and its operational envelope, with exactly-once consumption.
3. **Bounded validation-session lifecycle** — controller/handle identity with generation,
   the `declared → armed → active → closing → closed` lifecycle, terminal states, and
   rejection-safe, payload-free diagnostics.

### 2.2 Explicit exclusions (must remain absent)

The candidate must neither emit a communication item nor create a transport, gateway, network
listener, journal, lease, dashboard, persistent store, or external service. Stimulation is
disabled by default; Maestro triggers and any communication provider/observation/item/payload
behaviour are out of scope. Normal-route emission count is zero.

### 2.3 Out of scope for this slice (later stimulation work)

This is a *bounded foundation*. It establishes permit and session primitives only. Actual
stimulation, stimulation enablement/arming of external effects, Maestro trigger delivery, and
durable intent/outcome records are later tasks (T026–T034) and are **not** implemented or
claimed here. Requirement statements that mention these areas are marked *allocated* or
*deferred* in §9.

## 3. Admitted inputs and integrity

| Input | SHA-256 | Use |
| --- | --- | --- |
| `packet.md` | `8b507653464b75cb9b1493ea86ed7e76825dd8fd675e299a2091239c8c800c39` | normative T025 scope, behaviour, and verification expectations |
| `interface-bridge.md` | `103dd9cbfd2848b73c4ce8634435c44537f662e4fb0cd6dce28f96e07d994b3c` | candidate paths, namespace, REF-002 allocation |

`admission.json` (classification `SANITIZED`, accepted predecessor commit) governs authority
and allowed inputs. No other project input is admitted; the worker must not seek the
restricted predecessor checkout, historical SESN records, credentials, or network access.

## 4. Terminology and measurement

| Term | Meaning in T025 |
| --- | --- |
| Clock domain | A named, declared source of monotonic or wall-clock time with an identity the authority understands. |
| Mapping | A declared directed rule from a source clock domain to a destination clock domain with a maximum admissible tolerance. |
| Permit | An immutable, host-issued validation permit binding exactly one session identity and operational envelope. |
| Consumption | The single successful act of accepting a permit for a session; never repeatable for the same permit or session identity. |
| Handle | A host-generated reference binding a controller identity and a generation counter to one live session record. |
| Rejection | A failed operation that performs no state mutation and yields a stable, ordered, payload-free diagnostic. |
| Normal route | The default (non-stimulating, non-test) execution path; its emission count must remain zero. |

Measurements used by this document are observable and discrete (state values, result codes,
diagnostic codes and ordering, counters, field comparisons). No numeric reliability target
(for example availability, MTBF, or probability-of-failure figures) is asserted: such targets
are not derivable from the admitted packet and must not be invented (§11).

## 5. Stakeholder requirements

Stakeholder requirements express accepted T025 intent in observable terms. Every software
requirement in §6 refines exactly one stakeholder requirement through the `refines` field of
its canonical record.

### T025-STK-001 — Explicit time authority governs all time-dependent decisions

**Statement.** All permit-validity and session-lifecycle time decisions must be made through a
single explicit time authority that knows its clock domains and only compares times within one
domain or through a declared mapping.

**Acceptance criteria (observable).**

- AC-1: No code path compares a raw timestamp from one clock domain with a raw timestamp from
  a different clock domain.
- AC-2: An unrecognised clock domain yields a distinct deterministic result rather than a
  silent success.
- AC-3: A cross-domain comparison without a declared mapping yields a distinct deterministic
  result rather than a silent success.
- AC-4: Unknown clock, missing mapping, tolerance failure, regression, and overflow are each
  distinguishable by result value.

**Source anchors.** `packet.md` §"The time authority identifies clock domains…"; `XVE-SYS-0147`.

### T025-STK-002 — Local validation permit is exactly-once and exactly-bound

**Statement.** A host-controlled local validation permit must bind exactly one session and its
complete operational envelope, and must be consumed at most once.

**Acceptance criteria (observable).**

- AC-1: A permit differing from the consuming session in any single bound field is rejected and
  the mismatching field is identifiable from the diagnostic.
- AC-2: A consumed permit cannot be consumed again, including when presented with a changed nonce.
- AC-3: A second session identity cannot consume a permit already consumed for another session.
- AC-4: Undefined action bits and composite values not explicitly allowed are rejected.
- AC-5: Exhausted finite quotas or capacities produce an explicit exhaustion result.

**Source anchors.** `packet.md` §"The immutable permit binds exactly one session identity…";
`interface-bridge.md` §REF-002 (`XVE-SYS-0152`, `XVE-SYS-0144`).

### T025-STK-003 — Bounded session lifecycle with controller-bound handles

**Statement.** A validation session is created by a host-generated controller identity, is
addressed by a handle bound to that controller identity and a generation, and moves only
through the defined lifecycle and terminal states.

**Acceptance criteria (observable).**

- AC-1: Every lifecycle state `declared`, `armed`, `active`, `closing`, `closed`, `expired`,
  `revoked`, `evidence-incomplete` is reachable through defined operations.
- AC-2: A stale handle (older generation), a foreign handle (other controller identity), and a
  handle from a recreated controller cannot authorise an operation on another live session.
- AC-3: An unsafe repeat of an already-completed lifecycle operation is rejected deterministically.
- AC-4: Validation of handle, context, time, and action completes before any state mutation.

**Source anchors.** `packet.md` §"Session handles bind a host-generated controller identity…";
`XVE-SYS-0144`, `XVE-SYS-0152`.

### T025-STK-004 — Rejection is non-mutating; diagnostics are stable and payload-free

**Statement.** Any rejected operation leaves the affected session and permit state unchanged and
produces a stable, ordered diagnostic that carries no payload.

**Acceptance criteria (observable).**

- AC-1: For every negative case, observable session state, permit consumption state, and
  counters are identical before and after the rejected call.
- AC-2: Repeating an identical rejected call produces an identical diagnostic code sequence.
- AC-3: When more than one failure applies, the reported code follows the declared precedence
  order deterministically.
- AC-4: No diagnostic contains a payload, item, observation, or free-form content field.

**Source anchors.** `packet.md` §"Rejected operations leave state unchanged…"; `XVE-SYS-0154`.

### T025-STK-005 — Zero normal-route emissions

**Statement.** The normal route must emit zero communication items, zero telemetry, zero
network traffic, and zero persisted records.

**Acceptance criteria (observable).**

- AC-1: The candidate exposes no emission, transport, journal, or persistence API.
- AC-2: Nominal (non-test) execution performs no I/O beyond in-memory state.
- AC-3: Any normal-route emission counter reported by the candidate is zero.

**Source anchors.** `packet.md` §"The foundation must neither emit a communication item nor
create a transport…".

### T025-STK-006 — Bounded, concurrency-safe resources

**Statement.** The foundation's memory, permit bookkeeping, and session capacity are finite and
configurable, and concurrent use yields deterministic results without duplicate consumption.

**Acceptance criteria (observable).**

- AC-1: Session capacity, permit-consumption bookkeeping, and mapping tables have finite,
  host-configurable bounds with defined exhaustion behaviour.
- AC-2: Concurrent attempts to consume the same permit produce exactly one success and a
  deterministic set of failures.
- AC-3: Concurrent session operations do not corrupt handle/controller binding or lifecycle state.
- AC-4: Time-authority lifetime and copy/synchronisation rules are explicit and honoured.

**Source anchors.** `packet.md` §"Define synchronization and lifetime rules…";
`interface-bridge.md` §REF-002 (`XVE-SYS-0147`).

## 6. Software requirements

Software requirements are the level the standalone C++20 candidate must satisfy and that the
later trace graph links to components, units, code, and tests. Each refines one §5 stakeholder
requirement. Result codes named below (for example `UnknownClock`, `MissingMapping`) are the
candidate's public deterministic outcomes; the design stage fixes their exact identifiers and
the implementation stage provides them.

### 6.1 Time authority

#### T025-SR-001 — Declare and identify clock domains (refines T025-STK-001)

**Statement.** The authority must accept a finite set of declared clock domain identities and
must report an unknown or undeclared domain as a distinct deterministic failure.

**Acceptance criteria.**

- A declared domain is accepted and addressable by identity.
- An undeclared domain yields `UnknownClock` and no state mutation.
- Domain identity is stable across calls and comparable for equality.

**Verification intent.** Unit: register/query declared domains; query an undeclared domain and
assert the `UnknownClock` outcome and unchanged authority state.

#### T025-SR-002 — Bounded current-time acquisition (refines T025-STK-001)

**Statement.** The authority must obtain current time for a declared domain from a host-supplied
time source within a bounded, explicit interval, and must report failure distinctly when the
source is unavailable or returns an out-of-bounds value.

**Acceptance criteria.**

- A valid read returns a timestamp attributed to the requested domain only.
- A source failure or out-of-bounds value yields a distinct deterministic failure, not a guess.
- Reads never fabricate time nor fall back to another domain silently.

**Verification intent.** Unit: inject a deterministic source; assert returned domain attribution;
inject failure and out-of-bounds sources and assert distinct failures.

#### T025-SR-003 — Declared source→destination mapping with tolerance (refines T025-STK-001)

**Statement.** Converting a time from a source domain to a destination domain must require a
declared mapping carrying source, destination, and maximum admissible tolerance; a missing
mapping or a tolerance failure must return distinct deterministic results.

**Acceptance criteria.**

- A declared mapping converts within tolerance and reports the destination domain.
- An undeclared source→destination pair yields `MissingMapping`.
- A conversion beyond the declared tolerance yields a distinct tolerance-failure result.
- Mappings are directional: a declared A→B mapping does not silently enable B→A.

**Verification intent.** Unit: declared mapping inside/at/beyond tolerance; reverse-direction
request; undeclared pair; assert distinct outcomes and no mutation.

#### T025-SR-004 — Regression and overflow are distinct failures (refines T025-STK-001)

**Statement.** The authority must detect monotonic regression in a domain and arithmetic
overflow during conversion, and must return distinct deterministic results for each.

**Acceptance criteria.**

- A reading earlier than a prior reading in the same declared monotonic domain yields a distinct
  regression result.
- A conversion whose result cannot be represented yields a distinct overflow result.
- Regression and overflow are distinguishable from tolerance failure and from each other.

**Verification intent.** Unit: sequence decreasing readings; construct boundary conversion that
overflows; assert distinct codes and unchanged state.

#### T025-SR-005 — Validity and lifecycle decisions use the authority only (refines T025-STK-001)

**Statement.** Permit-validity and session-lifecycle time decisions must be expressed as
authority queries in a single domain or through a declared mapping; raw timestamps from
different domains must never be compared directly.

**Acceptance criteria.**

- Every time-dependent decision path resolves its comparison through the authority.
- A permit whose validity interval is expressed in another domain is only evaluated after a
  successful declared mapping (or is rejected with `MissingMapping`).
- No code path direct-compares two raw domain timestamps.

**Verification intent.** Unit: valid/expired permit in-domain; permit in a foreign domain with
and without a mapping; static check that direct cross-domain comparison is absent.

#### T025-SR-006 — Authority lifetime and synchronisation contract (refines T025-STK-006)

**Statement.** The time authority must be non-copyable, must have an explicit documented
lifetime, and must be safe for concurrent read/query use with deterministic results.

**Acceptance criteria.**

- Copy construction/assignment of the authority is not available.
- The public API documents ownership, lifetime, and thread-safety guarantees.
- Concurrent queries from multiple threads return deterministic results with no data race under
  the applicable sanitizer check.

**Verification intent.** Unit/static: non-copyability assertion; concurrent query test; strict
Doxygen build for the documented contract.

### 6.2 Immutable permit binding and one-time consumption

#### T025-SR-007 — Immutable permit binds the exact session envelope (refines T025-STK-002)

**Statement.** A permit must be immutable once constructed and must bind exactly one session
identity, plan digest, scenario, deployment, environment, tool, interface, target, nonce,
allowed action set, validity interval, and every finite quota or capacity.

**Acceptance criteria.**

- All listed fields are present and individually comparable; the permit exposes no mutator.
- A mismatch in any single field between permit and consuming session is detected.
- Absent or default-initialised values for an identity-bearing field are rejected, not treated
  as a wildcard.

**Verification intent.** Unit: field-by-field mismatch matrix (one test per bound field) that
asserts rejection and names the mismatching field; mutability absence asserted by API shape.

#### T025-SR-008 — Undefined actions and composite values are rejected (refines T025-STK-002)

**Statement.** The allowed action set must be a closed, finite set; undefined action bits and
composite values not explicitly allowed must be rejected deterministically.

**Acceptance criteria.**

- A permitted single action within the allowed set succeeds at validation.
- An undefined action bit is rejected with a distinct code.
- A composite/combined value not declared allowed is rejected with a distinct code, never
  interpreted as its components.

**Verification intent.** Unit: allowed single action; undefined bit; disallowed combination;
assert distinct codes, no partial acceptance.

#### T025-SR-009 — Exactly-once consumption with explicit replay scope (refines T025-STK-002)

**Statement.** Consumption must be controller-scoped and exactly-once: a consumed permit
identity, or a session identity already bound to a consumed permit, must not be consumed again,
including when presented with a changed nonce.

**Acceptance criteria.**

- First consumption of a valid permit succeeds and records the binding atomically.
- Re-presenting the same permit identity is rejected, including with a different nonce.
- A different session identity presenting an already-consumed permit identity is rejected.
- Attempts to consume a permit already bound to another session identity are rejected.
- The declared replay scope (per controller instance) is documented and enforced.

**Verification intent.** Unit: replay matrix — same permit/same nonce, same permit/changed nonce,
different session/same permit; concurrent double-consumption; assert exactly one success.

#### T025-SR-010 — Quota and capacity exhaustion is explicit (refines T025-STK-002, T025-STK-006)

**Statement.** Every finite quota or capacity bound carried by the permit and every bounded
bookkeeping structure must have an explicit exhaustion result and must never exceed its bound.

**Acceptance criteria.**

- Consuming at the final available unit succeeds; one beyond yields a distinct exhaustion result.
- Exhaustion does not consume, partially apply, or mutate unrelated state.
- Bookkeeping structures never grow past their configured bound.

**Verification intent.** Unit/boundary: capacity-1 and capacity-N boundaries for quotas and for
session/permit tables; assert last-success and first-exhaustion results.

### 6.3 Session lifecycle, identity, and diagnostics

#### T025-SR-011 — Handles bind controller identity and generation (refines T025-STK-003)

**Statement.** A session handle must bind a host-generated controller identity and a generation
counter so that stale, foreign, and recreated-controller handles cannot authorise any operation.

**Acceptance criteria.**

- A valid current handle from the owning controller is accepted.
- A stale handle (prior generation) is rejected distinctly.
- A foreign handle (different controller identity) is rejected distinctly.
- A handle from a recreated controller with the same name but a new identity is rejected.
- Handle forgery (arbitrary/generated handle values) never addresses a live session.

**Verification intent.** Unit: ownership and recreation matrix; stale/foreign/forged handles;
assert rejection, no mutation, and that no other live session is affected.

#### T025-SR-012 — All lifecycle and terminal states are defined and reachable (refines T025-STK-003)

**Statement.** The lifecycle must expose `declared → armed → active → closing → closed`, with
`expired`, `revoked`, and `evidence-incomplete` as terminal states, and must define which
transitions are legal from each state.

**Acceptance criteria.**

- Each state is reachable via its defined operation from its predecessor.
- Terminal states admit no outgoing transition; attempts are rejected deterministically.
- Invalid transitions (for example `declared → active`) are rejected without mutation.
- Expiry and revocation can be applied from the states where they are defined as legal.

**Verification intent.** Unit: full transition table (legal and illegal pairs); terminal-state
lockout; assert resulting state values and rejection codes.

#### T025-SR-013 — Validation precedes mutation; safe idempotency only (refines T025-STK-003)

**Statement.** Validation of handle, context, time, and action must complete before any state
mutation; safe (idempotent) repeats must be accepted with a stable "already applied" outcome and
unsafe repeats must be rejected.

**Acceptance criteria.**

- No state change is observable when any pre-mutation validation fails.
- A safe repeat (already in the requested state, same owning handle) returns a stable
  already-applied outcome without changing state.
- An unsafe repeat (requested transition conflicts with current state) is rejected distinctly.
- The set of safe repeats is explicitly enumerated in the design.

**Verification intent.** Unit: each pre-mutation failure stage injected in turn with state
snapshot comparison; safe-repeat and unsafe-repeat cases for each transition.

#### T025-SR-014 — Bounded session capacity and lifecycle bookkeeping (refines T025-STK-006)

**Statement.** Live session capacity and controller/handle bookkeeping must be finite and
host-configurable; creation beyond capacity must fail explicitly without leaking a handle.

**Acceptance criteria.**

- Creating sessions up to capacity succeeds; one beyond yields an explicit capacity result.
- A failed creation returns no usable handle and leaves capacity unchanged.
- Closing/terminating a session frees exactly its capacity slot, allowing reuse.

**Verification intent.** Unit/boundary: fill to capacity, attempt overflow, close one, reuse;
assert results, handle invalidity, and slot accounting.

#### T025-SR-015 — Rejection leaves state unchanged (refines T025-STK-004)

**Statement.** Every rejected operation must leave the affected session record, permit
consumption bookkeeping, counters, and authority caches unchanged.

**Acceptance criteria.**

- For each negative case there is a snapshot-equality assertion (state, consumed set, counters).
- Rejection of one session does not perturb any other session or the authority.
- A failed transition never partially applies (no intermediate state is observable).

**Verification intent.** Unit: snapshot-before/after for every negative case in the mismatch,
replay, clock, handle, and lifecycle matrices.

#### T025-SR-016 — Ordered, payload-free diagnostics (refines T025-STK-004, T025-STK-005)

**Statement.** Diagnostics must be returned as an ordered sequence of stable, enumerable codes
with no payload, item, observation, or free-form content, and multi-failure ordering must follow
a declared precedence.

**Acceptance criteria.**

- A diagnostic value is a bounded, enumerable code (plus at most a bounded numeric locator such
  as an interface index), with no strings carrying data.
- Multi-failure inputs produce the declared precedence order, identical on repetition.
- The same input yields the same code sequence across runs and builds.
- No diagnostic can carry a communication item, observation, or payload.

**Verification intent.** Unit: precedence cases with an expected exact code sequence; repeat
determinism; structural assertion that diagnostic types hold no payload.

#### T025-SR-017 — Deterministic concurrency for consumption and mutation (refines T025-STK-006)

**Statement.** Concurrent permit consumption and concurrent session mutation must be atomic with
respect to shared state, producing deterministic outcomes (exactly one success where the
operation is exactly-once).

**Acceptance criteria.**

- N concurrent consumptions of one valid permit yield exactly one success.
- The remaining N−1 outcomes are drawn from the defined non-success set, with no duplicates of
  a successfully applied mutation.
- Shared mutable state is guarded so no data race is reported under the applicable sanitizer run.

**Verification intent.** Unit/integration: multithreaded consumption and lifecycle stress with
an exact success-count assertion and sanitizer execution.

#### T025-SR-018 — Zero normal-route emissions (refines T025-STK-005)

**Statement.** The candidate must not expose or perform any normal-route emission: no
communication item, transport, gateway, network listener, journal, lease, dashboard, persistent
store, or external service, and no logging/telemetry in the nominal path.

**Acceptance criteria.**

- The public API surface contains no emission/transport/persistence entry point (static check).
- Nominal operations perform no file, socket, or environment I/O (static check plus test
  harness that fails if any such call is reached).
- A reported normal-route emission counter is zero after the nominal test scenario.

**Verification intent.** Static: API-surface enumeration and I/O-call inspection. Unit/integration:
nominal scenario asserting the zero-emission counter and the absence of emission side effects.

## 7. Preserved accepted requirement anchors

The admitted packet requires preservation of the accepted functional requirement IDs
`FR-015`–`FR-020` and `FR-033`. Their authoritative statements live in the restricted
predecessor checkout, which is unavailable to the worker; therefore this document preserves the
IDs as **trace anchors only** and does not restate, renumber, or reinterpret their content.

| Anchor | Preservation in this candidate | Limitation |
| --- | --- | --- |
| FR-015 | Link anchor on `T025-SR-001`–`T025-SR-005` (X-COM validator time/behaviour family) | statement not restated; predecessor text unavailable |
| FR-016 | Link anchor on `T025-SR-007`, `T025-SR-008` (validator binding/envelope family) | statement not restated; predecessor text unavailable |
| FR-017 | Link anchor on `T025-SR-009`, `T025-SR-010` (validator consumption/quota family) | statement not restated; predecessor text unavailable |
| FR-018 | Link anchor on `T025-SR-011`, `T025-SR-012` (validator session/identity family) | statement not restated; predecessor text unavailable |
| FR-019 | Link anchor on `T025-SR-013`, `T025-SR-015` (validator ordering/rejection family) | statement not restated; predecessor text unavailable |
| FR-020 | Link anchor on `T025-SR-016`, `T025-SR-018` (validator diagnostics/emission family) | statement not restated; predecessor text unavailable |
| FR-033 | Link anchor on `T025-SR-005`, `T025-SR-017` (authority/concurrency obligation) | statement not restated; predecessor text unavailable |

Because the worker cannot read the predecessor, the exact allocation of these anchors is a
**protected-review decision**. The trace matrix marks each such link as *anchor-preserved,
allocation unverified*. If protected review finds a mismatch, this is the decision needed:
*confirm the authoritative statement and allocation of FR-015–FR-020 and FR-033, or return the
corrected anchor-to-requirement mapping.*

## 8. REF-002 dispositions

The bridge allocates four public-safe REF-002 IDs to this slice. Dispositions below use the
required vocabulary (implemented, partial, allocated, deferred, conflicting, needing
clarification). "Implemented" here means within this standalone candidate only — it never
implies predecessor acceptance.

| REF-002 ID | Disposition | Basis |
| --- | --- | --- |
| `XVE-SYS-0144` | **partial** (channel identity/access **deferred** to Security) | T025 implements only a bounded local validation permit; general channel identity and access remain Security's scope and are deferred. |
| `XVE-SYS-0147` | **partial** (clock-domain interface) with **allocated** hard-real-time proof | T025 declares clock domains, mappings, tolerance, regression, and overflow; hard real-time proof is deferred to protected verification. |
| `XVE-SYS-0152` | **partial** (permit/session foundations) with stimulation **deferred** | T025 provides permit and session primitives; actual stimulation and Maestro triggers are later tasks. |
| `XVE-SYS-0154` | **partial** (payload-free diagnostics) with durable intent/outcome **deferred** | T025 delivers ordered payload-free diagnostics; durable intent/outcome provenance remains deferred. |

**Conflicting:** none identified within the admitted inputs.
**Needing clarification:** none identified for REF-002 itself; the FR anchor allocation in §7 is
the sole item referred to protected review.

## 9. Distinction from later stimulation tasks

| Area | This T025 foundation (bounded) | Later tasks T026–T034 (out of scope) |
| --- | --- | --- |
| Time | Clock domains, bounded reads, declared mapping, tolerance/regression/overflow outcomes | Hard real-time guarantees and system-wide clock certification |
| Permit | Immutable binding, closed action set, exactly-once consumption, quotas | Security-grade channel identity and access control |
| Session | Bounded lifecycle, controller/handle identity, terminal states | Stimulation enablement, Maestro trigger delivery |
| Diagnostics | Ordered, payload-free codes | Durable intent/outcome records and provenance store |
| Emissions | Zero normal-route emissions (asserted) | Communication item production on the normal route |

No requirement in §5–§6 asserts stimulation behaviour; the corresponding REF-002 scope is
recorded as *deferred* above.

## 10. Assumptions and open items

1. **A-1** — The authoritative statements of FR-015–FR-020 and FR-033 are unavailable; only the
   IDs are preserved. *Effect:* anchor allocation needs protected confirmation (§7).
2. **A-2** — Result/diagnostic code identifiers are candidate-chosen names; the design stage
   fixes exact spellings. *Effect:* none on behaviour, naming may differ from predecessor.
3. **A-3** — All numeric capacities are host-configured finite bounds with defined exhaustion;
   no specific numeric reliability target is claimed. *Effect:* capacity values are a design
   parameter, not an accepted reliability claim.
4. **A-4** — The candidate uses only the C++20 standard library and does not include predecessor
   headers. *Effect:* integration into the accepted repository is a protected host step.

**Material gap requiring a decision:** item A-1. It is a *link-preservation* gap, not an
implementation blocker: the candidate can be built and internally verified without predecessor
text, and the affected links are marked anchor-preserved/allocation-unverified. The worker
therefore proceeds and records the decision needed rather than returning `blocked`. Should
protected review instead require the authoritative text *before* any candidate work, the exact
decision is: *provide the accepted statements and allocation for FR-015–FR-020 and FR-033, or
authorise anchor-only preservation.*

## 11. Requirement-to-canonical-record index

| Requirement | Canonical record | Level | Refines |
| --- | --- | --- | --- |
| T025-STK-001 | `engineering/requirements/T025-STK-001.json` | stakeholder | — |
| T025-STK-002 | `engineering/requirements/T025-STK-002.json` | stakeholder | — |
| T025-STK-003 | `engineering/requirements/T025-STK-003.json` | stakeholder | — |
| T025-STK-004 | `engineering/requirements/T025-STK-004.json` | stakeholder | — |
| T025-STK-005 | `engineering/requirements/T025-STK-005.json` | stakeholder | — |
| T025-STK-006 | `engineering/requirements/T025-STK-006.json` | stakeholder | — |
| T025-SR-001 … T025-SR-006 | `engineering/requirements/T025-SR-00{1..6}.json` | software | T025-STK-001 / T025-STK-006 |
| T025-SR-007 … T025-SR-010 | `engineering/requirements/T025-SR-00{7..9},010.json` | software | T025-STK-002 |
| T025-SR-011 … T025-SR-014 | `engineering/requirements/T025-SR-01{1..4}.json` | software | T025-STK-003 / T025-STK-006 |
| T025-SR-015 … T025-SR-018 | `engineering/requirements/T025-SR-01{5..8}.json` | software | T025-STK-004 / T025-STK-005 / T025-STK-006 |

All records carry `status: accepted` at the *candidate* level. The deterministic next gate
exports these records to ReqIF 1.2 preserving `id`, `statement`, `level`, `refines`, and
`source`.

