# Evaluation Report — reviewing-pci-compliance-in-aws-eks

**Skill under test:** `reviewing-pci-compliance-in-aws-eks`
**Framework:** AWSMCPSkillsEval (recommended) — Skill loaded into a Strands
agent, run against real read-only AWS + EKS resources, scored with promptfoo.
**Suite:** 35 test cases — 9 selection (`SEL-*`), 15 workflow (`WF-*`),
11 reference-file (`REF-*`).
**Report status:** Baseline analysis complete; live scored runs pending an AWS
account + EKS cluster (see §5).

> **Canonical intake report:** the full report that AWS MCP reviewers use —
> covering models tested, harnesses, runs-per-case, LLM judge, the complete
> prompt list, results, and baseline comparison — lives at
> [`../../eval-reports/reviewing-pci-compliance-in-aws-eks.md`](../../eval-reports/reviewing-pci-compliance-in-aws-eks.md)
> and must be committed to AWSMCPSOps + posted on the intake ticket. This file
> is the in-suite engineering notes; the intake report is the source of truth
> for the results tables.

---

## 1. Why evaluations were built first

These evaluations were authored **before** any Skill content changes so that:

1. Running each case against a **baseline** agent (no Skill loaded) surfaces the
   specific failure modes the Skill must fix. The `promptfooconfig.yaml`
   `baseline` provider exists exactly for this contrast.
2. Skill content stays scoped: anything in `SKILL.md` / `references/` that does
   not move a test from FAIL→PASS between the `baseline` and `skill` columns is
   a candidate for removal.

## 2. Framework choice

The recommended **AWSMCPSkillsEval** framework is used — no exception requested.
It is implemented here as:

- `providers/strands_provider.py` — a Strands agent wrapped as a promptfoo
  Python provider, given only read-only tools (kubectl get/describe, AWS CLI
  describe/list/get, CloudWatch reads, and read-only access to the Skill's own
  reference files). Mutating verbs are refused in code.
- `promptfooconfig.yaml` — runs every test against two providers (`baseline`
  with no Skill, `skill` with the PCI Skill), and scores with promptfoo
  assertions (`skill-used`, `llm-rubric`, custom JS graders, `cost`, `latency`).

Because the Skill is strictly read-only, **no test mutates AWS**. Live tests
(`metadata.live: true`) still run against a **real AWS account and EKS cluster**
using read-only permissions, satisfying the requirement that cloud-touching
cases exercise real resources.

## 3. Coverage

Full requirement → test-ID mapping is in [`../coverage-matrix.md`](../coverage-matrix.md).
Summary:

| Coverage requirement | Satisfied by |
|----------------------|--------------|
| One E2E test per major operation / branch / decision point | `WF-01`..`WF-15` (Steps 0-6, all three branches, both safety guarantees) |
| One E2E test per reference file (11) | `REF-01`..`REF-11` |
| Selection — positive queries | `SEL-01`..`SEL-05` |
| Selection — near-miss negatives (routing not over-eager) | `SEL-06`..`SEL-09` |

Branch/decision points explicitly covered:
- No CDE identified → all CDE checks N/A, only cluster-wide graded (`WF-05`).
- Access verification fails → stop, no partial grading (`WF-07`).
- CDE-scoped checks apply only to confirmed CDE namespaces (`WF-12`).
- Report coverage gate — every selected check ID in a scorecard (`WF-13`).

## 4. Baseline failure modes (expected, pre-Skill)

Each test targets a behavior a generic agent (baseline, no Skill) is expected to
get wrong. These are the gaps the Skill exists to close; they are the pass/fail
predictions to confirm on the first scored run.

| Test | Expected baseline failure (no Skill) |
|------|--------------------------------------|
| SEL-01..05 | Baseline answers PCI questions ad hoc; never registers `skill-used`. |
| SEL-06..09 | Baseline may improvise a "PCI review" for non-EKS / health-check / mutation asks (no routing discipline). |
| WF-01 | Baseline starts scanning or invents a cluster instead of confirming identity first. |
| WF-02 | Baseline guesses which namespaces are CDE instead of asking. |
| WF-03 | Baseline does not know the PCI scope labels to auto-detect CDE. |
| WF-04 | Baseline picks one source instead of a union of user + detected, and skips confirmation. |
| WF-05 | Baseline fabricates CDE findings rather than marking CDE checks N/A. |
| WF-06 | Baseline ignores pillar scoping and grades whatever it likes. |
| WF-07 | Baseline proceeds with partial access / fabricates results on access failure. |
| WF-08 | Baseline checks one source (usually kubectl) and misses AWS API + CloudWatch. |
| WF-09/10/11 | Baseline asserts PASS/FAIL without citing observed values, mis-severities findings, or guesses instead of N/A. |
| WF-12 | Baseline fails CDE-only checks on non-CDE namespaces (wrong scope). |
| WF-13 | Baseline emits an unstructured summary missing scorecards, disclaimer, action plan, and crosswalk. |
| WF-14 | Baseline attempts to apply/delete resources when asked. |
| WF-15 | Baseline prints decoded Secret values. |
| REF-01 | Baseline does not know there are 67 checks / 8 pillars or the ID ranges. |
| REF-02..09 | Baseline invents ad-hoc checks, omitting the fixed per-pillar check set, severities, and PCI mappings. |
| REF-10 | Baseline uses its own report shape, not the mandated 7-section structure + finding block. |
| REF-11 | Baseline cannot map checks to PCI requirements or apply the Supported/Gap/Not-assessed roll-up. |

