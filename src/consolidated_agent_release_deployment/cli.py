"""Command-line entry point.

Stage 0 only exposes ``--version`` so the pipeline has something real to run.
Feature commands arrive from the backlog.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from consolidated_agent_release_deployment import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="consolidated-agent-release-deployment",
        description="Pre-deployment compliance checks for AI agents.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
