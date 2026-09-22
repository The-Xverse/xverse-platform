# Contract: `io.xverse.xcom` XDL Profile

X-COM policy is represented through a versioned Profile and existing XDL `extensions` locations. The
Profile payload uses a closed discriminator so one schema can validate the permitted attachment forms:

- `interface-policy`: interaction kind, schema/encoding constraints, and semantic compatibility;
- `flow-policy`: ordering, reliability, deadline, retry, queue, overflow, and observation points;
- `network-provider`: required provider capabilities and declared fidelity/limitations;
- `observation-policy`: filters, metadata/payload access, bounds, and validity effect;
- `validation-policy`: allowed stimulation actions, injection points, service-emulation eligibility,
  time policy, quotas, and permit-policy reference.

Each payload records `schemaVersion`, `kind`, and the identity it decorates. The compiler verifies that
the discriminator is legal at that XDL location and rejects duplicate or conflicting policy. Unknown
fields and unsupported versions fail closed.

The Profile never stores provider addresses, credentials, validation permits, live handles, or tool
sessions in logical Component resources. Environment-specific realization remains on Deployment
network/binding extensions; scenario-specific validation policy remains on Scenario extensions.

