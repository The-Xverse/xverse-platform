# ADR-ML3-EVIDENCE-0001: original public evidence descriptor transport

Status: DRAFT engineering decision before code, within unfinished increment17.
Implements the next part of coverage-runtime-closure.md; acceptance is pending.
Requirements ML-SR-016–024 remain partial; all18 source parents remain unvalidated.

The original broker's complete bounded public projection can exceed the private
64-KiB packet bound. Keep every admitted generation and the existing packet/input
bounds. Add optional sealed persistence v5 admission for the original coverage-
declared broker artifact. Transfer its public bytes through exactly one sealed
immutable regular data descriptor, with a bounded size and original byte digest.
The data grants no permit, process handle, productive descriptor ownership or cleanup
authority. The receiver owns and closes only the transferred inert data descriptor.

Python owns this finite control/evidence boundary; the existing native authority
continues to own productive effects. The original parent creates the public-only
memfd and sends it to its original worker under the original operation deadline.
The authenticated receiver closes all received descriptors on every path, including
credential/frame/shape/timeout/size/seal/hash failures. Only an explicitly admitted
public-blob request accepts one data descriptor. Other requests/replies preserve
their current zero-rights behavior. The worker receives inert bytes, independently
checks closed public shape/original run/lifecycle/context inventory and writes only
the original declared broker path through its pinned Argus root. It verifies actual
written bytes and the accepted public artifact-index return value before ACK.

The original parent method accepts its actual RunBroker, not arbitrary public
bytes or a copied projection. Receipt publication binds original admission, actual
snapshot digest and exact index entry. Matching repeats return the retained original
snapshot, without claiming it reflects later broker state. A failed/lost ACK closes
starts and preserves partial artifacts; it cannot replay publication. Default
v1–v4 configuration bytes/events remain unchanged. No Argus API is modified.

This supplies original input to the complete runtime path, not a stable subincrement
or a completed U7/U8/M1. Full collection, output quiescence, logical dispositions,
terminal ordering, permitted closure and independent closed verification remain
required. Do not infer hard latency from descriptor/byte bounds; host/kernel stalls
remain explicit limitations. Further starts must be fenced by the full closure
coordinator before it treats any snapshot as the terminal one.

Alternatives: dropping generations violates the admitted universe; raising the
packet limit changes all private framing; a shared filesystem mailbox would add
supervisor storage I/O and mutable transport. An immutable data descriptor keeps
large inert bytes separate from authority and the original worker owns storage.

Separate findings and unit expectations in public-evidence-transport.md precede
implementation. This decision changes no canonical thesis note or scientific scope.

## Lazy complete-profile schedule records (candidate, 2026-10-19)

Finding144 refines existing D2/D7 and lazy-issuance-runtime.md. Original sealed v6
selects logical scheduling before workload claims. Handle-free prepare and eligible
start-dispatch bookkeeping use actual scheduler validate annotations, generation0
and original schedule-admission source; these are not start intents/readiness.
The original first start effect creates durable M3 intent and Stage/issued ACK,
then binds its exact handle and performs unchanged controller/dependency/Release
checks under its fixed original end. No other statement may grow bindings.
Worker begin/terminal preserve the full prepared universe and independently reject
handle-free productive completion or duplicate/uncertain attempt substitution.
Existing eager profile remains compatible; all full17 gates remain open.

## Original terminal report/close protocol (candidate, 2026-10-19)

Under v6, terminal-report publish/close use the two previously reserved requests
and one fixed original <=2s report end. Publish uses retained real index ACKs and
confined actual bytes, writes retained original fields/M3 and one provisional
coverage report, then returns a compact receipt. Close must match that original
receipt digest and independently retained finalize predicate. Positive public
flush usability precedes any abort, including after a finalize error whose state
remains open. Neither private stream inspection nor writer recreation is allowed.
After closure, an accepted-reader runtime verifier takes externally pinned original
CoverageAdmission and CollectionPlan, checks actual manifest/artifacts and rederives
collection/report semantics. ACKs alone cannot supply full lifecycle/helper success.
Defaults retain previous behavior; full17/M1/runtime/acceptance gates remain open.

Report integration refinement before code (2026-10-19): v6 terminal state fixes
reportEndNs before publication, disallows other mutations once report is attempted,
and binds close to SHA256 of its exact retained compact report receipt. The parent
retains a matching immutable outcome even when acknowledgements fail and never
replays an uncertain report. Each operation is limited by original root cleanup
lease and fixed report end; a separate already-reserved drain window follows.
Actual report eligibility requires complete required/applicability/optional integrity,
original metadata/current worker items, final broker after terminal and successful
normal execution; a caller boolean cannot grant it. Automatic v6 dispatcher closure
is the target behavior. Older absent-profile paths keep their prior APIs.

