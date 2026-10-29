# 0007. Agent manifest format: flat TOML, versioned, strict, all errors at once

- **Status:** Proposed
- **Date:** 2026-10-23 (updated 2026-10-30)
- **Decider:** Jahanvi Joshi (to accept)

## Context

Stage 1 checks compare an agent's behaviour with what it declares. Users write these
declarations by hand, so the format must be easy to write and impossible to get
*silently* wrong. The Stage 0 draft mixed product fields with test-only fields
(`expected`, `expected_reason`) and stopped at the first error.

## Options considered

1. **File format** — TOML (readable, comments, in the Python standard library as
   `tomllib`, no dependency) vs YAML (popular but needs a library and has surprising
   type rules, e.g. `no` becomes false) vs JSON (no comments, noisy for humans). → TOML.
2. **Shape** — flat keys vs nested tables (`[limits] max_steps = 5`). Nested scales
   better with many fields; flat is simpler while there are six. → Flat now; a future
   `schema_version = 2` can nest if needed.
3. **Unknown fields** — ignore vs reject. Ignoring means `max_step = 5` (typo) silently
   leaves no step limit. → Reject, with a "did you mean" suggestion.
4. **Error reporting** — stop at the first problem vs collect all. → Collect all.
5. **Validation library** — hand-written vs pydantic/jsonschema. A library would be the
   first runtime dependency (ADR 0001 keeps zero) for six fields. → Hand-written, standard
   library only. Revisit when the schema grows substantially.

## Decision

- Fields: `schema_version` (=1), `name`, `description`, `declared_tools`, `max_steps`,
  optional `entrypoint` (default `agent.py:run`). Added 2026-10-30 for the version
  record (ADR 0008), all optional: `prompts`, `env` (names only), `dependencies`,
  `[model]` with `[model.settings]`, and `[config]`. Settings hold only text, numbers or
  true/false, so every value can be compared on one line. Full field list in the
  `manifest.py` docstring and `learning/topics/08-validating-input.md`.
- Unknown fields are errors; all problems are reported together.
- `entrypoint` must stay inside the agent folder (no `..`, no absolute path) — the tool
  will later import that file, so this blocks pointing it at arbitrary code.
- Sample-agent test expectations move to a separate `expected.toml`, so `agent.toml`
  contains only what a real user would write.

## Consequences

- Clear, actionable errors; typos can't weaken a policy.
- Adding a field means updating `KNOWN_FIELDS`, the docs and tests — deliberate friction.
- Breaking changes require bumping `schema_version` and supporting both versions for a while.
