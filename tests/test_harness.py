from __future__ import annotations

from pathlib import Path

import pytest

from consolidated_agent_release_deployment.manifest import parse_manifest
from sample_agents.harness import (
    ExpectationError,
    ToolBox,
    default_tools,
    discover,
    load_expectation,
    load_run_function,
)

MANIFEST = parse_manifest(
    {
        "schema_version": 1,
        "name": "x",
        "description": "testing",
        "declared_tools": [],
        "max_steps": 1,
    }
)


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "expected.toml"
    path.write_text(body)
    return path


def test_toolbox_records_calls_and_counts_steps() -> None:
    box = ToolBox(tools=default_tools())
    box.call("search", query="a")
    box.call("read_file", path="notes.txt")
    assert box.steps == 2
    assert box.tools_used == {"search", "read_file"}
    assert box.calls[1].args == {"path": "notes.txt"}


def test_toolbox_unknown_tool_is_recorded_not_raised() -> None:
    box = ToolBox(tools={})
    assert box.call("shell", cmd="ls").startswith("ERROR: unknown tool")
    assert box.tools_used == {"shell"}


def test_fake_email_tool_reports_length() -> None:
    assert default_tools()["send_email"](to="a@example.invalid", body="hi") == (
        "queued email to a@example.invalid (2 chars)"
    )


def test_pass_expectation_loads(tmp_path: Path) -> None:
    e = load_expectation(_write(tmp_path, 'verdict = "pass"\n'))
    assert (e.verdict, e.reason) == ("pass", None)


def test_fail_expectation_loads(tmp_path: Path) -> None:
    e = load_expectation(_write(tmp_path, 'verdict = "fail"\nreason = "step_budget"\n'))
    assert (e.verdict, e.reason) == ("fail", "step_budget")


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ('verdict = "maybe"\n', "'pass' or 'fail'"),
        ("", "'pass' or 'fail'"),
        ('verdict = "fail"\n', "'reason' is required"),
        ('verdict = "pass"\nreason = "x"\n', "only applies"),
        ('verdict = "pass"\nextra = 1\n', "unknown field"),
    ],
)
def test_invalid_expectations_give_clear_errors(tmp_path: Path, body: str, message: str) -> None:
    with pytest.raises(ExpectationError, match=message):
        load_expectation(_write(tmp_path, body))


def test_agent_file_without_entry_function_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text("x = 1\n")
    with pytest.raises(ImportError, match=r"does not define run\(task, tools\)"):
        load_run_function(tmp_path, MANIFEST)


def test_missing_agent_file_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_run_function(tmp_path, MANIFEST)


def test_custom_entrypoint_is_used(tmp_path: Path) -> None:
    (tmp_path / "bot.py").write_text("def go(task, tools):\n    return 'went'\n")
    manifest = parse_manifest(
        {
            "schema_version": 1,
            "name": "x",
            "description": "d",
            "declared_tools": [],
            "max_steps": 1,
            "entrypoint": "bot.py:go",
        }
    )
    assert load_run_function(tmp_path, manifest)("t", ToolBox(tools={})) == "went"


def test_discover_ignores_folders_without_manifest(tmp_path: Path) -> None:
    (tmp_path / "with").mkdir()
    (tmp_path / "with" / "agent.toml").write_text("")
    (tmp_path / "without").mkdir()
    assert [p.name for p in discover(tmp_path)] == ["with"]
