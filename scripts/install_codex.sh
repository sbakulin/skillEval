#!/usr/bin/env bash
# Put this repo's skills where Codex looks for them.
#
#   scripts/install_codex.sh                                   # every skill, working tree, into ~/.agents/skills
#   scripts/install_codex.sh /etc/codex/skills add-to-watchlist--v0.1.0 data-access--v1.0.0
#
# With release tags (<skill>--v<version>) each skill is taken exactly as it was
# released — what an agent image does at build time: one directory for every
# user of the machine, pinned versions, and an update is a rebuild.
# Codex reads the same SKILL.md as Claude Code; nothing is converted.
set -euo pipefail
DEST="${1:-$HOME/.agents/skills}"; shift || true
cd "$(dirname "$0")/.."
mkdir -p "$DEST"

install_dir() {  # <source skill dir> <name>
  local target="$DEST/$2"
  [ -n "$2" ] && [ -d "$1" ] || { echo "no skill at $1" >&2; exit 1; }
  rm -rf "$target"; cp -R "$1" "$target"; echo "installed $2 → $target"
}

if [ "$#" -eq 0 ]; then
  for d in plugins/*/skills/*; do install_dir "$d" "$(basename "$d")"; done
else
  TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
  for tag in "$@"; do
    name="${tag%%--v*}"
    [ "$name" != "$tag" ] || { echo "not a release tag: $tag (expected <skill>--v<version>)" >&2; exit 1; }
    mkdir -p "$TMP/$tag"
    git archive "$tag" "plugins/$name/skills/$name" | tar -x -C "$TMP/$tag"
    install_dir "$TMP/$tag/plugins/$name/skills/$name" "$name"
  done
fi
echo "Restart Codex; /skills lists them."
