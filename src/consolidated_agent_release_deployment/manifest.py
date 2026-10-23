"""Agent manifest (``agent.toml``): the schema, loading and validation.

Every agent checked by this tool describes itself in an ``agent.toml`` file. The
compliance checks compare what an agent *does* against what its manifest *declares*,
so the manifest must be strictly validated: a typo such as ``max_step = 5`` must be an
error, not silently ignored.

Validation collects **every** problem before raising, so a user fixes their file in
one pass instead of one error at a time. See ``docs/agent-manifest.md``.
"""

from __future__ import annotations

import difflib
import re
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

SCHEMA_VERSION = 1
DEFAULT_ENTRYPOINT = "agent.py:run"
MAX_STEPS_LIMIT = 10_000

_NAME = re.compile(r"[a-z][a-z0-9_-]{0,63}")
_TOOL = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,63}")
_ENTRYPOINT = re.compile(r"(?P<file>[A-Za-z0-9_./-]+\.py):(?P<func>[A-Za-z_][A-Za-z0-9_]*)")

REQUIRED_FIELDS = ("schema_version", "name", "description", "declared_tools", "max_steps")
OPTIONAL_FIELDS = ("entrypoint",)
KNOWN_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS


@dataclass(frozen=True)
class Issue:
    """One problem found in a manifest."""

    field: str
    message: str

    def __str__(self) -> str:
        return f"{self.field}: {self.message}"


class ManifestError(ValueError):
    """Raised when a manifest cannot be read or is invalid. Lists every issue found."""

    def __init__(self, source: str, issues: Sequence[Issue]) -> None:
        self.source = source
        self.issues = tuple(issues)
        count = len(self.issues)
        lines = [f"{source}: {count} problem{'s' if count != 1 else ''} in agent manifest"]
        lines += [f"  - {issue}" for issue in self.issues]
        super().__init__("\n".join(lines))


@dataclass(frozen=True)
class AgentManifest:
    """A validated agent manifest. Construct it with ``load_manifest`` or ``parse_manifest``."""

    schema_version: int
    name: str
    description: str
    declared_tools: tuple[str, ...]
    max_steps: int
    entrypoint: str = DEFAULT_ENTRYPOINT

    @property
    def entrypoint_file(self) -> str:
        return self.entrypoint.split(":", 1)[0]

    @property
    def entrypoint_function(self) -> str:
        return self.entrypoint.split(":", 1)[1]


