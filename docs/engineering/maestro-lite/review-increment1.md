# Preparation increment — separate review pass

Reviewer: current Codex session, separate read-only pass; no independent agent or factory review is claimed.
Date: 2026-10-18. Subject: initial U1/U6 working candidate over platform
`c2997c0f810d117cf45b2e34a4011b3ba7219494`.

Findings recorded before successor edits:

| ID | Severity | Evidence | Required repair |
| --- | --- | --- | --- |
| PREP-REV-01 | MAJOR | A real loader/compiler fixture with `observe-source` and no explicit dependsOn returns both `start-source` and `observe-source` eligible at tick zero with no completed steps. The graph also lacks a join from the start step's completion into later phases. | Include implicit phase and graph-derived step predecessors in static eligibility. This remains static eligibility, never live readiness or execution authority. |
| PREP-REV-02 | MAJOR | Flow pointer `xdl://org.xverse.experiment/system/sample-loop#/spec/flows/sample-flow` uses an ID as an array index. Step/binding pointers have the same defect. | Preserve actual normalized-XDL array indices, with the selected resource URI, and test resolution against original content. |
| PREP-REV-03 | MINOR | Limits validates positivity but permits max_units/max_steps larger than the declared engineering caps. | Reject bound enlargement beyond this increment's declared caps. |
| PREP-REV-04 | MINOR | Ruff reports two unused imports: `Mapping` in projection and `replace` in clock tests. | Remove unused imports and rerun the relevant checks. |

Initial verification: 45 feature checks passed in 4.21 seconds; an offline wheel was built. These facts do not resolve the findings. The initial full platform suite was still running when this review was recorded; its final result is recorded separately. The first attempted feature run used the platform venv without pytest; the second exposed a test adapter passing text instead of bytes to validate_sources. The adapter was corrected; no behavior claim is based on those failed attempts.

The historical rejected implementation's false-success facade and process helper are excluded. No descriptor/C1, host watchdog, lifecycle evidence, source-parent semantics, factory admission, acceptance or merge is verified by this preparation increment.

## Successor verification findings, before the next repair

`evidence/feature-tests-review1.log` records 48 passed and two failed cases. PREP-REV-01 needs one additional join: the dependent cleanup must precede the prerequisite's explicit stop dispatch, and the dependent stop-step completion must precede cleanup. The graph previously waited at termination but static dispatch could still become eligible early. PREP-REV-02 also needs the full extension pointer `/extensions/io.xverse.experiment/dependsOn`, rather than a nonexistent direct step member. These are recorded defects, not passing verification.

The first full platform run records 603 passed, 21 failed and 24 subtests. All 21 failures concern missing test-environment build tooling or subprocess imports without an installed distribution. A separate Python 3.13 environment now contains the build tools and an editable installation of this isolated candidate. The failure log is retained; final regression must run after source repair in that environment. No accepted Argus source or test is changed to accommodate it.

## Final read-only review disposition

Source manifest SHA-256: `ce008c3274de56f9fc8ac605cb82bbb312db6a0889e34d319bd5d684bf4ebc82`.
PREP-REV-01–04 have no remaining finding within this increment: phase/teardown dispatch
joins are explicit, pointers resolve actual XDL records, engineering caps cannot be enlarged,
and lint passes. The final wheel's five checked import identities match the exact source.
The source-excluded consumer passes 50 checks; the owning-platform Python suite passes
629 tests and 24 subtests, with the bound increment source unchanged during verification.
Earlier failures remain retained. Editable-install staleness was resolved by installing
the rebuilt wheel; a final stale test-pointer assertion was corrected before that build.

Verdict: **reviewed partial preparation candidate; not full Phase 3 delivery or runtime readiness**.
The review is by this same Codex session in a separate pass, not a separate agent or
independent factory reviewer. The full descriptor/C1, trusted trace, lifecycle/evidence,
source-parent and acceptance gates remain open. No process-mode proof is inferred from
the existing platform's owned-fixture regression checks. Next: U2 exact permit admission,
then the separately admitted bounded supervisor/broker and evidence work.
