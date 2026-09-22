# Quickstart: XDL loader, validator, and normalizer

From `xverse-platform`, create an isolated environment and install the locked project:

```sh
uv sync --frozen
```

Validate the complete approved example graph with its local illustrative Profile schema:

```sh
uv run xdl validate --format text \
  --profile-schema tests/fixtures/measurement-profile.schema.json \
  xdl/examples/v1alpha1/profile.xdl.yaml \
  xdl/examples/v1alpha1/component.xdl.yaml \
  xdl/examples/v1alpha1/system.xdl.yaml \
  xdl/examples/v1alpha1/deployment.xdl.yaml \
  xdl/examples/v1alpha1/scenario.xdl.yaml
```

Produce canonical normalized JSON:

```sh
uv run xdl normalize \
  --profile-schema tests/fixtures/measurement-profile.schema.json \
  xdl/examples/v1alpha1/profile.xdl.yaml \
  xdl/examples/v1alpha1/component.xdl.yaml \
  xdl/examples/v1alpha1/system.xdl.yaml \
  xdl/examples/v1alpha1/deployment.xdl.yaml \
  xdl/examples/v1alpha1/scenario.xdl.yaml
```

Run capability validation:

```sh
uv run python -m unittest discover -s tests -v
uv run python scripts/validate_xdl_loader.py
uv run python scripts/benchmark_xdl_loader.py
uv run python scripts/validate_m2.py --self-test
.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
git diff --check
```

The command never fetches missing resources or schemas. Supply a complete resource set and each used
Profile schema explicitly. `Ready` means statically complete declarations; it is not live readiness.
