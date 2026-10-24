---
title: Time and evidence
description: Separate declared timing, observed behavior, and evidence provenance.
sidebar:
  order: 4
---

A declared time domain gives experiment values an interpretation. It does not establish a timing guarantee.

## Time domains

A System declares its time domains and may select a default domain. Scenario steps and flows refer to domains explicitly. Deployment time mappings describe relationships required by a realization.

Clock class, epoch, rate interpretation, and monotonicity are part of the description. Conversion between domains needs an admitted mapping; arbitrary clock values are not interchangeable.

The bounded flow layer provides explicit time quantities and mapping helpers. Use the [generated flow API](/reference/python/xverse-flows.html) for current signatures.

## Intent and observation

A compiled plan records intended actions and dependencies. Evidence records what a particular execution path reports.

A declared observer or metric is part of intent. It is not proof that observations were collected or that the metric was evaluated. Acceptance text remains a declaration unless an admitted evaluator supplies results.

## Provenance and integrity

XDL provenance identifies description origins and revisions. The experiment plan carries input provenance and a digest. Argus adds bounded run evidence storage and offline reconstruction.

A digest helps bind content to an identity. It does not independently establish the truth of every recorded event or the fitness of an experiment.

## Practical interpretation

Read static validation, compiled plan, runtime outcome, and evidence verification as separate results. Preserve the associated versions and limitations when comparing experiments.

Continue with [experiment compilation](/docs/guides/experiments/) and [Argus evidence](/docs/guides/argus/).
