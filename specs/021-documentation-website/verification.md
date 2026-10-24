# Website candidate verification and handoff

**Source candidate:** `febfa8d5113ea29228597f2b7b6f9dad021c99f2` on `021-documentation-website`.
**Base platform revision:** `64ff9d3eb3c7f8c74e745dbcaf25b91bcfca1aae`.
**Status:** locally implemented and reviewed; user acceptance, main integration, hosted workflow execution, and publication pending.

## Delivered scope

Custom responsive home page; 20 authored documentation topic pages plus a 404 page; 13 generated CLI/schema/profile/example pages; public Python and C++ references. The final assembled site contains 567 HTML pages, of which 411 content pages enter the shared Pagefind index.

Canonical source schemas, public declarations/docstrings, CLI definitions, and actual example files drive reference generation. Narrative guides remain reviewed source. A prepared GitHub Actions workflow checks pull requests and publishes only successful main builds once Pages is enabled.

## Exact-candidate checks

All commands below succeeded against the source candidate. `evidence/verification.json` retains argument arrays, tool/environment identities, exit status, duration, log hashes, artifact inventory hash, manifest hash, and browser/screenshot identities.

| Check | Outcome |
| --- | --- |
| Fresh `npm ci` and frozen uv documentation environment | Passed. |
| Generator contract suite | 9 tests passed, including source mutation, cleanup, missing input, broken anchors, and publication cache rejection. |
| Root-domain build, `BASE_PATH=/` | Passed; zero internal link/anchor/publication errors. |
| Project build, `BASE_PATH=/xverse-platform/` | Passed; 567 HTML pages and 29,596 checked local links. |
| Publication manifest | 194 source hashes verified; source revision matches the exact candidate. |
| Public XDL graph / experiment fixture / home snippet | Validated / compiled / validated without a runtime workload. |
| Public artifact scope | No build caches, private/local HTML paths, or verbatim header-source views. |
| Browser checks | Keyboard skip/search, Python/C++ search results, clipboard, illustration controls, light/dark themes, mobile menu, 390px layouts, and native return navigation passed with no observed errors/failed requests. |
| Separate reviews | All six findings closed; final read-only exact-revision audit passed. |

Tools: Node 22.23.4, npm 10.8.2, uv 0.12.17, Doxygen 1.9.1, Sphinx 8.2.3, Chromium 156.0.8078.4. The task used a portable Node installation to avoid changing the system Node. CI installs its declared tools independently; hosted execution is not claimed.

Final manifest SHA-256: `f83ad7bfb63007498ecc1ab004a6a1234039204014f55d459f38b97f87ba6c71`.

## Local artifacts

- Static website: `website/dist/`.
- Portable archive: `build/website/xverse-website.zip` (3,517,304 bytes; SHA-256 `982dfc8032df2dd5119339c97f64d2859569c5185b9f2326938a325aa6f3dbf7`). Extract and serve its containing directory; the site is under `xverse-platform/`.
- Browser screenshots: `build/website/screenshots/`, with hashes in the evidence report.
- Source/build/maintenance instructions: `website/README.md`.

Generated output and local QA artifacts are intentionally ignored. Evidence-only records added after the source candidate do not change any website, workflow, or ADR input. The final artifact remains bound to the source candidate above.

## Remaining acceptance and hosting steps

The repository requires explicit acceptance of inspected artifacts. After acceptance, integrate the exact candidate into `xverse-platform/main`, verify the assembled platform documentation build, and enable GitHub Pages with GitHub Actions. The configured destination is `https://the-xverse.github.io/xverse-platform/`; it is not represented as live.

No runtime API, schema, legacy repository, production workload, or existing local main-worktree file was changed. Runtime regression execution is not applicable to this documentation-only change; the checks above establish documentation behavior and offline example consistency only.
