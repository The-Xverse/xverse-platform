# Research and boundary assessment

## Decisions

- Astro + Starlight provides the requested custom home page and Markdown documentation, with static search and no paid hosting dependency. Official references: https://starlight.astro.build/guides/pages/ and https://docs.astro.build/en/guides/deploy/github/ . Docusaurus was considered; built-in version snapshots are not required for the first publication.
- Reuse the repository Doxygen aliases but override publication inputs to public headers only. Existing `Doxyfile` includes tests/scripts/private members and is unsuitable as the public website configuration unchanged.
- Sphinx autodoc documents public `__all__` exports of `xverse_xdl`, Argus, Maestro, faults, and flows. Import only those admitted packages; never recursively import runtime workers. Imports happen during documentation build and must remain side-effect free.
- Schemas are rendered generically with JSON pointers and full JSON downloads, preserving constraints that cannot be summarized in field tables. CLI references use actual help/usage, not manually copied options.
- Public narrative is authored rather than recursively copying `docs/engineering`. The 2026-10-24 release record is newer than the README and establishes bounded Lite implementations of Maestro/Argus/faults/flows; generalized services remain targets. The release is rc.1 with soak pending, not final 1.0.
- Astro 7.4.2 / Starlight 0.42.7 currently require Node >=22.23.4. Use a portable task-local Node for local verification instead of modifying the system installation.

## REF-002 disposition

This capability implements none of the source SADS runtime requirements. Documentation can describe allocated requirements but cannot discharge them. The existing register `docs/architecture/sads-requirements-traceability.json` remains authoritative; documentation/tooling does not alter it. Adjacent allocations XVE-SYS-0159–0178 (product UI), XVE-SYS-0179–0197 (Argus observability), and XVE-SYS-0236–0250 (SDK/extensibility) remain deferred/outside this documentation capability, with their existing runtime owners unchanged. No direct documentation-hosting requirement is established by the register; none is invented here. Public documentation is distinct from an experiment UI or an operational dashboard.

## Authorization and source baseline

User requested a free open source home/documentation website, agreed to code-derived references and automatic updates, then said “go”. Baseline `64ff9d3eb3c7f8c74e745dbcaf25b91bcfca1aae`. Implementation is local in a separate worktree. No production workload, legacy repository write, hosted publication, acceptance, or main merge is implied by implementation completion.
