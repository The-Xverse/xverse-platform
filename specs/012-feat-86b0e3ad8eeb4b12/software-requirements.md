# SWE.1 Software requirements (EARS)

## XCOM-TYPE-001 [ubiquitous]

The X-COM core value model shall remain domain-neutral and shall keep logical identity independent from provider, protocol, address, and physical realization.

Source: specs/007-xcom-core/spec.md FR-001 and FR-003; provenance: accepted; status: accepted.

Verification intent: Compile and exercise the public types using only domain-neutral logical identifiers and prove that no provider, protocol, address, automotive, or physical-realization field is required.

## XCOM-TYPE-002 [ubiquitous]

The X-COM core value model shall represent signal/state update, message/event, service request, and service response as distinct interaction kinds with explicit compatible directions.

Source: specs/007-xcom-core/spec.md FR-004; provenance: accepted; status: accepted.

Verification intent: Run table-driven positive and negative interaction-kind and direction tests.

## XCOM-TYPE-003 [ubiquitous]

The X-COM communication item shall carry contract version, logical interface and endpoint identity, schema identity and version, origin, timestamp and clock domain, correlation and causation identity, and route and provider identity.

Source: specs/007-xcom-core/spec.md FR-005; provenance: accepted; status: accepted.

Verification intent: Construct valid items and reject missing, empty, inconsistent, or over-bound metadata through deterministic table-driven tests.

## XCOM-TYPE-004 [ubiquitous]

The X-COM diagnostic model shall use stable codes and shall carry severity, phase, affected identity, reason, correction, and deterministic ordering information.

Source: specs/007-xcom-core/spec.md FR-025; provenance: accepted; status: accepted.

Verification intent: Compare exact diagnostic codes and byte-stable sorted diagnostic sequences across reordered invalid inputs.

## XCOM-TYPE-005 [ubiquitous]

The X-COM core value library shall perform no network discovery, ambient configuration lookup, secret access, legacy repository access, filesystem access, or process execution during normal use.

Source: specs/007-xcom-core/spec.md FR-026 and FR-028; provenance: accepted; status: accepted.

Verification intent: Inspect the bounded source set and run the unit and consumer fixtures in a network-disabled SESN verifier.

## XCOM-TYPE-006 [ubiquitous]

The X-COM core-types slice shall provide useful Doxygen documentation for every public and changed internal C++ unit, covering ownership, lifetime, thread-safety, failure behavior, parameters, and results where applicable.

Source: specs/007-xcom-core/spec.md FR-029; provenance: accepted; status: accepted.

Verification intent: Generate warning-free Doxygen HTML/XML and reject undocumented declared units or missing contract clauses.

## XCOM-TYPE-007 [ubiquitous]

The core-types slice shall provide bidirectional requirements-to-design-to-code-to-test traceability and revision-bound unit, static-analysis, integration, validation, and independent-review evidence.

Source: specs/007-xcom-core/spec.md FR-030; provenance: accepted; status: accepted.

Verification intent: Validate a machine-readable traceability table and inspect SESN evidence and the separate review for the exact candidate revision.

## XCOM-TYPE-008 [ubiquitous]

The core-types slice shall build as C++20 with the accepted warning-as-error policy and shall expose CTest unit and external-consumer integration targets through the existing offline build envelope.

Source: specs/007-xcom-core/tasks.md T012 and T016; provenance: accepted; status: accepted.

Verification intent: Configure with Ninja, build with warnings as errors, run CTest, and compile and execute a consumer against the public target.
