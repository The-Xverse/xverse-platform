---
title: X-Verse documentation
description: A practical path from system descriptions to bounded experiments and evidence.
---

X-Verse is an open source platform for describing and experimenting with **cyber-physical systems**: software interacting with simulated models, virtual hardware, or physical devices.

Its central idea is to preserve logical identity while making realization choices explicit. A sensor remains the same logical sensor whether a deployment selects a simulator or a physical device.

## Start with a complete example

1. [Install the local tools](/docs/getting-started/installation/).
2. [Validate your first five-resource system](/docs/getting-started/first-system/).
3. [Compile an experiment plan](/docs/guides/experiments/).
4. [Explore generated API and schema references](/docs/reference/).

## What the platform contains

| Area | Responsibility |
| --- | --- |
| **XDL** | Canonical descriptions, validation, normalization, and experiment compilation. |
| **Maestro** | Lifecycle preparation and bounded Lite orchestration. |
| **X-COM** | C++ communication contracts, observation, and controlled stimulation. |
| **Argus** | Bounded run evidence storage, offline inspection, and export. |
| **Faults and flows** | Deterministic fault schedules and a bounded Python flow layer. |

The current baseline is **X-Verse Lite 1.0 rc.1** as recorded on 2026-10-24, with final release qualification pending. These are bounded engineering capabilities; individual subsystem scope matters. Read [status and limitations](/docs/status/) before selecting an integration.

## Choose a documentation path

- **Concepts** explain identity, realization, architecture, resources, time, and evidence.
- **Guides** walk through authoring and integration tasks.
- **Reference** is generated from public API declarations, schemas, CLI definitions, and actual example files.
- **Development** explains contribution, compatibility, and automatic documentation updates.

Automated reference generation reflects source structure. Narrative explanations and maturity claims are reviewed alongside source changes.
