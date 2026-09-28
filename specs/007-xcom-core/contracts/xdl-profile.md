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

## Profile v0.1 payload grammar (normative)

`xdl/profiles/xcom-v0.1.schema.json` is the closed, Draft 2020-12 schema for the `io.xverse.xcom`
Profile v0.1 payload. It is attached as the value of the `extensions["io.xverse.xcom"]` member of a
legal XDL resource, or supplied as the payload selected by a Profile resource's `spec.schemaRef`.
It is a payload grammar for existing XDL extension points; it does not define a configuration
language of its own.

The payload is a closed object. It requires `schemaVersion`, `kind`, `target`, and `policy`, and it
rejects any other member (`additionalProperties: false`). `schemaVersion` is the constant string
`"0.1"`. `kind` is one closed discriminator whose value is exactly one of `interface-policy`,
`flow-policy`, `network-provider`, `observation-policy`, or `validation-policy`. `target` is the
decorated logical identity: a closed object requiring `apiVersion` (constant
`"xverse.io/xdl/v1alpha1"`), `kind` (one of `Component`, `Deployment`, `Scenario`), `namespace`,
`name`, and an optional `version`.

The permitted `policy` object is selected by `kind` and is closed for that form:

- `interface-policy` requires `interactionKind` (`signal`, `message`, or `service`), `schemaId`,
  `schemaVersion`, `encoding`, and `semanticCompatibility`.
- `flow-policy` requires `ordering`, `reliability`, `deadlineMs`, `retry`, `queueDepth`, `overflow`
  (`drop-oldest`, `drop-newest`, `coalesce`, `lossless-backpressure`, `reject`, or `fail-closed`),
  and `observationPoints`.
- `network-provider` requires `requiredCapabilities`, `fidelity`, and `limitations`.
- `observation-policy` requires `filters`, `payloadAccess` (`metadata-only` or `allow-listed`),
  `bounds`, and `validityEffect`; `allow-listed` additionally requires `allowList`.
- `validation-policy` requires `allowedActions`, `injectionPoints`, `serviceEmulation`, `timePolicy`,
  `quotas`, and `permitPolicyRef`.

An unknown member, an unknown discriminator value, an unsupported `schemaVersion`, a missing
required member, or a payload for a form that does not match its declared `kind` is rejected. The
schema and the payload carry no provider address, credential, validation permit, live handle, or
tool session: every object is closed, so such a member is rejected as unknown. Exactly one payload
may decorate a given logical identity; a duplicate or conflicting policy for the same decorated
identity is rejected.

## Activation-plan v1 digest and provenance (normative)

`src/xverse/xcom/contracts/v1/activation-plan.schema.json` is the closed, Draft 2020-12 schema for
the canonical activation-plan v1 produced from an already normalized and validated XDL graph. It is
derived, not authored, and is not a second configuration language. The plan requires `planVersion`
(constant `"1"`), `digest`, `generator`, `provenance`, `contracts`, `endpoints`, `routes`,
`providers`, `policies`, `observationPoints`, `stimulation`, `clockDomains`, `activationOrder`,
`diagnostics`, `status`, and `inputResolution`, and rejects any unknown member. Every identity-bearing
collection is ordered by its declared identifier with unique identifiers; `diagnostics` is ordered by
`(code, targetId)`; `activationOrder` is a duplicate-free sequence of declared endpoint or route
identifiers. `status` is `inspectable` or `activatable`; a plan that declares `activatable` while any
member of `inputResolution` is `unresolved` is rejected, so a plan with an unresolved identity,
schema, capability, time, ownership, or policy input is inspectable but cannot activate.

**Canonical serialization.** The canonical byte string of a plan is the UTF-8 encoding of its JSON
value with object members ordered lexicographically by member name, no insignificant whitespace,
every mathematically integral number emitted in its single integer form (so `100` and `100.0` produce
identical canonical bytes and the same digest), no non-finite numbers, and no duplicate members. A
document that repeats a member name is rejected fail-closed rather than collapsed last-wins. The
independent decoder (T019) must reproduce these rules, including the integral-number form. Arrays
keep their validated deterministic order.

**Digest.** The digested region is the plan value with the top-level `digest` member removed. The
domain separator is the ASCII prefix `xverse.xcom.activation-plan.v1` followed by one `0x00` byte.
The digest is the SHA-256 of the domain separator concatenated with the canonical bytes of the
digested region. The `digest` member is `{"algorithm": "sha256", "value": "<64 lowercase hex
characters>"}`, and a digest is never computed over itself. The decoder independently recomputes the
digest over the received plan body and rejects a mismatch.

**Provenance and reproducibility.** `provenance` is a closed object requiring `generatedAt`, a
`graphDigest`, and an ordered `resources` array in which each entry records the normalized resource
`apiVersion`, `kind`, `namespace`, `name`, optional `version`, and `sourceDigest`. `generator`
records the generator `task` and `version`. `provenance.generatedAt` participates in the digested
region and is obtained from an explicit deterministic input; when none is supplied the fixed sentinel
`1970-01-01T00:00:00Z` is used. Semantically equivalent normalized inputs therefore produce
byte-identical canonical bytes and the same digest.

