"""claude-code adapter — renders CANVAS core/ into Claude Code's on-disk format.

Output layout (project scope under <target>/.claude, or global user scope
~/.claude when --global):

  .claude/skills/<id>/SKILL.md        workflow skills (slash commands)
  .claude/agents/<id>.md              workers as subagents

The CANVAS reference corpus stays in the CANVAS repo (single git pull updates
it). Each exported file gets a one-line "reference root" preamble so the model
knows where lib/android/reference and lib/android/skills live — this is the
Claude-Code-specific "how" of pointing at the shared "what".

Note: unlike opencode, Claude Code has no `references` config key; the corpus
is addressed by absolute path (CANVAS repo) and by CLAUDE.md when the consumer
mounts the repo. Global install is fully supported (skills/agents are just
files under ~/.claude/).
"""
from __future__ import annotations

from pathlib import Path

SKILL_FOLDER_NAMES = {
    "build-android-starter": "build-android-starter",
    "build-android-feature": "build-android-feature",
    "audit": "audit",
    "perf-review": "perf-review",
}
MARKER = "<!-- canvas-reference-root -->"


def _yaml_scalar(key: str, value: str) -> str:
    value = value.strip()
    if value == "" or value[0] in "-?:" or value[0].isdigit() or any(c in value for c in ":,{}[]&*#|>!%@`\"'"):
        return f"{key}: \"{value.replace(chr(34), chr(92)+chr(34))}\"\n"
    return f"{key}: {value}\n"


def _body(core_path: Path) -> str:
    text = core_path.read_text()
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return text.strip()


def _front_matter(core_path: Path) -> dict:
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


def _reference_root(root: Path, global_install: bool) -> str:
    return str(root.expanduser().resolve())


def _with_reference_preamble(body: str, root: Path, siblings: dict | None = None) -> str:
    line = f"{MARKER} CANVAS reference corpus root: {root} (read-only; lib/android/reference/*-impl.md, lib/android/skills/, lib/process/gates/)."
    for name, info in (siblings or {}).items():
        loc = info.get("path") or info.get("url")
        if loc:
            line += f" | {name}: {loc}"
    if MARKER in body:
        return body
    return line + "\n\n" + body


def _skill_front_matter(meta: dict, skill_id: str) -> str:
    name = SKILL_FOLDER_NAMES.get(skill_id, skill_id)
    out = "---\n"
    out += _yaml_scalar("name", name)
    out += _yaml_scalar("description", meta["description"])
    tools = meta.get("tools")
    if tools:
        out += _yaml_scalar("allowed-tools", tools)
    out += "---\n"
    return out


def _agent_front_matter(meta: dict) -> str:
    out = "---\n"
    out += _yaml_scalar("name", meta["id"])
    out += _yaml_scalar("description", meta["description"])
    model = meta.get("model")
    if model:
        out += _yaml_scalar("model", model)
    tools = meta.get("tools")
    if not tools:
        raise ValueError(
            f"agent '{meta['id']}' has no tools grant in core/manifest.json — "
            "refusing to guess (a read-only agent must never receive Write/Edit)"
        )
    out += _yaml_scalar("tools", tools)
    out += "---\n"
    return out


def _meta(manifest_entry: dict, core_file: Path) -> dict:
    src = _front_matter(core_file)
    merged = dict(manifest_entry)
    merged.setdefault("id", manifest_entry["id"])
    merged.setdefault("description", src.get("description", ""))
    merged.setdefault("model", src.get("model"))  # absent => subagent uses default model
    return merged


def render(root: Path, manifest: dict, target: Path, global_install: bool) -> list[str]:
    # Effective install base. Global -> the user's ~/.claude dir; project ->
    # <target>/.claude (mirrors opencode's <target>/.opencode).
    base = (Path.home() / ".claude") if global_install else (target / ".claude")
    ref_root = _reference_root(root, global_install)

    written: list[str] = []
    skills_dir = base / "skills"
    agents_dir = base / "agents"
    shown = Path.home() if global_install else target
    siblings = manifest.get("_siblings")

    for skill in manifest["skills"]:
        src = root / "core" / "skills" / f"{skill['id']}.md"
        folder = SKILL_FOLDER_NAMES.get(skill["id"], skill["id"])
        out = skills_dir / folder / "SKILL.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        meta = _meta(skill, src)
        body = _with_reference_preamble(_body(src), ref_root, siblings)
        out.write_text(_skill_front_matter(meta, skill["id"]) + "\n" + body + "\n")
        written.append(f"~/{out.relative_to(shown)}" if global_install else str(out.relative_to(target)))

    for agent in manifest["agents"]:
        src = root / "core" / "agents" / f"{agent['id']}.md"
        out = agents_dir / f"{agent['id']}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        meta = _meta(agent, src)
        body = _with_reference_preamble(_body(src), ref_root, siblings)
        out.write_text(_agent_front_matter(meta) + "\n" + body + "\n")
        written.append(f"~/{out.relative_to(shown)}" if global_install else str(out.relative_to(target)))

    return written
