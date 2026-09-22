# X-Verse vNext domain-neutral metamodel

**Status**: Approved M1 architecture; user approval recorded on 2026-09-20.
**Date**: 2026-09-20
**Authority**: This document refines the approved [architecture guidance](XVERSE_VNEXT_ARCHITECTURE_AND_CODEX_GUIDANCE.md). It does not replace it, implement XDL, or establish a runtime API.

## Purpose and scope

This is the stable semantic vocabulary from which a future XDL semantic model can be derived. It
describes a multi-industry cyber-physical system, its realization, and an experiment that observes
or perturbs it. A term is a semantic concept, never an instruction to start a process, contact a
device, or create a deployment.

The core contains no industry-specific roles, protocols, equipment classes, or simulator brands.
Those belong to a declared profile, compatibility adapter, or blueprint. M1 excludes serialization,
schema shape, custom syntax, runtime planning, catalog entries, credentials, addresses, provider
plug-ins, and executable adapters. Those are M2 or later work.

## Normative conventions

- **Identity** is a stable, namespace-qualified semantic identifier. It must not be an address,
  process identifier, container name, or provider-local handle. Its XDL syntax is deferred to M2.
- **Metadata** includes a human-readable name, description, version where owned, and provenance.
  Metadata never changes semantic identity.
- **Logical identity** describes what the system is. A **realization** describes how it is made
  available in one environment. Several deployments may realize one logical identity.
- **Extension** means a declared namespace/profile that adds attributes or relationships without
  redefining a core term’s identity, required relationships, or validation rule.
- **Evidence** records provenance, maturity, assumptions, and verification state. A declared model
  or artifact is not evidence of successful execution.

### Lifecycle profiles

| Profile | States | Meaning |
|---|---|---|
| Definition | Draft → Declared → Validated → Retired | A design-time object is authored, referenceable, semantically checked, or no longer offered for new use. |
| Binding | Unbound → Resolved → Bound → Superseded | A logical reference has no realization, eligible candidates, a selected environment binding, or a replacement. |
| Execution intent | Requested → Prepared → Ready → Active → Quiescing → Stopped, or Failed | A proposed lifecycle contract, not an M1 runtime implementation. |
| Observation | Planned → Collecting → Finalized → Invalidated | An observation definition is ready, gathers evidence, records a final result, or records why its result is invalid. |

A concept may omit states that do not apply, but cannot report a later state without satisfying the
earlier state’s validation conditions.

## Model layers and relationship rules

| Layer | Concepts | Question answered |
|---|---|---|
| System | System, Component, Node, Device, Sensor, Actuator, Interface, Endpoint, Flow, Network, Link, Protocol, Model, Parameter | What exists and how can it exchange meaning? |
| Realization | Artifact, ExecutionTarget, Simulator, ComputeResource, Resource, Deployment, TimeDomain, Clock | How is the logical system bound in an environment? |
| Experiment | Scenario, Fault, Observer, Metric | How is a declared system exercised, observed, and evaluated? |

System concepts may reference realization concepts only through a Deployment or explicit binding.
Experiment concepts may select declared logical objects and deployment bindings, but cannot alter
their identity. Profiles may specialize core concepts; core concepts cannot depend on profiles.

## Core concept catalogue

Each entry provides purpose, identity/lifecycle, required and optional attributes, relationships,
validation, and extension strategy. Required attributes are semantic requirements; their eventual
YAML or JSON spelling is deliberately unspecified.

### System

**Purpose**: named logical boundary of a cyber-physical composition. **Identity/lifecycle**: stable
system identifier; Definition profile. **Required**: metadata, composition root, provenance, and
maturity. **Optional**: requirement references, tags, Parameters, default TimeDomain. **Relations**:
owns or references Components, Nodes, Devices, Interfaces, Networks, Models, Parameters; is selected
by Scenarios and realized by Deployments. **Validation**: contained identifiers are unique and every
relationship resolves; realization-only values are prohibited in the logical definition.
**Extension**: profiles add roles to contained elements, never change System ownership.

### Scenario

**Purpose**: repeatable declaration of how a System is exercised and assessed. **Identity/lifecycle**:
stable scenario identifier; Definition and Observation profiles. **Required**: target System,
initial condition, stimuli/steps or references, and expected observations. **Optional**: selection
criteria, Parameters, Faults, resource limits, replay evidence. **Relations**: selects Deployments,
targets Faults, and contains Observer/Metric references. **Validation**: all targets are admissible
for the System; every stimulus and observation has a TimeDomain interpretation; unresolved bindings
block Ready. **Extension**: profiles add stimulus and assessment kinds in their namespace.

### Component