Owned failure controls before repair (2026-10-19): the native test bootstrap may
embed fixed role3 Python fault code in a compiled copy whose exact digest is admitted
before birth. Production bootstrap and worker configuration gain no fault modes.
Actual public writer abort/finalize followed by a lost report-index ACK exercises
non-open close observation. Authentic original receipt/end must remain necessary;
independent closed completeness cannot mint the missing report index ACK or permit
another writer operation. Failed/closed writer observation, report eligibility and
whole-lifecycle completion remain separate facts.

Helper closure composition refinement before code (2026-10-19): RunClosure consumes
only a genuine original PersistenceClient's pinned TerminalReceipt when report/close
has already been attempted. An additive terminal_reports result preserves its exact
ACK/unknown facts; it never converts finalize observations to legacy abort fields or
replays the writer RPC. Original helper/root/native/C1 closure remains independently
required. Missing/ineligible report/close evidence adds an incomplete-report diagnostic,
not invented successful closure. The prior abort-only path remains for clients without
an original terminal outcome. Lifecycle/readiness maturity gates are unchanged.

Original runtime assessment scope before code (2026-10-19): a pure immutable
RuntimeEvidenceScope carries the canonical original CollectionPlan and generation.
Coverage and closed verification accept it only with an explicit external joint
runtime digest, rederive its inputs and generation reservation before I/O and derive
the terminal evidence ceiling from original generation minus reserved drain. The
original active interval still limits productive evidence/health windows; no dispatch,
lease,operation,collection,report or generation end is extended. Exact teardown intent
source proof distinguishes it from a late productive start intent. Runtime reports
bind this scope via inputDigests.runtimeAdmission, an allowed schema2.0 named digest;
standalone coverage retains its old default. Runtime pre-/post-closure paths use the
same scope and require original external inputs; report data cannot define its bound.

## Primary execution diagnostic during secondary cleanup failure (candidate)

Finding179: DispatchResult.diagnostic retains the first normalized execution failure
when cleanup also raises. With no earlier failure, cleanup-incomplete remains the
diagnostic. TeardownResult still explicitly marks emergency/incomplete cleanup and
execution remains unsuccessful. This changes diagnostic precedence only; it grants
no writer ACK, normal record, authority, deadline or lifecycle completion. Verify
using actual stopped original helpers and caller-side loss of the original cleanup
return, then repeat the whole affected source/installed-wheel scope.

## Offline evidence dependency boundary (candidate, finding181)

Place inert broker and collection evidence validation in a shared module containing
no runtime process/transport imports. Both original worker composition and offline
verification consume the same shape/digest checks. Retain public runtime decoder
functions as wrappers where necessary to preserve PersistenceError identity; the
offline codec uses a plain ValueError subtype with the same diagnostic text. Do not
duplicate protocol rules or change writer/collection semantics. Verify in a fresh
process with U3–U5 imports denied while reading actual independently pinned closed
evidence, then repeat all affected source/installed-wheel and compatibility checks.

## Native prerequisite guard delegation (candidate, finding185)

DependencyGuard identity validation remains at ReleaseOwner entry. For the original
native broker path, the live admitted prerequisite probe occurs at the broker's
existing final guard after ARM and durable revalidation, immediately before RELEASE.
The owner delegation boundary no longer persists a duplicate probe. Legacy gates
retain their existing initial and final guard checks. The start health scan remains
unchanged. No observation cache, permit/issuance shortcut, new deadline, relaxed
freshness or unguarded Release is introduced. Verify actual parent probe count,
after-ARM parent death and early identity rejection before repeating the complete
affected source/installed-wheel scope once.

## Amendment S1a-4: per-element bounded encoding of retained inputs (2026-10-23, written at 22:08:50; before implementation)

- **Context.** `_bounded` encodes the retained-inputs and public-export documents with `JSONEncoder.iterencode`
  (CPython's pure-Python path) and checks the deadline on every yielded chunk. At the S-D1 long-run size that is
  166,561 checks and about 1.1 s of a 2 s terminal budget (S1a review log finding 28). It made the live terminal
  report time out under load.
- **Decision.** `_bounded` encodes a top-level object as its sorted keys, and a list value element by element.
  Each element uses the same encoder (`sort_keys=True`, `separators=(',', ':')`, `ensure_ascii=False`,
  `allow_nan=False`). The cap is enforced on the running byte count after each element, and the checkpoint runs
  once per element.
- **The output is byte-identical** to the previous encoding for every input. A differential test proves it.
- **Unchanged.**
  - The 8192 limits, the caps and `ML-EVIDENCE-EXPORT-SIZE`.
  - The checkpoint semantics (deadline and liveness). Only its granularity is now per element rather than per
    chunk; one element is at most 64 KiB (`retained_intent` bound).
  - The digests, the files, and every reader.
- **Not done here.** No incremental cache of the snapshot. That is reconsidered only if the re-measured terminal
  report still lacks margin at load 10.
