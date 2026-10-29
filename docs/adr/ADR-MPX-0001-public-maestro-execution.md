# ADR-MPX-0001: Public host-bound Maestro execution

Status: implemented public platform boundary accepted by the user on2026-10-29;
actual Studio/Autoverse integration remains open. See capability022 acceptance decision.

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

## 2026-10-29 platform-first sequencing clarification

The initial task chain put MPX-T07 (actual Studio/Autoverse integration) before
MPX-T10 (platform acceptance/main), conflicting with the existing platform-first
rule and Studio's requirement to consume admitted platform APIs. Preserve all
task/requirement IDs and the overall goal; allocate T06 to actual neutral native
X-COM/public-Maestro/Argus contract verification, then T08/T09 platform verification
and review, T10 explicit user acceptance/exact main integration, then T07 the actual
Studio/Autoverse three-view demonstration. T07 remains required and cannot be
satisfied by the neutral native test. No automatic acceptance or permission to
change legacy sources follows from this sequencing correction.

T02–T05 implementation evidence covers the bounded Linux host-provider prototype,
not admission of every future provider. Concrete provider semantics, installation
and permissions require their own actual verification under T06/T07. The capability
as a whole remains incomplete until all its tasks and the overall live goal pass.
