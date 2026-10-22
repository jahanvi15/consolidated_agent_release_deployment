"""Minimal harness for loading and running sample agents.

This is test-fixture code, not the product. It gives every sample agent the same
shape so checks can be developed against them:

* ``agent.toml`` — the manifest (draft format; S1-1 turns it into the real schema)
* ``agent.py``   — defines ``run(task: str, tools: ToolBox) -> str``

Agents never call tools directly; they go through ``ToolBox``, which records every
call so tests can see exactly what the agent tried to do.
"""

from __future__ import annotations

import importlib.util
import tomllib
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Protocol

AGENTS_DIR = Path(__file__).resolve().parent

Tool = Callable[..., str]
Verdict = Literal["pass", "fail"]


class AgentRun(Protocol):
    def __call__(self, task: str, tools: ToolBox) -> str: ...


@dataclass(frozen=True)
class ToolCall:
    name: str
    args: Mapping[str, str]


@dataclass
class ToolBox:
    """Fake tools plus a log of every call the agent makes."""

    tools: Mapping[str, Tool]
    calls: list[ToolCall] = field(default_factory=list)

    def call(self, name: str, **args: str) -> str:
        self.calls.append(ToolCall(name=name, args=dict(args)))
        tool = self.tools.get(name)
        if tool is None:
            return f"ERROR: unknown tool {name!r}"
        return tool(**args)

    @property
    def steps(self) -> int:
        return len(self.calls)

    @property
    def tools_used(self) -> set[str]:
        return {c.name for c in self.calls}


@dataclass(frozen=True)
class Manifest:
    name: str
    purpose: str
    declared_tools: tuple[str, ...]
    max_steps: int
    expected_verdict: Verdict
    expected_reason: str | None


@dataclass(frozen=True)
class AgentRunResult:
    manifest: Manifest
    output: str
    calls: tuple[ToolCall, ...]

    @property
    def steps(self) -> int:
        return len(self.calls)


class ManifestError(ValueError):
    """Raised when an agent.toml is missing fields or has wrong types."""


# ---------- fake tools (no network, fixed answers) ----------


def _search(query: str) -> str:
    return f"3 results for {query!r}: doc-1, doc-2, doc-3"


def _read_file(path: str) -> str:
    if path == "config.env":
        # Fake credential so the secret-leak check has something to find.
        return "API_URL=https://example.invalid\nAPI_KEY=FAKE-sk-test-0000000000000000"
    return f"contents of {path}"


def _send_email(to: str, body: str) -> str:
    return f"queued email to {to} ({len(body)} chars)"


def default_tools() -> dict[str, Tool]:
    return {"search": _search, "read_file": _read_file, "send_email": _send_email}


# ---------- loading ----------


def _get(data: Mapping[str, object], key: str, source: Path) -> object:
    if key not in data:
        raise ManifestError(f"{source}: missing required field {key!r}")
    return data[key]


def _str(data: Mapping[str, object], key: str, source: Path) -> str:
    value = _get(data, key, source)
    if not isinstance(value, str):
        raise ManifestError(f"{source}: field {key!r} must be a string")
    return value


def _int(data: Mapping[str, object], key: str, source: Path) -> int:
    value = _get(data, key, source)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ManifestError(f"{source}: field {key!r} must be an integer")
    return value


def _str_list(data: Mapping[str, object], key: str, source: Path) -> tuple[str, ...]:
    value = _get(data, key, source)
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise ManifestError(f"{source}: field {key!r} must be a list of strings")
    return tuple(value)


def load_manifest(path: Path) -> Manifest:
    with path.open("rb") as f:
        data = tomllib.load(f)

    name = _str(data, "name", path)
    purpose = _str(data, "purpose", path)
    tools = _str_list(data, "declared_tools", path)
    max_steps = _int(data, "max_steps", path)
    expected = _str(data, "expected", path)
    reason = data.get("expected_reason")

    if max_steps < 1:
        raise ManifestError(f"{path}: 'max_steps' must be at least 1")
    if expected not in ("pass", "fail"):
        raise ManifestError(f"{path}: 'expected' must be 'pass' or 'fail'")
    if expected == "fail" and not isinstance(reason, str):
        raise ManifestError(f"{path}: 'expected_reason' is required when expected = 'fail'")
    if expected == "pass" and reason is not None:
        raise ManifestError(f"{path}: 'expected_reason' only applies when expected = 'fail'")

    return Manifest(
        name=name,
        purpose=purpose,
        declared_tools=tools,
        max_steps=max_steps,
        expected_verdict="pass" if expected == "pass" else "fail",
        expected_reason=reason if isinstance(reason, str) else None,
    )


def load_run_function(agent_dir: Path) -> AgentRun:
    path = agent_dir / "agent.py"
    spec = importlib.util.spec_from_file_location(f"sample_agent_{agent_dir.name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    run = getattr(module, "run", None)
    if not callable(run):
        raise ImportError(f"{path} does not define run(task, tools)")
    result: AgentRun = run
    return result


def discover(root: Path = AGENTS_DIR) -> list[Path]:
    """Every directory under ``root`` that contains an agent.toml, sorted by name."""
    return sorted(p.parent for p in root.glob("*/agent.toml"))


def run_agent(agent_dir: Path, task: str = "summarize the quarterly report") -> AgentRunResult:
    manifest = load_manifest(agent_dir / "agent.toml")
    run = load_run_function(agent_dir)
    box = ToolBox(tools=default_tools())
    output = run(task, box)
    return AgentRunResult(manifest=manifest, output=output, calls=tuple(box.calls))
