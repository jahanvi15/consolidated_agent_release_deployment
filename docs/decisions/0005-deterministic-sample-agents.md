# 0005. Test against small deterministic sample agents

- **Status:** Accepted
- **Date:** 2026-10-23
- **Decider:** Jahanvi Joshi

## Context

Checks need agents to run against — some that behave and some that break specific rules.
Real LLM-backed agents are slow, cost money, need API keys in CI, and give different
answers each run, so tests would be flaky.

## Decision

`sample_agents/` holds tiny scripted agents with no network and no model calls. Each has:

- `agent.toml` — a manifest (name, purpose, declared tools, step budget, expected verdict).
- `agent.py` — a `run(task, tools)` function that calls tools through a recording
  `ToolBox`, so tests can inspect exactly what the agent tried to do.

Initial set: one well-behaved agent and one agent per planned Stage 1 check
(undeclared tool use, secret leakage, step-budget overrun).

## Consequences

- Tests are fast, free and repeatable.
- The manifest format here is a draft; backlog item S1-1 turns it into the real schema.
- Real-model agents come later as opt-in integration tests, never in the default CI run.
