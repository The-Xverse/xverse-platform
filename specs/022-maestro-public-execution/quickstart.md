# Development and verification

This capability is under implementation and has no admitted run command yet.
Do not use private _OriginalRuntimeRun imports or flip RuntimeService flags to
manufacture admission. Run only the owned tests introduced by this capability.
The full Studio demonstration remains open until actual Maestro, native X-COM and
Argus share one verified run and the platform acceptance gate is satisfied.

The public Python prototype is xverse.maestro.execution.PublicExecutionService;
its exact input/provider/permit operations are documented in
contracts/public-execution.md. It is not wired to an external HTTP endpoint.
For owned development verification, rebuild the installed package and run:

```text
uv pip install --python .venv/bin/python --no-deps --reinstall -e .
.venv/bin/python -I -m pytest tests/maestro_public -q
```

These tests create only their fixed owned Linux children and actual Argus output
under pytest temporary roots; they do not run Autoverse, containers or devices.
The closed legacy runtime still requires its existing independent admission gates.
Operational/recovery limits are in docs/engineering/maestro-public/maintenance.md.
