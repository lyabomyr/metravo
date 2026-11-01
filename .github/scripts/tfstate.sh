#!/usr/bin/env bash
# Keep OpenTofu's encrypted state on the orphan branch "infra-state".
#
#   tfstate.sh pull   # branch → ./terraform.tfstate (nothing if there is no state yet)
#   tfstate.sh push   # ./terraform.tfstate → branch
#
# Run from infra/terraform. The file is encrypted by OpenTofu before it is
# written, so what lands on the branch is unreadable without TF_STATE_PASSPHRASE.
set -euo pipefail

BRANCH=infra-state
STATE="$PWD/terraform.tfstate"

case "${1:-}" in
  pull)
    if git fetch -q origin "$BRANCH" 2>/dev/null; then
      git show FETCH_HEAD:terraform.tfstate > "$STATE"
      echo "state restored from $BRANCH"
    else
      echo "no saved state yet"
    fi
    ;;
  push)
    work=$(mktemp -d)
    git worktree add -q --detach "$work"
    cd "$work"
    if git fetch -q origin "$BRANCH" 2>/dev/null; then
      git checkout -q -B "$BRANCH" FETCH_HEAD
    else
      git checkout -q --orphan "$BRANCH"
      git rm -rqf .
    fi
    cp "$STATE" terraform.tfstate
    git add terraform.tfstate
    if git diff --cached --quiet; then
      echo "state unchanged"
    else
      git -c user.name=github-actions -c user.email=github-actions@users.noreply.github.com \
        commit -qm "infra state [skip ci]"
      git push -q origin "$BRANCH"
      echo "state saved to $BRANCH"
    fi
    ;;
  *)
    echo "usage: $0 pull|push" >&2
    exit 2
    ;;
esac
