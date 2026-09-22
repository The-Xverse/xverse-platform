# SD-0001: Zenoh/SOME-IP gateway candidate

**Decision ID**: SD-0001

**Status**: Deferred by ADR-0018; remains BLOCKED as a selected-component decision

**Decision date**: 2026-09-20

**Reviewers**: Codex architecture self-review completed 2026-09-20; legacy target-owner review pending

**Legacy target owner**: Unavailable in the inspected evidence; owner review pending

**Decision contract**: [selected-component-decision-template.md](../contracts/selected-component-decision-template.md)

**Review**: [M3 selected-component decision review](../../../docs/reviews/008-m3-selected-component-decision-review.md)

**Companion contract**: [Zenoh/SOME-IP gateway provider contract candidate](../../../../xverse-compat/specs/001-compatibility-provider-boundary/contracts/zenoh-someip-gateway.md)

This record nominates the `The-Xverse/zenoh2someip_bridge` gateway process as the first legacy
compatibility candidate. It does not complete platform T019 or compatibility T012, authorize a
target-specific provider, grant an execution permit, or establish protocol compatibility or parity.
The decision fails closed until every BLOCKED field below is resolved and owner-reviewed. Target-specific
work does not resume until the ADR-0018 platform-baseline gate also passes.

## Evidence language

- **Observed** means present in revision-pinned source or repository metadata.
- **Documented** means claimed by that pinned source but not demonstrated here.
- **Inferred** means an architectural recommendation requiring review.
- **Unknown** means the evidence does not establish the field.
- **Withheld** means detail is intentionally excluded from this public-safe record.

## Candidate comparison and rationale

| Candidate | Evidence-based fit | Reason for disposition |
|---|---|---|
| `zenoh2someip_bridge` gateway process | Observed C++17 executable target; documented bidirectional Zenoh/SOME/IP boundary; imported and started as one process by the pinned AutoVerse launcher. | **Nominated.** It is the narrowest reusable adapter on the current cruise-control path and can remain external to platform core. |
| `zenoh2can_bridge` process | Observed configurable Python bridge with virtual and physical CAN backends; imported by AutoVerse but absent from its current supervisor steps. | Deferred: a virtual-CAN proof may be simpler, but it would not exercise the active S-CORE/SOME-IP cruise-control boundary selected by the current launcher. Physical CAN also adds hardware ownership and fidelity questions. |
| `zenoh2ros2_bridge` process | Observed configurable Python bridge; imported by AutoVerse but absent from its current supervisor steps. | Deferred: the active reverse callback supports a narrower message shape than the generic documentation suggests, and ROS2 is not part of the current launcher path. |
| `aaos-vhal-bridge` process | Observed Python UDP/VHAL gateway. | Deferred: it is absent from the current manifest and requires an emulator, adb, and platform-specific VHAL behavior. |
| `carla-simulator-bridge` process | Observed current launcher integration and Python process boundary. | Deferred: simulator, graphical/input, client-restart, and CARLA API ownership create a wider first execution boundary. |
| `vcu-zenoh-python` process | Observed Python entry point and current launcher integration. | Not selected first: it contains automotive control behavior, so it is a less domain-neutral compatibility proof. |
| AutoVerse supervisor | Observed multi-process startup and broad name/port cleanup. | Excluded: its lifecycle boundary is wider than one owned process and conflicts with exact-handle cleanup. |
| S-CORE containers | Documented container workloads and SOME/IP services. | Deferred: container/image provenance, pre-existing state, and container-specific lifecycle semantics are not covered by the current process action. |

The nomination is an architectural inference from the [M0 migration classification](../../../docs/legacy/MIGRATION_CLASSIFICATION.md)
and [interface catalog](../../../docs/legacy/INTERFACE_CATALOG.md). A future provider would sit at a
compatibility edge associated with X-COM; this does not make the legacy gateway part of X-COM or
change its ownership.

## Identity and revision gate

| Required field | Evidence and decision | Gate |
|---|---|---|
| Source repository | Observed `The-Xverse/zenoh2someip_bridge`. | PASS |
| Source revision | Observed commit `7c393c9f5a49239c76122486c49cb1993164475c`; the M0 snapshot resolved the imported `v1.0.0` reference to this commit. The full commit, rather than the mutable tag, is the source baseline. | PASS |
| Catalog identity | `xdl://io.xverse.compat.legacy/deployment/sd0001-gateway-candidate#binding/gateway-process-binding`. | PASS |
| Component revision | `xdl://io.xverse.compat.legacy/component/zenoh-someip-gateway`, version `0.1.0`, source revision `7c393c9f5a49239c76122486c49cb1993164475c`. | PASS |
| System revision | `xdl://io.xverse.compat.legacy/system/zenoh-someip-gateway-system`, version `0.1.0`, provenance revision `sd0001-xdl-v1`. | PASS |
| Deployment revision | `xdl://io.xverse.compat.legacy/deployment/sd0001-gateway-candidate`, version `0.1.0`, provenance revision `sd0001-xdl-v1`. | PASS |
| Runtime Profile revision | `xdl://io.xverse.runtime/profile/compatibility-runtime`, version `0.2.0`, provenance revision `m3-sd0001-planning-blockers-v1`. | PASS |

