---
title: Fault schedules
description: Resolve fault intent with explicit timing, parameters, and owned boundaries.
sidebar:
  order: 7
---

Faults Lite interprets the admitted closed fault vocabulary and resolves compiled fault intent onto planned ticks. It separates describing a fault from applying it through an owned boundary.

## From intent to effect

1. A Scenario declares a fault and its target.
2. The experiment Profile supplies structured fault intent.
3. Compilation records that intent in the plan.
4. Resolution checks parameters, timing, supported vocabulary, and arbitration.
5. A separately admitted scheduler/boundary applies owned effects and records evidence.

Compilation alone does not perform step 5.

## Use current definitions

The public `xverse.faults` facade exposes `VOCABULARY`, `kind_spec`, `validate_parameters`, `resolve_entry`, `resolve_schedule`, `validate_static`, and related models/constants.

Use the [generated fault API](/reference/python/xverse-faults.html) and [experiment Profile schema](/docs/reference/generated/profiles/experiment-lite-v0.1/) when authoring. Unsupported kinds and parameters must be rejected rather than approximated.

## Timing

Resolution uses the declared clock interpretation and planned ticks. A nominal trigger time and its effective tick may differ. Preserve the mapping and resulting resolution when interpreting evidence.

A deterministic schedule is deterministic within its admitted input and execution model; it does not establish timing fidelity for a physical device.

## Failure and scope

Application failure policies and arbitration are explicit vocabulary elements. Unexecuted intent must remain distinguishable from applied effects.

The current scheduler works through owned relay boundaries. It does not authorize arbitrary external mutation or generalized fault injection across unknown components.
