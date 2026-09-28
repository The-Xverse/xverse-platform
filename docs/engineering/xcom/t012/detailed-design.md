# T012 Detailed Design — Subtree Build Rules, Sanitizer Opt-In, and Contract Verification

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T012 (capability 007, slice `T-CORE`) |
| Stage / role | plan → detailed design |
| Revision | 1 |
| Baseline revision | `ade79ee1f73f176c0178b77d6b10ed8ba8587da6` |
| Requirements authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed design | `docs/engineering/xcom/t011/detailed-design.md` §6 (admitted build contract); `docs/engineering/xcom/t010/detailed-design.md` |
| Classification | Public-safe engineering work product |

## 2. Design overview

T012's design has three cooperating parts, all realized in the single shared production path
`src/xverse/xcom/CMakeLists.txt`:

1. **Subtree rules** — a declaration block that names the runtime target inventory, asserts the inherited
   warning-as-error policy, and resolves the opt-in sanitizer selection (§4).
2. **Uniform application** — every runtime and test target is routed through one helper so the rules cannot
   be applied to some targets and forgotten on others (§5).
3. **Contract verification** — the effective policy is emitted as generated evidence beneath the build tree
   and checked by one deterministic, offline CTest target (§6).

The design is additive: with `XVERSE_XCOM_SANITIZERS` empty (the default), the produced targets, compiler
invocations, CTest names, and labels are the baseline's, plus one new build-contract test.

## 3. Design constraints and invariants

| ID | Invariant |
| --- | --- |
| `INV-01` | Every target defined under `src/xverse/xcom/` is C++20 with extensions disabled. |
| `INV-02` | Every runtime and test target links `xverse::xcom_warnings`; the effective options include `-Wall -Wextra -Wpedantic -Werror`. |
| `INV-03` | Configuration terminates before defining accepted targets when the warning policy is absent or not promoted to an error. |
| `INV-04` | The empty sanitizer selection adds no `-fsanitize` flag to any target; a non-empty selection adds the selected flags to every runtime and test target. |
| `INV-05` | An unknown sanitizer entry or the `address`+`thread` combination terminates configuration; no partial target set is presented. |
| `INV-06` | Every baseline CTest name and label is preserved; the only added test is `xcom_build_contract` (label `t012`). |
| `INV-07` | The build-contract verifier is deterministic, offline, and returns a specific nonzero result naming the violated invariant. |
| `INV-08` | No new mandatory environment input is introduced; the admitted inputs are consumed unmodified. |
| `INV-09` | No network client, resolver, package manager, registry, FetchContent resolution, or added thread. |
| `INV-10` | Generated contract evidence exists only beneath the build directory; committed files contain no absolute host path. |
| `INV-11` | The candidate changes no `.cpp`/`.hpp`, no `tests/` source, and no accepted ADR, requirement, test, or ownership path. |
| `INV-12` | The declared runtime target inventory is exactly the six baseline libraries plus their aliases. |

## 4. Subtree rules (rules block, prepended before any target)

The rule block is inserted near the top of `src/xverse/xcom/CMakeLists.txt`, before the first
`add_library`. Function definitions inherit the root scope, including the root helper
`_xverse_xcom_json_string` used later for evidence generation.

### 4.1 Declared runtime inventory

```cmake
set(
  XVERSE_XCOM_RUNTIME_TARGETS
  xverse_xcom_core_types
  xverse_xcom_observation
  xverse_xcom_endpoint_route_lifecycle
  xverse_xcom_provider_loopback
  xverse_xcom_validation_session
  xverse_xcom_activation_plan
)
```

The order is declared and deterministic and matches the baseline target definitions. Aliases
(`xverse::xcom_core_types`, …) are unchanged and are not part of the compiled inventory.

### 4.2 Warning-policy assertion (`T12-CMP-WARN`)

```cmake
function(xverse_xcom_assert_runtime_warning_policy)
  if(NOT TARGET xverse::xcom_warnings)
    message(FATAL_ERROR "X-COM subtree requires the inherited xverse::xcom_warnings target")
  endif()
  get_target_property(_xcom_warning_options xverse::xcom_warnings INTERFACE_COMPILE_OPTIONS)
  if(NOT _xcom_warning_options)
    message(FATAL_ERROR "X-COM warning policy publishes no compile options")
  endif()
  set(_xcom_promotes_errors FALSE)
  foreach(_option IN LISTS _xcom_warning_options)
    if(_option STREQUAL "-Werror" OR _option STREQUAL "/WX" OR _option MATCHES "^-Werror=")
      set(_xcom_promotes_errors TRUE)
    endif()
  endforeach()
  if(NOT _xcom_promotes_errors)
    message(FATAL_ERROR "X-COM warning policy does not promote warnings to errors")
  endif()
endfunction()
```

### 4.3 Sanitizer selection (`T12-CMP-SAN`)

