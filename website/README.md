# X-Verse website

Astro/Starlight home page and public documentation with source-generated references. Apache 2.0, like the platform. No backend or paid service is required.

## Build and preview

Prerequisites: Node **22.23.4+**, npm, Python **3.11+**, uv, and Doxygen. On Debian/Ubuntu install Doxygen using your normal package manager. The Python documentation environment is separate from the platform environment.

From the repository root:

```sh
npm --prefix website ci
uv sync --project website/reference --frozen
npm --prefix website run test
npm --prefix website run build
npm --prefix website run preview
```

Open the printed URL under `/xverse-platform/`. For authoring, `npm --prefix website run dev` generates references once and starts the development server. Restart it or run `npm --prefix website run generate` after Python/C++/schema changes. Search requires a built site; test it with preview.

## Sources and updates

- Home page: `src/pages/index.astro`; styles in `src/styles/`.
- Narrative documentation: `src/content/docs/docs/`.
- Scope/source mapping: `content-map.json`.
- Generated schema/CLI/example pages: `scripts/generate.py`.
- Python API: public package `__all__` exports through Sphinx autodoc; selected imports only.
- C++ API: public X-COM headers through `website/Doxyfile`, reusing root aliases. The existing developer Doxyfile is unchanged.
- Unified static search: Pagefind indexes the assembled HTML after Astro.

Change comments/docstrings and narrative guides in the same pull request as behavior. Structural references update on build; rationale and maturity still require review. API availability does not prove runtime success.

Generated files, HTML, caches, and environments are ignored. Do not edit or commit generated reference pages. Every run replaces generated directories and writes `public/publication-manifest.json` with revision and input hashes. `scripts/check_site.py` rejects missing outputs, broken internal links/anchors, base-path escapes, and local/private host paths in HTML.

## Automatic publication

`.github/workflows/website.yml` checks pull requests and builds every main push. After candidate acceptance/integration, enable **Settings → Pages → GitHub Actions**. The successful main build uploads the checked static artifact and a separate job deploys it. The workflow uses GitHub's job token; no personal token is needed.

The default target is `https://the-xverse.github.io/xverse-platform/`. This is the configured destination, not a claim that it has been deployed. Hosted execution and account settings must be verified after enablement.

For root/custom-domain hosting:

```sh
SITE_URL=https://example.org BASE_PATH=/ npm --prefix website run build
```

Update both workflow environment values and the Pages domain settings when changing hosting. A custom domain is optional and may cost money; the `github.io` address is free within GitHub's service limits. Static output can also be hosted by another static server.

## Verification boundaries

The build validates the five public XDL resources and compiles the owned offline experiment fixture. It does not run Maestro providers, native helpers, simulations, device workloads, or the C++ test suite. Doxygen parses headers without building X-COM. Sphinx imports only selected public package facades; keep those imports free of runtime side effects.

Candidate requirements, design, traceability, verification, and review are under `specs/021-documentation-website/`. Acceptance/main integration and publication follow the repository's explicit acceptance rules.
