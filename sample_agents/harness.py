"""Minimal harness for loading and running sample agents.

This is test-fixture code, not the product. It gives every sample agent the same
shape so checks can be developed against them:

* ``agent.toml``    — the real product manifest, validated by
  ``consolidated_agent_release_deployment.manifest`` (see docs/agent-manifest.md)
* ``agent.py``      — defines ``run(task: str, tools: ToolBox) -> str``
* ``expected.toml`` — fixture only: what the compliance checks should conclude

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

from consolidated_agent_release_deployment.manifest import AgentManifest, load_manifest

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
class Expectation:
    """What a sample agent's compliance result should be (from expected.toml)."""

    verdict: Verdict
    reason: str | None


@dataclass(frozen=True)
class AgentRunResult:
    manifest: AgentManifest
    expectation: Expectation
    output: str
    calls: tuple[ToolCall, ...]

    @property
    def steps(self) -> int:
        return len(self.calls)


class ExpectationError(ValueError):
    """Raised when an expected.toml fixture file is malformed."""


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


def load_expectation(path: Path) -> Expectation:
    with path.open("rb") as f:
        data = tomllib.load(f)
    unknown = set(data) - {"verdict", "reason"}
    if unknown:
        raise ExpectationError(f"{path}: unknown field(s) {sorted(unknown)}")
    verdict = data.get("verdict")
    reason = data.get("reason")
    if verdict not in ("pass", "fail"):
        raise ExpectationError(f"{path}: 'verdict' must be 'pass' or 'fail'")
    if verdict == "fail" and not isinstance(reason, str):
        raise ExpectationError(f"{path}: 'reason' is required when verdict = 'fail'")
    if verdict == "pass" and reason is not None:
        raise ExpectationError(f"{path}: 'reason' only applies when verdict = 'fail'")
    return Expectation(verdict="pass" if verdict == "pass" else "fail", reason=reason)


def load_run_function(agent_dir: Path, manifest: AgentManifest) -> AgentRun:
    path = agent_dir / manifest.entrypoint_file
    spec = importlib.util.spec_from_file_location(f"sample_agent_{agent_dir.name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    run = getattr(module, manifest.entrypoint_function, None)
    if not callable(run):
        raise ImportError(f"{path} does not define {manifest.entrypoint_function}(task, tools)")
    result: AgentRun = run
    return result


def discover(root: Path = AGENTS_DIR) -> list[Path]:
    """Every directory under ``root`` that contains an agent.toml, sorted by name."""
    return sorted(p.parent for p in root.glob("*/agent.toml"))


def run_agent(agent_dir: Path, task: str = "summarize the quarterly report") -> AgentRunResult:
    manifest = load_manifest(agent_dir / "agent.toml")
    expectation = load_expectation(agent_dir / "expected.toml")
    run = load_run_function(agent_dir, manifest)
    box = ToolBox(tools=default_tools())
    output = run(task, box)
    return AgentRunResult(
        manifest=manifest, expectation=expectation, output=output, calls=tuple(box.calls)
    )
