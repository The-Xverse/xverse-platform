# Catalog contract

## Purpose

The catalog is a deterministic read-only index derived from a closed set of normalized XDL resources.
It has no independently authored catalog document or new XDL kind. Each entry follows one Deployment
binding through its System component instance to an exact Component and joins the binding's
`io.xverse.runtime.compatibility` Profile payload.

## Required semantic fields

| Area | Contract |
|---|---|
| Catalog identity | Exact Deployment identity plus binding ID; unique in the supplied graph. |
| Logical identity | Binding logicalRef → System componentInstance → exact Component resource. |
| Profile | Exact compatible Profile owning `io.xverse.runtime.compatibility`; payload occurs only on the Deployment binding. |
| Provenance | Deployment artifact digest/source plus resource provenance or explicit unavailable/withheld marker. |
| Realization | Binding class, target, resources, artifact references, and physical asset where applicable. |
| Interfaces | Exact Component/System interface and endpoint references plus declared contract limits. |
| Lifecycle | Core lifecycle declaration plus typed Profile actions, ownership, readiness, timeout, and failure semantics. |
| Evidence | Evidence references, maturity, fidelity/compatibility limits, and public-safety classification. |

## Invariants

- Entries are derived locally, deterministic, revision-pinned, and unique by catalog identity.
- Digest-identical artifacts may be shared by multiple entries; a shared artifact does not merge their
  lifecycle identity, state, ownership, or evidence.
- Entries cannot contain raw credentials, private infrastructure, or proprietary payload/source text.
- Unknown or withheld fields do not imply executable defaults.
- An entry may be catalog-valid while blocked from planning or execution. Missing lifecycle data or a
  secret requirement blocks planning; a missing execution permit blocks only execution.
- Runtime Profile v0.2 may carry unique stable `XVERSE-PLAN-*` blocker codes for unresolved decision
  evidence. Derivation sorts and preserves them in the plan and public projection; they cannot waive
  schema validation, make a plan plannable, or confer execution authority.
