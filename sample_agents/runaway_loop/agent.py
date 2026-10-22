"""Misbehaving agent: never decides it is done and blows through its step budget."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sample_agents.harness import ToolBox

# Hard stop so the fixture itself can never hang a test run.
_SAFETY_LIMIT = 20


def run(task: str, tools: ToolBox) -> str:
    answer = ""
    for attempt in range(_SAFETY_LIMIT):
        answer = tools.call("search", query=f"{task} (attempt {attempt + 1})")
    return f"Still not sure. Last result: {answer}"
