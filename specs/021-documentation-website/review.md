# Separate read-only review and repair record

## Candidate 1 — 2026-10-24

Reviewer: independent `documentation_inventory` research/review agent, read-only. Reviewed source identity is recorded in `evidence/reviewed-candidate-1.json`. Review preceded the repairs below; acceptance remains pending.

### W-DOC-001 — MAJOR — Build caches enter the publication

At candidate-1 `website/scripts/generate.py:248`, Sphinx has no separate doctree directory. Its output contains `.doctrees/environment.pickle` and six doctree files, copied into the built static artifact. The pickle contains local build paths. `check_site.py` only scans HTML, so its public-boundary check misses those files.

Required repair: put doctrees under ignored `website/reference/_build/`, remove `.buildinfo`, and make artifact checks reject build caches/pickles. Verify a negative cache-artifact case and inspect the rebuilt artifact. Initial root/subpath builds passed link checks but do not support a public-safe-artifact claim because of this finding.

### W-DOC-002 — MAJOR — Manifest omits declared inputs and hosting values

Candidate-1 `generate.py:275` hashes `content-map.json` without resolving/validating its narrative source entries. Mapped release/concept/versioning/ADR/license sources are omitted, along with the favicon, namespace facade, tsconfig, and effective hosting environment values. Missing mapped inputs therefore do not fail the build.

Required repair: validate and hash every declared narrative file, explicitly expand admitted header directories, include publication/build inputs, and record `BASE_PATH`/`SITE_URL`. Test missing-input rejection and changed-input hashes.

### W-DOC-003 — MINOR — Home example should share a validated source

Implementer browser/content review: home-page XDL is an independently authored literal rather than an included validated source file. Move it to a standalone checked example and include it at build time to prevent future drift. Add a test that proves Python docstring/signature changes reach generated HTML, plus stale-output cleanup coverage.

### Observed checks before repair

Root and project-base builds: 584 HTML pages, 37,028 local links checked, 428 indexed pages. Five generator tests pass. Browser checks: home realization buttons and clipboard work; desktop/mobile home and docs have no horizontal overflow; guide and Python API search results use the correct root/project URLs; no observed browser errors or failed requests. These observations do not clear W-DOC-001/002.

CI source review found no additional issue with PR/deploy permission separation, offline-only build scope, public package selection, or Lite maturity. Hosted CI/deployment remains unverified.

## Repair successor

Independent repair review closed W-DOC-001/002/003: no cache artifacts, all 194 manifest input hashes match source, hosting is recorded, and the home snippet is a validated file. Nine contract tests and the project build pass. Source identity: `evidence/reviewed-candidate-2.json`. Root build also passed after repair.

## Native reference browser review

### W-DOC-004 — MINOR — Python return link executes before the body exists

Browser traversal of the actual Python API page shows its return link script is loaded in the document head. The script calls `document.body.prepend` before the body exists, so the return link is absent. Record before repair: wait for DOMContentLoaded and verify both native references and return navigation in a browser.

### W-DOC-005 — MINOR — Doxygen still publishes verbatim header views

The rendered C++ header page exposes “Go to the source code” despite `SOURCE_BROWSER=NO`, because Doxygen's independent `VERBATIM_HEADERS` default remains enabled. The design excludes implementation/source browsing. Record before repair: disable verbatim headers, rebuild and check that no header-source HTML remains.

No acceptance or hosted publication has occurred.

### W-DOC-006 — MINOR — Long Python annotations overflow narrow screens

At a 390px viewport, one Argus signature contains an inherited Sphinx `span.pre` nowrap rule and expands the page to 584px. Record before repair: allow signature fragments to wrap, then repeat native API mobile and return-navigation checks. The C++ reference measured 390px without overflow and both repaired return links work without browser errors.

## Final scoped review and browser confirmation

Independent read-only review closed W-DOC-004/005/006 with no new findings. Built JS/CSS match the repaired source; public C++ output contains zero `*_source.html` pages. Subsequent browser checks confirmed both return links, 390px-wide Python/C++ pages without horizontal overflow, home controls/clipboard, keyboard skip/search, cross-language search results, theme switching, and mobile menu navigation. No browser errors or failed requests were observed. The repeatable QA script is `browser-check.cjs`; final command records and screenshots are identified by the verification evidence.

All six recorded findings are closed for this candidate. Hosted CI/deployment and explicit user acceptance remain unverified; no merge or publication is recorded.
