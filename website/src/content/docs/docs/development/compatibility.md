---
title: Compatibility and versioning
description: Distinguish resource API, content, package, release, and evidence versions.
sidebar:
  order: 3
---

X-Verse carries several version identities because they answer different questions.

| Identity | Meaning |
| --- | --- |
| XDL API version | Resource serialization and semantic contract, currently `xverse.io/xdl/v1alpha1`. |
| Resource metadata version | Version of a particular resource's content. |
| Profile version/schema | Extension vocabulary and admitted constraints. |
| Python package version | Installed distribution identity, currently `xverse-xdl` 0.4.0. |
| Lite release baseline | Cross-component engineering release identity, currently 1.0 rc.1 at this documentation baseline. |
| Source revision/digest | Exact code or input content used for a build/run. |
| Evidence format version | Interpretation of a stored manifest or event record. |

## Compatibility is explicit

Stable logical identity does not establish interchangeable implementations. Compare payload schemas, units, timing semantics, lifecycle assumptions, provider capability, and version constraints.

A converter or adapter must be admitted explicitly. Describing a protocol reference does not imply that the corresponding provider is implemented.

## Source and release documentation

Generated API pages follow the checked-out source revision. The status page is an authored statement grounded in release and acceptance records.

When sharing evidence, retain exact revision and digest identities. Do not extrapolate a result from one candidate to an untested successor.

## Changing a contract

Document the before/after behavior, affected callers, migration requirements, failure modes, and verification scope. Preserve historical evidence for the exact revisions it identifies rather than rewriting it as current proof.
