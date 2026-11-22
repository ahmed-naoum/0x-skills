#!/usr/bin/env python3
"""Generate the readable tree from the plan.

Usage: python3 plan/make_roadmap.py [output-dir]     (default: the repo root)

Writes:
  TREE.md                                        the whole tree, for people
  skills/roadmap/references/layer-NN-<slug>.md   one file per layer, for the roadmap skill
  skills/roadmap/references/skill-map.md         every skill, what it owns, and its reference files

Run build.py first: this script reads the plan.json it produces.
"""
import json
import os
import re
import sys
from collections import Counter

D = os.path.dirname(os.path.abspath(__file__))
out_root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(D)
with open(os.path.join(D, "plan.json"), encoding="utf-8") as f:
    plan = json.load(f)
layers, skills = plan["layers"], plan["skills"]
MARK = {"core": "●", "pro": "◐", "expert": "○"}
LEGEND = "● core: every shipped product needs it   ◐ pro: needed once real users and money arrive   ○ expert: needed at scale or in special cases"


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower().replace("&", "and")).strip("-")


def leaves_of(skill):
    return [leaf for ref in skill["references"] for leaf in ref["leaves"]]


def count(items):
    c = Counter(leaf["level"] for leaf in items)
    return f"{len(items)} ({c['core']} ● / {c['pro']} ◐ / {c['expert']} ○)"


def write(rel, lines):
    path = os.path.join(out_root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip("\n") + "\n")
    return path


def skill_block(skill, heading):
    block = [f"{heading} {skill['name']}", "", skill["summary"], ""]
    for ref in skill["references"]:
        block.append(f"**{ref['title']}**" + ("" if ref["file"] == "SKILL.md" else f" (`references/{ref['file']}`)"))
        block.append("")
        for leaf in ref["leaves"]:
            block.append(f"- {MARK[leaf['level']]} {leaf['topic']}")
        block.append("")
    return block


all_leaves = [leaf for s in skills for leaf in leaves_of(s)]
refs_total = sum(len(s["references"]) for s in skills if not s.get("existing"))

# TREE.md
tree = [
    "# The tree: web development from the machine to the customer",
    "",
    f"{len(layers)} layers, {len(skills)} skills, {len(all_leaves)} competencies. "
    "Read it top to bottom: each layer stands on the ones above it.",
    "",
    LEGEND,
    "",
    "| # | Layer | The question it answers | Skills |",
    "|---|---|---|---|",
]
for layer in layers:
    mine = [s for s in skills if s["layer"] == layer["id"]]
    names = ", ".join(f"[{s['name']}](#{s['name']})" for s in mine)
    tree.append(f"| {layer['id']} | [{layer['name']}](#layer-{layer['id']}-{slug(layer['name'])}) | {layer['question']} | {names} |")
tree.append("")
for layer in layers:
    mine = [s for s in skills if s["layer"] == layer["id"]]
    layer_leaves = [leaf for s in mine for leaf in leaves_of(s)]
    tree += [f"## Layer {layer['id']}: {layer['name']}", "", f"{layer['question']} Competencies: {count(layer_leaves)}.", ""]
    for s in mine:
        tree += skill_block(s, "###")
write("TREE.md", tree)

# One file per layer for the roadmap skill
ref_dir = os.path.join("skills", "roadmap", "references")
layer_files = []
for layer in layers:
    mine = [s for s in skills if s["layer"] == layer["id"]]
    layer_leaves = [leaf for s in mine for leaf in leaves_of(s)]
    name = f"layer-{layer['id']:02d}-{slug(layer['name'])}.md"
    lines = [
        f"# Layer {layer['id']}: {layer['name']}",
        "",
        f"Read this when: the user asks what there is to know about {layer['name'].lower()}, wants a study list or a gap check for this layer, "
        "or you need to see which skill and file owns a topic here.",
        "",
        f"{layer['question']}",
        "",
        f"Competencies: {count(layer_leaves)}. {LEGEND}",
        "",
        "Each heading is a skill (`0x:<name>`); each bold line is one of its reference files.",
        "",
    ]
    for s in mine:
        lines += skill_block(s, "##")
    write(os.path.join(ref_dir, name), lines)
    layer_files.append((layer, name, mine, layer_leaves))

# Skill map
smap = [
    "# Skill map",
    "",
    "Read this when: you need to know which skill, and which file inside it, owns a topic; or the user asks what the set covers.",
    "",
    "| Layer | Skill | Owns | Competencies |",
    "|---|---|---|---|",
]
for layer in layers:
    for s in skills:
        if s["layer"] == layer["id"]:
            smap.append(f"| {layer['id']} {layer['name']} | `0x:{s['name']}` | {s['summary']} | {count(leaves_of(s))} |")
smap += ["", "## What each skill hands to another", ""]
for s in skills:
    if s.get("notFor"):
        smap.append(f"**{s['name']}** does not cover:")
        for nf in s["notFor"]:
            smap.append(f"- {nf['topic']} → `{nf['use']}`")
        smap.append("")
smap += ["## Reference files by skill", ""]
for s in skills:
    if s.get("existing"):
        continue
    smap.append(f"**{s['name']}**: " + "; ".join(f"`{r['file']}` ({r['title']})" for r in s["references"]))
    smap.append("")
write(os.path.join(ref_dir, "skill-map.md"), smap)

print(f"TREE.md: {len(tree)} lines; {len(layer_files)} layer files; skill-map.md: {len(smap)} lines")
for layer, name, mine, layer_leaves in layer_files:
    print(f"  {name}: {len(mine)} skills, {count(layer_leaves)}")
