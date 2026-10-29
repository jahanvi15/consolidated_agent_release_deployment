"""The audit log: what happened, when, and who did it (ADR 0009).

A version record says *what a version is*. An audit event says *what happened*:
a version was created, an agent was checked and found unchanged, or the tool refused
to record it (possible secret, uncommitted changes, invalid agent).

Events form a **hash chain**. Every event has

* ``sequence`` — 1, 2, 3... across the whole log, with no gaps;
* ``previous`` — the ``event_id`` of the event before it;
* ``event_id`` — the SHA-256 fingerprint of the event itself, including ``previous``.

Changing or deleting any event changes its fingerprint, so the next event no longer
points to it, and ``verify`` finds the break.

Layout: ``audit/<YYYY>/<MM>/<sequence, 9 digits>-<YYYYMMDDTHHMMSSZ>.json``, one file per
event, never edited.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Literal

from pydantic import Field, field_validator, model_validator

from consolidated_agent_release_deployment.version_record import (
    FINGERPRINT_PATTERN,
    Source,
    StrictModel,
    VersionRecord,
    canonical_json,
    sha256_text,
)

AUDIT_DIR = "audit"
EVENT_SCHEMA_VERSION: Literal[1] = 1

EventType = Literal["version.created", "version.unchanged", "version.refused"]
Reason = Literal["possible_secret", "uncommitted_changes", "invalid_agent"]


class EventDraft(StrictModel):
    """An event before it joins the chain (no sequence, previous or id yet)."""

    type: EventType
    occurred_at: datetime
    actor: str = Field(description="The person: GitHub login, or Git user name locally")
    via: Literal["local", "github-actions"] = Field(description="The system acting for them")
    agent: str | None = None
    version: int | None = Field(default=None, ge=1)
    fingerprint: str | None = Field(default=None, pattern=FINGERPRINT_PATTERN)
    reason: Reason | None = None
    details: list[str] = Field(default_factory=list)
    source: Source

    @field_validator("occurred_at")
    @classmethod
    def _must_be_utc(cls, value: datetime) -> datetime:
        if value.utcoffset() != timedelta(0):
            raise ValueError("must be a UTC time, e.g. 2026-10-30T09:00:00Z")
        return value

    @model_validator(mode="after")
    def _fields_fit_the_type(self) -> EventDraft:
        if self.type == "version.refused":
            if self.reason is None:
                raise ValueError("a refused event needs a reason")
        elif self.reason is not None or None in (self.agent, self.version, self.fingerprint):
            raise ValueError(f"{self.type} needs agent, version and fingerprint, and no reason")
        return self


class AuditEvent(EventDraft):
    """An event in the chain. Built by ``link``; checked again whenever it is read."""

    schema_version: Literal[1] = EVENT_SCHEMA_VERSION
    sequence: int = Field(ge=1)
    previous: str | None = Field(pattern=FINGERPRINT_PATTERN)
    event_id: str = Field(pattern=FINGERPRINT_PATTERN)

    @model_validator(mode="after")
    def _chain_fields_are_consistent(self) -> AuditEvent:
        if (self.sequence == 1) != (self.previous is None):
            raise ValueError("only event 1 has no previous event")
        if self.event_id != event_fingerprint(self):
            raise ValueError("event_id does not match the event (event was changed?)")
        return self

    def to_json(self) -> str:
        return self.model_dump_json(indent=2) + "\n"

    @classmethod
    def from_json(cls, text: str) -> AuditEvent:
        return cls.model_validate_json(text)


def event_fingerprint(event: EventDraft) -> str:
    """Fingerprint of everything in the event except ``event_id`` itself."""
    data = event.model_dump(mode="json", exclude={"event_id"})
    return sha256_text(canonical_json(data))


def event_path(event: AuditEvent) -> str:
    t = event.occurred_at
    return f"{AUDIT_DIR}/{t:%Y}/{t:%m}/{event.sequence:09d}-{t:%Y%m%dT%H%M%SZ}.json"


def link(drafts: Sequence[EventDraft], last: AuditEvent | None) -> list[AuditEvent]:
    """Give each draft its sequence number and chain it to the one before."""
    events: list[AuditEvent] = []
    for draft in drafts:
        previous = events[-1] if events else last
        chain = {
            "schema_version": EVENT_SCHEMA_VERSION,
            "sequence": previous.sequence + 1 if previous else 1,
            "previous": previous.event_id if previous else None,
        }
        # The id is the fingerprint of everything else, exactly as event_fingerprint sees it.
        event_id = sha256_text(canonical_json({**draft.model_dump(mode="json"), **chain}))
        events.append(AuditEvent(**draft.model_dump(), **chain, event_id=event_id))
    return events


def created_event(record: VersionRecord) -> EventDraft:
    """The event that goes with saving a new record."""
    return EventDraft(
        type="version.created",
        occurred_at=record.created_at,
        actor=record.created_by,
        via=record.source.platform,
        agent=record.agent,
        version=record.version,
        fingerprint=record.fingerprint,
        source=record.source,
    )


# ---------- checking the whole log ----------


@dataclass
class Verification:
    """Result of ``verify``: problems mean the log can't be trusted as it is."""

    events: int = 0
    problems: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems


