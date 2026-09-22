# SD-0001 selection-closure packet

**Date**: 2026-09-21

**Status**: Ready for evidence intake; selected-component decision remains blocked

**Purpose**: Collect the minimum owner-reviewed evidence needed to close the seven blockers in the
SD-0001 plan. This packet is a review checklist, not an XDL document, runtime configuration, execution
permit, or authorization to implement or run the gateway.

## Locked candidate baseline

Run the side-effect-free validator from `xverse-platform`:

```sh
.venv/bin/python scripts/validate_sd0001.py
```

The validator checks [`candidate.lock.json`](../../../xdl/candidates/sd0001/candidate.lock.json), the
four candidate XDL files, runtime Profile schema v0.2, exact catalog/provider/artifact/resource
identities, plan digest, and blocker set. A successful result must still report `plannable:false`,
`executionEligible:false`, and `legacyExecution:false`.

## Evidence closure matrix

| Plan blocker | Required decision evidence | Acceptable public record | Restricted evidence, if needed | Current status |
|---|---|---|---|---|
| `XVERSE-PLAN-OWNER-UNASSIGNED` | Accountable host owner and rollback/containment owner accept the exact candidate, environment, stop authority, and evidence duties. | Role or team labels, approval date, decision scope, exclusions, evidence reference. | Personal/contact data or internal approval record. | Unavailable; required input. |
| `XVERSE-PLAN-ENVIRONMENT-UNPINNED` | Immutable environment identity covering OS/image, architecture, system libraries, filesystem boundary, network allow/deny boundary, execution root, non-secret environment allowlist, and disposition of the compiled private Zenoh endpoint found by static audit. | Non-sensitive digest/version identities and limitations. | Private topology, addresses, registry, host, and deployment values. | Unavailable; required input. |
| `XVERSE-PLAN-RESOURCE-LIMITS-UNAPPROVED` | CPU, memory, process, file-descriptor, storage/log, and queue/backpressure ceilings plus limit-exceeded behavior. | Approved numeric ceilings or a versioned policy reference. | Infrastructure-specific capacity detail. | Unavailable; required input. |
| `XVERSE-PLAN-READINESS-UNVERIFIED` | External probe proving both protocol boundaries and one minimal approved bidirectional message path; exact timeout, failure codes, stop escalation, detached-work disposition, and expected terminal state. | Probe semantics, bounded timing, pass/fail outcome categories, evidence reference. | Exact peer addresses, identifiers, mappings, payloads, or captures. | No readiness API or bundled probe; required input. |
| `XVERSE-PLAN-INTERFACE-CONTRACT-UNVERIFIED` | Owner acceptance of the static projection plus supported Zenoh and SOME/IP/vsomeip versions, peer ABI/byte order, discovery/wire subset, six direction mappings, payload types/units/ranges, timing/delivery assumptions, and incompatibility behavior. | Safe interface/version/limit projection. | Exact service/event/topic identifiers, payload layouts, and mappings. | Static projection drafted; restricted review and runtime verification absent. |
| `XVERSE-PLAN-ARTIFACT-RETENTION-UNAPPROVED` | Controlled retention location, access class, retention period, integrity check, and deletion owner for the candidate bundle and later restricted evidence; raw payload-bearing logs require an approved discard or restricted-retention policy. | Location class, retention policy ID, period, owner role, digest-verification rule. | Actual internal storage location, any retained raw logs, and access-control details. | Temporary local artifact only; required durable decision. |
| `XVERSE-PLAN-VENDOR-BINARY-DISPOSITION` | Target owner either accepts the exact vendor libraries, digest-only Zenoh identity, and withheld historical paths inside the pinned isolation boundary or approves reproducible rebuild/sanitization; system runtime libraries are pinned with the environment. | Chosen disposition, artifact/environment digests, limitations, approval reference. | Vendor provenance and historical path values. | Configurable-rebuild strategy selected 2026-09-21 and ADR-0017 recorded; restricted patch, new artifact, containment, dependency provenance, and target-owner acceptance remain required. |

