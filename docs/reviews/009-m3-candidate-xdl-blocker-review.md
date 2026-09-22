# M3 candidate XDL and planning-blocker architecture review

**Date**: 2026-09-21

**Reviewer**: Codex, separate architecture pass after implementation

**Scope**: Runtime Profile v0.2, declared planning-blocker derivation, the SD-0001 candidate XDL graph,
platform API 0.4.0 migration, deterministic tests, companion target contract, public safety, and the
legacy immutability/execution boundary.

**Disposition**: PASS for representing and reviewing the nominated candidate. The change resolves
SD-R02. It does not complete SD-0001, T019, ACC015, target-provider implementation, or legacy execution.

## Findings

| ID | Severity | Finding / impact | Disposition | Status |
|---|---|---|---|---|
| CX-R01 | MINOR | A declared blocker list could drift in order between authors even though semantic meaning is set-like. | Schema requires uniqueness; catalog derivation sorts and deduplicates codes before plan hashing and public projection. | Resolved in implementation |
| CX-R02 | MINOR | Introducing Profile v0.2 could silently alter the approved fixture contract. | v0.1 remains present and tested as plannable with no blockers; candidate tests use v0.2 explicitly. | Resolved by regression tests |
| CX-R03 | MINOR | A valid candidate graph could be misreported as executable once schema validation passes. | The test asserts all seven blocker codes, `is_plannable == false`, `execution_eligible == false`, and the exact plan digest; documents distinguish validity from authorization. | Resolved by tests and maturity language |

No BLOCKER or MAJOR implementation/documentation finding was discovered in this pass. The external
SD-R03–SD-R06 and SD-R08 findings remain open and map directly to plan blockers. Their closure requires
new evidence or owner decisions rather than code changes.

## Architecture assessment

- **XDL centrality**: PASS. The candidate is expressed as Component, System, Deployment, and Profile;
  the catalog remains derived and no parallel descriptor is introduced.
- **Domain neutrality**: PASS. Generic blocker mechanics remain in `xverse_xdl`; protocol-specific
  identities and limits stay in the candidate resources and `xverse-compat` contract.
- **Fail-closed planning**: PASS. Schema-valid data yields a deterministic inspectable plan while any
  declared blocker keeps it unplannable and ineligible for execution.
- **Version compatibility**: PASS. Runtime Profile v0.1 remains supported for the fixture; v0.2 is
  selected explicitly by the candidate and platform API is versioned to 0.4.0.
- **Dependency direction**: PASS. `xverse-compat` consumes the platform API and XDL identity; platform
  does not import the target-specific contract.
- **Production immutability**: PASS. Tests, validation, and documentation operate only on vNext files;
  no legacy checkout or executable is accessed.
- **Maturity/public safety**: PASS. Exact public hashes and summarized boundaries are retained; private
  addresses, credentials, source excerpts, restricted mappings, and historical path values are absent.

## Verification reviewed

- 86 platform tests pass, including v0.1 compatibility and exact SD-0001 v0.2 plan assertions.
- 17 companion conformance tests pass against exact `xverse-xdl==0.4.0` and its 22-file content lock.
- Both Spec Kit prerequisite checks resolve their active features.
- Both uv lock checks, Python compilation checks, and Doxygen coverage/build checks pass.
- Direct CLI validation accepts all four candidate resources; no lifecycle or external process runs.

## Remaining gates

The candidate still needs an immutable isolated environment, accountable owners, resource limits,
approved readiness and shutdown behavior, verified interface/protocol limits, durable restricted
retention, and vendor-binary disposition. The companion contract remains a reviewed draft until those
values close its open findings. Provider implementation and every legacy lifecycle action require
their own later authorization.
