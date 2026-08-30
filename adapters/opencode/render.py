"""opencode adapter — renders CANVAS core/ into opencode's on-disk format.

Output layout (project scope under <target>/.opencode, or global under the
opencode user config when --global):

  .opencode/skills/<id>/SKILL.md     workflow skills (user-invocable commands)
  .opencode/agent/<id>.md            workers as subagents (mode: subagent)
  opencode.json                      references.canvas -> the CANVAS repo (reads lib/android/reference)

The reference wiring is what makes lib/android/reference/*-impl.md available
inside ANY project: opencode mounts the CANVAS repo as an advertised reference
dir, and the exported skills/agents point section-queries at it.

Deliberately dependency-free (stdlib only): front-matter is simple scalar YAML.
"""
from __future__ import annotations

import json
from pathlib import Path

SKILL_FOLDER_NAMES = {
    "build-android-starter": "build-android-starter",
    "build-android-feature": "build-android-feature",
    "audit": "audit",
    "perf-review": "perf-review",
}


def _yaml_scalar(key: str, value: str) -> str:
    """Emit a single-line YAML scalar; quote only if it could be misparsed."""
    value = value.strip()
    if value == "" or value[0] in "-?:" or value[0].isdigit() or any(c in value for c in ":,{}[]&*#|>!%@`\"'"):
        return f"{key}: \"{value.replace(chr(34), chr(92)+chr(34))}\"\n"
    return f"{key}: {value}\n"


def _skill_front_matter(meta: dict) -> str:
    name = SKILL_FOLDER_NAMES.get(meta["id"], meta["id"])
    out = "---\n"
    out += _yaml_scalar("name", name)
    out += _yaml_scalar("description", meta["description"])
    out += "---\n"
    return out


def _agent_front_matter(meta: dict) -> str:
    out = "---\n"
    out += _yaml_scalar("description", meta["description"])
    out += _yaml_scalar("mode", "subagent")
    out += _yaml_scalar("model", meta["model"])
    out += "---\n"
    return out


def _body(core_path: Path) -> str:
    """Body is the markdown AFTER the YAML front matter in the core file."""
    text = core_path.read_text()
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return text.strip()


def _front_matter(core_path: Path) -> dict:
    """Parse the core file's YAML front matter into a dict (stdlib-only)."""
    text = core_path.read_text()
    meta: dict = {}
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


def _meta(manifest_entry: dict, core_file: Path) -> dict:
    """Merge manifest entry with the source front-matter (source wins on desc)."""
    src = _front_matter(core_file)
    merged = dict(manifest_entry)
    merged.setdefault("description", src.get("description", ""))
    merged.setdefault("model", src.get("model", "sonnet"))
    return merged


def render(root: Path, manifest: dict, target: Path, global_install: bool) -> list[str]:
    if global_install:
        raise NotImplementedError(
            "opencode adapter is per-project only for now. Run without --global "
            "to write .opencode/ + opencode.json into a project dir. "
            "(Global install would need to merge into ~/.config/opencode/opencode.jsonc.)"
        )
    written: list[str] = []
    skills_dir = target / ".opencode" / "skills"
    agents_dir = target / ".opencode" / "agent"

    for skill in manifest["skills"]:
        src = root / "core" / "skills" / f"{skill['id']}.md"
        folder = SKILL_FOLDER_NAMES.get(skill["id"], skill["id"])
        out = skills_dir / folder / "SKILL.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        meta = _meta(skill, src)
        out.write_text(_skill_front_matter(meta) + "\n" + _body(src) + "\n")
        written.append(str(out.relative_to(target)))

    for agent in manifest["agents"]:
        src = root / "core" / "agents" / f"{agent['id']}.md"
        out = agents_dir / f"{agent['id']}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        meta = _meta(agent, src)
        out.write_text(_agent_front_matter(meta) + "\n" + _body(src) + "\n")
        written.append(str(out.relative_to(target)))

    cfg_path = target / "opencode.json"
    cfg = {}
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text())
        except Exception:
            cfg = {}
    cfg.setdefault("$schema", "https://opencode.ai/config.json")
    cfg.setdefault("references", {})
    cfg["references"]["canvas"] = {
        "path": str(root),
        "description": "CANVAS reference corpus — lib/android/reference/*-impl.md and core/ skills/agents. Use for native-Android architecture, Kotlin/Compose/Hilt/Room how-to.",
    }
    cfg_path.write_text(json.dumps(cfg, indent=2) + "\n")
    written.append("opencode.json (references.canvas)")

    return written
