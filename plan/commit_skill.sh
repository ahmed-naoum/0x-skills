#!/usr/bin/env bash
# Commit and push one finished skill. Usage: plan/commit_skill.sh <skill-name> ["message"]
# Safe to run from several processes at once: a lock file serializes git access.
set -u
name="${1:?skill name}"
msg="${2:-Add the $name skill}"
repo="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo" || exit 1
[ -d "skills/$name" ] || { echo "no such skill folder: skills/$name"; exit 1; }
exec 9>"$repo/.git/0x-commit.lock"
flock -w 300 9 || { echo "could not get the commit lock"; exit 1; }
git add -- "skills/$name"
if git diff --cached --quiet -- "skills/$name"; then
  echo "nothing new to commit for $name"
else
  git commit -q -m "$msg" -m "Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_016EmRLzsdtiYnUpwku8fD9P" -- "skills/$name" || { echo "commit failed"; exit 1; }
  echo "committed $name"
fi
for wait in 0 2 4 8 16; do
  sleep "$wait"
  if git push -q -u origin main 2>/dev/null; then echo "pushed"; exit 0; fi
done
echo "push failed (the commit is saved locally; it will go out with the next push)"
exit 0
