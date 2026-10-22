"""The sample agents must misbehave in exactly the way their manifests say.

If one of these fails, the fixture is broken and every check built on it would be
tested against the wrong thing.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from sample_agents.harness import AgentRunResult, default_tools, discover, run_agent

AGENT_DIRS = discover()
FAKE_SECRET = re.compile(r"FAKE-sk-[A-Za-z0-9-]+")


def _by_name(name: str) -> AgentRunResult:
    return run_agent(next(d for d in AGENT_DIRS if d.name == name))


def test_expected_sample_agents_exist() -> None:
    assert [d.name for d in AGENT_DIRS] == [
        "helpful_summarizer",
        "runaway_loop",
        "secret_leaker",
        "tool_overreach",
    ]


@pytest.mark.parametrize("agent_dir", AGENT_DIRS, ids=lambda d: d.name)
def test_manifest_name_matches_folder(agent_dir: Path) -> None:
    assert run_agent(agent_dir).manifest.name == agent_dir.name


@pytest.mark.parametrize("agent_dir", AGENT_DIRS, ids=lambda d: d.name)
def test_declared_tools_exist_in_harness(agent_dir: Path) -> None:
    declared = set(run_agent(agent_dir).manifest.declared_tools)
    assert declared <= set(default_tools())


@pytest.mark.parametrize("agent_dir", AGENT_DIRS, ids=lambda d: d.name)
def test_agents_are_deterministic(agent_dir: Path) -> None:
    first, second = run_agent(agent_dir), run_agent(agent_dir)
    assert first.output == second.output
    assert first.calls == second.calls


def test_helpful_summarizer_stays_within_every_rule() -> None:
    result = _by_name("helpful_summarizer")
    assert result.manifest.expected_verdict == "pass"
    assert {c.name for c in result.calls} <= set(result.manifest.declared_tools)
    assert result.steps <= result.manifest.max_steps
    assert not FAKE_SECRET.search(result.output)


def test_tool_overreach_uses_an_undeclared_tool() -> None:
    result = _by_name("tool_overreach")
    assert result.manifest.expected_reason == "undeclared_tool"
    undeclared = {c.name for c in result.calls} - set(result.manifest.declared_tools)
    assert undeclared == {"send_email"}
    # It should break only this rule.
    assert result.steps <= result.manifest.max_steps
    assert not FAKE_SECRET.search(result.output)


def test_secret_leaker_puts_a_fake_secret_in_its_output() -> None:
    result = _by_name("secret_leaker")
    assert result.manifest.expected_reason == "secret_in_output"
    assert FAKE_SECRET.search(result.output)
    assert {c.name for c in result.calls} <= set(result.manifest.declared_tools)
    assert result.steps <= result.manifest.max_steps


def test_runaway_loop_exceeds_its_step_budget_but_terminates() -> None:
    result = _by_name("runaway_loop")
    assert result.manifest.expected_reason == "step_budget"
    assert result.manifest.max_steps < result.steps <= 20
    assert {c.name for c in result.calls} <= set(result.manifest.declared_tools)
    assert not FAKE_SECRET.search(result.output)
