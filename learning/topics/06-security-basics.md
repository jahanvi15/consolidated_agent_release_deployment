# 06 — Security basics for a code project

**You'll learn:** how accounts, secrets and history can leak, and the protections this
project uses against each. For a compliance tool, our own hygiene is part of the product.

## 1. Protect the account: two-factor authentication (2FA)

Whoever controls your GitHub account controls the code. 2FA means a stolen password
isn't enough; a code from your phone's authenticator app is also needed.

- Prefer an **authenticator app** over SMS (SIM-swap attacks can steal SMS codes).
- Store the **recovery codes** safely — they're the only way back in if you lose the phone.

## 2. Keep secrets out of the repository

A **secret** is anything that grants access: passwords, API keys, tokens.

**Git never forgets.** If a secret is committed and pushed, deleting it in a later commit
does not remove it — it's still in history, and bots scan public GitHub for keys within
minutes. The only real fix is to **revoke the secret** (make it stop working) and issue
a new one.

Protections in this project:

| Protection | Where |
|-----------|-------|
| `.env` files (where secrets often live) are never tracked | `.gitignore` |
| Fake secrets in tests must start with `FAKE-` so they're obviously fake | `CLAUDE.md` rule 3 |
| ruff's `S` (bandit) rules flag hard-coded passwords | `pyproject.toml` |
| GitHub secret scanning + push protection blocks pushes containing real keys | Repo settings (backlog S0-6) |
| Real tokens go in **GitHub Actions secrets**, encrypted, never in files | `docs/test-accounts.md` |

## 3. Least privilege for tokens

A **PAT (Personal Access Token)** lets a program act as you. Rules:

- **Fine-grained** tokens limited to specific repositories.
- **Minimum permissions** — only what the task needs (e.g. read checks, not delete repos).
- **Expiry** of 90 days or less, so a leaked token dies on its own.
- Named after their purpose, so you know what breaks when you revoke one.

The same idea applies to our CI: `permissions: contents: read` and
`persist-credentials: false` mean the workflow can read code but can't change anything,
and doesn't leave a token on the machine.

## 4. Privacy in history: the noreply email

Every commit records the author's email, publicly and permanently. We use GitHub's
**noreply** address (`99080522+jahanvi15@users.noreply.github.com`), so commits still
link to the profile but the real email can't be harvested.

GitHub → **Settings → Emails**:
- **Keep my email addresses private** — uses noreply for edits made on the website.
- **Block command line pushes that expose my email** — rejects a push (error `GH007`)
  if a commit accidentally carries the real address.

**This actually happened (journal 0001, problem 9):** a commit made on a new PC before
`user.name`/`user.email` were set went out as `unknown <real email>`. It was removed by
resetting `main` before protection was switched on, but GitHub can keep a removed commit
viewable by its exact link for a while. Prevention: check `git config --global --list`
on every new machine, and keep the "Block command line pushes" box ticked.

## 5. Protect `main`

Branch protection means no one — including a compromised token or a mistaken AI — can
push directly to `main`, rewrite its history (force-push), or delete it. Every change
goes through a pull request with green checks. See `docs/decisions/0004-protected-main-and-ci.md`.

## 6. Supply chain: other people's code

Every dependency is code you run but didn't write. We:

- keep **runtime dependencies at zero** until a decision record approves one;
- pin GitHub Actions to major versions and let **Dependabot** propose updates as PRs,
  so updates are visible and go through CI;
- only copy in third-party code with a compatible license (MIT, BSD, Apache).

## If a secret leaks — checklist

1. **Revoke it immediately** at the provider (GitHub → Settings → Developer settings →
   tokens; or the API provider's dashboard).
2. Create a replacement and store it properly (Actions secrets / password manager).
3. Check the provider's logs for use you don't recognize.
4. Only then think about cleaning history — revoking is what actually protects you.

## Try it yourself

1. In GitHub → **Settings → Emails**, confirm both privacy boxes are ticked.
2. Open `.gitignore` and find the three lines about `.env`. Why is `.env.example` allowed?
3. In `sample_agents/harness.py`, find the fake API key. How can you tell it's fake?
