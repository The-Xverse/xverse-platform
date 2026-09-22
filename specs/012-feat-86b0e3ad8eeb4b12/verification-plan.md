# SWE.4–SWE.6 Verification measures

Entry: identified integrated candidate and available toolchain. Exit: selected checks pass without changing inputs; every phase checklist has independent approval.

## VM-XCOM-TYPES-UNIT

Methods: unit_test. Levels: unit, component. Requirements: XCOM-TYPE-001, XCOM-TYPE-002, XCOM-TYPE-003, XCOM-TYPE-004, XCOM-TYPE-008. Architecture: Contract, CommunicationItem, Diagnostic, CoreValueResult.

Selection: Builds the bounded C++20 library and runs table-driven unit and negative tests..

Pass criteria: Command exits with status zero and candidate inputs remain unchanged.

Command argv: ['python3', 'scripts/validate_xcom_core_types.py', '--unit']. Timeout: 600s.

## VM-XCOM-TYPES-LINT

Methods: lint. Levels: unit. Requirements: XCOM-TYPE-001, XCOM-TYPE-004, XCOM-TYPE-005, XCOM-TYPE-006, XCOM-TYPE-008. Architecture: Contract, CommunicationItem, Diagnostic.

Selection: Enforces repository layout, forbidden dependency/API scans, formatting policy, and warning-clean compilation..

Pass criteria: Command exits with status zero and candidate inputs remain unchanged.

Command argv: ['python3', 'scripts/validate_xcom_core_types.py', '--lint']. Timeout: 600s.

## VM-XCOM-TYPES-STATIC

Methods: static_analysis. Levels: unit, component. Requirements: XCOM-TYPE-003, XCOM-TYPE-004, XCOM-TYPE-005, XCOM-TYPE-006, XCOM-TYPE-008. Architecture: Contract, CommunicationItem, Diagnostic, CoreValueResult.

Selection: Runs the admitted clang-tidy and warning-free Doxygen gates against every changed C++ unit..

Pass criteria: Command exits with status zero and candidate inputs remain unchanged.

Command argv: ['python3', 'scripts/validate_xcom_core_types.py', '--static']. Timeout: 600s.

## VM-XCOM-TYPES-INTEGRATION

Methods: integration_test. Levels: integration. Requirements: XCOM-TYPE-001, XCOM-TYPE-002, XCOM-TYPE-003, XCOM-TYPE-004, XCOM-TYPE-008. Architecture: XComCoreTypes, ExternalConsumer.

Selection: Compiles and runs a separate external-consumer fixture using only the exported public CMake target..

Pass criteria: Command exits with status zero and candidate inputs remain unchanged.

Command argv: ['python3', 'scripts/validate_xcom_core_types.py', '--integration']. Timeout: 600s.

## VM-XCOM-TYPES-VALIDATION

Methods: validation_test. Levels: software. Requirements: XCOM-TYPE-001, XCOM-TYPE-002, XCOM-TYPE-003, XCOM-TYPE-004, XCOM-TYPE-005, XCOM-TYPE-006, XCOM-TYPE-007, XCOM-TYPE-008. Architecture: XComCoreTypes, Traceability.

Selection: Runs the complete slice acceptance suite and validates public-safe bidirectional traceability..

Pass criteria: Command exits with status zero and candidate inputs remain unchanged.

Command argv: ['python3', 'scripts/validate_xcom_core_types.py', '--all']. Timeout: 900s.
