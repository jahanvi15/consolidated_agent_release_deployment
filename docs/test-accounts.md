# Test accounts

Free accounts used for development and integration testing. **Create these yourself** —
Claude does not create accounts or handle passwords. Nothing in this file is secret;
record only *which* account exists and where its token is stored, never the token itself.

## Rules for every account

- Use a dedicated sandbox identity where possible, not your main work account.
- Tokens: fine-grained, minimum scopes, **expiry ≤ 90 days**, named after their purpose.
- Tokens live in GitHub Actions secrets or your password manager. Never in the repo,
  `.env` files that get committed, issue comments, or chat with Claude.
- Note the expiry date in the table below so renewal isn't a surprise.

## Needed now (Stage 0 / Stage 1)

| # | Account | Why | Cost | Status | Token stored in | Expires |
|---|---------|-----|------|--------|-----------------|---------|
| 1 | **GitHub personal account** | Hosts this repo; runs our CI | Free (public repo: unlimited Actions minutes) | ☐ | — | — |
| 2 | **GitHub organization, e.g. `<you>-agent-sandbox`** | A separate "customer" repo that consumes our Action, so we test it from the outside the way users will | Free | ☐ | — | — |
| 3 | **Fine-grained PAT on the sandbox org** | Lets integration tests open PRs and read check results in the sandbox repo only | Free | ☐ | Actions secret `SANDBOX_GH_TOKEN` | |

Setup notes:

1. Create the repo **public** — branch protection is only enforced on public repos with
   GitHub Free (ADR 0004). Don't initialize it with a README or license; this scaffold has them.
2. In the sandbox org, create an empty public repo `consumer-test-repo`.
3. PAT scopes: repository access *only* `consumer-test-repo`; permissions
   Contents read/write, Pull requests read/write, Checks read. Nothing else.

## Needed soon (second platform)

| # | Account | Why | Cost | Status |
|---|---------|-----|------|--------|
| 4 | **Azure DevOps organization** (sign in with a Microsoft account at dev.azure.com) | Second pipeline platform (BACKLOG inbox) | Free: up to 5 users | ☐ |
| 5 | **Azure subscription linked for billing** (an Azure free account works) | The free Microsoft-hosted pipeline grant only switches on once the organization is linked to an Azure subscription. Free tier for private projects: 1 job at a time, max 60 min per run, 1,800 min per month | Free within those limits | ☐ |

Alternative to #5 if you'd rather not attach a subscription: run pipelines on a
**self-hosted agent** (your own machine or VM), which needs no billing link.
Verified against Microsoft's docs on 2026-10-23; check again before relying on it.

## Later (not yet)

- **TestPyPI** account — practice publishing before a real release (needs an ADR first).
- **Model provider API key** — only for opt-in integration tests with real-LLM agents
  (ADR 0005). Set a low monthly spend limit when you create it.