**Purpose**: logical capability with declared behavior and interfaces; not a repository, process, or
container. **Identity/lifecycle**: stable component identifier; Definition then Binding profiles.
**Required**: capability role, interface declarations, provenance/maturity. **Optional**: Model,
Artifact, Parameters, Resource requirements. **Relations**: may be hosted by a Node, use Devices,
expose Endpoints, and be bound by a Deployment. **Validation**: endpoints conform to interfaces; no
undeclared resource or incompatible artifact is referenced. **Extension**: profiles define capability
roles and configuration attributes.

### Node

**Purpose**: logical participant or composition point grouping capabilities and interaction roles.
Core roles are compute, sensor, actuator, gateway, and composite. **Identity/lifecycle**: stable node
identifier; Definition profile. **Required**: one or more core or profile roles. **Optional**:
Component/Device references, Parameters, Resource requirements. **Relations**: hosts Components,
represents Devices, owns Endpoints, participates in Flows. **Validation**: a composite has non-empty
containment; hosted capabilities are local or explicitly imported. **Extension**: profiles add roles
without renaming or weakening the core roles.

### Device

**Purpose**: logical cyber-physical thing whose identity can survive simulated, virtual, physical,
or hybrid realization. **Identity/lifecycle**: stable device identifier; Definition then Binding.
**Required**: capabilities and supported realization classes. **Optional**: Sensor, Actuator, Model,
Artifact, calibration Parameters, owner. **Relations**: can be represented by a Node, realized via
Deployment, and produce/consume Flows. **Validation**: logical identity embeds no provider address;
a physical binding resolves an external asset before Ready. **Extension**: profiles add equipment
semantics without changing realization classes.

### Sensor

**Purpose**: role that produces observations of a phenomenon or state. **Identity/lifecycle**: stable
sensor identifier; Definition then Binding. **Required**: observed semantic quantity and output
Endpoint. **Optional**: sampling intent, uncertainty/fidelity, calibration Parameter, Device.
**Relations**: role of a Device or Node; produces Flows and may use a Model. **Validation**: output
schema and units are declared; claimed fidelity has evidence or a target/unknown label.
**Extension**: measurement taxonomies live in profiles.

### Actuator

**Purpose**: role that accepts a command and affects a declared target or state. **Identity/lifecycle**:
stable actuator identifier; Definition then Binding. **Required**: controlled semantic quantity and
input Endpoint. **Optional**: limits, safety constraints, calibration Parameter, Device.
**Relations**: role of a Device or Node; consumes Flows and may be constrained by Faults.
**Validation**: command input matches the controlled quantity and declared limits. **Extension**:
command semantics live in profiles.

### ComputeResource

**Purpose**: declared computational capacity required or offered for realization. **Identity/lifecycle**:
stable resource identifier; Definition then Binding. **Required**: capability class and capacity or
constraint semantics. **Optional**: affinity, acceleration capability, availability, isolation.
**Relations**: specializes Resource; requested by Components/Deployments and offered by
ExecutionTargets. **Validation**: capacity units and sharing policy are explicit; binding cannot
exceed a hard limit. **Extension**: providers add capability attributes without changing allocation
meaning.

### Interface

**Purpose**: semantic contract for an interaction, independent of transport or endpoint location.
**Identity/lifecycle**: stable interface identifier; Definition profile. **Required**: direction,
payload contract, compatibility policy, owner. **Optional**: unit conventions, quality constraints,
version range, conversion policy. **Relations**: exposed through Endpoints, carried by Flows, bound
to Protocols. **Validation**: payload and direction are defined; incompatible versions require an
explicit converter/binding. **Extension**: profiles add contract semantics.

### Endpoint

**Purpose**: named interaction point on a Component, Node, Device, or external boundary.
**Identity/lifecycle**: stable endpoint identifier in its owner namespace; Definition profile.
**Required**: owner, direction, Interface. **Optional**: multiplicity, discovery intent, readiness
condition, quality constraints. **Relations**: sources or sinks a Flow; may bind to a Link.
**Validation**: exactly one owner and interface; direction matches every attached Flow.
**Extension**: discovery details belong in bindings, not the core endpoint.

### Flow

**Purpose**: directed semantic transfer between source and destination Endpoints. **Identity/lifecycle**:
stable flow identifier; Definition then Binding. **Required**: source, one or more destinations,
Interface, delivery intent. **Optional**: ordering, latency/freshness intent, transformation,
TimeDomain. **Relations**: uses Links, Networks, Protocol bindings, and may be observed.
**Validation**: endpoint direction and interface compatibility agree; timing is meaningful in the
selected TimeDomain. **Extension**: profiles add message semantics through Interfaces or declared
transformations.

### Network

**Purpose**: logical communication domain containing Links and common capabilities. **Identity/lifecycle**:
stable network identifier; Definition then Binding. **Required**: scope and connectivity/capability
declaration. **Optional**: topology, quality policy, segmentation, Resource reference.
**Relations**: contains Links and is selected by Flows. **Validation**: every Link belongs to one
Network; a selected Network meets a Flow’s requirements. **Extension**: concrete technologies remain
profile or provider bindings.

