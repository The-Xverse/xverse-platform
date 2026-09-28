# X-COM Capability 007 Requirements Register

> Deterministic projection of `requirements-register.json` (schema version 1).
> Do not edit by hand; regenerate from the model and re-run
> `scripts/validate_xcom_requirements_traceability.py --check-human`.

## Register identity

| Field | Value |
| --- | --- |
| Task | T008 |
| Capability | 007-xcom-core |
| Schema version | 1 |
| Baseline revision | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| Candidate revision rule | Every candidate records its own exact revision and the exact accepted predecessor revision it derives from; acceptance is per candidate and is never inherited from a sibling or inferred from source presence. |
| Requirement levels | stakeholder, system, software |
| Requirements | 91 |
| REF-002 dispositions | 20 |

## Maturity vocabulary

`allocated`, `conflicting`, `deferred`, `implemented`, `needs_clarification`, `partial`, `superseded`

## Authorization records

`ACC001`, `ACC002`, `ACC003`, `ACC004`, `ACC005`, `ACC006`, `ACC007`, `ACC008`, `ACC009`, `ACC010`, `ACC011`, `ACC012`, `ACC013`, `ACC014`, `ACC015`, `ADR-0018`, `ADR-0019`, `ADR-0020`

## Declared counts

| Key | Count |
| --- | ---: |
| XCOM-STK | 8 |
| XCOM-SW-CORE | 10 |
| XCOM-SW-ENB | 4 |
| XCOM-SW-GW | 3 |
| XCOM-SW-INTG | 3 |
| XCOM-SW-OBS | 5 |
| XCOM-SW-STIM | 9 |
| XCOM-SW-XDL | 3 |
| XCOM-SYS-FR | 35 |
| XCOM-SYS-SC | 11 |
| software | 37 |
| stakeholder | 8 |
| system | 46 |

## Requirements

