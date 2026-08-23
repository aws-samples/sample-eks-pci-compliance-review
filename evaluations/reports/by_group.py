#!/usr/bin/env python3
"""Per-group (SEL/WF/REF) assertion-level + strict pass for a given provider label, infra excluded."""
import json, sys, re
from collections import defaultdict
path=sys.argv[1]; label=sys.argv[2] if len(sys.argv)>2 else "skill"
with open(path) as f: data=json.load(f)
INFRA=re.compile(r"endpoint|could not connect|connect to the|timed out|worker timed out|ReadTimeout",re.I)
def is_infra(r):
    e=r.get("error") or ""
    if isinstance(e,dict): e=e.get("message","")
    return bool(INFRA.search(str(e)))
def tid(r):
    md=(r.get("testCase") or {}).get("metadata") or {}
    if md.get("id"): return md["id"]
    return ((r.get("testCase") or {}).get("description") or "")[:6]
def grp(t):
    for g in ("SEL","WF","REF"):
        if str(t).startswith(g): return g
    return "?"
agg=defaultdict(lambda:{"a_t":0,"a_p":0,"t_t":0,"t_p":0,"infra":0})
for r in data["results"]["results"]:
    if (r.get("provider") or {}).get("label")!=label: continue
    g=grp(tid(r)); a=agg[g]
    if is_infra(r): a["infra"]+=1; continue
    a["t_t"]+=1
    if r.get("success"): a["t_p"]+=1
    for c in ((r.get("gradingResult") or {}).get("componentResults") or []):
        a["a_t"]+=1
        if c.get("pass"): a["a_p"]+=1
print(f"provider={label}")
tot=defaultdict(int)
for g in ("SEL","WF","REF"):
    a=agg[g]
    tot["a_t"]+=a["a_t"]; tot["a_p"]+=a["a_p"]; tot["t_t"]+=a["t_t"]; tot["t_p"]+=a["t_p"]; tot["infra"]+=a["infra"]
    print(f"  {g}: assertion {a['a_p']}/{a['a_t']} ({100*a['a_p']/max(a['a_t'],1):.0f}%)  strict {a['t_p']}/{a['t_t']} ({100*a['t_p']/max(a['t_t'],1):.0f}%)  infra={a['infra']}")
print(f"  ALL: assertion {tot['a_p']}/{tot['a_t']} ({100*tot['a_p']/max(tot['a_t'],1):.1f}%)  strict {tot['t_p']}/{tot['t_t']} ({100*tot['t_p']/max(tot['t_t'],1):.1f}%)  infra={tot['infra']}")
