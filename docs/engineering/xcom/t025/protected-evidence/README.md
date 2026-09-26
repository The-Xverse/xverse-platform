# Protected T025 candidate evidence

The [successor evidence](successor-evidence.md) is the current exact-revision record. The
measure table below retains the first integration snapshot and its diagnostic attempts.

**Inspected source revision:** unreferenced review snapshot
`92dde5ff9971867b30c478a3f43b721745dd3edb`, parent
`d244eeb3aa26f1b27d23d75fabc750380405269f`. The detached review checkout was clean before
and after verification. No official branch ref was moved by this snapshot. These results bind to
that exact source revision; the eventual evidence-bearing commit must retain the same source bytes.

## Environment and commands

Ubuntu 22.04 host; GCC 11.4.0; CMake 3.22.1; Ninja 1.10.1; Python 3.13.13;
Doxygen 1.9.1. The twelve-package X-COM lock was admitted from an external manifest and clean
extracted prefix. The separate three-package GTest 1.11.0-3 prefix passed
`python3 scripts/check_xcom_t025_test_dependencies.py PACKAGE_DIR TEST_PREFIX`.
`XVERSE_XCOM_TOOLCHAIN`, `XVERSE_XCOM_PACKAGE_MANIFEST`, and
`XVERSE_XCOM_T025_TEST_TOOLCHAIN` named those exact external inputs. `PATH`, `LD_LIBRARY_PATH`,
`PKG_CONFIG_SYSROOT_DIR`, `PKG_CONFIG_PATH`, and `CMAKE_PREFIX_PATH` selected the admitted base
prefix as documented in `docs/engineering/xcom/build-environment.md`.

The official predecessor gate used the legacy validator's `SESN_CANDIDATE_REVISION` environment
name solely to bind its clean detached clone to the revision above. SESN itself was not invoked.

| Measure | Exact command shape and result | Log SHA-256 |
| --- | --- | --- |
| GTest admission | `python3 scripts/check_xcom_t025_test_dependencies.py PACKAGE_DIR TEST_PREFIX`; exit 0 | [`gtest-admission.log`](gtest-admission.log) `291dfc832767c8b8c21097c7fa32d6d02e1edff31e0b776ae601844f5dfdc47f` |
| Official configure | `cmake -S . -B BUILD -G Ninja -DCMAKE_BUILD_TYPE=Debug`; exit 0 | [`t025-configure.log`](t025-configure.log) `ac544a6a3807ee0f7b317e16a38dd5aaa2a86e1e7a627efda299fe5aca161e56` |
| T025 build | `cmake --build BUILD --target xverse_xcom_validation_unit_tests xverse_xcom_validation_integration_tests xverse_xcom_validation_validation_tests -j 4`; exit 0 | [`t025-build.log`](t025-build.log) `b70c83292d4d202f5de853e0b8dff049bfe35d5be6e5d343fc62ac35b9a4e706` |
| T025 tests | `ctest --test-dir BUILD -L t025 -j 4 --output-on-failure`; exit 0, 144/144 passed | [`t025-ctest.log`](t025-ctest.log) `c752d7f28313d24c520115d815a48c23b292c3a60a473802480ef1a32e3cdd83` |
| Protected regression | `python3 scripts/validate_xcom_observation.py --all`; exit 0, including all three accepted predecessor `--all` gates | [`predecessor-observation-all.log`](predecessor-observation-all.log) `23576b08181c86af93fe1fca9d314368e54b6c7c55f53a8b9769efbe73d221a2` |
| ASan/UBSan | Configure/build with `-fsanitize=address,undefined -fno-omit-frame-pointer`; `ASAN_OPTIONS=detect_leaks=1 UBSAN_OPTIONS=halt_on_error=1 ctest --test-dir BUILD -L t025 -j 1 --output-on-failure`; exit 0, 144/144 passed | [`asan-ctest.log`](asan-ctest.log) `3cbd09a94e7664e8d812e1f218c38e7891e7c5a6a317bd709cab0f35e307745a` |
| ThreadSanitizer first attempt | Configure passed; build failed during GTest discovery because the executable reported `FATAL: ThreadSanitizer: unexpected memory mapping`. | [`tsan-build.log`](tsan-build.log) `9c5429eca3d722e3d05458d6bccd07336791d0ff165a41fd7b8d808378720425` |
| ThreadSanitizer rerun | Configure with `CMAKE_GTEST_DISCOVER_TESTS_DISCOVERY_MODE=PRE_TEST`; build; `TSAN_OPTIONS=halt_on_error=1 setarch x86_64 -R ctest --test-dir BUILD -L t025 -j 1 --output-on-failure`; exit 0, 144/144 passed | [`tsan-pretest-ctest.log`](tsan-pretest-ctest.log) `562a21e5d5334df7da9d753bbc55e0fe0d62d45048e1e42798972d12a44848b0` |

The corresponding ASan and TSan configure/build logs are retained in this directory. The TSan
rerun resolves the host discovery failure for this revision; the first failed attempt remains
visible. CodeQL evidence is pending. The exact copied Fabro-run and terminal-review hashes are in
[`transfer-verification.json`](transfer-verification.json).
