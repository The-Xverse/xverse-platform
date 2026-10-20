# Joint admission and bounded runtime entry

Status: DRAFT implementation refinement, before code. Capability024 D1/D3 and
ML-SR-001/005/009–013/016–024 remain governing. Finding262 records the current gap.

Implement the complete bounded runtime entry over the existing original BS17,
PersistenceInput v6, RunBroker, FiniteDispatcher and RunClosure. The end state is
the draft's blocking whole-lifecycle start plus explicit concurrent stop/restart,
matching collect and retained terminal results. One original registry owns each
run and permits no reconstruction/adoption from public metadata. Existing accepted
preparation imports and private construction paths remain compatible.

First add a joint read-only admission preflight. Its inputs are existing original
preparation/persistence/bootstrap values plus separately supplied bootstrap
authorization and facility-attestation data from the trusted admission owner.
Require externally held authorization/facility/design/implementation/environment
digest pins; no digest taken from the submitted bundle can replace those pins.
An externally approved facility attestation identifies all nine original full
runtime-case receipts, exact helper artifacts, host environment and enforcement
claims. Validate its bindings and shape, never execute or manufacture its receipts.
The trusted owner remains responsible for receipt verification, source-parent
dispositions, operator approval and current host suitability. These records are
not self-authenticating approval, a kernel capability or evidence of completeness.

Bind exact existing v6 persistence and BS17 bytes and rederive the original
configuration. Check run/lifecycle/session/cleanup-end equality, exact bootstrap
approval reference, helper/environment pins, aware UTC start validity, original
host lease/end and complete scheduling/collection terminal reserve. Never compare
UTC to host-monotonic values. Start validity may expire before cleanup authority;
cleanup never extends start authority. Reject before any helper/sink/C1 mutation.

The preflight returns inert immutable descriptive pins with ready_for_execution
false. Do not export public start until the original launcher, live admission
revalidation, run registry, control APIs and terminal path are integrated and
verified. Future start must still validate original descriptor identities, exact
executable bytes and current facility/approval at use; preflight cannot replace
those checks. No automatic factory run or author acceptance follows.

Python remains allocated to bounded host control/admission; existing native BS17/
AFFA retain containment, epochs, launch and direct waits. No new XDL dialect,
data-plane implementation, Argus mutation, public CLI or scientific parameter.
Synthetic unit vectors exercise the validator only and must never be reported as
actual M1 receipts or runtime admission. Full entry, complete M1/environment,
source-parent validation, regression, review and stable17 remain open.
