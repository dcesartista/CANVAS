"""claude-plugin adapter — renders CANVAS core/ into a self-contained Claude
Code plugin for distribution via a plugin marketplace.

Unlike the plain claude-code adapter (which writes skills/agents into a
project's .claude/ and references the CANVAS repo by absolute path), this
produces a PLUGIN that Claude Code copies into its cache on install. Cached
plugins cannot reference files outside their own directory, so the plugin is
SELF-CONTAINED: the whole reference corpus is mirrored into the plugin under
the same lib/ layout the skill/agent bodies expect.

Output (a plugin root, e.g. distribution/claude-plugin/canvas):

  .claude-plugin/plugin.json   identity + version (the installable unit)
  skills/<id>/SKILL.md         4 workflow skills (slash commands)
  agents/<id>.md              4 workers (subagents)
  lib/android/reference/*.md   the impl corpus (as the bodies expect)
  lib/android/skills/*/SKILL.md
  reference/*.md               the theory corpus
  QUALITY-BAR.md               the anchor

Distribution: the plugin lives inside a marketplace git repo that has
.claude-plugin/marketplace.json; users run /plugin marketplace add <repo>
then /plugin install canvas@<marketplace> — no repo cloning.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

SKILL_FOLDER_NAMES = {
    "build-android-starter": "build-android-starter",
    "build-android-feature": "build-android-feature",
    "audit": "audit",
    "perf-review": "perf-review",
}
MARKER = "<!-- canvas-reference-root -->"


def _yaml_scalar(key, value):
    value = value.strip()
    if value == "" or value[0] in "-?:" or value[0].isdigit() or any(c in value for c in ":,{}[]&*#|>!%@`\"'"):
        return f"{key}: \"{value.replace(chr(34), chr(92)+chr(34))}\"\n"
    return f"{key}: {value}\n"


def _body(core_path):
    text = core_path.read_text()
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return text.strip()


def _front_matter(core_path):
    text = core_path.read_text()
    meta = {}
    if not text.startswith("---"):
        return meta
    parts = text.split("---", 2)
    if len(parts) < 3:
        return meta
    for line in parts[1].strip().splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        val = val.strip()
        if val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        meta[key.strip()] = val
    return meta


def _meta(entry, core_file):
    src = _front_matter(core_file)
    merged = dict(entry)
    merged.setdefault("id", entry["id"])
    merged.setdefault("description", src.get("description", ""))
    merged.setdefault("model", src.get("model"))  # absent => subagent uses default model
    return merged


def _with_reference_preamble(body):
    line = (f"{MARKER} Reference corpus bundled in this plugin: QUALITY-BAR.md at plugin root; "
            "impl docs under lib/android/reference/; component skills under lib/android/skills/; "
            "theory docs under reference/. Load the file you need before authoring.")
    if MARKER in body:
        return body
    return line + "\n\n" + body


def _skill_front_matter(meta, skill_id):
    name = SKILL_FOLDER_NAMES.get(skill_id, skill_id)
    out = "---\n" + _yaml_scalar("name", name) + _yaml_scalar("description", meta["description"])
    out += _yaml_scalar("slash_command", f"/{name}") + _yaml_scalar("usage", "<project-intent>") + "---\n"
    return out


def _agent_front_matter(meta):
    out = "---\n" + _yaml_scalar("name", meta["id"]) + _yaml_scalar("description", meta["description"])
    model = meta.get("model")
    if model:
        out += _yaml_scalar("model", model)
    out += _yaml_scalar("mode", "subagent") + _yaml_scalar("tools", "Read, Write, Edit, Glob, Grep, Bash")
    out += "---\n"
    return out


def _copy(src: Path, dst: Path):
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def render(root: Path, manifest: dict, target: Path, global_install: bool) -> list[str]:
    # The plugin is a self-contained dir; target <dir> IS the plugin root.
    written: list[str] = []

    # 1. bundle the corpus (mirror lib/ so bodies resolve unchanged)
    _copy(root / "QUALITY-BAR.md", target / "QUALITY-BAR.md")
    written.append("QUALITY-BAR.md")
    _copy(root / "lib" / "android" / "reference", target / "lib" / "android" / "reference")
    written.append("lib/android/reference/ (14 impl docs)")
    _copy(root / "lib" / "android" / "skills", target / "lib" / "android" / "skills")
    written.append("lib/android/skills/ (15 component skills)")
    _copy(root / "reference", target / "reference")
    written.append("reference/ (12 theory docs)")

    # 2. skills + agents
    for skill in manifest["skills"]:
        src = root / "core" / "skills" / f"{skill['id']}.md"
        folder = SKILL_FOLDER_NAMES.get(skill["id"], skill["id"])
        out = target / "skills" / folder / "SKILL.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        meta = _meta(skill, src)
        out.write_text(_skill_front_matter(meta, skill["id"]) + "\n" + _with_reference_preamble(_body(src)) + "\n")
        written.append(f"skills/{folder}/SKILL.md")
    for agent in manifest["agents"]:
        src = root / "core" / "agents" / f"{agent['id']}.md"
        out = target / "agents" / f"{agent['id']}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        meta = _meta(agent, src)
        out.write_text(_agent_front_matter(meta) + "\n" + _with_reference_preamble(_body(src)) + "\n")
        written.append(f"agents/{agent['id']}.md")

    # 3. plugin manifest
    v = manifest.get("_canvas_version") or "0.1.0"
    plugin_manifest = {
        "name": "canvas",
        "description": "Agentic native-Android coding system: scaffold, feature, audit and perf-review skills + workers, bundled with the CANVAS reference corpus.",
        "version": v,
        "author": {"name": "Dito Cesartista", "email": "m.cesartista@gmail.com"},
    }
    mdir = target / ".claude-plugin"
    mdir.mkdir(parents=True, exist_ok=True)
    (mdir / "plugin.json").write_text(json.dumps(plugin_manifest, indent=2) + "\n")
    written.append(".claude-plugin/plugin.json")

    return written