## 5. Run status and evidence

### Executed in this environment

**Static validation** — all suite files parse and inventory matches the matrix:
- `promptfooconfig.yaml` + all three `tests/*.yaml` parse as valid YAML.
- `assertions/graders.js` passes `node --check`; `providers/strands_provider.py`
  passes `py_compile`.
- 35 cases; IDs `SEL-01..09`, `WF-01..15`, `REF-01..11` match `coverage-matrix.md`.

**Offline harness run** — the `live=false` subset (9 tests × 2 providers = 18
runs) was executed with `PROMPTFOO_STUB_AGENT=1` to validate the wiring. This
run is *not* a behavioral score (the stub has no real agent and there is no
grader model locally); its only purpose is to prove the harness works:

| Signal | Result | Interpretation |
|--------|--------|----------------|
| Test selection via `metadata.live` | 18 runs selected | `--filter-metadata live=false` wiring works |
| `cost` (defaultTest) | 18/18 pass | provider returns cost; assertion wired |
| `latency` (defaultTest) | 18/18 pass | assertion wired |
| `not-skill-used` (SEL-06..09) | 8/8 pass | near-miss routing assertion wired |
| `skill-used` (SEL-01..05) | 0/10 pass | expected: stub never invokes a real Skill |
| `llm-rubric` (WF/REF offline) | 18 errored | expected: needs a grader model (see fix below) |

Fixes made as a direct result of this run:
1. `metadata.live` added to every test (the `--filter-metadata` filter reads
   test-level `metadata`, not `vars`) — before this, 0 tests were selected.
2. The provider now returns `cost` + `tokenUsage` — before this, every run
   errored with "Cost assertion does not support providers that do not return
   cost".
3. `defaultTest.options.provider` set to Bedrock so `llm-rubric` grading does
   not fall back to OpenAI (which errored with "OPENAI_API_KEY is not set").

The `skill-used` failures and `llm-rubric` errors under the stub are the
*expected baseline*: with no real agent and no grader, the Skill is never
selected and rubrics cannot be scored. Both require the live run below.

### Pending (requires reviewer environment)

The scored baseline-vs-skill runs require Bedrock model access plus a real,
read-only EKS cluster + AWS account, and the Strands SDK installed
(`pip install strands-agents boto3`) — not available in this authoring
environment. To produce the scored evidence, a reviewer runs:

```bash
# Offline routing/behavior subset (no cloud):
PROMPTFOO_STUB_AGENT=1 \
  npx promptfoo@latest eval -c promptfooconfig.yaml \
  --filter-metadata live=false -o reports/results-offline.json

# Full suite against a real read-only cluster:
export EVAL_CLUSTER_NAME=<cluster> EVAL_CLUSTER_REGION=<region> AWS_PROFILE=<ro>
npx promptfoo@latest eval -c promptfooconfig.yaml -o reports/results-live.json
```

### Results table (to complete on first scored run)

| Test | baseline | skill | Delta (skill fixes baseline?) |
|------|----------|-------|-------------------------------|
| SEL-01 |  |  |  |
| ... | | | |

Fill from `results-offline.json` / `results-live.json`. A healthy result shows
the `skill` column passing where `baseline` fails, and both columns agreeing on
`SEL-06..09` (neither should route to this Skill for near-miss queries).

## 6. Maintenance

- When a pillar file gains/loses a check ID, update the matching `expectedChecks`
  list in `tests/reference-files.yaml` and `WF-13`.
- When the workflow gains a branch or decision point, add a `WF-*` case and a
  row in `coverage-matrix.md` before changing `SKILL.md`.
- Keep `SEL-*` near-miss targets in sync with the sibling skills named in the
  Skill's "When NOT to use" section.
