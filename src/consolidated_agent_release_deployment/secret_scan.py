"""Find things that look like secrets before they are saved anywhere.

A version record is kept forever (records are never edited), so a secret that slips
into one can never be removed. This scan is the safety net: if anything looks like a
key, the record is blocked and nothing is written.

Two kinds of check:

* **Known key shapes** in any text, e.g. ``sk-...`` (AI provider keys) or ``ghp_...``
  (GitHub tokens).
* **Suspicious setting names**: a ``[config]`` entry called ``api_key`` or ``password``
  means a value was written where only a *name* belongs. Such values go in ``env``.

The scan reports where it found a problem but never prints the secret itself.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

# Each pattern: (label, regex). Shapes come from the providers' published formats.
KEY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("AI provider API key (sk-...)", re.compile(r"sk-[A-Za-z0-9_-]{8,}")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
)

SECRET_NAME = re.compile(
    r"(secret|token(?!s)|passw(or)?d|api[_.-]?key|private[_.-]?key|credential)", re.IGNORECASE
)


@dataclass(frozen=True)
class Finding:
    """One suspected secret. ``where`` says where it is; the value is never stored."""

    where: str
    kind: str

    def __str__(self) -> str:
        return f"{self.where}: possible {self.kind}"


def scan_text(text: str, where: str) -> list[Finding]:
    """Every known key shape found in ``text``."""
    return [Finding(where, label) for label, pattern in KEY_PATTERNS if pattern.search(text)]


def scan_settings(settings: Mapping[str, object], where: str) -> list[Finding]:
    """Settings whose *name* suggests a secret value was written down.

    Only text values count: ``max_output_tokens = 400`` is a number, not a secret.
    """
    findings = []
    for key, value in settings.items():
        if SECRET_NAME.search(key) and isinstance(value, str) and value.strip():
            findings.append(
                Finding(
                    f"{where}.{key}",
                    "secret value (list the variable name under `env` instead)",
                )
            )
    return findings
