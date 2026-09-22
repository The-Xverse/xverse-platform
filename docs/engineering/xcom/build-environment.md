# X-COM build environment

This is a prototype-only build and dependency-admission environment for capability 007, slice 1. It provides no X-COM runtime behavior and makes no compatibility, timing, safety, production-readiness, or deployment claim.

## Explicit inputs and host envelope

The caller must set these two authoritative locations to absolute paths:

- `XVERSE_XCOM_TOOLCHAIN`: the isolated, already-provisioned dependency prefix.
- `XVERSE_XCOM_PACKAGE_MANIFEST`: the twelve-entry JSON manifest. The twelve retained package files must be siblings of this manifest outside Git.

The host must provide Python `python3` 3.11 or newer, CMake 3.22 or newer, Ninja 1.10 or newer, a C++20 compiler available as `c++`, and `dpkg-deb`. The compiler must accept `-Wall -Wextra -Wpedantic -Werror`; CMake rejects non-Ninja generators, disabled testing, and unsupported warning policies. These host tools are build-envelope prerequisites, not members of the twelve-package dependency lock. In particular, Ubuntu Jammy's default Python is not assumed to satisfy the Python 3.11 minimum.

The isolated prefix must provide nlohmann/json 3.10.5, Protocol Buffers 3.12.4, gRPC 1.30.2, clang-tidy 14.0.0, `protoc`, and `grpc_cpp_plugin`, with the headers, libraries, pkg-config metadata, and generated-code provenance described in [dependency-lock.md](dependency-lock.md).

## Deterministic offline prefix reconstruction

Retrieval is deliberately separate from admission. In a controlled online staging process, obtain the twelve public objects listed in [dependency-lock.md](dependency-lock.md), retain them under the exact manifest filenames, verify their recorded sizes and SHA-256 values, and then transfer the manifest and archives into the offline environment. Do not run these steps until all thirteen files are already local.

The following provisions a new prefix by extraction only. It does not invoke APT, resolve dependencies, contact a network endpoint, install a system package, or execute package maintainer scripts. `XVERSE_XCOM_TOOLCHAIN` must name a new path so stale or untracked payloads cannot survive reconstruction.

```sh
set -eu
: "${XVERSE_XCOM_TOOLCHAIN:?set an absolute path for a new isolated prefix}"
: "${XVERSE_XCOM_PACKAGE_MANIFEST:?set an absolute path to package-manifest.json}"

case "$XVERSE_XCOM_TOOLCHAIN" in /*) ;; *) exit 64 ;; esac
case "$XVERSE_XCOM_PACKAGE_MANIFEST" in /*) ;; *) exit 64 ;; esac
test -f "$XVERSE_XCOM_PACKAGE_MANIFEST"
test ! -e "$XVERSE_XCOM_TOOLCHAIN"
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'
command -v dpkg-deb >/dev/null

package_directory=$(dirname -- "$XVERSE_XCOM_PACKAGE_MANIFEST")
package_list=$(mktemp)
trap 'rm -f -- "$package_list"' EXIT HUP INT TERM

python3 - "$XVERSE_XCOM_PACKAGE_MANIFEST" >"$package_list" <<'PY'
import hashlib
import json
import pathlib
import sys

manifest_path = pathlib.Path(sys.argv[1])
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
if not isinstance(manifest, list) or len(manifest) != 12:
    raise SystemExit("manifest must contain exactly twelve records")
if any(not isinstance(record, dict) for record in manifest):
    raise SystemExit("every manifest record must be an object")
for record in manifest:
    if set(record) != {"file", "sha256", "size"}:
        raise SystemExit("manifest record fields differ from the accepted schema")
    if not isinstance(record["file"], str):
        raise SystemExit("manifest filename must be a string")
seen = set()
for record in sorted(manifest, key=lambda item: item["file"]):
    name = record["file"]
    digest = record["sha256"]
    size = record["size"]
    if (
        not isinstance(name, str)
        or pathlib.PurePath(name).name != name
        or not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
        or type(size) is not int
        or size <= 0
    ):
        raise SystemExit("manifest record is malformed")
    if name in seen:
        raise SystemExit("manifest contains a duplicate filename")
    seen.add(name)
    package = manifest_path.parent / name
    if not package.is_file() or package.stat().st_size != size:
        raise SystemExit(f"package size differs: {name}")
    observed = hashlib.sha256(package.read_bytes()).hexdigest()
    if observed != digest:
        raise SystemExit(f"package SHA-256 differs: {name}")
    print(name)
PY

umask 022
mkdir -m 0755 -- "$XVERSE_XCOM_TOOLCHAIN"
while read -r package_file; do
    dpkg-deb -x "$package_directory/$package_file" "$XVERSE_XCOM_TOOLCHAIN"
done <"$package_list"
```

