# Enterprise Identity & Access Management (IAM) Policy

- **Doc ID:** `KB-IAM-101`
- **Canonical URL:** `https://kb.enterprise.internal/iam/production-access`
- **Classification:** Enterprise Confidential / Tier-1 IT Policy

## 1. Production Database & Cloud Access
1. Production database access requests (PostgreSQL, RDS, Snowflake, Redis) require explicit dual-approval from the Engineering Director and Data Security Officer.
2. Temporary elevation (break-glass) access is granted for a maximum window of 4 hours via Okta Privileged Access Management.
3. High-privilege access requests must never be auto-approved by AI triage models and require human ticket assignment to Security Operations.

## 2. Password & Credential Resets
1. Active Directory (AD) and LDAP passwords can be self-reset via the Okta Self-Service Portal if phone-based MFA is enabled.
2. If MFA hardware token is lost, the employee must perform a live video identity verification with the IT Helpdesk desk.
