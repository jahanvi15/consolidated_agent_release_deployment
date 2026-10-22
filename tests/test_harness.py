from __future__ import annotations

from pathlib import Path

import pytest

from sample_agents.harness import (
    ManifestError,
    ToolBox,
    default_tools,
    discover,
    load_manifest,
    load_run_function,
)

VALID = """
name = "x"
purpose = "testing"
declared_tools = ["search"]
max_steps = 2
expected = "pass"
"""


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "agent.toml"
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


def test_valid_manifest_loads(tmp_path: Path) -> None:
    m = load_manifest(_write(tmp_path, VALID))
    assert m.declared_tools == ("search",)
    assert m.expected_verdict == "pass"
    assert m.expected_reason is None


@pytest.mark.parametrize(
    ("body", "message"),
    [
        (VALID.replace('name = "x"\n', ""), "missing required field 'name'"),
        (VALID.replace('purpose = "testing"', "purpose = 3"), "'purpose' must be a string"),
        (VALID.replace("max_steps = 2", "max_steps = true"), "'max_steps' must be an integer"),
        (VALID.replace("max_steps = 2", "max_steps = 0"), "at least 1"),
        (VALID.replace('["search"]', "[1]"), "list of strings"),
        (VALID.replace('"pass"', '"maybe"'), "'pass' or 'fail'"),
        (VALID.replace('"pass"', '"fail"'), "'expected_reason' is required"),
        (VALID + 'expected_reason = "x"\n', "only applies"),
    ],
)
def test_invalid_manifests_give_clear_errors(tmp_path: Path, body: str, message: str) -> None:
    with pytest.raises(ManifestError, match=message):
        load_manifest(_write(tmp_path, body))


def test_agent_file_without_run_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text("x = 1\n")
    with pytest.raises(ImportError, match="does not define run"):
        load_run_function(tmp_path)


def test_missing_agent_file_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_run_function(tmp_path)


def test_discover_ignores_folders_without_manifest(tmp_path: Path) -> None:
    (tmp_path / "with").mkdir()
    (tmp_path / "with" / "agent.toml").write_text(VALID)
    (tmp_path / "without").mkdir()
    assert [p.name for p in discover(tmp_path)] == ["with"]
