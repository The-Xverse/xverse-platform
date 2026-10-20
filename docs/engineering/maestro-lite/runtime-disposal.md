# Original runtime resource disposal

2026-10-19. Partial capability024 candidate under ADR-ML3-RUNTIME-0010.
The original red snapshot,failed verification setup and passing repair remain
separate. No full runtime case, stable increment17 or acceptance is claimed.

Persistence disposal can verify the original BootstrapChild wait after its
client-local drain expired. This releases only local descriptors and preserves
the earlier unresolved drain, RuntimeResult and startup outcome. A live child
still rejects. Plain Popen clients retain their existing local-drain requirement.
The original client lock serializes disposal and normal requests; successful
matching disposal is retained, and ambiguous close failure remains unresolved.

Broker admission now pins a finite single-use image-disposal state. The first
close requires the original cleanup context and actual authority-child wait.
Every original image/cwd/recipe descriptor is consumed before its close attempt;
remaining original descriptors are attempted after an individual close error.
Successful replay needs no already-closed client transport. An ambiguous close
error is retained and never authorizes retrying a consumed descriptor number.
This preserves cleanup after ordinary issuer loss without granting adoption.

Original `runtime-disposal-20261019a` has three failures in each phase: late
original-root helper wait, repeated broker disposal, and entry retry after a
one-shot client-disposal rejection. The owned guard prevented four attempted
closes of reused canary descriptors. All six needed separate external local
disposal. The audit retains six absent environment roots and316 M3 links.

The corrected `runtime-disposal-20261019c` passes four new controls and all157
selected affected checks per source/wheel phase (314 executions). Six positive
disposal cases complete through the product without fallback. Two deliberate
actual-close-then-error cases retain unresolved disposal and separate external
local cleanup; no canary close is attempted. The audit checks81 packaged Python/C
sources,only two changed,298 absent environment roots,1264 M3 links and28 explicit
source-projection gaps. It does not promote normal evidence or unknown waits.
Intermediate b failed its fresh-environment guard before build/install/pytest;
its archive and setup-failure receipt remain retained under finding345.

The [partial trace](evidence/affa17/runtime-disposal-partial-traceability.json)
retains24 requirements and18 unvalidated source parents,with six endpoints/24
links for this delta. The CAPA successor validates39 records/210 bindings and
preserves all198 prior bindings.338,344 and345 are local FIX_CANDIDATE/HYPOTHESIS;
337 and the nine older unknown causes remain unresolved. All effectiveness stays
NOT_DEMONSTRATED; no automatic CAPA engine or capability025 integration is claimed.

One complete current-candidate regression is now running as
`integrated-maestro-20261019b`, original exec97867,1501 collected per phase. Its273
frozen inputs are byte-identical to c. It is pending,not passing evidence. The
previous full a's five failures remain immutable. Follow the
[continuation](evidence/affa17/continuation-runtime-disposal-20261019.md).
Other partial client/root close failures,complete crash/runtime matrices,M1,
source-parent semantics and separate complete review remain open. Actual M1
admissions0; main and the canonical note are unchanged.