```cmake
function(xverse_xcom_runtime_sanitizers)
  set(_selected_compile "" PARENT_SCOPE)
  set(_selected_link "" PARENT_SCOPE)
  set(_requested "${XVERSE_XCOM_SANITIZERS}")
  if("${_requested}" STREQUAL "")
    return()
  endif()
  string(REPLACE "," ";" _requested "${_requested}")
  set(_seen "")
  foreach(_name IN LISTS _requested)
    if(NOT _name MATCHES "^(address|thread|undefined)$")
      message(FATAL_ERROR "Unsupported XVERSE_XCOM_SANITIZERS entry '${_name}'")
    endif()
    if(_name IN_LIST _seen)
      continue()
    endif()
    list(APPEND _seen "${_name}")
  endforeach()
  if("address" IN_LIST _seen AND "thread" IN_LIST _seen)
    message(FATAL_ERROR "XVERSE_XCOM_SANITIZERS: address and thread are mutually exclusive")
  endif()
  foreach(_name IN LISTS _seen)
    if(_name STREQUAL "address")
      list(APPEND _selected_compile -fsanitize=address -fno-omit-frame-pointer)
      list(APPEND _selected_link -fsanitize=address)
    elseif(_name STREQUAL "thread")
      list(APPEND _selected_compile -fsanitize=thread)
      list(APPEND _selected_link -fsanitize=thread)
    else()
      list(APPEND _selected_compile -fsanitize=undefined -fno-sanitize-recover=undefined)
      list(APPEND _selected_link -fsanitize=undefined)
    endif()
  endforeach()
  set(_selected_compile "${_selected_compile}" PARENT_SCOPE)
  set(_selected_link "${_selected_link}" PARENT_SCOPE)
endfunction()
```

| Selection | Compile flags | Link flags |
| --- | --- | --- |
| (empty, default) | none | none |
| `address` | `-fsanitize=address -fno-omit-frame-pointer` | `-fsanitize=address` |
| `thread` | `-fsanitize=thread` | `-fsanitize=thread` |
| `undefined` | `-fsanitize=undefined -fno-sanitize-recover=undefined` | `-fsanitize=undefined` |

Mutual exclusion exists because ASan and TSan cannot be combined in one binary; combining them with UBSan is
permitted. Unsupported sanitizers fail configuration rather than being silently ignored (T011-SR-006's
"reported, not assumed").

### 4.4 Uniform application (`T12-CMP-INV`)

```cmake
function(xverse_xcom_apply_runtime_rules target)
  if(NOT TARGET "${target}")
    message(FATAL_ERROR "Cannot configure missing X-COM target ${target}")
  endif()
  xverse_xcom_apply_warnings("${target}")
  if(xverse_xcom_sanitize_compile)
    target_compile_options("${target}" PRIVATE ${xverse_xcom_sanitize_compile})
    target_link_options("${target}" PRIVATE ${xverse_xcom_sanitize_link})
  endif()
endfunction()

xverse_xcom_assert_runtime_warning_policy()
xverse_xcom_runtime_sanitizers()
```

Every existing `xverse_xcom_apply_warnings(<target>)` call in the subtree file is replaced by
`xverse_xcom_apply_runtime_rules(<target>)`. This is a mechanical, uniform substitution: it changes no target
name, source list, link library, include directory, or registered test, and it guarantees that no runtime or
test target escapes the warning or (optional) sanitizer rules. When the selection is empty the substitution
is behaviorally identical to the baseline.

## 5. Target inventory and per-target configuration

The baseline target definitions are preserved verbatim except for the helper substitution. The inventory:

| Runtime target | Kind | Sources (unchanged) | Public link libraries (unchanged) |
| --- | --- | --- | --- |
| `xverse_xcom_core_types` | STATIC | `src/contract.cpp`, `src/diagnostic.cpp`, `src/item.cpp`, `src/value.cpp` | — |
| `xverse_xcom_observation` | STATIC | `src/observation.cpp` | `xverse::xcom_core_types` |
| `xverse_xcom_endpoint_route_lifecycle` | STATIC | `src/endpoint_route_lifecycle.cpp` | `xverse::xcom_core_types` |
| `xverse_xcom_provider_loopback` | STATIC | `src/provider.cpp`, `src/loopback_provider.cpp` | lifecycle, observation |
| `xverse_xcom_validation_session` | STATIC | `src/validation_session.cpp` | — |
| `xverse_xcom_activation_plan` | STATIC | `src/activation_plan.cpp` | `nlohmann_json::nlohmann_json` |

Test-executable targets under `if(BUILD_TESTING)` (core types, lifecycle, observation, provider loopback,
activation-plan decoder/T020, validation session) keep their names, sources, and labels. The baseline
`xverse_xcom_provider_loopback` compile definition
`XVERSE_XCOM_ENABLE_DISABLED_OBSERVATION_BENCHMARK=1` is unchanged.

## 6. Build-contract evidence and verifier (`T12-CMP-CTEST`, `T12-CMP-CONTRACT`)

### 6.1 Generated evidence

Beneath the build tree, at configure time, the effective policy is written to
`${CMAKE_CURRENT_BINARY_DIR}/xcom-runtime-contract.json` (fields: `schema_version`, `task_id`,
`cxx_standard`, `cxx_extensions`, `warning_options`, `sanitizers`, `runtime_targets`, `build_testing`). The
root helper `_xverse_xcom_json_string` is reused to JSON-escape the values; the file is produced with
`file(GENERATE)` so the content is stable for a given configuration.

