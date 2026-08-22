#!/usr/bin/env python3
"""Detailed per-test breakdown for skill provider: which tests fail strict, and why."""
import json, sys, re
from collections import defaultdict

path = sys.argv[1] if len(sys.argv) > 1 else "reports/results-sonnet-v6.json"
with open(path) as f:
    data = json.load(f)
results = data["results"]["results"]

INFRA = re.compile(r"endpoint|could not connect|connect to the|timed out|worker timed out|ReadTimeout", re.I)
def is_infra(r):
    err = (r.get("error") or "")
    if isinstance(err, dict): err = err.get("message","")
    return bool(INFRA.search(str(err)))

# group skill records by test id (from vars or description)
def test_id(r):
    md = (r.get("testCase") or {}).get("metadata") or {}
    if md.get("id"): return md["id"]
    desc = (r.get("testCase") or {}).get("description") or ""
    return desc[:40]

skill = [r for r in results if ((r.get("provider") or {}).get("label")=="skill")]
# per test id: aggregate over the 3 repeats
byid = defaultdict(list)
for r in skill:
    if is_infra(r): 
        byid[test_id(r)].append(("INFRA",None))
        continue
    byid[test_id(r)].append(("OK" if r.get("success") else "FAIL", r))

print("Per-test (skill) across 3 repeats [strict = all assertions pass]:")
strict_fail_ids = []
for tid in sorted(byid):
    runs = byid[tid]
    oks = sum(1 for s,_ in runs if s=="OK")
    fails = sum(1 for s,_ in runs if s=="FAIL")
    infras = sum(1 for s,_ in runs if s=="INFRA")
    marker = "" if fails==0 and infras==0 else "  <-- has strict failures" if fails else "  (infra only)"
    print(f"  {tid:18s} OK={oks} FAIL={fails} INFRA={infras}{marker}")
    if fails:
        strict_fail_ids.append(tid)

# What assertion types drive the strict failures?
print("\nFailing assertion detail (first failing component per failing run):")
fail_types = defaultdict(int)
for tid in strict_fail_ids:
    for s, r in byid[tid]:
        if s!="FAIL": continue
        gr = r.get("gradingResult") or {}
        for c in (gr.get("componentResults") or []):
            if not c.get("pass"):
                t = ((c.get("assertion") or {}).get("type")) or "?"
                fail_types[t]+=1
for t,n in sorted(fail_types.items(), key=lambda x:-x[1]):
    print(f"  {t}: {n} failing components")
