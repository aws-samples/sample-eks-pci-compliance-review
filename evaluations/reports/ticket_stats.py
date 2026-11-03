#!/usr/bin/env python3
"""Extract token / LLM-call / latency / cost stats per provider for the intake ticket,
infra errors excluded."""
import json, sys, re
from collections import defaultdict
path = sys.argv[1] if len(sys.argv)>1 else "reports/results-sonnet-v6.json"
with open(path) as f: data=json.load(f)
results=data["results"]["results"]
INFRA=re.compile(r"endpoint|could not connect|connect to the|timed out|worker timed out|ReadTimeout",re.I)
def is_infra(r):
    e=r.get("error") or ""
    if isinstance(e,dict): e=e.get("message","")
    return bool(INFRA.search(str(e)))

agg=defaultdict(lambda: {"n":0,"tok":0,"calls":0,"lat":0,"cost":0,"tok_n":0,"calls_n":0,"lat_n":0,"cost_n":0})
for r in results:
    if is_infra(r): continue
    lab=(r.get("provider") or {}).get("label") or "?"
    a=agg[lab]; a["n"]+=1
    tu=r.get("tokenUsage") or {}
    tot=tu.get("total")
    if tot: a["tok"]+=tot; a["tok_n"]+=1
    # llm calls: tokenUsage.numRequests if present, else metadata.toolCalls length is separate
    nr=tu.get("numRequests")
    if nr: a["calls"]+=nr; a["calls_n"]+=1
    lat=r.get("latencyMs")
    if lat: a["lat"]+=lat; a["lat_n"]+=1
    c=r.get("cost")
    if c: a["cost"]+=c; a["cost_n"]+=1

for lab,a in sorted(agg.items()):
    print(f"=== {lab} (n={a['n']}) ===")
    if a["tok_n"]:  print(f"  avg tokens/run:   {a['tok']/a['tok_n']:.0f}  (from {a['tok_n']} runs)")
    if a["calls_n"]:print(f"  avg LLM calls/run:{a['calls']/a['calls_n']:.2f}  (from {a['calls_n']} runs)")
    if a["lat_n"]:  print(f"  avg latency/run:  {a['lat']/a['lat_n']:.0f} ms  (from {a['lat_n']} runs)")
    if a["cost_n"]: print(f"  avg cost/run:     ${a['cost']/a['cost_n']:.4f}  (from {a['cost_n']} runs)")
