"""opencode adapter — renders CANVAS core/ into opencode's on-disk format.

Scope (chosen by the CLI):

  per-project (default)  <target>/.opencode/skills/<id>/SKILL.md
                         <target>/.opencode/agent/<id>.md
                         <target>/opencode.json     references.canvas
  global (--global)      ~/.config/opencode/skills/<id>/SKILL.md
                         ~/.config/opencode/agent/<id>.md
                         merge references.canvas into ~/.config/opencode config

The references.canvas entry is the seam that exposes the CANVAS corpus
(lib/android/reference/*-impl.md) inside any project. When a git repo URL is
given (manifest["_canvas_repo"]), it uses `repository:` so opencode AUTO-FETCHES
the CANVAS repo into its cache — the user never clones it by hand. Without a
URL it falls back to `path:` pointing at this local checkout.

Deliberately dependency-free (stdlib only): front-matter is simple scalar YAML.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

SKILL_FOLDER_NAMES = {
    "build-android-starter": "build-android-starter",
    "build-android-feature": "build-android-feature",
    "audit": "audit",
    "perf-review": "perf-review",
}


def _yaml_scalar(key, value):
    value = value.strip()
    if value == "" or value[0] in "-?:" or value[0].isdigit() or any(c in value for c in ":,{}[]&*#|>!%@`\"'"):
        return f"{key}: \"{value.replace(chr(34), chr(92)+chr(34))}\"\n"
    return f"{key}: {value}\n"


def _skill_front_matter(meta):
    name = SKILL_FOLDER_NAMES.get(meta["id"], meta["id"])
    return "---\n" + _yaml_scalar("name", name) + _yaml_scalar("description", meta["description"]) + "---\n"


def _agent_front_matter(meta):
    out = (
        "---\n"
        + _yaml_scalar("description", meta["description"])
        + _yaml_scalar("mode", "subagent")
    )
    model = meta.get("model")
    if model:
        out += _yaml_scalar("model", model)
    return out + "---\n"


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


def _meta(manifest_entry, core_file):
    src = _front_matter(core_file)
    merged = dict(manifest_entry)
    merged.setdefault("description", src.get("description", ""))
    merged.setdefault("model", src.get("model"))  # absent => subagent inherits the invoking primary agent's model
    return merged


def _open_config(path: Path) -> dict:
    cfg = {}
    if path.exists():
        try:
            cfg = json.loads(path.read_text())
        except Exception:
            cfg = {}
    cfg.setdefault("$schema", "https://opencode.ai/config.json")
    cfg.setdefault("references", {})
    return cfg


def _canvas_reference(manifest: dict, root: Path) -> dict:
    repo = manifest.get("_canvas_repo") or os.environ.get("CANVAS_REPO")
    if repo:
        return {"repository": repo, "description": "CANVAS reference corpus — lib/android/reference/*-impl.md and core/ skills/agents. Use for native-Android architecture, Kotlin/Compose/Hilt/Room how-to."}
    return {"path": str(root), "description": "CANVAS reference corpus — lib/android/reference/*-impl.md and core/ skills/agents. Use for native-Android architecture, Kotlin/Compose/Hilt/Room how-to."}


def _sibling_reference(name: str, info: dict) -> dict:
    """Turn a sibling manifest entry into an opencode reference + description.

    Prefer git repository: (opencode auto-fetches, no clone) and fall back to a
    local path (e.g. the installer's flattened ~/.canvas cache checkout).
    """
    if info.get("url"):
        ref = {"repository": info["url"]}
    else:
        ref = {"path": str(info["path"])}
    ref["description"] = f"{name} — sibling design-system repo of CANVAS (referenced, never vendored)."
    return ref


def _write_config(cfg_path: Path, cfg: dict) -> str:
    """Merge + write a config file; returns the path string to report."""
    cfg_path.write_text(json.dumps(cfg, indent=2) + "\n")
    return f"{cfg_path} (references.canvas)"


def render(root: Path, manifest: dict, target: Path, global_install: bool) -> list[str]:
    if global_install:
        base = Path.home() / ".config" / "opencode"
    else:
        base = target / ".opencode"

    skills_dir = base / "skills"
    agents_dir = base / "agent"
    written: list[str] = []
    shown = Path.home() if global_install else target

    for skill in manifest["skills"]:
        src = root / "core" / "skills" / f"{skill['id']}.md"
        folder = SKILL_FOLDER_NAMES.get(skill["id"], skill["id"])
        out = skills_dir / folder / "SKILL.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        meta = _meta(skill, src)
        out.write_text(_skill_front_matter(meta) + "\n" + _body(src) + "\n")
        written.append(f"~/{out.relative_to(shown)}" if global_install else str(out.relative_to(target)))

    for agent in manifest["agents"]:
        src = root / "core" / "agents" / f"{agent['id']}.md"
        out = agents_dir / f"{agent['id']}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        meta = _meta(agent, src)
        out.write_text(_agent_front_matter(meta) + "\n" + _body(src) + "\n")
        written.append(f"~/{out.relative_to(shown)}" if global_install else str(out.relative_to(target)))

    # --- references.canvas + sibling repos wiring ---
    refs = {"canvas": _canvas_reference(manifest, root)}
    for name, info in (manifest.get("_siblings") or {}).items():
        if info.get("url") or info.get("path"):
            refs[name] = _sibling_reference(name, info)
    if global_install:
        cfg_dir = Path.home() / ".config" / "opencode"
        cfg_path = cfg_dir / "opencode.json"
        if not cfg_path.exists() and (cfg_dir / "opencode.jsonc").exists():
            cfg_path = cfg_dir / "opencode.jsonc"
        cfg = _open_config(cfg_path)
        cfg["references"].update(refs)
        written.append(_write_config(cfg_path, cfg))
    else:
        cfg_path = target / "opencode.json"
        cfg = _open_config(cfg_path)
        cfg["references"].update(refs)
        written.append(_write_config(cfg_path, cfg))

    return written