The manifest and the repository lock remain authoritative for exact byte sizes; the final preflight rechecks both sizes and hashes, Debian control metadata, and the required extracted payload. The reconstruction loop is ordered by retained filename and produces no package-manager database. If any step fails, discard that newly created prefix and restart with a different new path; do not treat it as admitted.

## Environment for admission and builds

Set a clean shell explicitly. The first two values are authoritative checker inputs. The remaining variables make generated-code tools, shared libraries, pkg-config metadata, and CMake prefix lookup prefer the same extracted prefix during manual engineering work:

```sh
export XVERSE_XCOM_TOOLCHAIN=/absolute/path/to/new-xcom-prefix
export XVERSE_XCOM_PACKAGE_MANIFEST=/absolute/path/to/package-manifest.json
export PATH="$XVERSE_XCOM_TOOLCHAIN/usr/bin:$PATH"
export LD_LIBRARY_PATH="$XVERSE_XCOM_TOOLCHAIN/usr/lib/x86_64-linux-gnu"
export PKG_CONFIG_SYSROOT_DIR="$XVERSE_XCOM_TOOLCHAIN"
export PKG_CONFIG_PATH="$XVERSE_XCOM_TOOLCHAIN/usr/lib/x86_64-linux-gnu/pkgconfig:$XVERSE_XCOM_TOOLCHAIN/usr/lib/pkgconfig"
export CMAKE_PREFIX_PATH="$XVERSE_XCOM_TOOLCHAIN/usr"
```

Do not append ambient library or pkg-config directories and then describe the result as hermetic. The checker resolves its admitted executables, headers, libraries, and metadata directly beneath `XVERSE_XCOM_TOOLCHAIN`; CMake uses explicit imported targets after preflight. `PATH` still supplies the host prerequisites `python3`, `cmake`, `ninja`, `c++`, and `dpkg-deb`, whose selected identities are probed.

The twelve-package set does not lock all shared-library dependencies of its executables or gRPC's base-system transitive libraries, including the C/C++ runtime, LLVM/Clang runtime, OpenSSL, zlib, c-ares, Abseil, and the Protocol Buffers runtime package. Consequently, this envelope is limited to Linux x86-64 with an ABI-compatible Ubuntu Jammy-derived host matching the admitted packages. `LD_LIBRARY_PATH` selects admitted shared objects when present, but it does not make absent transitive objects part of the lock. The compile-only imported targets are controlled top-level locators, not proof of a hermetic runtime link. A later authorized slice must admit transitive artifacts or define and verify a pinned base-system ABI before compiling or executing runtime targets.

## Offline admission and build-policy validation

From the repository root, first prove the host Python requirement, then run the SESN verification measures with network access absent:

```sh
python3 -c 'import sys; assert sys.version_info >= (3, 11), sys.version'
python3 scripts/xcom_dependency_preflight.py --self-test
python3 scripts/xcom_dependency_preflight.py --verify-toolchain
python3 scripts/xcom_dependency_preflight.py --all
```

`--self-test` exercises controlled positive and negative fixtures. Both admission modes verify the manifest, all twelve sibling package archives, Debian metadata, extracted-payload binding, prefix tools/headers/libraries/pkg-config metadata, host build tools, documentation, and a disposable CMake/Ninja compile-only policy probe. The checker uses local file reads, SHA-256, bounded local subprocesses, and temporary directories only. It contains no resolver or network client, installs nothing, and does not modify either explicit input.

### SESN host verification evidence

SESN runs all five required measures—`VM-BLD-UNIT`, `VM-BLD-LINT`, `VM-BLD-STATIC`, `VM-BLD-INTEGRATION`, and `VM-BLD-VALIDATION`—with `allow_network=false`. The host verifier places each measure and its trusted tool-version probe in a bubblewrap network namespace recorded as `bubblewrap-unshare-net`; the command cannot use the host network namespace.

For each measure, SESN retains a bounded log and a private raw environment manifest bound to the exact candidate Git revision. The `index.json` evidence record identifies the measure and carries `command_argv`, `exit_code`, `outcome`, and the SHA-256 hashes of the log and manifest. The raw manifest records the network policy, isolation mechanism, and host environment; it can contain absolute executable paths. Public summaries omit those host-specific paths as well as environment-specific prefix, package-manifest, temporary, and evidence-store paths.

Reviewers must find five revision-matching records in `index.json` and their log/manifest pairs, recompute both recorded hashes, inspect `command_argv`, `exit_code`, and `outcome` in each evidence record, and confirm that every raw manifest has `network_policy.allowed` set to `false` and `network_policy.enforcement` set to `bubblewrap-unshare-net`. This documentation describes the evidence contract only: admission or acceptance requires fresh passing evidence for the reviewed candidate and the separate required review; missing, stale, mismatched, or failed evidence cannot support either claim.

After admission, the repository can be configured without a fetch step:

