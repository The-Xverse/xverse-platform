---
title: X-COM communication
description: Communication contracts, observation, stimulation, and the C++ build boundary.
sidebar:
  order: 5
---

X-COM is the platform's **C++ communication boundary**. The current bounded prototype covers explicit contracts, provider/endpoint/route lifecycle, controlled observation and stimulation, and a local IPC/gRPC tool gateway.

## Contracts before transport

A flow states source, destinations, interface, delivery intent, and timing context. A provider binding must explicitly account for the requested semantics.

A successful route plan does not prove a particular physical network, middleware adapter, or application-level behavior.

## Observe and stimulate

Observation and controlled stimulation are separate contracts. A tool must respect ownership, lifetime, capacity, session, and admission conditions.

X-COM supplies the communication boundary. Argus or another consumer owns evidence presentation and dashboards.

The [C++ API reference](/reference/cpp/) is generated from public headers. Header comments describe ownership, lifetime, thread safety, failure semantics, and bounds where provided.

## Build prerequisites

The current documented build envelope uses Linux x86-64, a compatible Jammy-derived ABI environment, C++20, CMake 3.22+, Ninja 1.10+, Python 3.11+, and `dpkg-deb`.

The runtime dependency bundle and GTest bundle are separate, exact admitted inputs. They are not included in a repository clone. Follow the repository build-environment and dependency-admission guides when provisioning those inputs.

With the exact bundles verified and the corresponding `XVERSE_XCOM_TOOLCHAIN`, `XVERSE_XCOM_PACKAGE_MANIFEST`, `XVERSE_XCOM_T025_TEST_TOOLCHAIN`, and library path configured:

```sh
cmake -S . -B build/xcom -G Ninja \
  -DCMAKE_BUILD_TYPE=Debug -DBUILD_TESTING=ON
cmake --build build/xcom
ctest --test-dir build/xcom --output-on-failure
```

Do not substitute an arbitrary dependency prefix and infer reproducibility. Configuration rejects missing or mismatched admitted inputs.

## Python flow layer

The Lite Python flow layer mirrors admitted loopback rules and does not activate the C++ core. Read [flow bindings](/docs/guides/flows/) for that distinct boundary.
