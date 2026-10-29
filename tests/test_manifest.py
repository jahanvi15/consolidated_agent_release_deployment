"""Tests for the agent manifest schema (backlog S1-1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from consolidated_agent_release_deployment.manifest import (
    DEFAULT_ENTRYPOINT,
    AgentManifest,
    Issue,
    ManifestError,
    ModelSpec,
    load_manifest,
    parse_manifest,
)


def valid(**overrides: object) -> dict[str, object]:
    """A valid manifest as parsed TOML data, with optional fields replaced or removed."""
    data: dict[str, object] = {
        "schema_version": 1,
        "name": "demo_agent",
        "description": "A demo agent.",
        "declared_tools": ["search", "read_file"],
        "max_steps": 5,
    }
    for key, value in overrides.items():
        if value is REMOVE:
            data.pop(key, None)
        else:
            data[key] = value
    return data


REMOVE = object()


def issues_for(data: dict[str, object]) -> list[str]:
    with pytest.raises(ManifestError) as exc:
        parse_manifest(data)
    return [str(i) for i in exc.value.issues]


# ---------- happy path ----------


def test_valid_manifest_parses_into_typed_object() -> None:
    m = parse_manifest(valid())
    assert m == AgentManifest(
        schema_version=1,
        name="demo_agent",
        description="A demo agent.",
        declared_tools=("search", "read_file"),
        max_steps=5,
    )


def test_entrypoint_defaults_and_splits() -> None:
    m = parse_manifest(valid())
    assert m.entrypoint == DEFAULT_ENTRYPOINT == "agent.py:run"
    assert (m.entrypoint_file, m.entrypoint_function) == ("agent.py", "run")


def test_custom_entrypoint_in_subfolder() -> None:
    m = parse_manifest(valid(entrypoint="src/my_agent.py:main"))
    assert (m.entrypoint_file, m.entrypoint_function) == ("src/my_agent.py", "main")


def test_empty_tool_list_is_allowed() -> None:
    assert parse_manifest(valid(declared_tools=[])).declared_tools == ()


def test_description_whitespace_is_trimmed() -> None:
    assert parse_manifest(valid(description="  hi  ")).description == "hi"


# ---------- every problem is reported at once ----------


def test_all_problems_reported_together() -> None:
    problems = issues_for(valid(name="Bad Name", max_steps=0, description=REMOVE))
    assert len(problems) == 3
    assert problems[0] == "description: required field is missing"
    assert problems[1].startswith("name: must be 1-64 characters")
    assert problems[2] == "max_steps: must be between 1 and 10000"


def test_error_message_lists_source_and_each_problem() -> None:
    with pytest.raises(ManifestError) as exc:
        parse_manifest(valid(name=3, max_steps=0), source="agents/x/agent.toml")
    text = str(exc.value)
    assert text.splitlines()[0] == "agents/x/agent.toml: 2 problems in agent manifest"
    assert "  - name: must be" in text
    assert "  - max_steps: must be between 1 and 10000" in text


def test_single_problem_uses_singular_wording() -> None:
    with pytest.raises(ManifestError, match="1 problem in agent manifest"):
        parse_manifest(valid(max_steps=0))


def test_issue_str() -> None:
    assert str(Issue("name", "bad")) == "name: bad"


# ---------- individual rules ----------


@pytest.mark.parametrize(
    "field",
    ["schema_version", "name", "description", "declared_tools", "max_steps"],
)
def test_required_fields(field: str) -> None:
    assert issues_for(valid(**{field: REMOVE})) == [f"{field}: required field is missing"]


def test_unknown_field_suggests_closest_match() -> None:
    data = valid()
    data["max_step"] = 5
    [problem] = issues_for(data)
    assert problem.startswith("max_step: unknown field; did you mean 'max_steps'?")


def test_unknown_field_without_close_match_lists_allowed() -> None:
    data = valid()
    data["colour"] = "blue"
    [problem] = issues_for(data)
    assert problem.startswith("colour: unknown field (allowed: schema_version, name,")


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"schema_version": "1"}, "schema_version: must be the integer 1"),
        ({"schema_version": True}, "schema_version: must be the integer 1"),
        ({"schema_version": 2}, "schema_version: unsupported version 2; this tool supports 1"),
        ({"description": ""}, "description: must be a non-empty string"),
        ({"description": "   "}, "description: must be a non-empty string"),
        ({"description": 7}, "description: must be a non-empty string"),
        ({"max_steps": "5"}, "max_steps: must be a whole number"),
        ({"max_steps": 2.5}, "max_steps: must be a whole number"),
        ({"max_steps": True}, "max_steps: must be a whole number"),
        ({"max_steps": 0}, "max_steps: must be between 1 and 10000"),
        ({"max_steps": 10_001}, "max_steps: must be between 1 and 10000"),
        ({"declared_tools": "search"}, "declared_tools: must be a list of tool names"),
        ({"declared_tools": ["search", "search"]}, "'search' is listed more than once"),
        ({"declared_tools": ["ok", 5]}, "declared_tools[1]: tool names must be"),
        ({"declared_tools": [""]}, "declared_tools[0]: tool names must be"),
        ({"declared_tools": ["1st_tool"]}, "declared_tools[0]: tool names must be"),
        ({"entrypoint": "agent.py"}, "entrypoint: must look like 'agent.py:run'"),
        ({"entrypoint": "agent.js:run"}, "entrypoint: must look like 'agent.py:run'"),
        ({"entrypoint": 5}, "entrypoint: must look like 'agent.py:run'"),
        ({"entrypoint": "../outside.py:run"}, "entrypoint: file must be inside the agent folder"),
        ({"entrypoint": "/etc/evil.py:run"}, "entrypoint: file must be inside the agent folder"),
    ],
)
def test_invalid_values(overrides: dict[str, object], expected: str) -> None:
    [problem] = issues_for(valid(**overrides))
    assert expected in problem


@pytest.mark.parametrize("name", ["a", "my-agent", "agent_2", "x" * 64])
def test_valid_names(name: str) -> None:
    assert parse_manifest(valid(name=name)).name == name


@pytest.mark.parametrize("name", ["", "Agent", "2agent", "my agent", "x" * 65, "agent!"])
def test_invalid_names(name: str) -> None:
    [problem] = issues_for(valid(name=name))
    assert problem.startswith("name: must be 1-64 characters")


@pytest.mark.parametrize("tool", ["search", "read_file", "github.create-issue", "T"])
def test_valid_tool_names(tool: str) -> None:
    assert parse_manifest(valid(declared_tools=[tool])).declared_tools == (tool,)


# ---------- loading files ----------


def test_load_manifest_from_file(tmp_path: Path) -> None:
    path = tmp_path / "agent.toml"
    path.write_text(
        'schema_version = 1\nname = "a"\ndescription = "d"\n'
        'declared_tools = ["search"]\nmax_steps = 1\n'
    )
    assert load_manifest(path).name == "a"


def test_missing_file_is_a_clear_error(tmp_path: Path) -> None:
    with pytest.raises(ManifestError, match="file: not found"):
        load_manifest(tmp_path / "agent.toml")


def test_toml_syntax_error_reports_line(tmp_path: Path) -> None:
    path = tmp_path / "agent.toml"
    path.write_text('schema_version = 1\nname = "unterminated\n')
    with pytest.raises(ManifestError) as exc:
        load_manifest(path)
    assert str(path) in str(exc.value)
    assert "file: invalid TOML" in str(exc.value)
    assert "line 2" in str(exc.value)


# ---------- optional fields used by the version record (Feature 1) ----------


def test_full_manifest_with_every_optional_field() -> None:
    m = parse_manifest(
        valid(
            prompts=["prompts/system.md"],
            env=["SEARCH_API_KEY"],
            dependencies=["httpx>=0.27", "pydantic[email]==2.9"],
            model={"provider": "fake", "name": "m1", "settings": {"temperature": 0.2}},
            config={"style": "short", "retries": 2, "verbose": False},
        )
    )
    assert m.prompts == ("prompts/system.md",)
    assert m.env == ("SEARCH_API_KEY",)
    assert m.dependencies == ("httpx>=0.27", "pydantic[email]==2.9")
    assert m.model == ModelSpec(provider="fake", name="m1", settings={"temperature": 0.2})
    assert m.config == {"style": "short", "retries": 2, "verbose": False}


def test_optional_fields_default_to_empty() -> None:
    m = parse_manifest(valid())
    assert (m.prompts, m.env, m.dependencies, m.model, m.config) == ((), (), (), None, {})


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"prompts": "p.md"}, "prompts: must be a list of file paths"),
        ({"prompts": ["../outside.md"]}, "prompts[0]: file must be inside the agent folder"),
        ({"prompts": ["/etc/passwd"]}, "prompts[0]: file must be inside the agent folder"),
        ({"prompts": ["prompts\\win.md"]}, "prompts[0]: file must be inside the agent folder"),
        ({"env": ["search_key"]}, "env[0]: must be one of: UPPER_SNAKE_CASE names"),
        ({"env": ["A", "A"]}, "env[1]: 'A' is listed more than once"),
        ({"dependencies": ["not a package!"]}, "dependencies[0]: must be one of"),
        ({"model": "gpt"}, "model: must be a table"),
        ({"model": {"provider": "x"}}, "model.name: must be a non-empty string"),
        ({"model": {"provider": "x", "name": "y", "size": 1}}, "model.size: unknown field"),
        ({"config": []}, "config: must be a table"),
        ({"config": {"nested": {"a": 1}}}, "config.nested: must be text, a number"),
        ({"config": {"bad key": 1}}, "config.bad key: key must be letters"),
        (
            {"model": {"provider": "x", "name": "y", "settings": {"l": [1]}}},
            "model.settings.l: must be text, a number",
        ),
    ],
)
def test_invalid_optional_fields(overrides: dict[str, object], expected: str) -> None:
    assert any(p.startswith(expected) for p in issues_for(valid(**overrides))), issues_for(
        valid(**overrides)
    )
