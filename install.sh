#!/usr/bin/env bash
# Install the skills in ./skills into one or more agent skill directories.
#
#   ./install.sh                         symlink every skill into ~/.agents/skills
#   ./install.sh ~/.claude/skills DIR2  ...or into the given directories instead
#   ./install.sh --skill openalex DIR   only the named skill(s); repeatable
#   ./install.sh --copy DIR             copy instead of symlink (for harnesses that don't follow links)
#   ./install.sh --force DIR            move an existing, different install to $BACKUP_DIR and replace it
#   ./install.sh --uninstall DIR        remove symlinks that point into this repo
#   ./install.sh --check                only check prerequisites
#   ./install.sh --index                print a skill index for harnesses without native skill support
#
# Symlinks are the default so that `git pull` here updates every installed copy.
# Nothing is ever deleted except symlinks into this repo; --force moves things aside.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
SRC="$REPO/skills"
DEFAULT_TARGET="$HOME/.agents/skills"
# Backups live outside every skills dir: a backup left beside the original would still
# hold a SKILL.md and be loaded as a duplicate skill.
BACKUP_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/agent-skills/backups"

mode=link force=0 action=install
skills=() targets=()

usage() { sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

while [ $# -gt 0 ]; do
  case "$1" in
    --copy) mode=copy ;;
    --force) force=1 ;;
    --uninstall) action=uninstall ;;
    --check) action=check ;;
    --index) action=index ;;
    --skill) [ $# -ge 2 ] || usage 1; skills+=("$2"); shift ;;
    -h|--help) usage 0 ;;
    -*) echo "unknown option: $1" >&2; usage 1 ;;
    *) targets+=("$1") ;;
  esac
  shift
done

if [ ${#skills[@]} -eq 0 ]; then
  for d in "$SRC"/*/; do [ -f "$d/SKILL.md" ] && skills+=("$(basename "$d")"); done
fi
for s in "${skills[@]}"; do
  [ -f "$SRC/$s/SKILL.md" ] || { echo "no such skill: $s (have: $(ls "$SRC" | tr '\n' ' '))" >&2; exit 1; }
done
[ ${#targets[@]} -gt 0 ] || targets=("$DEFAULT_TARGET")

# --- prerequisites -----------------------------------------------------------

ok()   { printf '  [ok]   %s\n' "$*"; }
warn() { printf '  [warn] %s\n' "$*"; }
miss() { printf '  [miss] %s\n' "$*"; }

check() {
  echo "Prerequisites:"
  if command -v python3 >/dev/null && python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))'; then
    ok "python3 $(python3 -c 'import platform; print(platform.python_version())')"
  else
    miss "python3 >= 3.10 (needed by openalex)"
  fi
  for s in "${skills[@]}"; do
    case "$s" in
      openalex)
        if command -v uv >/dev/null; then ok "uv (openalex: provides duckdb for \`oa.py sql\`)"
        else warn "uv not found: openalex works except \`oa.py sql\` (install: https://docs.astral.sh/uv/)"; fi
        if [ -n "${OPENALEX_API_KEY:-}" ] || [ -s "$HOME/.config/openalex/api_key" ]; then
          ok "OpenAlex API key"
        else
          warn "no OpenAlex API key: works, but 1,000 credits/day instead of 10,000."
          warn "  get a free key from an openalex.org account, then:"
          warn "  mkdir -p ~/.config/openalex && (umask 077; printf %s KEY > ~/.config/openalex/api_key)"
        fi ;;
      papis)
        if command -v papis >/dev/null; then
          ok "papis $(papis --version 2>/dev/null | awk '{print $NF}')"
          n=$(papis list --libraries 2>/dev/null | grep -c . || true)
          if [ "$n" -gt 0 ]; then ok "papis libraries configured: $n"
          else warn "papis has no libraries configured (see ~/.config/papis/config)"; fi
        else
          miss "papis (install: uv tool install papis, or pipx install papis)"
        fi ;;
    esac
  done
}

# --- index for harnesses without native skill support -------------------------

frontmatter() {  # frontmatter FIELD FILE
  awk -v k="$1" 'NR==1 && $0!="---" {exit} NR>1 && $0=="---" {exit}
                 NR>1 { if (index($0, k": ")==1) { print substr($0, length(k)+3); exit } }' "$2"
}

index() {
  echo "## Skills"
  echo
  echo "Before starting a task that matches one of these, read its SKILL.md in full and follow it."
  echo "Paths inside a skill are relative to the directory holding its SKILL.md."
  echo
  for s in "${skills[@]}"; do
    echo "- **$(frontmatter name "$SRC/$s/SKILL.md")** ($SRC/$s/SKILL.md): $(frontmatter description "$SRC/$s/SKILL.md")"
  done
}

# --- install / uninstall -------------------------------------------------------

install_one() {  # install_one SKILL TARGET_DIR
  local src="$SRC/$1" dst="$2/$1"
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
    if [ "$mode" = link ]; then echo "  = $dst (already linked)"; return; fi
  fi
  if [ -e "$dst" ] || [ -L "$dst" ]; then
    if [ "$force" -ne 1 ]; then
      echo "  ! $dst exists and is not a link to this repo; skipped (use --force to move it aside)"
      return
    fi
    if [ -L "$dst" ]; then
      rm "$dst"                       # a symlink: removing it touches no data
    else
      local bak; bak="$BACKUP_DIR/$1-$(date +%Y%m%d-%H%M%S)"
      mkdir -p "$BACKUP_DIR"; mv "$dst" "$bak"; echo "  ~ moved existing $dst -> $bak"
    fi
  fi
  if [ "$mode" = link ]; then ln -s "$src" "$dst"; echo "  + $dst -> $src"
  else cp -R "$src" "$dst"; find "$dst" -name __pycache__ -prune -exec rm -rf {} +; echo "  + $dst (copy)"; fi
}

uninstall_one() {
  local src="$SRC/$1" dst="$2/$1"
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then rm "$dst"; echo "  - $dst"
  elif [ -e "$dst" ]; then echo "  ! $dst is not a link to this repo; left alone"
  fi
}

case "$action" in
  check) check ;;
  index) index ;;
  install|uninstall)
    for t in "${targets[@]}"; do
      echo "$t:"
      [ "$action" = install ] && mkdir -p "$t"
      [ -d "$t" ] || { echo "  (does not exist)"; continue; }
      for s in "${skills[@]}"; do "${action}_one" "$s" "$t"; done
    done
    [ "$action" = install ] && { echo; check; }
    ;;
esac
