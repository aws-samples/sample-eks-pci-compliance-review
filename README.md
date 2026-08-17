# aws-eks-pci-compliance-review

A Kiro skill that performs a read-only PCI DSS v4.0 readiness assessment of Amazon EKS cluster infrastructure.

## Overview

This skill performs a structured, read-only assessment of an EKS cluster against 67 checks across 8 architecture areas derived from the AWS blog post [Building PCI DSS-Compliant Architectures on Amazon EKS](https://aws.amazon.com/blogs/containers/building-pci-dss-compliant-architectures-on-amazon-eks/).

## Features

- **CDE-aware scoping** Differentiates between Cardholder Data Environment (CDE) namespaces and non-CDE namespaces, applying stricter checks to CDE workloads
- **8 architecture pillars** Namespace Isolation, Pod Security, Scheduling, Network Segmentation, Storage Isolation, IAM, Logging/Monitoring, Vulnerability Management
- **PCI DSS v4.0 mapping** Every check maps to specific PCI DSS requirements
- **Scope-configurable** Run all 8 pillars or select specific areas
- **Full findings report** Scorecard + detailed finding blocks with PCI-specific remediation
- **Read-only** No cluster mutations; kubectl get/describe and AWS CLI describe/list/get only. The skill does not retrieve pod logs, Secret objects, or Secret values.

## Usage

Tell Kiro:
- "Run a PCI DSS compliance review on my EKS cluster"
- "Validate my EKS cluster for PCI compliance"
- "Check if my CDE namespaces meet PCI DSS requirements"

## Check Summary

| Pillar | Checks | PCI DSS Requirements |
|--------|--------|---------------------|
| Namespace Isolation | NS1-NS8 (8) | Req 1.4, 2.2.1, 7.2.5 |
| Pod Security Controls | PS1-PS12 (12) | Req 2.2, 10.4, 11.5 |
| Scheduling & Node Isolation | SI1-SI5 (5) | Req 2.2.3, 2.2.6 |
| Network Segmentation | NET1-NET9 (9) | Req 1.3, 1.4, 2.2 |
| Storage Isolation | ST1-ST6 (6) | Req 3.5.1.2 |
| IAM Isolation | IAM1-IAM9 (9) | Req 7, 8 |
| Logging & Monitoring | LOG1-LOG10 (10) | Req 10, 11.5.1 |
| Vulnerability Management | VUL1-VUL8 (8) | Req 2.2, 6.2, 6.3 |
| **Total** | **67 checks** | |

## Prerequisites

- kubectl access to the target EKS cluster (read-only)
- AWS CLI configured with read-only IAM permissions
- CloudWatch access for logging/monitoring validation

## Disclaimer

This skill provides directional guidance and does not constitute a formal PCI DSS assessment. A Qualified Security Assessor (QSA) must conduct the official assessment.
