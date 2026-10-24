---
title: Your first system
description: Validate and normalize a complete, domain-neutral XDL example.
sidebar:
  order: 2
---

This guide uses the five public example resources already in the repository. They describe sample production and observation. Their provenance labels explicitly identify structural examples; validating them establishes consistency rather than runtime behavior.

## 1. Understand the input set

| File | Role |
| --- | --- |
| `component.xdl.yaml` | Reusable sample-producing component. |
| `system.xdl.yaml` | Logical composition, endpoints, flow, device, and time domain. |
| `deployment.xdl.yaml` | Selected targets, artifacts, and realization bindings. |
| `scenario.xdl.yaml` | Declared actions, faults, observers, and metrics. |
| `profile.xdl.yaml` | Measurement extension vocabulary and schema reference. |

Browse the [actual source examples](/docs/reference/generated/examples/). The example Profile uses an illustrative schema URI; validation receives its local schema explicitly.

## 2. Validate the complete graph

```sh
uv run --frozen xdl validate --format text \
  --profile-schema tests/fixtures/measurement-profile.schema.json \
  xdl/examples/v1alpha1/profile.xdl.yaml \
  xdl/examples/v1alpha1/component.xdl.yaml \
  xdl/examples/v1alpha1/system.xdl.yaml \
  xdl/examples/v1alpha1/deployment.xdl.yaml \
  xdl/examples/v1alpha1/scenario.xdl.yaml
```

Expected output:

```text
valid: 5 resource(s)
```

The website build checks this same input set with the current validator. No simulator, device, or process provider is started.

## 3. Export canonical JSON

```sh
mkdir -p build/xdl
uv run --frozen xdl normalize \
  --profile-schema tests/fixtures/measurement-profile.schema.json \
  --output build/xdl/normalized.json \
  xdl/examples/v1alpha1/*.xdl.yaml
```

Add `--include-source-map` when you need mappings to authored locations. Choose a fresh output path: an existing output file may be overwritten, while input resources and schemas cannot be used as output paths.

## 4. Try a deliberate error

Copy the examples into a temporary directory and change a referenced element ID without changing its declaration. Validate that copied set. The validator should reject the unresolved reference and provide a diagnostic location and correction.

Restore the copied input and validate again. This gives a concrete distinction between YAML syntax, resource structure, and cross-resource semantics.

## What success establishes

The supplied descriptions are statically consistent under the admitted schemas. Static readiness does not establish live target readiness, timing behavior, or compatibility with a legacy application.

Continue with [authoring XDL](/docs/guides/xdl/) or [compiling an experiment plan](/docs/guides/experiments/).
