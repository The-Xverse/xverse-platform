---
title: Resources and profiles
description: The five canonical XDL resource types and their shared metadata.
sidebar:
  order: 3
---

XDL v1alpha1 defines five resource kinds. They share the `apiVersion`, `kind`, `metadata`, and `spec` envelope.

| Kind | Question | Typical contents |
| --- | --- | --- |
| Component | What can be reused? | Capabilities, interfaces, endpoints, parameters, requirements. |
| System | How is it composed? | Instances, devices, endpoints, flows, networks, time domains. |
| Deployment | Where and how is it realized? | Targets, artifacts, resources, bindings, time mappings. |
| Scenario | What should the experiment do? | Initial conditions, ordered steps, faults, observers, metrics. |
| Profile | What extension vocabulary applies? | Namespace ownership, compatible API versions, schema reference. |

## Metadata

`metadata.namespace` and `metadata.name` establish resource scope. `metadata.version` identifies the resource content version. Labels and annotations assist discovery; they do not establish compatibility.

Provenance includes source, revision, and maturity, with optional evidence references and limitations. A maturity value of `verified` requires evidence for the stated claim. Passing validation alone does not justify it.

## Profiles

A Profile owns exactly one namespaced key in a resource's `extensions` mapping. The corresponding payload must validate against the supplied compatible profile schema.

A missing or unsupported Profile is unresolved; it is not silently accepted as semantically valid. The v1alpha1 extension conflict policy is `reject`.

The CLI receives local profile schema files explicitly. A schema URI in a description is an identifier/reference, not permission for the tools to retrieve arbitrary remote content.

## Detailed definitions

Browse the generated [core schemas](/docs/reference/generated/schemas/xdl/), [common definitions](/docs/reference/generated/schemas/common/), and [experiment Profile](/docs/reference/generated/profiles/experiment-lite-v0.1/). The complete JSON on each page preserves constraints that field summaries alone cannot express.
