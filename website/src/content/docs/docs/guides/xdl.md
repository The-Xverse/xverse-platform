---
title: Author XDL resources
description: Build a complete, explicit resource set using canonical schemas.
sidebar:
  order: 1
---

Start with the [validated source examples](/docs/reference/generated/examples/) and modify one concern at a time.

## Authoring sequence

1. Define reusable capabilities and interface contracts in a **Component**.
2. Compose instances, devices, endpoints, and flows in a **System**.
3. Bind logical elements to targets and realizations in a **Deployment**.
4. Describe experiment actions in a **Scenario**.
5. Supply each required **Profile** and its local schema.

Validate the complete set after each structural change. The loader does not discover missing resources for you.

## References and IDs

Use lowercase, schema-conforming names. A reference must resolve against an explicitly supplied resource. IDs referenced within a resource follow the schema-defined local scope.

A System needs at least one node or device and at least one time domain. Avoid empty optional collections where omission communicates the same intent.

## Units and parameters

Specify units or an explicit dimensionless interpretation where required. Parameter declarations carry value type, constraints, and mutability. A unit label is not a conversion rule; transformations need their own explicit contract.

## Extend with a Profile

Choose a namespace for the extension, declare a compatible Profile, supply its schema, and validate the payload. Preserve the canonical resource envelope and cross-resource identities.

Use the current [Profile schema](/docs/reference/generated/schemas/profile/) and [profile references](/docs/reference/generated/profiles/experiment-lite-v0.1/) rather than creating another configuration language.

## Validate and inspect

```sh
uv run --frozen xdl validate --format json \
  --profile-schema tests/fixtures/measurement-profile.schema.json \
  xdl/examples/v1alpha1/*.xdl.yaml
```

Inspect diagnostics and static readiness before normalization. A valid description may still be insufficient to run a real experiment; live integration is an additional step.

See [validation and diagnostics](/docs/guides/validation/) for interpreting rejection.
