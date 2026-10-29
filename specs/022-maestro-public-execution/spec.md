# Feature Specification: Public Maestro execution boundary

Feature branch: `feat/022-maestro-public-execution`
Created: 2026-10-29
Status: bounded public platform boundary accepted by the user on2026-10-29;
actual Studio/Autoverse integration remains open. See acceptance-decision.json.

The user authorized the concrete public execution-interface scope proposed in
Studio ADR-0034: specification, digest-bound inspection, start/stop, tests and
review in xverse-platform. Final platform acceptance remains the user's. This
capability is one prerequisite of the full Maestro/native-X-COM/Argus Studio goal;
it does not replace that goal with an owned-process fixture demonstration.

## User scenarios and testing

### US1 — Inspect exact inputs without execution (P1)
A trusted host submits explicit authored XDL and selection, binds admitted
provider installations, and learns the actual effective plan before starting.
Given edited inputs, unknown profiles, unavailable providers, missing permission,
or a plan mismatch, inspection rejects with no process, message or device effect.
An accepted inspection retains source-byte, input-semantic and compiled-plan
identities separately. A changed host binding invalidates the inspection.

### US2 — Run and stop through public interfaces (P1)
A host starts the inspected experiment idempotently and follows actual per-element
preparation, dependency scheduling, start, observation, stop and cleanup outcomes.
Start retries create exactly one run. Failed readiness never becomes running.
Partial startup triggers bounded reverse cleanup; unknown ownership cannot authorize
signals, deletion or new stimulation. Inspecting/reconnecting cannot replay start.

### US3 — Follow real evidence across services (P1)
Maestro emits actual lifecycle decisions through Argus with the same run, plan,
logical-element, operation and correlation identities used by native X-COM data.
A reader can follow an explicit correlation/causation link; unrelated receipt times
never imply causality. Evidence failure is independent of workload termination.

### US4 — Integrate existing providers without editing production assets (P2)
A trusted host registers reviewed, versioned provider implementations and fixed
installation bindings. Project content selects compatible declarations, never
executable host instructions. A real owned-process provider verifies the public
boundary. Studio later binds the existing Autoverse interfaces and native X-COM
adapter using the same public contract; the platform contains no industry dispatch.

## Functional requirements

- MPX-FR-001: Export a documented public execution API requiring no private run type.
- MPX-FR-002: Compile/validate supplied XDL through authoritative public APIs and
  retain source-byte, input-semantic and compiled-plan identities without coercion.
- MPX-FR-003: Inspection is side-effect-free and bounded; exact effective-input
  equality and current host/provider pins are required before start.
- MPX-FR-004: Executable bindings, environment, provider permissions, resource and
  time budgets are supplied only by a trusted host outside project content.
- MPX-FR-005: Maestro owns dependency scheduling, per-element lifecycle and bounded
  rollback/stop/cleanup through admitted providers; readiness is observed separately.
- MPX-FR-006: Start and stop have bounded idempotency, stable operation identities,
  state-version checks, conflict handling and no dispatch replay after uncertainty.
- MPX-FR-007: Process/resource identity requires birth and installation witnesses;
  unknown ownership remains unknown and confers no signal/delete authority.
- MPX-FR-008: Actual lifecycle and communication records are persisted through
  Argus, preserving correlation, causation, logical identities and original clocks.
- MPX-FR-009: Reader/evidence failures, missing observations, queue loss and cleanup
  uncertainty remain explicit; no synthetic success or cross-clock mapping.
- MPX-FR-010: Native X-COM integrations use its C++ public provider/observation
  contracts. Lite flow emulation and Zenoh-only traffic cannot satisfy this claim.
- MPX-FR-011: The existing private trusted-host runtime, lane approvals, native
  containment permits and readiness gates are not reinterpreted or auto-approved.
- MPX-FR-012: Delivery includes public exports, documentation, bounded diagnostics,
  exact-candidate verification, separate review and user acceptance before integration.

## Key entities

CanonicalSubmission; HostBinding; ProviderRuntime; EffectiveInspection;
ExecutionHandle; LifecycleObservation; EvidenceReference. See data-model.md.

## Success criteria

SC-001: Public client imports no private run constructor and changes no production
companion source while performing inspection/start/read/stop.
SC-002: Negative admission cases cause zero provider lifecycle/message/device calls.
SC-003: One actual native experiment yields Maestro lifecycle, native C++ X-COM
exchange and Argus verification with matching identities and explicit correlations.
SC-004: Retry, failed readiness, partial launch, ownership replacement, output
pressure, writer failure and stop failure retain truthful bounded outcomes.
SC-005: Exact reviewed candidate is presented for explicit user acceptance, then
integrated into platform main and assembled verification is retained.

## Compatibility, fidelity and exclusions

New prototype API; existing public preparation and existing closed runtime paths
remain unchanged. Initial host execution evidence is native Linux with approved
owned virtual/simulation resources. Windows, arbitrary devices, physical effects,
distributed execution, real-time guarantees and deterministic replay are not claimed.
The actual Autoverse/Studio integration remains a required downstream deliverable
of the user's overall goal. See traceability.json for explicit REF-002 dispositions.
