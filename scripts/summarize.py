#!/usr/bin/env python3
"""
Summarise one re-eval run (results/<timestamp>/) as Markdown.

Tier 1 — per skill, from claude plugin eval: mean score with the skill and
without it, and Δ. Tier 2 — per skill, from reach eval over the whole catalog:
  recall     share of the skill's own drafted prompts on which it fired
  lured      share of the near-miss prompts drafted from it (meant for a
             neighbour) on which it fired anyway — the misroute we gate on
Thresholds are the NanoCast gate's: recall >= 0.90, lured <= 0.05.
"""
import json, re, sys
from collections import defaultdict
from pathlib import Path

out = Path(sys.argv[1]); root = Path(__file__).resolve().parent.parent
lines = [f"## Re-eval {out.name}", ""]

rows = ["| skill | cases | with skill | without | Δ | tier 1 |", "|---|---|---|---|---|---|"]
for f in sorted(out.glob("*.plugin-eval.json")):
    d = json.loads(f.read_text())
    w = [r["score"] for c in d.get("cases", []) for r in c.get("arms", {}).get("with", [])]
    wo = [r["score"] for c in d.get("cases", []) for r in c.get("arms", {}).get("without", [])]
    mw = sum(w) / len(w) if w else 0.0
    mwo = sum(wo) / len(wo) if wo else 0.0
    agg = d.get("aggregates", {})
    ok = agg.get("casesPassed") == agg.get("casesTotal") and not d.get("partial")
    rows.append(f"| {f.name.split('.')[0]} | {agg.get('casesTotal')} | {mw:.2f} | {mwo:.2f} | {mw - mwo:+.2f} | {'pass' if ok else 'fail'} |")
lines += ["### Tier 1 · with the skill vs without", ""] + rows + [""]

cat = out / "catalog-eval.jsonl"
if cat.exists():
    queries = {q["id"]: q for q in json.loads((root / "catalog/queries.json").read_text())["queries"]}
    own = defaultdict(lambda: [0, 0]); lured = defaultdict(lambda: [0, 0]); errors = 0
    for line in cat.read_text().splitlines():
        r = json.loads(line); q = queries.get(r.get("query_id"))
        if not q: continue
        if r.get("error"): errors += 1; continue
        fired = set(r.get("invoked_skills") or [])
        if q.get("kind") == "neighbor_negative":
            m = re.fullmatch(r"adv-(.+)-\d+", q["id"]); target = m.group(1) if m else None
            if target: lured[target][0] += target in fired; lured[target][1] += 1
        else:
            own[q["expected_skill"]][0] += q["expected_skill"] in fired; own[q["expected_skill"]][1] += 1
    rows = ["| skill | recall | lured by near misses | tier 2 |", "|---|---|---|---|"]
    for s in sorted(set(own) | set(lured)):
        rh, rn = own[s]; lh, ln = lured[s]
        rec = rh / rn if rn else None; lr = lh / ln if ln else None
        ok = (rec is None or rec >= 0.9) and (lr is None or lr <= 0.05)
        rows.append(f"| {s} | {rh}/{rn} | {lh}/{ln} | {'pass' if ok else 'fail'} |")
    lines += ["### Tier 2 · among the whole catalog", ""] + rows + ["", f"Probes discarded with an error: {errors}.", ""]
print("\n".join(lines))
