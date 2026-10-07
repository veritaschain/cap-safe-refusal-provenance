# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue in CAP-SRP, please report it responsibly.

### How to Report

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please send an email to:

📧 **security@veritaschain.org**

### What to Include

Please include the following information in your report:

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Any suggested fixes (optional)

### Response Timeline

| Stage | Timeline |
|-------|----------|
| Initial acknowledgment | Within 48 hours |
| Preliminary assessment | Within 7 days |
| Resolution target | Within 30 days (severity-dependent) |

### Scope

This security policy covers:

- **In Scope:**
  - Cryptographic implementation flaws (hash chain, signatures)
  - Event integrity bypass vulnerabilities
  - Evidence pack tampering vectors
  - Key management weaknesses

- **Out of Scope (PoC Limitations):**
  - Production key management (this is a PoC)
  - Denial of service attacks
  - Issues in third-party dependencies (report upstream)

### Recognition

We appreciate responsible disclosure and will acknowledge security researchers in our release notes (with permission).

### Important Note

> **This is a Proof-of-Concept implementation.**
> 
> It is designed to demonstrate cryptographic audit trail concepts, not for production deployment without significant hardening. Production implementations should undergo independent security audits.

## Security Design Principles

CAP-SRP is built on the following security principles:

1. **Tamper Evidence**: Hash chains detect local inconsistency; independent commitments are needed to detect a producer rewriting an entire history
2. **Non-Repudiation**: Ed25519 signatures bind events to issuers
3. **Privacy by Design**: Prompt fields store hashes; hashes can remain linkable and metadata requires review
4. **Verifiability**: Independent verification requires authenticated keys/commitments; standalone pack verification is not implemented

## Contact

- Security issues: security@veritaschain.org
- General inquiries: standards@veritaschain.org
- Website: https://veritaschain.org

---

**© 2025-2026 VeritasChain Standards Organization. All rights reserved.**
