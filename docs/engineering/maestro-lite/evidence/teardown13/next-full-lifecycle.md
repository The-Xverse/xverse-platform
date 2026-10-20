# Next lifecycle integration — DRAFT engineering handoff

Follow thesis capability 024 in full. Increment 13 supplies reverse unit teardown;
full helper closure and all seven P3 tasks remain open. This note records code
inspection, not a new run admission or scientific parameter.

The next implementation should compose finite automatic host-health supervision,
the prepared complete phase/step schedule and supervised simulation ticks with
normal failure/disposition records and the existing reverse cleanup. A caller-driven
start loop alone does not meet D2/D5. Readiness remains sampled process existence.

Inspect before coding:

- ProcessReadiness.start rechecks all already released units, probes every
  transitive prerequisite twice through DependencyGuard in ReleaseOwner.release,
  performs two original persistence intent revalidations, and allows up to three
  own readiness samples. Admission must budget those actual calls, not just one
  start/probe per unit. With n successfully started units and d(u) transitive
  prerequisites, current worst-case calls through full normal unit teardown are
  1 init + n commits + 2n revalidations + n(n-1)/2 prior-health samples
  + 2 sum(d(u)) prerequisite samples + 3n own samples + 4n teardown records.
  One abort adds one further call; scheduled observe, cadence, failure/disposition,
  coverage and future normal closure require their additional admitted calls.
  A 16-unit chain already exceeds the inherited private 128-request cap without
  periodic health. Derive and freeze the complete admission before any Release;
  reject an inadmissible budget or explicitly revise the bounded private contract.
- A new dispatcher must cap every intervening operation by the next health/lease
  deadline or use independently admitted supervision. Polling only after a slow
  storage RPC returns does not demonstrate cadence. A missed observation closes
  starts and initiates teardown; a missing normal record remains missing.
- Root BootstrapSession renewal and gate renewal are distinct operations. Renew
  original scopes before expiry within the original generation; cancellation is
  irreversible. Do not let a paused tick prevent host health/cancellation.
- Tick callbacks require supervised execution with exact original input/output
  scope and bounded cancellation. Keep simulation, host and UTC domains separate;
  never infer simulation progress from host elapsed time or fabricate tick evidence.
- Dispatch all admitted prepare/start/observe/stop/cleanup steps in their windows
  using combined graph dependencies and deterministic ties. Final-horizon cleanup
  is obligatory. Blocked/never-issued steps need honest normal dispositions and
  applicability evidence; reverse resource teardown does not alone close steps.
- Next integrate full helper shutdown, global epoch cancellation, explicit restart
  and both ordinary versus cleanup-only recovery, U7 provisional/offline coverage,
  U8 confined collection/results and failure-stage writer reporting. Keep normal
  journal facts separate from emergency observations and actual original-child wait.

Retain all 24 ML-SR, 18 unvalidated/null-mapped REF-002 parents, 30 scenario pairs,
90 declared endpoints and nine full runtime cases. Phases 4–9 remain downstream.
Original bootstrap/environment admission, full M1/G1/G3/G4/G5, independent review
and author acceptance remain open. No empirical campaign is admitted by this note.
No canonical-note, main, legacy or scientific change. Sol/high is recommended for
this authority/concurrency integration; cheaper models suit routine receipts.
