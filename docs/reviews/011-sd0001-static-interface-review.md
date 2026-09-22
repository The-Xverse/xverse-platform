# SD-0001 static interface evidence review

**Date**: 2026-09-21

**Reviewer**: Codex, separate architecture pass after the static audit and contract projection

**Scope**: Frozen source/configuration provenance, public-safe interface evidence, protocol and
serialization limits, lifecycle/readiness observations, compatibility contract projection, blocker
impact, and maturity claims. No executable or network operation was performed.

**Disposition**: Accept the static audit and companion projection as a stronger review baseline.
Reject closure of the interface, environment, readiness, retention, or vendor blockers. The audit
adds one explicit execution BLOCKER and several owner/runtime decisions.

## Findings

| ID | Severity | Finding / impact | Required disposition | Status |
|---|---|---|---|---|
| SI-R01 | BLOCKER | The exact gateway embeds a withheld private Zenoh endpoint outside selected configuration. A generic provider cannot safely override it, and the artifact is not environment-neutral. | The configurable-rebuild strategy was authorized on 2026-09-21 and recorded in ADR-0017. Produce and review the restricted patch and new artifact inside an approved immutable containment environment. | Strategy selected; artifact/environment blocker remains open |
| SI-R02 | MAJOR | Native-memory float encoding lacks byte-order/ABI/schema identity, while reverse routes forward raw bytes. Static consistency does not establish peer interoperability. | Approve a peer ABI or portable serialization contract and later verify the minimal bidirectional path. | Open; mapped to IA-R02/A16 |
| SI-R03 | MAJOR | Detached work, no router stop, no signal handler, and no readiness API prevent a graceful-shutdown or readiness claim. | Approve bounded external probe and process termination/containment semantics with explicit outstanding-work limitations. | Open; mapped to IA-R03/IA-R05/A16 |
| SI-R04 | MAJOR | Source logs may include restricted identifiers and payload values; the current generic process provider discards child output rather than producing target evidence. | Approve discard or restricted retention and use external structured probe evidence for public results. | Open; mapped to IA-R04/A16 |
| SI-R05 | MINOR | The Zenoh binary is digest-pinned but has no trustworthy semantic version metadata, and source test tools are outside the candidate bundle. | Retain digest-only compatibility limits or obtain provenance; separately pin any approved peer/probe artifact. | Open; mapped to IA-R06/IA-R07 |
| SI-R06 | ADVISORY | The static projection is protocol-specific and might be mistaken for X-COM implementation. | Keep it in `xverse-compat`; describe only a future X-COM edge until X-COM has its own accepted capability. | Open; non-blocking |

No defect in the audit documents permits unsafe action: all material findings map to existing declared
plan blockers, and the candidate validator continues to require the exact seven-code blocker set.

## Evidence-quality assessment

- **Revision binding**: PASS. Source commit/tree, selected configuration, executable, libraries, and
  relevant source units are digest-pinned.
- **Fact/inference separation**: PASS. Route counts, transformation classes, library identities, and
  lifecycle constructs are observed. Compatibility and runtime outcome remain explicitly unknown.
- **Public safety**: PASS. Exact routes, addresses, ports, payload values/layouts, and proprietary
  excerpts are absent. The machine summary records only classifications, counts, hashes, and limits.
- **Contract accuracy**: PASS. The projection describes artifact behavior without assigning payload
  transformation to the provider or inventing an API/version.
- **Maturity**: PASS. The evidence is `static-contract-evidence-runtime-unverified`; it supports no
  readiness, interoperability, parity, safety, performance, or production claim.
- **Repository direction**: PASS. Evidence and selection remain platform-owned; target-specific
  projection remains in compatibility; X-COM stays a later architectural target.
- **Production immutability**: PASS. Inspection was read-only and no legacy source or artifact changed.

## Gate checklist

- [X] Exact static evidence and machine-readable public summary are pinned.
- [X] Six selected routes are represented without publishing restricted identities.
- [X] Transformation, transport, serialization, lifecycle, and logging limits are explicit.
- [X] Candidate XDL remains unchanged and blocked; no static fact is promoted to runtime success.
- [X] Companion provider contract links to the public projection without implementing behavior.
- [ ] Owner accepts or replaces the compiled endpoint.
- [ ] Peer ABI/serialization and exact restricted mapping are approved.
- [ ] External bidirectional readiness and bounded stop/containment are approved and later verified.
- [ ] Raw-log discard/retention and Zenoh provenance are approved.
- [ ] Target-specific implementation authorization is recorded.

The later authorization covers the controlled rebuild mechanism and synthetic fixtures. It does not
authorize a target-specific provider, supply the restricted patch, or permit gateway/peer execution.

## Conclusion

The strongest safe result is a more precise blocked contract. SD-R05 is narrowed but remains open;
SD-R03, SD-R04, SD-R06, and SD-R08 are strengthened. T019/ACC015 and compatibility T012–T015 remain
open. Provider implementation or legacy execution would bypass unresolved evidence and is therefore
outside the authorized next step.
