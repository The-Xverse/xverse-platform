# M0 architecture review

**Date**: 2026-09-20. **Review scope**: setup, Spec Kit artifacts, four inventory reports,
sanitized evidence snapshot and offline validation. **Disposition**: suitable for M0 human review;
no M0 BLOCKER found. This does not approve M1, freeze contracts, or prove runtime compatibility.

The authoring agent performed a separate read-only reviewer pass after report generation and initial
validation. This is not an independent human assessment or a review by a separate agent. No legacy
source or deliverable was repaired during that pass. This report records its findings afterward.

## Architecture gates

| Concern | Assessment |
|---|---|
| Domain neutrality / blueprint isolation | Pass for M0: domain terms describe legacy assets; no platform core implementation exists. |
| Production isolation / compatibility | Pass: only GET API inspection; no legacy execution, modifications or remote writes. Candidate wrappers are proposals. |
| Dependency direction | Pass: repository responsibilities are explicit; legacy graph is labeled separately from vNext design. |
| XDL / standards | Pass: no competing runtime configuration, schemas or metamodel introduced. Snapshot JSON is documentary evidence. |
| ADR discipline | Pass: ADR-0001–0004 record approved baseline decisions; future design is deferred. |
| Reproducibility | Partial for future runtime: source commits and manifest versions pinned; binaries, environment and live parity are not verified. |
| Lifecycle / failures / observability | Appropriate for M0: source limits and errors are recorded; no runtime guarantee is claimed. |
| Extensibility / plugin isolation / API stability | Not exercised: no plugins or APIs added. Rules preserve later design space. |
| Testability | Offline checks cover inventory structure, references, links and preservation; semantic review remains necessary. |
| Maturity / governance readiness | Clear separation of source evidence, documented intent, inference and unknowns. No maintainer identity, certification or license permission is invented. |

## Findings

**BLOCKER**: none for the agreed M0 delivery. Human approval of the inventory is still an explicit
entry gate to M1 under guidance section 46; successful M0 checks do not satisfy that gate.

| ID | Severity | Finding / impact | Disposition |
|---|---|---|---|
| R01 / G01 | MAJOR | AutoVerse README PID/Rust path differs from configured S-CORE launcher. A parity baseline cannot be inferred. | Disclosed in dependency map; reviewer must select supported variant and versions before runtime compatibility work. |
| R02 / G02 | MAJOR | Launcher uses fixed sleeps, broad cleanup, continued startup after exceptions, and process polling; container lifecycle is not fully established by command-process exit. | Disclosed; define isolated ownership, readiness and stop behavior before wrapping/executing. No legacy fix in M0. |
| R03 / G03 | MAJOR | ROS2 reverse callback creates a fixed scalar message despite generic mapping/decode facilities. | Catalog limits the claim; future adapter needs tests for the supported subset. |
| R04 / G04 | MAJOR | Cuttlefish documentation claims AutoVerse linkage absent from pinned launcher/manifest; Android versions and bundled APK provenance differ or remain unproven. | Treat as a separate candidate runtime; confirm image/ABI/APK provenance before inclusion. |
| R05 / G05 | MAJOR | HwSim board request dispatch exists, but inspected serving method does not register transport handlers. | Catalog avoids claiming network-ready register access; verify callable boundary before remote integration. |
| R06 | MINOR | Five README-only repositories and opaque hardware/archive assets cannot supply complete runtime contracts. | Explicit unknowns and artifact coverage; retain external status rather than invent implementations. |
| R07 | MINOR | VCU README module invocation differs from actual tree/AutoVerse entrypoint; PID topics differ from older examples. | Use pinned source contracts in later tests; do not propagate README commands as proven launch recipes. |
| R08 | ADVISORY | Private source links require access and source pins do not pin all runtime artifacts, external bindings or deployed environments. | Keep public summaries bounded; collect appropriately restricted contract/artifact evidence during later capabilities. |
| R09 | ADVISORY | Offline validator initially exercises invalid snapshots but quickstart also names guidance/constitution mismatch scenarios. | Add temporary-fixture negative checks in a subsequent implementation pass before final validation. |

The MAJOR findings constrain future implementation and must be dispositioned in inventory review;
they are documented discovery outcomes, not unresolved defects in an M0 runtime implementation.

## Source evidence for findings

- R01/R02: [documented baseline](https://github.com/The-Xverse/autoverse/blob/fc9af6d6bb4de702a65bf0272b3c77256a5d1697/README.md); [configured lifecycle](https://github.com/The-Xverse/autoverse/blob/fc9af6d6bb4de702a65bf0272b3c77256a5d1697/run_autoverse.py).
- R03: [active bridge callback](https://github.com/The-Xverse/zenoh2ros2_bridge/blob/ef83ee85b664d9defec1128a345803715ea3cba1/ros2-zenoh-bridge-python/src/bridge.py).
- R04: [Cuttlefish claims](https://github.com/The-Xverse/aaos_cuttlefish/blob/a794faf61c1f8173730a09428962d6dc8c42a59b/README.md); [workspace composition](https://github.com/The-Xverse/autoverse/blob/fc9af6d6bb4de702a65bf0272b3c77256a5d1697/autoverse.repos); [HAL build baseline](https://github.com/The-Xverse/aosp_zenoh_vhal_impl/blob/5287bdb51bf8e23b91fb7cae90bb94c366557c52/README.md).
- R05: [gateway source](https://github.com/The-Xverse/HwSim/blob/27bba949417483e618d2564401b27b1a39d5c439/hwsim/transport/zenoh_gateway.py).
- R06: [coverage snapshot](../legacy/inventory-snapshot.json) and [inventory](../legacy/REPOSITORY_INVENTORY.md).
- R07: [VCU documentation](https://github.com/The-Xverse/vcu-zenoh-python/blob/125566ef561fbd601defec22d5846068448722b9/README.md); [VCU entrypoint](https://github.com/The-Xverse/vcu-zenoh-python/blob/125566ef561fbd601defec22d5846068448722b9/src/main.py); [PID entrypoint](https://github.com/The-Xverse/simulink-vecu/blob/505ba3402713f41bc9c7bb2d2c12bf080d421957/pid_controller/main.py).
- R08/R09: [validation guide](../../specs/001-legacy-repository-inventory/quickstart.md) and [validator](../../scripts/validate_m0.py).

## Acceptance boundary

M0 can be marked ready for review after the final validation record and acceptance checklist pass.
Use [M0_REVIEW_CHECKLIST.md](M0_REVIEW_CHECKLIST.md) to record actual reviewer decisions. Remaining
baseline, lifecycle, artifact and private-contract gaps may be accepted as exclusions or require more
discovery; they are not silently resolved by creating M1 specifications.

## Subsequent implementation disposition

R09: resolved after the review pass. The validator now exercises guidance-copy and constitution
mismatches in temporary copies; both checks pass. The original review observation above is retained.
All other findings remain documented constraints for human review and future capability planning.
See the [final validation record](../../specs/001-legacy-repository-inventory/validation.md).

## Later human review decision — 2026-09-20

The user confirmed the review package after the authoring/reviewer passes above. See the
[decision record](M0_REVIEW_CHECKLIST.md). The M0 review gate is now satisfied for M1 specification/design.
Historical references to pending approval above describe the state at the time of the review.
R01–R05 remain accepted follow-up constraints, not repaired or disproved findings. The
[new references](../architecture/REFERENCE_REGISTER.md) add context without overriding source evidence.
