# SWE.1 Software requirements (EARS)

## XCOM-PROV-005 [event_driven]

When a communication item is submitted, the X-COM provider composition shall accept it only through an exact active provider-route handle when its contract, interaction kind, logical source endpoint, route, provider, payload size, and lifecycle state match the prepared route.

Source: specs/007-xcom-core/spec.md FR-004 through FR-007 and FR-009; provenance: accepted; status: accepted.

Verification intent: Submit valid items for all four interaction families and reject each identity, contract, kind, payload, handle, and state mismatch with zero delivery.

## XCOM-PROV-011 [ubiquitous]

The provider-composition slice shall provide useful Doxygen documentation and reciprocal requirements-to-design-to-code-to-test traceability with revision-bound unit, static-analysis, integration, validation, and independent-review evidence.

Source: specs/007-xcom-core/spec.md FR-029 and FR-030; provenance: accepted; status: accepted.

Verification intent: Generate warning-free strict Doxygen output, validate every traceability edge reciprocally, execute all five measures, and inspect an independent Astra review of the exact revision.
