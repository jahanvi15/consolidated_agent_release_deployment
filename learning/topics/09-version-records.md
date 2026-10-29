# 09 — Version records: fingerprints, append-only storage and Git's inner parts

**You'll learn:** the ideas behind Feature 1, explained from zero: what a hash
(fingerprint) is, why records are never edited, how Git stores things, how the tool
writes to a branch without touching your files, what pydantic does, and two security
habits for running commands. Example throughout: journal 0003, ADR 0008.

## 1. What a version record is

A **version record** is a small JSON file that says exactly what one version of one
agent was: its model and settings, prompts, tools, config, and a fingerprint of every
file. It also says who made it, when, and from which commit.

```
records/helpful_summarizer/000002.json   ← version 2 of the agent "helpful_summarizer"
```

Every later feature reads these: "what changed" compares two records, rule checks read
one, sign-off approves one, and undo goes back to an older one.

## 2. Fingerprints (hashes)

A **hash function** turns any data into a short, fixed-length code. We use
**SHA-256**, which always gives 64 hexadecimal characters:

```python
import hashlib

hashlib.sha256(b"hello").hexdigest()
# '2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824'
```

Three properties make it useful:

1. **Same input → same output**, on every computer, forever.
2. **Tiny change → completely different output.** Change one letter and the whole code
   changes.
3. **You can't go backwards** from the code to the data, and no one can find two
   different inputs with the same code.

We call it a **fingerprint** and write it as `sha256:2cf24d…`. Uses in this project:

- Each file in the agent folder gets one, so "did the prompt change?" is a comparison of
  two short strings.
- The whole record content gets one. If the newest saved record has the same
  fingerprint, nothing changed and no new version is created.
- When a record is loaded, the fingerprint is computed again. If someone edited the
  file, it no longer matches, and loading fails (a **tamper check**).

### The same data must become the same text

`{"b": 1, "a": 2}` and `{"a": 2, "b": 1}` mean the same thing but are different text,
so they would hash differently. **Canonical JSON** fixes this by always writing data
one exact way: keys sorted, no spaces.

```python
json.dumps(data, sort_keys=True, separators=(",", ":"))
```

### Windows vs Linux line endings

