# Nonblocking follow-up from the final read-only pass

14. MINOR identity consistency, open: BootstrapSession.session is initialized from
    the immutable admitted generation but is a public mutable attribute, and its
    holder check does not compare it back to that original value. Pin/reject a
    changed alias in the next source increment and test rejection before dispatch.
    Initial registration already checks the exact original C1 deadline/session;
    native generation/lease bounds and unit-owner/client session checks remain
    enforced. No cross-process adoption, unit Release or readiness is demonstrated
    by changing this label. Do not cite the current helper API as full host-session
    identity validation or full M1 closure.

Keep original-supervisor admission, durable bootstrap-permit authentication and
consumption, exact tested environment/ABI/dependency admission, full owner/guard-loss
M1 and all readiness/lifecycle/evidence/runtime obligations open. This same-agent
component review is not independent full-candidate review or acceptance. Thirteen
earlier findings have successor repairs; this public-label guard remains traceable
without changing bytes under the executing v4 regression.
