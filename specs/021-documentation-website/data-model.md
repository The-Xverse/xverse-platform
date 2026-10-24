# Publication model

- **Source input**: repository-relative path and SHA-256. Only explicit narrative/source/schema roots admitted by the generator are consumed.
- **Reference page**: stable URL, title, input paths, and generator kind. Generated output directories are replaced on each run to remove stale pages.
- **Publication manifest**: format version, Git revision (or `unknown`), package version, source hashes, and generated routes; no absolute paths or timestamps are required.
- **Capability status**: authored description with implementation scope, source record, and limitations. Automatic generation cannot promote a maturity claim.

Build state: inputs checked → references generated → Astro built → search indexed → artifact checked → deployable. Any failed transition ends the command unsuccessfully; CI deployment depends on the complete build.
