# SWE.4–SWE.6 Verification measures

Entry: identified integrated candidate and available toolchain. Exit: selected checks pass without changing inputs; every phase checklist has independent approval.

## VM-XCOM-LIFE-UNIT

Methods: unit_test. Levels: unit, component. Requirements: XCOM-LIFE-002, XCOM-LIFE-003, XCOM-LIFE-004, XCOM-LIFE-005, XCOM-LIFE-006, XCOM-LIFE-007, XCOM-LIFE-008, XCOM-LIFE-011. Architecture: EndpointSpec, RouteSpec, OwnershipHandle, LifecycleController.

Selection: Builds the lifecycle units and runs table-driven state, ownership, capacity, compatibility, and negative tests..

Pass criteria: Command exits with status zero and candidate inputs remain unchanged.

Command argv: ['python3', 'scripts/validate_xcom_endpoint_route_lifecycle.py', '--unit']. Timeout: 600s.

## VM-XCOM-LIFE-LINT

Methods: lint. Levels: unit. Requirements: XCOM-LIFE-001, XCOM-LIFE-006, XCOM-LIFE-009, XCOM-LIFE-010. Architecture: EndpointRouteLifecycle.

Selection: Enforces formatting, owned paths, forbidden APIs and dependencies, no CommunicationItem storage, and warning-clean compilation..

Pass criteria: Command exits with status zero and candidate inputs remain unchanged.

Command argv: ['python3', 'scripts/validate_xcom_endpoint_route_lifecycle.py', '--lint']. Timeout: 600s.

## VM-XCOM-LIFE-STATIC

Methods: static_analysis. Levels: unit, component. Requirements: XCOM-LIFE-003, XCOM-LIFE-006, XCOM-LIFE-007, XCOM-LIFE-009, XCOM-LIFE-010. Architecture: OwnershipHandle, LifecycleController, Traceability.

Selection: Runs admitted clang-tidy, strict warning-free Doxygen, fixed-capacity/layout checks, and reciprocal traceability validation..

Pass criteria: Command exits with status zero and candidate inputs remain unchanged.

Command argv: ['python3', 'scripts/validate_xcom_endpoint_route_lifecycle.py', '--static']. Timeout: 600s.

## VM-XCOM-LIFE-INTEGRATION

Methods: integration_test. Levels: integration. Requirements: XCOM-LIFE-002, XCOM-LIFE-003, XCOM-LIFE-004, XCOM-LIFE-005, XCOM-LIFE-006, XCOM-LIFE-008, XCOM-LIFE-009, XCOM-LIFE-011. Architecture: ExternalLifecycleConsumer, LifecycleController, XComCoreTypes.

Selection: Compiles a separate public-API consumer and exercises an endpoint pair and route through valid lifecycle, invalid-transition, and stale-handle scenarios without transporting data..

Pass criteria: Command exits with status zero and candidate inputs remain unchanged.

Command argv: ['python3', 'scripts/validate_xcom_endpoint_route_lifecycle.py', '--integration']. Timeout: 600s.

## VM-XCOM-LIFE-VALIDATION

Methods: validation_test. Levels: software. Requirements: XCOM-LIFE-001, XCOM-LIFE-002, XCOM-LIFE-003, XCOM-LIFE-004, XCOM-LIFE-005, XCOM-LIFE-006, XCOM-LIFE-007, XCOM-LIFE-008, XCOM-LIFE-009, XCOM-LIFE-010, XCOM-LIFE-011. Architecture: EndpointRouteLifecycle, XComCoreTypes, Traceability.

Selection: Runs the complete lifecycle acceptance suite, the accepted core-types regression suite, and public-safe bidirectional traceability checks..

Pass criteria: Command exits with status zero and candidate inputs remain unchanged.

Command argv: ['python3', 'scripts/validate_xcom_endpoint_route_lifecycle.py', '--all']. Timeout: 900s.
