#!/usr/bin/env bash
# Protect the default branch with a GitHub repository ruleset (ADR 0004).
#
# Usage:   scripts/protect-main.sh OWNER/REPO
# Needs:   GitHub CLI (`gh`) logged in as a repo admin.
# Safe to re-run: updates the ruleset if it already exists.
#
# Note: on GitHub Free, rulesets are only enforced on PUBLIC repositories.
set -euo pipefail

REPO="${1:?usage: scripts/protect-main.sh OWNER/REPO}"
RULESET_NAME="protect-main"
REQUIRED_CHECK="ci-pass"

read -r -d '' BODY <<JSON || true
{
  "name": "${RULESET_NAME}",
  "target": "branch",
  "enforcement": "active",
  "bypass_actors": [],
  "conditions": {
    "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] }
  },
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 0,
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": true
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": true,
        "required_status_checks": [ { "context": "${REQUIRED_CHECK}" } ]
      }
    }
  ]
}
JSON

existing_id="$(gh api "repos/${REPO}/rulesets" \
  --jq ".[] | select(.name == \"${RULESET_NAME}\") | .id" || true)"

if [[ -n "${existing_id}" ]]; then
  echo "Updating ruleset '${RULESET_NAME}' (id ${existing_id}) on ${REPO}"
  gh api -X PUT "repos/${REPO}/rulesets/${existing_id}" --input - <<<"${BODY}" >/dev/null
else
  echo "Creating ruleset '${RULESET_NAME}' on ${REPO}"
  gh api -X POST "repos/${REPO}/rulesets" --input - <<<"${BODY}" >/dev/null
fi

visibility="$(gh api "repos/${REPO}" --jq .visibility)"
echo "Done. Repo visibility: ${visibility}"
if [[ "${visibility}" != "public" ]]; then
  echo "WARNING: private repo. Rules are only enforced on GitHub Pro, Team or Enterprise."
fi
