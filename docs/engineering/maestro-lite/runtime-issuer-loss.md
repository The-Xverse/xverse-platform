# Whole-runtime cleanup after issuer-registry loss

Status: partial owned repair; full increment17 remains unfinished. Architecture
and authority boundary precede the correction in
[ADR-ML3-RUNTIME-0009](ADR-ML3-RUNTIME-0009.md), refining the existing original
cleanup-context contract. External024 v2 remains DRAFT.

Whole blocking start passed its original broker explicitly to RunClosure,whose
constructor demanded intact ordinary issuer registries. Losing the generation
registry therefore blocked primary cleanup construction even though original
cleanup capabilities survived. Two actual windows reproduce this: native STAGED
before handle publication,and after the first productive workload release.

The correction replaces that constructor's ordinary `_holder` call with the
existing `_cleanup_context`. Exact broker type,original bootstrap/session/owner/
storage/authority pins and any original derived-broker identity remain required.
Ordinary broker/issuer operations still reject registry loss. A copied broker
rejects before native I/O. No handle,registry,process,permit or new start authority
is reconstructed or adopted.

Original a45734 fails both controls per source/wheel phase: four missing primary
closures require four external original-root fallbacks. Those results remain
immutable. Repaired b32326 passes both controls per phase with four actual primary
closures,zero fallback,original helper/root waits and C1 release. Matching whole
start/collection retains the result without another process; the unrelated
sentinel retains original membership,scope and fresh heartbeats. Unknown direct
workload waits and incomplete normal records are preserved,not called complete.

The affected verification includes closure,startup,entry,issuer loss,registry and
authorization-window controls. b stops after a nominal wheel timeout and teardown
error; c58542 executes only the six planned checks skipped by that stop. b/c have
identical272 frozen inputs and81 packaged Python/C files. Current selected counts
are source85 passed,wheel84 passed/one failed/one teardown error. The failed test
was not retried. Current audits retain162 absent owned environment roots and823
verified M3 references. Runtime and sentinel managers share their per-test harness
environment root; they are not counted as separate environment receipts.

337 retains a source-generation1 teardown timeout in the nominal registry wheel
case.338 separately retains disposal rejection: original root/helper waits and
C1 release are observed,while PersistenceClient.dispose reports ML-PERSIST-RETAINED.
Its local drain receipt is absent or unreaped; exact local value was not retained.
Both causes remain UNKNOWN. A later physical wait must not silently rewrite an
earlier unknown result. Investigate original-capability late wait and partial
disposal/retry before changing that path; do not extend ends or infer a repair.

The first auditor wrongly counted managers as environment roots; its original
failure/v2 correction remain336. The first new CAPA snapshot reused an old ADR
evidence ID; that intermediate is rejected340. The
[corrected register](evidence/affa17/capa-20261019-runtime-issuer-loss-v2/register.json)
validates37 records/198 bindings and passes an explicit170-parent-binding check.
The bad intermediate fails that check. All effectiveness remains NOT_DEMONSTRATED;
no independent cause confirmation,automatic CAPA engine or025 integration follows.

The [partial trace](evidence/affa17/runtime-issuer-loss-partial-traceability.json)
retains24 software requirements/18 allocation-only source parents and adds eight
current endpoints/24 links. Original30 pairs/90 endpoints,nine complete runtime
cases,seven P3 tasks,source semantics,M1/environment,whole-platform regression and
separate full review remain open. The earlier1495-test source/wheel attempt remains
failed evidence for its exact pre-repair snapshot; this affected scope does not
relabel it. No stable17 commit,acceptance,merge or scientific result is claimed.

Next: investigate338 with actual original wait/capability identity and honest
partial disposal effects. Sol/high recommended. The
[continuation](evidence/affa17/continuation-runtime-issuer-loss-20261019.md) retains
exact identities,failed attempts and authorization limits.
