# Research: XDL loader, validator, and normalizer

## Decision summary

| Topic | Decision | Rationale | Rejected alternatives |
|---|---|---|---|
| Implementation | Python package and local CLI, CPython 3.11–3.14 | Portable, readable reference implementation; repository already uses Python acceptance tooling; library and CLI can share one pipeline. | A daemon creates an unneeded production interface; a custom parser duplicates mature standards tooling. |
| YAML | `ruamel.yaml` 0.19.x, pure safe/round-trip-derived loading, YAML 1.2, duplicate keys disabled | Supports YAML 1.2, source positions, safe construction, and duplicate-key rejection. Pin the tested minor series because its own docs recommend pinning. | PyYAML primarily follows YAML 1.1 scalar resolution and would not implement the approved contract precisely. |
| JSON Schema | `jsonschema` 4.26.x with Draft202012Validator and format checking | Maintained implementation with full Draft 2020-12 support and iterable errors. | The M2 documentary subset is intentionally incomplete and cannot certify general schema semantics. |
| References | `referencing` 0.37.x with an in-memory Registry | Explicit registry is deterministic and does not retrieve unknown remote references. | Deprecated automatic resolver behavior risks implicit network retrieval. |
| Packaging | PEP 517/621 `pyproject.toml`, `src/` layout, console script | Keeps imports isolated from the repository root and supports editable/test installs. | Ad-hoc `PYTHONPATH` and standalone scripts obscure dependency and API boundaries. |
| Tests | Standard-library `unittest`, subprocess CLI integration tests | Avoids a test-only dependency while covering library and CLI behavior. | A broad test framework adds little value for this initial bounded package. |
| Resource resolution | Closed explicit catalog | Matches approved M2 rules and makes repeat results independent of environment. | Filesystem search, registries, and network resolution are deferred and nondeterministic. |
| Extension schemas | Explicit local schema inputs keyed by `$id` | Satisfies Profile validation without enabling network access. | Trusting a Profile declaration without payload validation would weaken M2; automatic retrieval violates the resolution boundary. |
| Identity | Resource-wide element ID uniqueness | ElementRef and canonical identity omit collection, so collection-local duplicates are ambiguous. | Adding collection to ElementRef would break the approved v1alpha1 schema. |
| Canonical output | Deterministic JSON with recursively sorted mapping keys and compact separators | Stable for automation and semantic comparison; source maps can be emitted separately. | Canonical byte signatures are a separate cryptographic/governance decision. |

## Dependency evidence

- [`jsonschema` on PyPI](https://pypi.org/project/jsonschema/) documents Draft 2020-12 support,
  iterable validation errors, Python 3.10+, and release 4.26.0.
- [`referencing` on PyPI](https://pypi.org/project/referencing/) documents the explicit reference
  registry implementation and release 0.37.0.
- [`jsonschema` reference-resolution documentation](https://python-jsonschema.readthedocs.io/)
  explains that `referencing.Registry` does not implicitly retrieve remote resources.
- [`ruamel.yaml` on PyPI](https://pypi.org/project/ruamel.yaml/) documents YAML 1.2 support, current
  0.19.x releases, supported Python versions, and the recommendation to pin tested versions.
- [`ruamel.yaml` API documentation](https://yaml.dev/doc/ruamel.yaml/api/) documents safe loader
  modes and duplicate-key rejection; its basic-use documentation distinguishes pure YAML 1.2 behavior.
- [Python packaging guidance](https://packaging.python.org/en/latest/) defines modern `pyproject.toml`
  metadata, build backends, console scripts, and `src` layout conventions.

Versions are bounded to tested compatible minor series rather than claimed as permanent choices.
The lock file records the exact resolved development environment.

## Security and resource-limit evidence

Input is untrusted data. The loader reads bytes with a per-file limit, decodes strict UTF-8, uses no
unsafe YAML constructors, rejects duplicate and non-string keys, detects cycles, and bounds traversal
depth/nodes/resource count. JSON rejects duplicate keys and non-finite constants. Schema registries
contain only packaged core schemas and explicitly supplied Profile schemas; unresolved URIs fail.

No input value is passed to a shell, imported as code, interpreted as an expression, dereferenced as
a filesystem path, or used for network access. Scenario actions, acceptance strings, lifecycle text,
secret references, and external URIs remain opaque data.

## Maturity and limitations

This is a prototype reference implementation of approved XDL v1alpha1. Python-library behavior and
the local CLI are implemented and tested. Cross-language canonicalization, cryptographic signing,
registries, conversions, streaming, incremental graphs, live readiness, and runtime plans remain
architectural targets.
