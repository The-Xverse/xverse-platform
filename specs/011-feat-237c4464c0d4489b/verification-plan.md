# SWE.4–SWE.6 Verification measures

Entry: identified integrated candidate and available toolchain. Exit: selected checks pass without changing inputs; every phase checklist has independent approval.

## VM-BLD-UNIT

Methods: unit_test. Levels: unit, component. Requirements: XCOM-BLD-001, XCOM-BLD-002, XCOM-BLD-003, XCOM-BLD-004, XCOM-BLD-005. Architecture: not applicable.

Selection: Exercises deterministic dependency-manifest parsing and positive/negative toolchain probes without network or host mutation..

Pass criteria: Command exits with status zero and candidate inputs remain unchanged.

Command argv: ['python3', 'scripts/xcom_dependency_preflight.py', '--self-test']. Timeout: 300s.

## VM-BLD-LINT

Methods: lint. Levels: unit. Requirements: XCOM-BLD-001, XCOM-BLD-002, XCOM-BLD-003, XCOM-BLD-004, XCOM-BLD-005. Architecture: DependencyManifest, ToolchainProbe.

Selection: Runs an independent Python lint engine over the dependency-admission implementation..

Pass criteria: Command exits with status zero and candidate inputs remain unchanged.

Command argv: ['ruff', 'check', '--no-cache', 'scripts/xcom_dependency_preflight.py']. Timeout: 300s.

## VM-BLD-STATIC

Methods: static_analysis. Levels: unit. Requirements: XCOM-BLD-001, XCOM-BLD-002, XCOM-BLD-003, XCOM-BLD-004, XCOM-BLD-005. Architecture: DependencyManifest, ToolchainProbe, DiagnosticSet.

Selection: Runs independent strict Python type analysis over the dependency-admission implementation..

Pass criteria: Command exits with status zero and candidate inputs remain unchanged.

Command argv: ['mypy', '--strict', '--cache-dir=/tmp/xcom-mypy', 'scripts/xcom_dependency_preflight.py']. Timeout: 300s.

## VM-BLD-INTEGRATION

Methods: integration_test. Levels: integration. Requirements: XCOM-BLD-001, XCOM-BLD-002, XCOM-BLD-003, XCOM-BLD-004, XCOM-BLD-005. Architecture: DependencyManifest, BuildEnvelope, OfflineToolchainPrefix.

Selection: Verifies the exact isolated prefix as an integrated compiler, generator, header, library, static-analysis, and documentation toolchain..

Pass criteria: Command exits with status zero and candidate inputs remain unchanged.

Command argv: ['python3', 'scripts/xcom_dependency_preflight.py', '--verify-toolchain']. Timeout: 300s.

## VM-BLD-VALIDATION

Methods: validation_test. Levels: software. Requirements: XCOM-BLD-001, XCOM-BLD-002, XCOM-BLD-003, XCOM-BLD-004, XCOM-BLD-005. Architecture: DependencyManifest, BuildEnvelope.

Selection: Validates the accepted dependency-admission and public documentation outcomes against every slice requirement..

Pass criteria: Command exits with status zero and candidate inputs remain unchanged.

Command argv: ['python3', 'scripts/xcom_dependency_preflight.py', '--all']. Timeout: 300s.
