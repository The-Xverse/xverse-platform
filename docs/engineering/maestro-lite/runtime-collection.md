# Original runtime collection

DRAFT engineering refinement within full increment17, before code. Governing
inputs: coverage-runtime-closure.md and its v2 hash-bound inputs; D3/D8/U8 and
ML-SR-016–024 remain partial. All24 requirements and18 unvalidated parents remain.

Python owns bounded file I/O in the original disposable persistence owner. Native
authority owns workload fencing/waits; collection metadata grants no authority.
An original CollectionSource opens a no-follow absolute source root before workload
and compares its actual device/inode with explicitly admitted values. Keep that
descriptor until terminal collection/disposal. Binding a collection checks the
original descriptor and named path, opens the distinct evidence root, and compares
the new source descriptor to the original pin. Replacement cannot be adopted.

Retain one aggregate collection deadline (positive, at most10s), full ordered output
declarations and per-declaration caps (0–1MiB), with16MiB total accepted read budget.
An incremental collect_next accepts exactly the next index; matching prior indices
return original rows without I/O, even after timeout. Invalid/skipped/boolean indices
reject. Each operation has its own earlier original-session deadline; it never
replaces or extends the aggregate end. Read bytes debit the retained aggregate
before copy; failed copies cannot replenish it. Existing collect consumes the same
cursor/budget and returns the same complete original result.

Index each collected item through the accepted public writer API, compare the whole
entry and exact byte type, and cache the original receipt by actual writer and row
identity. Failure is single-attempt: an uncertain/lost index ACK cannot be silently
retried. Whole-result index uses those same receipts without duplicate publication.
Root/declaration/cap/result substitutions remain errors. Nested destination parents
must be explicitly confined before use; the collector never traverses undeclared
files or overwrites an existing destination.

The later v6 worker profile must rederive full original coverage/output declarations,
pin source before writer effects, reserve every RPC/event, prove actual native/C1
quiescence plus fenced future starts before reading, step within original operation
and aggregate ends, write/index factual collection metadata, then publish terminal
records. Unknown/live ownership retains unavailable/error rows and gains no trusted
output credit. No provider/metric/scenario/oracle is called. Full finalize/abort and
independent closed-reader coverage remain separate required work.

Controls authored before implementation:

- IC01 actual root pinned early, later original collection/index and closed bytes.
- IC02 wrong inode, replaced/missing/symlink root and copied/closed pin reject.
- IC03 strict ordered item cursor and repeat retain original row without I/O.
- IC04 one retained aggregate deadline; earlier per-operation timeout cannot extend it.
- IC05 explicit per-item caps,16MiB retained debit across steps and failed copies.
- IC06 incremental and whole collection/index share original rows and index receipts.
- IC07 malformed/lost ACK, copied row, foreign writer/session and conflicts reject.
- IC08 default whole collection behavior and all existing confinement controls remain.

No stable subincrement, full runtime verification, acceptance or scientific result
is claimed by these controls. Continue full increment17 after this implementation.

## Sealed admission refinement before integration

An optional v6 collection plan binds the original coverage digest, absolute source
root and declared device/inode, all unit-scoped artifact expectations across every
admitted generation, per-file source/destination/media type, and a required run-level
collection metadata path. The three internal coverage paths cannot be file-copy
outputs. Metadata is bounded at1MiB; collection outputs at1MiB each/16MiB total.
Require explicit positive finite operation, per-unit teardown, collection, terminal
and drain budgets under D3 caps5/5/10/2/2s. Reserve the whole original unit universe's
teardown plus collection/report/drain before the admitted generation end; no timeout
is inferred. Worker independently rederives declarations and capacities before sinks,
then opens/retains the actual source pin before journal/writer creation. Init failure
must close that pin. Worker exit also closes it. Collection RPC/quiescence/terminal
coordination remains unfinished until implemented and verified end to end.

IC09 exact original coverage mapping includes inactive future output declarations;
missing/extra/required-flag/generation/cap mismatches reject before filesystem access.
IC10 metadata and explicit budget/capacity validation reject overflow before sinks.
IC11 actual worker pins before writer effects and rejects a replaced/missing source
at Init; default v1–v5 inputs/events remain byte compatible. These are admission
controls, not proof of later collection or full runtime closure.


