---
title: Compile experiment intent
description: Produce a deterministic offline experiment plan and inspect its digest.
sidebar:
  order: 3
---

XDL Lite extends the resource graph with an admitted experiment Profile. Compilation resolves **declared intent** into a plan; it does not start components, activate faults, or collect measurements.

## Compile the owned example

From the repository root:

```sh
mkdir -p build/xdl
uv run --frozen xdl experiment compile \
  --profile-schema xdl/profiles/experiment-lite-v0.1.schema.json \
  --output build/xdl/experiment-plan.json \
  tests/thesis_lite/xdl/fixtures/profile.xdl.yaml \
  tests/thesis_lite/xdl/fixtures/component.xdl.yaml \
  tests/thesis_lite/xdl/fixtures/system.xdl.yaml \
  tests/thesis_lite/xdl/fixtures/deployment.xdl.yaml \
  tests/thesis_lite/xdl/fixtures/scenario.xdl.yaml
```

Success prints a `resolved plan` summary and a SHA-256 digest. The website build also compiles this input set.

## Inspect the plan

The plan records selected resource identities, input provenance, parameters, time mappings, dependency order, lifecycle intent, faults, observers, metrics, and declared limitations.

Treat the plan as a resolved input to later orchestration. A step in the plan is an intended action, not a record that the action occurred.

## Reproducibility

Preserve the input files, schema/profile versions, tool version, and plan digest together. Optional `--run-id` and `--generated-at` values must be supplied explicitly when needed.

`--expect-input-digest NAME=SHA256` supports explicit expected input identities. See [current CLI reference](/docs/reference/generated/cli/) and the public `compile_experiment_files` / `plan_matches_digest` APIs.

## Next boundary

Execution requires admitted providers, ownership, environment assumptions, and lifecycle controls. Read [Maestro and lifecycle](/docs/guides/maestro/) before treating an offline plan as executable.
