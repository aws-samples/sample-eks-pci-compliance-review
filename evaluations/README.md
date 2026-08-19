# Evaluations — aws-eks-pci-compliance-review

Evaluations are the contract for this Skill. They were written **before** any
Skill content so that baseline runs (no Skill loaded) expose the specific
failure modes the Skill must fix, and so that Skill content stays scoped to
what actually changes an evaluation outcome.

Framework: **AWSMCPSkillsEval** — loads the Skill into a Strands agent, runs the
agent against real (read-only) AWS + EKS resources, and scores results with
[promptfoo](https://www.promptfoo.dev/docs/guides/test-agent-skills/).

## Layout

```
evaluations/
├── promptfooconfig.yaml       # providers (baseline vs skill) + test wiring
├── coverage-matrix.md         # operation/branch/reference-file -> test ID map
├── providers/
│   └── strands_provider.py    # Strands agent wrapped as a promptfoo provider (read-only tools)
├── assertions/
│   └── graders.js             # shared JS assertions
├── tests/
│   ├── selection.yaml         # SEL-*: routing (positive + near-miss)
│   ├── workflow.yaml          # WF-*:  one E2E per operation/branch/decision point
│   └── reference-files.yaml   # REF-*: one E2E per reference file (11)
└── reports/
    └── evaluation-report.md   # baseline evidence + required report fields
```

## What each test group proves

- **Selection (`SEL-*`)** — the Skill is chosen for real PCI-on-EKS queries and
  is *not* chosen for near-miss queries that belong to sibling skills
  (`eks-operations-review`, `eks-healthdashboard`) or to non-EKS PCI work.
- **Workflow (`WF-*`)** — one end-to-end test per major operation, branch, and
  decision point in SKILL.md Steps 0-6, including the three branches
  (no-CDE → CDE checks N/A; access-fail → stop; CDE-scoped checks apply only to
  CDE namespaces) and the read-only / no-secrets safety guarantees.
- **Reference files (`REF-*`)** — one end-to-end test per reference file so each
  file earns its place: the check index, all 8 pillar files, the report format,
  and the PCI DSS crosswalk.

See `coverage-matrix.md` for the exact requirement → test-ID mapping.

## Evaluation Framework Setup

### Prerequisites

1. **Node + promptfoo** (test runner / scorer):
   ```bash
   node --version        # >= 18
   npx promptfoo@latest --version
   ```
2. **Python + Strands** (the agent under test):
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install strands-agents boto3
   ```
3. **Bedrock model access** for the model id in `promptfooconfig.yaml`
   (`us.anthropic.claude-sonnet-4-20250514-v1:0`). Adjust the id to a model your
   account is entitled to.

### AWS + cluster access (read-only)

Live tests (`live: true`) run against a **real AWS account and a real EKS
cluster**, using only read-only permissions:

- `kubectl` context pointing at the target cluster, with `get`/`describe` allowed.
- AWS credentials with `describe*`/`list*`/`get*` on: eks, ec2, iam, ecr,
  inspector2, guardduty, securityhub, logs, cloudwatch, cloudtrail,
  network-firewall, backup, accessanalyzer.

The provider only ever issues read-only verbs; mutating calls are refused in
code. This Skill has no mutating operations, so no test changes cloud state.
Set the target once:

```bash
export EVAL_CLUSTER_NAME=<cluster>
export EVAL_CLUSTER_REGION=<region>
export AWS_PROFILE=<read-only-profile>
```

### Run

```bash
# Everything (requires live cluster + AWS):
npx promptfoo@latest eval -c promptfooconfig.yaml

# Offline only — routing/behavior tests that need no cloud:
PROMPTFOO_STUB_AGENT=1 \
  npx promptfoo@latest eval -c promptfooconfig.yaml --filter-metadata live=false

# Inspect side by side (baseline vs skill):
npx promptfoo@latest view
```

Useful flags: `--repeat 3` (sample nondeterministic behavior), `--no-cache`
(while iterating on Skill text), `-o results.json` (machine-readable output for
the evaluation report).

### Baseline-first workflow

1. Run the suite with `skill: none` behavior only (the `baseline` provider
   column) and record failures in `reports/evaluation-report.md`.
2. Confirm each failure is something the Skill is meant to fix.
3. Only then iterate on `SKILL.md` / `references/` and re-run to show the
   `skill` column passing where `baseline` failed.

## Scoring model

- Primary signal: task correctness (JS graders in `assertions/graders.js` —
  check-ID coverage, required phrases, forbidden content, read-only trace,
  reference-file reads).
- Routing signal: `skill-used` / `not-skill-used` for `SEL-*`.
- Secondary signals: `latency`, `cost` (defined in `defaultTest`).
