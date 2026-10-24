---
title: Maestro and lifecycle
description: Understand lifecycle preparation, owned execution, and the Lite boundary.
sidebar:
  order: 4
---

Maestro coordinates lifecycle and experiment intent. The current repository contains **bounded Maestro Lite implementations**, while a generalized orchestration service remains a broader target.

## Prepare before execution

The public `xverse.maestro` facade exposes `prepare`, `Limits`, `PreparationError`, `PreparedLifecycle`, and `ProviderDescriptor`. Preparation projects experiment intent onto admitted lifecycle/provider descriptions.

Use the [generated preparation API](/reference/python/xverse-maestro.html) for exact signatures. Internal runtime modules are not automatically stable extension interfaces.

## Ownership and permits

Runtime actions must operate on explicitly owned resources. A logical reference or compiled plan does not confer execution authority.

The `xverse_xdl` lifecycle APIs expose execution permits, owned handles, provider contracts, and evidence journaling. Cleanup must preserve ownership boundaries and diagnose failures rather than inventing success.

## Isolated fixture demonstration

The existing repository demonstration exercises bounded lifecycle mechanics using an in-memory fixture:

```sh
uv run --frozen python scripts/validate_m3.py
```

It validates a fixture graph, derives catalog information, and exercises preparation, start, observation, stop, and cleanup. Its outcome establishes only the demonstrated fixture scope.

The website build does not run this demonstration or any process-provider path.

## Lite implementation limits

The release candidate contains a specialized trusted-host orchestration path, admission controls, evidence handling, and native helpers. Those engineering results are bound to their recorded configuration and limits.

Do not infer a network scheduler, arbitrary workload launcher, automatic legacy compatibility, or complete production runtime from the public preparation API.

## Integration sequence

1. Compile and inspect the XDL intent.
2. Identify exact provider and lifecycle contracts.
3. Establish required ownership, admission, and environment assumptions.
4. Execute only within the separately authorized integration scope.
5. Preserve evidence and inspect partial/failed outcomes.

Read [Argus evidence](/docs/guides/argus/) and [status](/docs/status/) before extending the path.
