---
title: Flow bindings
description: Bind described flows to explicit policies and inspect bounded outcomes.
sidebar:
  order: 8
---

The Lite flow runtime supplies a bounded Python route layer that mirrors admitted C++ X-COM loopback rules. It does not open a C++ X-COM route or activate the core.

## Binding

The public `bind` operation takes compiled intent and normalized resources, returning a `FlowBindingRecord`. Bindings use explicit per-route policies; refusals are collected rather than silently discarded.

Current public types include `FlowPolicy`, `FlowBinding`, `FlowBindingRecord`, and flow identity/hash helpers. See the [generated flow API](/reference/python/xverse-flows.html).

## Time interpretation

Use the closed time grammar, `TimeMapping`, quantity parsing, and clock helpers provided by the flow package. Preserve declared domains and conversion assumptions with the experiment.

Do not compare values from different clocks by treating their raw numbers as equivalent.

## Receiving and evidence

The receiver produces explicit item verdicts. The harness and evidence helpers make bounded outcomes inspectable without converting the Python layer into a general transport implementation.

A sent item, command echo, receiver verdict, and measured physical effect are distinct observations.

## Integration checklist

- Validate the complete resource graph and compile its intent.
- Inspect every binding refusal and provider capability.
- Confirm route policy, payload schema, units, timing, and capacity.
- Preserve the exact mirrored source identity when claiming correspondence.
- Inspect evidence and limitations for the specific run.

Use the [X-COM guide](/docs/guides/xcom/) for the separate C++ implementation and tool gateway boundary.
