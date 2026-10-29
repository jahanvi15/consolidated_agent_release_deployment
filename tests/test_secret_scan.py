"""Tests for the secret scan. Every example key is fake and starts with FAKE- (CLAUDE.md)."""

from __future__ import annotations

import pytest

from consolidated_agent_release_deployment.secret_scan import Finding, scan_settings, scan_text


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("key = FAKE-sk-0000000000000000", "AI provider API key"),
        ("FAKE-AKIA0000000000000000", "AWS access key"),
        ("token FAKE-ghp_000000000000000000000000", "GitHub token"),
        ("FAKE-AIza00000000000000000000000000000000000", "Google API key"),
        ("FAKE-xoxb-0000000000-0000", "Slack token"),
        ("-----BEGIN RSA PRIVATE KEY-----", "private key"),
    ],
)
def test_known_key_shapes_are_found(text: str, kind: str) -> None:
    findings = scan_text(text, "record")
    assert len(findings) == 1
    assert findings[0].kind.startswith(kind)


def test_ordinary_text_is_clean() -> None:
    assert scan_text('{"model": "deterministic-v1", "task-skip": "ok"}', "record") == []


def test_finding_never_contains_the_secret() -> None:
    finding = scan_text("FAKE-sk-0000000000000000", "record")[0]
    assert "0000" not in str(finding)
    assert str(finding) == "record: possible AI provider API key (sk-...)"


@pytest.mark.parametrize("name", ["api_key", "API-KEY", "db_password", "token", "client_secret"])
def test_secret_looking_setting_names_with_text_values(name: str) -> None:
    assert scan_settings({name: "FAKE-value"}, "config") == [
        Finding(f"config.{name}", "secret value (list the variable name under `env` instead)")
    ]


@pytest.mark.parametrize(
    "settings",
    [
        {"max_output_tokens": 400},  # a number, and "tokens" means text length here
        {"token_limit": 1000},
        {"api_key": ""},  # empty: nothing written down
        {"style": "short"},
    ],
)
def test_harmless_settings_pass(settings: dict[str, object]) -> None:
    assert scan_settings(settings, "config") == []
