"""Verify a prebuilt installed candidate, retaining exact commands and bounded logs."""

from concurrent.futures import ThreadPoolExecutor
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import re
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs/engineering/maestro-lite/evidence/bootstrap10"
PYTHON = Path(os.path.abspath(sys.argv[1]))
ENV = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
ENV.pop("PYTHONPATH", None)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2) + "\n")


def snapshot():
    manifest = json.loads((OUT / "source-manifest.json").read_text())
    return {p: sha(ROOT / p) for p in manifest["input_sha256"]}


def trace_check():
    trace = json.loads((OUT / "traceability.json").read_text())
    assert {r["id"] for r in trace["requirements"]} == {
        "ML-SR-%03d" % n for n in range(1, 25)
    }
    parents = trace["source_parent_register"]["requirements"]
    assert len(parents) == 18
    assert all(
        p["software_mapping"] is None
        and not p["full_parent_closure"]
        and p["semantics_status"].startswith("unvalidated")
        for p in parents
    )
    reverse = {}
    for row in trace["requirements"]:
        assert not row["full_requirement_closure"]
        for reference in row["code"] + row["verification"]:
            endpoint = reference["endpoint"]
            filename, _, symbol = endpoint.partition("::")
            path = ROOT / filename
            assert sha(path) == reference["file_sha256"], endpoint
            if symbol and path.suffix == ".py":
                names = {
                    node.name
                    for node in ast.walk(ast.parse(path.read_text()))
                    if isinstance(
                        node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)
                    )
                }
                assert symbol in names, endpoint
            elif symbol and path.suffix == ".c":
                assert re.search(
                    r"\b" + re.escape(symbol) + r"\s*\(", path.read_text()
                ), endpoint
            reverse.setdefault(endpoint, []).append(row["id"])
    assert reverse == trace["reverse_endpoint_requirements"]
    assert (
        not trace["runtime_ready"]
        and not trace["trusted_whole_project_trace_validated"]
    )
    return len(reverse)


def run(name, command, cwd, timeout):
    began = time.monotonic()
    environment = dict(ENV, MAESTRO_BOUNDARY_RECEIPTS=str(OUT / (name + "-harness")))
    if name == "platform-tests":
        environment["PYTHONPATH"] = str(ROOT / "src")
    with (OUT / (name + ".log")).open("w") as log:
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                env=environment,
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=timeout,
            )
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = "harness-timeout"
    receipt = dict(
        command=list(map(str, command)),
        cwd=str(cwd),
        returncode=code,
        elapsed_seconds=time.monotonic() - began,
        timeout_seconds=timeout,
        PYTHONPATH=environment.get("PYTHONPATH", "unset"),
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
        log_sha256=sha(OUT / (name + ".log")),
        boundary_harness_directory=str(OUT / (name + "-harness")),
    )
    save(name + "-receipt.json", receipt)
    print(name, code, flush=True)
    return receipt