def load_manifest(path: Path) -> AgentManifest:
    """Read and validate an ``agent.toml`` file."""
    source = str(path)
    try:
        with path.open("rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        raise ManifestError(source, [Issue("file", "not found")]) from None
    except tomllib.TOMLDecodeError as exc:
        raise ManifestError(source, [Issue("file", f"invalid TOML: {exc}")]) from None
    return parse_manifest(data, source=source)


def parse_manifest(data: Mapping[str, object], source: str = "<manifest>") -> AgentManifest:
    """Validate already-parsed manifest data. Raises ``ManifestError`` listing all issues."""
    issues: list[Issue] = []

    for key in data:
        if key not in KNOWN_FIELDS:
            issues.append(Issue(key, _unknown_field_message(key)))
    for key in REQUIRED_FIELDS:
        if key not in data:
            issues.append(Issue(key, "required field is missing"))

    schema_version = _check_schema_version(data, issues)
    name = _check_name(data, issues)
    description = _check_description(data, issues)
    tools = _check_tools(data, issues)
    max_steps = _check_max_steps(data, issues)
    entrypoint = _check_entrypoint(data, issues)

    if (
        issues
        or schema_version is None
        or name is None
        or description is None
        or tools is None
        or max_steps is None
    ):
        raise ManifestError(source, issues)
    return AgentManifest(
        schema_version=schema_version,
        name=name,
        description=description,
        declared_tools=tools,
        max_steps=max_steps,
        entrypoint=entrypoint,
    )


# ---------- individual field checks ----------
# Each returns the cleaned value, or None after appending an Issue. A missing required
# field returns None silently: it was already reported above.


def _unknown_field_message(key: str) -> str:
    close = difflib.get_close_matches(key, KNOWN_FIELDS, n=1)
    hint = f"; did you mean {close[0]!r}?" if close else ""
    return f"unknown field{hint} (allowed: {', '.join(KNOWN_FIELDS)})"


def _check_schema_version(data: Mapping[str, object], issues: list[Issue]) -> int | None:
    if "schema_version" not in data:
        return None
    value = data["schema_version"]
    # In Python, True/False are also ints (True == 1), so booleans are rejected explicitly.
    if isinstance(value, bool) or not isinstance(value, int):
        issues.append(Issue("schema_version", f"must be the integer {SCHEMA_VERSION}"))
        return None
    if value != SCHEMA_VERSION:
        issues.append(
            Issue(
                "schema_version",
                f"unsupported version {value}; this tool supports {SCHEMA_VERSION}",
            )
        )
        return None
    return value


def _check_name(data: Mapping[str, object], issues: list[Issue]) -> str | None:
    if "name" not in data:
        return None
    value = data["name"]
    if not isinstance(value, str) or not _NAME.fullmatch(value):
        issues.append(
            Issue(
                "name",
                "must be 1-64 characters: lowercase letters, digits, '_' or '-', "
                "starting with a letter",
            )
        )
        return None
    return value


def _check_description(data: Mapping[str, object], issues: list[Issue]) -> str | None:
    if "description" not in data:
        return None
    value = data["description"]
    if not isinstance(value, str) or not value.strip():
        issues.append(Issue("description", "must be a non-empty string"))
        return None
    return value.strip()


def _check_tools(data: Mapping[str, object], issues: list[Issue]) -> tuple[str, ...] | None:
    if "declared_tools" not in data:
        return None
    value = data["declared_tools"]
    if not isinstance(value, list):
        issues.append(Issue("declared_tools", 'must be a list of tool names, e.g. ["search"]'))
        return None
    ok = True
    seen: set[str] = set()
    for i, tool in enumerate(value):
        where = f"declared_tools[{i}]"
        if not isinstance(tool, str) or not _TOOL.fullmatch(tool):
            issues.append(
                Issue(
                    where,
                    "tool names must be 1-64 characters: letters, digits, '_', '.' or '-', "
                    "starting with a letter",
                )
            )
            ok = False
        elif tool in seen:
            issues.append(Issue(where, f"{tool!r} is listed more than once"))
            ok = False
        else:
            seen.add(tool)
    return tuple(value) if ok else None


def _check_max_steps(data: Mapping[str, object], issues: list[Issue]) -> int | None:
    if "max_steps" not in data:
        return None
    value = data["max_steps"]
    # `max_steps = true` would otherwise count as 1, because bool is a subclass of int.
    if isinstance(value, bool) or not isinstance(value, int):
        issues.append(Issue("max_steps", "must be a whole number"))
        return None
    if not 1 <= value <= MAX_STEPS_LIMIT:
        issues.append(Issue("max_steps", f"must be between 1 and {MAX_STEPS_LIMIT}"))
        return None
    return value


def _check_entrypoint(data: Mapping[str, object], issues: list[Issue]) -> str:
    value = data.get("entrypoint", DEFAULT_ENTRYPOINT)
    match = _ENTRYPOINT.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        issues.append(Issue("entrypoint", "must look like 'agent.py:run' (file:function)"))
        return DEFAULT_ENTRYPOINT
    file = PurePosixPath(match["file"])
    # Security: the entrypoint must stay inside the agent's own folder.
    if file.is_absolute() or ".." in file.parts:
        issues.append(Issue("entrypoint", "file must be inside the agent folder (no '..' or '/')"))
        return DEFAULT_ENTRYPOINT
    return str(value)
