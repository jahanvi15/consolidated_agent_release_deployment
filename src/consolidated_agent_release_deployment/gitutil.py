"""Run ``git`` commands safely.

All Git access goes through ``git()``: arguments are passed as a list (never through a
shell, so a strange file name can't become a command), and errors become ``GitError``
with Git's own message.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path


class GitError(RuntimeError):
    """A git command failed. The message includes what git printed."""


def git(
    args: Sequence[str],
    cwd: Path,
    *,
    input_text: str | None = None,
    env: Mapping[str, str] | None = None,
) -> str:
    """Run ``git <args>`` in ``cwd`` and return its output without the final newline."""
    exe = shutil.which("git")
    if exe is None:
        raise GitError("git is not installed or not on PATH")
    result = subprocess.run(  # noqa: S603 -- fixed git executable, list args, no shell
        [exe, *args],
        cwd=cwd,
        input=input_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, **(env or {})},
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise GitError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.rstrip("\n")


def try_git(args: Sequence[str], cwd: Path) -> str | None:
    """Like ``git()`` but returns None instead of raising (e.g. not a Git folder)."""
    try:
        return git(args, cwd)
    except GitError:
        return None
