# X-COM post-SESN workflow review

**Date:** 2026-09-26
**Scope:** Read-only review of capability 007 tasks T026–T041 and their upstream gates after the
user directed that future X-Verse work will not use SESN.
**Baseline:** `d244eeb3aa26f1b27d23d75fabc750380405269f` plus the preserved dirty workspace.
**Maturity:** Governance review only; no production software was implemented or accepted.

## Findings

| ID | Severity | Finding | Required disposition |
|---|---|---|---|
| XCOM-NOSESN-01 | BLOCKER | `AGENTS.md`, capability-007 planning, and ACC012 require SESN, while the user's current direction removes it. | Record a forward-looking governance decision and replace SESN-specific execution language without altering historical evidence. |
| XCOM-NOSESN-02 | BLOCKER | T025 is unchecked and no accepted T025 implementation exists in the current source baseline. T026 depends on its time authority, permit, and session lifecycle. | Complete and accept a successor T025 through the replacement workflow before T026. |
| XCOM-NOSESN-03 | MAJOR | T039 and T040 require SESN to run review and export the evidence bundle. | Replace them with a separate read-only review and repository-owned, exact-candidate evidence bundle. |
| XCOM-NOSESN-04 | MAJOR | Removing SESN would remove the named owner of SWE.1–SWE.6 work products, exact-candidate evidence capture, and repair sequencing unless replacements are explicit. | Assign those outputs to the direct engineering workflow and retain bidirectional traceability, candidate binding, host verification, and separate review. |
| XCOM-NOSESN-05 | MAJOR | T026 does not define bounded durability, partial-write recovery, disk-full behavior, retention, or journal recovery. | Add explicit journal semantics and verification before implementation. |
| XCOM-NOSESN-06 | MAJOR | T027 precedes the complete fail-closed checks in T028 and could create a temporarily unguarded emission path. | Implement and test the pre-emission authorization guard before action routing; then complete lifecycle closure behavior. |
| XCOM-NOSESN-07 | MAJOR | T029 does not explicitly cover journal-before-emission ordering and journal failure/recovery. | Expand negative, durability, lifecycle, and concurrency coverage. |
| XCOM-NOSESN-08 | MINOR | T012–T024 remain unchecked in the capability task list although accepted predecessor and observation records exist. | Reconcile completed slices against exact accepted revisions without treating source presence as acceptance proof. |
| XCOM-NOSESN-09 | MINOR | Generic Spec Kit prerequisite discovery currently resolves feature 020, not capability 007. | Address capability-007 artifacts by explicit path and rerun its consistency analysis after repair. |

## Task disposition

- Retain the technical intent of T026–T038.
- Strengthen T026, split the guard from the action paths in T027–T028, and broaden T029.
- Preserve T030–T034; “generated client” means Protocol Buffers generated code and does not imply
  SESN.
- Preserve T035–T038 with repository-owned evidence manifests and exact-candidate binding.
- Rewrite T039–T041 around independent review, an inspected evidence bundle, and explicit user
  acceptance.
- Replace the upstream SESN baseline tasks and dependency language before any further implementation.

## Required sequence

1. Record the workflow decision and amend forward-looking governance.
2. Reconcile accepted capability-007 slices and establish repository-owned engineering work products.
3. Complete and accept T025.
4. Implement T026–T038 with host-owned, exact-candidate evidence.
5. Conduct a separate read-only review and record findings before any repair.
6. Present the inspected bundle for explicit user acceptance.

## Review result

Capability 007 remains technically viable without SESN, but implementation is blocked until the
forward-looking governance and task workflow are amended and T025 has an accepted successor. Existing
SESN evidence remains historical evidence for the revisions it identifies; this decision does not
retroactively invalidate or relabel it.
