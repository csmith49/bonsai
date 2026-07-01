#!/usr/bin/env bash

vault="${1:-${BONSAI_VAULT_ROOT:-$PWD}}"
branch="${2:-main}"

cd "$vault" || exit 1

git add -A
git diff --cached --quiet && exit 0

git commit -m "backup $(date '+%Y-%m-%d')"
git push origin "$branch"
