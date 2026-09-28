# X-COM Capability 007 Traceability Matrix

> Deterministic projection of `traceability-matrix.json` (schema version 1).
> Do not edit by hand; regenerate from the model and re-run
> `scripts/validate_xcom_requirements_traceability.py --check-human`.

## Matrix identity

| Field | Value |
| --- | --- |
| Task | T008 |
| Schema version | 1 |
| Baseline revision | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| Candidate revision rule | Every candidate records its own exact revision and the exact accepted predecessor revision it derives from; acceptance is per candidate and is never inherited from a sibling or inferred from source presence. |
| Artifacts | 21 |
| Links | 327 |

## Link relations

`allocated_to`, `derives_from`, `evidenced_by`, `implemented_by`, `refines`, `verified_by`

## Target kinds

`design_unit`, `evidence`, `measure`, `requirement`, `sads`, `source`, `test`

## Artifacts

| ID | Kind | Locator | Status | Revision binding |
| --- | --- | --- | --- | --- |
| XCOM-DU-CORE-BASELINE | design_unit | src/xverse/xcom/include/xverse/xcom/core_types.hpp | planned | `planned` |
| XCOM-DU-ENB-BASELINE | design_unit | docs/engineering/xcom/t008/requirements-register.json | planned | `planned` |
| XCOM-DU-GW-BASELINE | design_unit | proto/xverse/xcom/v1/tool_gateway.proto | planned | `planned` |
| XCOM-DU-INTG-BASELINE | design_unit | docs/engineering/xcom/t010/design-units.md | planned | `planned` |
| XCOM-DU-OBS-BASELINE | design_unit | src/xverse/xcom/include/xverse/xcom/observation.hpp | planned | `planned` |
| XCOM-DU-REQ-BASELINE | design_unit | specs/007-xcom-core/spec.md | planned | `planned` |
| XCOM-DU-STIM-BASELINE | design_unit | src/xverse/xcom/include/xverse/xcom/validation_session.hpp | planned | `planned` |
| XCOM-DU-XDL-BASELINE | design_unit | src/xverse/xcom/include/xverse/xcom/activation_plan.hpp | planned | `planned` |
| XCOM-M-STIM-SESSION | measure | tests/xcom/validation_session/validation_tests.cpp | established | `4b01586b438a8587d231ee8828d896c206c06a96` |
| XCOM-SRC-SPEC-007 | source | specs/007-xcom-core/spec.md | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-SRC-STIM-SESSION-CPP | source | src/xverse/xcom/src/validation_session.cpp | established | `4b01586b438a8587d231ee8828d896c206c06a96` |
| XCOM-SRC-STIM-SESSION-HPP | source | src/xverse/xcom/include/xverse/xcom/validation_session.hpp | established | `4b01586b438a8587d231ee8828d896c206c06a96` |
| XCOM-T-CORE | test | tests/xcom/core_types/ | planned | `planned` |
| XCOM-T-ENB | test | docs/engineering/xcom/t008/ | planned | `planned` |
| XCOM-T-GW | test | tests/xcom/tool_gateway/ | planned | `planned` |
| XCOM-T-INTG | test | docs/engineering/xcom/t037/ | planned | `planned` |
| XCOM-T-OBS | test | tests/xcom/observation/ | planned | `planned` |
| XCOM-T-REQ-TRACE | test | scripts/validate_xcom_requirements_traceability.py | planned | `planned` |
| XCOM-T-STIM | test | tests/xcom/stimulation_journal/ | planned | `planned` |
| XCOM-T-STIM-SESSION | test | tests/xcom/validation_session/ | established | `4b01586b438a8587d231ee8828d896c206c06a96` |
| XCOM-T-XDL | test | tests/xcom/activation_plan/ | planned | `planned` |

## Links

