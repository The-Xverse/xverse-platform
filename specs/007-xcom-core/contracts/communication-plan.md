# Contract: Derived X-COM activation plan

The activation plan is a canonical, immutable runtime artifact compiled from an already normalized and
validated XDL graph. It is not edited by users and is not a second configuration language.

## Required content

- plan format version, canonical digest, generator version, and generation time;
- exact normalized XDL resource identities, API versions, source digests, and graph digest;
- communication contracts and schema/version references;
- endpoint roles and route graph;
- selected provider IDs and capability requirements;
- queue, ordering, reliability, deadline, retry, overflow, and backpressure policies;
- allowed observation points and payload policies;
- allowed stimulation actions and permit-policy references;
- clock domains, activation order, and deterministic diagnostics.

Unknown fields fail closed for the initial version. A plan with unresolved identity, schema, capability,
time, ownership, or policy input is inspectable but cannot activate. Canonical output must be
byte-identical for semantically equivalent normalized inputs.

The compiler may be implemented outside the C++ data path, but activation independently verifies the
plan version, digest, bounds, and required capabilities before allocating resources.

