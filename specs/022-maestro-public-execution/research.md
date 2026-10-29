# Baseline inspection and decisions

The selected platform's top-level Maestro surface exports preparation only.
RuntimeService is a candidate trusted-host facade whose RuntimeSubmission requires
_OriginalRuntimeRun. Its release record keeps the service closed to the blueprint.
The Studio integration cannot construct that private object or self-approve reviews.

Public Argus EvidenceStore.open_run/read_run/read_records are installed in the
same pinned distribution. The manifest field plan.semanticDigest stores the
compiled plan digest; Studio separately tracks its input-semantic digest. These
names must not be conflated. Argus recorded and assessed statuses are separate.

Native C++ X-COM exposes provider, observation, local-IPC ToolGateway and optional
gRPC interfaces. Existing generated descriptors and libraries must be pinned and
verified; a Python Lite-flow record is not native-core evidence. Payload policy,
validation session and provider permissions remain authoritative.

Decision: add a separately specified public host/provider execution boundary;
retain all existing closed/runtime approval semantics. Reuse accepted public XDL,
Maestro preparation where compatible, actual Argus storage and native X-COM APIs.
A narrow fixed preset which generates different XDL is insufficient for Studio.

Additional inspection: existing prepare_lifecycle is component-instance/simulation-
clock/closed-provider only; it cannot directly run the current declared devices and
host-clock demo. The new capability must retain that boundary and provide explicit
public device/host-provider execution semantics. See the detailed design; a neutral
native fixture is verification support, not replacement of the current demonstration.
