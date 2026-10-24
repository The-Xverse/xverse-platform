# Candidate validation

Prerequisites: Node >=22.23.4, npm, Python >=3.11, uv, Doxygen. From repository root:

```sh
npm --prefix website ci
uv sync --project website/reference --frozen
npm --prefix website run test
npm --prefix website run build
BASE_PATH=/ npm --prefix website run build
npm --prefix website run dev
```

Expected: generated Python/C++/schema/CLI references; valid five-resource example; zero broken internal links/anchors; Pagefind search assets. Open the printed local URL at the configured base path. Inspect the home page and guide at desktop/mobile widths, keyboard navigation, realization toggle, clipboard button, docs theme selector, search, and reference links.

For GitHub Pages, after explicit acceptance integrate the candidate and select Settings → Pages → GitHub Actions. The workflow publishes subsequent successful main-branch builds. Local commands do not verify hosted permissions or deployment.
