# M2 architecture review — XDL Core v0.1

**Date**: 2026-09-20
**Scope**: Proposed XDL specification, schemas, examples, ADR-0009–ADR-0012, Spec Kit package,
and documentary validation.
**Review method**: Separate read-only pass after implementation and automated validation.
**Disposition**: User approved M2 on 2026-09-20. The next capability may be specified; its
implementation remains subject to its own approval.

## Architecture gates

| Concern | Assessment |
|---|---|
| Domain neutrality | Pass: kind names, core collections, examples, and schema enums introduce no industry or provider dependency. |
| M1 semantic traceability | Pass: all 26 M1 concepts have an XDL location or an explicit realization/experiment role; Deployment remains the only logical-to-realization binding. |
| XDL centrality | Pass: one resource language and normalized model are defined; no parallel configuration language or custom grammar appears. |
| Logical/physical separation | Pass: System and Component prohibit realization data; physical realization requires an external asset binding in Deployment. |
| Standards interoperability | Pass: YAML 1.2.2, JSON Schema Draft 2020-12, SemVer, SysML/UML, SSP/FMI/FMUs, and other external semantics are referenced rather than copied. |
| Identity and evolution | Pass: references are explicit, four version dimensions are separate, unknown fields fail, and breaking semantics require a new API version. |
| Failure and readiness | Pass for specification: six ordered gates and diagnostic obligations are defined; live evaluation is accurately deferred. |
| Evidence and maturity | Pass: examples and package use architectural-target/proposed labels and make no runtime or compatibility claim. |
| Repository and production safety | Pass: M2 artifacts are confined to xverse-platform; no legacy or companion runtime surface is changed. |
| Public safety | Pass: examples use `example.invalid`, opaque URNs, placeholder digests, and no credentials or private infrastructure. |

## Findings

**BLOCKER**: none.

**MAJOR**: none.

| ID | Severity | Finding / impact | Disposition |
|---|---|---|---|
| M2-R06 | Resolved MINOR | The first namespace pattern allowed a hyphen-only name even though Profile namespaces require reverse-domain form. | Repaired in the post-review pass: the common pattern now requires two or more dot-separated DNS-style segments; the malformed-namespace negative case passes. |
| M2-R07 | Resolved MINOR | Resource prose allowed a System composition rooted by a node or a device, while the first schema draft required `nodes`. | Repaired in the post-review pass: the schema now requires at least one of non-empty `nodes` or `devices`. |
| M2-R08 | Resolved MINOR | The first documentary semantic checks resolved structured references but did not check several local owner/interface/network/time/resource IDs. | Repaired in the post-review pass: Component/System local relationships, Deployment offered resources, and Scenario time domains are checked. |
| M2-R01 | Accepted MINOR | Schema `$id` values express the intended canonical namespace but are not published endpoints. External consumers cannot retrieve them. | Decide registry and hosting in a separately specified publication capability; local relative `$ref` resolution remains deterministic. |
| M2-R02 | Accepted MINOR | `validate_m2.py` implements the Draft 2020-12 keywords used by these drafts plus selected semantic rules; it is not independent certification by a general standards validator. | Retain the explicit documentary label. Select and test a maintained validator dependency before a production loader capability. |
| M2-R03 | Accepted MINOR | Scenario action/acceptance strings and Deployment lifecycle/readiness conditions are declarative text with no standardized expression or probe semantics. | Define typed execution semantics only in later loader/runtime specifications; do not execute or infer these strings. |
| M2-R04 | Accepted ADVISORY | Profile namespace/conflict behavior is defined, but discovery, registry ownership, signing, and revocation are deferred. | Resolve governance before third-party Profiles are distributed. |
| M2-R05 | Accepted ADVISORY | Bundle/import and conversion behavior is absent, so v1alpha1 examples rely on an explicitly supplied resource set. | Keep implicit lookup prohibited and specify composition only from validated use cases. |

## Review checklist

- [X] The common envelope, all five kinds, identity, references, and version dimensions were reviewed.
- [X] Every schema was compared with its normative resource definition and positive example.
- [X] Logical/realization separation and physical binding rules were reviewed.
- [X] Interface, endpoint, flow, time, observer, metric, lifecycle, and readiness semantics were reviewed.
- [X] Profile namespace isolation and standards-reference rules were reviewed.
- [X] Positive and negative validation evidence was reviewed without treating it as runtime proof.
- [X] Legacy immutability, repository direction, public safety, and maturity labels were reviewed.
- [X] Deferred capabilities were checked for accidental implicit behavior.
- [X] The user approved ADR-0009–ADR-0012 and the M2 acceptance checklist on 2026-09-20.

## Handoff

The user approved M2. Findings M2-R01–M2-R05 remain explicit constraints for later features and do
not authorize their implementation. The next step needs a new Spec Kit capability and scope decision.
