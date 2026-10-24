---
title: Identity and realization
description: Keep a logical device stable while changing how it is implemented.
sidebar:
  order: 2
---

A logical device answers **what participates in the system**. A realization answers **how that device is provided for a particular deployment**.

For example, `sample-device` can retain its logical identity while one deployment binds it to a simulated realization and another selects a physical device. This supports comparisons without redefining the logical system for every environment.

## Resource and element identity

A resource has an API version, kind, namespace, and name. Its content carries a separate semantic version. Elements have IDs scoped to their owning resource.

- Use a resource reference for another resource.
- Use an element reference when a relationship identifies an element within a resource.
- Use local ID fields only where the containing schema defines their collection and scope.

An element ID must be unique across its owning resource; an element reference does not carry a collection name.

## Ownership

The owning resource controls an element's lifecycle. Referring to a device does not transfer authority to modify or execute it. Runtime ownership and execution permits are separate contracts.

## Realization classes

A device can declare supported realization classes. A Deployment selects bindings and supplies the explicit artifacts and resources those bindings require.

A simulated, virtual, physical, or hybrid arrangement must state its actual fidelity and constraints. Reusing a logical identity does not imply equivalent behavior or timing.

See [Deployment schema](/docs/reference/generated/schemas/deployment/) and [lifecycle guide](/docs/guides/maestro/).
