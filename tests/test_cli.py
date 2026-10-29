from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from consolidated_agent_release_deployment import __version__
from consolidated_agent_release_deployment.cli import main
from consolidated_agent_release_deployment.gitutil import git
from sample_agents.harness import AGENTS_DIR
from tests.conftest import commit_all


def test_version_flag_prints_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_no_arguments_prints_help_and_succeeds(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert "usage: consolidated-agent-release-deployment" in capsys.readouterr().out


def test_unknown_argument_is_an_error() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--no-such-flag"])
    assert exc.value.code == 2


# ---------- record commands (Feature 1) ----------

GITHUB_ENV = {"GITHUB_ACTIONS": "true", "GITHUB_ACTOR": "ci-bot", "GITHUB_SHA": "b" * 40}


def run(
    argv: list[str],
    cwd: Path,
    monkeypatch: pytest.MonkeyPatch,
    env: dict[str, str] | None = None,
) -> int:
    monkeypatch.chdir(cwd)
    return main(argv, env=env or {})


def test_create_records_every_agent_then_skips_unchanged(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run(["record", "create", "agents"], repo, monkeypatch) == 0
    out = capsys.readouterr().out
    assert out.count("created version 1") == 4
    assert run(["record", "create", "agents"], repo, monkeypatch) == 0
    assert capsys.readouterr().out.count("unchanged, still version 1") == 4


def test_a_change_makes_version_2_only_for_that_agent(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    run(["record", "create", "agents"], repo, monkeypatch)
    (repo / "agents" / "secret_leaker" / "agent.py").write_text("# new code\n")
    commit_all(repo)
    capsys.readouterr()
    assert run(["record", "create", "agents"], repo, monkeypatch) == 0
    out = capsys.readouterr().out
    assert "secret_leaker: created version 2" in out
    assert "helpful_summarizer: unchanged, still version 1" in out


def test_create_refuses_uncommitted_changes(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    agent = repo / "agents" / "helpful_summarizer"
    (agent / "agent.py").write_text("# not committed yet\n")
    assert run(["record", "create", str(agent)], repo, monkeypatch) == 1
    assert "has uncommitted changes" in capsys.readouterr().err
    assert run(["record", "create", "--allow-uncommitted", str(agent)], repo, monkeypatch) == 0


def test_preview_saves_nothing(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    agent = "agents/helpful_summarizer"
    assert run(["record", "preview", agent], repo, monkeypatch, GITHUB_ENV) == 0
    record = json.loads(capsys.readouterr().out)
    assert record["version"] == 1
    assert record["created_by"] == "ci-bot"
    assert record["source"]["platform"] == "github-actions"
    assert git(["branch", "--list", "agent-releases"], repo) == ""


def test_preview_says_when_nothing_changed(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    run(["record", "create", "agents/runaway_loop"], repo, monkeypatch)
    capsys.readouterr()
    run(["record", "preview", "agents/runaway_loop"], repo, monkeypatch)
    assert capsys.readouterr().out.startswith("# runaway_loop: unchanged since version 1\n")


def test_preview_works_outside_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    shutil.copytree(AGENTS_DIR / "tool_overreach", tmp_path / "tool_overreach")
    assert run(["record", "preview", "."], tmp_path, monkeypatch) == 0
    assert json.loads(capsys.readouterr().out)["agent"] == "tool_overreach"


def test_list_and_show(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    run(["record", "create", "agents/helpful_summarizer"], repo, monkeypatch)
    capsys.readouterr()
    assert run(["record", "list", "helpful_summarizer"], repo, monkeypatch) == 0
    line = capsys.readouterr().out.strip()
    assert line.startswith("1  ")
    assert line.endswith("Test User")
    assert run(["record", "show", "helpful_summarizer", "1"], repo, monkeypatch) == 0
    assert json.loads(capsys.readouterr().out)["version"] == 1


def test_store_dir_option(repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    folder = tmp_path / "local-records"
    argv = ["record", "create", "--store-dir", str(folder), "agents/runaway_loop"]
    assert run(argv, repo, monkeypatch) == 0
    assert (folder / "records" / "runaway_loop" / "000001.json").is_file()


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["record", "list", "nobody"], "no versions recorded for 'nobody'"),
        (["record", "show", "nobody", "1"], "nobody has no version 1"),
        (["record", "create", "missing-folder"], "missing-folder: not a folder"),
        (["record", "create", "agents/helpful_summarizer/prompts"], "no agent.toml found"),
    ],
)
def test_clear_errors(
    argv: list[str],
    message: str,
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert run(argv, repo, monkeypatch) == 1
    assert message in capsys.readouterr().err


def test_create_needs_git_or_a_store_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    shutil.copytree(AGENTS_DIR / "tool_overreach", tmp_path / "tool_overreach")
    assert run(["record", "create", "."], tmp_path, monkeypatch) == 1
    assert "use --store-dir" in capsys.readouterr().err


def test_secret_in_config_blocks_the_record(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    toml = repo / "agents" / "helpful_summarizer" / "agent.toml"
    toml.write_text(toml.read_text() + 'api_key = "FAKE-sk-0000000000000000"\n')
    commit_all(repo)
    assert run(["record", "create", "agents"], repo, monkeypatch) == 1
    err = capsys.readouterr().err
    assert "blocked, the record would contain a secret" in err
    assert "config.api_key" in err
    assert "FAKE-sk-0000" not in err  # the secret itself is never printed
    # No record is saved, but the refusal is logged, again without the secret.
    saved = git(["ls-tree", "-r", "--name-only", "agent-releases"], repo)
    assert "records/helpful_summarizer" not in saved
    shown = git(["show", "agent-releases"], repo)
    assert '"reason": "possible_secret"' in shown
    assert "FAKE-sk-0000" not in shown


def test_secret_in_a_model_setting_blocks_the_record(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    toml = repo / "agents" / "helpful_summarizer" / "agent.toml"
    text = toml.read_text().replace("[config]", 'auth_token = "FAKE-x"\n\n[config]')
    toml.write_text(text)
    assert run(["record", "preview", "agents/helpful_summarizer"], repo, monkeypatch) == 1
    assert "model.settings.auth_token" in capsys.readouterr().err


def test_invalid_manifest_is_reported(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (repo / "agents" / "runaway_loop" / "agent.toml").write_text("max_steps = 0\n")
    assert run(["record", "preview", "agents/runaway_loop"], repo, monkeypatch) == 1
    assert "problems in agent manifest" in capsys.readouterr().err


def test_tampered_record_is_reported(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = tmp_path / "recs"
    run(["record", "create", "--store-dir", str(folder), "agents/runaway_loop"], repo, monkeypatch)
    path = folder / "records" / "runaway_loop" / "000001.json"
    path.write_text(path.read_text().replace('"max_steps": 5', '"max_steps": 50'))
    capsys.readouterr()
    assert (
        run(["record", "show", "--store-dir", str(folder), "runaway_loop", "1"], repo, monkeypatch)
        == 1
    )
    assert "fingerprint does not match content" in capsys.readouterr().err


def test_folders_like_venv_are_skipped(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    shutil.copytree(repo / "agents" / "runaway_loop", repo / ".venv" / "copy")
    assert run(["record", "preview", "."], repo, monkeypatch) == 0
    assert capsys.readouterr().out.count('"agent": "runaway_loop"') == 1


def test_record_without_action_is_a_usage_error() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["record"])
    assert exc.value.code == 2


# ---------- audit log (ADR 0009) ----------


def audit_list(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> list[str]:
    capsys.readouterr()
    assert run(["audit", "list"], repo, monkeypatch) == 0
    return capsys.readouterr().out.splitlines()


def test_every_outcome_is_logged(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    run(["record", "create", "agents"], repo, monkeypatch)
    run(["record", "create", "agents"], repo, monkeypatch)
    lines = audit_list(repo, monkeypatch, capsys)
    assert len(lines) == 8
    assert "runaway_loop  v1  created  Test User" in lines[1]
    assert "runaway_loop  v1  unchanged  Test User" in lines[5]


def test_one_save_per_run(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run(["record", "create", "agents"], repo, monkeypatch)
    log = git(["log", "--format=%s", "agent-releases"], repo).splitlines()
    assert log == [
        "record: helpful_summarizer v1, runaway_loop v1, secret_leaker v1, "
        "tool_overreach v1 (events 1-4)"
    ]
    run(["record", "create", "agents"], repo, monkeypatch)
    assert git(["log", "-1", "--format=%s", "agent-releases"], repo) == "audit: events 5-8"


def test_uncommitted_refusal_is_logged_and_others_still_saved(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (repo / "agents" / "runaway_loop" / "agent.py").write_text("# not committed\n")
    assert run(["record", "create", "agents"], repo, monkeypatch) == 1
    lines = audit_list(repo, monkeypatch, capsys)
    assert "runaway_loop  -  refused (uncommitted_changes)" in lines[1]
    assert "secret_leaker  v1  created" in lines[2]


def test_invalid_agent_refusal_is_logged(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (repo / "agents" / "runaway_loop" / "agent.toml").write_text("max_steps = 0\n")
    commit_all(repo)
    assert run(["record", "create", "agents/runaway_loop"], repo, monkeypatch) == 1
    assert "refused, invalid agent" in capsys.readouterr().err
    event = json.loads(git(["show", "agent-releases:audit/" + _first_event(repo)], repo))
    assert event["reason"] == "invalid_agent"
    assert event["agent"] is None
    assert event["source"]["agent_path"] == "agents/runaway_loop"
    assert "max_steps: must be between 1 and 10000" in event["details"]


def test_missing_prompt_file_refusal_is_logged(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (repo / "agents" / "helpful_summarizer" / "prompts" / "system.md").unlink()
    commit_all(repo)
    assert run(["record", "create", "agents/helpful_summarizer"], repo, monkeypatch) == 1
    assert "not found: prompts/system.md" in capsys.readouterr().err
    assert "refused (invalid_agent)" in audit_list(repo, monkeypatch, capsys)[0]


def _first_event(repo: Path) -> str:
    paths = git(["ls-tree", "-r", "--name-only", "agent-releases", "--", "audit/"], repo)
    return paths.splitlines()[0].removeprefix("audit/")


def test_audit_list_filters(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    run(["record", "create", "agents"], repo, monkeypatch)
    capsys.readouterr()
    assert run(["audit", "list", "--agent", "secret_leaker"], repo, monkeypatch) == 0
    assert len(capsys.readouterr().out.splitlines()) == 1
    assert run(["audit", "list", "--since", "2999-01-01"], repo, monkeypatch) == 1
    assert "no audit events match" in capsys.readouterr().err
    assert run(["audit", "list", "--until", "2000-01-01"], repo, monkeypatch) == 1


def test_audit_verify_ok_then_broken(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    store = ["--store-dir", str(tmp_path / "s")]
    run(["record", "create", *store, "agents"], repo, monkeypatch)
    capsys.readouterr()
    assert run(["audit", "verify", *store], repo, monkeypatch) == 0
    assert "audit log intact: 4 events, 4 records checked" in capsys.readouterr().out
    next((tmp_path / "s" / "audit").rglob("000000002-*.json")).unlink()
    assert run(["audit", "verify", *store], repo, monkeypatch) == 1
    err = capsys.readouterr().err
    assert "problem: event 3: expected event 2 here" in err
    assert "audit log NOT intact" in err


def test_audit_verify_notes_records_from_before_the_log(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from consolidated_agent_release_deployment.version_record import Source, load_agent, new_record

    manifest, content = load_agent(repo / "agents" / "runaway_loop")
    old = new_record(
        manifest.name,
        content,
        version=1,
        created_by="earlier",
        source=Source(platform="local", agent_path="agents/runaway_loop"),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )
    folder = tmp_path / "s" / "records" / "runaway_loop"
    folder.mkdir(parents=True)
    (folder / "000001.json").write_text(old.to_json())
    store = ["--store-dir", str(tmp_path / "s")]
    run(["record", "create", *store, "agents/runaway_loop"], repo, monkeypatch)
    capsys.readouterr()
    assert run(["audit", "verify", *store], repo, monkeypatch) == 0
    out = capsys.readouterr().out
    assert "note: records/runaway_loop/000001.json: recorded before the audit log started" in out


def test_audit_export_csv(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    run(["record", "create", "agents"], repo, monkeypatch)
    capsys.readouterr()
    assert run(["audit", "export", "--agent", "runaway_loop"], repo, monkeypatch) == 0
    rows = capsys.readouterr().out.splitlines()
    assert rows[0].startswith("sequence,occurred_at,type")
    assert len(rows) == 2
    target = tmp_path / "log.csv"
    assert run(["audit", "export", "--output", str(target)], repo, monkeypatch) == 0
    assert len(target.read_text().splitlines()) == 5
    assert f"wrote {target}" in capsys.readouterr().out


def test_github_summary_table(repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    summary = tmp_path / "summary.md"
    env = {**GITHUB_ENV, "GITHUB_STEP_SUMMARY": str(summary)}
    assert run(["record", "create", "agents/runaway_loop"], repo, monkeypatch, env) == 0
    text = summary.read_text()
    assert "### Agent version records" in text
    assert "| 1 | runaway_loop | created | 1 |" in text


def test_who_and_via_on_github(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run(["record", "create", "agents/runaway_loop"], repo, monkeypatch, GITHUB_ENV)
    event = json.loads(git(["show", "agent-releases:audit/" + _first_event(repo)], repo))
    assert (event["actor"], event["via"]) == ("ci-bot", "github-actions")
