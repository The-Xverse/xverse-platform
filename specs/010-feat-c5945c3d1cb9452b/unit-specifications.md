# SWE.3 Unit specifications (EARS)

## XCOM-BLD-UNIT-001 — DependencyManifest [ubiquitous]

The DependencyManifest shall reject missing, duplicate, malformed, or hash-mismatched package records.

Source: XCOM-BLD-002 through XCOM-BLD-004.

Verification intent: Run table-driven parser and hash fixtures.

## XCOM-BLD-UNIT-002 — ToolchainProbe [ubiquitous]

The ToolchainProbe shall inspect only the explicitly supplied offline prefix and shall return deterministic classified results.

Source: XCOM-BLD-001 through XCOM-BLD-004.

Verification intent: Run positive and missing-tool/header/library/version fixtures without network access.

## XCOM-BLD-UNIT-003 — BuildEnvelope [ubiquitous]

The BuildEnvelope shall enforce C++20, warning-as-error, test enablement, and explicit dependency discovery.

Source: XCOM-BLD-001 through XCOM-BLD-003.

Verification intent: Configure a controlled empty foundation and inspect generated configuration without adding runtime sources.