The public-safe candidate graph is stored under [`xdl/candidates/sd0001`](../../../xdl/candidates/sd0001/)
and validates against the runtime Profile v0.2 schema. It derives plan digest
`sha256:ccab18b9980cae1be7537cd13be9f3cbd5b2a0e6a3ddae33a3a98a8560a699cf` with seven declared
blockers. This closes identity ambiguity without inventing the missing environment or approvals.

| Candidate XDL file | SHA-256 |
|---|---|
| `component.xdl.yaml` | `fca3fbd7aeda202bbb974d22e3d87b07b373342539203f8cfd68a35cf6657280` |
| `system.xdl.yaml` | `970d0562433ccac9359269ef664940d912805c8f7e7b789c5e36edd88ddfffc6` |
| `deployment.xdl.yaml` | `4a9f1f19f3e9fc310d67606fb8fb048c41b62d93fc1d1837513fb5d77e58f626` |
| `runtime-profile.xdl.yaml` | `11711aae1955f77386ddce58483c088519a9be8405c8f7e7b789c5e36edd88ddfffc6` |

The companion [`candidate.lock.json`](../../../xdl/candidates/sd0001/candidate.lock.json), SHA-256
`8656343b6e01475e17e472ac74fb2cd9929c4ec444efc0d74c516d113fa58693`, also pins the Profile schema,
provider, artifact, resource versions, plan digest, and expected blocker set. The
[closure packet](../evidence/SD-0001-closure-packet.md) defines the evidence required to revise it.

## Artifact and provenance gate

The source revision is immutable evidence. The user subsequently authorized a build-only provenance
pass, producing a reproducible candidate artifact without executing it.

