# SD-0001 selection-closure readiness review

**Date**: 2026-09-21

**Reviewer**: Codex, separate architecture pass after closure-tool implementation

**Scope**: Candidate content lock, side-effect-free validator, negative tests, evidence-closure packet,
supplemental-reference reconciliation, Spec Kit traceability, and companion contract links.

**Disposition**: PASS for evidence intake and deterministic blocked-candidate validation. The artifacts
are ready for owner/environment/interface evidence. SD-0001 remains blocked and no target-provider or
legacy execution work may start from this result.

## Findings

| ID | Severity | Finding / impact | Required disposition | Status |
|---|---|---|---|---|
| CL-R01 | MAJOR | REF-001 places S-CORE before the gateway, while revision-pinned launcher evidence starts the gateway before S-CORE. Choosing either order could encode an incorrect prerequisite/readiness contract. | Target owner identifies the intended baseline and supplies observable dependency/readiness evidence; keep A14 and SD-R04 open until then. | Open; external evidence required |
| CL-R02 | MINOR | A validator cannot independently authenticate the lock file that tells it which digests to expect. | Pin the lock digest in the reviewed SD-0001 decision and rely on repository review/version history for this local prototype; a future artifact-registry/signature capability may replace this trust boundary. | Accepted limitation; lock digest pinned |
| CL-R03 | MINOR | A content-lock reader could expose or hash files outside the reviewed tree if authored paths or symlinks were trusted. | Require traversal-free repository paths below exact candidate/schema roots, reject final and intermediate symlink escape, and emit only a stable public failure. | Resolved in validator and negative test |
| CL-R04 | ADVISORY | The closure packet is Markdown rather than a machine-submitted approval object. | Keep it as a human evidence-intake checklist so it does not become a second deployment/configuration language; update XDL only after reviewed decisions exist. | Accepted for M3 |

No unresolved implementation/documentation BLOCKER exists. CL-R01 is an unresolved external MAJOR
within the already blocked readiness decision; the current candidate cannot be planned or executed.

## Architecture assessment

- **Spec Kit traceability**: PASS. C18, A14, SC-011, T017/T019, ACC015, research, plan, quickstart,
  validation, and the selected-component contract identify the closure flow.
- **Exactness**: PASS. The lock covers four XDL files, the Profile schema, resource versions, provider,
  artifact, catalog identity, plan digest, and blocker set. SD-0001 pins the lock digest.
- **Fail-closed behavior**: PASS. Exact validation succeeds only while reporting seven blockers,
  `plannable:false`, `executionEligible:false`, and `legacyExecution:false`; content drift, malformed
  lock data, traversal, and symlink escape fail before catalog use.
- **XDL centrality**: PASS. The lock is an integrity manifest and the closure packet is a review aid;
  neither represents topology, deployment, or lifecycle configuration.
- **Reference discipline**: PASS. REF-001/REF-002 statements remain documented requirements/context.
  They do not become owner approval, measured limits, live readiness, or verified compatibility.
- **Repository direction**: PASS. Platform owns the decision and intake packet; `xverse-compat` links
  to them and does not duplicate evidence or implement the provider.
- **Public safety**: PASS. The packet requests public projections and restricted references without
  storing people/contact data, private topology, addresses, payloads, mappings, or credentials.
- **Production immutability**: PASS. The validator reads only vNext candidate/schema files and never
  imports or executes a legacy artifact.

## Verification reviewed

- 90 platform tests pass, including four validator integration/negative tests.
- 17 companion conformance tests remain passing against platform API 0.4.0.
- The exact validator report passes with four resources and seven blockers.
- Doxygen covers 20 production Python files and indexes all 30 Python files without warnings.
- Python compilation, uv lock checks, Spec Kit prerequisite checks, local-link/placeholder scans, and
  public-safety scans pass.

## Gate result

The repository work needed to request external evidence is complete. T019/ACC015 and compatibility
T012–T014 remain open. Closing them requires direct values and approval for every row in the closure
matrix, followed by regeneration and separate review. Provider implementation then requires explicit
authorization, and any external lifecycle action requires a later exact permit.
