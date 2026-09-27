#!/usr/bin/env python3
"""
Regenerate each plugin's runnable eval suite from its evals/cases.json.

cases.json is the source of truth: the author's cases in the NanoCast format
({id, prompt, should_fire, expectations:[{id,text}]}). This script writes the
layout `claude plugin eval` runs — evals/<case>/prompt.md + graders/*.md — with
the same rules as the NanoCast pipeline (src/lib/skills/plugin-eval.ts):

  should_fire: true   graders/fired.md          tool_used: Skill, input_match the skill name
                      graders/exp-NN-<id>.md    one llm grader per expectation, told to quote
  should_fire: false  graders/not-fired.md      tool_used: Skill, min 0, max 0, arm both

It also writes evals/reach-queries.json for every skill: the slice of the
catalog query set (catalog/queries.json, drafted by `reach query draft
--adversarial`) that concerns this skill — its own drafted prompts, and the
near-miss prompts drafted from it that belong to a neighbour. The catalog file
stays the source: adversarial prompts are about pairs of skills, so they are
kept whole and only viewed per skill.

Run it after editing cases.json or catalog/queries.json; CI fails on drift.
    python3 scripts/build_evals.py            # all plugins
    python3 scripts/build_evals.py --check    # exit 1 if anything would change
"""
import json, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_TURNS = 6

def slug(s, i):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return s or f"case-{i + 1}"

def case_ids(cases):
    seen, out = {}, []
    for i, c in enumerate(cases):
        base = slug(c.get("id"), i)
        n = seen.get(base, 0) + 1
        seen[base] = n
        out.append(base if n == 1 else f"{base}-{n}")
    return out

def fm(pairs):
    return "---\n" + "".join(f"{k}: {v}\n" for k, v in pairs) + "---\n"

def llm_grader(claim):
    return (fm([("type", "llm"), ("weight", 1)]) +
            "Judge only the agent's final answer to the user.\n\n"
            f"PASS if the answer satisfies this claim: {claim}\n"
            "FAIL otherwise.\n\n"
            "Quote the exact fragment of the answer that supports your verdict. "
            "If no fragment supports the claim, say so and FAIL.\n")

def build(plugin_dir: Path):
    skill_dirs = sorted((plugin_dir / "skills").iterdir())
    skill = skill_dirs[0].name
    cases = json.loads((plugin_dir / "evals" / "cases.json").read_text(encoding="utf-8"))
    files = {}
    for c, cid in zip(cases, case_ids(cases)):
        files[f"{cid}/prompt.md"] = (fm([("max_turns", MAX_TURNS), ("allowed_tools", "[Read, Glob, Grep, Skill]")])
                                     + "\n" + c["prompt"].strip() + "\n")
        if c.get("should_fire"):
            files[f"{cid}/graders/fired.md"] = fm([("type", "tool_used"), ("tool", "Skill"), ("input_match", json.dumps(skill))])
            exps = c.get("expectations") or []
            if not exps:
                files[f"{cid}/graders/exp-01-addresses-request.md"] = llm_grader(
                    "the answer addresses the user's request directly and is not a refusal or a question back")
            for j, e in enumerate(exps):
                files[f"{cid}/graders/exp-{j + 1:02d}-{slug(e.get('id'), j)}.md"] = llm_grader(e["text"])
        else:
            files[f"{cid}/graders/not-fired.md"] = fm([("type", "tool_used"), ("tool", "Skill"), ("min", 0), ("max", 0), ("arm", "both")])
    return files

def reach_slice(skill, catalog):
    own = [q for q in catalog.get("queries", []) if q.get("expected_skill") == skill and q.get("kind") != "neighbor_negative"]
    near = [q for q in catalog.get("queries", []) if q.get("kind") == "neighbor_negative" and re.fullmatch(rf"adv-{re.escape(skill)}-\d+", str(q.get("id", "")))]
    return {
        "derived_from": "catalog/queries.json",
        "skill": skill,
        "skill_digest": (catalog.get("provenance") or {}).get("skill_digests", {}).get(skill),
        "should_fire": own,
        "should_not_fire": near,
    }

def main():
    check = "--check" in sys.argv
    drift = []
    cat_path = ROOT / "catalog" / "queries.json"
    catalog = json.loads(cat_path.read_text(encoding="utf-8")) if cat_path.exists() else {"queries": []}
    for plugin_dir in sorted((ROOT / "plugins").iterdir()):
        skill = sorted((plugin_dir / "skills").iterdir())[0].name
        want = json.dumps(reach_slice(skill, catalog), indent=2, ensure_ascii=False) + "\n"
        out = plugin_dir / "evals" / "reach-queries.json"
        if not out.exists() or out.read_text(encoding="utf-8") != want:
            drift.append(f"{plugin_dir.name} (reach-queries)")
            if not check:
                out.write_text(want, encoding="utf-8")
    for plugin_dir in sorted((ROOT / "plugins").iterdir()):
        if not (plugin_dir / "evals" / "cases.json").exists():
            continue
        want = build(plugin_dir)
        suite = plugin_dir / "evals" / "suite"
        have = {str(p.relative_to(suite)): p.read_text(encoding="utf-8") for p in suite.rglob("*.md")} if suite.exists() else {}
        if want != have:
            drift.append(plugin_dir.name)
            if not check:
                shutil.rmtree(suite, ignore_errors=True)
                for rel, text in want.items():
                    (suite / rel).parent.mkdir(parents=True, exist_ok=True)
                    (suite / rel).write_text(text, encoding="utf-8")
    if check and drift:
        print("generated eval suites are out of date for:", ", ".join(drift), "— run scripts/build_evals.py")
        sys.exit(1)
    print(("checked" if check else "built"), "eval suites;", "changed:" if drift else "nothing changed", ", ".join(drift))

if __name__ == "__main__":
    main()