| ID | Level | Family | Owning task | Maturity | Refines | Source anchors |
| --- | --- | --- | --- | --- | --- | --- |
| XCOM-STK-001 | stakeholder | - | T008 | allocated | - | US1, SC-001, SC-002 |
| XCOM-STK-002 | stakeholder | - | T008 | allocated | - | US2, SC-003, SC-004, SC-005 |
| XCOM-STK-003 | stakeholder | - | T008 | allocated | - | US3, SC-006, SC-007 |
| XCOM-STK-004 | stakeholder | - | T008 | allocated | - | US4 |
| XCOM-STK-005 | stakeholder | - | T008 | allocated | - | FR-007, FR-010, FR-013, FR-025 |
| XCOM-STK-006 | stakeholder | - | T008 | allocated | - | FR-001, FR-002, FR-003, FR-031 |
| XCOM-STK-007 | stakeholder | - | T008 | allocated | - | FR-027, FR-028, FR-029, FR-030, FR-035, SC-009, SC-010 |
| XCOM-STK-008 | stakeholder | - | T008 | allocated | - | FR-032, SC-011 |
| XCOM-SW-CORE-001 | software | CORE | T012 | partial | XCOM-SYS-FR-002, XCOM-SYS-FR-003 | FR-002, FR-003 |
| XCOM-SW-CORE-002 | software | CORE | T013 | partial | XCOM-SYS-FR-004, XCOM-SYS-FR-005 | FR-004, FR-005 |
| XCOM-SW-CORE-003 | software | CORE | T013 | partial | XCOM-SYS-FR-006 | FR-006 |
| XCOM-SW-CORE-004 | software | CORE | T014 | partial | XCOM-SYS-FR-007, XCOM-SYS-FR-008 | FR-007, FR-008 |
| XCOM-SW-CORE-005 | software | CORE | T014 | partial | XCOM-SYS-FR-009, XCOM-SYS-FR-010 | FR-009, FR-010 |
| XCOM-SW-CORE-006 | software | CORE | T015 | partial | XCOM-SYS-FR-025 | FR-025 |
| XCOM-SW-CORE-007 | software | CORE | T015 | partial | XCOM-SYS-FR-001, XCOM-SYS-FR-026, XCOM-SYS-FR-028 | FR-001, FR-026, FR-028 |
| XCOM-SW-CORE-008 | software | CORE | T016 | partial | XCOM-SYS-FR-024 | FR-024 |
| XCOM-SW-CORE-009 | software | CORE | T016 | partial | XCOM-SYS-SC-001 | SC-001 |
| XCOM-SW-CORE-010 | software | CORE | T012 | partial | XCOM-SYS-FR-025 | FR-025 |
| XCOM-SW-ENB-001 | software | ENB | T008 | partial | XCOM-SYS-FR-030 | FR-030 |
| XCOM-SW-ENB-002 | software | ENB | T008 | partial | XCOM-SYS-FR-035 | FR-035 |
| XCOM-SW-ENB-003 | software | ENB | T039 | allocated | XCOM-SYS-SC-010 | SC-010 |
| XCOM-SW-ENB-004 | software | ENB | T011 | allocated | XCOM-SYS-FR-029, XCOM-SYS-FR-030 | FR-029, FR-030 |
| XCOM-SW-GW-001 | software | GW | T030 | allocated | XCOM-SYS-FR-022 | FR-022 |
| XCOM-SW-GW-002 | software | GW | T031 | allocated | XCOM-SYS-FR-032 | FR-032 |
| XCOM-SW-GW-003 | software | GW | T032 | allocated | XCOM-SYS-SC-011 | SC-011 |
| XCOM-SW-INTG-001 | software | INTG | T035 | allocated | XCOM-SYS-FR-027 | FR-027 |
| XCOM-SW-INTG-002 | software | INTG | T037 | allocated | XCOM-SYS-FR-029, XCOM-SYS-SC-009 | FR-029, SC-009 |
| XCOM-SW-INTG-003 | software | INTG | T036 | allocated | XCOM-SYS-SC-008 | SC-008 |
| XCOM-SW-OBS-001 | software | OBS | T021 | partial | XCOM-SYS-FR-011 | FR-011 |
| XCOM-SW-OBS-002 | software | OBS | T022 | partial | XCOM-SYS-FR-012, XCOM-SYS-SC-003 | FR-012, SC-003 |
| XCOM-SW-OBS-003 | software | OBS | T022 | partial | XCOM-SYS-FR-013, XCOM-SYS-SC-004 | FR-013, SC-004 |
| XCOM-SW-OBS-004 | software | OBS | T023 | partial | XCOM-SYS-FR-014, XCOM-SYS-SC-005 | FR-014, SC-005 |
| XCOM-SW-OBS-005 | software | OBS | T024 | partial | XCOM-SYS-FR-023 | FR-023 |
| XCOM-SW-STIM-001 | software | STIM | T025 | implemented | XCOM-SYS-FR-015 | FR-015 |
| XCOM-SW-STIM-002 | software | STIM | T025 | implemented | XCOM-SYS-FR-016 | FR-016 |
| XCOM-SW-STIM-003 | software | STIM | T026 | allocated | XCOM-SYS-FR-017, XCOM-SYS-SC-006 | FR-017, SC-006 |
| XCOM-SW-STIM-004 | software | STIM | T027 | allocated | XCOM-SYS-FR-018 | FR-018 |
| XCOM-SW-STIM-005 | software | STIM | T028 | allocated | XCOM-SYS-FR-019 | FR-019 |
| XCOM-SW-STIM-006 | software | STIM | T028 | allocated | XCOM-SYS-FR-020, XCOM-SYS-FR-033 | FR-020, FR-033 |
| XCOM-SW-STIM-007 | software | STIM | T026 | allocated | XCOM-SYS-FR-021 | FR-021 |
| XCOM-SW-STIM-008 | software | STIM | T028 | allocated | XCOM-SYS-FR-034 | FR-034 |
| XCOM-SW-STIM-009 | software | STIM | T029 | allocated | XCOM-SYS-SC-007 | SC-007 |
| XCOM-SW-XDL-001 | software | XDL | T017 | allocated | XCOM-SYS-FR-031, XCOM-SYS-FR-002 | FR-031, FR-002 |
| XCOM-SW-XDL-002 | software | XDL | T018 | allocated | XCOM-SYS-FR-002 | FR-002 |
| XCOM-SW-XDL-003 | software | XDL | T019 | allocated | XCOM-SYS-SC-002 | SC-002 |
| XCOM-SYS-FR-001 | system | - | T008 | allocated | XCOM-STK-006 | FR-001 |
| XCOM-SYS-FR-002 | system | - | T008 | allocated | XCOM-STK-006 | FR-002 |
| XCOM-SYS-FR-003 | system | - | T008 | allocated | XCOM-STK-006 | FR-003 |
| XCOM-SYS-FR-004 | system | - | T008 | allocated | XCOM-STK-001 | FR-004 |
| XCOM-SYS-FR-005 | system | - | T008 | allocated | XCOM-STK-001 | FR-005 |
| XCOM-SYS-FR-006 | system | - | T008 | allocated | XCOM-STK-005 | FR-006 |
| XCOM-SYS-FR-007 | system | - | T008 | allocated | XCOM-STK-005 | FR-007 |
| XCOM-SYS-FR-008 | system | - | T008 | allocated | XCOM-STK-005 | FR-008 |
| XCOM-SYS-FR-009 | system | - | T008 | allocated | XCOM-STK-004 | FR-009 |
| XCOM-SYS-FR-010 | system | - | T008 | allocated | XCOM-STK-005 | FR-010 |
| XCOM-SYS-FR-011 | system | - | T008 | allocated | XCOM-STK-002 | FR-011 |
| XCOM-SYS-FR-012 | system | - | T008 | allocated | XCOM-STK-002 | FR-012 |
| XCOM-SYS-FR-013 | system | - | T008 | allocated | XCOM-STK-005 | FR-013 |
| XCOM-SYS-FR-014 | system | - | T008 | allocated | XCOM-STK-002 | FR-014 |
| XCOM-SYS-FR-015 | system | - | T008 | allocated | XCOM-STK-003 | FR-015 |
| XCOM-SYS-FR-016 | system | - | T008 | allocated | XCOM-STK-003 | FR-016 |
| XCOM-SYS-FR-017 | system | - | T008 | allocated | XCOM-STK-003 | FR-017 |
| XCOM-SYS-FR-018 | system | - | T008 | allocated | XCOM-STK-003 | FR-018 |
| XCOM-SYS-FR-019 | system | - | T008 | allocated | XCOM-STK-003 | FR-019 |
| XCOM-SYS-FR-020 | system | - | T008 | allocated | XCOM-STK-003 | FR-020 |
| XCOM-SYS-FR-021 | system | - | T008 | allocated | XCOM-STK-003 | FR-021 |
| XCOM-SYS-FR-022 | system | - | T008 | allocated | XCOM-STK-004 | FR-022 |
| XCOM-SYS-FR-023 | system | - | T008 | allocated | XCOM-STK-002 | FR-023 |
| XCOM-SYS-FR-024 | system | - | T008 | allocated | XCOM-STK-004 | FR-024 |
| XCOM-SYS-FR-025 | system | - | T008 | allocated | XCOM-STK-005 | FR-025 |
| XCOM-SYS-FR-026 | system | - | T008 | allocated | XCOM-STK-007 | FR-026 |
| XCOM-SYS-FR-027 | system | - | T008 | allocated | XCOM-STK-007 | FR-027 |
| XCOM-SYS-FR-028 | system | - | T008 | allocated | XCOM-STK-007 | FR-028 |
| XCOM-SYS-FR-029 | system | - | T008 | allocated | XCOM-STK-007 | FR-029 |
| XCOM-SYS-FR-030 | system | - | T008 | allocated | XCOM-STK-007 | FR-030 |
| XCOM-SYS-FR-031 | system | - | T008 | allocated | XCOM-STK-006 | FR-031 |
| XCOM-SYS-FR-032 | system | - | T008 | allocated | XCOM-STK-008 | FR-032 |
| XCOM-SYS-FR-033 | system | - | T008 | allocated | XCOM-STK-003 | FR-033 |
| XCOM-SYS-FR-034 | system | - | T008 | allocated | XCOM-STK-003 | FR-034 |
| XCOM-SYS-FR-035 | system | - | T008 | allocated | XCOM-STK-007 | FR-035 |
| XCOM-SYS-SC-001 | system | - | T008 | allocated | XCOM-STK-001 | SC-001 |
| XCOM-SYS-SC-002 | system | - | T008 | allocated | XCOM-STK-001 | SC-002 |
| XCOM-SYS-SC-003 | system | - | T008 | allocated | XCOM-STK-002 | SC-003 |
| XCOM-SYS-SC-004 | system | - | T008 | allocated | XCOM-STK-002 | SC-004 |
| XCOM-SYS-SC-005 | system | - | T008 | allocated | XCOM-STK-002 | SC-005 |
| XCOM-SYS-SC-006 | system | - | T008 | allocated | XCOM-STK-003 | SC-006 |
| XCOM-SYS-SC-007 | system | - | T008 | allocated | XCOM-STK-003 | SC-007 |
| XCOM-SYS-SC-008 | system | - | T008 | allocated | XCOM-STK-002 | SC-008 |
| XCOM-SYS-SC-009 | system | - | T008 | allocated | XCOM-STK-007 | SC-009 |
| XCOM-SYS-SC-010 | system | - | T008 | allocated | XCOM-STK-007 | SC-010 |
| XCOM-SYS-SC-011 | system | - | T008 | allocated | XCOM-STK-008 | SC-011 |

