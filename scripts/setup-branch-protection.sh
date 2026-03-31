#!/usr/bin/env bash
set -euo pipefail

# Setup branch protection rules for the repository.
# Requires: gh CLI authenticated with admin access.
#
# Usage: ./scripts/setup-branch-protection.sh [owner/repo]

REPO="${1:-$(gh repo view --json nameWithOwner -q .nameWithOwner)}"
BRANCH="main"

echo "Setting up branch protection for ${REPO}@${BRANCH}..."

gh api "repos/${REPO}/branches/${BRANCH}/protection" \
  -X PUT \
  -H "Accept: application/vnd.github+json" \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["ci"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_linear_history": false
}
EOF

echo "Branch protection configured:"
echo "  - PRs required (1 approval)"
echo "  - Status checks required (ci)"
echo "  - Direct pushes to main blocked"
echo "  - Force pushes disabled"
echo ""
echo "Next steps:"
echo "  1. Install cubic.dev GitHub App on this repo"
echo "  2. cubic.dev will auto-review all PRs once installed"
