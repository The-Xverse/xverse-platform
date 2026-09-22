# ADR-0016: Platform subsystem names

**Status**: Accepted — directed by the user on 2026-09-20.

**Date**: 2026-09-20

## Context

The vNext guidance defines domain-neutral orchestration, communication, and observability capabilities
but uses only functional labels. Stable subsystem names are needed before their public packages,
commands, APIs, dashboards, or documentation are introduced.

## Decision

The three platform subsystems use these names:

| Functional capability | Product name | Python namespace | Future source directory |
|---|---|---|---|
| Orchestration | **Maestro** | `xverse.maestro` | `src/xverse/maestro/` |
| Communication | **X-COM** | `xverse.xcom` | `src/xverse/xcom/` |
| Observability | **Argus** | `xverse.argus` | `src/xverse/argus/` |

Public prose and user interfaces use the exact display names **Maestro**, **X-COM**, and **Argus**.
Python identifiers use `maestro`, `xcom`, and `argus` because a hyphen is not valid in a Python module
name.

XDL and the domain-neutral metamodel retain semantic terms such as `communication` and
`observability`. These are portable model concepts, while X-COM and Argus are platform subsystems that
may realize those concepts. Maestro similarly implements orchestration behavior without changing the
generic lifecycle vocabulary.

## Consequences

Future Spec Kit capabilities, ADRs, package names, command groups, diagrams, and public documentation
must use these names consistently. Until each capability is separately specified and accepted, the
names identify architectural targets only and create no implementation or compatibility claim.

The original approved architecture-guidance document remains unchanged as historical baseline input.
This ADR is the authoritative later naming decision where its generic directory labels differ.

## Scope

This decision reserves names and namespaces only. It does not scaffold packages, define APIs, select
protocols or storage, authorize runtime implementation, or change any legacy repository.