## REF-002 dispositions

| ID | Disposition | Maturity | Owner | Covers | Reason |
| --- | --- | --- | --- | --- | --- |
| XVE-SYS-0139 | allocated | architectural-target | - | XCOM-SYS-FR-004, XCOM-SYS-FR-005 | Allocated to the first X-COM prototype; remains architectural-target until implemented source and exact-candidate evidence pass review. |
| XVE-SYS-0140 | allocated | architectural-target | - | XCOM-SYS-FR-011 | Allocated to the first X-COM prototype; remains architectural-target until implemented source and exact-candidate evidence pass review. |
| XVE-SYS-0141 | deferred | architectural-target | protocol/provider capabilities | - | Deferred to protocol/provider capabilities; capability 007 records but does not implement it. |
| XVE-SYS-0142 | allocated | architectural-target | - | XCOM-SYS-FR-002 | Allocated to the first X-COM prototype; remains architectural-target until implemented source and exact-candidate evidence pass review. |
| XVE-SYS-0143 | deferred | architectural-target | registry/reconfiguration capabilities | - | Deferred to registry/reconfiguration capabilities; capability 007 records but does not implement it. |
| XVE-SYS-0144 | deferred | architectural-target | Security/deployment capabilities | - | Deferred to Security/deployment capabilities; capability 007 records but does not implement it. |
| XVE-SYS-0145 | allocated | architectural-target | - | XCOM-SYS-FR-003 | Allocated to the first X-COM prototype; remains architectural-target until implemented source and exact-candidate evidence pass review. |
| XVE-SYS-0146 | allocated | architectural-target | - | XCOM-SYS-FR-005 | Allocated to the first X-COM prototype; remains architectural-target until implemented source and exact-candidate evidence pass review. |
| XVE-SYS-0147 | allocated | architectural-target | - | XCOM-SYS-FR-007 | Allocated to the first X-COM prototype; remains architectural-target until implemented source and exact-candidate evidence pass review. |
| XVE-SYS-0148 | deferred | architectural-target | record/replay, edge/cloud, and Argus adapters | - | Deferred to record/replay, edge/cloud, and Argus adapters; capability 007 records but does not implement it. |
| XVE-SYS-0149 | allocated | architectural-target | - | XCOM-SYS-FR-025 | Allocated to the first X-COM prototype; remains architectural-target until implemented source and exact-candidate evidence pass review. |
| XVE-SYS-0150 | deferred | architectural-target | record/replay, edge/cloud, and Argus adapters | - | Deferred to record/replay, edge/cloud, and Argus adapters; capability 007 records but does not implement it. |
| XVE-SYS-0151 | deferred | architectural-target | record/replay, edge/cloud, and Argus adapters | - | Deferred to record/replay, edge/cloud, and Argus adapters; capability 007 records but does not implement it. |
| XVE-SYS-0152 | allocated | architectural-target | - | XCOM-SYS-FR-009 | Allocated to the first X-COM prototype; remains architectural-target until implemented source and exact-candidate evidence pass review. |
| XVE-SYS-0153 | deferred | architectural-target | Security/deployment capabilities | - | Deferred to Security/deployment capabilities; capability 007 records but does not implement it. |
| XVE-SYS-0154 | allocated | architectural-target | - | XCOM-SYS-FR-010 | Allocated to the first X-COM prototype; remains architectural-target until implemented source and exact-candidate evidence pass review. |
| XVE-SYS-0155 | deferred | architectural-target | Security/deployment capabilities | - | Deferred to Security/deployment capabilities; capability 007 records but does not implement it. |
| XVE-SYS-0156 | allocated | architectural-target | - | XCOM-SYS-FR-006 | Allocated to the first X-COM prototype; remains architectural-target until implemented source and exact-candidate evidence pass review. |
| XVE-SYS-0157 | deferred | architectural-target | registry/reconfiguration capabilities | - | Deferred to registry/reconfiguration capabilities; capability 007 records but does not implement it. |
| XVE-SYS-0158 | deferred | architectural-target | Faults/Runtime recovery | - | Deferred to Faults/Runtime recovery; capability 007 records but does not implement it. |