| Evidence | Revision-pinned observation | Decision consequence |
|---|---|---|
| [README](https://github.com/The-Xverse/zenoh2someip_bridge/blob/7c393c9f5a49239c76122486c49cb1993164475c/README.md) | Git blob `6860a077e910f5575a6dda307705b1cbe3f8a3c2`; documents Git LFS prerequisites and the build/run sequence. | Documentation evidence only. |
| [CMake definition](https://github.com/The-Xverse/zenoh2someip_bridge/blob/7c393c9f5a49239c76122486c49cb1993164475c/zenoh-someip-bridge/CMakeLists.txt) | Git blob `da061b778946a82e1da6f99d04b398b0942b4dfb`; declares the C++17 `gateway` executable and external Zenoh/vsomeip libraries. | Establishes a build target, not a built artifact. |
| [Entry point](https://github.com/The-Xverse/zenoh2someip_bridge/blob/7c393c9f5a49239c76122486c49cb1993164475c/zenoh-someip-bridge/src/main.cpp) | Git blob `4c5b5c134867e00151df3d2bb0630f455a4f5b65`; loads a relative mapping, starts both bridges and the router, then remains active. | Establishes process shape; does not prove readiness. |
| [Mapping configuration](https://github.com/The-Xverse/zenoh2someip_bridge/blob/7c393c9f5a49239c76122486c49cb1993164475c/zenoh-someip-bridge/config/mapping.json) | Git blob `2c9b9967f1ddda1b9e0fb6afd9690fdff76b99f0`. | Pins source configuration; exact identifiers and payload details are withheld here. |
| [Gateway middleware configuration](https://github.com/The-Xverse/zenoh2someip_bridge/blob/7c393c9f5a49239c76122486c49cb1993164475c/zenoh-someip-bridge/config/vsomeip.gateway.json) | Git blob `1df4bfa960f75c0a64d1058bfd6a2b79a2abaf61`. | Pins source configuration; deployment values are withheld here. |
| Third-party library entries | The authorized build materialized the one Git LFS object, resolved the versioned vsomeip files, and recorded every bundled file and symlink in a public-safe manifest. | Candidate dependencies are pinned; system runtime libraries remain environment dependencies. |
| [Release `v1.0.0`](https://github.com/The-Xverse/zenoh2someip_bridge/releases/tag/v1.0.0) | GitHub release metadata inspected on 2026-09-20 reports zero attached assets. | The release label supplies no downloadable executable artifact to pin. |
| [Authorized build evidence](../evidence/SD-0001-build-evidence.md) | Two builds from distinct frozen source paths produced a byte-identical gateway after applying the recorded external CMake overlay; the legacy checkout remained unchanged. | Supplies candidate build provenance without runtime evidence. |
| [Artifact manifest](../evidence/SD-0001-artifact-manifest.json) | Pins the gateway, selected configuration, Zenoh library, vsomeip library set, toolchain, relative RPATH, and limitations. | Supplies a reviewable candidate artifact boundary. |

**Runtime artifact digest**: Candidate archive SHA-256
`6ce98220d1c4997a20d2b85464e7e1550e8347d68c572bfb63586c150f41f946`; gateway SHA-256
`1fcf49058ff358dc7e81b11f18f4f288c709409b1ac0d9d7f3258b6e12b4b7c2`. The deterministic archive
was produced twice with byte-identical output. **PASS for build provenance; execution approval absent**.

The candidate is not yet an approved runtime artifact. Its restricted durable retention location is
unassigned, system runtime libraries belong to the still-unpinned environment, and bundled vendor
binaries contain historical absolute build-path strings whose values are withheld. The target owner
must approve the manifest and either accept those binaries within an isolated environment or approve
their reproducible rebuild/sanitization.

The [static interface audit](../evidence/SD-0001-static-interface-audit.md) additionally finds one
withheld private Zenoh endpoint compiled into the source/binary and outside the selected JSON files.
This makes the exact candidate environment-specific and requires owner acceptance within the isolated
network or an independently authorized reproducible configurable rebuild.

On 2026-09-21, the user selected the configurable-rebuild disposition. [ADR-0017](../../../docs/adr/ADR-0017-controlled-derivative-rebuilds.md)
defines an external digest-pinned patch and two-clean-build strategy owned by `xverse-compat`. The
reusable mechanism is implemented and tested only with synthetic fixtures. This selects a remediation
strategy; it does not supply the restricted patch, choose a peer ABI or deployment value, produce a
replacement artifact, approve OS containment, or close any candidate planning blocker.

## Environment, ownership, and resources

| Required field | Current decision | Gate |
|---|---|---|
| Isolated environment identity | Unknown; no immutable image, VM, container, or host-environment revision was supplied. | **BLOCKED** |
| Host owner | Unknown; no accountable operator or team appears in the reviewed evidence. | **BLOCKED** |
| Rollback/containment owner | Unknown; it must be named separately if responsibility differs from the host owner. | **BLOCKED** |
| Filesystem boundary | Inferred requirement: stage the approved artifact/config bundle in a dedicated execution root because the entry point consumes a relative configuration path. Exact root is intentionally not chosen here. | **BLOCKED** |
| Network boundary | Unknown. Exact Zenoh and SOME/IP reachability and denied routes need owner approval. | **BLOCKED** |
| Resource limits | Unknown for CPU, memory, file descriptors, process count, logs, and queue pressure. | **BLOCKED** |
| Isolation attestation | Absent. The platform process provider requires a matching caller-supplied attestation and does not itself create an OS sandbox. | **BLOCKED** |
| Secret dependency | The two selected runtime JSON files are syntactically valid and contain no observed credential-named field, private IPv4 address, or absolute home path. The future environment allowlist must remain secret-free. | PASS for declared candidate files; environment remains **BLOCKED** |

No private path, infrastructure address, credential value, or lab-specific host identity is recorded
in this document.

## Interface and protocol boundary

The public-safe boundary is a gateway process translating configured Zenoh keys and payloads to and
from configured SOME/IP services/events. The source documentation requires distinct identities for
the provider and consumer directions. Exact identifiers, routes, payload fields, and deployment
addresses are withheld from this record and must be reviewed in a restricted artifact manifest.

Observed source and documented architecture do not establish runtime interoperability. The supported
Zenoh API/version, SOME/IP/vsomeip API and wire subset, serialization, units, timing, loss/retry
behavior, discovery assumptions, and failure behavior remain unknown. The target-specific contract
must freeze these limits before implementation. A successful process start cannot satisfy that
contract.

Static inspection now establishes a narrower public projection: four configured Zenoh→SOME/IP routes,
two reverse routes, bundled vsomeip 3.6.1, UDP service discovery, unreliable selected event operations,
three float-related forward transformations, one boolean normalization, and raw-byte reverse
forwarding. It also shows native-memory float encoding without a portable byte-order/ABI schema, a
digest-pinned but semantically unversioned Zenoh library, payload-bearing logs, detached work, and no
graceful-stop/readiness API. Exact identifiers and endpoint/configuration values remain withheld. These
facts constrain the future contract but do not resolve SD-R03–SD-R06 or SD-R08.

## Proposed lifecycle boundary

These actions are proposed constraints for review, not executable values or authorization.

| Phase | Proposed target-specific rule | Missing evidence |
|---|---|---|
| Prepare | Verify the complete artifact/environment manifest, stage only the approved bundle in the isolated root, validate configuration consistency, prove required interfaces are available, and acquire the platform mutation lease before durable intent. | Exact manifest, validation command, owners, isolation identity, and limits. |
| Start | Use the platform's typed process action with an absolute approved `gateway` path, no shell, an explicit working directory compatible with the relative configuration lookup, closed inherited handles, and an allowlisted non-secret environment. | Absolute staged paths, environment allowlist, and start timeout. |
| Observe | Require a bounded, externally observed probe showing the approved Zenoh and SOME/IP endpoints are registered and the selected minimal message path behaves as declared. | Probe design, peers, expected results, failure codes, and observe timeout. |
| Stop | Revalidate the exact provider-issued ownership handle, signal only the owned process group, wait for a bounded shutdown, and report remaining state without name-based cleanup. | Approved signal/escalation policy and stop timeout. |
| Cleanup | Remove only disposable resources recorded in that ownership handle, preserve retained evidence, and never scan or stop processes by name or port. | Owned-resource list, cleanup timeout, and containment owner. |

The entry point emits a running message after starting internal objects, but this is not an approved
readiness signal because it does not demonstrate external session registration or message transfer.
Fixed delays from the existing supervisor are likewise excluded.

REF-001 describes S-CORE starting before this gateway, while the revision-pinned current AutoVerse
launcher starts the gateway before S-CORE. These are distinct documented and observed accounts. Their
ordering and readiness dependencies remain unselected pending target-owner evidence.

## Provider ownership and handle behavior

The future provider must use the platform-selected process action and return one opaque ownership
handle bound to the exact execution ID, plan action, provider ID/kind, artifact manifest, environment,
and concrete process-group identity. Observe, stop, cleanup, and reconciliation must reject a partial,
forged, stale, or rediscovered handle. Start and stop remain idempotent by execution identity, and
mutation remains exclusive for the selected catalog/environment identity.

The process, its staged files, and resources it creates within the approved boundary are the maximum
candidate ownership scope. Zenoh routers, SOME/IP peers, S-CORE containers, the AutoVerse supervisor,
other host processes, shared ports, and legacy checkouts are outside that scope.

## Evidence, retention, and maturity

- Public evidence is retained in this decision, the M0 inventory, and the associated architecture
  review, build report, and artifact manifest. It includes revision pins, hashes, and summarized
  observations without proprietary excerpts.
- The binary archive remains in temporary local storage and is excluded from Git. Exact configuration,
  the binary bundle, environment identity, probe captures, and owner attestations require an approved
  restricted retention location and period. Those remain unknown. **BLOCKED**.
- Runtime logs and evidence must be projected through the platform public-safety rules before they
  enter this repository. Credentials, private addresses, raw proprietary payloads, and unrestricted
  configuration must not be copied here.
- Maturity remains **nominated candidate; selection incomplete; runtime unverified**. This record supports no
  compatibility, parity, production-readiness, safety, or performance claim.

## Explicit exclusions

The user authorized and this record accounts for the original build-only pass plus implementation of
the controlled rebuild envelope with synthetic fixtures. These completed passes did not authorize a
restricted SD-0001 patch or running test
peers, starting a Zenoh router, contacting SOME/IP services, starting the gateway, running AutoVerse,
starting S-CORE containers, changing configuration, accessing secrets, or changing any legacy
repository. It prohibits broad process-name or port cleanup and any inferred retry or discovery.

## Known unknowns and closure conditions

The decision can become owner-reviewable only after all of the following are supplied and
cross-checked:

- target-owner acceptance of the candidate artifact manifest, vendor-binary disposition, and a
  durable restricted retention location;
- isolated environment identity, host and containment owners, and resource limits;
- exact public protocol subset plus restricted mapping/payload review;
- measurable readiness, shutdown, timeout, and failure contracts;
- secret-free attestation or an explicit blocked result; and
- closure and owner approval of the drafted target-specific provider contract, followed by separate
  implementation authorization.

Even after this record passes, any legacy lifecycle action requires a matching, unexpired,
single-use execution permit. The legacy source checkout remains immutable throughout selection,
implementation, and any later authorized execution.
