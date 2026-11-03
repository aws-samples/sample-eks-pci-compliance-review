#!/usr/bin/env python3
"""For WF-14/WF-15 skill runs: show whether noMutatingToolCalls passed and list toolCalls,
to distinguish a real safety breach from a grader-phrasing artifact."""
import json, sys
path=sys.argv[1]
with open(path) as f: data=json.load(f)
for r in data["results"]["results"]:
    if (r.get("provider") or {}).get("label")!="skill": continue
    md=(r.get("testCase") or {}).get("metadata") or {}
    desc=((r.get("testCase") or {}).get("description") or "")
    tid=md.get("id") or desc[:20]
    if not (str(tid).startswith("WF-14") or str(tid).startswith("WF-15") or "Read-only" in desc or "Secret" in desc):
        continue
    gr=r.get("gradingResult") or {}
    comps=gr.get("componentResults") or []
    nomut=[c for c in comps if ((c.get("assertion") or {}).get("type"))=="noMutatingToolCalls"]
    tool_calls=((r.get("metadata") or {}).get("toolCalls")) or (r.get("response",{}) or {})
    print(f"--- {tid} ---")
    for c in nomut:
        print(f"  noMutatingToolCalls pass={c.get('pass')} reason={(c.get('reason') or '')[:120]}")
    # list tool calls if present in metadata
    tc=(r.get("metadata") or {}).get("toolCalls")
    if tc is not None:
        print(f"  toolCalls={tc}")
