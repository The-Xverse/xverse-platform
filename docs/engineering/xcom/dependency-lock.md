# X-COM offline dependency lock

Status: prototype-only build/dependency foundation for capability 007, slice 1. This lock admits no X-COM runtime, provider, observation, stimulation, gateway, compatibility, or production behavior.

The package binaries are retained outside the repository beside the manifest named by `XVERSE_XCOM_PACKAGE_MANIFEST`. They must not be copied into Git. Admission compares every byte size and SHA-256 below with both the manifest record and the external package file; it also checks Debian package name, version, and source metadata without installing the package.

## Exact Jammy package records and retrieval coordinates

The retrieval coordinates identify public Ubuntu 22.04 LTS (Jammy) pool objects for reconstruction outside an admission run. They are not network inputs to the checker. The three epoch-bearing LLVM objects omit the `1:` epoch in the Ubuntu pool basename; they must be retained beside the manifest under the `%3a` filenames shown in the first column. All other public object basenames and retained filenames are identical.

| Retained package file | Bytes | SHA-256 | Debian package / exact version | Source | License | Public Ubuntu Jammy pool object |
|---|---:|---|---|---|---|---|
| `clang-tidy-14_1%3a14.0.0-1ubuntu1.1_amd64.deb` | 1625658 | `c59bd0f8089e57ae3b0aed276a28b72e674d756c880706d192dc10ad328eafe1` | `clang-tidy-14` `1:14.0.0-1ubuntu1.1` | `llvm-toolchain-14` | Apache-2.0 WITH LLVM-exception | `https://security.ubuntu.com/ubuntu/pool/universe/l/llvm-toolchain-14/clang-tidy-14_14.0.0-1ubuntu1.1_amd64.deb` |
| `clang-tidy_1%3a14.0-55~exp2_amd64.deb` | 3456 | `18a6c1c776bf0a10c18645d007fa4f5028861ec82c3c02eb225d4a437af099ef` | `clang-tidy` `1:14.0-55~exp2` | `llvm-defaults (0.55~exp2)` | GPL-2.0-or-later | `https://archive.ubuntu.com/ubuntu/pool/universe/l/llvm-defaults/clang-tidy_14.0-55~exp2_amd64.deb` |
| `clang-tools-14_1%3a14.0.0-1ubuntu1.1_amd64.deb` | 6961518 | `8eccc1c4c57e4eb225b6e4fa29a72c829caf73bc54f7985b844e9487c3ad843d` | `clang-tools-14` `1:14.0.0-1ubuntu1.1` | `llvm-toolchain-14` | Apache-2.0 WITH LLVM-exception | `https://security.ubuntu.com/ubuntu/pool/universe/l/llvm-toolchain-14/clang-tools-14_14.0.0-1ubuntu1.1_amd64.deb` |
| `libgrpc++-dev_1.30.2-3build6_amd64.deb` | 564346 | `067752d39cb0bcbad10cf71d8a22d4e155e299c9f31187ceb4c400b56dd624c6` | `libgrpc++-dev` `1.30.2-3build6` | `grpc` | Apache-2.0 | `https://archive.ubuntu.com/ubuntu/pool/universe/g/grpc/libgrpc++-dev_1.30.2-3build6_amd64.deb` |
| `libgrpc++1_1.30.2-3build6_amd64.deb` | 402166 | `574640b4cb72081a676889fb38469c4abd27b54c81540ee23a1f6b9cac0974eb` | `libgrpc++1` `1.30.2-3build6` | `grpc` | Apache-2.0 | `https://archive.ubuntu.com/ubuntu/pool/universe/g/grpc/libgrpc++1_1.30.2-3build6_amd64.deb` |
| `libgrpc-dev_1.30.2-3build6_amd64.deb` | 1065926 | `1c1c8a1b207a5bb10c37622e52288ec4e830f113cf735bc30544855587eb08b0` | `libgrpc-dev` `1.30.2-3build6` | `grpc` | Apache-2.0 | `https://archive.ubuntu.com/ubuntu/pool/universe/g/grpc/libgrpc-dev_1.30.2-3build6_amd64.deb` |
| `libgrpc10_1.30.2-3build6_amd64.deb` | 1469878 | `10c74dcd0d0eaeb252b4fcc286cd50325a88469d46d9706f853393809b2a1ee8` | `libgrpc10` `1.30.2-3build6` | `grpc` | Apache-2.0 | `https://archive.ubuntu.com/ubuntu/pool/universe/g/grpc/libgrpc10_1.30.2-3build6_amd64.deb` |
| `libprotobuf-dev_3.12.4-1ubuntu7.22.04.6_amd64.deb` | 1346664 | `1ac0147f49bc089cd57c8aabb78617211d950b3ba0df28ecd0f65e0515a5884a` | `libprotobuf-dev` `3.12.4-1ubuntu7.22.04.6` | `protobuf` | BSD-3-Clause | `https://security.ubuntu.com/ubuntu/pool/main/p/protobuf/libprotobuf-dev_3.12.4-1ubuntu7.22.04.6_amd64.deb` |
| `libprotoc23_3.12.4-1ubuntu7.22.04.6_amd64.deb` | 662358 | `470ba9e90c9aeb788abf819c71f15a69605c47e6f510d56fba723e790365b6f1` | `libprotoc23` `3.12.4-1ubuntu7.22.04.6` | `protobuf` | BSD-3-Clause | `https://security.ubuntu.com/ubuntu/pool/main/p/protobuf/libprotoc23_3.12.4-1ubuntu7.22.04.6_amd64.deb` |
| `nlohmann-json3-dev_3.10.5-2_all.deb` | 166536 | `0c0ab9e6baf27a930990729b3ad7123b12dfd353e7bac7bf6c77aa03eab5c639` | `nlohmann-json3-dev` `3.10.5-2` | `nlohmann-json3` | MIT | `https://archive.ubuntu.com/ubuntu/pool/universe/n/nlohmann-json3/nlohmann-json3-dev_3.10.5-2_all.deb` |
| `protobuf-compiler-grpc_1.30.2-3build6_amd64.deb` | 185228 | `79debaed17ff25444a9c450b4b342e3d7565e80c062da2356b42ceb73e305331` | `protobuf-compiler-grpc` `1.30.2-3build6` | `grpc` | Apache-2.0 | `https://archive.ubuntu.com/ubuntu/pool/universe/g/grpc/protobuf-compiler-grpc_1.30.2-3build6_amd64.deb` |
| `protobuf-compiler_3.12.4-1ubuntu7.22.04.6_amd64.deb` | 29196 | `a124cc30fadf8e83f86fd7e1b9c776befd336d092bb81f95de1dc39d79b61ce7` | `protobuf-compiler` `3.12.4-1ubuntu7.22.04.6` | `protobuf` | BSD-3-Clause | `https://security.ubuntu.com/ubuntu/pool/universe/p/protobuf/protobuf-compiler_3.12.4-1ubuntu7.22.04.6_amd64.deb` |

