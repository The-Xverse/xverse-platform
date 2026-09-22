# Migration classification — M0 recommendations

These classifications are **inferences for review**, not repository migration instructions.
Production remains unchanged. The pinned evidence and all 15 fields are in the
[repository inventory](REPOSITORY_INVENTORY.md). No replacement or repository move is authorized.

| Repository | Classification | Candidate external boundary | Long-term treatment |
|---|---|---|---|
| [.github](REPOSITORY_INVENTORY.md#repo-dotgithub) | I — Support/tooling (governance documentation). | I — Reference documentation externally; no runtime adapter. | I — Remain external. |
| [aaos-vhal-bridge](REPOSITORY_INVENTORY.md#repo-aaos-vhal-bridge) | I — Reusable adapter. | I — Wrap the existing Python process and its UDP/VHAL interfaces externally. | I — Wrap; preserve existing interfaces. |
| [aaos_cuttlefish](REPOSITORY_INVENTORY.md#repo-aaos_cuttlefish) | I — Simulator integration (virtual Android runtime). | I — Wrap existing prepared container/device lifecycle after confirming image/APK provenance. | I — Wrap with explicit version/environment contract in a future capability. |
| [adas_s-core](REPOSITORY_INVENTORY.md#repo-adas_s-core) | I — Demonstrator/application with device/vECU implementation. | I — Wrap prepared container workload and service interfaces; keep controller logic in automotive domain. | I — Wrap; retain research/domain behavior externally. |
| [aosp_zenoh_vhal_impl](REPOSITORY_INVENTORY.md#repo-aosp_zenoh_vhal_impl) | I — Reusable adapter (platform-specific HAL integration). | I — Consume an existing Android image or public HAL interface; do not alter legacy Android build repositories during vNext work. | I — Remain specialized; wrap the resulting image/interface. |
| [aosp_zenohc_cross_compiled_libs](REPOSITORY_INVENTORY.md#repo-aosp_zenohc_cross_compiled_libs) | I — Support/tooling (prebuilt dependency packaging). | I — Versioned external artifact dependency with future ABI/digest checks. | I — Remain external. |
| [autoverse](REPOSITORY_INVENTORY.md#repo-autoverse) | I — Demonstrator/application (integration workspace). | I — Use observed component boundaries to define a future blueprint; do not blindly execute the supervisor as a safe isolated adapter. | I — Remain external; wrap the use case through a future compatibility blueprint. |
| [c-shenron-rfe](REPOSITORY_INVENTORY.md#repo-c-shenron-rfe) | I — Research PoC. | I — Wrap scenario/tool invocation and output artifacts within a specialized blueprint. | I — Remain specialized; wrap reproducible experiments. |
| [carla-simulator-bridge](REPOSITORY_INVENTORY.md#repo-carla-simulator-bridge) | I — Simulator integration. | I — External client/process adapter using the existing CARLA and Zenoh interfaces. | I — Wrap; keep CARLA-specific logic outside core. |
| [digital-cluster-vecu](REPOSITORY_INVENTORY.md#repo-digital-cluster-vecu) | I — Demonstrator/application. | I — Treat APK plus messaging contract as an external domain application. | I — Remain specialized; wrap installation/lifecycle in a future blueprint. |
| [feature-radar-sensor-streaming](REPOSITORY_INVENTORY.md#repo-feature-radar-sensor-streaming) | I — Research PoC candidate/documentation, provisional. | I — Reference-only until a radar implementation and contract are identified. | I — Remain external pending implementation evidence. |
| [FreeRTOS-vECU](REPOSITORY_INVENTORY.md#repo-freertos-vecu) | I — Device/vECU implementation. | I — External physical-device/firmware boundary via CAN and diagnostics. | I — Remain specialized; wrap physical integration. |
| [HwSim](REPOSITORY_INVENTORY.md#repo-hwsim) | I — Simulator integration / reusable hardware tooling. | I — Prefer existing CLI/evidence artifact boundary first; verify actual transport handlers before promising remote device control. | I — Wrap selected capabilities; leave internal model language external. |
| [real_simulink](REPOSITORY_INVENTORY.md#repo-real_simulink) | I — Simulator integration candidate, provisional. | I — No executable boundary identified. | I — Remain external pending evidence. |
| [robot-framework](REPOSITORY_INVENTORY.md#repo-robot-framework) | I — Support/tooling candidate, provisional. | I — No runtime boundary until implementation evidence exists. | I — Remain external pending clarification. |
| [simulink-vecu](REPOSITORY_INVENTORY.md#repo-simulink-vecu) | I — Device/vECU implementation. | I — Wrap the existing controller process, inputs, outputs, and artifacts; do not infer an FMU from the repository name. | I — Wrap; retain specialized controller behavior. |
| [synchronous-simulation-mode](REPOSITORY_INVENTORY.md#repo-synchronous-simulation-mode) | I — Research PoC/architectural-target candidate. | I — No runtime boundary until implementation is identified. | I — Remain external; use as a requirement input only. |
| [vcu-zenoh-python](REPOSITORY_INVENTORY.md#repo-vcu-zenoh-python) | I — Device/vECU implementation. | I — Wrap process and version-specific message contract; preserve domain control logic externally. | I — Wrap; keep automotive logic specialized. |
| [vECU-Grafic-User-Interface](REPOSITORY_INVENTORY.md#repo-vecu-grafic-user-interface) | I — Demonstrator/application. | I — Physical-display adapter using existing serial contract and versioned assets. | I — Remain specialized. |
| [vECU_Board](REPOSITORY_INVENTORY.md#repo-vecu_board) | I — Support/tooling (hardware artifact). | I — Reference versioned hardware artifacts; future device descriptor must bind actual board/firmware revision. | I — Remain specialized. |
| [vECU_Component-Symbols](REPOSITORY_INVENTORY.md#repo-vecu_component-symbols) | I — Support/tooling (hardware library). | I — External versioned design dependency, not runtime plugin. | I — Remain specialized. |
| [vECU_FootPrints](REPOSITORY_INVENTORY.md#repo-vecu_footprints) | I — Support/tooling (hardware library). | I — External versioned design dependency, not runtime plugin. | I — Remain specialized. |
| [x-verse](REPOSITORY_INVENTORY.md#repo-x-verse) | I — Platform infrastructure candidate, provisional; not the new xverse-platform implementation. | I — Reference context only; no executable boundary. | I — Remain external; do not rename or migrate. |
| [zenoh-core](REPOSITORY_INVENTORY.md#repo-zenoh-core) | I — Platform infrastructure with domain-specific device/control implementation. | I — Separate external Zenoh utilities from the automotive vehicle process; do not import the latter into vNext core. | I — Wrap selected artifacts; keep vehicle logic specialized. |
| [zenoh2can_bridge](REPOSITORY_INVENTORY.md#repo-zenoh2can_bridge) | I — Reusable adapter. | I — Wrap existing process and map its declared bus capabilities externally. | I — Wrap; validate virtual and physical backends separately. |
| [zenoh2ros2_bridge](REPOSITORY_INVENTORY.md#repo-zenoh2ros2_bridge) | I — Reusable adapter. | I — Wrap only the verified message subset; require contract tests before claiming generic bidirectionality. | I — Wrap with explicit capability limits. |
| [zenoh2someip_bridge](REPOSITORY_INVENTORY.md#repo-zenoh2someip_bridge) | I — Reusable adapter. | I — Wrap existing gateway executable and configuration; preserve payload and service identifiers. | I — Wrap; do not reimplement protocol logic in core. |
| [Zephyr-BCM](REPOSITORY_INVENTORY.md#repo-zephyr-bcm) | I — Device/vECU implementation candidate, provisional. | I — Candidate emulator/artifact boundary only after provenance and interface review. | I — Remain external pending artifact verification. |
| [zephyr-vecu](REPOSITORY_INVENTORY.md#repo-zephyr-vecu) | I — Device/vECU implementation. | I — Wrap firmware/emulator lifecycle and CAN interface; physical and emulated realizations remain distinct. | I — Wrap the selected application; retain board logic externally. |

## Priorities for later capabilities

1. Review AutoVerse's source-defined S-CORE path and documented PID path and select the actual
compatibility baseline. Preserve component revisions and behavior, including legacy limitations.
2. Describe process/container boundaries in future XDL Component resources only after M1/M2.
The existing SOME/IP gateway is a bounded wrapper candidate, subject to lifecycle and payload tests.
3. Keep Android images/apps, firmware, hardware assets and research experiments specialized. Any
future adapter must declare realization, prerequisites, fidelity and version compatibility.
4. Keep document-only and opaque-artifact repositories external until their owners supply evidence.
Do not convert uncertainty into a migration or deprecation recommendation.

## Compatibility impact

This delivery changes only vNext governance and discovery documentation. It alters no production
repository, public API, CI configuration, topic, image, package, service identity or deployment.
No automatic startup, compatibility guarantee, repository consolidation or retirement is introduced.

## Human review required before M1

Confirm repository classifications, owner-supported versions, actual runtime boundaries and
interfaces, startup dependencies and unknowns. Reviewers may accept exclusions or require additional
evidence; neither M0 validation nor these recommendations substitute for their decision.
