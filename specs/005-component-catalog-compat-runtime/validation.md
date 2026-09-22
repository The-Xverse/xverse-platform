# M3 implementation validation record

**Date**: 2026-09-20
**Scope**: Design, T005–T017 platform/isolated-fixture implementation, T018 companion design package,
runtime Profile v0.2, and the blocked SD-0001 selected-component candidate graph and assessment.
**Result**: Pass for the implemented prototype and repaired companion-design scope; legacy selection,
provider implementation, and execution remain gated.

## Completed documentary checks

- Spec Kit feature pointer resolves this M3 package and required planning artifacts exist.
- Specification quality checklist has no unresolved clarification marker or template placeholder.
- M0 R01–R05 and capability 004 boundaries are mapped into M3 requirements, assumptions, analysis,
  tasks, and acceptance gates.
- ADR-0014 and ADR-0015 define the accepted catalog and lifecycle safety decisions.
- M3-R01–M3-R07 are resolved in the normative specification, five contracts, task coverage, and ADRs.
- FR-001–FR-035, T001–T023, and ACC001–ACC019 are contiguous; all local links resolve, and the
  marker, trailing-whitespace, and public-safety pattern scans pass across the 19 M3 review files.
- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` resolves
  `specs/005-component-catalog-compat-runtime` and reports every required design artifact.
- Implementation review M3-I01–M3-I09 was recorded before repair; the subsequent repair and re-review
  leave no unresolved BLOCKER or MAJOR finding.
- The complete suite passes 90 tests, including 22 M3 catalog/lifecycle tests, four SD-0001 validator
  tests, and all 64 earlier XDL tests. Python compilation, `uv lock --check`, and the Spec Kit
  prerequisite check pass. Within the
  restricted agent filesystem, uv's cache is redirected to writable `/tmp`; the lockfile resolves
  package version 0.4.0.
- `uv build` produces the 0.4.0 source archive and wheel; both include runtime Profile schemas v0.1
  and v0.2, preserving the fixture contract while packaging declared-blocker support.
- `scripts/validate_m3.py` derives one entry and deterministic plan, records eight durable fixture
  evidence events, completes `running → running → stopped → cleaned`, and reports
  `legacyExecution:false`.
- The separately reviewed `xverse-compat` T018 design imports the exact provider ID/kind and
  process-action boundary from platform API `0.4.0`; its initial two BLOCKER, two MAJOR, and two MINOR
  findings are resolved with no new BLOCKER or MAJOR finding.
- The authorized companion conformance pass adds an exact package/content pin, explicit composition
  root, and in-memory fixture. Its 17 tests prove C01–C14 without a subprocess or legacy target; its
  separate implementation review resolves three MAJOR and three MINOR findings.
- Documentation and implementation complete no legacy selection and start no legacy or production
  process. Companion-repository changes add a target-specific contract candidate and review while
  keeping provider implementation blocked.
- SD-0001 nominates the revision-pinned `zenoh2someip_bridge` gateway for owner review because it is a
  narrow reusable process boundary. Review 008 originally recorded three BLOCKER, two MAJOR, one
  MINOR, and one ADVISORY finding. The authorized reproducible build resolves the missing-artifact
  BLOCKER and adds one MAJOR vendor-binary/environment finding. Two BLOCKER, three MAJOR, one MINOR,
  and one ADVISORY finding were open before the candidate graph pass; T019 and ACC015 remain open.
- User-requested architecture self-review accepts the candidate nomination while rejecting completion
  of the selection gate. It resolved two document-quality MAJOR findings and one MINOR finding by
  expanding the alternatives analysis, preserving retained evidence during cleanup, and clarifying
  the maturity label. The candidate graph later resolves SD-R02; external findings SD-R03–SD-R06 and
  SD-R08 remain open.
- The subsequent build-only authorization produced a byte-identical gateway from two distinct frozen
  source paths and a deterministic candidate archive. The gateway, archive, source/LFS dependencies,
  configuration, toolchain, and external CMake overlay are digest-pinned in public-safe evidence.
  No built executable was run, the legacy checkout stayed clean, and the archive is excluded from Git.
  Runtime Profile v0.2 and four candidate XDL resources now validate as one exact catalog identity and
  yield deterministic blocked plan digest
  `sha256:ccab18b9980cae1be7537cd13be9f3cbd5b2a0e6a3ddae33a3a98a8560a699cf` without execution.
  Environment identity, owners, lifecycle/interface contracts, durable artifact retention, and
  vendor-binary disposition remain unresolved.
- The separate candidate-XDL architecture review reports no unresolved document/code BLOCKER or MAJOR;
  seven plan blockers continue to represent the external decision gaps.
- `scripts/validate_sd0001.py` verifies the candidate lock, resource/schema digests, exact identities,
  plan digest, and blocker set without lifecycle action. Negative tests reject digest drift, path
  traversal, and symlink escape with stable public-safe failure. The closure packet maps every blocker to required public
  and restricted evidence and preserves the REF-001/current-launcher startup-order disagreement.
- The separate closure-readiness review passes the implementation for evidence intake. Its CL-R01
  external MAJOR remains open until the target owner resolves the startup prerequisite/readiness
  contract; this does not weaken the currently blocked plan.
- Read-only static inspection of the frozen SD-0001 source/configuration produces a digest-pinned
  machine summary and public interface audit without execution. It narrows the contract to six routes,
  selected transformation classes, vsomeip 3.6.1, UDP discovery, and unreliable events while exposing
  a compiled private endpoint, native float ABI, payload-bearing logs, detached work, absent graceful
  stop/readiness, unknown Zenoh semantic version, and missing peer tools as unresolved limits.
- The separate static-interface review accepts the audit/projection quality but keeps SI-R01 BLOCKER,
  SI-R02–SI-R04 MAJOR, SI-R05 MINOR, and SI-R06 ADVISORY findings open. They map to the existing seven
  plan blockers and authorize no target code or execution.

## Deferred validation

No legacy adapter, completed selected-component decision, compatibility proof, application parity evidence,
production-readiness evidence, or cross-process production runtime exists. The process provider's
isolation attestation is declarative and does not replace an OS sandbox. A wheel build was not run
because this workspace's environment lacks pip/hatchling build frontends; imports, CLI tests, source
compilation, and locked-source tests pass.

## Review gate

Completing selection requires the closure-packet evidence and owner review of SD-0001 findings, then T019–T021, a
separately reviewed provider, and exact execution authorization. Final M3 and M4 acceptance remain
human decisions.
