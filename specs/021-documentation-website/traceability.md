# Requirement and verification traceability

| Requirement | Implementation | Verification |
| --- | --- | --- |
| FR-001 | `website/src/pages/index.astro`, styles, Search component, Starlight configuration | Browser keyboard, search, theme, navigation and mobile checks in `browser-check.cjs`. |
| FR-002 | 20 authored topic pages under `website/src/content/docs/docs/` | Navigation/schema validation, artifact links, content-map inventory, read-only maturity review. |
| FR-003 | Public-export Sphinx generation and public-header Doxygen configuration | Warning-as-error builds; real signature/docstring mutation test; native reference browser traversal. |
| FR-004 | `generate.py` schema, CLI, and example generation | Schema mutation/nested-field test, nested CLI discovery test, actual example validation/compilation. |
| FR-005 | Input map resolution, SHA-256 publication manifest, package and hosting metadata | Missing/changed narrative-input tests; full hash comparison in review. |
| FR-006 | Fail-closed generator and `check_site.py` | Broken anchor/base escape, missing source, cache rejection tests; zero errors in full artifact checks. |
| FR-007 | `.github/workflows/website.yml` | Source review of triggers, dependencies and job permissions; local build commands. Hosted execution pending. |
| FR-008 | Explicit package/header/schema/profile inputs and curated narrative | Read-only scope review; private-path and build-cache rejection; artifact inspection. |
| FR-009 | `BASE_PATH`, `SITE_URL`, remark URL rewriting, generated navigation | Root and project builds; browser search-prefix checks. |
| FR-010 | Documentation maintenance guide, status page, contribution guide | Separate narrative/maturity review. |

## Build unit specifications

- **Generator:** inputs are the reviewed source map and admitted code/schema roots. Outputs are replaced generated directories and a hashed manifest. A missing input, bad schema, failed validation, missing tool, or failed subprocess returns nonzero. It does not invoke providers.
- **Schema rendering:** preserve raw definitions, exact pointers, local required lists, and complete schema JSON. Do not infer merged semantics from compositions.
- **CLI discovery:** enumerate parser subcommands recursively and capture help-only output. The Argus adapter accepts its documented usage-only exit 2, not a workload invocation.
- **Publication checker:** resolve local URLs within the effective base, require files/anchors, reject caches and local/private host paths, and require reference/search outputs. Any error prevents deployment.
- **Browser layer:** home controls are illustrative only; clipboard copies CLI help. Search loads a static index. Native references expose return navigation and readable narrow-screen content.

## Compatibility, SADS, and runtime

No runtime API, resource schema, dependency allocation, or legacy repository changes occur. Adjacent REF-002 IDs and unchanged owner dispositions are recorded in `research.md`. No runtime requirement is satisfied by this website. Validation is bounded to documentation behavior and offline example consistency; it does not establish live integration, production readiness, or a final Lite release.
