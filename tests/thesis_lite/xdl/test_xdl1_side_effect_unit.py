"""XDL1-SR-014-U / XDL1-SR-003-U: pure offline no-side-effect unit cases."""

from __future__ import annotations

import builtins
import datetime
import hashlib
import multiprocessing
import os
import socket
import subprocess
import threading
import time

from xverse_xdl import experiment_plan as ep

from tests.thesis_lite.xdl import support as S


def _explode(*args, **kwargs):
    raise AssertionError("the pure compiler must not perform this action")


def test_compiler_opens_no_file_after_admission(monkeypatch):
    monkeypatch.setattr(builtins, "open", _explode)
    result = S.compile_declared(S.declared())
    assert result.is_valid, [item.code for item in result.diagnostics]


def test_compiler_creates_no_process(monkeypatch):
    monkeypatch.setattr(subprocess, "Popen", _explode)
    monkeypatch.setattr(subprocess, "run", _explode)
    monkeypatch.setattr(os, "system", _explode)
    result = S.compile_declared(S.declared())
    assert result.is_valid


def test_compiler_performs_no_network_access(monkeypatch):
    monkeypatch.setattr(socket, "socket", _explode)
    monkeypatch.setattr(socket, "create_connection", _explode)
    result = S.compile_declared(S.declared())
    assert result.is_valid


def test_compiler_spawns_no_thread(monkeypatch):
    monkeypatch.setattr(threading, "Thread", _explode)
    monkeypatch.setattr(multiprocessing, "Process", _explode)
    result = S.compile_declared(S.declared())
    assert result.is_valid


class _NoClock:
    """Stand-in datetime type whose constructors refuse to be called."""

    @staticmethod
    def now(*args, **kwargs):
        _explode()

    @staticmethod
    def utcnow(*args, **kwargs):
        _explode()


def test_compiler_reads_no_ambient_clock(monkeypatch):
    monkeypatch.setattr(time, "time", _explode)
    monkeypatch.setattr(time, "monotonic", _explode)
    monkeypatch.setattr(datetime, "datetime", _NoClock)
    result = S.compile_declared(S.declared())
    assert result.is_valid
    assert result.run["generatedAt"] == ep.DEFAULT_GENERATED_AT


def test_compilation_independent_of_locale_and_timezone(monkeypatch):
    monkeypatch.setenv("TZ", "UTC")
    monkeypatch.setenv("LANG", "C")
    first = S.compile_declared(S.declared())
    monkeypatch.setenv("TZ", "Australia/Sydney")
    monkeypatch.setenv("LANG", "de_DE.UTF-8")
    second = S.compile_declared(S.declared())
    assert first.is_valid and second.is_valid
    assert ep.canonical_plan_bytes(first.plan) == ep.canonical_plan_bytes(second.plan)
    assert first.plan["digest"] == second.plan["digest"]


def test_successful_compile_leaves_supplied_files_unchanged():
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in S.FIXTURE_PATHS}
    result = ep.compile_experiment_files(S.FIXTURE_PATHS, profile_schema_paths=S.PROFILE_SCHEMA_REFS)
    assert result.is_valid
    after = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in S.FIXTURE_PATHS}
    assert before == after
