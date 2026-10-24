---
title: Installation
description: Install the Python tools from a source checkout.
sidebar:
  order: 1
---

The Python distribution is `xverse-xdl`; its commands are `xdl` and `xverse-argus`. The current package version is **0.4.0**. Package version and Lite release-candidate name are separate identities.

## Prerequisites

- Python **3.11 or newer**.
- [uv](https://docs.astral.sh/uv/getting-started/installation/).
- Git and a checkout of the platform repository.

The X-COM C++ toolchain is needed only for C++ development. Node, Sphinx, and Doxygen are documentation-build dependencies, not requirements for using the Python validator.

## Install the locked environment

```sh
git clone https://github.com/The-Xverse/xverse-platform.git
cd xverse-platform
uv sync --frozen
uv run --frozen xdl version
```

Run guide commands from the repository root. The installation creates a local `.venv` using the project lockfile; package download access may be needed during installation.

## Inspect the commands

```sh
uv run --frozen xdl --help
uv run --frozen xdl validate --help
uv run --frozen xdl experiment compile --help
```

See the [generated CLI reference](/docs/reference/generated/cli/) for current command options. Argus currently prints usage when invoked without arguments, returning exit status 2.

## Next step

[Validate your first system](/docs/getting-started/first-system/). This exercises local validation without connecting to running components.
