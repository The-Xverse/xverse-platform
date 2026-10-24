---
title: Reference
description: Source-derived APIs, schemas, CLI help, and validated examples.
---

These pages are regenerated from the platform's current source inputs.

| Reference | Source |
| --- | --- |
| [Python API](/reference/python/) | Explicit public package exports and their signatures/docstrings. |
| [C++ API](/reference/cpp/) | Public X-COM headers and Doxygen comments. |
| [Command line](/docs/reference/generated/cli/) | Actual XDL parser help and Argus usage output. |
| [Core XDL schemas](/docs/reference/generated/schemas/xdl/) | Canonical v1alpha1 JSON schemas. |
| [Common definitions](/docs/reference/generated/schemas/common/) | Shared metadata, identity, references, and constraints. |
| [Experiment Profile](/docs/reference/generated/profiles/experiment-lite-v0.1/) | Admitted experiment-intent schema. |
| [Source examples](/docs/reference/generated/examples/) | Actual example files, checked during the website build. |

## Public Python surfaces

- `xverse_xdl`: validation, normalization, catalog/lifecycle, and experiment-plan APIs.
- `xverse.argus`: evidence storage and offline reconstruction.
- `xverse.maestro`: public preparation facade.
- `xverse.faults`: closed vocabulary and resolution.
- `xverse.flows`: bounded flow policies, binding, clocks, receiver, and evidence helpers.

Internal worker modules are outside this published API surface.

## Reading generated schemas

Tables preserve field definitions and indicate whether a field is required by the immediate object. Conditional rules, references, and schema compositions remain in the complete JSON shown on each page.

The canonical JSON schema is authoritative. A field table does not replace validation.

## Provenance

The [publication manifest](/publication-manifest.json) records source revision, input hashes, selected public packages, and generated pages. Native Python and C++ references share the site's search index and include a return link.

See [how documentation updates](/docs/development/documentation/) for maintaining this site.
