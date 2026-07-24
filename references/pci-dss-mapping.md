# PCI DSS v4.0 Requirement Coverage Crosswalk

This document maps PCI DSS v4.0 requirements to the specific checks in this skill that validate them. Use this for the report's §7 PCI DSS Requirement Coverage section.

## Requirement 1: Install and Maintain Network Security Controls

| Sub-Requirement | Description | Covered By |
|----------------|-------------|------------|
| 1.3.2 | Restrict inbound/outbound traffic to CDE | NET1, NET2, NET3, NET6, NET8 |
| 1.4.1 | NSCs between trusted and untrusted networks | NET1, NET5, NS1, NS7 |
| 1.4.2 | Inbound traffic from untrusted to CDE restricted | NET2 |
| 1.4.4 | Outbound traffic from CDE restricted | NET3, NET9 |

## Requirement 2: Apply Secure Configurations to All System Components

| Sub-Requirement | Description | Covered By |
|----------------|-------------|------------|
| 2.2 | System components configured securely | PS1, PS3, PS4, PS5, PS6, NET4, VUL4 |
| 2.2.1 | Single purpose, resource limits | NS4, NS5, PS1 |
| 2.2.3 | Primary functions with different security levels separated | PS7, SI1, SI2, SI5 |
| 2.2.6 | Security parameters prevent misuse | NS8, PS8, PS9, PS10, PS11, SI3, SI4 |

## Requirement 3: Protect Stored Account Data

| Sub-Requirement | Description | Covered By |
|----------------|-------------|------------|
| 3.5.1.2 | Render PAN unreadable with strong cryptography | ST1, ST2, ST3, ST4, ST5, ST6 |

## Requirement 6: Develop and Maintain Secure Systems and Software

| Sub-Requirement | Description | Covered By |
|----------------|-------------|------------|
| 6.2.3 | Continuous vulnerability scanning | VUL1, VUL2, VUL5 |
| 6.2.4 | Vulnerability scanning tools | VUL2 |
| 6.3.1 | Identify and rank security vulnerabilities | VUL3, VUL6, VUL8 |
| 6.3.3 | Critical patches within one month | VUL7 |

## Requirement 7: Restrict Access to System Components and Cardholder Data

| Sub-Requirement | Description | Covered By |
|----------------|-------------|------------|
| 7.2.5 | Least privilege access | NS2, NS3, NS6, IAM1, IAM2, IAM3, IAM4, IAM7, IAM9 |
| 7.3.3 | Default deny-all access control | IAM6 |

## Requirement 8: Identify Users and Authenticate Access

| Sub-Requirement | Description | Covered By |
|----------------|-------------|------------|
| 8 (general) | Identify and authenticate all access | IAM5, IAM8 |

## Requirement 10: Log and Monitor All Access

| Sub-Requirement | Description | Covered By |
|----------------|-------------|------------|
| 10.2.1 | Audit log captures user access/admin actions | LOG1, LOG2, LOG4, NET7 |
| 10.2.2 | Audit log includes event details | LOG3, LOG6 |
| 10.3.1 | Read-only access to audit logs | LOG9 |
| 10.3.2 | Audit logs protected from modification | LOG9 |
| 10.3.3 | Audit log history available | LOG5 |
| 10.3.4 | Audit log stored securely | LOG5 |
| 10.4 | Audit logs reviewed for anomalies | PS2, PS12, LOG8, LOG10 |

## Requirement 11: Test Security of Systems and Networks Regularly

| Sub-Requirement | Description | Covered By |
|----------------|-------------|------------|
| 11.5.1 | Intrusion detection/prevention | PS12, LOG7 |
| 11.5.2 | Change detection mechanism | PS1 (PSA enforce prevents unauthorized changes) |

## Requirements NOT Covered by This Skill

The following PCI DSS requirements are **out of scope** for this EKS infrastructure review:

| Requirement | Reason |
|-------------|--------|
| Req 3 (beyond 3.5.1.2) | Application-level PAN tokenization/masking — not infrastructure |
| Req 4 | Protect cardholder data in transit over open networks — application-level TLS |
| Req 5 | Protect systems from malware — covered partially by VUL4 (hardened OS) |
| Req 9 | Restrict physical access — AWS responsibility in shared responsibility model |
| Req 12 | Information security policy — organizational policy, not infrastructure |

## Usage

When producing the report's §7 PCI DSS Requirement Coverage section:
1. List each PCI DSS requirement from this crosswalk
2. For each, show the check IDs that cover it
3. Roll up the results: if ALL covering checks PASS → requirement "Supported"; if ANY FAIL → "Gap identified"; if ALL N/A → "Not assessed"
