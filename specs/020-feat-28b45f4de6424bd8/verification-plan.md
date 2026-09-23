# SWE.4–SWE.6 Verification measures

Entry: identified integrated candidate and available toolchain. Exit: selected checks pass without changing inputs; every phase checklist has independent approval.

## VM-XCOM-VAL-CORE

Methods: unit_test, static_analysis, validation_test. Levels: unit, component, software. Requirements: XCOM-VAL-001, XCOM-VAL-003. Architecture: CoreTypesValidator.

Selection: Runs the complete accepted core-types gate on the exact integrated candidate..

Pass criteria: Command exits zero without changing candidate inputs..

Command argv: ['python3', 'scripts/validate_xcom_core_types.py', '--all']. Timeout: 1200s.

## VM-XCOM-VAL-LIFECYCLE

Methods: unit_test, static_analysis, integration_test, validation_test. Levels: component, integration, software. Requirements: XCOM-VAL-001, XCOM-VAL-003. Architecture: EndpointRouteLifecycleValidator.

Selection: Runs the complete accepted endpoint/route lifecycle gate on the exact integrated candidate..

Pass criteria: Command exits zero without changing candidate inputs..

Command argv: ['python3', 'scripts/validate_xcom_endpoint_route_lifecycle.py', '--all']. Timeout: 1200s.

## VM-XCOM-VAL-PROVIDER

Methods: unit_test, static_analysis, integration_test, validation_test. Levels: component, integration, software. Requirements: XCOM-VAL-001, XCOM-VAL-003. Architecture: ProviderLoopbackValidator.

Selection: Runs the complete accepted provider/loopback gate on the exact integrated candidate..

Pass criteria: Command exits zero without changing candidate inputs..

Command argv: ['python3', 'scripts/validate_xcom_provider_loopback.py', '--all']. Timeout: 1200s.

## VM-XCOM-VAL-OBSERVATION

Methods: unit_test, lint, static_analysis, integration_test, validation_test. Levels: unit, component, integration, software. Requirements: XCOM-VAL-001, XCOM-VAL-002, XCOM-VAL-003, XCOM-VAL-004. Architecture: ObservationEvidence, PredecessorValidationComposition.

Selection: Runs the complete observation gate including exact-candidate predecessor regressions..

Pass criteria: Command exits zero, retains exact-candidate predecessor evidence, and leaves inputs unchanged..

Command argv: ['python3', 'scripts/validate_xcom_observation.py', '--all']. Timeout: 1800s.
