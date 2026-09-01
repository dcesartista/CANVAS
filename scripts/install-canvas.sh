#!/usr/bin/env bash
# install-canvas.sh — CANVAS bootstrap. Designed to run as `curl -fsSL <url> | sh`.
#
# Scope (opencode):
#   bare | --project [dir]   project-local: writes .opencode/ + opencode.json
#                            into the current folder (or <dir>). Nothing global.
#   --global                 CANVAS for all projects. EXPLICIT OPT-IN.
#
# CANVAS is fetched into the hidden ~/.canvas cache (never cloned into the
# consumer project), then `scripts/canvas export --host opencode` renders from
# that cache and applies the chosen scope.
set -euo pipefail

PROG="$(basename "$0")"
: "${CANVAS_URL:=https://github.com/dcesartista/CANVAS.git}"

usage() {
  cat <<EOF
usage: curl -fsSL <installer> | sh [--] [options]

options:
  --global          install CANVAS for ALL projects (explicit opt-in)
  --project <dir>   install into <dir>/ (default: the current folder)
  --url <repo>      CANVAS git source (default: \$CANVAS_URL)
  --help            show this help
EOF
}

scope="project"
target=""
url="$CANVAS_URL"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --global) scope="global"; shift ;;
    --project) scope="project"; target="$2"; shift 2 ;;
    --url) url="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    --) shift; break ;;
    *) usage >&2; exit 2 ;;
  esac
done

# --- fetch CANVAS into the hidden cache (no clone into the project) ---
CACHE_ROOT="$HOME/.canvas"
dest="$CACHE_ROOT/src/canvas"
echo "canvas: fetching $url -> $dest"
mkdir -p "$CACHE_ROOT/src"

if [[ -d "$dest/.git" ]]; then
  git -C "$dest" fetch --depth 1 --force origin >/dev/null 2>&1
  git -C "$dest" reset --hard FETCH_HEAD >/dev/null 2>&1
else
  rm -rf "$dest"
  git clone --depth 1 "$url" "$dest" >/dev/null 2>&1
fi
[[ -f "$dest/scripts/canvas" ]] || { echo "canvas: error: source did not yield CANVAS (bad --url?)" >&2; exit 1; }

# --- build the scope args for the exported CLI ---
args=(export --host opencode --from "$dest" --repo "$url")
if [[ "$scope" == "global" ]]; then
  args+=(--global)
else
  # project-local: land .opencode/ + opencode.json in the target (this folder by default)
  if [[ -n "$target" ]]; then
    args+=(--project "$(cd "$target" && pwd)")
  fi
fi

echo "canvas: applying $scope install"
exec python3 "$dest/scripts/canvas" "${args[@]}"