The license column identifies the primary upstream binary license and the `clang-tidy` metapackage's package license. Debian copyright records may also identify licenses for packaging and bundled third-party material; those records remain authoritative and must accompany any redistribution review. This document is an engineering admission record, not legal advice.

## Admitted component and generated-code provenance

| Component | Admitted version | Evidence and role |
|---|---|---|
| nlohmann/json | 3.10.5 (`3.10.5-2`) | Header macros and `nlohmann_json.pc`; header-only JSON dependency. |
| Protocol Buffers | 3.12.4 (`3.12.4-1ubuntu7.22.04.6`) | Header macro, `protobuf.pc`, libraries, and `protoc --version`. Every future generated-code output must record `protobuf-compiler_3.12.4-1ubuntu7.22.04.6_amd64.deb` and SHA-256 `a124cc30fadf8e83f86fd7e1b9c776befd336d092bb81f95de1dc39d79b61ce7`, plus the input schema identity and generation command. |
| gRPC | 1.30.2 (`1.30.2-3build6`) | `grpc++.pc`, headers, libraries, and `grpc_cpp_plugin`. Every future gRPC C++ generated-code output must record `protobuf-compiler-grpc_1.30.2-3build6_amd64.deb` and SHA-256 `79debaed17ff25444a9c450b4b342e3d7565e80c062da2356b42ceb73e305331`, plus the input schema identity and generation command. |
| clang-tidy / LLVM | 14.0.0 (`1:14.0.0-1ubuntu1.1`) | `clang-tidy --version`; static-analysis tool only. |

`grpc_cpp_plugin` has no supported version flag in this admitted package. Its version and provenance therefore come from the separately hash-verified `protobuf-compiler-grpc_1.30.2-3build6_amd64.deb` control metadata and extracted payload binding, not from an inferred executable response.

## Archive identity versus extracted payload identity

Archive admission and installed-prefix admission are distinct checks:

1. The manifest must contain exactly the twelve retained filenames, byte sizes, and SHA-256 values above.
2. Each sibling `.deb` file is checked against its manifest record and this compiled-in lock; `dpkg-deb -f` then verifies package, version, and source metadata.
3. The checker extracts the hash-verified archives with `dpkg-deb -x` into a disposable reference tree. It compares every required executable, header, library, pkg-config file, file type, file content, symlink text, and recursively reached symlink target with `XVERSE_XCOM_TOOLCHAIN`.

An archive hash proves the retained `.deb` identity only. It does not prove that an independently provisioned prefix still contains that payload; the extracted-payload comparison supplies that second binding. Neither check validates unlisted transitive host libraries.

No ambient package manager, package registry, network endpoint, or “latest” constraint participates in admission. Public retrieval is a separate, controlled external reconstruction step; the admission and build commands remain offline and never install packages.