## Isolation attestation fields

The future attestation must bind all of these fields to one immutable environment revision:

- attestation ID and review date;
- catalog identity and plan digest;
- execution root and read-only legacy-checkout rule;
- filesystem boundary and writable paths;
- network allowlist and explicit denied reachability;
- exact executable allowlist and non-secret environment-name allowlist;
- CPU, memory, process, file-descriptor, storage/log, and queue limits;
- external peer ownership and prerequisite status;
- host owner and rollback/containment owner roles;
- stop/escalation authority and maximum containment time;
- restricted evidence destination and retention policy reference.

The current `IsolationAttestation` model is a prototype trust input and does not create an OS sandbox.
The evidence must identify the actual containment mechanism separately.

## Interface and readiness acceptance record

The owner-reviewed record must answer each item without copying restricted values into this repository:

1. Which exact Zenoh API/protocol and SOME/IP/vsomeip versions are supported?
2. Which discovery, transport, serialization, session, and delivery features are required or excluded?
3. What are the four directional message contracts and conversion limits?
4. Which one minimal bidirectional path is safe to exercise in the isolated environment?
5. Which independently observed signals establish peer registration and message-path readiness?
6. Which observations mean `not-ready`, `unavailable`, timeout, incompatible, or failed?
7. What stop signal and bounded escalation are permitted for the exact owned process group?
8. What terminal evidence proves that no owned process or disposable resource remains?

Process survival, log text, fixed delay, repository documentation, and fixture success are insufficient.

The [static interface audit](SD-0001-static-interface-audit.md) and companion public projection define
the current evidence floor. Any restricted mapping/peer review must reconcile native float ABI/byte
order, raw reverse payloads, the compiled endpoint, unreliable events, special reset timing,
payload-bearing logs, and absence of a graceful-stop/readiness API.

The companion controlled-rebuild envelope can enforce exact Git/tool/source/patch identities and
repeatable outputs. Its directory stages are not OS containment, and reproducibility cannot replace
the peer, readiness, retention, resource, or owner evidence requested here.

## Reference reconciliation

[REF-001 and REF-002](../../../docs/architecture/REFERENCE_REGISTER.md) provide useful architecture
context but cannot close these blockers:

- REF-001 describes Zenoh/SOME/IP integration and reports prior integration activity, but the
  underlying mapping/test artifacts were not supplied or independently verified.
- REF-001 describes a broader bring-up sequence with the S-CORE container before the gateway. The
  revision-pinned current AutoVerse launcher evidence starts the gateway before S-CORE. No ordering
  contract is selected until an owner identifies the intended baseline and readiness dependencies.
- REF-001's cloud sizing is a proposal for a broader CARLA/Android environment, not measured limits
  for this isolated gateway process.
- REF-002 requires monitoring, readiness, quotas, isolation, and retention as target capabilities. It
  does not identify their implementation, immutable environment, approved values, or accountable owner.

These sources remain documented or target evidence. They cannot be promoted to verified execution
evidence or owner authorization.

## Closure procedure

1. Record restricted evidence in the approved controlled location and place only its public-safe
   reference and decision projection in SD-0001.
2. Obtain host and containment owner approval for the exact artifact/environment/interface/lifecycle
   set, not for a mutable tag or repository name.
3. Replace only blocker-backed candidate fields with approved values, increment affected XDL resource
   versions/provenance revisions, and regenerate the candidate lock and deterministic plan digest.
4. Run platform and compatibility validation, public-safety review, and a separate architecture pass.
5. Close SD-R03–SD-R06 and SD-R08 only where evidence directly satisfies each finding.
6. Mark T019/ACC015 and compatibility T012–T014 complete only after the owner-reviewed decision passes.
7. Seek separate authorization for target-provider implementation. A later execution still requires
   a matching unexpired single-use permit.

## Intake result

The packet is structurally complete. No owner, environment, interface, readiness, retention, resource,
or vendor-binary decision is inferred from the supplied references. All seven plan blockers remain.
