# Agent manifest reference (`agent.toml`)

Every agent checked by `consolidated-agent-release-deployment` has an `agent.toml` file
in its folder. It declares what the agent is allowed to do; the compliance checks then
compare what the agent *actually* does against these declarations.

Current schema version: **1**. Decision record: [ADR 0007](decisions/0007-agent-manifest-format.md).

## Example

```toml
schema_version = 1
name = "support_bot"
description = "Answers customer questions from the help-center articles."
declared_tools = ["search", "read_file"]
max_steps = 10
entrypoint = "agent.py:run"   # optional; this is the default
```

## Fields

| Field | Required | Type | Rules |
|-------|----------|------|-------|
| `schema_version` | yes | integer | Must be `1`. Lets the format change later without breaking old files silently. |
| `name` | yes | string | 1–64 characters: lowercase letters, digits, `_`, `-`; must start with a letter. |
| `description` | yes | string | Non-empty. What the agent is for, in plain words. |
| `declared_tools` | yes | list of strings | Every tool the agent may call. Names: 1–64 characters of letters, digits, `_`, `.`, `-`, starting with a letter. No duplicates. May be empty (`[]`). |
| `max_steps` | yes | integer | Maximum tool calls per run, 1–10000. Booleans are rejected. |
| `entrypoint` | no | string | `file.py:function`, default `agent.py:run`. The file must be inside the agent's folder (no `..`, no absolute paths). |

Any other field is an **error**, with a suggestion when it looks like a typo
(`max_step` → "did you mean 'max_steps'?"). Ignoring unknown fields would let a typo
silently disable a limit.

## Errors

All problems are reported together, so you can fix the file in one pass:

```text
agents/demo/agent.toml: 6 problems in agent manifest
  - max_step: unknown field; did you mean 'max_steps'? (allowed: schema_version, name, description, declared_tools, max_steps, entrypoint)
  - description: required field is missing
  - max_steps: required field is missing
  - name: must be 1-64 characters: lowercase letters, digits, '_' or '-', starting with a letter
  - declared_tools[1]: 'search' is listed more than once
  - entrypoint: file must be inside the agent folder (no '..' or '/')
```

A file that isn't valid TOML at all reports the line and column of the syntax error.

## Using it from Python

```python
from pathlib import Path
from consolidated_agent_release_deployment.manifest import ManifestError, load_manifest

try:
    manifest = load_manifest(Path("my_agent/agent.toml"))
except ManifestError as err:
    print(err)  # the full message above
    print(err.issues)  # structured: tuple of Issue(field, message)
else:
    print(manifest.declared_tools, manifest.max_steps)
```
