#!/usr/bin/env bash
# Put this repo's skills where Codex looks for them.
#
#   scripts/install_codex.sh                 # every skill, into ~/.agents/skills
#   scripts/install_codex.sh /etc/codex/skills add-to-watchlist--v0.1.0
#
# The second form is what an agent image does at build time: one directory for
# every user of the machine, and the skills at exactly the git tag that was
# released — so the image tag is the version, and an update is a rebuild.
# Codex reads the same SKILL.md as Claude Code; nothing is converted.
set -euo pipefail
DEST="${1:-$HOME/.agents/skills}"; REF="${2:-}"
cd "$(dirname "$0")/.."
if [ -n "$REF" ]; then
  TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
  git archive "$REF" plugins | tar -x -C "$TMP"; SRC="$TMP/plugins"
else
  SRC="plugins"
fi
mkdir -p "$DEST"
for d in "$SRC"/*/skills/*; do
  n="$(basename "$d")"; rm -rf "${DEST:?}/$n"; cp -R "$d" "$DEST/$n"; echo "installed $n → $DEST/$n"
done
echo "Restart Codex; /skills lists them."
