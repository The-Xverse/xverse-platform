# Website build and publication contract

From repository root, install website npm dependencies and `uv sync --project website/reference --frozen`. `npm --prefix website run build` generates every reference, validates offline examples, builds Astro, indexes all reference HTML, and checks internal links/anchors. `npm --prefix website run dev` prepares the same references before starting the local documentation server.

`SITE_URL` defaults to `https://the-xverse.github.io`. `BASE_PATH` defaults to `/xverse-platform/`; set `/` for a custom root domain. Only absolute URL origins and absolute normalized path prefixes are supported. All authored site links include the configured prefix at build time.

Generated outputs: `website/src/content/docs/docs/reference/generated/`, `website/public/reference/`, `website/public/schemas/`, and `website/public/publication-manifest.json`. These are ignored; source is version controlled. Static output is `website/dist/`.

CI: pull requests run the full build with read-only repository permission; main pushes and manual dispatch build and then deploy with job-scoped Pages write/id-token permission. Pages must be configured to use GitHub Actions. Failed checks never deploy. No secret or personal access token is required for Pages deployment.

Failure reporting: commands return nonzero with the missing input/tool, generator error, example diagnostic, or broken URL. No fallback to partial generated references. Python and C++ source imports/parsing are documentation-only and never authorize live execution.
