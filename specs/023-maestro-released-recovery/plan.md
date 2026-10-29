# Plan

Python implements bounded control-plane recovery beside the accepted Python public
Maestro/Argus APIs. Native C++ X-COM is unchanged; no new dependency or protocol.
Keep one module for public immutable receipts, permits, source verification and
retirement persistence. The lifecycle service owns locking and Start admission.

Public design: RecoveryProviderBinding, RecoveryInspection, HostRecoveryPermit,
RecoveryRetirement; PublicExecutionService gets optional recovery_bindings and
inspect_recovery/run retirement/status operations. A trusted host configures exact
provider installation pins; these are declared pins, not an attestation by Argus.
Runtime root identity and actual source witnesses are independently observed.

Tasks: specification/design/read-only consistency; implementation; owned-process
and adverse verification; separate read-only review; repair/reverify if required;
exact-candidate user acceptance; isolated main merge/assembled verification; Studio
pin/integration plus complete live experiment. Never automatically accept a candidate.

Bounds: claim8192B; manifest1MiB; original4096events of16KiB; source64MiB plus at
most64artifacts in the actual reader; inspection/receipt32KiB; root1024entries,
128claims,256retirement records and8perclaim; permit lifetime<=300s. Unknown or
exceeded bounds fail closed. No provider callback is used in inspection/retirement.
Default recovery_bindings=() leaves accepted legacy behavior fenced.
