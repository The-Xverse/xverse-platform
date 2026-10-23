# Review log: Thesis Lite stabilization S1b (graceful stop, stderr capture, marker readiness probe)

The thesis increment is S1, `specs/029-lite-stabilization` (FR-009 to FR-013; tasks S1-T07 to S1-T12; author
decision S-D2, approved on 2026-10-23).
- **Branch.** `candidate/lite-stabilization-s1b-20261023`, from the S1a-2 candidate head `d8b44719c`. That head
  is not merged; S1b is rebased onto the merged S1a-2 before its own acceptance.
- **CAPA.** S1b is CAPA step 11, because S1a-2 takes step 10. Each finding is recorded here before its repair or
  implementation.

1. **S1-T07: the amended as-built limits (FR-012, S-D2). Written at 19:35:53 2026-10-23, before any S1b code.** The
   frozen texts stay as written. Each is superseded here and in the thesis record
   `specs/024-maestro-lite-lifecycle/review/amendment-s1b-as-built-limits-20261023.md`, from the S1b merge on.
   - **A1, DV04 n0.**
     - Frozen text (as-built reconciliation 2026-10-21, line 55, and C4 in `review-affa19.md`): "no
       application-level probe exists".
     - Amendment: an observe action may declare one admitted application probe, the nonce marker probe (FR-011,
       S-D3). `running` remains the default. Periodic health stays liveness-only, and unchanged units stay
       liveness-only.
     - DV04 n0 then becomes a positive case for a marker that never appears (`ML-PROBE-NOT-READY`), and a negative
       case for a marker that appears late but within the bound.
   - **A2, DV06 n5.**
     - Frozen text (line 57, C4, and `review-affa19.md` about line 565): "no SIGTERM is delivered to workloads".
       Workload teardown goes straight to `cgroup.kill`.
     - Amendment: a unit stop on the owned path may send SIGTERM through the pidfd before the freeze, wait up to an
       admitted grace inside the existing ≤ 5 s per-unit budget, and then freeze and kill as before (FR-009). The
       STOPPED record states whether the unit exited on TERM or was forced.
     - DV06 n5 then becomes the case of a unit that ignores TERM and is forced.
     - The cancel path, the Phase 5 `crash` fault, the emergency path and the cleanup path stay SIGKILL.
   - **A3, `ADR-ML3-TEARDOWN-0001` line 15.**
     - Frozen text: "This component does not add an arbitrary graceful application stop callback."
     - Amendment: there is still no arbitrary callback. The only addition is the admitted, bounded SIGTERM grace
       of A2, with no application code run by Maestro.
   - **A4, `ADR-ML3-LAUNCHER-0001` lines 42–43.**
     - Frozen text: the stub "redirects standard streams".
     - Amendment: stdin and stdout stay on `/dev/null`. fd 2 may be a declared, run-scoped, size-capped stderr
       file, created `O_CREAT|O_EXCL` without following links (FR-010). It is a private artifact, not exported.
     - `inheritedHandles: closed` means that no control descriptor is inherited.
   - **A5, `ADR-ML3-PERSISTENCE-0001` lines 31–35 (in-flight cancel).** Already amended as S1a-1, which is merged.
     It is listed here for completeness and gets no further change.
   - **The design decisions follow as ADR amendments, before the code:** the protocol and recipe form, the
     paths covered, the cap mechanism and the probe placement.
