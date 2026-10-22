"""Well-behaved agent: one search, then a short summary."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sample_agents.harness import ToolBox


def run(task: str, tools: ToolBox) -> str:
    results = tools.call("search", query=task)
    return f"Summary for {task!r} based on: {results}"
