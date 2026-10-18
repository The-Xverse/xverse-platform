# ADR-ML3-SUPERVISION-0001 — host monitoring of an original worker

Date: 2026-10-18. Status: partial implementation-candidate decision; not accepted.
Parent: ML3-ADMISSION2-2026-10-18-v2, platform baseline c2997c0.
Scope: part of U3 and ML-SR-009/011/023/024; no new requirements. Ownership,
cleanup and evidence-failure requirements remain constraints, not implemented closures.

The supervisor needs a host-time path that invokes no provider, tick, journal or
telemetry callback. Add a Linux pidfd monitor for an original direct child held by
the original supervisor. It does not create a process, take a coordinator lock,
read child output, call Popen.wait/poll, discover a process, or reconstruct ownership.
The original parent registers the actual Popen object before operation dispatch.
Registration is a trusted integration input, not authenticated bootstrap approval.
It must occur after separately admitted helper creation and before that helper can
receive an operation. This component does not bound helper creation or registration.

Use an irreversible cancellation latch independent of worker work, a real monotonic
clock, retained pidfd identity, nonblocking waitid and finite polling. On timeout or
cancel, send TERM and then KILL only to that retained child, and confirm its exact
exit and reaping. A permission error, lost parent wait ownership, failed observation
or exhausted bound is unresolved. Retain original identity resources on uncertainty.
No signal delivery or exit code proves containment cleanup. Descendants are always
unknown here: successful monitoring never sets lifecycle cleanup or readiness true.

Freeze each operation/TERM/KILL deadline at registration. Calling the monitor late,
copying its object, forking the holder, cancellation or repeat monitoring cannot
extend authority. Cached replies are observations of the same original operation,
not fresh observations or restored ownership. Cancellation takes precedence over
an exit first observed after the latch closed; snapshots include the latch epoch
and the next coordinator must still validate its current epoch before committing.

Python matches the existing control plane. This uses Linux stdlib pidfd/waitid;
unsupported platforms reject. No new runtime dependency or data-plane change.
Host scheduling/kernel faults can exceed test allowances; no hard real-time claim.
The host clock is rechecked before signalling. Userspace cannot atomically enforce
a kernel deadline across preemption after that guard; M1/U4 must supply the actual
facility fence before runtime admission. This monitor cannot substitute for it.
The isolated owner must prevent concurrent reaping and untrusted mutation of its
private registry. Loss of that original holder remains unresolved, with no adoption.

This is one supervisory primitive, not the complete U3 watchdog, AFFA, M1, C1 or U4.
An independently supervised bootstrap/launcher and real exact containment remain
mandatory before process mode. No public start API, ticket, workload or experiment
is admitted. Full 24-requirement trace and the nine ML3 runtime cases stay open.
All 18 REF-002 parents remain allocation-only/unvalidated/null mapped. No acceptance,
merge, canonical-note edit or factory admission follows from this component.

## API references

Python's [pidfd_open](https://docs.python.org/3.13/library/os.html#os.pidfd_open)
returns a process descriptor; [waitid](https://docs.python.org/3.13/library/os.html#os.waitid)
supports P_PIDFD, WNOHANG and WNOWAIT; [pidfd_send_signal](https://docs.python.org/3.13/library/signal.html#signal.pidfd_send_signal)
addresses the retained descriptor. These API contracts do not supply descendant
containment or a launcher lease. Runtime verification uses Python 3.13.13; the online
3.13 documentation was checked as an API reference, not an environment identity.