## Actual collection protocol, authored before implementation

The genuine parent collect_outputs method takes its original RunBroker and one
original-session aggregate end<=the explicitly admitted collection budget. Matching
repeats return the original receipt; changed broker/end/plan or concurrent calls
reject. The end is fixed before cancellation/projection/transport, never reset by
per-item calls. Each RPC uses min(that end,now+original operation budget). Collect
requires terminal report/drain reserve inside the original generation end.

Cancel through the original broker before taking its full public projection. Retain
actual native Cancel ACK or original issuer death+reaping; cached local flags alone
never establish fencing. If the original Cancel result is uncertain, refine only
through its retained original revoke capability. Send one sealed inert collection-
context descriptor (explicit v6 purpose,<=1MiB, closed shape) containing full original
broker data, actual issuer death/reaping and the absolute aggregate end. Preserve
legacy v5 broker-projection admission and zero-rights behavior of other operations.
Worker checks original identity/inventory and its own retained issuance; no public
metadata creates process/root/cleanup authority. Unknown fencing remains unknown.

Begin binds the already pinned source, distinct original evidence root and complete
ordered declarations/caps once. Only a genuinely issued generation with actual
original direct-child wait, C1 empty and released, plus fenced future starts may
have its declared files read. Never-issued/inactive/unknown/live generations get
explicit unavailable rows; absence is not fabricated cleanup or applicability.
Unresolved direct waits remain separate gaps. No inode/name/PID discovery repairs
unknown authority. This path does not assume normal cleanup when only emergency
facts exist or require an inferred native retirement after actual issuer death.

Each collect item handles exactly its original next index, preserves missing/error/
unavailable outcomes and retained16MiB debit, verifies its actual copy/index ACK,
and returns bounded metadata only. Matching old indices replay no I/O. Create only
admitted destination parents under original no-follow roots. One fixed aggregate
end includes finish: write/index the complete bounded collection-result document,
then append/flush one factual run collect event. No run-terminal precedes collection.
Receipt contains original declaration/context/document digests and actual index/event
ACK; parent independently reconstructs expected document bytes from its retained
item ACKs and original context, rather than accepting a self-consistent invented
hash. Retain uncertain index/event/metadata failures without rewriting/retry.

IC12 actual original two-unit release/stop/cleanup then declared nested file copy,
metadata/index/event and closed-reader checks; matching repeat performs no RPC/read.
IC13 actual still-live/unknown/never-issued outputs remain unavailable and unread;
local close/revoke flags alone cannot gain trusted bytes. Fixed inert tables test
all quiescence branches without claiming native runtime results.
IC14 complete context/issuance/run/generation/digest/descriptor-purpose mismatch
rejects before output reads; legacy and v6 receive fault hooks still activate.
IC15 one aggregate end/per-RPC caps, cursor conflicts and bad/lost item/finish ACKs
preserve original facts and no replay. Inactive future declarations remain present.
IC16 required/optional missing and changed/symlink/oversized output remain distinct;
unknown output ownership never becomes optional-missing completeness.
IC17 normal collection metadata/event ordering, closed actual bytes and failed
writer/index/event cases do not confer complete lifecycle/cleanup/finalize credit.
All remaining full runtime/terminal/lazy issuance/coverage closure gates still bind.


Retained-input refinement: metadata retains the complete inert collection context,
not only its digest. This preserves original collection-time host/broker/fence fields
for later independent inspection even when the final broker snapshot differs.
The declared metadata cap still binds all context and item rows; overflow fails
without trimming. No productive descriptor, private scope or absolute source path
is serialized in this public artifact.

### Terminal lease controls (finding136; before implementation)

TL01 actual native cleanup-only transition keeps the original writer usable past
old bootstrap/authority leases without clearing the shared cancellation latch.
TL02 terminal mode rejects native birth, activation, watch and ordinary renewal;
BS10 rejects new requests. Missing/changed ACK is uncertain, never retry admission.
TL03 service lock/session/end errors have no new effects; operation and aggregate
ends remain fixed. Native authority death is not workload reaping evidence.
TL04 root-parent/storage death, lease/generation expiry still trigger original
native cleanup. Collection does not depend on a blocked writer renewing itself.
Full terminal dispatcher, writer closure and global M1 remain pending.
