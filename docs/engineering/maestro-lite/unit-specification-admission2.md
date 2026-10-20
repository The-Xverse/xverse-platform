# U2 permit admission and M3 journal claim unit specification

Revision: ML3-ADMISSION2-2026-10-18-v2. Status: partial implementation candidate.
Basis: existing ML-SR-005/006/023/024, U2, and the current descriptor/C1 downstream contract.
ADR: ADR-ML3-ADMISSION-0001. No additional system requirements are introduced.

| Unit/endpoint | Inputs and output | Invariant and failure |
| --- | --- | --- |
| `validate_permits` | Prepared value, original normalized XDL/compiler result, explicit run, immutable M3 bindings/approval facts, aware validity observation → checked tuples | Recompile and compare the complete prepared value; exactly one binding per unit; unique execution/permit/nonce; exact action/class sets; recognized exclusions only; strict types and validity. Pure: no journal/provider/lock/ticket operation. |
| `permit_digest` | Actual immutable M3 ExecutionPermit → private exact-content SHA-256 | Reject mutable scope sequences. The digest includes private nonce and is not a public authority token or authenticated approval. |
| `PermitSession` | Fully checked tuples and actual FileEvidenceJournal → original private coordinator context | Snapshot mutable compiler plan while retaining immutable XDL/envelope values. Read existing consumption; keep execution readiness false. In-memory substitutes cannot establish durability. |
| `PermitSession.claim_start_intent` | Exact unit and fresh aware validity observation → redacted IntentReceipt after durable claim | Revalidate before use; no provider callback or ticket; persistence exception returns no receipt. Pending intent without outcome consumes the permit. Restart/adoption remains unsupported. |
| `InMemoryEvidenceJournal.claim_intent` | Pending exact EvidenceRecord → one sequenced record | Under existing thread lock reject duplicate permit ID, nonce or execution, unknown history and invalid types. Fixture evidence only. |
| `FileEvidenceJournal.claim_intent` | Pending exact EvidenceRecord and owned file journal → one fsynced record | Same consumption decision and persistence under existing thread/process locks. Strict history parser rejects malformed/duplicate wire identities. Journal/directory fsync and store marker publication precede return. |
| M3 store identity helpers | Existing lock descriptor, retained journal/parent/lock identities, prefix and minimum ordinal | Never reset a nonempty marker. Before append reserve minimum sequence; after append bind exact prefix. Loss/replacement/truncation and uncertain publication keep consumption unresolved. No second nonce database or implicit ownership recovery. |

Exclusion matching is against declared plans, not proof of actual artifact behavior. Positive
fixture cases exercise explicit synthetic approval-owner inputs; they do not issue real approvals.
Aware UTC validity is distinct from host deadlines and simulation ticks. File locking/fsync can
block at the kernel, so this unit does not close the U3 watchdog obligation.

Revision 2: revalidate the complete initial set at the first claim and the selected
unit at later claims. Previously used start validity never becomes teardown authority
and never invalidates another unit's fresh permit. Persistence/read failures latch the
original session's claims closed. A newly constructed session must reject unresolved
prior intent scopes despite fresh permit/nonce/execution identities. This does not
reconstruct ordinary resource ownership or authorize recovery; U3–U5 remain responsible.

Verification uses real accepted M3 values and file journals, independent bounded child processes
contending at a barrier, reopen and replay attempts, injected fsync/partial-publication failures,
and missing/replaced/truncated/corrupt history. No provider or production workload is launched.
Negative checks require no new intent bytes or explicit unresolved consumption, rather than
fabricated successful cleanup. The existing platform regression and source-excluded wheel
consumer must pass on exact current source identities.

All 24 requirements and 18 allocation-only source parents remain retained in the successor
trace index. All full-scope runtime cases, bootstrap/fence/authority evidence, source semantics,
trusted whole-project trace, lifecycle coverage, acceptance and merge remain pending.
