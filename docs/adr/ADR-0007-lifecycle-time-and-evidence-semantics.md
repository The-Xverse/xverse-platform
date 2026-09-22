# ADR-0007: Lifecycle, time, and evidence semantics

**Status**: Accepted — user approved M1 architecture review on 2026-09-20.
**Date**: 2026-09-20

## Context

M0 identified uncertain readiness, cleanup, and timing behavior in legacy startup paths. The target
architecture requires lifecycle, time, failure, observability, and reproducibility to be explicit
without falsely asserting runtime support.

## Decision

Adopt four semantic lifecycle profiles: Definition, Binding, Execution intent, and Observation.
Model TimeDomain and Clock explicitly; require cross-domain mappings or tolerances. Model Fault,
Observer, Metric, maturity, provenance, and evidence limitations as first-class semantics. A Failed
state must retain its reason and cannot imply that cleanup or recovery succeeded.

## Consequences and alternatives

Later components can validate intent before execution and report evidence without conflating
declared behavior with demonstrated behavior. An implicit lifecycle inherited from each provider was
rejected because it prevents reproducible cross-provider scenarios.

## Evidence and scope

Guidance sections 22, 30–32, 35–38, and 48; M0 findings R01–R05. This does not define scheduling,
clock synchronization, fault injection, or observability implementations.
