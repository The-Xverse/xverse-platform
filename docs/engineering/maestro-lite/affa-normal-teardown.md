# Normal owned AFFA stop and cleanup

DRAFT detailed design before implementation; partial AF06/08/12/17/18/25 and
ML-SR-009–014/016–020/022–024. All full runtime/admission/acceptance gates remain.

Extend the original ReverseTeardown, not a replacement writer or metadata registry.
Its phase API already quiesces one declared leaf while unrelated units retain
admission; its run API closes all starts and processes reverse dependency order.
Use the exact original RunUnitIssuer and six-field handle, never a public reference
or caller-supplied observations. Acquire the original broker mutation lock without
waiting alongside the facade/owner locks; cancellation stays independent.

Normal stop: original worker appends/flushes stop intent; actual original native
STOP freezes, kills and waits its original direct child; original C1 then observes
empty membership; worker appends/flushes stop outcome. Retain native wait even if
subsequent C1 or evidence work fails. Original helper wait is a separate observation.

Normal cleanup: worker appends/flushes cleanup intent; actual native RETIRE makes
that old generation permanently nonproductive; original C1 removes its exact empty
boundary; worker appends/flushes cleanup outcome. Retain immutable original native
stop/retire ACKs. Old matching repeats return cached old-generation facts and never
acquire replacement-resource facts. A successful scoped phase does not Cancel the
global authority, close unrelated starts or imply an autonomous restart.

Use descriptor generation in the original request/result and validate it against
the original worker's actually retained M3 claim, not a counter. Keep worker
teardown state/handle/pending records generation-qualified, with current-unit aliases
only for existing scheduler/recovery consumers. This does not yet admit a future
permit or implement generation2 M3 outcomes; those remain required next.

Failure: original owner closes starts independently. A genuine native Cancel ACK
irreversibly fences starts even if freeze is incomplete; otherwise require actual
original issuer death/reaping before certifying C1 release. Preserve unknown native
workload waits and missing/unacknowledged normal records. Do not repeatedly invoke
one already-failed native operation as a substitute for the reserved fallback.
No cleanup success or complete evidence is inferred from signal delivery alone.

Expected real controls: normal reverse two-unit cleanup with eight actual normal
M3/Argus records and actual native waits; scoped dependent stop/cleanup leaves the
prerequisite live and global epoch unchanged; prerequisite stop with unquiesced
dependents rejects without mutation; stopped native authority or storage cannot
hold independent cancellation; native death precedes fallback release; damaged
normal ACKs remain incomplete even if original C1 release is confirmed.
