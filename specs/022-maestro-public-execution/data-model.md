# Public execution data model

CanonicalSubmission: caller run identity, explicit document names/bytes and exact
System/Deployment/Scenario selection. Contains no host command or credential.
HostBinding: host identity, installed provider IDs/versions/content digests,
allowlisted fixed installations, permitted operations, resources and finite budgets.
Canonical bytes/digests bind the immutable host configuration outside submitted XDL.
ProviderRuntime: trusted implementation whose inspection and lifecycle operations
return versioned receipts for actual readiness, resource ownership and cleanup.
EffectiveInspection: immutable source-byte digests, input-semantic digest, compiled
plan digest/body, logical bindings, current host/provider pins and bounded expiry.
ExecutionHandle: stable run/operation identity, state version, inspection identity,
per-element observed lifecycle, evidence references and cleanup outcomes.
LifecycleObservation: original event ID, run, element, phase, observed outcome,
source/receipt clock fields and explicit correlation/causation IDs when known.
EvidenceReference: actual Argus run identity, original record/artifact references,
reader identity, recorded status and independent assessed status/reasons.

States distinguish inspected/rejected, preparing/ready/running/stopping, stopped,
failed and unknown. State version ordering does not establish cross-clock causality.
Inspection never owns a resource. A running handle cannot acquire new authority by
metadata changes or a repeated request. Uncertain dispatch cannot be replayed.
