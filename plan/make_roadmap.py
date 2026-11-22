#!/usr/bin/env python3
"""Generate the readable tree, the README and the roadmap skill's generated files from the plan.

Usage: python3 plan/make_roadmap.py [output-dir]     (default: the repo root)

Always writes:
  TREE.md      the whole tree, for people
  README.md    install line, layers, and the skills table with what is built so far

If skills/roadmap/SKILL.md exists in the output dir, also writes:
  skills/roadmap/references/layer-NN-<slug>.md   one file per layer
  skills/roadmap/references/skill-map.md         every skill, what it owns, what it hands off
and refreshes the block between "<!-- layers:start -->" and "<!-- layers:end -->" in that SKILL.md.

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


# README.md
def built(skill):
    return os.path.isfile(os.path.join(out_root, "skills", skill["name"], "SKILL.md"))


def reviewed_names():
    """Skills whose adversarial review is committed, read from the git history."""
    import subprocess
    try:
        log = subprocess.run(["git", "-C", out_root, "log", "--format=%s"], capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return set()
    return {m.group(1) for m in re.finditer(r"^Review the ([a-z0-9-]+) skill", log, flags=re.M)}


reviewed = reviewed_names()


def status_of(skill):
    if skill.get("existing"):
        return "built and tested"
    if not built(skill):
        return "planned"
    return "built and reviewed" if skill["name"] in reviewed else "draft, review pending"


done = [s for s in skills if status_of(s).startswith("built")]
readme = [
    "# 0x skills",
    "",
    "Skills for Claude Code that cover web development from the machine to the customer: "
    f"{len(skills) + 1} skills on a tree of {len(layers)} layers and {len(all_leaves)} competencies. "
    "Each skill is what a principal engineer who has also founded companies would tell Claude before it touches that part of your product: "
    "the defaults, the decision rules, the numbers, what breaks in production, and what to skip until later.",
    "",
    "## Install",
    "",
    "In Claude Code (2.1.275 or later):",
    "",
    "```",
    "/plugin install 0x --marketplace ahmed-naoum/0x-skills",
    "```",
    "",
    "On older versions, in two steps:",
    "",
    "```",
    "/plugin marketplace add ahmed-naoum/0x-skills",
    "/plugin install 0x@0x-skills",
    "```",
    "",
    "The skills appear as `0x:<name>` and load by themselves when a task falls in their area. "
    "Ask `0x:roadmap` what to learn next, what is missing before a launch, or which skill owns a topic.",
    "",
    "## The tree",
    "",
    f"[TREE.md](TREE.md) lists all {len(all_leaves)} competencies, marked by level: {LEGEND}.",
    "",
    "| # | Layer | The question it answers | Skills |",
    "|---|---|---|---|",
]
for layer in layers:
    mine = [s for s in skills if s["layer"] == layer["id"]]
    readme.append(f"| {layer['id']} | {layer['name']} | {layer['question']} | " + ", ".join(f"`{s['name']}`" for s in mine) + " |")
readme += [
    "",
    "## Skills",
    "",
    (f"{len(done)} of {len(skills)} are finished so far; the rest are being written and reviewed, the most used first. " if len(done) < len(skills) else f"All {len(skills)} are built and reviewed. ")
    + ("`roadmap`, the map of the set, is built too." if os.path.isfile(os.path.join(out_root, "skills", "roadmap", "SKILL.md")) else "`roadmap`, the map of the set, is written last."),
    "",
    "| Skill | What it covers | Reference files | Competencies | Status |",
    "|---|---|---|---|---|",
]
for s in skills:
    n_refs = "engine + templates" if s.get("existing") else str(len(s["references"]))
    status = status_of(s)
    link = f"[`{s['name']}`](skills/{s['name']}/SKILL.md)" if built(s) else f"`{s['name']}`"
    readme.append(f"| {link} | {s['summary']} | {n_refs} | {len(leaves_of(s))} | {status} |")
readme += [
    "",
    "## How a skill is shaped",
    "",
    "```",
    "skills/<name>/",
    "├── SKILL.md           stance, route table, defaults by stage, done-checks, what it hands to other skills",
    "└── references/*.md    one file per sub-area, read only when the task needs it",
    "```",
    "",
    "Advice is tagged by stage: **Prototype** (no real users yet), **Launch** (real users and first revenue), "
    "**Scale** (meaningful traffic or revenue, and a team). The default stack the skills assume when you have not chosen one is "
    "TypeScript, Next.js, PostgreSQL, Stripe and a PaaS; every skill follows what your project already uses first.",
    "",
    "## How the set is built and extended",
    "",
    "The `plan/` folder is the source of the tree and of every skill:",
    "",
    "- `plan/layers.json` and `plan/skills/<name>.json`: the layers, and for each skill its triggers, its hand-offs and the competencies each reference file must cover.",
    "- `plan/build.py`: validates the plan (every competency exactly once, size limits, hand-offs that point at real skills) and writes `plan/tree.md` and `plan/index.md`.",
    "- `plan/WRITING.md`: the standard every skill is written to.",
    "- `plan/check_skill.py <name>`: checks a written skill against its plan entry and the standard.",
    "- `plan/make_roadmap.py`: regenerates `TREE.md`, this README and the roadmap skill's tree files.",
    "",
    "To add or change a skill: edit its plan entry, run `python3 plan/build.py`, write the files to the standard, "
    "run `python3 plan/check_skill.py <name>`, then `python3 plan/make_roadmap.py`.",
    "",
    "Each skill was written from its plan entry, then reviewed by a second, adversarial pass that checked commands, code, "
    "numbers and vendor facts and fixed what it found. That lowers the error rate; it does not make it zero. "
    "Legal, tax and accounting sections describe common practice and say where a professional is needed.",
]
write("README.md", readme)

layer_files = []
roadmap_skill = os.path.join(out_root, "skills", "roadmap", "SKILL.md")
if os.path.isfile(roadmap_skill):
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
    write(os.path.join(ref_dir, "skill-map.md"), smap)

    with open(roadmap_skill, encoding="utf-8") as f:
        text = f.read()
    a, b = "<!-- layers:start -->", "<!-- layers:end -->"
    if a in text and b in text:
        table = ["| # | Layer | Skills | Tree file |", "|---|---|---|---|"]
        for layer, name, mine, layer_leaves in layer_files:
            table.append(f"| {layer['id']} | {layer['name']}: {layer['question']} | " + ", ".join(f"`0x:{s['name']}`" for s in mine) + f" | `references/{name}` |")
        text = text[: text.index(a) + len(a)] + "\n" + "\n".join(table) + "\n" + text[text.index(b):]
        with open(roadmap_skill, "w", encoding="utf-8") as f:
            f.write(text)

print(f"TREE.md: {len(tree)} lines; README.md: {len(readme)} lines; {len(layer_files)} roadmap layer files; {len(done)}/{len(skills)} skills built")
for layer, name, mine, layer_leaves in layer_files:
    print(f"  {name}: {len(mine)} skills, {count(layer_leaves)}")
