# Lifecycle evidence journal contract

## Record pairs

Every mutating lifecycle action has a stable action ID and two append-only records:

1. `intent`: persisted before the provider action, binding execution ID, plan digest, catalog identity,
   permit ID, action, expected ownership effect, and monotonic sequence number;
2. `outcome`: persisted after the provider returns, binding the same identifiers to observed result,
   ownership handle reference including provider ID/kind, diagnostics, timestamps, and evidence limitations.

Observation-only records use the same execution/action identity but do not create ownership.

## Failure semantics

- Intent persistence failure blocks the mutating action.
- Outcome persistence failure marks the run `evidence-incomplete` and blocks every new start.
- Observation and handle-authorized stop/cleanup remain allowed so an already-owned resource can be
  contained safely; their persistence failures remain fatal diagnostics.
- Restart enters observation-only reconciliation. The provider must revalidate the persisted handle
  before any mutation; an unverifiable handle is treated as unowned.
- An incomplete journal cannot support a successful lifecycle or compatibility claim.

## Public-safety projection

The runtime evidence model may retain restricted references in an approved local environment. Any
repository/public report replaces secret values, private addresses, sensitive paths, and proprietary
payloads with explicit withheld markers while preserving identity, outcome, and limitation structure.