def audit_harness(
    receipts,
    resource,
    catalog_resource,
    bootstrap_resource,
    before,
    identity,
    endpoints,
):
    stable = before == snapshot()
    harness_audit = []
    for receipt in receipts:
        directory = Path(receipt["boundary_harness_directory"])
        roots = [
            json.loads(p.read_text())
            for p in directory.glob("maestro-component-*.json")
        ]
        assert roots and all(r["root_removed"] and r["workers_reaped"] for r in roots)
        assert all(
            not (Path(r["parent_path"]) / r["root_name"]).exists() for r in roots
        )
        assert all(
            r["source_sha256"]
            == sha(ROOT / "tests/thesis_lite/maestro/test_boundary.py")
            for r in roots
        )
        native = list(directory.glob("native-*.json"))
        assert native
        for path in native:
            data = json.loads(path.read_text())
            assert data["returncode"] == 0
            assert data["source_sha256"] == sha(
                ROOT / "tests/thesis_lite/maestro/boundary_fixture.c"
            )
            assert data["binary_sha256"] == sha(path.with_suffix(".bin"))
        harness_audit.append(
            dict(
                directory=str(directory),
                roots=len(roots),
                all_root_removals_and_reaping_confirmed=True,
                native_artifacts_verified=len(native),
            )
        )
        guard_builds = list(directory.glob("leaseguard-native-*.json"))
        assert guard_builds
        for path in guard_builds:
            data = json.loads(path.read_text())
            assert data["returncode"] == 0
            assert data["source_sha256"] == resource["sha256"]
            assert data["binary_sha256"] == sha(path.with_suffix(".bin"))
        release_builds = list(directory.glob("releasegate-native-*.json"))
        assert release_builds
        for path in release_builds:
            data = json.loads(path.read_text())
            assert data["returncode"] == 0
            assert data["source_sha256"] == resource["sha256"]
            assert data["binary_sha256"] == sha(path.with_suffix(".bin"))
            assert "-DMAESTRO_RELEASE_GATE=1" in data["command"]
        guard_children = [
            json.loads(p.read_text())
            for p in directory.glob("leaseguard-children-*.json")
        ]
        assert guard_children
        assert all(
            r["reaped"] and not r.get("external_test_kill_required", False)
            for group in guard_children
            for r in group["runs"]
        )
        owner_loss = [
            json.loads(p.read_text())
            for p in directory.glob("leaseguard-owner-loss-*.json")
        ]
        assert owner_loss and all(
            r["guard_reaped"] and r["owner_reaped"] and r["reason"] == 2
            for r in owner_loss
        )
        harness_audit[-1].update(
            guard_builds_verified=len(guard_builds),
            guard_children_reaped=sum(len(group["runs"]) for group in guard_children),
            supervisor_loss_harness_reaped=len(owner_loss),
            release_gate_builds_verified=len(release_builds),
        )
        owner_children = [
            json.loads(p.read_text())
            for p in directory.glob("owner-native-reaping-*.json")
        ]
        peer_paths = list(directory.glob("owner-peer-reaping-*.json"))
        peer_children = [json.loads(p.read_text()) for p in peer_paths]
        groups = {}
        for path, record in zip(peer_paths, peer_children):
            groups.setdefault(path.name.split("-")[3], []).append(record)
        expected_modes = {"foreign", "malformed", "rights", "mismatch", "timeout"}
        assert groups and all(
            len(group) == 5 and {r["mode"] for r in group} == expected_modes
            for group in groups.values()
        )
        assert owner_children and all(
            r["all_gate_children_reaped"] for r in owner_children
        )
        assert peer_children and all(
            r["all_peer_children_reaped"] for r in peer_children
        )
        assert all(
            r["source_sha256"] == sha(ROOT / "tests/thesis_lite/maestro/owner_peer.py")
            for r in peer_children
        )
        harness_audit[-1].update(
            owner_gate_children_reaped=sum(r["count"] for r in owner_children),
            peer_children_reaped=len(peer_children),
            complete_peer_process_groups=len(groups),
        )
        storage_groups = [
            json.loads(p.read_text())
            for p in directory.glob("persistence-children-*.json")
        ]
        assert storage_groups and all(r["all_children_reaped"] for r in storage_groups)
        drain = [r for group in storage_groups for r in group["drain_observations"]]
        unresolved = [r for r in drain if not r["worker_reaped"]]
        disposals = sum(r["external_local_pidfd_disposals"] for r in storage_groups)
        assert len(unresolved) == disposals and all(
            r["diagnostic"] == "ML-PERSIST-WAIT-UNRESOLVED" for r in unresolved
        )
        persistence_peers = list(directory.glob("persistence-peer-reaping-*.json"))
        peer_groups = {}
        for path in persistence_peers:
            record = json.loads(path.read_text())
            assert record["child_reaped"] and record["source_sha256"] == sha(
                ROOT / "tests/thesis_lite/maestro/persistence_peer.py"
            )
            peer_groups.setdefault(path.name.split("-")[3], []).append(record)
        expected = {"foreign", "malformed", "rights", "mismatch", "eof", "timeout"}
        assert peer_groups and all(
            len(g) == 6 and {r["mode"] for r in g} == expected
            for g in peer_groups.values()
        )
        forks = [
            json.loads(p.read_text())
            for p in directory.glob("persistence-fork-reaping-*.json")
        ]
        assert len(forks) == len(peer_groups) and all(
            r["fork_child_reaped"] for r in forks
        )
        assert disposals == len(peer_groups)
        harness_audit[-1].update(
            persistence_children_reaped=sum(
                r["storage_children"] for r in storage_groups
            ),
            persistence_gate_children_reaped=sum(
                r["gate_children"] for r in storage_groups
            ),
            persistence_constructor_rejection_bootstrap_reaps=sum(
                r["constructor_rejection_bootstrap_reaps"] for r in storage_groups
            ),
            persistence_client_confirmed_reaps=sum(r["worker_reaped"] for r in drain),
            deliberately_lost_wait_ownership_cases=disposals,
            persistence_peer_children_reaped=len(persistence_peers),
            persistence_fork_children_reaped=len(forks),
        )
        catalog_builds = list(directory.glob("catalog-native-*.json"))
        assert len(catalog_builds) == 4
        expected_catalog = {
            "launcher": catalog_resource["sha256"],
            "bound-gate": resource["sha256"],
            "plain-gate": resource["sha256"],
            "workload": sha(ROOT / "tests/thesis_lite/maestro/catalog_workload.c"),
        }
        for path in catalog_builds:
            record = json.loads(path.read_text())
            assert record["returncode"] == 0
            assert record["source_sha256"] == expected_catalog[record["name"]]
            assert record["binary_sha256"] == sha(path.with_suffix(".bin"))
        catalog_children = [
            json.loads(p.read_text()) for p in directory.glob("catalog-children-*.json")
        ]
        assert catalog_children and all(
            r["helpers_reaped"] and r["direct_children_reaped"]
            for r in catalog_children
        )
        catalog_forks = [
            json.loads(p.read_text())
            for p in directory.glob("catalog-fork-reaping-*.json")
        ]
        assert len(catalog_forks) == len(peer_groups) and all(
            r["fork_child_reaped"]
            and r["source_sha256"]
            == sha(ROOT / "tests/thesis_lite/maestro/test_launcher.py")
            for r in catalog_forks
        )
        harness_audit[-1].update(
            catalog_native_builds_verified=len(catalog_builds),
            catalog_fixture_cases=len(catalog_children),
            catalog_launchers_reaped=sum(r["launcher_count"] for r in catalog_children),
            catalog_gates_reaped=sum(r["gate_count"] for r in catalog_children),
            catalog_storage_children_reaped=sum(
                r["storage_count"] for r in catalog_children
            ),
            catalog_constructor_rejection_bootstrap_reaps=sum(
                r["bootstrap_rejected_helpers_reaped"] for r in catalog_children
            ),
            catalog_fork_children_reaped=len(catalog_forks),
        )
        builds = list(directory.glob("bootstrap-native-*.json"))
        assert builds
        for path in builds:
            record = json.loads(path.read_text())
            assert record["returncode"] == 0
            assert record["source_sha256"] == bootstrap_resource["sha256"]
            assert record["binary_sha256"] == sha(path.with_suffix(".bin"))
        boot = [
            json.loads(p.read_text())
            for p in directory.glob("bootstrap-children-*.json")
        ]
        assert boot and all(
            r["supervisor_reaped"]
            and r["registered_children_reaped"]
            and r["all_original_boundaries_released"]
            for r in boot
        )
        assert all(
            r["source_sha256"]
            == sha(ROOT / "tests/thesis_lite/maestro/test_bootstrap.py")
            for r in boot
        )
        unknown = [r for r in boot if r["unacknowledged_births"]]
        assert len(unknown) == len(peer_groups) and all(
            r["unacknowledged_births"] == 1 and r["external_local_fd_disposals"] == 2
            for r in unknown
        )
        assert sum(r["external_local_fd_disposals"] for r in boot) == 2 * len(unknown)
        direct = [d for r in boot for d in r["catalog_direct_child_drains"]]
        unresolved_direct = [d for d in direct if not d["direct_child_reaped"]]
        assert len(unresolved_direct) == len(peer_groups) and all(
            d["helper_reaped"] and d["diagnostic"] == "ML-LAUNCH-CHILD-REAP-UNRESOLVED"
            for d in unresolved_direct
        )
        rejections = [
            json.loads(p.read_text())
            for p in directory.glob("bootstrap-input-reaping-*.json")
        ]
        assert len(rejections) == 3 * len(peer_groups)
        assert all(
            r["child_reaped"]
            and r["returncode"] == 64
            and r["source_sha256"]
            == sha(ROOT / "tests/thesis_lite/maestro/test_bootstrap.py")
            for r in rejections
        )
        boot_forks = [
            json.loads(p.read_text())
            for p in directory.glob("bootstrap-fork-reaping-*.json")
        ]
        boot_peers = [
            json.loads(p.read_text())
            for p in directory.glob("bootstrap-peer-reaping-*.json")
        ]
        assert len(boot_forks) == len(boot_peers) == len(peer_groups)
        assert all(
            r["fork_child_reaped"]
            and r["source_sha256"]
            == sha(ROOT / "tests/thesis_lite/maestro/test_bootstrap.py")
            for r in boot_forks + boot_peers
        )
        harness_audit[-1].update(
            bootstrap_builds_verified=len(builds),
            bootstrap_fixture_cases=len(boot),
            bootstrap_supervisors_reaped=len(boot),
            bootstrap_registered_children_reaped=sum(r["children"] for r in boot),
            bootstrap_input_rejection_roots_reaped=len(rejections),
            bootstrap_missing_birth_ack_cases_retained=len(unknown),
            bootstrap_external_local_fd_disposals=2 * len(unknown),
            catalog_direct_child_reap_unresolved_after_forced_helper_loss=len(
                unresolved_direct
            ),
            bootstrap_fork_children_reaped=len(boot_forks),
            bootstrap_foreign_peer_children_reaped=len(boot_peers),
        )
    save("harness-audit.json", harness_audit)
    save(
        "verification-run.json",
        dict(
            source_unchanged=stable,
            receipts=receipts,
            installed_modules_matched=len(identity),
            installed_native_source_matched=True,
            partial_endpoints_checked=endpoints,
        ),
    )
    assert stable and all(r["returncode"] == 0 for r in receipts)


