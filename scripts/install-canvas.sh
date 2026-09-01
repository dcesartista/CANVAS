#!/usr/bin/env bash
# install-canvas.sh — CANVAS bootstrap. Designed to run as `curl -fsSL <url> | sh`.
#
# Installs every host CANVAS supports (currently opencode + claude-code) from a
# single fetched source, no plugin required. Scope:
#
#   bare | --project [dir]   project-local: writes <host>'s project layout into
#                            the current folder (or <dir>). Nothing global.
#   --global                 CANVAS for ALL projects. EXPLICIT OPT-IN.
#   --host <h>[,<h>...]      restrict to specific hosts (default: all supported)
#
# CANVAS is fetched into the hidden ~/.canvas cache (never cloned into the
# consumer project), then `scripts/canvas export --host <h> --from <cache>`
# renders from that cache and applies the chosen scope for each host.
set -euo pipefail

: "${CANVAS_URL:=https://github.com/dcesartista/CANVAS.git}"

usage() {
  cat <<EOF
usage: curl -fsSL <installer> | sh [--] [options]

options:
  --global          install CANVAS for ALL projects (explicit opt-in)
  --project <dir>   install into <dir>/ (default: the current folder)
  --host <h>[,..]   restrict to hosts: opencode, claude-code (default: all)
  --url <repo>      CANVAS git source (default: \$CANVAS_URL)
  --help            show this help
EOF
}

scope="project"
target=""
url="$CANVAS_URL"
declare -a hosts=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --global) scope="global"; shift ;;
    --project) scope="project"; target="$2"; shift 2 ;;
    --host)
      IFS=',' read -r -a hosts <<< "$2"; shift 2 ;;
    --url) url="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    --) shift; break ;;
    *) usage >&2; exit 2 ;;
  esac
done

# Supported hosts (adapter dirs present in the source). Default = all of them.
if [[ ${#hosts[@]} -eq 0 ]]; then
  hosts=("opencode" "claude-code")
fi

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

# --- install for each requested host ---
# project scope: the CLI defaults the opencode target to cwd, but be explicit
# so claude-code lands in the same folder too.
proj_args=()
if [[ "$scope" == "project" ]]; then
  proj_args+=(--target "$(cd "${target:-$PWD}" && pwd)")
fi

for host in "${hosts[@]}"; do
  echo "canvas: applying $scope install for host '$host'"
  args=(export --host "$host" --from "$dest" --repo "$url")
  if [[ "$scope" == "global" ]]; then
    args+=(--global)
  else
    args+=("${proj_args[@]}")
  fi
  python3 "$dest/scripts/canvas" "${args[@]}"
done