### Link

**Purpose**: logical connection between two or more Endpoints in a Network. **Identity/lifecycle**:
stable link identifier; Definition then Binding. **Required**: Network, participants, direction or
connectivity semantics. **Optional**: bandwidth, latency, loss, security, Fault model.
**Relations**: carries Flows and binds Protocols. **Validation**: participants are admissible in the
Network; quality values have units and do not contradict Network policy. **Extension**: provider
topology details remain external.

### Protocol

**Purpose**: declared communication semantic/binding capability, not a hard-coded core technology.
**Identity/lifecycle**: stable protocol identifier; Definition profile. **Required**: capability
vocabulary, compatibility statement, payload adaptation rules or reference. **Optional**: discovery,
quality, security, addressing semantics. **Relations**: binds Interfaces, Flows, Links, adapters.
**Validation**: binding satisfies Interface and Flow requirements; limitations are explicit.
**Extension**: concrete protocol definitions belong to profiles or compatibility catalogs.

### Model

**Purpose**: referenceable representation of behavior, structure, physics, or control. **Identity/lifecycle**:
stable model identifier; Definition then Binding. **Required**: model kind, provenance, input/output
semantic contract. **Optional**: fidelity, Parameters, standard-format reference, Artifact.
**Relations**: supports Components, Devices, Sensors, Actuators, Simulators. **Validation**:
inputs/outputs connect only through compatible Interfaces; a fidelity claim has evidence or an
explicit maturity limit. **Extension**: standard-specific semantics are referenced, not duplicated.

### Artifact

**Purpose**: immutable, versioned material input or output used to realize or evidence a model.
**Identity/lifecycle**: stable artifact identifier plus immutable revision/digest; Definition then
Binding. **Required**: kind, version/revision, provenance, integrity identifier where available.
**Optional**: license, distribution location, compatibility declaration, retention. **Relations**:
referenced by Models, Components, Deployments, observation results. **Validation**: mutable labels
alone cannot provide reproducibility; unavailable/restricted artifacts are explicit gaps.
**Extension**: providers add retrieval metadata without credentials.

### ExecutionTarget

**Purpose**: abstract place or mechanism capable of realizing a Component or Device.
**Identity/lifecycle**: stable target identifier; Definition plus Execution-intent. **Required**:
target class (process, container, virtual machine, emulator, model unit, remote, or physical),
capabilities, lifecycle contract reference. **Optional**: offered Resources, environment constraints,
provider binding. **Relations**: hosts Deployments, offers ComputeResources, may be managed by a
Simulator. **Validation**: target satisfies every bound resource/artifact constraint; remote and
physical detail remains an overlay. **Extension**: providers implement target classes without
becoming core types.

### Simulator

**Purpose**: provider role that advances or hosts a simulated model or device realization.
**Identity/lifecycle**: stable simulator identifier; Definition plus Execution-intent. **Required**:
supported Model/Device capability and time interaction. **Optional**: fidelity/evidence, Artifact,
ExecutionTarget, resource requirements. **Relations**: realizes simulated Devices, hosts Models,
participates in TimeDomains, binds through Deployments. **Validation**: input/output and clock
interaction are declared before a Scenario relies on it. **Extension**: vendor/tool semantics remain
in a provider profile.

### TimeDomain

**Purpose**: declared interpretation of time for related Flows, Models, targets, and observations.
**Identity/lifecycle**: stable time-domain identifier; Definition then Binding. **Required**: time
basis, ordering/advancement semantics, synchronization expectation. **Optional**: epoch, resolution,
tolerance, rate, synchronization evidence. **Relations**: contains Clocks; referenced by Flows,
Scenarios, Models, Simulators, Metrics. **Validation**: cross-domain interaction needs explicit
mapping/tolerance; determinism requires evidence. **Extension**: provider clock APIs remain external.

### Clock

**Purpose**: named source, observer, or controller of time in a TimeDomain. **Identity/lifecycle**:
stable clock identifier; Definition then Binding. **Required**: TimeDomain and role. **Optional**:
drift, precision, synchronization source, quality evidence. **Relations**: used by Models,
Simulators, ExecutionTargets, Observers. **Validation**: clock claims match domain advancement.
**Extension**: implementation timestamps are bindings, not core clock identity.

### Fault

**Purpose**: declared adverse condition or injected perturbation used by a Scenario.
**Identity/lifecycle**: stable fault identifier; Definition plus Execution-intent. **Required**:
target class/reference, activation condition, intended observable consequence or explicit unknown.
**Optional**: duration, severity, recovery condition, safety boundary, reproducibility reference.
**Relations**: selected by Scenarios; can affect Flows, Links, Components, Devices, Resources, or
TimeDomains. **Validation**: target and lifecycle are explicit; no fault silently alters an
out-of-scope production asset. **Extension**: fault taxonomies live in profiles.

