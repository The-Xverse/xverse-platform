# SWE.4–SWE.6 Verification measures

Entry: identified integrated candidate and available toolchain. Exit: selected checks pass without changing inputs; every phase checklist has independent approval.

## VM-XCOM-PROV-UNIT

Methods: unit_test. Levels: unit, component. Requirements: XCOM-PROV-002, XCOM-PROV-003, XCOM-PROV-004, XCOM-PROV-005, XCOM-PROV-006, XCOM-PROV-007, XCOM-PROV-008, XCOM-PROV-009. Architecture: ProviderDescriptor, ProviderRegistry, ProviderRouteHandle, LoopbackProvider.

Selection: Builds provider units and runs table-driven capability, ownership, queue, lifecycle, delivery, and negative tests..

Pass criteria: Command exits with status zero and candidate inputs remain unchanged.

Command argv: ['python3', 'scripts/validate_xcom_provider_loopback.py', '--unit']. Timeout: 600s.

## VM-XCOM-PROV-LINT

Methods: lint. Levels: unit. Requirements: XCOM-PROV-001, XCOM-PROV-009, XCOM-PROV-010, XCOM-PROV-011. Architecture: ProviderComposition, LoopbackProvider.

Selection: Enforces formatting, warning-clean compilation, owned paths, forbidden APIs, and dependency isolation..

Pass criteria: Command exits with status zero and candidate inputs remain unchanged.

Command argv: ['python3', 'scripts/validate_xcom_provider_loopback.py', '--lint']. Timeout: 600s.

## VM-XCOM-PROV-STATIC

Methods: static_analysis. Levels: unit, component. Requirements: XCOM-PROV-001, XCOM-PROV-004, XCOM-PROV-006, XCOM-PROV-008, XCOM-PROV-009, XCOM-PROV-010, XCOM-PROV-011. Architecture: ProviderRouteHandle, FixedProviderStorage, Traceability.

Selection: Runs admitted clang-tidy, strict Doxygen, fixed-storage and forbidden-dependency checks, and reciprocal traceability validation..

Pass criteria: Command exits with status zero and candidate inputs remain unchanged.

Command argv: ['python3', 'scripts/validate_xcom_provider_loopback.py', '--static']. Timeout: 600s.

## VM-XCOM-PROV-INTEGRATION

Methods: integration_test. Levels: integration. Requirements: XCOM-PROV-003, XCOM-PROV-004, XCOM-PROV-005, XCOM-PROV-006, XCOM-PROV-007, XCOM-PROV-008, XCOM-PROV-009. Architecture: ExternalProviderConsumer, ProviderComposition, LoopbackProvider, LifecycleController.

Selection: Compiles a separate public consumer and proves all interaction families, saturation, drain, close, and recreation through exact lifecycle handles..

Pass criteria: Command exits with status zero and candidate inputs remain unchanged.

Command argv: ['python3', 'scripts/validate_xcom_provider_loopback.py', '--integration']. Timeout: 600s.

## VM-XCOM-PROV-VALIDATION

Methods: validation_test. Levels: software. Requirements: XCOM-PROV-001, XCOM-PROV-002, XCOM-PROV-003, XCOM-PROV-004, XCOM-PROV-005, XCOM-PROV-006, XCOM-PROV-007, XCOM-PROV-008, XCOM-PROV-009, XCOM-PROV-010, XCOM-PROV-011. Architecture: ProviderComposition, LoopbackProvider, XComCoreTypes, EndpointRouteLifecycle, Traceability.

Selection: Runs the complete provider acceptance suite, all accepted prior X-COM regressions, isolation checks, and public-safe traceability checks..

Pass criteria: Command exits with status zero and candidate inputs remain unchanged.

Command argv: ['python3', 'scripts/validate_xcom_provider_loopback.py', '--all']. Timeout: 900s.
