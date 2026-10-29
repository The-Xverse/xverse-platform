# Public execution unit specifications

Status: static inspection implemented in progress; runtime units remain planned.
Capability: specs/022-maestro-public-execution. This is not acceptance or certification.

| Unit | Responsibility and invariants | Verification |
|---|---|---|
| MPX-U01 CanonicalSubmission/ExperimentSelection | Immutable explicit source bytes, selected resource URIs and expected independent digests; document/count/byte bounds; no executable host instructions | public inspection positive, mismatch, invalid XDL, name/size and selection tests |
| MPX-U02 InspectionHost/SchemaPin/TargetBinding | Static host-installed provider and schema identities; duplicate/bounds checks; schema content verified before and after actual compilation; no runtime permit | target rejection and schema replacement tests |
| MPX-U03 inspect_submission | Actual public compiler, exact input/plan/selection agreement, preserved logical device/component identity, no process/writer calls, static-only readiness | installed-package public API and zero-effects tests |
| MPX-U04 EffectiveInspection | Independent JSON copies, canonical receipt and stable domain-separated digest; executionAllowed false until a separate runtime layer actually admits execution | mutation/repeatability test |
| MPX-U05 runtime admission/service | Planned: provider effective configuration, host permissions, lifecycle dispatch, original Argus evidence and resource ownership | not implemented or passed |

Source: src/xverse/maestro/execution/inspection.py and public __init__.py.
Tests: tests/maestro_public/test_inspection.py. Static inspection alone cannot
satisfy MPX-FR-003 effective-provider equality or the full user's three-service goal.
