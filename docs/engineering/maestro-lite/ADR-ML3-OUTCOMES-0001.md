# Durable start/probe outcomes before scheduled execution

ML3-OUTCOMES12-2026-10-18-v1; parent 89bf5e3. Decision before product code.
Python extends the existing isolated persistence protocol with one closed probe
record request. The original storage child remains the only M3/Argus writer.
It uses FileEvidenceJournal.append/public_records and Argus append_event plus
flush_buffer, without editing accepted storage internals or adding writer kinds.
The existing private v1 framing, credentials, sequence cap 128, per-RPC <=5 s and
original generation remain unchanged. New replies are bounded public receipts,
not capabilities. No callback, shell, file I/O or new process creation is added to
the coordinator operation path.

Every actual ProcessReadiness query is recorded before its result can satisfy
readiness or dependent admission. The first observed running result appends an M3
start outcome and a started annotation, then a separate M3 probe observation and
probe/ready annotations. Pending exec produces a not-ready observation and failed
probe, never a fabricated start outcome. Later samples emit health, and failed
samples health-loss when an actual observation exists. Missing/failed observations
and complete failure-outcome/disposition paths remain downstream; unknown cannot
be converted into an observed success. Samples bind original issued full handle,
unit/generation, catalog observe action, session/time and monotonic sequence.

The client accepts only the exact current observation object of its original
ProcessReadiness facade and issuing launcher. The storage worker independently
checks its genuine intent, derived plan/execution/provider/action, fixed original
handle and increasing sample sequence. It derives dependency parents from the
prepared combined graph and uses only its own acknowledged fresh predecessor
probe receipts in annotation dependencies. Original successful intent and mirror
must remain present; changed or missing history fails closed. Public projections
never carry raw handles, nonces, argv, environment values, PIDs or private paths.

A normal-record write/append/flush failure or timeout closes starts, retains
consumption and exact C1, and cannot return ready. Missing normal records remain
incomplete even when original C1 later completes cleanup. This increment supports
U4/U5/U7 partially; automatic health/tick scheduling, normal stop/cleanup, reverse
teardown, restart/recovery, dual coverage/collection, full bootstrap/admission/M1
and all nine runtime cases remain open. No acceptance, merge or factory run.

Trace: ML-SR-005/007/008/009/012/016/017/018/019/024 supporting partial mappings;
all 24 ML-SR and 18 allocation-only REF-002 parents retained, never closed by this
component. Source semantics remain unvalidated. External thesis 024 governs this
continuation; main prerequisite detects unrelated 020. No extension hooks exist.
Sol/high is recommended for lifecycle/evidence authority; cheaper models fit receipt
processing. This is engineering judgment, not measured cost or a model switch.

## Amendment S1a-2: per-operation mirror check without a per-event full re-parse (2026-10-23)

This is thesis specs/029-lite-stabilization FR-002/FR-003, decision S-D7. The rule "original successful
intent and mirror must remain present; changed or missing history fails closed" is unchanged, and it is
still checked on every operation, with these changes:
- **Argus mirror check.** It uses `EvidenceStore.read_records` with a checkpoint (Argus design section
  8.6). Every check re-hashes the whole already-verified stream prefix and scans only new bytes with the
  frozen acceptance rules. Any changed byte, identity or manifest triggers a complete `read_run`.
- **Event comparison.** Expected event fields are compared again only when the expected object or the
  accepted record object changed; a complete read produces new objects, so everything is compared.
- **M3 journal reload.** It re-reads the whole file, re-hashes the verified prefix, and parses only new
  lines.
- **Tamper tests.** The existing tests (`test_outcomes.py`) are unchanged. New tests cover same-size
  rewrites, truncation, replaced files, foreign appends and manifest changes.

