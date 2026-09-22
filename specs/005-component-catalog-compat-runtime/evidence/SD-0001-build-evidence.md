# SD-0001 reproducible-build evidence

**Date**: 2026-09-20

**Authorization**: The user explicitly authorized the isolated reproducible build after accepting
the ACC017 target-neutral implementation review. This authorization covered artifact construction and
inspection only. It did not authorize starting the gateway, test peers, middleware, AutoVerse, or any
production workload.

**Result**: PASS for a reproducible candidate artifact; NOT READY for execution or final selection.

## Source and isolation

- Repository: `The-Xverse/zenoh2someip_bridge`
- Detached commit: `7c393c9f5a49239c76122486c49cb1993164475c`
- Git tree: `4aab3e623a293626b44a9d8e33c05a307bf51956`
- Source date epoch: `1782746096`
- The repository was cloned into temporary build storage. Its one Git LFS object was materialized,
  checked against object SHA-256 `49bfc1572a8b35b77050a91334fbc73024e798865a834e364e6544ff3f870187`,
  and the checkout was made read-only before configuration.
- A clean Git/LFS status check after the build confirmed the pinned checkout was unchanged.
- All builds were out of tree. No legacy checkout, vNext production source, or running service was
  modified.

Git LFS 3.0.2 was downloaded as an Ubuntu package into temporary tooling storage and was not installed
on the host. Its package SHA-256 was
`7882e77b38c19ff878ebdf013c82c354870f8b6503542cd656bb6748b804df07`.

## Default-build reproducibility finding

Two Release builds using the same source path produced identical gateway bytes. A third build from an
identical frozen source at a different absolute path produced a different digest:

| Build | Gateway SHA-256 | Result |
|---|---|---|
| Default, source path A | `0856a76543a3804112833f9b7324fc714940c0fe5d3cff1a4c0f09528e52c41e` | Reference |
| Default, source path B | `c6932c9ce82e2bbabc42a1a0367d2eeaf54a67bd3af5806383686e9995bf92ba` | Different |

Inspection showed that the default link embeds the absolute source location in RPATH. Therefore the
unmodified default build is not path-independent and is not the candidate artifact.

## Reproducible candidate build

The public-safe [CMake overlay](SD-0001-reproducible-gateway.cmake) was injected through
`CMAKE_PROJECT_INCLUDE`; it did not edit the legacy checkout. It:

- retains only the source project's intended `$ORIGIN`-relative Zenoh and vsomeip library paths;
- prevents CMake from appending host source directories; and
- disables the path-sensitive GNU build ID.

Release builds from two distinct absolute source paths then produced byte-identical 64-bit x86-64
PIE executables:

| Field | Value |
|---|---|
| Gateway SHA-256 | `1fcf49058ff358dc7e81b11f18f4f288c709409b1ac0d9d7f3258b6e12b4b7c2` |
| Gateway size | 271,832 bytes |
| Runtime lookup | `$ORIGIN`-relative bundled-library directories only |
| Build execution | Not performed; the executable was inspected statically only |

The build used Ubuntu 22.04.5 x86-64, CMake 3.22.1, Ninja 1.10.1, GCC/G++ 11.4.0, binutils 2.38,
Boost 1.74.0, `LC_ALL=C`, `TZ=UTC`, and the pinned source timestamp. Exact package and tool hashes are
in the [artifact manifest](SD-0001-artifact-manifest.json).

## Candidate bundle

The candidate bundle contains the gateway, the two source-selected runtime configuration files, the
materialized Zenoh library, and the repository's complete vsomeip library directory. Its layout
preserves the executable's relative configuration and library lookup assumptions.

Two independently generated deterministic tar archives were byte-identical:

| Field | Value |
|---|---|
| Archive SHA-256 | `6ce98220d1c4997a20d2b85464e7e1550e8347d68c572bfb63586c150f41f946` |
| Archive size | 123,566,080 bytes |
| Internal manifest SHA-256 | `f1f88f50213d20f027f9726512b2250ee453cc7d5d4d2753ad51e2714e85967e` |
| Member validation | 16 files/symlinks passed size, digest, target, ordering, and safe-path checks |
| Retention | Temporary local build storage; no durable restricted artifact store is approved |

The archive itself is excluded from Git. It includes third-party binaries and configuration whose
distribution and retention require owner approval.

## Remaining limitations

- The build is reproducible on one recorded host/toolchain across distinct source paths. A hermetic
  toolchain image or independently reproduced build is still unavailable.
- System runtime libraries are not bundled and the execution environment remains unpinned.
- Bundled vendor binaries contain historical absolute build-path strings. Their values are withheld;
  owner review must either accept them inside a restricted isolated environment or authorize a
  reproducible rebuild/sanitization of those libraries.
- The selected configuration files are valid JSON and contain no observed credential-named field,
  private IPv4 address, or absolute home path. This is evidence about those files only, not the future
  runtime environment.
- No executable, middleware session, network interface, readiness probe, or payload path was run.
  Compatibility, lifecycle behavior, and parity remain unverified.
