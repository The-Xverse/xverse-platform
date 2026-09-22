# Implementation Plan: XDL loader, validator, and normalizer

**Branch**: `main` | **Date**: 2026-09-20 | **Spec**: [spec.md](spec.md)

## Summary

Implement the approved v1alpha1 parsing, Draft 2020-12 schema, closed-set reference, semantic,
normalization, static-readiness, Profile-policy, diagnostic, library, and CLI contracts as a Python
package. Use safe YAML 1.2 parsing, an explicit offline schema registry, frozen public data, bounded
inputs, and deterministic output. Record resource-wide element identity and loader boundaries in
ADR-0013 before implementation.

## Technical Context

**Language/Version**: Python 3.11–3.14; reference environment Python 3.13.13

**Primary Dependencies**: `jsonschema[format]>=4.26,<5`, `referencing>=0.37,<1`,
`ruamel.yaml>=0.19.1,<0.20`

**Storage**: Read-only resource/schema files and optional explicit JSON output; no database

**Testing**: Standard-library `unittest`, CLI subprocess tests, M2 acceptance validators, performance probe

**Target Platform**: Local cross-platform CPython library/CLI; offline by design

**Project Type**: Parser/validator/normalizer library with CLI

**Performance Goals**: 100 small resources under 2 seconds and 128 MiB peak RSS in the reference environment

**Constraints**: Safe untrusted input, no networking, deterministic output, no partial normalization,
5 MiB/file, depth 100, nodes 100,000, resources 1,000 by default

**Scale/Scope**: Five XDL kinds, seven core schemas, explicit Profile schemas, six validation gates

## Constitution Check

Pass before research and after design:

- Production safety: implementation is confined to xverse-platform and reads no legacy checkout.
- Domain neutrality: code dispatches approved resource kinds and contains no domain/provider vocabulary.
- XDL centrality: implements the approved schemas and normalized model without another language.
- Standards: uses maintained YAML 1.2 and Draft 2020-12 libraries; no standards reimplementation.
- Logical/physical: semantics preserve Deployment-only realization and physical asset requirements.
- Compatibility: no legacy compatibility claim or production dependency is introduced.
- Repository direction: no companion change or reverse dependency.
- Maturity/evidence: prototype label, static readiness, dependency lock, tests, and limitations are explicit.
- Traceability: diagnostics retain source and pointers; normalized resources preserve provenance.

ADR-0013 resolves the resource-wide element identity rule and offline deterministic loader boundary.
No constitutional exception is required.

## Project Structure

### Documentation

```text
specs/004-xdl-loader-validator/
├── spec.md
├── clarifications.md
├── research.md
├── data-model.md
├── plan.md
├── quickstart.md
├── contracts/
│   ├── cli.md
│   └── library.md
├── checklists/
│   ├── requirements.md
│   └── acceptance.md
├── tasks.md
├── analysis.md
└── validation.md
```

### Source code

```text
pyproject.toml
src/xverse_xdl/
├── __init__.py
├── __main__.py
├── cli.py
├── diagnostics.py
├── loader.py
├── models.py
├── normalize.py
├── schema.py
├── semantics.py
└── validate.py
tests/
├── fixtures/
│   └── measurement-profile.schema.json
├── test_cli.py
├── test_loader.py
├── test_normalize.py
├── test_schema.py
├── test_semantics.py
└── test_validation.py
```

**Structure Decision**: One distributable package with separate modules for stages and frozen public
models. Core schemas remain authored under `xdl/schemas/v1alpha1` and are included as package data at
build time; development resolves them from one deterministic package resource location.

## Implementation phases

1. Package metadata, dependency lock, ignore rules, and ADR-0013.
2. Frozen models, diagnostics, limits, safe parsers, source maps, and schema registry.
3. Closed catalog/reference resolution and all kind-specific semantic rules.
4. Immutable normalization, canonical JSON, static readiness, and Profile policy.
5. Library orchestration and local CLI.
6. Positive, negative, equivalence, determinism, limit, CLI, and performance tests.
7. Documentation, Spec Kit analysis, validation evidence, and separate architecture review.

## X-Verse architecture gates

Runtime gate is limited to executing the parser/validator test suite and CLI against public-safe
fixtures. No X-Verse workload or legacy executable is run. Compatibility gate confirms no legacy
surface changes. Reproducibility records dependency versions, Python/platform, command results, and
performance. The required human acceptance was recorded on 2026-09-20; M3 may be specified, while
runtime implementation remains subject to its own authorization.

## Complexity Tracking

No constitutional violation. Three runtime dependencies are justified by standards compliance and
safe YAML parsing. Implementing those standards locally would be less reliable and harder to govern.
