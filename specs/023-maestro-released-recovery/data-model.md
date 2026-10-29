# Public data

RecoveryProviderBinding: installed provider ID and host-declared installation SHA256.
The complete tuple binds current host registry providers; no imported project input.
RecoveryInspection: immutable canonical bytes, digest, expected original claim
identity, host/runtime/recovery binding digests, source witness, original reader
verdicts and diagnostic codes, eligibility/reasons, original terminal/cleanup refs.
It is metadata only and cannot create ownership or authority.
HostRecoveryPermit: ID, environment/host/runtime/recovery binding, inspection digest,
approval reference, finite not-before/expiry and owned-simulation-recovery scope.
RecoveryRetirement: immutable separate receipt bound to exact inspection, original
claim/source and permit digests, host binding, time and version. It is not old state.

State dimensions: eligible/ineligible; retirement absent/verified/stale; original
read unknown; new activation independently admitted/refused. No collapsed health bit.
