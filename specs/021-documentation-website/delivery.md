# Accepted website integration and publication

The user accepted the reviewed candidate and authorized integration and GitHub Pages publication by replying **“yes”**. The accepted artifacts were merged into `xverse-platform/main` at `1fe5e5638cb5a82118fd2c2fdef8c32ad0235b56` after verification in an isolated worktree. The five pre-existing untracked local files were preserved byte-for-byte.

**Public website:** https://the-xverse.github.io/xverse-platform/

**Published source:** `db4ad46584b070c167e3e0afff43eee2f2220883`.

**Successful hosted workflow:** https://github.com/The-Xverse/xverse-platform/actions/runs/40083648493

## Verification

- The assembled merge passed the contract suite and both root/project-path builds before the initial push.
- A production browser check found the Doxygen language mismatch recorded as W-DOC-007 before repair. Its bounded build-tool repair received a separate read-only review; no runtime behavior changed.
- Eleven contract tests and both hosting-path builds passed locally and in the successor hosted workflow. Its publication gate requires one shared English search index.
- All eight checked public endpoints returned HTTP 200. The public manifest identifies the exact published source revision; all input hashes match the merged repository.
- Production browser checks passed for keyboard skip/search, Python/C++ search results, realization controls, clipboard, theme switching, mobile menu/navigation, 390px layouts, and native API return links. No browser errors or failed requests were observed.
- HTTPS is enforced, GitHub Pages uses the workflow build type, and the repository homepage metadata links to the site.

Evidence is under `evidence/integration/`, with the compatibility repair's local checks and reviewed source hashes under `evidence/search-repair/`. Historical candidate and initial-publication observations are retained as revision-specific evidence rather than rewritten as successful successor checks.

## Ongoing updates

Main-branch source changes trigger the documentation workflow automatically. Public API signatures/docstrings, C++ comments, schemas, command definitions, and example files generate their references; narrative guides and maturity claims remain reviewed source.

The final evidence-only commit changes no publication inputs and uses `[skip ci]` to avoid an identical redeployment. The hosted manifest remains pinned to the tested source revision above. All seven recorded review findings are closed. This delivery makes no runtime, production-readiness, or scientific-validity claim.
