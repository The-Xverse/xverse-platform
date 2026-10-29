# Implementation plan: public Maestro execution boundary

Branch: feat/022-maestro-public-execution. Baseline: platform
7fab6a290c3731533c2b88517158055c768b9d4e. Specification: spec.md.

## Technical context and allocation

Python >=3.11 implements the control-plane API alongside existing Maestro and
Argus Python modules. This preserves accepted XDL compiler/Argus contracts and
supports provider integration without placing industry code in the platform.
Performance-critical message exchange remains native C++ X-COM behind its public
provider/observation contracts. No replacement protocol or XDL grammar is introduced.
Fixed host bindings and original evidence live outside browser/project definitions.
JSON persistence is bounded and atomic; Argus owns its own canonical run evidence.
pytest verifies public contracts, actual owned child processes and native boundaries.
No new floating dependency or default network exposure is introduced.

## Constitution and architecture checks

Authorized edits are limited to platform public execution capability and Studio
integration. Existing legacy sources remain read-only. The new API must neither
export old private run types nor fabricate legacy readiness/review approvals.
Public XDL compilation is authoritative. Host-owned providers alone carry runtime
permissions. Native X-COM observations are distinct from physical effects and
solver coupling. Raw Argus evidence remains immutable. Every success claim must
have exact-candidate evidence; user acceptance is still required.

## Implementation structure

- src/xverse/maestro/execution/: public submission, inspection, host/provider
  contracts, lifecycle service, bounded process provider and evidence integration.
- src/xverse/maestro/__init__.py: deliberate public exports after verification.
- tests/maestro_public/: contract, owned-process, failure and integration checks.
- docs/engineering/maestro-public/: requirements/design/unit/maintenance/review
  and exact-candidate delivery records.
- specs/022-maestro-public-execution/: this complete capability work-product set.

## Staged delivery

1. Freeze contract and verify baseline boundaries/read-only consistency.
2. Implement public effective-input inspection and host binding admission.
3. Implement real per-element lifecycle through host providers, ownership and stop.
4. Persist original lifecycle records through actual Argus APIs and prove identity.
5. Exercise native X-COM adapter contract with actual C++ observations.
6. Separate review, repair, repeat affected checks and present exact candidate.
7. After explicit user acceptance, integrate accepted artifacts into main and verify
   assembled platform. Studio must consume that admitted candidate before full-goal
   acceptance; intermediate synthetic tests never complete the overall objective.
