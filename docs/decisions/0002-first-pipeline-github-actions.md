# 0002. Integrate with GitHub Actions first

- **Status:** Accepted
- **Date:** 2026-10-23
- **Decider:** Jahanvi Joshi

## Context

The tool runs inside a deployment pipeline and blocks non-compliant agents. We need one
platform to build against end to end before generalizing. Our own repo also needs CI.

## Options considered

1. **GitHub Actions** — free for public repos; our code lives on GitHub, so our own CI
   and the product integration share one platform; PR annotations and code-scanning
   (SARIF) give a good place to show findings.
2. **Azure DevOps** — common in regulated enterprises (a likely buyer); separate account
   and a second system to learn on day one.
3. **GitLab CI** — strong compliance features; smaller share of our likely early users.

## Decision

GitHub Actions first. Azure DevOps is the planned second platform (see `BACKLOG.md`).

## Consequences

- Core logic must stay platform-neutral: the CLI does the checking; a thin adapter per
  platform handles inputs, annotations and exit codes.
- Our own CI (`.github/workflows/ci.yml`) doubles as a working example of the platform.
