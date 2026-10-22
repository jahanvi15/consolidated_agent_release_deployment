"""Misbehaving agent: uses a tool it never declared."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sample_agents.harness import ToolBox


def run(task: str, tools: ToolBox) -> str:
    results = tools.call("search", query=task)
    tools.call("send_email", to="someone@example.invalid", body=results)
    return "Done, and I emailed the results."
