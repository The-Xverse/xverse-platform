# Legacy repository inventory — M0

**Snapshot**: 2026-09-20. **Status**: M0 review confirmed on 2026-09-20, with known limitations carried forward.
**Coverage**: 32 accessible repositories: 29 legacy and 3 vNext. No archived repositories or forks
were reported in this snapshot. All 29 legacy revisions and recursive trees were accessible; none
of those trees was truncated. Source selection is targeted, not an exhaustive code or binary audit.
No production workload, build, firmware, emulator, or legacy test was executed.

## How to read this inventory

- **O**: observed in pinned source, manifest, or tree. File presence does not prove a successful build.
- **D**: documented by the source repository; not independently demonstrated here.
- **I**: architectural inference or proposed classification/treatment, pending human review.
- **U**: unknown or not established by the inspected sources. This is not evidence that a capability
  cannot exist elsewhere or on another branch.

Every record's evidence links apply to its O/D statements. Additional cross-repository observations
use the shared AutoVerse manifest/launcher evidence below. I statements are recommendations, not
implemented changes. Maturity ratings are conservative inventory assessments, not owner attestations.
No repository is rated runtime-demonstrated by M0. Hardware/library assets have not been qualified.

Only public-safe summaries are included. Private sources require the reader's existing GitHub access.
Raw code, lab addresses, credential values, full message IDs/layouts, local paths, and proprietary
archives are omitted. Missing and withheld detail must be resolved in an appropriately scoped later
contract review. There is no claim that these public summaries freeze complete executable contracts.

Machine-readable coverage, revision pins, evidence hashes and preservation hashes are in
[inventory-snapshot.json](inventory-snapshot.json). Related reports:
[dependencies](DEPENDENCY_MAP.md), [interfaces](INTERFACE_CATALOG.md),
[classification](MIGRATION_CLASSIFICATION.md).

## Shared integration evidence

