#!/usr/bin/env python3
import json, sys, re
from collections import defaultdict
path = sys.argv[1]
targets = set(sys.argv[2:]) if len(sys.argv)>2 else None
with open(path) as f: data=json.load(f)
results=data["results"]["results"]
def tid(r):
    md=(r.get("testCase") or {}).get("metadata") or {}
    if md.get("id"): return md["id"]
    return ((r.get("testCase") or {}).get("description") or "")[:30]
for r in results:
    if (r.get("provider") or {}).get("label")!="skill": continue
    t=tid(r)
    if targets and not any(t.startswith(x) for x in targets): continue
    if r.get("success"): continue
    gr=r.get("gradingResult") or {}
    for c in (gr.get("componentResults") or []):
        if c.get("pass"): continue
        at=((c.get("assertion") or {}).get("type"))
        reason=(c.get("reason") or "")[:240]
        print(f"[{t}] {at}: {reason}")
    print("-"*60)
