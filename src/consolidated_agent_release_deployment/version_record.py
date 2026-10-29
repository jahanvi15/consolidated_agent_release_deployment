"""The version record: a permanent description of one version of one agent.

A record has four parts (ADR 0008):

* **Identity** — agent name, a counter (1, 2, 3...) and a *fingerprint* of the content.
* **Content** — what the agent *is*: model, prompts, tools, config, dependencies, and a
  fingerprint of every file in its folder. Small values are copied in; files are only
  fingerprinted (the real file is in Git at the recorded commit).
* **Who and when** — ``created_at`` (UTC) and ``created_by``.
* **Source** — where it was built (GitHub Actions run, commit...). Kept in its own
  section so the content stays the same on every platform.

Same content always gives the same fingerprint. That is how the tool knows "nothing
changed, no new version needed", and how Feature 2 will spot what changed.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from consolidated_agent_release_deployment.manifest import AgentManifest, Scalar, load_manifest

RECORD_SCHEMA_VERSION: Literal[1] = 1
FINGERPRINT_PATTERN = r"^sha256:[0-9a-f]{64}$"

# Never part of an agent's content: caches and tool folders that change on their own.
IGNORED_PARTS = frozenset({"__pycache__", ".git", ".venv", ".mypy_cache", ".pytest_cache"})
IGNORED_SUFFIXES = frozenset({".pyc", ".pyo"})


class _Strict(BaseModel):
    """Shared settings: unknown fields are errors and objects can't be changed."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ModelInfo(_Strict):
    provider: str
    name: str
    settings: dict[str, Scalar] = Field(default_factory=dict)


class RecordContent(_Strict):
    """Everything that defines the agent. The fingerprint is computed from this alone."""

    description: str
    entrypoint: str
    declared_tools: list[str]
    max_steps: int = Field(ge=1)
    model: ModelInfo | None = None
    prompts: list[str] = Field(default_factory=list)
    config: dict[str, Scalar] = Field(default_factory=dict)
    env: list[str] = Field(default_factory=list, description="Variable names only, no values")
    dependencies: list[str] = Field(default_factory=list)
    files: dict[str, str] = Field(description="Path inside the agent folder -> sha256")

    @field_validator("files")
    @classmethod
    def _hashes_look_right(cls, files: dict[str, str]) -> dict[str, str]:
        for path, digest in files.items():
            if not digest.startswith("sha256:") or len(digest) != len("sha256:") + 64:
                raise ValueError(f"{path}: not a sha256 fingerprint")
        return files


class Source(_Strict):
    """Where and from what the version was built. Platform details live only here."""

    platform: Literal["local", "github-actions"]
    agent_path: str
    commit: str | None = None
    uncommitted_changes: bool | None = None
    repository: str | None = None
    ref: str | None = None
    run_id: str | None = None
    run_url: str | None = None


class VersionRecord(_Strict):
    schema_version: Literal[1] = RECORD_SCHEMA_VERSION
    agent: str
    version: int = Field(ge=1)
    fingerprint: str = Field(pattern=FINGERPRINT_PATTERN)
    created_at: datetime
    created_by: str
    content: RecordContent
    source: Source

    @field_validator("created_at")
    @classmethod
    def _must_be_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(None):
            raise ValueError("must be a UTC time, e.g. 2026-10-30T09:00:00Z")
        return value

    @model_validator(mode="after")
    def _fingerprint_matches_content(self) -> VersionRecord:
        # Tamper check: if anyone edits the content, the stored fingerprint no longer fits.
        expected = fingerprint(self.agent, self.content)
        if self.fingerprint != expected:
            raise ValueError("fingerprint does not match content (record was changed?)")
        return self

    def to_json(self) -> str:
        """Pretty JSON for storage and display. Ends with a newline, like any text file."""
        return self.model_dump_json(indent=2) + "\n"

    @classmethod
    def from_json(cls, text: str) -> VersionRecord:
        return cls.model_validate_json(text)


# ---------- fingerprints ----------


def canonical_json(data: object) -> str:
    """One exact text for the same data: keys sorted, no spaces. Needed for stable hashes."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_fingerprint(path: Path) -> str:
    """Fingerprint of one file. Text files ignore Windows vs Linux line endings."""
    data = path.read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return "sha256:" + hashlib.sha256(data).hexdigest()
    return sha256_text(text.replace("\r\n", "\n"))


def fingerprint(agent: str, content: RecordContent) -> str:
    """Fingerprint of an agent's content. Time, counter and source are not included."""
    return sha256_text(canonical_json({"agent": agent, "content": content.model_dump(mode="json")}))


# ---------- building a record from a folder ----------


class ContentError(ValueError):
    """The agent folder doesn't match its manifest (e.g. a listed prompt file is missing)."""


def agent_files(agent_dir: Path) -> dict[str, str]:
    """Fingerprint every file in the agent folder, keyed by a '/'-separated path."""
    files: dict[str, str] = {}
    for path in sorted(agent_dir.rglob("*")):
        relative = path.relative_to(agent_dir)
        if not path.is_file() or IGNORED_PARTS & set(relative.parts):
            continue
        if path.suffix in IGNORED_SUFFIXES:
            continue
        files[relative.as_posix()] = file_fingerprint(path)
    return files


def build_content(agent_dir: Path, manifest: AgentManifest) -> RecordContent:
    files = agent_files(agent_dir)
    missing = [p for p in (manifest.entrypoint_file, *manifest.prompts) if p not in files]
    if missing:
        raise ContentError(f"{agent_dir}: listed in agent.toml but not found: {', '.join(missing)}")
    model = None
    if manifest.model is not None:
        model = ModelInfo(
            provider=manifest.model.provider,
            name=manifest.model.name,
            settings=dict(manifest.model.settings),
        )
    return RecordContent(
        description=manifest.description,
        entrypoint=manifest.entrypoint,
        declared_tools=list(manifest.declared_tools),
        max_steps=manifest.max_steps,
        model=model,
        prompts=list(manifest.prompts),
        config=dict(manifest.config),
        env=list(manifest.env),
        dependencies=list(manifest.dependencies),
        files=files,
    )


def load_agent(agent_dir: Path) -> tuple[AgentManifest, RecordContent]:
    manifest = load_manifest(agent_dir / "agent.toml")
    return manifest, build_content(agent_dir, manifest)


def new_record(
    agent: str,
    content: RecordContent,
    *,
    version: int,
    created_by: str,
    source: Source,
    now: datetime | None = None,
) -> VersionRecord:
    """Assemble a record. ``now`` can be passed in so tests get a fixed time."""
    created_at = (now or datetime.now(UTC)).astimezone(UTC).replace(microsecond=0)
    return VersionRecord(
        agent=agent,
        version=version,
        fingerprint=fingerprint(agent, content),
        created_at=created_at,
        created_by=created_by,
        content=content,
        source=source,
    )
