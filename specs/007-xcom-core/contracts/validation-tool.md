# Contract: X-COM validation-tool boundary

The tool boundary supports external validation behavior without granting an unrestricted alternate
publisher or service-provider path.

## Session lifecycle

1. validate and consume one exact local validation permit;
2. arm allowed actions and reserve bounded resources;
3. accept requests only while the session is active and within quota;
4. persist intent before routing an accepted stimulus;
5. emit and observe a bounded outcome;
6. revoke/expire, drain, and close all exact session-owned handles.

## Actions

- inject one declared signal/state update;
- inject one declared message/event;
- invoke one declared service operation;
- emulate one explicitly allowed service endpoint for the session.

Every request includes tool/session identity, target contract and endpoint, schema/version, typed input,
origin, correlation/causation, schedule and clock domain, and quota cost. Immediate requests are
explicitly labeled. Scheduled requests define ordering and late behavior.

The boundary rejects before emission when authorization, plan digest, identity, schema, direction,
action, time, quota, service ownership, or loop policy fails. Rejection and unknown outcomes are
evidence. Domain-specific diagnostic workflows, test languages, remote authentication, and proprietary
tool APIs belong in adapters or later capabilities.

