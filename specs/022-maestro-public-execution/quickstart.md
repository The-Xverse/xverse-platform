# Development and verification

This capability's bounded public Python boundary is user-accepted. The actual
Studio/Autoverse integration remains open; no production run command is introduced.
Do not use private _OriginalRuntimeRun imports or flip RuntimeService flags to
manufacture admission. Run only the owned tests introduced by this capability.
The full Studio demonstration remains open until actual Maestro, native X-COM and
Argus share one verified run and the platform acceptance gate is satisfied.

The public Python prototype is xverse.maestro.execution.PublicExecutionService;
its exact input/provider/permit operations are documented in
contracts/public-execution.md. It is not wired to an external HTTP endpoint.
For owned Linux development verification, rebuild the installed package, configure
the platform native build using its explicitly admitted offline dependency/test
prefixes, then build xverse_maestro_public_native_exchange. Missing native inputs
fail actionably; no skip or synthetic fallback satisfies the native case. Run:

```text
uv pip install --python .venv/bin/python --no-deps --reinstall -e .
cmake --build <admitted-native-build> --target xverse_maestro_public_native_exchange
Set XVERSE_MPX_NATIVE_EXCHANGE to <admitted-native-build>/tests/maestro_public/native/xverse_maestro_public_native_exchange
.venv/bin/python -I -m pytest tests/maestro_public -q
```

These tests create only their fixed owned Linux children and actual Argus output
under pytest temporary roots; the C++ helper actually exchanges native FIFO payloads.
They do not run Autoverse, containers, a network workload or devices. The helper is
a verification artifact, not an admitted production executable or a run command.
The closed legacy runtime still requires its existing independent admission gates.
Operational/recovery limits are in docs/engineering/maestro-public/maintenance.md.
