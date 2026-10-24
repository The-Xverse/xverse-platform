---
title: How documentation updates
description: The build pipeline, source ownership, and automatic publishing workflow.
sidebar:
  order: 2
---

The site follows **docs as code**: narrative pages, comments, schemas, example inputs, and build configuration are reviewed in the same repository as the implementation.

## What changes automatically

| You change | The next build updates |
| --- | --- |
| Public Python signatures or docstrings | Sphinx API reference. |
| Public C++ headers or documentation comments | Doxygen API reference. |
| Canonical XDL schema constraints | Field tables, full JSON, and downloadable schemas. |
| XDL parser commands/options | Command-line reference. |
| Source example files | Included example text and validation result. |
| Markdown guides | Narrative documentation and search index. |

The build replaces generated output directories first, so removed reference inputs do not leave stale generated pages.

## What still needs a person

Purpose, rationale, integration instructions, tradeoffs, and maturity statements need authorship. Include those updates with a behavior change even when its signature remains unchanged.

A generated reference does not prove runtime behavior or promote a release candidate to a final release.

## Pipeline

```text
Reviewed source inputs
  → Generate schemas, CLI help, examples, Python/C++ API
  → Validate example graph and compile experiment fixture
  → Build Astro/Starlight pages
  → Index the assembled site with Pagefind
  → Check internal links, anchors, and publication boundaries
  → Publish successful main-branch builds
```

Pull requests run checks without deployment permissions. Publication runs separately after a successful main build.

## Local commands

```sh
npm --prefix website run dev
npm --prefix website run build
npm --prefix website run preview
```

The development server prepares references, while search indexing happens during a full build. Use preview to test search.

Reference generation runs at server startup; after changing Python/C++/schema inputs, restart the dev command or run `npm --prefix website run generate`. Authored Astro/Markdown pages update through the development server.

## Hosting

GitHub Pages uses the workflow in `.github/workflows/website.yml`. The repository must enable **Settings → Pages → GitHub Actions**. Default hosting uses the project subpath `/xverse-platform/`.

Set `SITE_URL` and `BASE_PATH` consistently for another origin or a root-domain deployment. See `website/README.md` for exact maintenance commands.

## Publication scope

The build selects public package exports, public headers, canonical schemas/profiles, examples, and curated guides. It does not recursively copy engineering evidence, deployment configuration, or private research material.

Inspect the [manifest](/publication-manifest.json) when identifying the input set of a particular site build.
