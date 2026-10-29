"""Tests for building, fingerprinting and validating version records (Feature 1)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from consolidated_agent_release_deployment.version_record import (
    ContentError,
    Source,
    VersionRecord,
    agent_files,
    canonical_json,
    file_fingerprint,
    fingerprint,
    load_agent,
    new_record,
)

NOW = datetime(2026, 10, 30, 9, 0, 0, 123, tzinfo=UTC)
LOCAL = Source(platform="local", agent_path="agents/helpful_summarizer")


def make(agent_dir: Path, version: int = 1) -> VersionRecord:
    manifest, content = load_agent(agent_dir)
    return new_record(
        manifest.name, content, version=version, created_by="tester", source=LOCAL, now=NOW
    )


def test_record_copies_small_values_and_fingerprints_files(repo: Path) -> None:
    record = make(repo / "agents" / "helpful_summarizer")
    c = record.content
    assert record.agent == "helpful_summarizer"
    assert c.model is not None
    assert c.model.name == "deterministic-v1"
    assert c.model.settings == {"temperature": 0.0, "max_output_tokens": 400}
    assert c.config == {"summary_style": "bullet points", "max_results": 3}
    assert c.env == ["SEARCH_API_KEY"]
    assert c.prompts == ["prompts/system.md"]
    assert set(c.files) >= {"agent.py", "agent.toml", "prompts/system.md"}
    assert all(h.startswith("sha256:") for h in c.files.values())


def test_time_is_utc_without_microseconds(repo: Path) -> None:
    record = make(repo / "agents" / "helpful_summarizer")
    assert record.created_at == datetime(2026, 10, 30, 9, 0, 0, tzinfo=UTC)


def test_same_content_same_fingerprint_regardless_of_time_or_counter(repo: Path) -> None:
    agent = repo / "agents" / "helpful_summarizer"
    assert make(agent, 1).fingerprint == make(agent, 7).fingerprint


def test_any_file_change_changes_the_fingerprint(repo: Path) -> None:
    agent = repo / "agents" / "helpful_summarizer"
    before = make(agent).fingerprint
    (agent / "prompts" / "system.md").write_text("A different prompt.\n")
    assert make(agent).fingerprint != before


def test_windows_line_endings_do_not_change_the_fingerprint(tmp_path: Path) -> None:
    (tmp_path / "unix.txt").write_bytes(b"line 1\nline 2\n")
    (tmp_path / "windows.txt").write_bytes(b"line 1\r\nline 2\r\n")
    assert file_fingerprint(tmp_path / "unix.txt") == file_fingerprint(tmp_path / "windows.txt")


def test_binary_files_are_hashed_as_is(tmp_path: Path) -> None:
    (tmp_path / "a.bin").write_bytes(b"\xff\x00\r\n")
    (tmp_path / "b.bin").write_bytes(b"\xff\x00\n")
    assert file_fingerprint(tmp_path / "a.bin") != file_fingerprint(tmp_path / "b.bin")


def test_caches_are_not_part_of_the_content(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text("x = 1\n")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "agent.cpython-313.pyc").write_bytes(b"\x00")
    (tmp_path / "old.pyc").write_bytes(b"\x00")
    assert list(agent_files(tmp_path)) == ["agent.py"]


def test_missing_prompt_file_is_an_error(repo: Path) -> None:
    agent = repo / "agents" / "helpful_summarizer"
    (agent / "prompts" / "system.md").unlink()
    with pytest.raises(ContentError, match=r"not found: prompts/system\.md"):
        load_agent(agent)


def test_canonical_json_ignores_key_order() -> None:
    assert (
        canonical_json({"b": 1, "a": [2]})
        == canonical_json({"a": [2], "b": 1})
        == ('{"a":[2],"b":1}')
    )


def test_json_round_trip(repo: Path) -> None:
    record = make(repo / "agents" / "helpful_summarizer")
    text = record.to_json()
    assert text.endswith("}\n")
    assert VersionRecord.from_json(text) == record


def test_edited_record_fails_the_tamper_check(repo: Path) -> None:
    data = json.loads(make(repo / "agents" / "helpful_summarizer").to_json())
    data["content"]["max_steps"] = 999
    with pytest.raises(ValidationError, match="fingerprint does not match content"):
        VersionRecord.model_validate(data)


def test_unknown_fields_are_rejected(repo: Path) -> None:
    data = json.loads(make(repo / "agents" / "helpful_summarizer").to_json())
    data["surprise"] = True
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        VersionRecord.model_validate(data)


def test_bad_file_hash_is_rejected(repo: Path) -> None:
    data = json.loads(make(repo / "agents" / "helpful_summarizer").to_json())
    data["content"]["files"]["agent.py"] = "md5:abc"
    with pytest.raises(ValidationError, match="not a sha256 fingerprint"):
        VersionRecord.model_validate(data)


def test_non_utc_time_is_rejected(repo: Path) -> None:
    record = make(repo / "agents" / "helpful_summarizer")
    data = json.loads(record.to_json())
    data["created_at"] = datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    with pytest.raises(ValidationError, match="must be a UTC time"):
        VersionRecord.model_validate(data)


def test_records_are_frozen(repo: Path) -> None:
    record = make(repo / "agents" / "helpful_summarizer")
    with pytest.raises(ValidationError):
        record.version = 2  # type: ignore[misc]  # proving that assignment is refused


def test_fingerprint_depends_on_agent_name(repo: Path) -> None:
    _, content = load_agent(repo / "agents" / "helpful_summarizer")
    assert fingerprint("a", content) != fingerprint("b", content)
