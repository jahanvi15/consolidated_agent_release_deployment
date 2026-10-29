"""Tests for audit events, the hash chain, verification and output formats (ADR 0009)."""

from __future__ import annotations

import csv
import io
import json
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from consolidated_agent_release_deployment.audit import (
    AuditEvent,
    EventDraft,
    Reason,
    created_event,
    event_fingerprint,
    event_path,
    link,
    to_csv,
    to_markdown,
    verify,
)
from consolidated_agent_release_deployment.store import DirectoryStore, StoreError
from consolidated_agent_release_deployment.version_record import (
    Source,
    VersionRecord,
    load_agent,
    new_record,
)

NOW = datetime(2026, 10, 30, 9, 0, tzinfo=UTC)
SOURCE = Source(platform="local", agent_path="agents/x", commit="c" * 40)


def refused(
    reason: Reason = "possible_secret",
    details: tuple[str, ...] = ("config.api_key: possible secret value",),
) -> EventDraft:
    return EventDraft(
        type="version.refused",
        occurred_at=NOW,
        actor="tester",
        via="local",
        reason=reason,
        details=list(details),
        source=SOURCE,
    )


def record_for(repo: Path, version: int = 1, when: datetime = NOW) -> VersionRecord:
    manifest, content = load_agent(repo / "agents" / "runaway_loop")
    source = Source(platform="local", agent_path="agents/runaway_loop")
    return new_record(
        manifest.name, content, version=version, created_by="tester", source=source, now=when
    )


# ---------- events and the chain ----------


def test_link_numbers_and_chains_events() -> None:
    first, second, third = link([refused(), refused(), refused()], None)
    assert [e.sequence for e in (first, second, third)] == [1, 2, 3]
    assert first.previous is None
    assert second.previous == first.event_id
    assert third.previous == second.event_id
    assert len({first.event_id, second.event_id, third.event_id}) == 3


def test_link_continues_an_existing_chain() -> None:
    (last,) = link([refused()], None)
    (nxt,) = link([refused()], last)
    assert (nxt.sequence, nxt.previous) == (2, last.event_id)


def test_event_id_is_the_fingerprint_of_the_event() -> None:
    (event,) = link([refused()], None)
    assert event.event_id == event_fingerprint(event)
    assert AuditEvent.from_json(event.to_json()) == event


def test_edited_event_fails_to_load() -> None:
    (event,) = link([refused()], None)
    data = json.loads(event.to_json())
    data["actor"] = "someone-else"
    with pytest.raises(ValidationError, match="event_id does not match"):
        AuditEvent.model_validate(data)


def test_only_the_first_event_has_no_previous() -> None:
    (event,) = link([refused()], None)
    data = json.loads(event.to_json())
    data["sequence"] = 2
    with pytest.raises(ValidationError, match="only event 1 has no previous"):
        AuditEvent.model_validate(data)


def test_refused_needs_a_reason() -> None:
    with pytest.raises(ValidationError, match="needs a reason"):
        EventDraft(type="version.refused", occurred_at=NOW, actor="a", via="local", source=SOURCE)


def test_created_needs_agent_version_and_fingerprint() -> None:
    with pytest.raises(ValidationError, match="needs agent, version and fingerprint"):
        EventDraft(type="version.created", occurred_at=NOW, actor="a", via="local", source=SOURCE)


