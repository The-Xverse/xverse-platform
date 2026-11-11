# Jammy c-ares retrieval and native-build documentation maintenance

Scope: user-requested maintenance successor to
`12615d402ba16cde3cd48c55b70aca464ea90261`, for the independent Studio reproduction.
This is a reviewed development candidate, not a new platform acceptance or main
integration. The original commit and its recorded evidence remain unchanged.

## Read-only findings and repair

The teammate reported that the retained `.3` c-ares archive is no longer available
in the Jammy archive, while `.4` passes their complete native build. Inspection
also found twelve-package prose and reconstruction code inconsistent with the
already enforced thirteen-package lock, and a missing T025 prefix prerequisite.
These findings were recorded before changing the isolated candidate.

The repair changes only dependency admission metadata and documentation:

- Admit `libc-ares2_1.18.1-1ubuntu0.22.04.4_amd64.deb`, 45180 bytes, SHA-256
  `f06ba6fa152f36efd393943dc7e80e229cac041b241e6281d20d60ee7dfc14c2`.
- Update both the package row and gRPC/c-ares version note in the lock document.
- Make reconstruction and prose consistently require thirteen package archives
  plus the JSON manifest. Remove c-ares from the examples of unlocked libraries.
- Explain the separately admitted T025 GTest/GMock prefix before preflight and
  root CMake configuration, which requires `BUILD_TESTING=ON`.

No `src/xverse`, `cmake`, root `CMakeLists.txt`, schema or protocol source changes.
The `.4` artifact was independently downloaded from the declared Ubuntu archive,
then size, hash and Debian package/version/architecture/source were verified.
It retains the admitted `libcares.so.2` → `libcares.so.2.5.1` file relationship.
Admission remains exact and fail-closed; no package-manager install, floating
resolver, relaxed payload check or changed host ABI claim is introduced.

## Verification and review

These checks use isolated directories and an enforced unprivileged user/network
namespace; no simulator, VM or graphical/GPU workload is started:

- The original reconstruction code rejects the actual thirteen-record manifest;
  the updated documentation's literal shell block reconstructs a new prefix.
- `--self-test`: 39 tests pass.
- Missing T025 prefix reproduces `XCOM-BLD-E061`; with the independently verified
  T025 prefix, `--verify-toolchain` and `--all` both emit `XCOM-BLD-I000`.
- Full root CMake configure passes with Ninja, Release and `BUILD_TESTING=ON`;
  `xverse_xcom_provider_loopback` and its four static libraries build with `-j2`.
- Platform library source (`src/`) and CMake trees compare unchanged against the base above.

The affected requirement allocation is the existing exact dependency/payload
admission and documented build envelope (`XCOM-BLD-001`, `XCOM-BLD-002` and the
documentation checks in `build-environment.md`). No requirement or task ID is
regenerated. A separate read-only diff/review checks that package size/hash/version
agree, all thirteen-package mentions are consistent, and no native behavior or
permission boundary is changed. The Studio handoff records the successor pin,
installed-consumer/native-bridge checks and cleanup separately; old full-demo
evidence is not promoted to this candidate.

Raw logs and package archives stay outside Git. Public source identities and
verification results are retained in the Studio repository's dated dependency
maintenance evidence. Model recommendation for this provenance/admission review:
Terra with high reasoning; this is a task judgment, not a measured cost benchmark.
