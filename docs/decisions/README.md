# Decision log

Architecture Decision Records (ADRs). One file per decision, numbered in order, never
renumbered. To change a decision, write a new ADR that supersedes the old one and set the
old one's status to `Superseded by NNNN`.

| #    | Decision                                         | Status   | Date       |
|------|--------------------------------------------------|----------|------------|
| 0001 | [Python 3.11+ as the implementation language](0001-language-python.md) | Accepted | 2026-10-23 |
| 0002 | [GitHub Actions as the first pipeline platform](0002-first-pipeline-github-actions.md) | Accepted | 2026-10-23 |
| 0003 | [Apache License 2.0](0003-license-apache-2.md) | Accepted | 2026-10-23 |
| 0004 | [Protected `main`, PR-only workflow, single required check](0004-protected-main-and-ci.md) | Accepted | 2026-10-23 |
| 0005 | [Deterministic sample agents as test fixtures](0005-deterministic-sample-agents.md) | Accepted | 2026-10-23 |
| 0006 | [Merge commits; one branch per feature as work starts](0006-merge-commits-and-branch-per-feature.md) | Accepted | 2026-10-23 |
| 0007 | [Agent manifest format: flat TOML, versioned, strict](0007-agent-manifest-format.md) | Proposed | 2026-10-23 |
| 0008 | [Keep 0 required approvals with two contributors](0008-two-contributors-zero-required-approvals.md) | Accepted | 2026-10-24 |
| 0009 | [Follow the staged roadmap (features 1–13, Stages 0–7)](0009-staged-roadmap.md) | Accepted | 2026-10-24 |

New ADR: copy [`0000-template.md`](0000-template.md).
