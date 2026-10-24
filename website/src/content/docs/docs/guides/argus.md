---
title: Argus evidence
description: Inspect, verify, and export bounded run evidence offline.
sidebar:
  order: 6
---

Argus Lite provides bounded evidence persistence and offline reconstruction. Its CLI reads existing evidence; it does not start experiments or attach to a live stream.

## Verify an existing run

Replace `path/to/run-root` with an existing admitted evidence directory:

```sh
uv run --frozen xverse-argus verify path/to/run-root
```

The JSON summary includes the run ID, writer state, assessed evidence status/reasons, recorded evidence status/reasons, event count, and diagnostics.

Exit status 0 means complete evidence without diagnostics. Status 1 identifies incomplete/corrupt evidence; status 2 indicates a usage/input failure.

## Export

```sh
uv run --frozen xverse-argus export path/to/run-root --format json
uv run --frozen xverse-argus export path/to/run-root --format jsonl
```

Exports go to standard output. Redirect to a separate file when needed. The CLI does not mutate the run root.

Export success alone is not a complete-evidence verdict; inspect verification and diagnostics.

## Python API

The public facade provides `EvidenceStore`, `EvidenceRun`, `EvidenceReader`, `EvidenceManifest`, `EvidenceLimits`, diagnostics, errors, and format-version constants.

`EvidenceStore.open_run` is the programmatic writer entry point. `EvidenceStore.read_run` is the offline reader entry point. The [generated Argus API](/reference/python/xverse-argus.html) gives their exact contracts.

## Interpreting partial evidence

Compare recorded writer statements with the reader's assessed result. Preserve diagnostic codes and reasons. A verified prefix or readable export does not imply that all intended actions completed.

Evidence integrity and experiment validity answer different questions: correctly stored evidence can still describe a failed or limited experiment.

## Current scope

Argus Lite supplies storage and inspection. Live dashboards, metric computation, network collection, and generalized observability services are separate capabilities.
