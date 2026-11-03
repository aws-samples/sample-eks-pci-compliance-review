#!/usr/bin/env python3
"""Parse promptfoo results JSON: skill vs baseline, assertion-level + test-level,
excluding infrastructure errors (endpoint/connect/timeout)."""
import json, sys, re
from collections import defaultdict

path = sys.argv[1] if len(sys.argv) > 1 else "reports/results-sonnet-v6.json"
with open(path) as f:
    data = json.load(f)

results = data["results"]["results"]

INFRA = re.compile(r"endpoint|could not connect|connect to the|timed out|worker timed out|ReadTimeout", re.I)

def is_infra(r):
    err = (r.get("error") or "")
    if isinstance(err, dict):
        err = err.get("message", "")
    return bool(INFRA.search(str(err)))

# label -> list of records
by_label = defaultdict(list)
for r in results:
    label = (r.get("provider") or {}).get("label") or "?"
    by_label[label].append(r)

def summarize(label, recs):
    total = len(recs)
    infra = [r for r in recs if is_infra(r)]
    valid = [r for r in recs if not is_infra(r)]
    passed = [r for r in valid if r.get("success")]
    # assertion-level
    a_total = a_pass = 0
    comp_by_type = defaultdict(lambda: [0,0])
    for r in valid:
        gr = r.get("gradingResult") or {}
        comps = gr.get("componentResults") or []
        for c in comps:
            a_total += 1
            t = ((c.get("assertion") or {}).get("type")) or "?"
            comp_by_type[t][0] += 1
            if c.get("pass"):
                a_pass += 1
                comp_by_type[t][1] += 1
    print(f"\n=== {label} ===")
    print(f"  cases total={total}  infra_excluded={len(infra)}  valid={len(valid)}")
    if valid:
        print(f"  TEST-LEVEL pass: {len(passed)}/{len(valid)} = {100*len(passed)/len(valid):.1f}%")
    if a_total:
        print(f"  ASSERTION-LEVEL pass: {a_pass}/{a_total} = {100*a_pass/a_total:.1f}%")
    print("  by assertion type:")
    for t, (tot, pas) in sorted(comp_by_type.items()):
        print(f"    {t:24s} {pas}/{tot} = {100*pas/tot:.0f}%")
    return {
        "valid": len(valid), "infra": len(infra),
        "test_pass": len(passed),
        "test_rate": (100*len(passed)/len(valid)) if valid else 0,
        "assert_pass": a_pass, "assert_total": a_total,
        "assert_rate": (100*a_pass/a_total) if a_total else 0,
    }

out = {}
for label in sorted(by_label):
    out[label] = summarize(label, by_label[label])

print("\n\n===== SUMMARY (infra excluded) =====")
for label, s in out.items():
    print(f"{label:10s} test={s['test_rate']:.1f}%  assertion={s['assert_rate']:.1f}%  (valid n={s['valid']}, infra excl={s['infra']})")

if "skill" in out and "baseline" in out:
    print(f"\nImprovement (skill - baseline):")
    print(f"  test-level:      +{out['skill']['test_rate']-out['baseline']['test_rate']:.1f} pts")
    print(f"  assertion-level: +{out['skill']['assert_rate']-out['baseline']['assert_rate']:.1f} pts")
