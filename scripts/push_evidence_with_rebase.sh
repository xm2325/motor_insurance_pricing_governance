#!/usr/bin/env bash
set -euo pipefail

TARGET_BRANCH="${1:?target branch is required}"
MAX_ATTEMPTS="${2:-5}"

if ! [[ "$MAX_ATTEMPTS" =~ ^[1-9][0-9]*$ ]]; then
  echo "MAX_ATTEMPTS must be a positive integer" >&2
  exit 2
fi

for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
  echo "Evidence push attempt ${attempt}/${MAX_ATTEMPTS} -> ${TARGET_BRANCH}"
  git fetch origin "$TARGET_BRANCH"

  if ! git rebase "origin/${TARGET_BRANCH}"; then
    git rebase --abort || true
    echo "Evidence commit conflicts with origin/${TARGET_BRANCH}; refusing to overwrite." >&2
    exit 1
  fi

  if git push origin "HEAD:${TARGET_BRANCH}"; then
    echo "Evidence push succeeded on attempt ${attempt}."
    exit 0
  fi

  if [ "$attempt" -lt "$MAX_ATTEMPTS" ]; then
    sleep $((attempt * 2))
  fi
done

echo "Evidence push failed after ${MAX_ATTEMPTS} attempts; no force push was used." >&2
exit 1
