# SWE.3 Unit specifications (EARS)

## XCOM-TYPE-UNIT-001 — CommunicationContract [ubiquitous]

The CommunicationContract shall create an immutable logical contract only when its bounded identity, semantic version, schema identity and version, interaction kind, and compatible directions are complete and consistent.

Source: XCOM-TYPE-001, XCOM-TYPE-002, XCOM-TYPE-003.

Verification intent: Run positive construction and table-driven missing, over-bound, version, interaction, and direction rejection tests.

## XCOM-TYPE-UNIT-002 — CommunicationItem [ubiquitous]

The CommunicationItem shall create an immutable bounded item only when every required logical, schema, origin, time, causal, route, and provider field is present and consistent with its communication contract.

Source: XCOM-TYPE-002, XCOM-TYPE-003.

Verification intent: Run complete-item construction plus reordered table-driven rejection cases for every required field and bound.

## XCOM-TYPE-UNIT-003 — DiagnosticSet [ubiquitous]

The DiagnosticSet shall expose stable codes and deterministic ordering for diagnostics containing severity, phase, affected identity, reason, and correction.

Source: XCOM-TYPE-004.

Verification intent: Compare exact codes, fields, and sorted serialized views across reordered inputs.

## XCOM-TYPE-UNIT-004 — CoreValueResult [ubiquitous]

The CoreValueResult shall contain exactly one valid value or one non-empty immutable diagnostic sequence and shall perform no hidden I/O or ambient lookup.

Source: XCOM-TYPE-003, XCOM-TYPE-004, XCOM-TYPE-005.

Verification intent: Test success/error exclusivity, lifetime after input destruction, const concurrent reads, and forbidden API/dependency scans.
