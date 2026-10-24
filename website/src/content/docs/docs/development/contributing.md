---
title: Contributing
description: Make code, examples, and documentation changes together.
sidebar:
  order: 1
---

X-Verse is licensed under Apache 2.0. Contributions should preserve domain-neutral concepts, explicit boundaries, and reproducible evidence.

## Start with the intended behavior

Describe the problem, current behavior, expected behavior, compatibility impact, and how the change will be checked. Use the repository's capability/specification workflow for software changes.

Read `AGENTS.md`, the constitution, and the relevant architecture decisions in your checkout. Acceptance gates are part of the engineering process.

## Make documentation part of the change

- Update source docstrings/comments when API meaning changes.
- Update canonical schemas when admitted resource structure changes.
- Keep examples executable or statically checkable.
- Update affected guides and maturity statements.
- Include compatibility notes when callers must change.

The documentation build catches structural drift and broken links. It cannot decide whether an explanation remains conceptually correct.

## Validate the website

```sh
npm --prefix website ci
uv sync --project website/reference --frozen
npm --prefix website run test
npm --prefix website run build
```

Documentation tooling has a separate environment and does not change the platform's runtime dependencies.

## Review and acceptance

Reviewers assess behavior, evidence, compatibility, architecture, and public-safe content. A passing build is evidence for its checks; it is not automatic capability acceptance.

Keep generated HTML, reference Markdown, and local environments out of source control. The workflow rebuilds them from reviewed inputs.
