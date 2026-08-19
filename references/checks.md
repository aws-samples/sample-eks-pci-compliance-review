# EKS PCI DSS Compliance Review — Checks Index

Complete reference of all PCI DSS compliance checks for Amazon EKS clusters, organized by the **8 architecture areas** from the AWS blog post on building PCI DSS-compliant architectures on EKS.

Each pillar's checks live in its own file under [`pillars/`](pillars/) — read ONLY the pillar file(s) you are about to grade, one at a time.

## Key Concepts

### CDE Scope
Every check has a **CDE Scope** value that determines where it applies:
- **CDE-only**: Applies only to confirmed CDE (Cardholder Data Environment) namespaces — stricter enforcement
- **All**: Applies to all namespaces (both CDE and non-CDE)
- **Cluster**: Cluster-wide check, not namespace-scoped

### Access Limitations
When a kubectl command or AWS CLI call returns an access denied or authorization error:
- Mark the dependent check(s) as **N/A** with observation: "Unable to assess — access denied on {command}. Manual verification recommended."
- Include a dedicated "Access Limitations" section in the report
- Never silently skip checks — every check MUST have a definitive PASS, FAIL, or N/A

### PCI DSS Requirement Mapping
Every check maps to one or more PCI DSS v4.0 requirements. The full crosswalk is in [`pci-dss-mapping.md`](pci-dss-mapping.md).

---

## Pillar Files

Read each file only when running that pillar's checks:

| Pillar | File | Check IDs | Count | PCI DSS Requirements |
|--------|------|-----------|-------|---------------------|
| Namespace Isolation | [`pillars/namespace-isolation.md`](pillars/namespace-isolation.md) | NS1-NS9 | 9 | 1.4.1, 2.2.1, 7.2.5 |
| Pod Security Controls | [`pillars/pod-security.md`](pillars/pod-security.md) | PS1-PS14 | 14 | 2.2, 2.2.1, 2.2.3, 2.2.6, 10.4, 11.5.1, 11.5.2 |
| Scheduling & Node Isolation | [`pillars/scheduling-isolation.md`](pillars/scheduling-isolation.md) | SI1-SI5 | 5 | 2.2.3, 2.2.6 |
| Network Segmentation | [`pillars/network-segmentation.md`](pillars/network-segmentation.md) | NET1-NET11 | 11 | 1.3.2, 1.4.1, 1.4.2, 1.4.4, 2.2 |
| Storage Isolation | [`pillars/storage-isolation.md`](pillars/storage-isolation.md) | ST1-ST7 | 7 | 3.5.1.2 |
| IAM Isolation | [`pillars/iam-isolation.md`](pillars/iam-isolation.md) | IAM1-IAM9 | 9 | 7.2.5, 7.3.3, 8 |
| Logging, Monitoring & Audit | [`pillars/logging-monitoring.md`](pillars/logging-monitoring.md) | LOG1-LOG10 | 10 | 10.2.1, 10.2.2, 10.3.1-10.3.4, 10.4, 11.5.1 |
| Vulnerability Management | [`pillars/vulnerability-management.md`](pillars/vulnerability-management.md) | VUL1-VUL8 | 8 | 2.2, 6.2.3, 6.2.4, 6.3.1, 6.3.3 |

**Total baseline checks: 73**

---

## Summary

| Pillar | Check IDs | Focus |
|--------|-----------|-------|
| Namespace Isolation | NS1-NS9 | Dedicated namespaces, RBAC scoping, resource quotas, policy enforcement, SA token automounting |
| Pod Security Controls | PS1-PS14 | PSA enforcement, securityContext hardening, host restrictions, capability dropping, runtime monitoring |
| Scheduling & Node Isolation | SI1-SI5 | Taints/tolerations, node affinity, dedicated CDE node groups |
| Network Segmentation | NET1-NET11 | Default-deny policies, TLS, admin/application policies, endpoint privacy, VPC-level controls |
| Storage Isolation | ST1-ST7 | KMS encryption, secrets envelope encryption, per-tenant PVCs, CSI encryption in transit |
| IAM Isolation | IAM1-IAM9 | IRSA/Pod Identity, least privilege, MFA, access entries |
| Logging & Monitoring | LOG1-LOG10 | Control plane logs, CloudTrail, log retention, GuardDuty, Security Hub |
| Vulnerability Management | VUL1-VUL8 | ECR scanning, Inspector, image provenance, node hardening, patching |

## Context Management

Do NOT read all 8 pillar files at once. Read this index first, then read each `pillars/<pillar>.md` file only when you are about to run that pillar's checks. After grading a pillar, write findings to the artifact before moving to the next pillar file.
