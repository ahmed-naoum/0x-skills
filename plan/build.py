#!/usr/bin/env python3
"""Merge and validate the skill-tree plan. Run from anywhere: python3 build.py

Reads layers.json and skills/*.json next to this file; writes plan.json, tree.md and index.md;
prints errors and warnings. Exit code 1 if there are errors.

Skills are listed by layer, then by their optional integer "order" field, then by file name.
"""
import glob
import json
import os
import re
import sys
from collections import Counter

D = os.path.dirname(os.path.abspath(__file__))
EXTERNAL = {"seo-aeo-geo-ultimate", "data", "dataviz", "claude-api", "code-review", "security-review", "roadmap"}
LEVELS = ("core", "pro", "expert")
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+){0,2}$")
FILE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*\.md$")

errors, warns = [], []


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:  # noqa: BLE001
        errors.append(f"{os.path.relpath(path, D)}: cannot parse JSON ({e})")
        return None


layers = load(os.path.join(D, "layers.json")) or []
if not isinstance(layers, list):
    errors.append("layers.json: must be a list")
    layers = []
layer_ids = [layer.get("id") for layer in layers]
if layer_ids != list(range(len(layers))):
    errors.append(f"layers.json: ids must be 0..n-1 in order, got {layer_ids}")
if not 9 <= len(layers) <= 13:
    errors.append(f"layers.json: need 9-13 layers, got {len(layers)}")
for layer in layers:
    for key in ("name", "question"):
        if not layer.get(key):
            errors.append(f"layers.json: layer {layer.get('id')} missing '{key}'")

skills = []
for path in sorted(glob.glob(os.path.join(D, "skills", "*.json"))):
    s = load(path)
    if s is None:
        continue
    s["_file"] = os.path.basename(path)
    skills.append(s)

names = [s.get("name") for s in skills]
for n, c in Counter(names).items():
    if c > 1:
        errors.append(f"duplicate skill name: {n}")
if not 26 <= len(skills) <= 32:
    errors.append(f"need 26-32 skills (including 3dui), got {len(skills)}")
if "3dui" not in names:
    errors.append("the existing skill '3dui' is missing")
if "roadmap" in names:
    errors.append("'roadmap' is written separately - remove it from the plan")

seen = {}
level_count = Counter()
for s in skills:
    n = s.get("name", "?")
    where = f"skills/{s['_file']}"
    if s["_file"] != f"{n}.json":
        errors.append(f"{where}: file name must be '{n}.json'")
    if not NAME.match(str(n)):
        errors.append(f"{where}: name '{n}' must be lowercase kebab-case, 1-3 words")
    if s.get("layer") not in layer_ids:
        errors.append(f"{where}: layer {s.get('layer')!r} is not a layer id")
    for key in ("title", "summary"):
        if not s.get(key):
            errors.append(f"{where}: missing '{key}'")
    if "order" in s and (not isinstance(s["order"], int) or isinstance(s["order"], bool)):
        errors.append(f"{where}: 'order' must be an integer (position inside the layer)")
    use_when = s.get("useWhen") or []
    if not 5 <= len(use_when) <= 10:
        errors.append(f"{where}: useWhen needs 5-10 entries, has {len(use_when)}")
    not_for = s.get("notFor") or []
    if not 1 <= len(not_for) <= 6:
        errors.append(f"{where}: notFor needs 1-6 entries, has {len(not_for)}")
    for nf in not_for:
        if not nf.get("topic") or not nf.get("use"):
            errors.append(f"{where}: every notFor needs 'topic' and 'use'")
        elif nf["use"] not in names and nf["use"] not in EXTERNAL:
            errors.append(f"{where}: notFor points to unknown skill '{nf['use']}'")
        elif nf["use"] == n:
            errors.append(f"{where}: notFor points to itself")
    refs = s.get("references") or []
    existing = bool(s.get("existing"))
    if existing and n != "3dui":
        errors.append(f"{where}: only 3dui may be marked existing")
    if existing:
        if len(refs) != 1 or refs[0].get("file") != "SKILL.md":
            errors.append(f"{where}: existing skill needs exactly one reference with file 'SKILL.md'")
    elif not 3 <= len(refs) <= 8:
        errors.append(f"{where}: needs 3-8 references, has {len(refs)}")
    files = [r.get("file") for r in refs]
    for f, c in Counter(files).items():
        if c > 1:
            errors.append(f"{where}: duplicate reference file '{f}'")
    for r in refs:
        rw = f"{where} > {r.get('file')}"
        if not existing and not FILE.match(str(r.get("file"))):
            errors.append(f"{rw}: file name must be lowercase kebab-case ending .md")
        for key in ("title", "purpose"):
            if not r.get(key):
                errors.append(f"{rw}: missing '{key}'")
        leaves = r.get("leaves") or []
        if not 5 <= len(leaves) <= 10:
            (errors if not 4 <= len(leaves) <= 12 else warns).append(f"{rw}: wants 5-10 leaves, has {len(leaves)}")
        for leaf in leaves:
            topic = str(leaf.get("topic", "")).strip()
            if not topic:
                errors.append(f"{rw}: empty leaf")
                continue
            if leaf.get("level") not in LEVELS:
                errors.append(f"{rw}: leaf '{topic[:40]}' has level {leaf.get('level')!r}")
            else:
                level_count[leaf["level"]] += 1
            if len(topic.split()) > 18:
                warns.append(f"{rw}: leaf over 18 words: '{topic[:60]}...'")
            key = re.sub(r"[^a-z0-9]+", " ", topic.lower()).strip()
            if key in seen:
                errors.append(f"duplicate leaf '{topic[:60]}' in {rw} and {seen[key]}")
            seen[key] = rw

