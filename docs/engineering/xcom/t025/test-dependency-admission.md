# T025 offline test dependency admission

The T025 GTest targets use a separate, extraction-only prefix. The existing twelve-package X-COM
dependency lock and its prefix remain unchanged; adding files to that prefix fails its payload check.
The test-only prefix contains exactly these Ubuntu Jammy packages, retained outside Git:

| Package file | Bytes | SHA-256 |
| --- | ---: | --- |
| `googletest_1.11.0-3_all.deb` | 541360 | `7f665f45da5c1748ba85b7f7f1ff16e76ab9e6f61f2f09d8c4eb898d529c1b57` |
| `libgmock-dev_1.11.0-3_amd64.deb` | 127506 | `c34ed719d0fbb1cbcccddc3e0d119fb6b291719774f4f1465b5fe45453564f0c` |
| `libgtest-dev_1.11.0-3_amd64.deb` | 250406 | `43a86daecd536dfc36697053cf2e3351abe4c075f4963607af257faf38893317` |

Retrieve these exact pool objects from `https://archive.ubuntu.com/ubuntu/pool/universe/g/googletest/`
in a controlled online staging step. Verify their sizes and hashes before offline use. Extract each
with `dpkg-deb -x PACKAGE NEW_TEST_PREFIX`; do not install it or run package scripts. Then run:

```sh
python3 scripts/check_xcom_t025_test_dependencies.py PACKAGE_DIRECTORY NEW_TEST_PREFIX
export XVERSE_XCOM_T025_TEST_TOOLCHAIN=NEW_TEST_PREFIX
```

The checker verifies archive identity, package name/version, and every extracted path and byte against
the prefix. The T025 CMake targets resolve `GTestConfig.cmake` only from this prefix. The test prefix
is a test-only build input; it is not an X-COM runtime dependency. The C++ compiler, CMake, Ninja,
Python, and `dpkg-deb` retain their host-envelope status in [build-environment.md](../build-environment.md).