### Observer

**Purpose**: declared non-intrusive or explicitly intrusive evidence collector. **Identity/lifecycle**:
stable observer identifier; Definition plus Observation. **Required**: target/reference,
observation contract, output provenance policy. **Optional**: sampling, trigger, retention,
redaction, Resource requirement. **Relations**: observes Flows, Components, Devices,
ExecutionTargets, TimeDomains, or Scenarios; feeds Metrics. **Validation**: declares whether it can
perturb timing/payload and binds to a compatible target. **Extension**: collection tools remain
provider bindings.

### Metric

**Purpose**: named evaluation calculation over declared observations. **Identity/lifecycle**: stable
metric identifier; Definition plus Observation. **Required**: input Observer/evidence references,
calculation semantics, unit or categorical result, acceptance interpretation. **Optional**:
aggregation window, threshold, confidence, report format. **Relations**: evaluates Scenario outcomes
and may reference TimeDomains. **Validation**: inputs are observable, units compatible, provenance
preserved, and claims no broader fidelity than evidence supports. **Extension**: profiles add formula
vocabularies.

### Parameter

**Purpose**: typed named value that configures a semantic object without changing its identity.
**Identity/lifecycle**: stable identifier in owner namespace; Definition then Binding. **Required**:
owner, value type, unit/categorical domain where applicable, default or required-binding policy.
**Optional**: range, mutability, source, sensitivity label. **Relations**: configures Systems,
Components, Models, Devices, Scenarios, Deployments. **Validation**: values satisfy type/range/unit;
credentials and secrets are secure binding references, never Parameter values. **Extension**:
profiles add types through a declared namespace.

### Resource

**Purpose**: consumable, reservable, or constrained capability for a Scenario or realization.
**Identity/lifecycle**: stable resource identifier; Definition then Binding. **Required**: resource
class, capacity/constraint semantics, allocation policy. **Optional**: availability, locality,
isolation, cost/priority. **Relations**: ComputeResource specializes Resource; Deployments request
Resources; ExecutionTargets offer them. **Validation**: quantities use a declared measure and
bindings respect exclusivity/capacity. **Extension**: provider inventory remains outside the core.

### Deployment

**Purpose**: environment-specific overlay binding logical objects to realization without changing
logical identity. **Identity/lifecycle**: stable deployment identifier; Binding plus Execution-intent.
**Required**: target System/Component/Device, ExecutionTarget or realization class, Artifacts,
lifecycle/readiness contract, provenance/maturity. **Optional**: Resource assignments, Parameters,
network/time bindings, recovery policy, environment label. **Relations**: resolves logical objects to
ExecutionTargets, Artifacts, Resources, Networks, TimeDomains, Simulators. **Validation**: logical
object and realization are compatible; secrets/addresses come only from restricted overlays; Failed
records its reason and does not imply cleanup succeeded. **Extension**: provider details are isolated
behind profile or adapter bindings.

## Cross-cutting validation

1. Every reference resolves in declared scope, or has external provenance and availability state.
2. An Interface/Endpoint/Flow chain is directionally and semantically compatible; transformations
   and Protocol adaptation are declared rather than inferred.
3. Device identity is independent of Deployment and can bind to simulated, virtual, physical, or
   hybrid realization without identifier replacement.
4. A Deployment cannot become Ready until artifacts, resources, targets, time mappings, and
   lifecycle conditions resolve. M1 defines a semantic rule, not an executor.
5. Faults and observations identify target, condition, and evidence limitations. Runtime effects
   remain unverified until a later capability tests them.
6. Fidelity, determinism, performance, and compatibility claims include evidence and a maturity
   label: implemented/demonstrated, partial, architectural target, or exploratory/PoC.
7. A profile adds concepts/mappings only in its namespace and never redefines System, Deployment,
   Device, Interface, or Artifact semantics.

## Compatibility, standards, and review

Legacy assets remain immutable external dependencies. Their repositories, images, firmware, and
bridges may become future Artifact, Component, Interface, Protocol, and Deployment bindings only
after a separate compatibility capability. M0 findings R01–R05 remain constraints; M1 neither
selects a cruise-control variant nor claims it can launch one.

The model references external architecture/model standards through provenance and bindings. It does
not replace a general-purpose architecture language, a model-exchange standard, or provider
configuration. This is an **architectural target**: no schema, parser, validator, loader, catalog,
runtime, adapter, blueprint, interface, or production integration is implemented by M1.

The M1 review is approved. M2 may specify XDL from these semantics, subject to its own Spec Kit
feature, ADRs, validation, and review. See [the decision record](../../specs/002-domain-neutral-metamodel/checklists/acceptance.md).
