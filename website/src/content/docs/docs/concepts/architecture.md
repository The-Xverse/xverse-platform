---
title: Architecture
description: How XDL, Maestro, X-COM, Argus, profiles, and providers fit together.
sidebar:
  order: 1
---

X-Verse keeps **system intent**, **realization**, **execution**, **communication**, and **evidence** as distinct concerns. Its core concepts apply across cyber-physical domains.

## Dependency direction

```text
Domain blueprints
       ↓
Domain profiles
       ↓
XDL descriptions and platform APIs
       ↓
Runtime abstractions and provider contracts
```

A domain-specific blueprint consumes the platform. The platform core does not depend on a particular blueprint or industry.

## Responsibilities

| Part | Owns | Boundary |
| --- | --- | --- |
| XDL | Canonical resources, validation, normalization, and compiled intent. | Descriptions do not start components. |
| Maestro | Coordinating admitted lifecycle/experiment actions. | Execution needs exact ownership, provider, and admission contracts. |
| X-COM | Communication contracts and controlled observation/stimulation boundaries. | Telemetry presentation belongs elsewhere. |
| Argus | Evidence storage, inspection, and observability interfaces. | Evidence storage does not control experiments. |
| Provider | Binding a platform contract to a concrete realization. | A provider must declare its actual capabilities and limitations. |
| Profile | Namespaced semantics and validation extensions. | Extensions preserve the shared XDL resource model. |
| Blueprint | A composed domain example or experiment. | Domain assumptions remain explicit. |

## Repository responsibilities

- `xverse-platform` owns domain-neutral APIs, XDL, and architecture.
- `xverse-compat` owns compatibility boundaries and adapters.
- `xverse-blueprints` owns composed examples.

A user can install the local XDL tools using the platform repository alone. Compatibility paths have their own inputs and admission boundaries.

## Implementation and direction

The architecture describes long-term responsibilities. [Project status](/docs/status/) identifies the bounded implementations currently available. A subsystem diagram or package name is not an implementation or readiness guarantee.

See [logical identity and realization](/docs/concepts/identity/) and the [subsystem guides](/docs/guides/maestro/) for practical boundaries.