| ID | From | Relation | To | To kind | Status | Revision binding |
| --- | --- | --- | --- | --- | --- | --- |
| XCOM-L-0001 | XCOM-STK-001 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0002 | XCOM-STK-001 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0003 | XCOM-STK-002 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0004 | XCOM-STK-002 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0005 | XCOM-STK-003 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0006 | XCOM-STK-003 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0007 | XCOM-STK-004 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0008 | XCOM-STK-004 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0009 | XCOM-STK-005 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0010 | XCOM-STK-005 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0011 | XCOM-STK-006 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0012 | XCOM-STK-006 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0013 | XCOM-STK-007 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0014 | XCOM-STK-007 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0015 | XCOM-STK-008 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0016 | XCOM-STK-008 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0017 | XCOM-SW-CORE-001 | refines | XCOM-SYS-FR-002 | requirement | planned | `planned` |
| XCOM-L-0018 | XCOM-SW-CORE-001 | refines | XCOM-SYS-FR-003 | requirement | planned | `planned` |
| XCOM-L-0019 | XCOM-SW-CORE-001 | allocated_to | XCOM-DU-CORE-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0020 | XCOM-SW-CORE-001 | verified_by | XCOM-T-CORE | test | planned | `planned` |
| XCOM-L-0021 | XCOM-SW-CORE-002 | refines | XCOM-SYS-FR-004 | requirement | planned | `planned` |
| XCOM-L-0022 | XCOM-SW-CORE-002 | refines | XCOM-SYS-FR-005 | requirement | planned | `planned` |
| XCOM-L-0023 | XCOM-SW-CORE-002 | allocated_to | XCOM-DU-CORE-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0024 | XCOM-SW-CORE-002 | verified_by | XCOM-T-CORE | test | planned | `planned` |
| XCOM-L-0025 | XCOM-SW-CORE-003 | refines | XCOM-SYS-FR-006 | requirement | planned | `planned` |
| XCOM-L-0026 | XCOM-SW-CORE-003 | allocated_to | XCOM-DU-CORE-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0027 | XCOM-SW-CORE-003 | verified_by | XCOM-T-CORE | test | planned | `planned` |
| XCOM-L-0028 | XCOM-SW-CORE-004 | refines | XCOM-SYS-FR-007 | requirement | planned | `planned` |
| XCOM-L-0029 | XCOM-SW-CORE-004 | refines | XCOM-SYS-FR-008 | requirement | planned | `planned` |
| XCOM-L-0030 | XCOM-SW-CORE-004 | allocated_to | XCOM-DU-CORE-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0031 | XCOM-SW-CORE-004 | verified_by | XCOM-T-CORE | test | planned | `planned` |
| XCOM-L-0032 | XCOM-SW-CORE-005 | refines | XCOM-SYS-FR-009 | requirement | planned | `planned` |
| XCOM-L-0033 | XCOM-SW-CORE-005 | refines | XCOM-SYS-FR-010 | requirement | planned | `planned` |
| XCOM-L-0034 | XCOM-SW-CORE-005 | allocated_to | XCOM-DU-CORE-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0035 | XCOM-SW-CORE-005 | verified_by | XCOM-T-CORE | test | planned | `planned` |
| XCOM-L-0036 | XCOM-SW-CORE-006 | refines | XCOM-SYS-FR-025 | requirement | planned | `planned` |
| XCOM-L-0037 | XCOM-SW-CORE-006 | allocated_to | XCOM-DU-CORE-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0038 | XCOM-SW-CORE-006 | verified_by | XCOM-T-CORE | test | planned | `planned` |
| XCOM-L-0039 | XCOM-SW-CORE-007 | refines | XCOM-SYS-FR-001 | requirement | planned | `planned` |
| XCOM-L-0040 | XCOM-SW-CORE-007 | refines | XCOM-SYS-FR-026 | requirement | planned | `planned` |
| XCOM-L-0041 | XCOM-SW-CORE-007 | refines | XCOM-SYS-FR-028 | requirement | planned | `planned` |
| XCOM-L-0042 | XCOM-SW-CORE-007 | allocated_to | XCOM-DU-CORE-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0043 | XCOM-SW-CORE-007 | verified_by | XCOM-T-CORE | test | planned | `planned` |
| XCOM-L-0044 | XCOM-SW-CORE-008 | refines | XCOM-SYS-FR-024 | requirement | planned | `planned` |
| XCOM-L-0045 | XCOM-SW-CORE-008 | allocated_to | XCOM-DU-CORE-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0046 | XCOM-SW-CORE-008 | verified_by | XCOM-T-CORE | test | planned | `planned` |
| XCOM-L-0047 | XCOM-SW-CORE-009 | refines | XCOM-SYS-SC-001 | requirement | planned | `planned` |
| XCOM-L-0048 | XCOM-SW-CORE-009 | allocated_to | XCOM-DU-CORE-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0049 | XCOM-SW-CORE-009 | verified_by | XCOM-T-CORE | test | planned | `planned` |
| XCOM-L-0050 | XCOM-SW-CORE-010 | refines | XCOM-SYS-FR-025 | requirement | planned | `planned` |
| XCOM-L-0051 | XCOM-SW-CORE-010 | allocated_to | XCOM-DU-CORE-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0052 | XCOM-SW-CORE-010 | verified_by | XCOM-T-CORE | test | planned | `planned` |
| XCOM-L-0053 | XCOM-SW-ENB-001 | refines | XCOM-SYS-FR-030 | requirement | planned | `planned` |
| XCOM-L-0054 | XCOM-SW-ENB-001 | allocated_to | XCOM-DU-ENB-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0055 | XCOM-SW-ENB-001 | verified_by | XCOM-T-ENB | test | planned | `planned` |
| XCOM-L-0056 | XCOM-SW-ENB-002 | refines | XCOM-SYS-FR-035 | requirement | planned | `planned` |
| XCOM-L-0057 | XCOM-SW-ENB-002 | allocated_to | XCOM-DU-ENB-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0058 | XCOM-SW-ENB-002 | verified_by | XCOM-T-ENB | test | planned | `planned` |
| XCOM-L-0059 | XCOM-SW-ENB-003 | refines | XCOM-SYS-SC-010 | requirement | planned | `planned` |
| XCOM-L-0060 | XCOM-SW-ENB-003 | allocated_to | XCOM-DU-ENB-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0061 | XCOM-SW-ENB-003 | verified_by | XCOM-T-ENB | test | planned | `planned` |
| XCOM-L-0062 | XCOM-SW-ENB-004 | refines | XCOM-SYS-FR-029 | requirement | planned | `planned` |
| XCOM-L-0063 | XCOM-SW-ENB-004 | refines | XCOM-SYS-FR-030 | requirement | planned | `planned` |
| XCOM-L-0064 | XCOM-SW-ENB-004 | allocated_to | XCOM-DU-ENB-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0065 | XCOM-SW-ENB-004 | verified_by | XCOM-T-ENB | test | planned | `planned` |
| XCOM-L-0066 | XCOM-SW-GW-001 | refines | XCOM-SYS-FR-022 | requirement | planned | `planned` |
| XCOM-L-0067 | XCOM-SW-GW-001 | allocated_to | XCOM-DU-GW-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0068 | XCOM-SW-GW-001 | verified_by | XCOM-T-GW | test | planned | `planned` |
| XCOM-L-0069 | XCOM-SW-GW-002 | refines | XCOM-SYS-FR-032 | requirement | planned | `planned` |
| XCOM-L-0070 | XCOM-SW-GW-002 | allocated_to | XCOM-DU-GW-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0071 | XCOM-SW-GW-002 | verified_by | XCOM-T-GW | test | planned | `planned` |
| XCOM-L-0072 | XCOM-SW-GW-003 | refines | XCOM-SYS-SC-011 | requirement | planned | `planned` |
| XCOM-L-0073 | XCOM-SW-GW-003 | allocated_to | XCOM-DU-GW-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0074 | XCOM-SW-GW-003 | verified_by | XCOM-T-GW | test | planned | `planned` |
| XCOM-L-0075 | XCOM-SW-INTG-001 | refines | XCOM-SYS-FR-027 | requirement | planned | `planned` |
| XCOM-L-0076 | XCOM-SW-INTG-001 | allocated_to | XCOM-DU-INTG-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0077 | XCOM-SW-INTG-001 | verified_by | XCOM-T-INTG | test | planned | `planned` |
| XCOM-L-0078 | XCOM-SW-INTG-002 | refines | XCOM-SYS-FR-029 | requirement | planned | `planned` |
| XCOM-L-0079 | XCOM-SW-INTG-002 | refines | XCOM-SYS-SC-009 | requirement | planned | `planned` |
| XCOM-L-0080 | XCOM-SW-INTG-002 | allocated_to | XCOM-DU-INTG-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0081 | XCOM-SW-INTG-002 | verified_by | XCOM-T-INTG | test | planned | `planned` |
| XCOM-L-0082 | XCOM-SW-INTG-003 | refines | XCOM-SYS-SC-008 | requirement | planned | `planned` |
| XCOM-L-0083 | XCOM-SW-INTG-003 | allocated_to | XCOM-DU-INTG-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0084 | XCOM-SW-INTG-003 | verified_by | XCOM-T-INTG | test | planned | `planned` |
| XCOM-L-0085 | XCOM-SW-OBS-001 | refines | XCOM-SYS-FR-011 | requirement | planned | `planned` |
| XCOM-L-0086 | XCOM-SW-OBS-001 | allocated_to | XCOM-DU-OBS-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0087 | XCOM-SW-OBS-001 | verified_by | XCOM-T-OBS | test | planned | `planned` |
| XCOM-L-0088 | XCOM-SW-OBS-002 | refines | XCOM-SYS-FR-012 | requirement | planned | `planned` |
| XCOM-L-0089 | XCOM-SW-OBS-002 | refines | XCOM-SYS-SC-003 | requirement | planned | `planned` |
| XCOM-L-0090 | XCOM-SW-OBS-002 | allocated_to | XCOM-DU-OBS-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0091 | XCOM-SW-OBS-002 | verified_by | XCOM-T-OBS | test | planned | `planned` |
| XCOM-L-0092 | XCOM-SW-OBS-003 | refines | XCOM-SYS-FR-013 | requirement | planned | `planned` |
| XCOM-L-0093 | XCOM-SW-OBS-003 | refines | XCOM-SYS-SC-004 | requirement | planned | `planned` |
| XCOM-L-0094 | XCOM-SW-OBS-003 | allocated_to | XCOM-DU-OBS-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0095 | XCOM-SW-OBS-003 | verified_by | XCOM-T-OBS | test | planned | `planned` |
| XCOM-L-0096 | XCOM-SW-OBS-004 | refines | XCOM-SYS-FR-014 | requirement | planned | `planned` |
| XCOM-L-0097 | XCOM-SW-OBS-004 | refines | XCOM-SYS-SC-005 | requirement | planned | `planned` |
| XCOM-L-0098 | XCOM-SW-OBS-004 | allocated_to | XCOM-DU-OBS-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0099 | XCOM-SW-OBS-004 | verified_by | XCOM-T-OBS | test | planned | `planned` |
| XCOM-L-0100 | XCOM-SW-OBS-005 | refines | XCOM-SYS-FR-023 | requirement | planned | `planned` |
| XCOM-L-0101 | XCOM-SW-OBS-005 | allocated_to | XCOM-DU-OBS-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0102 | XCOM-SW-OBS-005 | verified_by | XCOM-T-OBS | test | planned | `planned` |
| XCOM-L-0103 | XCOM-SW-STIM-001 | refines | XCOM-SYS-FR-015 | requirement | planned | `planned` |
| XCOM-L-0104 | XCOM-SW-STIM-001 | implemented_by | XCOM-SRC-STIM-SESSION-HPP | source | established | `4b01586b438a8587d231ee8828d896c206c06a96` |
| XCOM-L-0105 | XCOM-SW-STIM-001 | verified_by | XCOM-T-STIM-SESSION | test | established | `4b01586b438a8587d231ee8828d896c206c06a96` |
| XCOM-L-0106 | XCOM-SW-STIM-001 | evidenced_by | XCOM-M-STIM-SESSION | measure | established | `4b01586b438a8587d231ee8828d896c206c06a96` |
| XCOM-L-0107 | XCOM-SW-STIM-002 | refines | XCOM-SYS-FR-016 | requirement | planned | `planned` |
| XCOM-L-0108 | XCOM-SW-STIM-002 | implemented_by | XCOM-SRC-STIM-SESSION-CPP | source | established | `4b01586b438a8587d231ee8828d896c206c06a96` |
| XCOM-L-0109 | XCOM-SW-STIM-002 | verified_by | XCOM-T-STIM-SESSION | test | established | `4b01586b438a8587d231ee8828d896c206c06a96` |
| XCOM-L-0110 | XCOM-SW-STIM-002 | evidenced_by | XCOM-M-STIM-SESSION | measure | established | `4b01586b438a8587d231ee8828d896c206c06a96` |
| XCOM-L-0111 | XCOM-SW-STIM-003 | refines | XCOM-SYS-FR-017 | requirement | planned | `planned` |
| XCOM-L-0112 | XCOM-SW-STIM-003 | refines | XCOM-SYS-SC-006 | requirement | planned | `planned` |
| XCOM-L-0113 | XCOM-SW-STIM-003 | allocated_to | XCOM-DU-STIM-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0114 | XCOM-SW-STIM-003 | verified_by | XCOM-T-STIM | test | planned | `planned` |
| XCOM-L-0115 | XCOM-SW-STIM-004 | refines | XCOM-SYS-FR-018 | requirement | planned | `planned` |
| XCOM-L-0116 | XCOM-SW-STIM-004 | allocated_to | XCOM-DU-STIM-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0117 | XCOM-SW-STIM-004 | verified_by | XCOM-T-STIM | test | planned | `planned` |
| XCOM-L-0118 | XCOM-SW-STIM-005 | refines | XCOM-SYS-FR-019 | requirement | planned | `planned` |
| XCOM-L-0119 | XCOM-SW-STIM-005 | allocated_to | XCOM-DU-STIM-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0120 | XCOM-SW-STIM-005 | verified_by | XCOM-T-STIM | test | planned | `planned` |
| XCOM-L-0121 | XCOM-SW-STIM-006 | refines | XCOM-SYS-FR-020 | requirement | planned | `planned` |
| XCOM-L-0122 | XCOM-SW-STIM-006 | refines | XCOM-SYS-FR-033 | requirement | planned | `planned` |
| XCOM-L-0123 | XCOM-SW-STIM-006 | allocated_to | XCOM-DU-STIM-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0124 | XCOM-SW-STIM-006 | verified_by | XCOM-T-STIM | test | planned | `planned` |
| XCOM-L-0125 | XCOM-SW-STIM-007 | refines | XCOM-SYS-FR-021 | requirement | planned | `planned` |
| XCOM-L-0126 | XCOM-SW-STIM-007 | allocated_to | XCOM-DU-STIM-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0127 | XCOM-SW-STIM-007 | verified_by | XCOM-T-STIM | test | planned | `planned` |
| XCOM-L-0128 | XCOM-SW-STIM-008 | refines | XCOM-SYS-FR-034 | requirement | planned | `planned` |
| XCOM-L-0129 | XCOM-SW-STIM-008 | allocated_to | XCOM-DU-STIM-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0130 | XCOM-SW-STIM-008 | verified_by | XCOM-T-STIM | test | planned | `planned` |
| XCOM-L-0131 | XCOM-SW-STIM-009 | refines | XCOM-SYS-SC-007 | requirement | planned | `planned` |
| XCOM-L-0132 | XCOM-SW-STIM-009 | allocated_to | XCOM-DU-STIM-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0133 | XCOM-SW-STIM-009 | verified_by | XCOM-T-STIM | test | planned | `planned` |
| XCOM-L-0134 | XCOM-SW-XDL-001 | refines | XCOM-SYS-FR-031 | requirement | planned | `planned` |
| XCOM-L-0135 | XCOM-SW-XDL-001 | refines | XCOM-SYS-FR-002 | requirement | planned | `planned` |
| XCOM-L-0136 | XCOM-SW-XDL-001 | allocated_to | XCOM-DU-XDL-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0137 | XCOM-SW-XDL-001 | verified_by | XCOM-T-XDL | test | planned | `planned` |
| XCOM-L-0138 | XCOM-SW-XDL-002 | refines | XCOM-SYS-FR-002 | requirement | planned | `planned` |
| XCOM-L-0139 | XCOM-SW-XDL-002 | allocated_to | XCOM-DU-XDL-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0140 | XCOM-SW-XDL-002 | verified_by | XCOM-T-XDL | test | planned | `planned` |
| XCOM-L-0141 | XCOM-SW-XDL-003 | refines | XCOM-SYS-SC-002 | requirement | planned | `planned` |
| XCOM-L-0142 | XCOM-SW-XDL-003 | allocated_to | XCOM-DU-XDL-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0143 | XCOM-SW-XDL-003 | verified_by | XCOM-T-XDL | test | planned | `planned` |
| XCOM-L-0144 | XCOM-SYS-FR-001 | refines | XCOM-STK-006 | requirement | planned | `planned` |
| XCOM-L-0145 | XCOM-SYS-FR-001 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0146 | XCOM-SYS-FR-001 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0147 | XCOM-SYS-FR-001 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0148 | XCOM-SYS-FR-002 | refines | XCOM-STK-006 | requirement | planned | `planned` |
| XCOM-L-0149 | XCOM-SYS-FR-002 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0150 | XCOM-SYS-FR-002 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0151 | XCOM-SYS-FR-002 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0152 | XCOM-SYS-FR-003 | refines | XCOM-STK-006 | requirement | planned | `planned` |
| XCOM-L-0153 | XCOM-SYS-FR-003 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0154 | XCOM-SYS-FR-003 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0155 | XCOM-SYS-FR-003 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0156 | XCOM-SYS-FR-004 | refines | XCOM-STK-001 | requirement | planned | `planned` |
| XCOM-L-0157 | XCOM-SYS-FR-004 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0158 | XCOM-SYS-FR-004 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0159 | XCOM-SYS-FR-004 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0160 | XCOM-SYS-FR-005 | refines | XCOM-STK-001 | requirement | planned | `planned` |
| XCOM-L-0161 | XCOM-SYS-FR-005 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0162 | XCOM-SYS-FR-005 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0163 | XCOM-SYS-FR-005 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0164 | XCOM-SYS-FR-006 | refines | XCOM-STK-005 | requirement | planned | `planned` |
| XCOM-L-0165 | XCOM-SYS-FR-006 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0166 | XCOM-SYS-FR-006 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0167 | XCOM-SYS-FR-006 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0168 | XCOM-SYS-FR-007 | refines | XCOM-STK-005 | requirement | planned | `planned` |
| XCOM-L-0169 | XCOM-SYS-FR-007 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0170 | XCOM-SYS-FR-007 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0171 | XCOM-SYS-FR-007 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0172 | XCOM-SYS-FR-008 | refines | XCOM-STK-005 | requirement | planned | `planned` |
| XCOM-L-0173 | XCOM-SYS-FR-008 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0174 | XCOM-SYS-FR-008 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0175 | XCOM-SYS-FR-008 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0176 | XCOM-SYS-FR-009 | refines | XCOM-STK-004 | requirement | planned | `planned` |
| XCOM-L-0177 | XCOM-SYS-FR-009 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0178 | XCOM-SYS-FR-009 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0179 | XCOM-SYS-FR-009 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0180 | XCOM-SYS-FR-010 | refines | XCOM-STK-005 | requirement | planned | `planned` |
| XCOM-L-0181 | XCOM-SYS-FR-010 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0182 | XCOM-SYS-FR-010 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0183 | XCOM-SYS-FR-010 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0184 | XCOM-SYS-FR-011 | refines | XCOM-STK-002 | requirement | planned | `planned` |
| XCOM-L-0185 | XCOM-SYS-FR-011 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0186 | XCOM-SYS-FR-011 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0187 | XCOM-SYS-FR-011 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0188 | XCOM-SYS-FR-012 | refines | XCOM-STK-002 | requirement | planned | `planned` |
| XCOM-L-0189 | XCOM-SYS-FR-012 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0190 | XCOM-SYS-FR-012 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0191 | XCOM-SYS-FR-012 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0192 | XCOM-SYS-FR-013 | refines | XCOM-STK-005 | requirement | planned | `planned` |
| XCOM-L-0193 | XCOM-SYS-FR-013 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0194 | XCOM-SYS-FR-013 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0195 | XCOM-SYS-FR-013 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0196 | XCOM-SYS-FR-014 | refines | XCOM-STK-002 | requirement | planned | `planned` |
| XCOM-L-0197 | XCOM-SYS-FR-014 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0198 | XCOM-SYS-FR-014 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0199 | XCOM-SYS-FR-014 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0200 | XCOM-SYS-FR-015 | refines | XCOM-STK-003 | requirement | planned | `planned` |
| XCOM-L-0201 | XCOM-SYS-FR-015 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0202 | XCOM-SYS-FR-015 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0203 | XCOM-SYS-FR-015 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0204 | XCOM-SYS-FR-016 | refines | XCOM-STK-003 | requirement | planned | `planned` |
| XCOM-L-0205 | XCOM-SYS-FR-016 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0206 | XCOM-SYS-FR-016 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0207 | XCOM-SYS-FR-016 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0208 | XCOM-SYS-FR-017 | refines | XCOM-STK-003 | requirement | planned | `planned` |
| XCOM-L-0209 | XCOM-SYS-FR-017 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0210 | XCOM-SYS-FR-017 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0211 | XCOM-SYS-FR-017 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0212 | XCOM-SYS-FR-018 | refines | XCOM-STK-003 | requirement | planned | `planned` |
| XCOM-L-0213 | XCOM-SYS-FR-018 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0214 | XCOM-SYS-FR-018 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0215 | XCOM-SYS-FR-018 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0216 | XCOM-SYS-FR-019 | refines | XCOM-STK-003 | requirement | planned | `planned` |
| XCOM-L-0217 | XCOM-SYS-FR-019 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0218 | XCOM-SYS-FR-019 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0219 | XCOM-SYS-FR-019 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0220 | XCOM-SYS-FR-020 | refines | XCOM-STK-003 | requirement | planned | `planned` |
| XCOM-L-0221 | XCOM-SYS-FR-020 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0222 | XCOM-SYS-FR-020 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0223 | XCOM-SYS-FR-020 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0224 | XCOM-SYS-FR-021 | refines | XCOM-STK-003 | requirement | planned | `planned` |
| XCOM-L-0225 | XCOM-SYS-FR-021 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0226 | XCOM-SYS-FR-021 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0227 | XCOM-SYS-FR-021 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0228 | XCOM-SYS-FR-022 | refines | XCOM-STK-004 | requirement | planned | `planned` |
| XCOM-L-0229 | XCOM-SYS-FR-022 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0230 | XCOM-SYS-FR-022 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0231 | XCOM-SYS-FR-022 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0232 | XCOM-SYS-FR-023 | refines | XCOM-STK-002 | requirement | planned | `planned` |
| XCOM-L-0233 | XCOM-SYS-FR-023 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0234 | XCOM-SYS-FR-023 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0235 | XCOM-SYS-FR-023 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0236 | XCOM-SYS-FR-024 | refines | XCOM-STK-004 | requirement | planned | `planned` |
| XCOM-L-0237 | XCOM-SYS-FR-024 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0238 | XCOM-SYS-FR-024 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0239 | XCOM-SYS-FR-024 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0240 | XCOM-SYS-FR-025 | refines | XCOM-STK-005 | requirement | planned | `planned` |
| XCOM-L-0241 | XCOM-SYS-FR-025 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0242 | XCOM-SYS-FR-025 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0243 | XCOM-SYS-FR-025 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0244 | XCOM-SYS-FR-026 | refines | XCOM-STK-007 | requirement | planned | `planned` |
| XCOM-L-0245 | XCOM-SYS-FR-026 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0246 | XCOM-SYS-FR-026 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0247 | XCOM-SYS-FR-026 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0248 | XCOM-SYS-FR-027 | refines | XCOM-STK-007 | requirement | planned | `planned` |
| XCOM-L-0249 | XCOM-SYS-FR-027 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0250 | XCOM-SYS-FR-027 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0251 | XCOM-SYS-FR-027 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0252 | XCOM-SYS-FR-028 | refines | XCOM-STK-007 | requirement | planned | `planned` |
| XCOM-L-0253 | XCOM-SYS-FR-028 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0254 | XCOM-SYS-FR-028 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0255 | XCOM-SYS-FR-028 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0256 | XCOM-SYS-FR-029 | refines | XCOM-STK-007 | requirement | planned | `planned` |
| XCOM-L-0257 | XCOM-SYS-FR-029 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0258 | XCOM-SYS-FR-029 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0259 | XCOM-SYS-FR-029 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0260 | XCOM-SYS-FR-030 | refines | XCOM-STK-007 | requirement | planned | `planned` |
| XCOM-L-0261 | XCOM-SYS-FR-030 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0262 | XCOM-SYS-FR-030 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0263 | XCOM-SYS-FR-030 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0264 | XCOM-SYS-FR-031 | refines | XCOM-STK-006 | requirement | planned | `planned` |
| XCOM-L-0265 | XCOM-SYS-FR-031 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0266 | XCOM-SYS-FR-031 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0267 | XCOM-SYS-FR-031 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0268 | XCOM-SYS-FR-032 | refines | XCOM-STK-008 | requirement | planned | `planned` |
| XCOM-L-0269 | XCOM-SYS-FR-032 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0270 | XCOM-SYS-FR-032 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0271 | XCOM-SYS-FR-032 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0272 | XCOM-SYS-FR-033 | refines | XCOM-STK-003 | requirement | planned | `planned` |
| XCOM-L-0273 | XCOM-SYS-FR-033 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0274 | XCOM-SYS-FR-033 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0275 | XCOM-SYS-FR-033 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0276 | XCOM-SYS-FR-034 | refines | XCOM-STK-003 | requirement | planned | `planned` |
| XCOM-L-0277 | XCOM-SYS-FR-034 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0278 | XCOM-SYS-FR-034 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0279 | XCOM-SYS-FR-034 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0280 | XCOM-SYS-FR-035 | refines | XCOM-STK-007 | requirement | planned | `planned` |
| XCOM-L-0281 | XCOM-SYS-FR-035 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0282 | XCOM-SYS-FR-035 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0283 | XCOM-SYS-FR-035 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0284 | XCOM-SYS-SC-001 | refines | XCOM-STK-001 | requirement | planned | `planned` |
| XCOM-L-0285 | XCOM-SYS-SC-001 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0286 | XCOM-SYS-SC-001 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0287 | XCOM-SYS-SC-001 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0288 | XCOM-SYS-SC-002 | refines | XCOM-STK-001 | requirement | planned | `planned` |
| XCOM-L-0289 | XCOM-SYS-SC-002 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0290 | XCOM-SYS-SC-002 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0291 | XCOM-SYS-SC-002 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0292 | XCOM-SYS-SC-003 | refines | XCOM-STK-002 | requirement | planned | `planned` |
| XCOM-L-0293 | XCOM-SYS-SC-003 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0294 | XCOM-SYS-SC-003 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0295 | XCOM-SYS-SC-003 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0296 | XCOM-SYS-SC-004 | refines | XCOM-STK-002 | requirement | planned | `planned` |
| XCOM-L-0297 | XCOM-SYS-SC-004 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0298 | XCOM-SYS-SC-004 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0299 | XCOM-SYS-SC-004 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0300 | XCOM-SYS-SC-005 | refines | XCOM-STK-002 | requirement | planned | `planned` |
| XCOM-L-0301 | XCOM-SYS-SC-005 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0302 | XCOM-SYS-SC-005 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0303 | XCOM-SYS-SC-005 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0304 | XCOM-SYS-SC-006 | refines | XCOM-STK-003 | requirement | planned | `planned` |
| XCOM-L-0305 | XCOM-SYS-SC-006 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0306 | XCOM-SYS-SC-006 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0307 | XCOM-SYS-SC-006 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0308 | XCOM-SYS-SC-007 | refines | XCOM-STK-003 | requirement | planned | `planned` |
| XCOM-L-0309 | XCOM-SYS-SC-007 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0310 | XCOM-SYS-SC-007 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0311 | XCOM-SYS-SC-007 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0312 | XCOM-SYS-SC-008 | refines | XCOM-STK-002 | requirement | planned | `planned` |
| XCOM-L-0313 | XCOM-SYS-SC-008 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0314 | XCOM-SYS-SC-008 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0315 | XCOM-SYS-SC-008 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0316 | XCOM-SYS-SC-009 | refines | XCOM-STK-007 | requirement | planned | `planned` |
| XCOM-L-0317 | XCOM-SYS-SC-009 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0318 | XCOM-SYS-SC-009 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0319 | XCOM-SYS-SC-009 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0320 | XCOM-SYS-SC-010 | refines | XCOM-STK-007 | requirement | planned | `planned` |
| XCOM-L-0321 | XCOM-SYS-SC-010 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0322 | XCOM-SYS-SC-010 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0323 | XCOM-SYS-SC-010 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| XCOM-L-0324 | XCOM-SYS-SC-011 | refines | XCOM-STK-008 | requirement | planned | `planned` |
| XCOM-L-0325 | XCOM-SYS-SC-011 | allocated_to | XCOM-DU-REQ-BASELINE | design_unit | planned | `planned` |
| XCOM-L-0326 | XCOM-SYS-SC-011 | verified_by | XCOM-T-REQ-TRACE | test | planned | `planned` |
| XCOM-L-0327 | XCOM-SYS-SC-011 | derives_from | XCOM-SRC-SPEC-007 | source | established | `957a60723f99c3a31efba1cbd137c454c4acb462` |