for layer in layers:
    if not any(s.get("layer") == layer.get("id") for s in skills):
        errors.append(f"layer {layer.get('id')} '{layer.get('name')}' has no skills")

total = sum(level_count.values())
if total:
    share = {k: level_count[k] / total for k in LEVELS}
    if share["core"] < 0.28 or share["expert"] > 0.30:
        warns.append(
            "level mix is off (want ~40/40/20): "
            + ", ".join(f"{k} {share[k]:.0%}" for k in LEVELS)
        )

# Inside a layer, skills follow their optional integer "order" (foundation first), then file name.
order = {n: i for i, n in enumerate(names)}
skills.sort(key=lambda s: (
    s.get("layer") if isinstance(s.get("layer"), int) else 99,
    s.get("order") if isinstance(s.get("order"), int) else 99,
    order[s.get("name")],
))
plan = {"layers": layers, "skills": [{k: v for k, v in s.items() if k != "_file"} for s in skills]}
with open(os.path.join(D, "plan.json"), "w", encoding="utf-8") as f:
    json.dump(plan, f, indent=1, ensure_ascii=False)

mark = {"core": "●", "pro": "◐", "expert": "○"}
out = ["# Tree (generated by build.py - do not edit)", "", "● core   ◐ pro   ○ expert", ""]
for layer in layers:
    out.append(f"## {layer.get('id')} · {layer.get('name')} — {layer.get('question')}")
    out.append("")
    for s in skills:
        if s.get("layer") != layer.get("id"):
            continue
        out.append(f"### {s.get('name')} — {s.get('summary')}")
        for r in s.get("references") or []:
            out.append(f"- **{r.get('file')}** — {r.get('title')}")
            for leaf in r.get("leaves") or []:
                out.append(f"  - {mark.get(leaf.get('level'), '?')} {leaf.get('topic')}")
        out.append("")
with open(os.path.join(D, "tree.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(out) + "\n")

# index.md: one line per reference, so a writer can see what every sibling skill owns.
idx = ["# Index (generated by build.py - do not edit)", ""]
for layer in layers:
    idx.append(f"## {layer.get('id')} · {layer.get('name')}")
    for s in skills:
        if s.get("layer") != layer.get("id"):
            continue
        idx.append(f"- **{s.get('name')}** — {s.get('summary')}")
        for r in s.get("references") or []:
            if r.get("file") != "SKILL.md":
                idx.append(f"  - {r.get('file')} — {r.get('title')}")
    idx.append("")
with open(os.path.join(D, "index.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(idx) + "\n")

refs_total = sum(len(s.get("references") or []) for s in skills)
print(f"{len(layers)} layers, {len(skills)} skills, {refs_total} references, {total} leaves "
      f"({', '.join(f'{k} {level_count[k]}' for k in LEVELS)})")
for w in warns:
    print("warning:", w)
for e in errors:
    print("ERROR:", e)
print(f"{len(errors)} errors, {len(warns)} warnings")
sys.exit(1 if errors else 0)