Windows ends text lines with two invisible characters, `\r\n`; Linux and Mac use one,
`\n`. The same prompt file could hash differently on your laptop and in CI. So before
hashing a text file the tool replaces `\r\n` with `\n`. (The repo's `.gitattributes`
already stores files with `\n` in Git; this protects files Git hasn't normalized yet.)

## 3. Copy or point?

Small values (model name, temperature, tool list) are **copied** into the record so it
can be read on its own. Files are only **fingerprinted**: the real content is in Git at
the commit the record names. This keeps records small and still detects every change.

## 4. Append-only: records are never edited

An **append-only** store only ever adds. Version 3 can't be overwritten or deleted by
the tool, and a mistake is fixed by creating version 4. That is what makes the history
trustworthy enough for an audit.

How the code enforces it:

- The next version must be exactly *latest + 1*; anything else is refused.
- The folder store opens files with mode `"x"` ("create only, fail if it exists").
- The Git store checks the path is new before writing it.

## 5. How Git stores things (and how we write a branch "from the side")

Most Git commands you know (`add`, `commit`, `checkout`) are called **porcelain**: the
friendly surface. Underneath are **plumbing** commands that work on Git's four basic
objects:

| Object | What it is |
|--------|------------|
| **blob** | The contents of one file |
| **tree** | A folder listing: names pointing to blobs and other trees |
| **commit** | A tree, plus parent commit(s), author, time and message |
| **ref** (branch) | A name pointing to one commit, e.g. `refs/heads/agent-releases` |

Every object is named by its own hash, which is why Git IDs look like `e5574f0…`.

To save a record on the `agent-releases` branch **without switching branches or
touching your files**, the tool does by hand what `git commit` does for you:

```bash
GIT_INDEX_FILE=/tmp/private-index git read-tree agent-releases   # start from the branch
git hash-object -w --stdin < record.json                         # store the file → blob id
GIT_INDEX_FILE=… git update-index --add --cacheinfo 100644,<blob>,records/a/000002.json
GIT_INDEX_FILE=… git write-tree                                  # → tree id
git commit-tree <tree> -p <old tip> -m "record a v2"             # → commit id
git update-ref refs/heads/agent-releases <new commit> <old tip>  # move the branch
```

The **index** (staging area) is where `git add` puts things. Using a *private* index
file (`GIT_INDEX_FILE`) means your own staged changes are left alone.

**Compare-and-swap:** the last command moves the branch *only if* it still points at
`<old tip>`. If another run saved a record in the meantime, it fails instead of
silently losing that record, and you just run the command again.

Records go on a separate branch so they never create commits on `main`, so no extra
pull requests or merges.

## 6. pydantic: typed, checked data

**pydantic** is a library where you describe data as a Python class and it checks
everything that comes in:

```python
class VersionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    agent: str
    version: int = Field(ge=1)  # whole number, at least 1
    fingerprint: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


VersionRecord.model_validate_json(text)  # JSON text → checked object, or an error
record.model_dump_json(indent=2)  # object → JSON text
```

- `extra="forbid"`: an unknown field is an error (same rule as the manifest).
- `frozen=True`: the object can't be changed after it is made.
- `@field_validator` / `@model_validator`: your own extra rules, like "time must be UTC"
  and "fingerprint must match content".

It's the project's first **runtime dependency** (needed to *run* the tool, not only to
test it), so it has an ADR: 0008.

## 7. One interface, several stores

`RecordStore` is an **abstract base class**: it holds the shared rules (append-only,
numbering) and leaves three small methods (list, read, create) to subclasses.
`GitBranchStore` and `DirectoryStore` fill them in. A database store later is one more
subclass; nothing else changes.

The same idea keeps platform details out of the record: only `source.py` knows about
GitHub's environment variables (`GITHUB_SHA`, `GITHUB_RUN_ID`…). Azure DevOps becomes
one more function there.

## 8. Two security habits

**Run commands with a list, never a shell string.**

```python
subprocess.run(["git", "show", user_input])  # safe: one argument, whatever it holds
subprocess.run(f"git show {user_input}", shell=True)  # unsafe: "x; rm -rf ~" runs rm
```

**In GitHub Actions, pass inputs through `env:`**, never paste `${{ inputs.x }}`
straight into a `run:` script. Otherwise a crafted value becomes part of the script
(**script injection**). Our `action.yml` follows this.

Plus the secret rule: records store the *names* of environment variables
(`SEARCH_API_KEY`), never values, and a scan blocks any record that looks like it holds
a key. It reports *where*, never the secret itself.

## 9. The workflow: least privilege

`.github/workflows/record-versions.yml` runs the tool automatically. Three settings
matter:

- **`permissions:`** Each run gets a temporary key called `GITHUB_TOKEN`. The file starts
  with `contents: read` for everything, and only the `record` job (after a merge) gets
  `contents: write`. A job that only previews can't change anything. Giving each part
  only the access it needs is called **least privilege**.
- **`concurrency:`** Two merges close together would start two saves. A concurrency
  group makes the second one wait, and `cancel-in-progress: false` means a save is
  never stopped halfway.
- **No loops:** pushes made with `GITHUB_TOKEN` don't start new workflow runs, so saving
  records can't trigger another save.

## 10. Making code testable: pass the world in

Functions take the current time (`now=`) and the environment (`env=`) as arguments
instead of reading them directly. Tests pass fixed values, so results are the same on
every run, and a fake "GitHub Actions" environment needs no real GitHub.

## Try it yourself

1. Run `record preview` on `sample_agents/helpful_summarizer` twice. Is the fingerprint
   the same both times? Why?
2. Add a space to `prompts/system.md` and preview again. Which file hashes changed?
3. In `record-versions.yml`, which job can write to the repository, and why only that one?
4. Open `.github/actions/record-version/action.yml`. Find the two places that stop
   script injection.
5. In `tests/test_store.py`, find the test proving your current branch and files are
   untouched after saving a record.

## Further reading

- Git internals (objects and plumbing): <https://git-scm.com/book/en/v2/Git-Internals-Plumbing-and-Porcelain>
- pydantic documentation: <https://docs.pydantic.dev/latest/>
- GitHub Actions security hardening: <https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions>
