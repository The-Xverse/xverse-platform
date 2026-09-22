# SWE.4–SWE.6 Verification measures

Entry: identified integrated candidate and available toolchain. Exit: selected checks pass without changing inputs; every phase checklist has independent approval.

## VM-XCOM-OBS-UNIT

Methods: unit_test. Levels: unit, component. Requirements: XCOM-OBS-001, XCOM-OBS-002, XCOM-OBS-003, XCOM-OBS-004, XCOM-OBS-005, XCOM-OBS-006, XCOM-OBS-008. Architecture: ObservationRecord, ObservationFilter, ObservationHub, TapHandle.

Selection: Builds observation units and runs table-driven filter, payload, queue, counter, handle, and concurrency tests..

Pass criteria: Command exits with status zero and candidate inputs remain unchanged.

Command argv: ['python3', 'scripts/validate_xcom_observation.py', '--unit']. Timeout: 600s.

## VM-XCOM-OBS-LINT

Methods: lint. Levels: unit. Requirements: XCOM-OBS-001, XCOM-OBS-008, XCOM-OBS-009, XCOM-OBS-010. Architecture: ObservationHub, ProviderComposition.

Selection: Enforces formatting, warnings, owned paths, forbidden APIs, and dependency isolation..

Pass criteria: Command exits with status zero and candidate inputs remain unchanged.

Command argv: ['python3', 'scripts/validate_xcom_observation.py', '--lint']. Timeout: 600s.

## VM-XCOM-OBS-STATIC

Methods: static_analysis. Levels: unit, component. Requirements: XCOM-OBS-002, XCOM-OBS-003, XCOM-OBS-006, XCOM-OBS-008, XCOM-OBS-009, XCOM-OBS-010. Architecture: FixedObservationStorage, ObservationTraceability.

Selection: Runs admitted clang-tidy, strict Doxygen, fixed-storage, public-safety, and reciprocal traceability checks..

Pass criteria: Command exits with status zero and candidate inputs remain unchanged.

Command argv: ['python3', 'scripts/validate_xcom_observation.py', '--static']. Timeout: 600s.

## VM-XCOM-OBS-INTEGRATION

Methods: integration_test. Levels: integration. Requirements: XCOM-OBS-001, XCOM-OBS-002, XCOM-OBS-003, XCOM-OBS-004, XCOM-OBS-005, XCOM-OBS-006, XCOM-OBS-007, XCOM-OBS-008. Architecture: ProviderComposition, ObservationHub, SyntheticObservationSink, LoopbackProvider.

Selection: Exercises actual loopback submissions through best-effort and lossless taps and proves observer failure isolation..

Pass criteria: Command exits with status zero and candidate inputs remain unchanged.

Command argv: ['python3', 'scripts/validate_xcom_observation.py', '--integration']. Timeout: 600s.

## VM-XCOM-OBS-PERFORMANCE

Methods: validation_test. Levels: integration, software. Requirements: XCOM-OBS-007, XCOM-OBS-010. Architecture: ProviderComposition, DisabledObservationFastPath.

Selection: Runs repeated paired loopback benchmarks and checks the accepted disabled-tap median threshold with environment disclosure..

Pass criteria: At least seven paired samples complete; disabled taps add no more than 2% median throughput or latency regression in the admitted fixture..

Command argv: ['python3', 'scripts/validate_xcom_observation.py', '--performance']. Timeout: 900s.

## VM-XCOM-OBS-VALIDATION

Methods: validation_test. Levels: software. Requirements: XCOM-OBS-001, XCOM-OBS-002, XCOM-OBS-003, XCOM-OBS-004, XCOM-OBS-005, XCOM-OBS-006, XCOM-OBS-007, XCOM-OBS-008, XCOM-OBS-009, XCOM-OBS-010. Architecture: ObservationBoundary, ProviderComposition, XComAcceptedRegressions.

Selection: Runs all observation measures, accepted provider/lifecycle/core regressions, isolation checks, public-safety checks, and traceability..

Pass criteria: Command exits with status zero and candidate inputs remain unchanged.

Command argv: ['python3', 'scripts/validate_xcom_observation.py', '--all']. Timeout: 1200s.
