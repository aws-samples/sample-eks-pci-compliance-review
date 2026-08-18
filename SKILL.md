---
name: aws-eks-pci-compliance-review
description: "Performs a read-only PCI DSS v4.0 readiness assessment for Amazon EKS across 8 architecture areas with CDE-aware scoping and PCI DSS requirement mapping. Produces a per-pillar PASS/FAIL/N/A scorecard with prioritized PCI-specific remediation. Uses kubectl, AWS CLI, and CloudWatch. Triggers on EKS PCI review, EKS PCI DSS compliance, PCI compliance review for EKS, validate EKS PCI, EKS cardholder data environment review, EKS PCI audit, and PCI DSS EKS assessment."
---

# EKS PCI DSS Compliance Review — Kiro Skill

## What this skill is

A structured, read-only assessment of an Amazon EKS cluster against PCI DSS v4.0 compliance
guidelines, based on the AWS blog post
[Building PCI DSS-Compliant Architectures on Amazon EKS](https://aws.amazon.com/blogs/containers/building-pci-dss-compliant-architectures-on-amazon-eks/).

The skill evaluates **73 checks** across **8 architecture areas** (pillars), differentiating
between **Cardholder Data Environment (CDE)** namespaces and non-CDE namespaces. Each check
maps to specific PCI DSS v4.0 requirements and provides PCI-specific remediation guidance.

> **Disclaimer**: This review provides directional guidance based on the referenced AWS blog
> post and PCI DSS v4.0. It does **not** constitute legal or compliance advice, nor does it
> replace a formal PCI DSS assessment by a Qualified Security Assessor (QSA). Customers remain
> responsible for their own independent compliance assessment.

## When to use

- "Run a PCI DSS compliance review on my EKS cluster"
- "Validate my EKS cluster for PCI compliance"
- "Check if my CDE namespaces meet PCI DSS requirements"
- "EKS PCI audit before QSA assessment"
- "Which PCI DSS controls are missing on my EKS cluster?"
- Pre-audit readiness checks for payment card processing workloads on EKS

## When NOT to use

- **General EKS best practices review** — use `aws-eks-operations-review` (covers 9 pillars, 288 checks beyond PCI)
- **Quick health check** — use `aws-eks-healthdashboard` for point-in-time cluster health
- **Non-EKS PCI assessment** — this skill is EKS-specific; other services need separate assessments
- **Formal PCI DSS certification** — this is guidance, not a QSA assessment
- **Active incident investigation** — use incident-triage skills
- **Cluster mutations** — this skill is strictly read-only

## Inputs

| Input | Required? | Description |
|-------|-----------|-------------|
| Cluster name / context | Yes | EKS cluster to review |
| CDE namespaces | Yes (asked at start) | Namespaces containing cardholder data workloads |
| Pillars to grade | No | Specific pillars to validate (default: all 8) |
| Region / Account | No | If not obvious from context |

## Required access (read-only)

### kubectl access
- `kubectl get` / `kubectl describe` on: namespaces, pods, daemonsets, services, networkpolicies,
  clusternetworkpolicies, rolebindings, clusterrolebindings, serviceaccounts, resourcequotas,
  limitranges, persistentvolumeclaims, persistentvolumes, storageclasses, nodes,
  validatingwebhookconfigurations, and installed policy custom resources such as Kyverno
  `clusterpolicies`
- Do not retrieve or list Secret objects. Derive Secret usage from workload references or use a
  metadata-only API where available; never retrieve `.data` values.
- Do not retrieve pod logs or run mutating or interactive commands (`apply`, `delete`, `patch`,
  `exec`, etc.).

### AWS CLI access (read-only)
- `eks describe-cluster`, `eks list-access-entries`, `eks list-associated-access-policies`,
  `eks list-addons`, `eks describe-addon`
- `ec2 describe-volumes`, `ec2 describe-flow-logs`, `ec2 describe-vpc-endpoints`
- `iam list-role-policies`, `iam get-role-policy`, `iam list-attached-role-policies`, `iam get-policy`,
  `iam get-policy-version`, `iam list-mfa-devices`, `iam list-access-keys`
- `ecr describe-repositories`, `inspector2 list-coverage`, `inspector2 list-findings`
- `guardduty list-detectors`, `guardduty get-detector`
- `securityhub describe-hub`
- `logs describe-log-groups`, `logs describe-resource-policies`
- `cloudwatch describe-alarms`, `cloudwatch list-metrics`
- `cloudtrail describe-trails`, `cloudtrail get-trail-status`
- `network-firewall list-firewalls`, `network-firewall describe-firewall`
- `backup list-backup-vaults`, `backup describe-backup-vault`
- `accessanalyzer list-findings`

## Production safety

- **Strictly read-only.** No kubectl mutating verbs or destructive AWS CLI calls.
- **Sequential calls** on large clusters to avoid API server pressure.
- **Never retrieve Secret objects or values.** Derive Secret usage from workload references or use a metadata-only API where available.
- **Never retrieve pod logs or application payloads.** This review assesses configuration and control-plane logging configuration only.
- Remediations are recommendations for human approval, not applied by the skill.

## Workflow

### Step 0 — Confirm cluster identity

Before anything else, confirm which EKS cluster to review:
- Ask for cluster name, region, and account ID (if not already known)
- Confirm the kubectl context points at the correct cluster
- State the environment (production vs non-production)

### Step 1 — Identify CDE scope

Determine which namespaces are in PCI DSS scope:

1. **Ask the user**: "Which namespaces contain cardholder data workloads (CDE)?"
2. **Auto-detect**: Scan for namespaces with labels:
   - `pci-scope=cde`
   - `compliance/pci-dss=in-scope`
   - `pci-dss/scope=cde`
3. **Merge**: Combine user-specified and auto-detected namespaces (union)
4. **Confirm**: Present the combined CDE scope to the user for confirmation

If no CDE namespaces are identified, inform the user that CDE-specific checks will all be N/A
and only cluster-wide checks will be graded.

### Step 2 — Confirm review scope

Confirm which pillars to grade:
- Default: all 8 pillars
- User may scope to specific pillars (e.g., "just network and pod security")
- State the confirmed scope before proceeding

### Step 3 — Verify cluster access

Run lightweight commands to confirm connectivity:
```bash
kubectl version --short
kubectl get nodes
kubectl auth can-i get pods --all-namespaces
```

If access fails, report the specific error and stop. Do not proceed with partial access.

### Step 4 — Discover cluster state

Collect data from all three sources:

**4a. kubectl discovery:**
- Namespaces (labels, annotations)
- Pod security: PSA labels, securityContext across all pods in CDE namespaces
- RBAC: RoleBindings, ClusterRoleBindings, ServiceAccounts
- Network: NetworkPolicies, ClusterNetworkPolicies, Services, Ingresses
- Storage: PVCs, PVs, StorageClasses
- Nodes: labels, taints, OS image, kubelet version
- Workloads: DaemonSets (Fluent Bit, Falco), policy-engine pods (Gatekeeper/Kyverno/Kubewarden)
- Webhooks: ValidatingWebhookConfigurations

**4b. AWS API discovery:**
- EKS: cluster config (logging, encryption, access entries)
- IAM: role policies for service accounts, MFA devices, access keys
- EC2: EBS volume encryption, VPC flow logs, VPC endpoints
- ECR: repository scan settings
- GuardDuty: detector status, EKS runtime monitoring
- Inspector: container coverage
- Network Firewall: firewall config
- Security Hub: hub status

**4c. CloudWatch discovery:**
- Log groups: retention policies, control plane log types
- Metrics: Container Insights namespace presence
- Alarms: security-related alarms
- CloudTrail: trail configuration

### Step 5 — Grade each selected pillar

For each pillar in the confirmed scope:
1. Load the pillar file from [`references/pillars/`](references/pillars/)
2. Grade every check against the discovered cluster state
3. For CDE-scoped checks: apply only to confirmed CDE namespaces
4. For cluster-scoped checks: apply cluster-wide
5. Record PASS / FAIL / N/A with evidence for each check
6. Write the pillar's scorecard to the report artifact immediately

**Grading rules:**
- **PASS**: Evidence confirms the control is in place
- **FAIL**: Evidence shows the control is missing or misconfigured
- **N/A**: Cannot be evaluated (access denied, not applicable, CDE empty)
- Every PASS/FAIL must cite the actual observed value
- Never guess — if data cannot be collected, mark N/A with the reason

### Step 6 — Finalize the report

Write the complete report artifact per [`references/report-format.md`](references/report-format.md):
1. Executive summary with PCI readiness posture
2. PCI DSS disclaimer
3. Prioritized action plan (all FAILs, Critical → Low)
4. Detailed findings (per-FAIL block with PCI DSS mapping)
5. Per-pillar scorecards
6. What was not assessed
7. PCI DSS requirement coverage crosswalk

Output: `eks-pci-review-{cluster}-{date}.md`

## Reference files

| File | Read it when |
|------|--------------|
| [`references/checks.md`](references/checks.md) | Start of review — check index with pillar→file map, ID ranges, counts |
| [`references/pillars/namespace-isolation.md`](references/pillars/namespace-isolation.md) | Grading NS1-NS9 |
| [`references/pillars/pod-security.md`](references/pillars/pod-security.md) | Grading PS1-PS14 |
| [`references/pillars/scheduling-isolation.md`](references/pillars/scheduling-isolation.md) | Grading SI1-SI5 |
| [`references/pillars/network-segmentation.md`](references/pillars/network-segmentation.md) | Grading NET1-NET11 |
| [`references/pillars/storage-isolation.md`](references/pillars/storage-isolation.md) | Grading ST1-ST7 |
| [`references/pillars/iam-isolation.md`](references/pillars/iam-isolation.md) | Grading IAM1-IAM9 |
| [`references/pillars/logging-monitoring.md`](references/pillars/logging-monitoring.md) | Grading LOG1-LOG10 |
| [`references/pillars/vulnerability-management.md`](references/pillars/vulnerability-management.md) | Grading VUL1-VUL8 |
| [`references/report-format.md`](references/report-format.md) | Writing the report — structure, severity model, finding format |
| [`references/pci-dss-mapping.md`](references/pci-dss-mapping.md) | PCI DSS requirement crosswalk — which checks cover which requirements |

## Output

A Markdown readiness report (`eks-pci-review-{cluster}-{date}.md`) containing:
- Executive summary with PCI readiness posture
- Per-pillar scorecards (all 73 checks with PASS/FAIL/N/A + evidence)
- Detailed finding blocks for each FAIL (PCI DSS requirement, impact, remediation, AWS links)
- Prioritized action plan ordered by severity
- PCI DSS requirement coverage crosswalk

## Non-goals

- **No writes.** Strictly read-only. Remediations are recommendations, not applied.
- **No formal certification.** This is guidance, not a QSA assessment.
- **No continuous monitoring.** Point-in-time review; for ongoing monitoring use CloudWatch alarms and GuardDuty.
- **No non-EKS PCI scope.** Only assesses EKS cluster configuration, not application-level PCI controls (e.g., PAN tokenization, payment gateway integration).

## Source attribution

- [Building PCI DSS-Compliant Architectures on Amazon EKS](https://aws.amazon.com/blogs/containers/building-pci-dss-compliant-architectures-on-amazon-eks/)
- [PCI DSS v4.0 on AWS Compliance Guide](https://docs.aws.amazon.com/whitepapers/latest/pci-dss-scoping-on-aws/pci-dss-scoping-on-aws.html)
- [Architecting with EKS for PCI Compliance](https://docs.aws.amazon.com/eks/latest/best-practices/)
- [EKS Best Practices Guides](https://docs.aws.amazon.com/eks/latest/best-practices/)
