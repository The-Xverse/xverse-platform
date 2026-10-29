# ADR-MPX-0001: Public host-bound Maestro execution

Status: proposed implementation decision under user-authorized capability022;
not platform acceptance. See specs/022-maestro-public-execution/plan.md and contracts.

The candidate RuntimeService currently requires a private run type. Add a public
canonical-source/host-provider execution boundary inside Maestro, preserving the
existing private trusted-host runtime and its closed admission gates. The control
plane stays Python; native X-COM remains C++. Use actual Argus persistence and
reader verdicts, shared original identities and explicit correlation. Providers
are fixed trusted-host installations; no project code, industry dispatch or
self-issued legacy review approvals enter this boundary.

A fixed preset that generates different XDL, or a facade which re-labels Studio
process events as Maestro, would not satisfy effective-input or live acceptance.
User acceptance and exact accepted-main integration remain required before delivery.