def verify(
    events: Sequence[tuple[str, AuditEvent | str]],
    records: Sequence[tuple[str, VersionRecord | str]],
) -> Verification:
    """Check the chain, and that events and records match each other.

    Both lists hold ``(path, object)`` pairs, or ``(path, error message)`` for files that
    could not be read, so one broken file is reported instead of stopping everything.
    """
    result = Verification()
    chain: list[AuditEvent] = []
    for path, event_or_error in events:
        if isinstance(event_or_error, str):
            result.problems.append(f"{path}: {event_or_error}")
            continue
        item = event_or_error
        if event_path(item) != path:
            result.problems.append(f"{path}: file name does not match event {item.sequence}")
        chain.append(item)
    chain.sort(key=lambda e: e.sequence)
    result.events = len(chain)

    previous: AuditEvent | None = None
    for event in chain:
        expected = previous.sequence + 1 if previous else 1
        if event.sequence != expected:
            result.problems.append(f"event {event.sequence}: expected event {expected} here")
        elif previous is not None and event.previous != previous.event_id:
            result.problems.append(
                f"event {event.sequence}: does not point to event {expected - 1}"
            )
        previous = event

    by_version: dict[tuple[str | None, int | None], AuditEvent] = {
        (e.agent, e.version): e for e in chain if e.type == "version.created"
    }
    first_event_time = chain[0].occurred_at if chain else None
    for path, record_or_error in records:
        if isinstance(record_or_error, str):
            result.problems.append(f"{path}: {record_or_error}")
            continue
        record = record_or_error
        key = (record.agent, record.version)
        matched = by_version.get(key)
        if matched is not None:
            del by_version[key]
            if matched.fingerprint != record.fingerprint:
                result.problems.append(f"{path}: fingerprint differs from event {matched.sequence}")
        elif first_event_time is None or record.created_at < first_event_time:
            result.notes.append(f"{path}: recorded before the audit log started")
        else:
            result.problems.append(f"{path}: no 'version.created' event for this record")
    leftover = list(by_version.values())
    for event in sorted(leftover, key=lambda e: e.sequence):
        agent, version = event.agent, event.version
        result.problems.append(f"event {event.sequence}: record {agent} v{version} is missing")
    return result


# ---------- output formats ----------

CSV_COLUMNS = (
    "sequence",
    "occurred_at",
    "type",
    "reason",
    "agent",
    "version",
    "fingerprint",
    "actor",
    "via",
    "commit",
    "run_url",
    "details",
    "event_id",
)


def _safe_cell(value: str) -> str:
    # Spreadsheets run a cell starting with = + - @ as a formula ("CSV injection").
    # A leading apostrophe makes them show it as plain text instead.
    return "'" + value if value[:1] in ("=", "+", "-", "@", "\t", "\r") else value


def to_csv(events: Iterable[AuditEvent]) -> str:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(CSV_COLUMNS)
    for e in events:
        row = [
            e.sequence,
            e.occurred_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            e.type,
            e.reason or "",
            e.agent or "",
            e.version or "",
            e.fingerprint or "",
            e.actor,
            e.via,
            e.source.commit or "",
            e.source.run_url or "",
            "; ".join(e.details),
            e.event_id,
        ]
        writer.writerow([_safe_cell(str(v)) for v in row])
    return out.getvalue()


def to_markdown(events: Sequence[AuditEvent]) -> str:
    """A short table for the GitHub Actions run summary page."""
    lines = [
        "### Agent version records",
        "",
        "| # | Agent | Result | Version | Fingerprint |",
        "|---|-------|--------|---------|-------------|",
    ]
    for e in events:
        result = {"version.created": "created", "version.unchanged": "unchanged"}.get(
            e.type, f"refused: {e.reason}"
        )
        agent = (e.agent or e.source.agent_path).replace("|", "\\|")
        version = str(e.version) if e.version else "-"
        short = f"`{e.fingerprint[7:19]}`" if e.fingerprint else "-"
        lines.append(f"| {e.sequence} | {agent} | {result} | {version} | {short} |")
    return "\n".join(lines) + "\n"
