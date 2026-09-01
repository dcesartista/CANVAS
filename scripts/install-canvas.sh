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
: "${PALETTE_URL:=https://github.com/dcesartista/PALETTE.git}"
: "${INK_BASIC_URL:=https://github.com/dcesartista/Ink-Basic.git}"

CACHE_ROOT="$HOME/.canvas"

usage() {
  cat <<EOF
usage: curl -fsSL <installer> | sh [--] [options]

options:
  --global          install CANVAS for ALL projects (explicit opt-in)
  --project <dir>   install into <dir>/ (default: the current folder)
  --host <h>[,..]   restrict to hosts: opencode, claude-code (default: all)
  --url <repo>      CANVAS git source (default: \$CANVAS_URL)
  --no-siblings     skip the sibling repos (palette + ink-basic) (default: include)
  --update          refresh an already-installed scope instead of (re)installing
  --help            show this help
EOF
}

scope="project"
target=""
url="$CANVAS_URL"
siblings=1
update=0
declare -a hosts=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --global) scope="global"; shift ;;
    --project) scope="project"; target="$2"; shift 2 ;;
    --host)
      IFS=',' read -r -a hosts <<< "$2"; shift 2 ;;
    --url) url="$2"; shift 2 ;;
    --no-siblings) siblings=0; shift ;;
    --update) update=1; shift ;;
    --help|-h) usage; exit 0 ;;
    --) shift; break ;;
    *) usage >&2; exit 2 ;;
  esac
done

# Supported hosts (adapter dirs present in the source). Default = all of them.
if [[ ${#hosts[@]} -eq 0 ]]; then
  hosts=("opencode" "claude-code")
fi

# --- fetch a repo into the hidden cache (no clone into the project) ---
fetch() {
  local repo_url="$1" label="$2"
  local d="$CACHE_ROOT/src/$label"
  if [[ -d "$d/.git" ]]; then
    git -C "$d" fetch --depth 1 --force origin >/dev/null 2>&1
    git -C "$d" reset --hard FETCH_HEAD >/dev/null 2>&1
  else
    rm -rf "$d"
    git clone --depth 1 "$repo_url" "$d" >/dev/null 2>&1
  fi
  [[ -d "$d/.git" ]] || { echo "canvas: error: could not fetch $label from $repo_url" >&2; exit 1; }
}

# --- build the sibling args + fetch them into the cache (skip on --update) ---
sib_args=()
if [[ "$update" -eq 1 ]]; then
  siblings=0
fi
if [[ "$siblings" -eq 1 ]]; then
  echo "canvas: fetching siblings: palette ($PALETTE_URL), ink-basic ($INK_BASIC_URL)"
  fetch "$PALETTE_URL"    palette
  fetch "$INK_BASIC_URL"  ink-basic
  sib_args=(
    --sibling "palette=$PALETTE_URL"    --sibling-path "palette=$CACHE_ROOT/src/palette"
    --sibling "ink-basic=$INK_BASIC_URL" --sibling-path "ink-basic=$CACHE_ROOT/src/ink-basic"
  )
fi

# --- fetch CANVAS into the hidden cache (no clone into the project) ---
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

# --- update mode: replay the recorded install instead of installing ---
if [[ "$update" -eq 1 ]]; then
  echo "canvas: updating recorded install ($scope)"
  uargs=(update)
  if [[ "$scope" == "global" ]]; then
    uargs+=(--global)
  else
    uargs+=(--project "$(cd "${target:-$PWD}" && pwd)")
  fi
  exec python3 "$dest/scripts/canvas" "${uargs[@]}"
fi

# --- install for each requested host ---
# project scope: the CLI defaults the opencode target to cwd, but be explicit
# so claude-code lands in the same folder too.
proj_args=()
if [[ "$scope" == "project" ]]; then
  proj_args+=(--target "$(cd "${target:-$PWD}" && pwd)")
fi

for host in "${hosts[@]}"; do
  echo "canvas: applying $scope install for host '$host'"
  args=(export --host "$host" --from "$dest" --repo "$url" "${sib_args[@]}")
  if [[ "$scope" == "global" ]]; then
    args+=(--global)
  else
    args+=("${proj_args[@]}")
  fi
  python3 "$dest/scripts/canvas" "${args[@]}"
done