### 6.2 Verifier script

A second generated file `${CMAKE_CURRENT_BINARY_DIR}/verify-xcom-runtime-contract.cmake` is a
`cmake -P` script that reads the JSON in its own directory (`CMAKE_CURRENT_LIST_DIR`) and fails with a
specific message when any invariant is violated:

- `"cxx_standard": 20`;
- `"cxx_extensions": "OFF"`;
- `"warning_options"` contains an error-promoting option (`-Werror`, `-Werror=…`, or `/WX`);
- `"warning_options"` contains `-Wall`, `-Wextra`, and `-Wpedantic`;
- `"runtime_targets"` equals the expected semicolon-separated inventory;
- `"build_testing": "ON"`;
- `"sanitizers"` is either empty or one of the supported selections.

### 6.3 CTest target

```cmake
add_test(
  NAME xcom_build_contract
  COMMAND ${CMAKE_COMMAND} -P "${CMAKE_CURRENT_BINARY_DIR}/verify-xcom-runtime-contract.cmake"
)
set_tests_properties(xcom_build_contract PROPERTIES LABELS "t012")
```

The test is added inside `if(BUILD_TESTING)`, is offline, single-threaded, and deterministic, and introduces
no new repository source path. It is additive: the baseline 247 registered tests become 248.

## 7. Failure semantics

| Condition | Class | Outcome |
| --- | --- | --- |
| warning target absent | configure error | `FATAL_ERROR` "requires the inherited xverse::xcom_warnings target"; no target generated |
| warning options empty | configure error | `FATAL_ERROR`; no target generated |
| warning options lack an error-promoting flag | configure error | `FATAL_ERROR`; no target generated |
| unknown sanitizer entry | configure error | `FATAL_ERROR` naming the entry; no target generated |
| `address` + `thread` selected | configure error | `FATAL_ERROR` naming the conflict |
| policy mismatch at test time | CTest failure | `xcom_build_contract` exits nonzero naming the invariant |
| missing admitted input | configure error | inherited `XComOfflineDependencies` `FATAL_ERROR` (T011 behaviour, unchanged) |
| non-Ninja generator / `BUILD_TESTING=OFF` | configure error | inherited root `FATAL_ERROR` (unchanged) |

No failure path emits a target set, evidence file, or test result that claims a weakened policy was accepted.

## 8. Boundedness and side effects

| Resource | Bound |
| --- | --- |
| Inputs | read-only; only the T011 admitted inputs and the repository |
| New mandatory inputs | none |
| Network | none; no resolver, registry, package manager, or FetchContent |
| Threads | none added; CMake configure is single-threaded (build/test parallelism is the caller's) |
| Subprocesses | only the inherited admission preflight (120 s timeout) |
| Writes | generated evidence and build trees beneath the build directory only |
| CTest additions | exactly one test (`xcom_build_contract`) and no new label family |

## 9. Public-safety design

Committed files record target names, compiler-flag identities, sanitizer names, and diagnostic messages
only. They must not contain host prefixes, package-manifest paths, test-toolchain paths, temporary
directories, credentials, private addresses, unrestricted payloads, proprietary source, or sensitive
deployment values. Generated contract evidence stays beneath the build directory and is not committed; the
T012 work products reference environment-variable **names**, not their values.

## 10. Error and edge-case handling

| Case | Handling |
| --- | --- |
| Sanitizer selected but unsupported by the compiler | configure succeeds with the requested flags; the resulting compile failure is reported by the compiler. Executed sanitizer evidence is T035's, and no sanitizer is falsely claimed executed. |
| Duplicate sanitizer entry | de-duplicated; no error |
| Sanitizer selection with whitespace | entries are matched literally; an entry that is not `address`/`thread`/`undefined` fails closed |
| Reconfigure with a different selection | the generated evidence reflects the current configuration; stale evidence is not reused |
| Target list drift (a later task adds a target) | the declared inventory and the verifier are updated by the owning task; an unlisted target does not satisfy INV-04/INV-12 until declared |
| `BUILD_TESTING=OFF` | configuration already fails at the root; the subtree never registers tests |

## 11. Requirement traceability

| Design section | Requirements |
| --- | --- |
| §4.1 inventory | T012-STK-001, T012-SR-001 |
| §4.2 warning assertion | T012-STK-002, T012-SR-002, T012-SR-003 |
| §4.3 sanitizer selection | T012-STK-003, T012-SR-004 |
| §4.4 uniform application | T012-SR-002, T012-SR-005 |
| §5 inventory/configuration | T012-SR-001, T012-SR-010 |
| §6 evidence/verifier/CTest | T012-STK-004, T012-SR-006, T012-SR-007 |
| §7 failure semantics | T012-STK-002, T012-SR-003, T012-SR-004 |
| §8 boundedness | T012-SR-008 |
| §9 public safety | T012-SR-009 |
| §10 edge cases | T012-SR-005, T012-SR-007 |
| `T12-WP` work products | T012-SR-011, T012-SR-012 |
