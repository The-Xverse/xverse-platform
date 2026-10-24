# Implementation Plan: Public documentation website

**Branch**: `021-documentation-website` | **Date**: 2026-10-24 | **Spec**: [spec.md](spec.md)

## Summary

Build an Astro/Starlight static home page and documentation in the platform repository. Use Doxygen for C++ headers, Sphinx autodoc for Python public exports, and a bounded Python generator for schemas, live CLI help, source examples, and provenance. Build references before Astro so the static artifact includes all outputs. Run Pagefind over the assembled artifact for unified search.

## Technical Context

- Languages: TypeScript/Astro/CSS for presentation; Python 3.11+ for build tooling.
- Dependencies: pinned Astro/Starlight/npm lock, Sphinx 8.2.3 in a separate locked uv project, existing Doxygen installation.
- Platform: Node 22.23.4+; GitHub Ubuntu runner; static HTML hosting.
- Storage: files only; no backend or accounts.
- Verification: generator contract tests, offline example validation, strict reference builds, artifact link/anchor checks, root/subpath builds, browser checks where available.
- Scope: public Python package exports, X-COM headers, canonical schemas/profiles, actual CLI help, curated narrative pages. No source-code browser or recursive engineering-document import.
- Model profile: Sol/medium recommended for implementation; separate read-only review. This is a task-based judgment, not a measured cost claim.

## Constitution Check

Pass before and after design: local isolated worktree, one capability specification, no legacy mutation or workload, domain-neutral content, XDL schemas remain canonical, no dependency-direction changes, and accurate Lite versus target maturity. Only allowlisted public surfaces enter the artifact. Existing SADS allocations are preserved. Runtime evidence is not inferred from documentation builds.

## Project Structure

```text
website/
  astro.config.mjs
  package.json / package-lock.json
  src/pages/index.astro
  src/content/docs/docs/
  src/styles/
  scripts/generate.py / check_site.py
  reference/pyproject.toml / uv.lock / conf.py
  Doxyfile
  tests/
.github/workflows/website.yml
specs/021-documentation-website/
docs/adr/ADR-0021-public-documentation-website.md
```

## X-Verse architecture gates

The website is a presentation/build layer over existing public platform source. It does not become an alternative configuration language, runtime API, Argus dashboard, registry, or execution interface. ADR-0021 records the design before implementation. A hashed candidate inventory and command evidence accompany review. User acceptance remains pending until explicitly given.
