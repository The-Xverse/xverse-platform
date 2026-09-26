# T025 protected successor evidence

**Exact reviewed source revision:** `25c650830c865c0ae0170a8eed53da7e8f076d8f`.
**Parent baseline:** `d244eeb3aa26f1b27d23d75fabc750380405269f`.
The detached checkout was clean before and after these commands. Its production and test source
bytes are identical to the earlier `92dde5ff9971867b30c478a3f43b721745dd3edb` snapshot;
the successor changes repository workflow and evidence documentation. The logs below were generated
on the successor itself. The evidence-bearing transfer tree may add these logs without changing
the inspected source files.

The host used Ubuntu 22.04, GCC 11.4.0, CMake 3.22.1, Ninja 1.10.1, Python 3.13.13, and Doxygen
1.9.1. The base dependency prefix was reconstructed from the twelve exact archives in the repository
lock. The separate GTest 1.11.0-3 prefix was reconstructed from the three exact archives in
[`../test-dependency-admission.md`](../test-dependency-admission.md). These prefixes, the manifest,
`PATH`, `LD_LIBRARY_PATH`, `PKG_CONFIG_SYSROOT_DIR`, `PKG_CONFIG_PATH`, and `CMAKE_PREFIX_PATH`
were set for the commands below. Their machine-local paths appear in the raw logs; no dependency
package was installed or resolved during the checks.

| Measure | Command and result | SHA-256 log |
| --- | --- | --- |
| GTest admission | `python3 scripts/check_xcom_t025_test_dependencies.py PACKAGE_DIR TEST_PREFIX`; exit 0 | [`successor-gtest-admission.log`](successor-gtest-admission.log) `291dfc832767c8b8c21097c7fa32d6d02e1edff31e0b776ae601844f5dfdc47f` |
| Normal T025 tests | `ctest --test-dir CODEQL_BUILD -L t025 -j 4 --output-on-failure`; exit 0, 144/144 | [`successor-t025-ctest.log`](successor-t025-ctest.log) `578ada35857cdbe76e1db3a97457e1c97f1550f4d33092c3aa3520179449e3d1` |
| ASan/UBSan | Configure/build with `-fsanitize=address,undefined -fno-omit-frame-pointer`; `ASAN_OPTIONS=detect_leaks=1 UBSAN_OPTIONS=halt_on_error=1 ctest --test-dir BUILD -L t025 -j 1 --output-on-failure`; exit 0, 144/144 | [`successor-asan-ctest.log`](successor-asan-ctest.log) `840949cf7cade8d8269cbb90684bed419956e26724b6f681464a684ea88b8d82` |
| ThreadSanitizer | Configure/build with `-fsanitize=thread -fno-omit-frame-pointer` and GTest discovery `PRE_TEST`; `TSAN_OPTIONS=halt_on_error=1 setarch x86_64 -R ctest --test-dir BUILD -L t025 -j 1 --output-on-failure`; exit 0, 144/144 | [`successor-tsan-ctest.log`](successor-tsan-ctest.log) `ca1b5c6cd50c8c24cd6ffe97814f03fecba2e2db5d4dee679246267e52c6bd7f` |
| Official predecessor regression | `SESN_CANDIDATE_REVISION=25c650830c865c0ae0170a8eed53da7e8f076d8f python3 scripts/validate_xcom_observation.py --all`; exit 0, including core-types, endpoint/route, and provider-loopback `--all` | [`successor-predecessor-observation-all.log`](successor-predecessor-observation-all.log) `83239fe9de7cdbdfb0326de5e52c0cc3e77b62fa58ba685ca0c5a0d365bfc872` |

The predecessor validator still names its exact-revision input `SESN_CANDIDATE_REVISION`; this is
legacy parameter spelling only. No SESN service was invoked. The full configure/build logs for
sanitizers and CodeQL are retained in this directory.

## CodeQL

Manually downloaded the official `codeql-bundle-v2.27.1` Linux x64 bundle from
`github/codeql-action` and checked the published archive SHA-256
`1ec99cfa9420f04c2330784b4ddb8363a0dd67c3e4471cd93963c50e6c433717` before extracting
the C++ CLI, extractor, and compatible query packs into an external cache. CodeQL CLI version 2.27.1;
`codeql/cpp-all` 12.1.1, `codeql/cpp-queries` 1.9.0, and `codeql/suite-helpers` 1.0.58.

`codeql database create DB --language=cpp --source-root=CHECKOUT --command='cmake --build BUILD
--target xverse_xcom_validation_unit_tests xverse_xcom_validation_integration_tests
xverse_xcom_validation_validation_tests -j 4' --threads=2 --ram=4096` exited 0 on this exact
revision. `codeql database analyze DB codeql/cpp-queries:codeql-suites/cpp-security-and-quality.qls
--format=sarifv2.1.0 --output=RESULT --threads=2 --ram=4096` exited 0. The suite reported two
`cpp/large-parameter` recommendations and no security alert. Both are individually dispositioned
in [`codeql-disposition.md`](codeql-disposition.md).

| Artifact | SHA-256 |
| --- | --- |
| [`codeql-create.log`](codeql-create.log) | `07e94f003c527628aac330cfad577f6c6b085a4e34abeb27f225bc34a65a089b` |
| [`codeql-analyze.log`](codeql-analyze.log) | `f949d2c9f90e2dfac26bd389e321876edab852ead23c93726459fdc2962f41bf` |
| [`codeql-results.sarif`](codeql-results.sarif) | `e5346c4f64e73f832c4324465043faeb23b0c56482c16cc0a979cd020bf518ad` |

The complete Fabro-run transfer and terminal-review file hashes remain in
[`transfer-verification.json`](transfer-verification.json). The earlier failed TSan discovery log
remains in this directory as historical diagnostic evidence, with the successful successor run
shown above.
