# 08 — Designing and validating an input format

**You'll learn:** how to design a file format people write by hand, how to validate it
so mistakes are caught loudly and clearly, and the Python tools used to do it. Example
throughout: our `agent.toml` (journal 0003). The record built from it is
explained in [topic 09](09-version-records.md).

## Every field in `agent.toml`

| Field | Required? | Example | What it means |
|-------|-----------|---------|---------------|
| `schema_version` | yes | `1` | Which version of this format the file uses |
| `name` | yes | `"support_bot"` | Unique name: lowercase letters, digits, `_`, `-` |
| `description` | yes | `"Answers billing questions"` | One line for humans |
| `declared_tools` | yes | `["search", "read_file"]` | The only tools the agent may call |
| `max_steps` | yes | `5` | Most tool calls allowed in one run (1–10000) |
| `entrypoint` | no | `"agent.py:run"` | File and function the agent starts from (this is the default) |
| `prompts` | no | `["prompts/system.md"]` | Prompt files inside the agent folder, written with `/` |
| `env` | no | `["SEARCH_API_KEY"]` | **Names** of environment variables the agent reads, never their values |
| `dependencies` | no | `["httpx>=0.27"]` | Python packages the agent needs |
| `[model]` | no | `provider = "openai"`, `name = "gpt-x"` | Which AI model it uses |
| `[model.settings]` | no | `temperature = 0.2` | Model settings: text, numbers or true/false only |
| `[config]` | no | `summary_style = "short"` | Any other plain settings |

A full example is `sample_agents/helpful_summarizer/agent.toml`.

## Why validation matters more for a compliance tool

Our tool trusts the manifest to know what an agent is *allowed* to do. If the manifest
is quietly misread, every check built on it is wrong — while reporting "pass". So the
rule is: **reject anything we don't fully understand.**

## Five design rules we followed

1. **Pick a human-friendly format.** TOML: `key = value`, comments with `#`, read by
   Python's built-in `tomllib` (no extra library).
2. **Version it.** `schema_version = 1` lets the format evolve without misreading old files.
3. **Be strict.** Unknown fields are errors. A typo must never switch a rule off.
4. **Report everything at once,** each problem pointing to the exact field
   (`declared_tools[1]` = the second item of the list; counting starts at 0).
5. **Have sensible defaults only where safe.** `entrypoint` defaults to `agent.py:run`;
   limits like `max_steps` have *no* default — a missing limit is an error, not "unlimited".

## The pattern in code

```python
issues: list[Issue] = []  # 1. start with an empty list

for key in data:  # 2. every check adds to the list…
    if key not in KNOWN_FIELDS:
        issues.append(Issue(key, "unknown field"))
max_steps = _check_max_steps(data, issues)

if issues:  # 3. …and only at the end do we stop
    raise ManifestError(source, issues)
return AgentManifest(...)  # 4. a clean, typed, frozen result
```

After this function, the rest of the program works with `AgentManifest` — an object
that is guaranteed valid. This is called **"parse, don't validate"**: turn untrusted
input into a trusted type once, at the edge, and never re-check it afterwards.

## Python details worth knowing

**`tomllib`** reads TOML into a plain dictionary:

```python
import tomllib

with open("agent.toml", "rb") as f:  # "rb" = read bytes; tomllib requires it
    data = tomllib.load(f)
# data == {"schema_version": 1, "name": "support_bot", ...}
```

A syntax error raises `tomllib.TOMLDecodeError` whose message includes the line and
column. We catch it and wrap it in our own `ManifestError` so users see one kind of error.

**`isinstance` and the bool trap:**

```python
isinstance(5, int)  # True
isinstance(True, int)  # True  ← surprise! bool is a kind of int in Python
```

So integer fields check `isinstance(value, bool) or not isinstance(value, int)`.

**Frozen dataclasses** — a compact way to define a record type:

```python
@dataclass(frozen=True)
class AgentManifest:
    name: str
    max_steps: int
```

Python generates `__init__`, `__eq__` and a readable `repr` automatically. `frozen=True`
makes instances unchangeable: `m.max_steps = 99` raises an error.

**Regular expressions** (`re` module):

| Pattern piece | Means |
|---------------|-------|
| `[a-z]` | one character from a to z |
| `[a-z0-9_-]` | one lowercase letter, digit, `_` or `-` |
| `{0,63}` | the previous piece repeated 0 to 63 times |
| `\.py` | a literal `.py` (`\` makes `.` mean a real dot) |
| `(?P<file>...)` | a named group you can read back with `match["file"]` |

`re.fullmatch(pattern, text)` succeeds only if the **entire** text fits — `re.match`
would accept `"agent!"` because its start, `"agent"`, fits.

**`difflib.get_close_matches("max_step", KNOWN_FIELDS)`** returns `["max_steps"]` —
the basis of "did you mean…?".

**Never trust paths from input.** `PurePosixPath("../x.py").parts` is `("..", "x.py")`,
so checking for `".."` in `.parts` and `.is_absolute()` blocks escaping the folder.

## Don't use `assert` for real checks

`assert` statements are removed when Python runs with `-O`. Use them in tests, never to
protect logic in product code. Use `if …: raise …` instead.

## Testing a validator

- One **happy-path** test proving a valid file produces the right object.
- One test **per rule**, ideally with `@pytest.mark.parametrize` listing many bad inputs
  and the exact message expected.
- Tests for **edge values**: `0`, `1`, `10000`, `10001`, empty strings, whitespace-only
  strings, booleans where numbers are expected.
- A test that **several problems** are reported together, in a stable order.

## Try it yourself

1. In `tests/test_manifest.py`, find the test that proves `max_steps = true` is rejected.
2. Write down three typos someone might make in `agent.toml`, add them to a copy of a
   sample agent, and run `consolidated-agent-release-deployment record preview` on that
   folder (journal 0003, "Commands used"). Read the messages.
3. Why does `max_steps` have no default, while `entrypoint` does?
