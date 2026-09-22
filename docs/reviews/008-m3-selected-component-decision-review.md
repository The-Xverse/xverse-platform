# M3 selected-component decision review

**Date**: 2026-09-20

**Reviewer**: Codex, at the user's explicit request for self-review

**Scope**: SD-0001 candidate comparison, source provenance, interface boundary, lifecycle proposal,
ownership, isolation, evidence policy, exclusions, and decision completeness.

**Method**: Separate read-only architecture pass against the approved M3 selected-component decision
contract and M0 revision-pinned evidence. No legacy source was changed or executed.

**Disposition**: The gateway is a reasonable first candidate, but the decision is BLOCKED and cannot
satisfy platform T019, compatibility T012–T015, or ACC015.

**Review decision**: Accept the gateway nomination, reproducible candidate artifact, and exact blocked
XDL graph; reject completion of the selected-component gate until SD-R03–SD-R06 and SD-R08 are resolved with evidence
and target-owner review.

## Findings

| ID | Severity | Finding / impact | Required disposition | Status |
|---|---|---|---|---|
| SD-R01 | BLOCKER | The source commit is pinned and the `v1.0.0` release has no attached asset, so the initial record had no built gateway, runtime-library set, selected configuration bundle, or build attestation. | Produce a reproducible candidate bundle and public-safe manifest without modifying or executing legacy source. | Resolved by authorized build evidence; owner acceptance and retention remain under SD-R03/SD-R06 |
| SD-R02 | BLOCKER | There was no exact catalog identity or candidate-specific Component, System, Deployment, and runtime Profile revision. Provider selection and plan binding would therefore have been inferred. | Author the candidate XDL graph only from approved artifact facts, validate it, and represent unresolved decision evidence as fail-closed planning blockers. | Resolved by runtime Profile v0.2 and the validated SD-0001 graph; plan remains blocked |
| SD-R03 | BLOCKER | Isolated environment identity, host owner, containment owner, resource limits, and process-provider isolation attestation are absent. Static audit also finds a withheld private endpoint compiled into the candidate. A safe execution boundary cannot be evaluated. | Name accountable owners and pin the environment, limits, filesystem/network boundary, endpoint disposition, and matching attestation. | Open; strengthened by IA-R01 |
| SD-R04 | MAJOR | The source's running message and the current supervisor's fixed delay do not prove interface readiness. Static audit finds detached work and no graceful-stop/readiness API. Timeout, stop escalation, and failure behavior remain unspecified. | Approve a bounded external readiness probe and exact prepare/start/observe/stop/cleanup timeouts and outcomes. | Open; narrowed by IA-R03/IA-R05 |
| SD-R05 | MAJOR | Static evidence now pins route counts, vsomeip 3.6.1, transport mode, and selected transformation classes, but native-memory float encoding, Zenoh version, peer ABI, exact restricted mapping, and interoperability remain unverified. | Owner-review the restricted mapping/peer ABI, accept the public projection, and test only the approved minimal interface path after authorization. | Open; public projection drafted |
| SD-R06 | MINOR | A restricted location and retention period for manifests, exact mappings, owner attestations, raw payload-bearing logs, and later execution evidence have not been assigned. | Assign a controlled retention location before completing the decision. | Open; strengthened by IA-R04 |
| SD-R07 | ADVISORY | The candidate aligns with a future X-COM compatibility edge, but X-COM is an architectural target and has no implemented runtime namespace here. | Keep this relationship descriptive until a later Spec Kit feature and ADR define it. | Open; non-blocking |
| SD-R08 | MAJOR | The source-provided vendor binaries contain historical absolute build-path strings, system runtime libraries remain outside the bundle, and the Zenoh library lacks trustworthy semantic-version metadata. This prevents treating the bundle as an approved isolated execution environment. | Target owner accepts the exact restricted bundle/environment or authorizes a reproducible vendor-library rebuild/sanitization; pin all system runtime dependencies and Zenoh provenance in the environment. | Open; strengthened by IA-R06 |

## Positive assessment

The candidate is narrower than the AutoVerse supervisor, uses the existing process-action shape, and
keeps protocol implementation outside platform core. SD-0001 distinguishes observed, documented,
inferred, unknown, and withheld information; rejects source hashes as executable evidence; defines an
exact-handle ownership ceiling; excludes broad cleanup; and preserves legacy checkout immutability.
Those qualities justify nomination for review but do not close any open finding.