```sh
cmake -S . -B build -G Ninja -DBUILD_TESTING=ON
cmake --build build --target xverse_xcom_policy_probe --verbose
ctest --test-dir build --output-on-failure
```

The root build exports controlled top-level dependency targets and `xverse::xcom_warnings`. It conditionally includes `src/xverse/xcom` only when a later accepted slice supplies that subtree. This slice intentionally adds no placeholder runtime source and does not establish runtime link readiness.

## Classified failure and evidence semantics

Success emits `XCOM-BLD-I000` with `admitted: true`. Every detected admission failure emits deterministic JSON with `admitted: false`, one or more `XCOM-BLD-E...` diagnostics, and a classified nonzero process result. The stable process classes are:

| Exit | Category | Covered failure |
|---:|---|---|
| 2 | `INPUT_MISSING` | Required environment input or prefix is unset/missing. |
| 3 | `MANIFEST_INVALID` | Manifest JSON, schema, count, uniqueness, filename, size, or digest differs. |
| 4 | `PACKAGE_MISSING` | A retained sibling archive is absent. |
| 5 | `HASH_MISMATCH` | A retained archive's byte size or SHA-256 differs. |
| 6 | `TOOL_MISSING` | Required host, generated-code, analysis, or extraction tool is absent. |
| 7 | `VERSION_MISMATCH` | Tool, header, pkg-config, or Debian identity/version/source differs. |
| 8 | `HEADER_MISSING` | Required admitted header is absent. |
| 9 | `LIBRARY_MISSING` | Required admitted library is absent. |
| 10 | `METADATA_MISSING` | Required Debian or pkg-config metadata is absent/unreadable. |
| 11 | `POLICY_INVALID` | Build, warning, C++20, Ninja, evidence, documentation, or reference-payload policy differs. |
| 12 | `IO_ERROR` | An input, package, payload node, or evidence file cannot be read. |
| 13 | `PROBE_FAILED` | A bounded local metadata, version, extraction, configuration, or build probe cannot execute. |
| 14 | `TIMEOUT` | A bounded local probe exceeds its time limit. |
| 15 | `PAYLOAD_MISMATCH` | Required prefix content, type, or symlink differs from the exact extracted archives. |

When several failures exist, the process returns the numerically lowest applicable nonzero class while preserving all sorted diagnostics in the JSON report. A failure never reports admission.

The manifest path, toolchain path, host paths, and temporary paths are environment-specific and are not copied into public evidence. Public evidence may record package filenames, hashes, versions, licenses, generated-code tool provenance, command identities, diagnostic codes, and pass/fail outcomes. It must not include package binaries, credentials, private addresses, unrestricted payloads, proprietary source, or sensitive deployment values.

## Requirement-to-check traceability

| Requirement | Verification measure and observable evidence |
|---|---|
| `XCOM-BLD-001` | `VM-BLD-UNIT`: `--self-test` covers missing and version-mismatched build-tool descriptions and compiler policy failures. `VM-BLD-VALIDATION`: `--all` configures and builds `xverse_xcom_policy_probe`, then checks CMake-selected compiler identity, C++20, Ninja, testing, and the accepted warning options in `xcom-build-policy.json` and `compile_commands.json`. |
| `XCOM-BLD-002` | `VM-BLD-INTEGRATION`: `--verify-toolchain` checks the exact manifest/archive sizes and hashes, Debian package/version/source metadata, licenses in the lock document, `protoc`, `grpc_cpp_plugin`, clang-tidy, headers, libraries, pkg-config versions, and extracted-payload provenance. Success is `XCOM-BLD-I000`; drift produces classified `XCOM-BLD-E...` evidence. |
| `XCOM-BLD-003` | `VM-BLD-INTEGRATION` and `VM-BLD-VALIDATION`: run the documented commands with network unavailable. The checker reads only the explicit manifest/prefix and repository; CMake disables package registries and FetchContent network resolution, and imported targets use exact prefix paths. Archive hashes and versions must equal the lock. |
| `XCOM-BLD-004` | `VM-BLD-UNIT`: negative fixtures cover missing/malformed manifest, hash drift, missing tools/headers/libraries/metadata, version drift, extraction failures, content/type/symlink drift, timeouts, and policy-evidence drift. `VM-BLD-INTEGRATION`: real-input failures emit `admitted: false` and a classified nonzero exit listed above. |
| `XCOM-BLD-005` | `VM-BLD-VALIDATION`: repository-document validation requires every filename, SHA-256, license, explicit input name, prototype-only/no-runtime boundary, and generated-code statement. Review this document and [dependency-lock.md](dependency-lock.md) for retrieval coordinates, ABI/environment limits, and package-versus-payload semantics. |

An admitted result demonstrates only this local foundation against the identified inputs. It is not a live-readiness probe, runtime validation, dependency redistribution approval, compatibility evidence, or evidence that future X-COM units exist.
