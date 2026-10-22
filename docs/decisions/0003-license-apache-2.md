# 0003. License the project under Apache License 2.0

- **Status:** Accepted
- **Date:** 2026-10-23
- **Decider:** Jahanvi Joshi

## Context

Compliance tooling is adopted by companies whose legal teams review licenses. We want
adoption to be easy and contributors to grant patent rights along with code.

## Options considered

1. **Apache-2.0** — permissive, includes an explicit patent grant and patent-retaliation
   clause; widely pre-approved by corporate legal teams.
2. **MIT** — shortest and permissive; no patent grant.
3. **Proprietary** — keeps commercial options fully open; blocks community adoption.
4. **AGPL-3.0** — stops others offering it as a closed hosted service; many companies ban it.

## Decision

Apache-2.0. `LICENSE` holds the unmodified text; `NOTICE` holds the copyright line.

## Consequences

- Anyone can use, modify and sell it, including in closed products, as long as they keep
  the notices. A paid offering would have to sit on top (hosting, support, extra checks).
- Contributions are accepted under Apache-2.0 (inbound = outbound). Add a DCO sign-off
  requirement if outside contributors arrive.
- Third-party code we copy in must be Apache-compatible (MIT, BSD, Apache are fine;
  GPL is not).