## Self-review repairs

| ID | Severity | Finding before repair | Resolution | Status |
|---|---|---|---|---|
| SD-S01 | MAJOR | The first candidate comparison omitted other M0 reusable bridges, weakening the claim that the gateway was the best first boundary. | SD-0001 now compares the CAN, ROS2, AAOS/VHAL, and CARLA alternatives and limits the recommendation to the active S-CORE/SOME/IP cruise-control path. | Resolved |
| SD-S02 | MAJOR | Cleanup wording could be read as deleting retained evidence, contrary to the evidence-preservation contract. | Cleanup now distinguishes disposable owned resources from evidence that must be preserved. | Resolved |
| SD-S03 | MINOR | The maturity phrase “candidate selected for review” could be mistaken for a completed selected-component decision. | Maturity now reads “nominated candidate; selection incomplete; runtime unverified.” | Resolved |

After these repairs, the self-review found no unresolved document-quality BLOCKER or MAJOR issue.
SD-R03–SD-R05 remain open because the underlying environment, lifecycle, and interface evidence is
absent; prose changes cannot resolve them.

## Authorized reproducible-build addendum

The user explicitly authorized a build-only pass after the self-review. The source was cloned at the
exact SD-0001 commit into temporary storage, its sole Git LFS object was digest-checked, and the
checkout was made read-only before out-of-tree configuration. No gateway, peer, middleware, network
interface, or production workload was started.

The default build failed a stronger reproducibility check: identical frozen sources at different
absolute paths produced different executable hashes because CMake appended the source location to
RPATH. A recorded external CMake overlay removed those paths, retained only the intended
`$ORIGIN`-relative lookup, and disabled the path-sensitive build ID. Two builds from distinct source
paths then produced byte-identical gateway digest
`1fcf49058ff358dc7e81b11f18f4f288c709409b1ac0d9d7f3258b6e12b4b7c2`.

The deterministic candidate archive has SHA-256
`6ce98220d1c4997a20d2b85464e7e1550e8347d68c572bfb63586c150f41f946`. Its public-safe
[build report](../../specs/005-component-catalog-compat-runtime/evidence/SD-0001-build-evidence.md),
[artifact manifest](../../specs/005-component-catalog-compat-runtime/evidence/SD-0001-artifact-manifest.json),
and exact [CMake overlay](../../specs/005-component-catalog-compat-runtime/evidence/SD-0001-reproducible-gateway.cmake)
resolve SD-R01's missing-artifact evidence. The archive is excluded from Git and temporarily retained;
SD-R06 and SD-R08 prevent final artifact approval.

## Candidate XDL addendum

Runtime Profile v0.2 and the four public-safe SD-0001 XDL resources now derive the exact catalog
identity and deterministic blocked plan recorded in the decision. This resolves SD-R02 without
supplying defaults for any external evidence gap. The separate
[candidate XDL review](009-m3-candidate-xdl-blocker-review.md) found no unresolved code/document
BLOCKER or MAJOR issue and confirms that all seven declared blockers prevent planning and execution.

## Gate checklist

- [X] Current-path and other reusable-adapter alternatives and domain-neutrality were compared.
- [X] Legacy source and launcher evidence is revision-pinned.
- [X] Public-safe interface summary and withheld fields are identified.
- [X] Proposed lifecycle uses typed process actions and exact ownership handles.
- [X] Legacy checkout immutability and prohibited actions are explicit.
- [X] Reproducible candidate executable/dependency/configuration artifact is pinned without execution.
- [X] Exact candidate XDL graph and catalog identity validate and yield a deterministic blocked plan.
- [ ] Environment, owners, limits, isolation, and secrets status are approved.
- [ ] Readiness, timeout, shutdown, and failure contracts are measurable.
- [ ] Interface/protocol subset and restricted evidence retention are approved.
- [X] Architecture self-review accepts the candidate nomination.
- [ ] Target owner approves the completed selection record after its evidence fields are closed.

## Review conclusion

SD-0001 is complete as a blocked candidate assessment with reproducible build evidence and an exact
catalog identity. It is incomplete as a
selected-component decision. No finding may be closed by inference from repository names, mutable
tags, supervisor behavior, local paths, or fixture results. Once SD-R03–SD-R06 and SD-R08 are
resolved, a new review pass must verify the final record before implementation authorization is
requested.
