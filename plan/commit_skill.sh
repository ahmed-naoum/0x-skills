#!/usr/bin/env bash
# Publish one skill from the build folder into the repo, commit and push it.
# Usage: plan/commit_skill.sh <skill-name> draft|review
# Safe to run from several processes at once: a lock file serializes git access.
set -u
name="${1:?skill name}"
stage="${2:?draft or review}"
case "$name" in *[!a-z0-9-]*|"") echo "bad skill name"; exit 1;; esac
case "$stage" in draft) msg="Draft the $name skill";; review) msg="Review the $name skill";; *) echo "stage must be draft or review"; exit 1;; esac
repo="$(cd "$(dirname "$0")/.." && pwd)"
build="${OX_BUILD:-/home/user/0x-build}"
src="$build/skills/$name"
[ -f "$src/SKILL.md" ] || { echo "nothing to publish: $src/SKILL.md is missing"; exit 1; }
python3 "$repo/plan/check_skill.py" "$name" "$build" >/tmp/0x-check-$name.txt 2>&1 || { cat /tmp/0x-check-$name.txt; echo "not published: fix the checker errors first"; exit 1; }
exec 9>"$repo/.git/0x-commit.lock"
flock -w 600 9 || { echo "could not get the commit lock"; exit 1; }
cd "$repo" || exit 1
python3 - "$src" "$repo/skills/$name" <<'PY'
import shutil, sys
src, dst = sys.argv[1], sys.argv[2]
shutil.rmtree(dst, ignore_errors=True)
shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", ".*"))
PY
git add -A -- "skills/$name"
git commit -q --allow-empty -m "$msg" -m "Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_016EmRLzsdtiYnUpwku8fD9P" -- "skills/$name" 2>/dev/null \
  || git commit -q --allow-empty -m "$msg" -m "Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_016EmRLzsdtiYnUpwku8fD9P" || { echo "commit failed"; exit 1; }
echo "committed: $msg"
for wait in 0 2 4 8 16; do
  sleep "$wait"
  if git push -q -u origin main 2>/dev/null; then echo "pushed"; exit 0; fi
done
echo "push failed (the commit is saved locally and goes out with the next push)"
exit 0
