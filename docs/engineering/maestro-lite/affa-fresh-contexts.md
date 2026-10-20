# Fresh M3 contexts in the surviving original run

DRAFT implementation design before code. Extends affa-generation-composition.md;
AF17 v2 and all capability024 requirements remain binding. Normal teardown is a
prerequisite, not a substitute for the complete selected increment17 scope.

## Admission and immutable approval inputs

Extend the original sealed PersistenceInput with an explicit optional version2
future-context list. Each entry is an exact PermitBinding and PermitApproval for
one declared unit and consecutive future generation. Preserve the accepted v1
initial-generation validation API and default bytes when the list is absent.
Validate every future entry's run, execution, unit, generation, lifecycle, plan,
provider artifact, environment, permit content, actions, exclusions and validity.
Require unique execution IDs, permit IDs and nonces across initial and future
contexts; bind at most128 total unit generations. An integer native generation
budget is insufficient. Revalidate the original selected approval at actual use.
The trusted admission owner supplies these values; controllers supply none.

Keep one original PermitSession, journal and Argus writer. Retain its initial
checked tuple unchanged and separately pin all admitted future contexts. Select
one unit's next exact context through an explicit original worker generation
operation; do not reset the worker or change the global initial generation.
Validate a selected claim against its own retained binding generation. All old
receipts and journal facts remain retained, including already consumed nonces.

## Original worker transition

Before changing the current unit context, the original worker must revalidate the
entire actual journal and Argus history, the old claim, actual normal stop and
cleanup outcomes, the old handle and original boundary digest. The request comes
only from a retained original broker statement. PersistenceClient accepts that
exact statement while active in the same broker; copied/public values are not
accepted as authority. The broker verifies its original native STOP/RETIRE ACKs
and actual original C1 release before issuing the statement. Actual helper reaping
is not a substitute for either workload wait or old boundary release.

The worker consumes the exact pre-admitted next permit and writes a genuine M3
intent and Argus mirror/flush before returning. Uncertainty irreversibly closes
new starts; a consumed permit is never retried as fresh. Historical claims remain
in a generation-qualified registry used by all consistency checks. Current-unit
aliases exist only for operations on the currently selected original execution.

## Native advance and readiness

The broker creates one fresh C1 leaf under the currently acknowledged native epoch
and WATCHes its original descriptor before ADVANCE. Unchanged sealed image/recipe/
cwd/action pins, exact new execution/claim/flush and new C1 identity reach the same
original AFFA. ADVANCE requires the old native retirement, actual boundary removal,
exact next generation and admitted budget. Its genuine ACK authorizes the original
C1 bridge. Neither a worker consumption nor a directory alone permits Stage.

Retain issuers by (unit,generation) and keep a separate current-unit mapping.
Old handles, STOP/RETIRE ACKs and terminal cleanup results remain old-generation
facts. They never gain the replacement's authority. An explicit successful advance
retires the affected readiness binding and requires a new binding and real probes;
no existing ready bit authorizes a new execution. Preserve unrelated live units,
original handles, claims and probes. Shared epoch changes burn pending tickets.

Normal outcome, teardown, recovery, scheduling and closure consumers must account
for actual generation/execution identity. Old stopped/cleaned state cannot authorize
the new generation. Do not silently discard old history to satisfy a consistency
check. No Argus root is reopened, and no new author approval is inferred.

## Required verification and remaining composition

Exercise actual original storage+AFFA+C1 with a leaf generation1→2→3 while its
prerequisite stays live; compare actual normal old-generation records and new
execution/permit consumption, native epochs and live dependency probes. Reject
missing, expired, duplicated or reused future approval/nonce, missing old cleanup,
wrong generation/epoch and stopped storage/AFFA. Preserve unknown waits and missing
normal evidence. Then compose transitive-dependent quiescence/restart, replaceable
controller sessions, dispatcher/run closure and public U7/U8 facts before freezing
increment17. Full runtime admission, full regression, independent review, explicit
acceptance and main integration remain pending. No experiment or factory admission
is implied by this design.

## Concrete implementation sequence

1. Add a pure future-context validator over exact initial and future binding/approval
   values. Initial validate_permits remains generation0/1 only. Require known units,
   consecutive per-unit successors, exact full approval binding, unique identities
   across every admitted context and the existing joint128-generation bound. Encode
   optional contexts only in sealed version2; absent contexts keep version1 bytes.
2. Preserve PermitSession's original initial checked tuple and validated preparation
   proof. Separately retain admitted future tuples and issued receipts. A successor
   claim must use its own original binding generation for live validation; it must
   also match the actually retained normal old stop/cleanup records before atomic
   consumption. Neither public metadata nor an integer budget supplies this witness.
3. Keep current worker claims by unit, plus an append-only historical registry.
   Existing consumers select current claims; _history/_mirrors and event capacity
   include every original historical claim and mirror. Use generation-qualified
   sample/teardown stores with current-unit aliases. Selecting a new original
   execution retires its old current sample/state alias, never the historical facts.
4. Add one original broker generation statement, active only during the original
   operation. PersistenceClient checks its exact type/identity and actual broker
   registries, STOP/RETIRE ACKs and C1 release before generation RPC. The worker
   verifies original old claim/handle/normal records/mirrors before selecting and
   consuming the exact pre-admitted successor. Retain new M3 intent and Argus flush
   before returning; never reset/reopen either evidence owner.
5. Create/WATCH the fresh original leaf under the currently acknowledged creation
   epoch. The same AFFA ADVANCE receives the actual fresh intent/flush and C1 digest;
   retain its genuine connection receipt. ADVANCE already records that generation's
   intent natively: subsequent Stage must validate that original receipt and MUST
   NOT send a duplicate INTENT. Continue revalidating actual storage before Stage
   and Arm/Release. The original operation end is never extended.
6. Register issuers by (unit,generation), keeping a separate current-unit mapping.
   Retire only affected readiness/attempt applicability on successful advance and
   bind/probe the new original issuer. Old terminal STOP/RETIRE/cleanup facts remain
   usable only for their old handle/generation. Old matching teardown repeats cannot
   acquire replacement facts. Existing legacy backends retain generation1 rules.
7. First exercise a declared leaf1→2→3 while its prerequisite retains original
   execution/handle and live actual probes. Then compose reverse-order transitive
   dependent quiescence and explicit admitted restart. Shared native epoch advances
   invalidate unused tickets, including unrelated pending starts; already running
   unrelated executions remain owned. No whole-run restart substitution.
8. Update actual scheduling/recovery/closure consumers and U7/U8 issuance facts,
   then add the admitted replaceable controller channel/session. Complete selected
   M1, runtime cases and independent review before a stable increment17 freeze.

This sequence is prospective design, not an implemented API or new approval.
The preparation-proof optimization changes no fresh-context permission boundary.