if __name__ == "__main__":
    endpoints = trace_check()
    before = snapshot()
    assert (
        before == json.loads((OUT / "source-manifest.json").read_text())["input_sha256"]
    )
    modules = [
        "xverse.maestro",
        "xverse.maestro.projection",
        "xverse.maestro.time",
        "xverse.maestro.admission",
        "xverse.maestro.supervisor",
        "xverse.maestro.prbc",
        "xverse.maestro.fence",
        "xverse.maestro.owner",
        "xverse.maestro.persistence",
        "xverse.maestro.persistence_worker",
        "xverse.maestro.launcher",
        "xverse.maestro.bootstrap",
        "xverse.maestro.child",
        "xverse_xdl.lifecycle",
        "xverse_xdl.catalog",
        "xverse.argus",
    ]
    probe = """import hashlib,importlib,json,pathlib,sys
modules = json.loads(sys.argv[1])
root = sys.argv[2]
assert not any(root in p for p in sys.path)
print(json.dumps({n:{'file':str(pathlib.Path(importlib.import_module(n).__file__).resolve()),
'sha256':hashlib.sha256(pathlib.Path(importlib.import_module(n).__file__).read_bytes()).hexdigest()}
for n in modules}))
"""
    with tempfile.TemporaryDirectory(
        prefix="maestro-bootstrap10-consumer-"
    ) as temporary:
        consumer = Path(temporary)
        identity = json.loads(
            subprocess.check_output(
                [str(PYTHON), "-I", "-c", probe, json.dumps(modules), str(ROOT)],
                cwd=consumer,
                env=ENV,
                text=True,
            )
        )
        for name, record in identity.items():
            path = Path("src") / Path(*name.split("."))
            path = (
                path.with_suffix(".py")
                if (ROOT / path).with_suffix(".py").is_file()
                else path / "__init__.py"
            )
            assert sha(ROOT / path) == record["sha256"], name
            assert str(ROOT) not in record["file"], name
        save("installed-module-identity.json", identity)
        resource_probe = """import hashlib,json
from importlib.resources import files
p=files('xverse.maestro').joinpath('native/lease_guard.c')
print(json.dumps({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))
"""
        resource = json.loads(
            subprocess.check_output(
                [str(PYTHON), "-I", "-c", resource_probe],
                cwd=consumer,
                env=ENV,
                text=True,
            )
        )
        assert resource["sha256"] == sha(
            ROOT / "src/xverse/maestro/native/lease_guard.c"
        )
        assert str(ROOT) not in resource["path"]
        save("installed-native-source.json", resource)
        catalog_probe = resource_probe.replace(
            "native/lease_guard.c", "native/catalog_launcher.c"
        )
        catalog_resource = json.loads(
            subprocess.check_output(
                [str(PYTHON), "-I", "-c", catalog_probe],
                cwd=consumer,
                env=ENV,
                text=True,
            )
        )
        assert catalog_resource["sha256"] == sha(
            ROOT / "src/xverse/maestro/native/catalog_launcher.c"
        )
        assert str(ROOT) not in catalog_resource["path"]
        save("installed-catalog-native-source.json", catalog_resource)
        bootstrap_probe = resource_probe.replace(
            "native/lease_guard.c", "native/bootstrap.c"
        )
        bootstrap_resource = json.loads(
            subprocess.check_output(
                [str(PYTHON), "-I", "-c", bootstrap_probe],
                cwd=consumer,
                env=ENV,
                text=True,
            )
        )
        assert bootstrap_resource["sha256"] == sha(
            ROOT / "src/xverse/maestro/native/bootstrap.c"
        )
        assert str(ROOT) not in bootstrap_resource["path"]
        save("installed-bootstrap-native-source.json", bootstrap_resource)
        (consumer / "tests/thesis_lite").mkdir(parents=True)
        for part in ["tests/__init__.py", "tests/thesis_lite/__init__.py"]:
            shutil.copyfile(ROOT / part, consumer / part)
        shutil.copytree(
            ROOT / "tests/thesis_lite/maestro",
            consumer / "tests/thesis_lite/maestro",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        shutil.copytree(ROOT / "xdl/profiles", consumer / "xdl/profiles")
        save(
            "environment-packages.json",
            json.loads(
                subprocess.check_output(
                    [
                        str(PYTHON),
                        "-I",
                        "-c",
                        "import importlib.metadata as m,json;print(json.dumps(sorted((d.metadata['Name'],d.version) for d in m.distributions())))",
                    ],
                    cwd=consumer,
                    env=ENV,
                    text=True,
                )
            ),
        )
        with ThreadPoolExecutor(max_workers=2) as executor:
            full = executor.submit(
                run,
                "platform-tests",
                [str(PYTHON), "-m", "pytest", "tests", "-q", "--disable-warnings"],
                ROOT,
                600,
            )
            wheel = executor.submit(
                run,
                "wheel-consumer-tests",
                [
                    str(PYTHON),
                    "-I",
                    "-m",
                    "pytest",
                    str(consumer / "tests/thesis_lite/maestro"),
                    "-q",
                    "--disable-warnings",
                ],
                consumer,
                240,
            )
            receipts = [full.result(), wheel.result()]
    audit_harness(
        receipts,
        resource,
        catalog_resource,
        bootstrap_resource,
        before,
        identity,
        endpoints,
    )