def test_event_time_must_be_utc() -> None:
    india = datetime(2026, 10, 30, 14, 30, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    with pytest.raises(ValidationError, match="must be a UTC time"):
        EventDraft(
            type="version.refused",
            occurred_at=india,
            actor="a",
            via="local",
            reason="invalid_agent",
            source=SOURCE,
        )


def test_created_event_matches_its_record(repo: Path) -> None:
    record = record_for(repo)
    draft = created_event(record)
    assert (draft.agent, draft.version, draft.fingerprint) == (
        "runaway_loop",
        1,
        record.fingerprint,
    )
    assert (draft.actor, draft.via, draft.occurred_at) == ("tester", "local", NOW)


def test_event_path_layout() -> None:
    (event,) = link([refused()], None)
    assert event_path(event) == "audit/2026/10/000000001-20261030T090000Z.json"


# ---------- verify ----------


def saved_store(tmp_path: Path, repo: Path) -> DirectoryStore:
    store = DirectoryStore(tmp_path / "store")
    first = record_for(repo)
    store.save([first], [created_event(first), refused()])
    second = record_for(repo, 2)
    store.save([second], [created_event(second)])
    return store


def test_verify_accepts_an_intact_log(tmp_path: Path, repo: Path) -> None:
    result = verify(*saved_store(tmp_path, repo).load_all())
    assert result.ok, result.problems
    assert result.events == 3
    assert result.notes == []


def test_verify_finds_a_deleted_event(tmp_path: Path, repo: Path) -> None:
    store = saved_store(tmp_path, repo)
    (store.root / store.event_paths()[1]).unlink()
    result = verify(*store.load_all())
    assert "event 3: expected event 2 here" in result.problems


def test_verify_finds_an_edited_event(tmp_path: Path, repo: Path) -> None:
    store = saved_store(tmp_path, repo)
    path = store.root / store.event_paths()[1]
    path.write_text(path.read_text().replace('"tester"', '"intruder"'))
    problems = verify(*store.load_all()).problems
    assert any("event_id does not match" in p for p in problems)
    assert "event 3: expected event 2 here" in problems


def test_verify_finds_a_replaced_chain_link(tmp_path: Path, repo: Path) -> None:
    store = saved_store(tmp_path, repo)
    # Rebuild event 2 from scratch: valid on its own, but not the event that was there.
    other = link([refused("invalid_agent")], store.read_event(store.event_paths()[0]))[0]
    (store.root / store.event_paths()[1]).write_text(other.to_json())
    problems = verify(*store.load_all()).problems
    assert problems == ["event 3: does not point to event 2"]


def test_verify_finds_a_missing_record(tmp_path: Path, repo: Path) -> None:
    store = saved_store(tmp_path, repo)
    (store.root / "records/runaway_loop/000002.json").unlink()
    assert verify(*store.load_all()).problems == ["event 3: record runaway_loop v2 is missing"]


def test_verify_finds_a_record_without_an_event(tmp_path: Path, repo: Path) -> None:
    store = saved_store(tmp_path, repo)
    extra = record_for(repo, 3, when=NOW + timedelta(hours=1))
    (store.root / "records/runaway_loop/000003.json").write_text(extra.to_json())
    assert verify(*store.load_all()).problems == [
        "records/runaway_loop/000003.json: no 'version.created' event for this record"
    ]


def test_records_older_than_the_log_are_only_noted(tmp_path: Path, repo: Path) -> None:
    store = DirectoryStore(tmp_path / "store")
    old = record_for(repo, when=NOW - timedelta(days=1))
    (store.root / "records/runaway_loop").mkdir(parents=True)
    (store.root / "records/runaway_loop/000001.json").write_text(old.to_json())
    store.save([], [refused()])
    result = verify(*store.load_all())
    assert result.ok
    assert result.notes == [
        "records/runaway_loop/000001.json: recorded before the audit log started"
    ]


def test_verify_finds_a_mismatched_fingerprint(tmp_path: Path, repo: Path) -> None:
    store = saved_store(tmp_path, repo)
    # Swap in a valid record for v2 whose content differs from what event 3 recorded.
    (repo / "agents" / "runaway_loop" / "agent.py").write_text("# different\n")
    (store.root / "records/runaway_loop/000002.json").write_text(record_for(repo, 2).to_json())
    assert verify(*store.load_all()).problems == [
        "records/runaway_loop/000002.json: fingerprint differs from event 3"
    ]


def test_verify_reports_unreadable_files(tmp_path: Path, repo: Path) -> None:
    store = saved_store(tmp_path, repo)
    (store.root / "records/runaway_loop/000001.json").write_text("{}")
    first_event = store.root / store.event_paths()[0]
    first_event.write_text("{}")
    problems = verify(*store.load_all()).problems
    assert any(p.startswith("records/runaway_loop/000001.json: ") for p in problems)
    assert any(p.startswith(store.event_paths()[0] + ": ") for p in problems)


def test_verify_finds_a_renamed_event_file(tmp_path: Path, repo: Path) -> None:
    store = saved_store(tmp_path, repo)
    path = store.root / store.event_paths()[2]
    path.rename(path.with_name("000000003-20261031T000000Z.json"))
    problems = verify(*store.load_all()).problems
    assert any("file name does not match event 3" in p for p in problems)


def test_empty_log_is_intact() -> None:
    assert verify([], []).ok


# ---------- saving ----------


def test_a_record_cannot_be_saved_without_its_event(tmp_path: Path, repo: Path) -> None:
    store = DirectoryStore(tmp_path)
    with pytest.raises(StoreError, match="no audit event to go with it"):
        store.save([record_for(repo)], [refused()])
    assert store.event_paths() == []


def test_several_versions_of_one_agent_in_one_save(tmp_path: Path, repo: Path) -> None:
    store = DirectoryStore(tmp_path)
    one, two = record_for(repo), record_for(repo, 2)
    store.save([one, two], [created_event(one), created_event(two)])
    assert store.versions("runaway_loop") == [1, 2]


# ---------- output formats ----------


def test_csv_has_one_row_per_event() -> None:
    events = link([refused(), refused("invalid_agent")], None)
    rows = list(csv.reader(io.StringIO(to_csv(events))))
    assert rows[0][:4] == ["sequence", "occurred_at", "type", "reason"]
    assert rows[1][:4] == ["1", "2026-10-30T09:00:00Z", "version.refused", "possible_secret"]
    assert rows[2][3] == "invalid_agent"
    assert len(rows) == 3


def test_csv_cells_cannot_become_spreadsheet_formulas() -> None:
    draft = refused(details=('=HYPERLINK("http://example.invalid")',))
    (event,) = link([draft], None)
    rows = list(csv.reader(io.StringIO(to_csv([event]))))
    assert rows[1][11] == '\'=HYPERLINK("http://example.invalid")'


def test_markdown_summary_table(repo: Path) -> None:
    record = record_for(repo)
    events = link([created_event(record), refused()], None)
    table = to_markdown(events)
    assert "| 1 | runaway_loop | created | 1 | `" in table
    assert "| 2 | agents/x | refused: possible_secret | - | - |" in table


def test_markdown_escapes_pipes() -> None:
    weird = Source(platform="local", agent_path="a|b")
    draft = EventDraft(
        type="version.refused",
        occurred_at=NOW,
        actor="a",
        via="local",
        reason="invalid_agent",
        source=weird,
    )
    assert "a\\|b" in to_markdown(link([draft], None))
