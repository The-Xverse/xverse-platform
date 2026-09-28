# T026–T029 Codex repair candidate

The successor repairs R-01–R-07 in the runtime and regression tests. R-08 has 93
Phase 6 software requirement records, 19 declared system anchors, scoped
components, unit specifications, validation scenarios, and links generated from
the task work products by `engineering/generate_phase6_trace.py`. The original
T020 records remain historical and are excluded by the strict Phase 6 policy.

The trace generator uses documented requirement-to-test mappings where present.
For 26 requirements without such a mapping, its explicit fallback table selects
contributing cases; each also has a distinct conformance inspection. These inspect
source, configuration, work products, and task history for the stated requirement.
The checks include bounded pattern scans, so independent content review remains
required. The source work products, changed-path inventory, and stage records
must be reviewed alongside the trusted unit, validation, static, conformance,
and pinned target-repository integration evidence.

The previous negative matrix had no current-scope rows and 99 gaps. The earlier
successor matrix had 109 current-scope rows and no structural gaps in a dry probe.
This successor adds the missing ancestry and conformance evidence. Its exact
committed state requires trusted measures and delivery before independent review.

This is a candidate. Independent review, user acceptance, and the subsequent
approved-artifact merge into `xverse-platform/main` remain separate steps.
