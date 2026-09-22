# Execution permit contract

## Purpose and trust boundary

An execution permit is an explicit local, single-use operational approval record. It is required only
when a future runtime crosses from an inspectable lifecycle plan into a mutating action. It does not
authenticate a person, grant operating-system permission, or replace an organizational approval
system. Host account and filesystem permissions remain the access-control boundary in M3.

## Required bindings

- unique permit ID and nonce;
- canonical lifecycle-plan digest;
- exact catalog identity and environment identity;
- permitted action IDs and operation classes;
- approval evidence reference and non-secret issuer label;
- `notBefore` and `expiresAt` validity bounds;
- explicit exclusions and public-safety classification.

The runtime fails closed if the permit is absent, expired, not yet valid, already consumed, malformed,
or mismatched to the plan, catalog identity, environment, or requested action. Consumption is recorded
durably before the first mutating action and activates exactly one execution ID. Reuse cannot activate
a second execution. Later idempotent calls within that execution use the persisted activation and
remain limited to the permit's action set and validated ownership handles.

The validity interval governs activation and new start authority. Permit expiry or consumption never
strips containment authority for a resource already owned by the activated execution: observation and
handle-authorized stop/cleanup remain available. Planning never consumes or requires a permit.

## Deferred capability

Cryptographic signatures, identity providers, distributed authorization, revocation services, and
remote policy decisions require a separately specified security capability. M3 makes no such claim.
