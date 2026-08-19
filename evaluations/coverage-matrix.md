# Evaluation Coverage Matrix — aws-eks-pci-compliance-review

This matrix is the contract between the Skill and its evaluations. Every major
operation, branch, decision point, and reference file in the Skill maps to at
least one end-to-end test case. Selection (routing) is covered separately with
positive and near-miss cases.

Rule applied (from intake guidance):
- One E2E test per major operation / branch / decision point.
- One E2E test per reference file.
- Selection test cases covering positive queries (Skill should be selected).
- Plus near-miss negatives so routing is not over-eager.

Test IDs use the file prefix: `SEL-*` (selection.yaml), `WF-*` (workflow.yaml),
`REF-*` (reference-files.yaml).

---

## A. Selection / routing (positive + near-miss)

| Requirement | Source in SKILL.md | Test ID(s) | Kind |
|-------------|--------------------|-----------|------|
| Triggers on "PCI DSS review on EKS" | description / When to use | SEL-01 | positive |
| Triggers on "validate EKS for PCI" | When to use | SEL-02 | positive |
| Triggers on "CDE namespaces meet PCI DSS" | When to use | SEL-03 | positive |
| Triggers on "EKS PCI audit before QSA" | When to use | SEL-04 | positive |
| Triggers on "which PCI DSS controls missing on EKS" | When to use | SEL-05 | positive |
| Does NOT fire for general EKS best-practices review | When NOT to use | SEL-06 | near-miss (→ eks-operations-review) |
| Does NOT fire for quick cluster health check | When NOT to use | SEL-07 | near-miss (→ eks-healthdashboard) |
| Does NOT fire for non-EKS PCI (RDS/EC2) | When NOT to use | SEL-08 | near-miss (non-EKS) |
| Does NOT fire for a cluster mutation request | When NOT to use / read-only | SEL-09 | near-miss (read-only guard) |

## B. Workflow operations / branches / decision points

| Step | Operation / branch / decision | Source | Test ID(s) |
|------|-------------------------------|--------|-----------|
| Step 0 | Confirm cluster identity (name/region/account, context, env) before acting | Workflow Step 0 | WF-01 |
| Step 1 | Ask user for CDE namespaces | Workflow Step 1.1 | WF-02 |
| Step 1 | Auto-detect CDE via labels (`pci-scope=cde`, `compliance/pci-dss=in-scope`, `pci-dss/scope=cde`) | Workflow Step 1.2 | WF-03 |
| Step 1 | Merge user + auto-detected (union) and confirm | Workflow Step 1.3-1.4 | WF-04 |
| Step 1 | **Branch: no CDE identified → CDE checks N/A, only cluster-wide graded** | Workflow Step 1 tail | WF-05 |
| Step 2 | Scope pillars (default all 8, or subset) and state it | Workflow Step 2 | WF-06 |
| Step 3 | Verify access; **branch: access fails → stop, do not proceed** | Workflow Step 3 | WF-07 |
| Step 4 | Discover from all three sources (kubectl / AWS API / CloudWatch) | Workflow Step 4a-4c | WF-08 |
| Step 5 | Grade PASS with cited observed evidence | Workflow Step 5 grading rules | WF-09 |
| Step 5 | Grade FAIL with cited observed evidence + severity | Workflow Step 5 grading rules | WF-10 |
| Step 5 | Grade N/A with reason (never guess) | Workflow Step 5 grading rules | WF-11 |
| Step 5 | CDE-scoped check applies ONLY to CDE namespaces | Workflow Step 5.3 | WF-12 |
| Step 6 | Finalize report + coverage gate (all check IDs present, disclaimer, crosswalk) | Workflow Step 6 / report-format Coverage Gate | WF-13 |
| Safety | Strictly read-only; refuse mutating verbs | Production safety / Non-goals | WF-14 |
| Safety | Never print Secret values (metadata only) | Production safety | WF-15 |

## C. Reference files (one E2E each)

| Reference file | Governs | Test ID |
|----------------|---------|---------|
| `references/checks.md` | Pillar→file map, ID ranges, 67 total, CDE-scope concept, read one pillar at a time | REF-01 |
| `references/pillars/namespace-isolation.md` | NS1-NS8 grading | REF-02 |
| `references/pillars/pod-security.md` | PS1-PS12 grading (privileged/hostPath = Critical) | REF-03 |
| `references/pillars/scheduling-isolation.md` | SI1-SI5 taints/tolerations/affinity | REF-04 |
| `references/pillars/network-segmentation.md` | NET1-NET9 default-deny etc. | REF-05 |
| `references/pillars/storage-isolation.md` | ST1-ST6 encryption; EBS-KMS-alone caveat | REF-06 |
| `references/pillars/iam-isolation.md` | IAM1-IAM9 IRSA/least-privilege/MFA | REF-07 |
| `references/pillars/logging-monitoring.md` | LOG1-LOG10 control-plane logs/retention | REF-08 |
| `references/pillars/vulnerability-management.md` | VUL1-VUL8 ECR/Inspector/pinned tags | REF-09 |
| `references/report-format.md` | Artifact structure, severity model, finding block, coverage gate | REF-10 |
| `references/pci-dss-mapping.md` | Requirement crosswalk + roll-up logic (Supported/Gap/Not assessed) | REF-11 |

---

## Mutating vs read-only test policy

Per intake guidance, "mutating test cases MUST interact with a real AWS account."
This Skill is strictly read-only, so no test mutates AWS. Tests tagged
`live: true` still exercise a real AWS account and a real EKS cluster
(read-only) to validate discovery and grading against actual resources.
Tests tagged `live: false` are offline routing/behavior checks that need no
cloud access.

| Group | live? | Why |
|-------|-------|-----|
| SEL-* | false | Routing/selection is a text-only decision |
| WF-01,02,04,05,06,14,15 | false | Prompt/branch behavior; no cloud needed |
| WF-03,07,08,09,10,11,12,13 | true | Require real cluster + AWS reads to exercise discovery/grading |
| REF-01,10,11 | false | Structure/index behavior |
| REF-02..09 | true | Per-pillar grading against a real cluster |