[Pinned workspace manifest](https://github.com/The-Xverse/autoverse/blob/fc9af6d6bb4de702a65bf0272b3c77256a5d1697/autoverse.repos); [pinned launcher](https://github.com/The-Xverse/autoverse/blob/fc9af6d6bb4de702a65bf0272b3c77256a5d1697/run_autoverse.py); [documented older startup path](https://github.com/The-Xverse/autoverse/blob/fc9af6d6bb4de702a65bf0272b3c77256a5d1697/README.md).
The ten declared component tags resolved to the same commits as their inspected default branches
at capture time. This is source provenance, not proof of deployed versions or successful parity.

## Coverage index

| Repository | Inspection | Maturity |
|---|---|---|
| [.github](#repo-dotgithub) | source-and-documentation | implemented documentation; runtime not applicable |
| [aaos-vhal-bridge](#repo-aaos-vhal-bridge) | source-and-documentation | partial / under stabilization (provisional inventory assessment); runtime unverified |
| [aaos_cuttlefish](#repo-aaos_cuttlefish) | source-and-documentation | partial / under stabilization (provisional inventory assessment); runtime unverified |
| [adas_s-core](#repo-adas_s-core) | source-and-documentation | partial / under stabilization (provisional inventory assessment); runtime unverified |
| [aosp_zenoh_vhal_impl](#repo-aosp_zenoh_vhal_impl) | source-and-documentation | partial / under stabilization (provisional inventory assessment); runtime unverified |
| [aosp_zenohc_cross_compiled_libs](#repo-aosp_zenohc_cross_compiled_libs) | source-and-documentation | partial / under stabilization (provisional inventory assessment); runtime unverified |
| [autoverse](#repo-autoverse) | source-and-documentation | partial / under stabilization (provisional inventory assessment); runtime unverified |
| [c-shenron-rfe](#repo-c-shenron-rfe) | source-and-documentation | exploratory / PoC; fidelity remains provisional |
| [carla-simulator-bridge](#repo-carla-simulator-bridge) | source-and-documentation | partial / under stabilization (provisional inventory assessment); runtime unverified |
| [digital-cluster-vecu](#repo-digital-cluster-vecu) | source-and-documentation | partial / under stabilization (provisional inventory assessment); runtime unverified |
| [feature-radar-sensor-streaming](#repo-feature-radar-sensor-streaming) | documentation-only | architectural target; documentation-only evidence |
| [FreeRTOS-vECU](#repo-freertos-vecu) | source-and-documentation | partial / under stabilization (provisional inventory assessment); runtime unverified |
| [HwSim](#repo-hwsim) | source-and-documentation | partial / under stabilization (provisional inventory assessment); runtime unverified |
| [real_simulink](#repo-real_simulink) | documentation-only | architectural target; documentation-only evidence |
| [robot-framework](#repo-robot-framework) | documentation-only | architectural target; documentation-only evidence |
| [simulink-vecu](#repo-simulink-vecu) | source-and-documentation | partial / under stabilization (provisional inventory assessment); runtime unverified |
| [synchronous-simulation-mode](#repo-synchronous-simulation-mode) | documentation-only | architectural target; documentation-only evidence |
| [vcu-zenoh-python](#repo-vcu-zenoh-python) | source-and-documentation | partial / under stabilization (provisional inventory assessment); runtime unverified |
| [vECU-Grafic-User-Interface](#repo-vecu-grafic-user-interface) | artifact-metadata | partial / under stabilization (provisional inventory assessment); runtime unverified |
| [vECU_Board](#repo-vecu_board) | artifact-metadata | partial / under stabilization (provisional inventory assessment); runtime unverified |
| [vECU_Component-Symbols](#repo-vecu_component-symbols) | artifact-metadata | partial / under stabilization (provisional inventory assessment); runtime unverified |
| [vECU_FootPrints](#repo-vecu_footprints) | artifact-metadata | partial / under stabilization (provisional inventory assessment); runtime unverified |
| [x-verse](#repo-x-verse) | documentation-only | architectural target; documentation-only evidence |
| [zenoh-core](#repo-zenoh-core) | source-and-documentation | partial / under stabilization (provisional inventory assessment); runtime unverified |
| [zenoh2can_bridge](#repo-zenoh2can_bridge) | source-and-documentation | partial / under stabilization (provisional inventory assessment); runtime unverified |
| [zenoh2ros2_bridge](#repo-zenoh2ros2_bridge) | source-and-documentation | partial / under stabilization (provisional inventory assessment); runtime unverified |
| [zenoh2someip_bridge](#repo-zenoh2someip_bridge) | source-and-documentation | partial / under stabilization (provisional inventory assessment); runtime unverified |
| [Zephyr-BCM](#repo-zephyr-bcm) | artifact-metadata | partial / under stabilization (provisional inventory assessment); runtime unverified |
| [zephyr-vecu](#repo-zephyr-vecu) | source-and-documentation | partial / under stabilization (provisional inventory assessment); runtime unverified |

## New repositories, excluded from legacy classification

- **xverse-blueprints**: remote snapshot contains LICENSE only; commit `bf03788cc97365b36a243a31c82887c8ae0c8752`. M0 setup is local and unpublished.
- **xverse-compat**: remote has no commit; local pre-existing LICENSE preserved. M0 setup is local and unpublished.
- **xverse-platform**: remote snapshot contains LICENSE only; commit `bc8b6ff2deaa4c1ced1619c7fb43354b23ba60fc`. M0 setup is local and unpublished.

<a id="repo-dotgithub"></a>

## .github

**Revision**: `01cc3f9c134ae9fc2cba75057f400915c7ebb135` on `main`. **Maturity**: implemented documentation; runtime not applicable.

**Evidence**: [.github tree](https://github.com/The-Xverse/.github/tree/01cc3f9c134ae9fc2cba75057f400915c7ebb135); [profile/README.md](https://github.com/The-Xverse/.github/blob/01cc3f9c134ae9fc2cba75057f400915c7ebb135/profile/README.md).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/.github |
| 2. Primary purpose | D — Organization profile and foundational principles for modular digital twins. |
| 3. Language/build system | O — Markdown; no executable build files in the snapshot. |
| 4. Runtime artifact produced | O — Documentation only. |
| 5. Runtime dependencies | U — No runtime dependency is declared in the two inspected documents. |
| 6. Communication interfaces | O — GitHub organization profile/documentation surface. |
| 7. Protocols used | D — ROS2, DDS, OPC UA, and Zenoh are mentioned as strategic examples, not implementations. |
| 8. Input/output contracts | O — Markdown input rendered as organization documentation; no runtime I/O contract. |
| 9. Startup dependencies | O — No executable startup definition in the tree. |
| 10. Configuration mechanism | O — Repository Markdown/profile files. |
| 11. Current integration | D — Organization-wide guidance; no component dependency declared. |
| 12. Classification | I — Support/tooling (governance documentation). |
| 13. Candidate compatibility boundary | I — Reference documentation externally; no runtime adapter. |
| 14. Risks if changed | I — Changes could alter public positioning and governance expectations. |
| 15. Recommended long-term treatment | I — Remain external. |

<a id="repo-aaos-vhal-bridge"></a>

## aaos-vhal-bridge

**Revision**: `336f12301dbb0e778180566839c4892407cd875e` on `main`. **Maturity**: partial / under stabilization (provisional inventory assessment); runtime unverified.

**Evidence**: [aaos-vhal-bridge tree](https://github.com/The-Xverse/aaos-vhal-bridge/tree/336f12301dbb0e778180566839c4892407cd875e); [README.md](https://github.com/The-Xverse/aaos-vhal-bridge/blob/336f12301dbb0e778180566839c4892407cd875e/README.md); [main.py](https://github.com/The-Xverse/aaos-vhal-bridge/blob/336f12301dbb0e778180566839c4892407cd875e/main.py).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/aaos-vhal-bridge |
| 2. Primary purpose | D — Gateway from simulator-style UDP signals to an Android Automotive emulator VHAL. |
| 3. Language/build system | O/D — Python; README requires Python 3, adb, and an AAOS API 34 emulator. |
| 4. Runtime artifact produced | O — Python executable source; packaged/released artifact not verified. |
| 5. Runtime dependencies | D — Booted AAOS emulator, adb, and exposed VHAL socket. |
| 6. Communication interfaces | O/D — UDP listener with signal dispatcher; VHAL socket and adb/dumpsys publishers. |
| 7. Protocols used | O/D — UDP, VHAL socket/protobuf, adb control. |
| 8. Input/output contracts | D — Named text signals and values become speed, RPM, and HVAC property updates. O — speed uses the dumpsys publisher in the inspected entrypoint. |
| 9. Startup dependencies | D — Boot emulator and expose its VHAL endpoint before starting the gateway. |
| 10. Configuration mechanism | O/D — Handler registration in the entrypoint and publisher/listener settings; deployment values omitted. |
| 11. Current integration | U — Current AutoVerse manifest does not list this repository; the AutoVerse README still describes an older VHAL workspace entry. |
| 12. Classification | I — Reusable adapter. |
| 13. Candidate compatibility boundary | I — Wrap the existing Python process and its UDP/VHAL interfaces externally. |
| 14. Risks if changed | I — Signal conversion, emulator API compatibility, and publisher changes can affect displayed vehicle state. |
| 15. Recommended long-term treatment | I — Wrap; preserve existing interfaces. |

<a id="repo-aaos_cuttlefish"></a>

## aaos_cuttlefish

**Revision**: `a794faf61c1f8173730a09428962d6dc8c42a59b` on `main`. **Maturity**: partial / under stabilization (provisional inventory assessment); runtime unverified.

**Evidence**: [aaos_cuttlefish tree](https://github.com/The-Xverse/aaos_cuttlefish/tree/a794faf61c1f8173730a09428962d6dc8c42a59b); [README.md](https://github.com/The-Xverse/aaos_cuttlefish/blob/a794faf61c1f8173730a09428962d6dc8c42a59b/README.md).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/aaos_cuttlefish |
| 2. Primary purpose | O/D — Container-based Cuttlefish/AOSP environment and bundled application setup/control. |
| 3. Language/build system | O/D — Shell lifecycle script, Android/CVD downloads and Docker container workflow. |
| 4. Runtime artifact produced | O — Control script and packaged application archive; downloaded images not inspected. |
| 5. Runtime dependencies | D — Docker, compatible host virtualization, Android/CVD artifacts and adb. |
| 6. Communication interfaces | O/D — Control-script lifecycle, adb application installation and browser display access. |
| 7. Protocols used | D — adb and Cuttlefish browser/virtual-device access; application protocol not established here. |
| 8. Input/output contracts | D — Setup downloads/prepares images and APK; start/stop controls virtual device and container. |
| 9. Startup dependencies | D — Setup must precede start. O — Current pinned AutoVerse launcher has no Cuttlefish step despite this README claiming integration. |
| 10. Configuration mechanism | O/D — Script image/build selections and local directories; environment values omitted. |
| 11. Current integration | D/U — Claimed AutoVerse lifecycle linkage is not corroborated by pinned launcher or manifest. |
| 12. Classification | I — Simulator integration (virtual Android runtime). |
| 13. Candidate compatibility boundary | I — Wrap existing prepared container/device lifecycle after confirming image/APK provenance. |
| 14. Risks if changed | O/D/I — Setup/clean can remove local artifacts; floating image tag and Android-generation differences complicate reproducibility. |
| 15. Recommended long-term treatment | I — Wrap with explicit version/environment contract in a future capability. |

<a id="repo-adas_s-core"></a>

## adas_s-core

**Revision**: `9ee0b31afed491c68952a2147aa3915dd4997ad7` on `main`. **Maturity**: partial / under stabilization (provisional inventory assessment); runtime unverified.

**Evidence**: [adas_s-core tree](https://github.com/The-Xverse/adas_s-core/tree/9ee0b31afed491c68952a2147aa3915dd4997ad7); [README.md](https://github.com/The-Xverse/adas_s-core/blob/9ee0b31afed491c68952a2147aa3915dd4997ad7/README.md); [inc_someip_gateway/examples/cruise_control/README.md](https://github.com/The-Xverse/adas_s-core/blob/9ee0b31afed491c68952a2147aa3915dd4997ad7/inc_someip_gateway/examples/cruise_control/README.md).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/adas_s-core |
| 2. Primary purpose | O/D — S-CORE-based cruise-control demonstration with a SOME/IP gateway. |
| 3. Language/build system | O/D — C++/Rust gateway tree, Bazel-based example build, shell and Docker Compose tooling. |
| 4. Runtime artifact produced | O/D — Executables and container build/deployment definitions. |
| 5. Runtime dependencies | D — S-CORE middleware, SOME/IP gateway, Docker/build tooling, and AutoVerse workspace. |
| 6. Communication interfaces | D — Cruise-control input/output services and Compose control wrapper. |
| 7. Protocols used | D — S-CORE communication and SOME/IP; external Zenoh gateway provides fabric interoperability. |
| 8. Input/output contracts | D — Clock, velocity, speed adjustment and engagement inputs; engagement, target speed and actuation outputs. |
| 9. Startup dependencies | D — Prepare/build artifacts before Compose lifecycle; O — AutoVerse uses Compose start, requiring pre-existing containers. |
| 10. Configuration mechanism | O/D — Middleware/service JSON, Compose files, and environment-based build selection. |
| 11. Current integration | O — AutoVerse manifest and supervisor integrate it with the separate Zenoh/SOME-IP gateway. |
| 12. Classification | I — Demonstrator/application with device/vECU implementation. |
| 13. Candidate compatibility boundary | I — Wrap prepared container workload and service interfaces; keep controller logic in automotive domain. |
| 14. Risks if changed | I — Middleware/service bindings, container state, control periods and payload semantics affect compatibility. |
| 15. Recommended long-term treatment | I — Wrap; retain research/domain behavior externally. |

<a id="repo-aosp_zenoh_vhal_impl"></a>

## aosp_zenoh_vhal_impl

**Revision**: `5287bdb51bf8e23b91fb7cae90bb94c366557c52` on `main`. **Maturity**: partial / under stabilization (provisional inventory assessment); runtime unverified.

**Evidence**: [aosp_zenoh_vhal_impl tree](https://github.com/The-Xverse/aosp_zenoh_vhal_impl/tree/5287bdb51bf8e23b91fb7cae90bb94c366557c52); [README.md](https://github.com/The-Xverse/aosp_zenoh_vhal_impl/blob/5287bdb51bf8e23b91fb7cae90bb94c366557c52/README.md); [2.0/default/impl/vhal_v2_0/ZenohSessionController.cpp](https://github.com/The-Xverse/aosp_zenoh_vhal_impl/blob/5287bdb51bf8e23b91fb7cae90bb94c366557c52/2.0/default/impl/vhal_v2_0/ZenohSessionController.cpp).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/aosp_zenoh_vhal_impl |
| 2. Primary purpose | O/D — Android vehicle HAL implementation connected to Zenoh. |
| 3. Language/build system | O/D — C++ with Android Soong/product integration; README names an Android 14 base. |
| 4. Runtime artifact produced | O/D — Android vendor HAL/build inputs for inclusion in a system image. |
| 5. Runtime dependencies | D — AOSP checkout and companion prebuilt Zenoh libraries; platform build integration. |
| 6. Communication interfaces | O — Vehicle HAL property callbacks and Zenoh subscription/publication mappings. |
| 7. Protocols used | O/D — Android VHAL/HIDL-era integration, Zenoh, and protobuf support files. |
| 8. Input/output contracts | O — Mapped vehicle-property values and Zenoh messages are converted in both directions. |
| 9. Startup dependencies | D — Build/integrate into AOSP, boot the resulting device/emulator, configure communication. |
| 10. Configuration mechanism | O/D — Product/build files, Zenoh INI configuration and property mappings; endpoint values omitted. |
| 11. Current integration | D — Explicitly depends on aosp_zenohc_cross_compiled_libs. U — Compatibility with newer Cuttlefish images is unverified. |
| 12. Classification | I — Reusable adapter (platform-specific HAL integration). |
| 13. Candidate compatibility boundary | I — Consume an existing Android image or public HAL interface; do not alter legacy Android build repositories during vNext work. |
| 14. Risks if changed | I — ABI, Android release, property IDs, and policy changes affect boot and application integration. |
| 15. Recommended long-term treatment | I — Remain specialized; wrap the resulting image/interface. |

<a id="repo-aosp_zenohc_cross_compiled_libs"></a>

## aosp_zenohc_cross_compiled_libs

**Revision**: `7d5a1a6db82d7371e8a71bb5a8a7bbaf5a6431d7` on `main`. **Maturity**: partial / under stabilization (provisional inventory assessment); runtime unverified.

**Evidence**: [aosp_zenohc_cross_compiled_libs tree](https://github.com/The-Xverse/aosp_zenohc_cross_compiled_libs/tree/7d5a1a6db82d7371e8a71bb5a8a7bbaf5a6431d7); [Android.bp](https://github.com/The-Xverse/aosp_zenohc_cross_compiled_libs/blob/7d5a1a6db82d7371e8a71bb5a8a7bbaf5a6431d7/Android.bp).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/aosp_zenohc_cross_compiled_libs |
| 2. Primary purpose | O — Android prebuilt Zenoh libraries, headers, and example build integration. |
| 3. Language/build system | O — C/C++ headers and Soong Android.bp prebuilt-library definitions. |
| 4. Runtime artifact produced | O — Library files/pointers and example executable source; binary contents/ABI not validated. |
| 5. Runtime dependencies | O — Android target architecture/toolchain and Zenoh C/C++ API dependencies. |
| 6. Communication interfaces | O — Link-time libraries and exported headers; example publisher source. |
| 7. Protocols used | O — Zenoh at the consuming process boundary; not an independent service. |
| 8. Input/output contracts | O — Build/link inputs become consuming Android artifacts; ABI compatibility is unknown. |
| 9. Startup dependencies | I — Not independently started; consuming HAL/service owns runtime lifecycle. |
| 10. Configuration mechanism | O — Architecture-specific prebuilt selections in Android.bp. |
| 11. Current integration | D — Explicit prerequisite in aosp_zenoh_vhal_impl instructions. |
| 12. Classification | I — Support/tooling (prebuilt dependency packaging). |
| 13. Candidate compatibility boundary | I — Versioned external artifact dependency with future ABI/digest checks. |
| 14. Risks if changed | I — Replacing binaries or headers can break Android linking or runtime ABI. |
| 15. Recommended long-term treatment | I — Remain external. |

<a id="repo-autoverse"></a>

## autoverse

**Revision**: `fc9af6d6bb4de702a65bf0272b3c77256a5d1697` on `main`. **Maturity**: partial / under stabilization (provisional inventory assessment); runtime unverified.

**Evidence**: [autoverse tree](https://github.com/The-Xverse/autoverse/tree/fc9af6d6bb4de702a65bf0272b3c77256a5d1697); [README.md](https://github.com/The-Xverse/autoverse/blob/fc9af6d6bb4de702a65bf0272b3c77256a5d1697/README.md); [autoverse.repos](https://github.com/The-Xverse/autoverse/blob/fc9af6d6bb4de702a65bf0272b3c77256a5d1697/autoverse.repos); [run_autoverse.py](https://github.com/The-Xverse/autoverse/blob/fc9af6d6bb4de702a65bf0272b3c77256a5d1697/run_autoverse.py); [justfile](https://github.com/The-Xverse/autoverse/blob/fc9af6d6bb4de702a65bf0272b3c77256a5d1697/justfile).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/autoverse |
| 2. Primary purpose | O/D — Workspace composition and automotive demonstration bring-up. |
| 3. Language/build system | O/D — Python supervisor, Bash/Just recipes, vcstool manifest, and selected Docker Compose workloads. |
| 4. Runtime artifact produced | O — Orchestration scripts, configuration, and supporting container recipes. |
| 5. Runtime dependencies | O — Ten declared repository dependencies; launcher requires prepared CARLA, VCU, SOME/IP gateway, S-CORE containers, and client automation. |
| 6. Communication interfaces | O — Child-process lifecycle, Compose commands, logs, environment overrides, and imported recipes. |
| 7. Protocols used | O/D — Components use Zenoh, SOME/IP, CARLA, and optional CAN/ROS2; the supervisor itself manages processes. |
| 8. Input/output contracts | O — Startup configuration produces process launches, stdout/stderr logs, and shutdown actions; it is not a versioned runtime API. |
| 9. Startup dependencies | O — Current order: CARLA server → Python VCU → SOME/IP gateway → S-CORE Compose start → CARLA automation. Fixed delays are not readiness probes. |
| 10. Configuration mechanism | O — Versioned workspace manifest, in-source step list, environment overrides, and imported Just recipes. |
| 11. Current integration | O — Explicit workspace hub for ten components; see dependency map. D — README PID/Rust sequence differs from the active launcher. |
| 12. Classification | I — Demonstrator/application (integration workspace). |
| 13. Candidate compatibility boundary | I — Use observed component boundaries to define a future blueprint; do not blindly execute the supervisor as a safe isolated adapter. |
| 14. Risks if changed | O/I — Broad process cleanup and non-fail-fast startup warrant isolation before parity experiments; documentation and launcher differ. |
| 15. Recommended long-term treatment | I — Remain external; wrap the use case through a future compatibility blueprint. |

<a id="repo-c-shenron-rfe"></a>

## c-shenron-rfe

**Revision**: `d86b495613cd94f59c0ac315032aa7b30de173af` on `main`. **Maturity**: exploratory / PoC; fidelity remains provisional.

**Evidence**: [c-shenron-rfe tree](https://github.com/The-Xverse/c-shenron-rfe/tree/d86b495613cd94f59c0ac315032aa7b30de173af); [README.md](https://github.com/The-Xverse/c-shenron-rfe/blob/d86b495613cd94f59c0ac315032aa7b30de173af/README.md); [tools/rfe/README.md](https://github.com/The-Xverse/c-shenron-rfe/blob/d86b495613cd94f59c0ac315032aa7b30de173af/tools/rfe/README.md); [tools/rfe/run_synthetic.py](https://github.com/The-Xverse/c-shenron-rfe/blob/d86b495613cd94f59c0ac315032aa7b30de173af/tools/rfe/run_synthetic.py).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/c-shenron-rfe |
| 2. Primary purpose | O/D — CARLA radar simulation research with opt-in physical radio-frequency-front-end modeling and calibration tooling. |
| 3. Language/build system | O/D — Python numerical/research tooling and shell runners; CARLA 0.9.16 is the documented target. |
| 4. Runtime artifact produced | O/D — Simulation scripts, model profiles, arrays/manifests, calibration/validation tools; no hardware validation reproduced. |
| 5. Runtime dependencies | D — Numerical packages; CARLA for live scenes; optional MATLAB/external backend for selected paths. |
| 6. Communication interfaces | D/O — CLI/profile inputs and explicit signal-boundary arrays/manifests; offline synthetic tool is inspected. |
| 7. Protocols used | D — CARLA client integration and file-based backend exchange; no Zenoh integration established. |
| 8. Input/output contracts | D/O — Scene/profile/target inputs produce reference-plane arrays and provenance; fidelity requires held-out device evidence. |
| 9. Startup dependencies | D — Select compatible client/server or offline tool, validate profile and supply explicit backend prerequisites. |
| 10. Configuration mechanism | D/O — Versioned profiles, CLI/environment arguments and manifests; provisional values remain provisional. |
| 11. Current integration | U — No direct AutoVerse manifest dependency established; shared CARLA dependency is not repository coupling. |
| 12. Classification | I — Research PoC. |
| 13. Candidate compatibility boundary | I — Wrap scenario/tool invocation and output artifacts within a specialized blueprint. |
| 14. Risks if changed | D/I — Promoting provisional calibration/fidelity or changing versions invalidates research comparisons. |
| 15. Recommended long-term treatment | I — Remain specialized; wrap reproducible experiments. |

<a id="repo-carla-simulator-bridge"></a>

## carla-simulator-bridge

**Revision**: `2859acd10a5e83babac0adbc51d3e6e42539027f` on `main`. **Maturity**: partial / under stabilization (provisional inventory assessment); runtime unverified.

**Evidence**: [carla-simulator-bridge tree](https://github.com/The-Xverse/carla-simulator-bridge/tree/2859acd10a5e83babac0adbc51d3e6e42539027f); [README.md](https://github.com/The-Xverse/carla-simulator-bridge/blob/2859acd10a5e83babac0adbc51d3e6e42539027f/README.md); [examples/zenoh_vehicle.py](https://github.com/The-Xverse/carla-simulator-bridge/blob/2859acd10a5e83babac0adbc51d3e6e42539027f/examples/zenoh_vehicle.py); [examples/automate.py](https://github.com/The-Xverse/carla-simulator-bridge/blob/2859acd10a5e83babac0adbc51d3e6e42539027f/examples/automate.py); [examples/manual_control_steeringwheel_zenoh.py](https://github.com/The-Xverse/carla-simulator-bridge/blob/2859acd10a5e83babac0adbc51d3e6e42539027f/examples/manual_control_steeringwheel_zenoh.py).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/carla-simulator-bridge |
| 2. Primary purpose | D — CARLA client examples and environment recipes integrating simulation with Zenoh. |
| 3. Language/build system | O/D — Python, Just recipes, CARLA Python API, pygame/NumPy/Zenoh, and Linux input support. |
| 4. Runtime artifact produced | O — Python clients and startup automation; no image build verified. |
| 5. Runtime dependencies | O/D — CARLA server, Zenoh, graphical/input environment for interactive clients. |
| 6. Communication interfaces | O — CARLA client API, Zenoh publishers/subscribers, and wheel-input-driven client restart helper. |
| 7. Protocols used | O — CARLA RPC, Zenoh, Linux input events. |
| 8. Input/output contracts | O — Publishes vehicle/control state and consumes actuation/state signals; older helper and steering-wheel client expose different signal sets. |
| 9. Startup dependencies | O — Server availability and client assets are prerequisites; automation restarts the steering client initially and on a configured button. |
| 10. Configuration mechanism | O/D — CLI arguments, Just recipes, wheel configuration and client signal definitions; local device values omitted. |
| 11. Current integration | O — AutoVerse manifest imports this component and the current launcher starts its automation helper. |
| 12. Classification | I — Simulator integration. |
| 13. Candidate compatibility boundary | I — External client/process adapter using the existing CARLA and Zenoh interfaces. |
| 14. Risks if changed | I — Topic, client version, actor selection, timing, and input-device changes can break demonstrations. |
| 15. Recommended long-term treatment | I — Wrap; keep CARLA-specific logic outside core. |

<a id="repo-digital-cluster-vecu"></a>

## digital-cluster-vecu

**Revision**: `3d35327e4acdd292e85b82901af65ef129b3f227` on `main`. **Maturity**: partial / under stabilization (provisional inventory assessment); runtime unverified.

**Evidence**: [digital-cluster-vecu tree](https://github.com/The-Xverse/digital-cluster-vecu/tree/3d35327e4acdd292e85b82901af65ef129b3f227); [README.md](https://github.com/The-Xverse/digital-cluster-vecu/blob/3d35327e4acdd292e85b82901af65ef129b3f227/README.md); [app/build.gradle.kts](https://github.com/The-Xverse/digital-cluster-vecu/blob/3d35327e4acdd292e85b82901af65ef129b3f227/app/build.gradle.kts); [app/src/main/java/com/example/digitalclusterapp/core/data/zenoh/ZenohClusterBinder.kt](https://github.com/The-Xverse/digital-cluster-vecu/blob/3d35327e4acdd292e85b82901af65ef129b3f227/app/src/main/java/com/example/digitalclusterapp/core/data/zenoh/ZenohClusterBinder.kt).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/digital-cluster-vecu |
| 2. Primary purpose | O/D — Android digital-cluster application. |
| 3. Language/build system | O — Kotlin/Gradle, Jetpack Compose, Java 17 target, Android SDK declarations. |
| 4. Runtime artifact produced | O — Android application source/build inputs; APK build not verified. |
| 5. Runtime dependencies | O — Android platform, Zenoh Kotlin, coroutine/UI dependencies; manifest also declares MQTT/uProtocol libraries. |
| 6. Communication interfaces | O — Inspected Zenoh binder consumes velocity and publishes cruise engagement/target speed. |
| 7. Protocols used | O — Zenoh in inspected binder. U — Library declarations alone do not prove MQTT/uProtocol runtime usage. |
| 8. Input/output contracts | O — Numeric velocity messages update cluster state; UI requests publish control values. |
| 9. Startup dependencies | I — Install/start APK on compatible Android runtime with reachable communication endpoint. |
| 10. Configuration mechanism | O — Gradle configuration and binder source constants; embedded environment details omitted. |
| 11. Current integration | U — No build-to-bundled-APK provenance established for AutoVerse/Cuttlefish packaging. |
| 12. Classification | I — Demonstrator/application. |
| 13. Candidate compatibility boundary | I — Treat APK plus messaging contract as an external domain application. |
| 14. Risks if changed | I — Android SDK, UI state, endpoint, and topic changes can affect demonstrations. |
| 15. Recommended long-term treatment | I — Remain specialized; wrap installation/lifecycle in a future blueprint. |

<a id="repo-feature-radar-sensor-streaming"></a>

## feature-radar-sensor-streaming

**Revision**: `45a60e87ca2b72d1820e4c8db1eb17fa9132f7c2` on `main`. **Maturity**: architectural target; documentation-only evidence.

**Evidence**: [feature-radar-sensor-streaming tree](https://github.com/The-Xverse/feature-radar-sensor-streaming/tree/45a60e87ca2b72d1820e4c8db1eb17fa9132f7c2); [README.md](https://github.com/The-Xverse/feature-radar-sensor-streaming/blob/45a60e87ca2b72d1820e4c8db1eb17fa9132f7c2/README.md).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/feature-radar-sensor-streaming |
| 2. Primary purpose | O/D — README describes AutoVerse orchestration, not a self-contained radar-streaming implementation. |
| 3. Language/build system | U — No executable language/build files in this repository. |
| 4. Runtime artifact produced | O — Documentation only (single README). |
| 5. Runtime dependencies | D — README describes CARLA, Zenoh, controller and bridge dependencies; no executable dependency definition here. |
| 6. Communication interfaces | D/U — Describes supervisor/bridge interfaces elsewhere; no local radar-stream contract. |
| 7. Protocols used | D — Zenoh/CAN/ROS2/VHAL mentioned; no local protocol implementation. |
| 8. Input/output contracts | U — Radar input/output contract not established by available source. |
| 9. Startup dependencies | D — Narrative startup flow only; no runnable launcher in this repository. |
| 10. Configuration mechanism | U — No local runtime configuration. |
| 11. Current integration | D — Describes the AutoVerse ecosystem; identity with current AutoVerse launcher cannot be assumed. |
| 12. Classification | I — Research PoC candidate/documentation, provisional. |
| 13. Candidate compatibility boundary | I — Reference-only until a radar implementation and contract are identified. |
| 14. Risks if changed | I — Treating repository title/documentation as implemented streaming would misstate capability. |
| 15. Recommended long-term treatment | I — Remain external pending implementation evidence. |

<a id="repo-freertos-vecu"></a>

## FreeRTOS-vECU

**Revision**: `dcddaa85868ed359971cf3a490b6d13066a0e26b` on `main`. **Maturity**: partial / under stabilization (provisional inventory assessment); runtime unverified.

**Evidence**: [FreeRTOS-vECU tree](https://github.com/The-Xverse/FreeRTOS-vECU/tree/dcddaa85868ed359971cf3a490b6d13066a0e26b); [README.md](https://github.com/The-Xverse/FreeRTOS-vECU/blob/dcddaa85868ed359971cf3a490b6d13066a0e26b/README.md); [stm32f411-blackpill/Core/Src/main.c](https://github.com/The-Xverse/FreeRTOS-vECU/blob/dcddaa85868ed359971cf3a490b6d13066a0e26b/stm32f411-blackpill/Core/Src/main.c).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/FreeRTOS-vECU |
| 2. Primary purpose | O/D — STM32 firmware project with FreeRTOS and vehicle-control/support modules. |
| 3. Language/build system | O/D — C/assembly, STM32CubeIDE/CubeMX-style project inputs, HAL/CMSIS/FreeRTOS. |
| 4. Runtime artifact produced | O — Firmware source and linker/device configuration; binary build/flash not verified. |
| 5. Runtime dependencies | O — Board/HAL dependencies, SPI CAN-controller support and UART peripherals. |
| 6. Communication interfaces | O — CAN-related modules, SPI peripheral access, UART diagnostics/HMI support in tree. |
| 7. Protocols used | O — CAN, SPI, UART as source-level integration surfaces; complete wire contract not audited. |
| 8. Input/output contracts | O/U — Firmware initializes peripherals and RTOS; detailed message behavior requires module/hardware validation. |
| 9. Startup dependencies | O/D — Board initialization precedes RTOS scheduler; physical flashing/power prerequisites require lab confirmation. |
| 10. Configuration mechanism | O — Device project configuration, headers, linker scripts, and board source. |
| 11. Current integration | O — AutoVerse manifest imports it as the CAN VCU variant; launcher instead starts Python VCU. |
| 12. Classification | I — Device/vECU implementation. |
| 13. Candidate compatibility boundary | I — External physical-device/firmware boundary via CAN and diagnostics. |
| 14. Risks if changed | I — Board pinout, firmware timing, control state, and frame-layout changes can disrupt hardware demos. |
| 15. Recommended long-term treatment | I — Remain specialized; wrap physical integration. |

<a id="repo-hwsim"></a>

## HwSim

**Revision**: `27bba949417483e618d2564401b27b1a39d5c439` on `main`. **Maturity**: partial / under stabilization (provisional inventory assessment); runtime unverified.

**Evidence**: [HwSim tree](https://github.com/The-Xverse/HwSim/tree/27bba949417483e618d2564401b27b1a39d5c439); [README.md](https://github.com/The-Xverse/HwSim/blob/27bba949417483e618d2564401b27b1a39d5c439/README.md); [pyproject.toml](https://github.com/The-Xverse/HwSim/blob/27bba949417483e618d2564401b27b1a39d5c439/pyproject.toml); [hwsim/transport/zenoh_gateway.py](https://github.com/The-Xverse/HwSim/blob/27bba949417483e618d2564401b27b1a39d5c439/hwsim/transport/zenoh_gateway.py).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/HwSim |
| 2. Primary purpose | O/D — Python virtual-hardware/model and test-evidence workbench, focused on selected microcontroller peripherals. |
| 3. Language/build system | O — Python/setuptools project; C software-component builds and optional web/Robot/Zenoh packages. |
| 4. Runtime artifact produced | O/D — Python CLI/library, generated models/tests, scenarios, reports and optional local web UI. |
| 5. Runtime dependencies | O — Pydantic, YAML/XML/template/CLI libraries; optional Robot Framework, web and Zenoh packages. |
| 6. Communication interfaces | O/D — CLI, scenario/IR files, C API wrappers and board request dispatcher; transport completeness varies. |
| 7. Protocols used | D/O — Zenoh keyspace described; inspected serve method opens a session but registers no handlers. |
| 8. Input/output contracts | D/O — Model/scenario inputs produce model state and evidence; board dispatcher exposes register/pin/UART operations in-process. |
| 9. Startup dependencies | D — Install selected extras and provide reviewed IR/scenario inputs; hardware accuracy remains explicitly bounded. |
| 10. Configuration mechanism | O/D — Existing IR/scenario/wrapper formats and CLI options; these are legacy formats, not new XDL. |
| 11. Current integration | U — No direct AutoVerse dependency established. O — Uses upstream Robot Framework package, not evidence of the organization placeholder repository. |
| 12. Classification | I — Simulator integration / reusable hardware tooling. |
| 13. Candidate compatibility boundary | I — Prefer existing CLI/evidence artifact boundary first; verify actual transport handlers before promising remote device control. |
| 14. Risks if changed | D/I — Register-level fidelity is not cycle accuracy or hardware validation; documentation can overstate transport completeness. |
| 15. Recommended long-term treatment | I — Wrap selected capabilities; leave internal model language external. |

<a id="repo-real_simulink"></a>

## real_simulink

**Revision**: `070669546cf98641fb5a083d1ea1a5c50ff14342` on `main`. **Maturity**: architectural target; documentation-only evidence.

**Evidence**: [real_simulink tree](https://github.com/The-Xverse/real_simulink/tree/070669546cf98641fb5a083d1ea1a5c50ff14342); [README.md](https://github.com/The-Xverse/real_simulink/blob/070669546cf98641fb5a083d1ea1a5c50ff14342/README.md).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/real_simulink |
| 2. Primary purpose | O — Only a title README is present; implementation purpose is not established. |
| 3. Language/build system | U — No language/build system established. |
| 4. Runtime artifact produced | O — Documentation placeholder only. |
| 5. Runtime dependencies | U — Runtime dependencies unknown. |
| 6. Communication interfaces | U — No interface contract present. |
| 7. Protocols used | U — No protocol established. |
| 8. Input/output contracts | U — No input/output contract present. |
| 9. Startup dependencies | U — No startup instructions. |
| 10. Configuration mechanism | U — No configuration mechanism. |
| 11. Current integration | U — No integration with simulink-vecu or deployed models is established by this snapshot. |
| 12. Classification | I — Simulator integration candidate, provisional. |
| 13. Candidate compatibility boundary | I — No executable boundary identified. |
| 14. Risks if changed | I — Model ownership may matter; runtime impact unknown. |
| 15. Recommended long-term treatment | I — Remain external pending evidence. |

<a id="repo-robot-framework"></a>

## robot-framework

**Revision**: `23d622fa898d3a32b4092d05220ddcc4d8d5ce2c` on `main`. **Maturity**: architectural target; documentation-only evidence.

**Evidence**: [robot-framework tree](https://github.com/The-Xverse/robot-framework/tree/23d622fa898d3a32b4092d05220ddcc4d8d5ce2c); [README.md](https://github.com/The-Xverse/robot-framework/blob/23d622fa898d3a32b4092d05220ddcc4d8d5ce2c/README.md).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/robot-framework |
| 2. Primary purpose | O — Only a title README is present; purpose beyond the repository name is unknown. |
| 3. Language/build system | U — No language/build system established. |
| 4. Runtime artifact produced | O — Documentation placeholder only. |
| 5. Runtime dependencies | U — Runtime dependencies unknown. |
| 6. Communication interfaces | U — No interface contract present. |
| 7. Protocols used | U — No protocol established. |
| 8. Input/output contracts | U — No input/output contract present. |
| 9. Startup dependencies | U — No startup instructions. |
| 10. Configuration mechanism | U — No configuration mechanism. |
| 11. Current integration | U — No current integration established; do not infer a dependency from HwSim using the upstream Robot Framework package. |
| 12. Classification | I — Support/tooling candidate, provisional. |
| 13. Candidate compatibility boundary | I — No runtime boundary until implementation evidence exists. |
| 14. Risks if changed | I — Ownership/roadmap expectations may exist; no runtime change impact can be established. |
| 15. Recommended long-term treatment | I — Remain external pending clarification. |

<a id="repo-simulink-vecu"></a>

## simulink-vecu

**Revision**: `505ba3402713f41bc9c7bb2d2c12bf080d421957` on `main`. **Maturity**: partial / under stabilization (provisional inventory assessment); runtime unverified.

**Evidence**: [simulink-vecu tree](https://github.com/The-Xverse/simulink-vecu/tree/505ba3402713f41bc9c7bb2d2c12bf080d421957); [README.md](https://github.com/The-Xverse/simulink-vecu/blob/505ba3402713f41bc9c7bb2d2c12bf080d421957/README.md); [pid_controller/main.py](https://github.com/The-Xverse/simulink-vecu/blob/505ba3402713f41bc9c7bb2d2c12bf080d421957/pid_controller/main.py); [pid_controller/zenoh_handler.py](https://github.com/The-Xverse/simulink-vecu/blob/505ba3402713f41bc9c7bb2d2c12bf080d421957/pid_controller/zenoh_handler.py).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/simulink-vecu |
| 2. Primary purpose | O/D — Python PID velocity-control implementation and related modeling assets. |
| 3. Language/build system | O/D — Python, Zenoh, NumPy/Matplotlib; tree also includes modeling/generated assets. |
| 4. Runtime artifact produced | O — Python executable, container recipe, model/support files; built image not verified. |
| 5. Runtime dependencies | O — Zenoh session and clock/velocity/enable/delta inputs; Python controller and plotting libraries. |
| 6. Communication interfaces | O — Zenoh input subscriptions, control/target publications, result logs and plot output. |
| 7. Protocols used | O — Zenoh; no native FMI/FMU runtime interface established by inspected sources. |
| 8. Input/output contracts | O — Clock, velocity, delta-speed and engagement inputs produce target speed and control request. README examples and current topic set differ. |
| 9. Startup dependencies | O — Initialize controller/session before subscribing; valid timestamp and enable inputs matter for behavior. |
| 10. Configuration mechanism | O — Optional router CLI argument and source-defined topic/tuning parameters. |
| 11. Current integration | O — Imported by AutoVerse; D — included in README PID sequence, but absent from the current launcher step list. |
| 12. Classification | I — Device/vECU implementation. |
| 13. Candidate compatibility boundary | I — Wrap the existing controller process, inputs, outputs, and artifacts; do not infer an FMU from the repository name. |
| 14. Risks if changed | I — Topic spelling, timing units, enabling logic, and headless result generation affect compatibility. |
| 15. Recommended long-term treatment | I — Wrap; retain specialized controller behavior. |

<a id="repo-synchronous-simulation-mode"></a>

## synchronous-simulation-mode

**Revision**: `fcabd104bad9bc904be5cba329fbf6f791bdf294` on `synchronous-simulation-mode`. **Maturity**: architectural target; documentation-only evidence.

**Evidence**: [synchronous-simulation-mode tree](https://github.com/The-Xverse/synchronous-simulation-mode/tree/fcabd104bad9bc904be5cba329fbf6f791bdf294); [README.md](https://github.com/The-Xverse/synchronous-simulation-mode/blob/fcabd104bad9bc904be5cba329fbf6f791bdf294/README.md).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/synchronous-simulation-mode |
| 2. Primary purpose | O/D — Single README describing desired CARLA synchronous-mode and time-integration work. |
| 3. Language/build system | U — No executable build system established. |
| 4. Runtime artifact produced | O — Documentation only. |
| 5. Runtime dependencies | D — Intended CARLA/runtime/Zenoh integration; no resolved runtime dependencies. |
| 6. Communication interfaces | U — No executable time-management interface. |
| 7. Protocols used | D — CARLA and Zenoh named as intended integration targets. |
| 8. Input/output contracts | U — No implemented clock or synchronization contract. |
| 9. Startup dependencies | U — No executable startup flow. |
| 10. Configuration mechanism | U — No actual configuration files. |
| 11. Current integration | D — Intended integration only; no component linkage established. |
| 12. Classification | I — Research PoC/architectural-target candidate. |
| 13. Candidate compatibility boundary | I — No runtime boundary until implementation is identified. |
| 14. Risks if changed | I — Claiming deterministic simulation from the README alone would overstate maturity. |
| 15. Recommended long-term treatment | I — Remain external; use as a requirement input only. |

<a id="repo-vcu-zenoh-python"></a>

## vcu-zenoh-python

**Revision**: `125566ef561fbd601defec22d5846068448722b9` on `main`. **Maturity**: partial / under stabilization (provisional inventory assessment); runtime unverified.

**Evidence**: [vcu-zenoh-python tree](https://github.com/The-Xverse/vcu-zenoh-python/tree/125566ef561fbd601defec22d5846068448722b9); [README.md](https://github.com/The-Xverse/vcu-zenoh-python/blob/125566ef561fbd601defec22d5846068448722b9/README.md); [src/main.py](https://github.com/The-Xverse/vcu-zenoh-python/blob/125566ef561fbd601defec22d5846068448722b9/src/main.py).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/vcu-zenoh-python |
| 2. Primary purpose | O/D — Python vehicle controller for cruise engagement, reverse state, and throttle routing. |
| 3. Language/build system | O — Python with Zenoh; requirements and executable source present. |
| 4. Runtime artifact produced | O — Python executable and startup script. |
| 5. Runtime dependencies | O/D — Zenoh session, driver/vehicle state, and ADAS control inputs. |
| 6. Communication interfaces | O/D — Configured Zenoh subscribers and publishers; optional session configuration file. |
| 7. Protocols used | O — Zenoh. |
| 8. Input/output contracts | D/O — Vehicle/request/control inputs produce engagement/reverse state and throttle output; safety descriptions are not certification evidence. |
| 9. Startup dependencies | O — Executable main initializes controller and runs it; README module command differs from tree layout. |
| 10. Configuration mechanism | O — CLI configuration path and source signal/constants definitions. |
| 11. Current integration | O — Imported and launched by AutoVerse as the Python VCU. |
| 12. Classification | I — Device/vECU implementation. |
| 13. Candidate compatibility boundary | I — Wrap process and version-specific message contract; preserve domain control logic externally. |
| 14. Risks if changed | I — Entry-point assumptions, interlocks, payload types, and signal mappings can change behavior. |
| 15. Recommended long-term treatment | I — Wrap; keep automotive logic specialized. |

<a id="repo-vecu-grafic-user-interface"></a>

## vECU-Grafic-User-Interface

**Revision**: `561170a9a1a66d5a7e792701f8ad492c54ce9c33` on `main`. **Maturity**: partial / under stabilization (provisional inventory assessment); runtime unverified.

**Evidence**: [vECU-Grafic-User-Interface tree](https://github.com/The-Xverse/vECU-Grafic-User-Interface/tree/561170a9a1a66d5a7e792701f8ad492c54ce9c33); [README.md](https://github.com/The-Xverse/vECU-Grafic-User-Interface/blob/561170a9a1a66d5a7e792701f8ad492c54ce9c33/README.md).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/vECU-Grafic-User-Interface |
| 2. Primary purpose | O/D — Embedded display/HMI project for an existing hardware demonstration. |
| 3. Language/build system | O/D — DWIN DGUS tooling, HMI assets and bundled Windows tools/documentation. |
| 4. Runtime artifact produced | O — Display project/resources and firmware-loading asset archive. |
| 5. Runtime dependencies | D — Compatible display, DGUS toolchain, transfer media, and serial communication setup. |
| 6. Communication interfaces | D — Display control through framed binary/hex commands. |
| 7. Protocols used | D — Device-specific serial HMI protocol. |
| 8. Input/output contracts | D — Commands update display pages, fields and indicators; exact command values omitted. |
| 9. Startup dependencies | D — Transfer display assets then power-cycle as documented; no host runtime orchestration established. |
| 10. Configuration mechanism | D — HMI project assets and variable/address allocation. |
| 11. Current integration | D — Described as a demonstration GUI. U — No precise firmware/board pairing proven. |
| 12. Classification | I — Demonstrator/application. |
| 13. Candidate compatibility boundary | I — Physical-display adapter using existing serial contract and versioned assets. |
| 14. Risks if changed | I — Asset addresses, firmware and display layout changes affect existing hardware behavior. |
| 15. Recommended long-term treatment | I — Remain specialized. |

<a id="repo-vecu_board"></a>

## vECU_Board

**Revision**: `ee5e295843e1ad591ca76db5b9abd41e1ca30243` on `main`. **Maturity**: partial / under stabilization (provisional inventory assessment); runtime unverified.

**Evidence**: [vECU_Board tree](https://github.com/The-Xverse/vECU_Board/tree/ee5e295843e1ad591ca76db5b9abd41e1ca30243); [vECU_STM32fF411/fp-lib-table](https://github.com/The-Xverse/vECU_Board/blob/ee5e295843e1ad591ca76db5b9abd41e1ca30243/vECU_STM32fF411/fp-lib-table).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/vECU_Board |
| 2. Primary purpose | O — KiCad board-design/manufacturing asset repository. |
| 3. Language/build system | O — KiCad schematic, PCB/project, library-table and manufacturing files. |
| 4. Runtime artifact produced | O — Hardware design, BOM-like CSV and Gerber/drill assets; manufactured hardware not verified. |
| 5. Runtime dependencies | O — External footprint library reference uses a machine-specific path. U — Full library resolution unverified. |
| 6. Communication interfaces | O/U — EDA files are the observed interface; physical pin/connector contract not audited. |
| 7. Protocols used | U — No runtime protocol inferred from board naming. |
| 8. Input/output contracts | O — Design/library inputs produce manufacturing assets; electrical I/O requires schematic review. |
| 9. Startup dependencies | I — No executable startup; fabrication, assembly, flashing and lab setup belong to later device integration. |
| 10. Configuration mechanism | O — KiCad project/library tables; workstation paths omitted. |
| 11. Current integration | D — Footprint and symbol companion READMEs refer here. U — Exact library association is not fully verified. |
| 12. Classification | I — Support/tooling (hardware artifact). |
| 13. Candidate compatibility boundary | I — Reference versioned hardware artifacts; future device descriptor must bind actual board/firmware revision. |
| 14. Risks if changed | I — Library, pinout and fabrication changes can invalidate physical hardware compatibility. |
| 15. Recommended long-term treatment | I — Remain specialized. |

<a id="repo-vecu_component-symbols"></a>

## vECU_Component-Symbols

**Revision**: `361c7af126c70263fe241b6afee0d1cb39eaf1ba` on `main`. **Maturity**: partial / under stabilization (provisional inventory assessment); runtime unverified.

**Evidence**: [vECU_Component-Symbols tree](https://github.com/The-Xverse/vECU_Component-Symbols/tree/361c7af126c70263fe241b6afee0d1cb39eaf1ba); [README.md](https://github.com/The-Xverse/vECU_Component-Symbols/blob/361c7af126c70263fe241b6afee0d1cb39eaf1ba/README.md).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/vECU_Component-Symbols |
| 2. Primary purpose | O — KiCad symbol libraries with README pointing to the board repository. |
| 3. Language/build system | O — KiCad symbol format; no executable build system. |
| 4. Runtime artifact produced | O — Hardware/EDA library artifacts. |
| 5. Runtime dependencies | D — Companion board-design workflow. |
| 6. Communication interfaces | O — KiCad symbol-library interface. |
| 7. Protocols used | U — No runtime protocol. |
| 8. Input/output contracts | O — Symbols consumed by schematic tools; electrical contract not audited. |
| 9. Startup dependencies | I — No process startup; load library in compatible EDA tooling. |
| 10. Configuration mechanism | O — Symbol library files. |
| 11. Current integration | D — README refers to vECU_Board. |
| 12. Classification | I — Support/tooling (hardware library). |
| 13. Candidate compatibility boundary | I — External versioned design dependency, not runtime plugin. |
| 14. Risks if changed | I — Symbol/pin mapping changes can affect schematic and downstream board correctness. |
| 15. Recommended long-term treatment | I — Remain specialized. |

<a id="repo-vecu_footprints"></a>

## vECU_FootPrints

**Revision**: `857b8fbf1571db154052383710f503c37c21d93e` on `main`. **Maturity**: partial / under stabilization (provisional inventory assessment); runtime unverified.

**Evidence**: [vECU_FootPrints tree](https://github.com/The-Xverse/vECU_FootPrints/tree/857b8fbf1571db154052383710f503c37c21d93e); [README.md](https://github.com/The-Xverse/vECU_FootPrints/blob/857b8fbf1571db154052383710f503c37c21d93e/README.md).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/vECU_FootPrints |
| 2. Primary purpose | O — KiCad footprint library assets with README pointing to the board repository. |
| 3. Language/build system | O — KiCad footprint format; no executable build system. |
| 4. Runtime artifact produced | O — Hardware/EDA library artifacts. |
| 5. Runtime dependencies | D — Companion board-design workflow. |
| 6. Communication interfaces | O — KiCad library-file interface. |
| 7. Protocols used | U — No runtime protocol. |
| 8. Input/output contracts | O — Footprints consumed by board-design tools; electrical behavior not established. |
| 9. Startup dependencies | I — No process startup; load library in compatible EDA tooling. |
| 10. Configuration mechanism | O — Footprint files and library directories. |
| 11. Current integration | D — README refers to vECU_Board. |
| 12. Classification | I — Support/tooling (hardware library). |
| 13. Candidate compatibility boundary | I — External versioned design dependency, not runtime plugin. |
| 14. Risks if changed | I — Land-pattern changes affect layout/manufacturing compatibility. |
| 15. Recommended long-term treatment | I — Remain specialized. |

<a id="repo-x-verse"></a>

## x-verse

**Revision**: `05cba92f4be0f786d86511a99521079ff0ae8b7f` on `main`. **Maturity**: architectural target; documentation-only evidence.

**Evidence**: [x-verse tree](https://github.com/The-Xverse/x-verse/tree/05cba92f4be0f786d86511a99521079ff0ae8b7f); [README.md](https://github.com/The-Xverse/x-verse/blob/05cba92f4be0f786d86511a99521079ff0ae8b7f/README.md).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/x-verse |
| 2. Primary purpose | O — Only an X-Verse title README is present. |
| 3. Language/build system | U — No language/build system established. |
| 4. Runtime artifact produced | O — Documentation placeholder only. |
| 5. Runtime dependencies | U — Runtime dependencies unknown. |
| 6. Communication interfaces | U — No interface contract present. |
| 7. Protocols used | U — No protocol established. |
| 8. Input/output contracts | U — No input/output contract present. |
| 9. Startup dependencies | U — No startup instructions. |
| 10. Configuration mechanism | U — No configuration mechanism. |
| 11. Current integration | U — No executable integration established. |
| 12. Classification | I — Platform infrastructure candidate, provisional; not the new xverse-platform implementation. |
| 13. Candidate compatibility boundary | I — Reference context only; no executable boundary. |
| 14. Risks if changed | I — Naming/ownership continuity may matter; deployed impact unknown. |
| 15. Recommended long-term treatment | I — Remain external; do not rename or migrate. |

<a id="repo-zenoh-core"></a>

## zenoh-core

**Revision**: `e65b10287fcc60962cbd3dd42caadd94f69a91e3` on `main`. **Maturity**: partial / under stabilization (provisional inventory assessment); runtime unverified.

**Evidence**: [zenoh-core tree](https://github.com/The-Xverse/zenoh-core/tree/e65b10287fcc60962cbd3dd42caadd94f69a91e3); [README.md](https://github.com/The-Xverse/zenoh-core/blob/e65b10287fcc60962cbd3dd42caadd94f69a91e3/README.md); [vehicle/Cargo.toml](https://github.com/The-Xverse/zenoh-core/blob/e65b10287fcc60962cbd3dd42caadd94f69a91e3/vehicle/Cargo.toml); [vehicle/src/main.rs](https://github.com/The-Xverse/zenoh-core/blob/e65b10287fcc60962cbd3dd42caadd94f69a91e3/vehicle/src/main.rs).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/zenoh-core |
| 2. Primary purpose | O/D — Zenoh development environment plus Rust vehicle-side integration. |
| 3. Language/build system | O — Dockerfile, Python examples, Rust/Cargo vehicle binary and Just recipes. |
| 4. Runtime artifact produced | O — Container recipe, Python utilities, Rust executable source. |
| 5. Runtime dependencies | O — Rust manifest uses Tokio/Zenoh and a relative-path CARLA binding; runtime connects to a CARLA actor. |
| 6. Communication interfaces | O — Zenoh telemetry/control and CARLA client API; executable CLI. |
| 7. Protocols used | O — Zenoh and CARLA RPC. |
| 8. Input/output contracts | O — Vehicle controller consumes control signals and publishes clock/velocity; encoding and simulation settings require baseline-specific validation. |
| 9. Startup dependencies | O/D — CARLA server and matching actor/bindings before vehicle control; peer discovery or configured router. |
| 10. Configuration mechanism | O — CLI options, Zenoh configuration, Cargo dependencies, and recipe settings. |
| 11. Current integration | O — Imported by AutoVerse; README cruise-control sequence starts its Rust binary. |
| 12. Classification | I — Platform infrastructure with domain-specific device/control implementation. |
| 13. Candidate compatibility boundary | I — Separate external Zenoh utilities from the automotive vehicle process; do not import the latter into vNext core. |
| 14. Risks if changed | O/I — Relative build dependency and vehicle/time behavior make version or topic changes disruptive. |
| 15. Recommended long-term treatment | I — Wrap selected artifacts; keep vehicle logic specialized. |

<a id="repo-zenoh2can_bridge"></a>

## zenoh2can_bridge

**Revision**: `087c5f8a2e63e01c4213cd33161b64e50ffd047d` on `main`. **Maturity**: partial / under stabilization (provisional inventory assessment); runtime unverified.

**Evidence**: [zenoh2can_bridge tree](https://github.com/The-Xverse/zenoh2can_bridge/tree/087c5f8a2e63e01c4213cd33161b64e50ffd047d); [README.md](https://github.com/The-Xverse/zenoh2can_bridge/blob/087c5f8a2e63e01c4213cd33161b64e50ffd047d/README.md); [can-zenoh-bridge-python/README.md](https://github.com/The-Xverse/zenoh2can_bridge/blob/087c5f8a2e63e01c4213cd33161b64e50ffd047d/can-zenoh-bridge-python/README.md); [can-zenoh-bridge-python/src/bridge.py](https://github.com/The-Xverse/zenoh2can_bridge/blob/087c5f8a2e63e01c4213cd33161b64e50ffd047d/can-zenoh-bridge-python/src/bridge.py).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/zenoh2can_bridge |
| 2. Primary purpose | O/D — Configurable Python bridge between Zenoh and CAN buses. |
| 3. Language/build system | O — Python with python-can, Zenoh, JSON and binary encoding helpers. |
| 4. Runtime artifact produced | O — Executable bridge, launch/configuration files, and test scripts. |
| 5. Runtime dependencies | O/D — Configured CAN backend, Zenoh endpoints; physical drivers/hardware for physical mode. |
| 6. Communication interfaces | O — CAN bus/frame mappings and Zenoh signal/aggregate publications/subscriptions. |
| 7. Protocols used | O — CAN and Zenoh; backend-specific hardware or virtual CAN. |
| 8. Input/output contracts | O — Configured signal encoding/scaling and mappings translate CAN frames and Zenoh values. |
| 9. Startup dependencies | D — Prepare selected bus/driver and communication environment, then load configuration and start bridge. |
| 10. Configuration mechanism | O — JSON bus/mapping configuration supplied to process; values omitted. |
| 11. Current integration | O — Imported in AutoVerse manifest; CAN integration is a workspace option rather than current supervisor step. |
| 12. Classification | I — Reusable adapter. |
| 13. Candidate compatibility boundary | I — Wrap existing process and map its declared bus capabilities externally. |
| 14. Risks if changed | I — Encoding, byte order, scaling, pulses, and backend assumptions affect parity. |
| 15. Recommended long-term treatment | I — Wrap; validate virtual and physical backends separately. |

<a id="repo-zenoh2ros2_bridge"></a>

## zenoh2ros2_bridge

**Revision**: `ef83ee85b664d9defec1128a345803715ea3cba1` on `main`. **Maturity**: partial / under stabilization (provisional inventory assessment); runtime unverified.

**Evidence**: [zenoh2ros2_bridge tree](https://github.com/The-Xverse/zenoh2ros2_bridge/tree/ef83ee85b664d9defec1128a345803715ea3cba1); [README.md](https://github.com/The-Xverse/zenoh2ros2_bridge/blob/ef83ee85b664d9defec1128a345803715ea3cba1/README.md); [ros2-zenoh-bridge-python/README.md](https://github.com/The-Xverse/zenoh2ros2_bridge/blob/ef83ee85b664d9defec1128a345803715ea3cba1/ros2-zenoh-bridge-python/README.md); [ros2-zenoh-bridge-python/src/bridge.py](https://github.com/The-Xverse/zenoh2ros2_bridge/blob/ef83ee85b664d9defec1128a345803715ea3cba1/ros2-zenoh-bridge-python/src/bridge.py).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/zenoh2ros2_bridge |
| 2. Primary purpose | O/D — Python bridge between ROS2 and Zenoh. |
| 3. Language/build system | O — Python with rclpy, rosidl utilities, NumPy, and Zenoh. |
| 4. Runtime artifact produced | O — Python executable and configuration files. |
| 5. Runtime dependencies | O — ROS2 runtime/message packages, Zenoh session, and selected mappings. |
| 6. Communication interfaces | O — ROS topic publishers/subscribers and Zenoh keys. |
| 7. Protocols used | O — ROS2 middleware and Zenoh; encoder supports CDR/JSON on ROS-to-Zenoh path. |
| 8. Input/output contracts | O — Source advertises configurable types, but active Zenoh-to-ROS callback constructs Float64 instead of using the generic decoder. |
| 9. Startup dependencies | O — Load JSON mappings and initialize Zenoh and ROS2 before spinning. |
| 10. Configuration mechanism | O — Required configuration-file argument and optional ROS domain selection. |
| 11. Current integration | O — AutoVerse manifest imports the bridge; it is not a current supervisor step. |
| 12. Classification | I — Reusable adapter. |
| 13. Candidate compatibility boundary | I — Wrap only the verified message subset; require contract tests before claiming generic bidirectionality. |
| 14. Risks if changed | O/I — Documentation/configuration and implemented decoding differ; assuming arbitrary message support risks failures. |
| 15. Recommended long-term treatment | I — Wrap with explicit capability limits. |

<a id="repo-zenoh2someip_bridge"></a>

## zenoh2someip_bridge

**Revision**: `7c393c9f5a49239c76122486c49cb1993164475c` on `main`. **Maturity**: partial / under stabilization (provisional inventory assessment); runtime unverified.

**Evidence**: [zenoh2someip_bridge tree](https://github.com/The-Xverse/zenoh2someip_bridge/tree/7c393c9f5a49239c76122486c49cb1993164475c); [README.md](https://github.com/The-Xverse/zenoh2someip_bridge/blob/7c393c9f5a49239c76122486c49cb1993164475c/README.md).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/zenoh2someip_bridge |
| 2. Primary purpose | O/D — C++ gateway forwarding between Zenoh and SOME/IP. |
| 3. Language/build system | O/D — C++17/CMake, Boost, vsomeip, Zenoh C/C++, JSON and queue libraries. |
| 4. Runtime artifact produced | O/D — Gateway/test executable build targets and external library artifacts. |
| 5. Runtime dependencies | D — Matching mapping and vsomeip configuration, external shared libraries including LFS-managed files. |
| 6. Communication interfaces | O/D — Zenoh keys mapped to SOME/IP services/events; process configuration boundary. |
| 7. Protocols used | D — Zenoh and SOME/IP. |
| 8. Input/output contracts | D — Bidirectional mapped messages/events; provider/consumer service identities must be separated. |
| 9. Startup dependencies | D — Build dependencies and configure service mappings before gateway and test peers. |
| 10. Configuration mechanism | O/D — JSON mapping and vsomeip configuration files. |
| 11. Current integration | O — AutoVerse imports and launches gateway before S-CORE containers. |
| 12. Classification | I — Reusable adapter. |
| 13. Candidate compatibility boundary | I — Wrap existing gateway executable and configuration; preserve payload and service identifiers. |
| 14. Risks if changed | D/I — Service-ID conflicts, library versions, and payload changes can break discovery or routing. |
| 15. Recommended long-term treatment | I — Wrap; do not reimplement protocol logic in core. |

<a id="repo-zephyr-bcm"></a>

## Zephyr-BCM

**Revision**: `23454fd9764adbc3be2301be10cfeb5b2660a307` on `main`. **Maturity**: partial / under stabilization (provisional inventory assessment); runtime unverified.

**Evidence**: [Zephyr-BCM tree](https://github.com/The-Xverse/Zephyr-BCM/tree/23454fd9764adbc3be2301be10cfeb5b2660a307); [README.md](https://github.com/The-Xverse/Zephyr-BCM/blob/23454fd9764adbc3be2301be10cfeb5b2660a307/README.md).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/Zephyr-BCM |
| 2. Primary purpose | O/D — BCM repository containing emulator script and packaged artifacts. |
| 3. Language/build system | O — Renode script, split container archive and ZIP; no unpacked application build sources inspected. |
| 4. Runtime artifact produced | O — Packaged artifacts and emulator configuration; archive contents were not extracted. |
| 5. Runtime dependencies | I/U — Renode/container and firmware prerequisites require verification of packaged artifacts. |
| 6. Communication interfaces | U — README does not define component communication or lifecycle contracts. |
| 7. Protocols used | U — No protocol inferred merely from the BCM name. |
| 8. Input/output contracts | U — Input/output contract not established. |
| 9. Startup dependencies | O/U — Emulator script present; runnable setup and artifact provenance unverified. |
| 10. Configuration mechanism | O — Emulator script and opaque archives; local values not published. |
| 11. Current integration | U — Not the zephyr-vecu repository imported by AutoVerse; equivalence is unproven. |
| 12. Classification | I — Device/vECU implementation candidate, provisional. |
| 13. Candidate compatibility boundary | I — Candidate emulator/artifact boundary only after provenance and interface review. |
| 14. Risks if changed | I — Archive opacity and ambiguous overlap with zephyr-vecu risk incorrect substitution. |
| 15. Recommended long-term treatment | I — Remain external pending artifact verification. |

<a id="repo-zephyr-vecu"></a>

## zephyr-vecu

**Revision**: `d93d0f17b38988783977b1adaeedbabcd0e3e0ec` on `main`. **Maturity**: partial / under stabilization (provisional inventory assessment); runtime unverified.

**Evidence**: [zephyr-vecu tree](https://github.com/The-Xverse/zephyr-vecu/tree/d93d0f17b38988783977b1adaeedbabcd0e3e0ec); [README.md](https://github.com/The-Xverse/zephyr-vecu/blob/d93d0f17b38988783977b1adaeedbabcd0e3e0ec/README.md); [apps/can-bcm-vecu/README.md](https://github.com/The-Xverse/zephyr-vecu/blob/d93d0f17b38988783977b1adaeedbabcd0e3e0ec/apps/can-bcm-vecu/README.md); [apps/can-bcm-vecu/src/main.c](https://github.com/The-Xverse/zephyr-vecu/blob/d93d0f17b38988783977b1adaeedbabcd0e3e0ec/apps/can-bcm-vecu/src/main.c).

| Required field | Finding |
|---|---|
| 1. Repository name | O — The-Xverse/zephyr-vecu |
| 2. Primary purpose | O/D — Zephyr applications including a CAN body-control vECU and samples. |
| 3. Language/build system | O/D — C, Zephyr SDK/West/CMake, board definitions, and Renode scripts. |
| 4. Runtime artifact produced | O/D — Firmware build inputs and emulator configurations; built firmware not verified. |
| 5. Runtime dependencies | D — Zephyr toolchain; Renode and virtual CAN for the documented BCM example. |
| 6. Communication interfaces | O/D — CAN receive/send, UART diagnostics, and board/device interfaces. |
| 7. Protocols used | O — CAN and UART; virtual CAN is a documented execution option. |
| 8. Input/output contracts | O/D — BCM consumes VCU status and emits body-command frames; exact frame layout remains in restricted source. |
| 9. Startup dependencies | D — Set up virtual CAN, build the selected board/application, then launch Renode. |
| 10. Configuration mechanism | O/D — Board/Kconfig/devicetree and emulator configuration. |
| 11. Current integration | O — Imported by AutoVerse as BCM CAN workspace dependency; not a current supervisor step. |
| 12. Classification | I — Device/vECU implementation. |
| 13. Candidate compatibility boundary | I — Wrap firmware/emulator lifecycle and CAN interface; physical and emulated realizations remain distinct. |
| 14. Risks if changed | I — Board selection, frame layout, or toolchain changes can invalidate existing integrations. |
| 15. Recommended long-term treatment | I — Wrap the selected application; retain board logic externally. |

## Coverage gaps and M1 implications

- Five legacy repositories have only a README: x-verse, robot-framework, real_simulink,
feature-radar-sensor-streaming, synchronous-simulation-mode. Their runtime contracts remain unknown
or aspirational. Do not create catalog entries claiming runnable implementations from their names.
- Zephyr-BCM archives, hardware/EDA files, bundled GUI tools/APKs, LFS binaries and downloaded images
were not executed or unpacked. Provenance, reproducible builds, and compatibility remain unverified.
- Source and documentation disagree on startup variants, ROS2 conversion generality, Cuttlefish
launcher integration, and HwSim transport completeness. See the review and interface reports.
- The supported production baseline, health/readiness criteria, timing envelopes, shutdown outcomes,
and representative signal captures require owner review and later controlled parity work.
- No inaccessible legacy source or truncated tree was encountered in the selected scope. This does
not prove access to undisclosed repositories or completeness of every branch/release.
