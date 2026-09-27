#!/usr/bin/env bash
# Re-evaluate every skill in this repo. Run it on a schedule, after a model
# change, or before tagging a release. Writes one report per run under
# results/<timestamp>/ (not committed; CI uploads it as an artifact).
#
#   tier 0  reach lint           form, names, description budget, overlaps. No model calls.
#   tier 1  claude plugin eval   each skill's own cases, with the skill and without (Δ).
#   tier 2  reach eval           the whole catalog at once: does each skill still win
#                                its own prompts, and stay out of its neighbours'?
#
# Needs: python3, uv, Claude Code >= 2.1.269 on PATH (the agents run 2.1.276), ANTHROPIC_API_KEY.
# Knobs: RUNS (default 3), MODEL for tier 1 (default sonnet), ONLY (one plugin).
#        Tier 2 agent, attempts and thresholds: reach.toml.
set -euo pipefail
cd "$(dirname "$0")/.."

REACH_REF="e620c06cdfd191c8ab8b7d26b24e2493dc390eda"   # pinned google/skill-reach commit
REACH=(uvx --from "git+https://github.com/google/skill-reach@${REACH_REF}" reach)
RUNS="${RUNS:-3}"; MODEL="${MODEL:-sonnet}"
OUT="results/$(date -u +%Y-%m-%dT%H-%M-%SZ)"; mkdir -p "$OUT"

# One flat catalog of every skill, the way an agent sees them all at once.
CATALOG="$(mktemp -d)"; trap 'rm -rf "$CATALOG"' EXIT
for d in plugins/*/skills/*; do cp -R "$d" "$CATALOG/"; done

echo "▸ generated files are current"
python3 scripts/build_evals.py --check

echo "▸ tier 0 · reach lint"
"${REACH[@]}" lint "$CATALOG" --format json > "$OUT/lint.json" || true
"${REACH[@]}" lint "$CATALOG" --format concise || true

echo "▸ tier 1 · claude plugin eval (runs=$RUNS, model=$MODEL)"
for p in plugins/*; do
  n="$(basename "$p")"
  [ -n "${ONLY:-}" ] && [ "$n" != "$ONLY" ] && continue
  [ -d "$p/evals/suite" ] || { echo "  $n: no cases, skipped"; continue; }
  claude plugin eval "$p" --runs "$RUNS" --model "$MODEL" --ablation with-without \
    --trust-plugin --no-publish --json "$OUT/$n.plugin-eval.json" >/dev/null 2>&1 \
    && echo "  $n: pass" || echo "  $n: FAIL (see $OUT/$n.plugin-eval.json)"
done

echo "▸ tier 2 · the catalog: every skill resident, every drafted prompt probed"
# --yes: the probe runs Claude Code with these skills loaded, on this machine.
# That is only acceptable because every skill here passed review into the repo.
# `reach eval`, not `reach check`: check ignores [runtime.options] in reach.toml,
# so the built-in skills stay resident and every probe is discarded as a leak.
"${REACH[@]}" eval --skills "$CATALOG" --queries catalog/queries.json --config reach.toml \
  --out "$OUT/catalog-eval.jsonl" --yes -q || echo "  catalog: probe run failed"

python3 scripts/summarize.py "$OUT" | tee "$OUT/SUMMARY.md"
