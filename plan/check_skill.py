#!/usr/bin/env python3
"""Check one written skill against the plan and the writing standard.

Usage: python3 check_skill.py <skill-name> [repo-dir]
Prints every problem, then "<n> errors, <m> warnings". Exit code 1 if there are errors.
"""
import json
import os
import re
import sys

D = os.path.dirname(os.path.abspath(__file__))
if len(sys.argv) < 2:
    sys.exit(__doc__)
name = sys.argv[1]
repo = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(D)
skill_dir = os.path.join(repo, "skills", name)
errors, warns = [], []

try:
    with open(os.path.join(D, "skills", f"{name}.json"), encoding="utf-8") as f:
        plan = json.load(f)
except Exception as e:  # noqa: BLE001
    sys.exit(f"cannot read the plan entry for '{name}': {e}")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")


def common(rel, text):
    fences = len(re.findall(r"^\s*```", text, flags=re.M))
    if fences % 2:
        errors.append(f"{rel}: unbalanced code fences ({fences})")
    for bad in ("WRITING.md", "plan entry", "SPEC.md", "check_skill.py"):
        if bad in text:
            errors.append(f"{rel}: mentions '{bad}' (the writing process must not appear in the skill)")
    if EMOJI.search(text):
        warns.append(f"{rel}: contains emoji or pictographs")
    for i, line in enumerate(text.split("\n"), 1):
        if len(line) > 400 and not line.lstrip().startswith(("|", "description:", "http")):
            warns.append(f"{rel}:{i}: very long line ({len(line)} chars)")


skill_md = os.path.join(skill_dir, "SKILL.md")
if not os.path.isfile(skill_md):
    errors.append("SKILL.md is missing")
else:
    text = read(skill_md)
    lines = text.split("\n")
    m = re.match(r"^---\n(.*?)\n---\n", text, flags=re.S)
    if not m:
        errors.append("SKILL.md: must start with a '---' frontmatter block")
    else:
        fm = {}
        for line in m.group(1).split("\n"):
            if not line.strip():
                continue
            km = re.match(r"^([A-Za-z_-]+):\s?(.*)$", line)
            if not km:
                errors.append(f"SKILL.md frontmatter: cannot parse line '{line[:60]}' (description must be one line)")
                continue
            fm[km.group(1)] = km.group(2).strip()
        if set(fm) != {"name", "description"}:
            errors.append(f"SKILL.md frontmatter: must have exactly 'name' and 'description', has {sorted(fm)}")
        if fm.get("name") != name:
            errors.append(f"SKILL.md frontmatter: name is '{fm.get('name')}', must be '{name}'")
        desc = fm.get("description", "")
        if desc[:1] in "\"'" and desc[-1:] == desc[:1]:
            desc = desc[1:-1]
        if "<" in desc or ">" in desc:
            errors.append("SKILL.md description: must not contain angle brackets")
        if not 200 <= len(desc) <= 450:
            errors.append(f"SKILL.md description: {len(desc)} characters, must be 250-420")
        elif not 250 <= len(desc) <= 420:
            warns.append(f"SKILL.md description: {len(desc)} characters, aim for 250-420")
        if "Use when" not in desc and "Use for" not in desc and "Use whenever" not in desc:
            warns.append("SKILL.md description: should say when to use it ('Use when ...')")
        if re.search(r":\s", desc) and fm.get("description", "")[:1] not in "\"'":
            errors.append("SKILL.md description: contains ': ' so YAML needs it wrapped in double quotes")
    if len(lines) > 175:
        errors.append(f"SKILL.md: {len(lines)} lines, limit is 160")
    elif len(lines) > 160:
        warns.append(f"SKILL.md: {len(lines)} lines, limit is 160")
    for r in plan.get("references", []):
        if f"references/{r['file']}" not in text:
            errors.append(f"SKILL.md: route table does not link references/{r['file']}")
    for ref in set(re.findall(r"references/([A-Za-z0-9._-]+\.md)", text)):
        if not os.path.isfile(os.path.join(skill_dir, "references", ref)):
            errors.append(f"SKILL.md: links references/{ref}, which does not exist")
    for nf in plan.get("notFor", []):
        if nf["use"] not in text:
            warns.append(f"SKILL.md: 'Not this skill' does not mention '{nf['use']}'")
    common("SKILL.md", text)

ref_dir = os.path.join(skill_dir, "references")
planned = [r["file"] for r in plan.get("references", [])]
for fn in planned:
    path = os.path.join(ref_dir, fn)
    rel = f"references/{fn}"
    if not os.path.isfile(path):
        errors.append(f"{rel}: missing")
        continue
    text = read(path)
    lines = text.rstrip("\n").split("\n")
    if not lines[0].startswith("# "):
        errors.append(f"{rel}: first line must be a '# Title' heading")
    if not any(line.startswith("Read this when:") for line in lines[:8]):
        errors.append(f"{rel}: needs a 'Read this when:' line right under the title")
    if len(lines) < 100 or len(lines) > 340:
        errors.append(f"{rel}: {len(lines)} lines, aim for 140-260 (hard limits 100-340)")
    elif len(lines) < 130 or len(lines) > 300:
        warns.append(f"{rel}: {len(lines)} lines, aim for 140-260")
    if len(lines) > 300 and "contents" not in text[:1500].lower():
        warns.append(f"{rel}: over 300 lines, add a short table of contents")
    if "## Ask the user" not in text:
        warns.append(f"{rel}: no '## Ask the user' section")
    common(rel, text)
if os.path.isdir(ref_dir):
    for fn in sorted(os.listdir(ref_dir)):
        if fn not in planned:
            warns.append(f"references/{fn}: not in the plan")
scripts = os.path.join(skill_dir, "scripts")
if os.path.isdir(scripts) and len(os.listdir(scripts)) > 2:
    warns.append("scripts/: more than two scripts")

for w in warns:
    print("warning:", w)
for e in errors:
    print("ERROR:", e)
print(f"{name}: {len(errors)} errors, {len(warns)} warnings")
sys.exit(1 if errors else 0)
