# CAP-SRP: Safe Refusal Provenance PoC

**Proving that harmful AI generations *never happened* — with cryptographic evidence.**

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![VAP Compatible](https://img.shields.io/badge/VAP-v1.1-green.svg)](https://veritaschain.org)

---
## Related Specifications

- **CAP Specification (Canonical Reference)**  
  The formal specification for CAP (Content / Creative AI Profile), defining the normative data model, event taxonomy, and cryptographic requirements.  
  👉 https://github.com/veritaschain/cap-spec
---

## PoC Definition

> **This PoC produces a verifiable evidence pack proving that a generation request was received AND refused.**
>
> **It does NOT contain unsafe prompts or generated NSFW outputs.**
>
> **Any third party can verify integrity and completeness using hash-chain + Ed25519 signatures (+ optional Merkle anchor).**

---

## The Problem: Grok's "Black Hole" of Non-Generation

In December 2025–January 2026, xAI's Grok generated **6,700+ non-consensual sexual images per hour**, including images of minors. Regulators worldwide launched investigations.

But here's the deeper problem that no one talks about:

| Current AI Systems | With SRP |
|-------------------|----------|
| Generated content → Logged | Generated content → Logged |
| **Refused content → No record** | **Refused content → Cryptographically proven** |

When regulators ask "Prove your safeguards worked," current systems cannot answer. The refusals simply vanish.

**SRP fixes this by recording every refusal as a verifiable, tamper-evident event.**

---

## What This PoC Demonstrates

### ✅ What It Proves

1. **Generation attempts are recorded** (`GEN_ATTEMPT` event)
2. **Refusals are cryptographically logged** (`GEN_DENY` event)
3. **The chain is tamper-evident** (hash linking + signatures)
4. **Completeness is verifiable** (every ATTEMPT has a corresponding outcome)
5. **Third parties can audit** (Evidence Pack with verification instructions)

### ❌ What It Does NOT Include

- Actual unsafe prompts (only hashes)
- Generated NSFW images
- Real personal data
- Production-grade key management

**Zero controversy risk by design.**

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/veritaschain/cap-srp-poc.git
cd cap-srp-poc

# Install dependencies (optional: PyNaCl for signatures)
pip install -r requirements.txt

# Run the demo
python examples/demo_scenarios.py

# Run tests
python tests/test_srp.py
```

---

## Event Model: ATTEMPT → OUTCOME

The key insight for audit defensibility: **every generation attempt MUST have a recorded outcome**.

```
┌─────────────────────────────────────────────────────────────────┐
│                     SRP Event Flow                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Request                                                   │
│      │                                                          │
│      ▼                                                          │
│  ┌───────────────────┐                                         │
│  │   GEN_ATTEMPT     │  ← Always recorded first                │
│  │   (promptHash,    │                                         │
│  │    policyId,      │                                         │
│  │    modelVersion)  │                                         │
│  └─────────┬─────────┘                                         │
│            │                                                    │
│            ▼                                                    │
│  ┌───────────────────┐                                         │
│  │  Risk Assessment  │                                         │
│  └─────────┬─────────┘                                         │
│            │                                                    │
│            ├──────────────────┐                                │
│            │                  │                                 │
│            ▼                  ▼                                 │
│     Risk < Threshold    Risk >= Threshold                      │
│            │                  │                                 │
│            ▼                  ▼                                 │
│       ┌────────┐        ┌─────────┐                           │
│       │  GEN   │        │ GEN_DENY│                           │
│       │(output)│        │(refusal)│                           │
│       └────────┘        └─────────┘                           │
│                                                                 │
│  Audit invariant: Every GEN_ATTEMPT has exactly one            │
│                   GEN or GEN_DENY following it.                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

This prevents the attack vector: "You only showed us DENYs—where are the ALLOWs you're hiding?"

---

## Core Events

### 1. GEN_ATTEMPT (Generation Request Received)

```json
{
  "eventType": "GEN_ATTEMPT",
  "eventId": "019467a1-2b3c-7def-8901-234567890abc",
  "timestamp": "2026-01-10T14:23:45.678Z",
  "promptHash": "sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
  "inputType": "image+text",
  "policyId": "cap.example.safe-refusal.v1",
  "modelVersion": "img-gen-v4.2.1",
  "sessionId": "sess-abc123",
  "previousHash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

### 2. GEN_DENY (Refusal Decision)

```json
{
  "eventType": "GEN_DENY",
  "eventId": "019467a1-2b3c-7def-8901-234567890abd",
  "timestamp": "2026-01-10T14:23:45.712Z",
  "attemptId": "019467a1-2b3c-7def-8901-234567890abc",
  "riskCategory": "CSAM_RISK",
  "riskScore": 0.97,
  "refusalReason": "Minor detected in reference image",
  "modelDecision": "DENY",
  "previousHash": "sha256:...",
  "eventHash": "sha256:...",
  "signature": "ed25519:..."
}
```

---

## Risk Categories

| Category | Description | Legal Reference |
|----------|-------------|-----------------|
| `CSAM_RISK` | Child sexual abuse material risk | 18 U.S.C. §2256 |
| `NCII_RISK` | Non-consensual intimate imagery | TAKE IT DOWN Act (2025) |
| `MINOR_SEXUALIZATION` | Sexualization of minors | EU DSA Article 35 |
| `REAL_PERSON_DEEPFAKE` | Non-consensual deepfake | EU AI Act Article 52 |
| `VIOLENCE_EXTREME` | Extreme violence/gore | Criminal codes |
| `HATE_CONTENT` | Hate speech/discrimination | DSA, national laws |

---

## Evidence Pack Structure

The PoC outputs a complete evidence package for regulatory submission:

```
evidence-pack-{chain_id}/
├── manifest.json           # Pack metadata, integrity status
├── events/
│   ├── 0001-gen_attempt.json
│   ├── 0002-gen_deny.json
│   └── ...
├── chain/
│   └── hash_chain.json     # Complete event chain
├── statistics/
│   └── refusal_stats.json  # ← MOST REVIEWED BY AUDITORS
└── verification/
    ├── merkle_root.json    # For external anchoring
    └── instructions.md     # Third-party verification guide
```

**Note for auditors:** The `statistics/refusal_stats.json` file is typically the first document reviewed in compliance audits. It provides aggregated metrics on refusal rates, categories, and chain integrity status.

---

## Third-Party Verification (2 minutes)

Anyone can verify the evidence pack:

1. **Recalculate each EventHash** from event data
2. **Verify hash chain linkage** (each `previousHash` matches prior `eventHash`)
3. **Verify signatures** (Ed25519 against public key)
4. **Check completeness** (every `GEN_ATTEMPT` has a `GEN` or `GEN_DENY`)
5. **Optional: Verify Merkle anchor** against external timestamp

```bash
# Automated verification
python src/srp_core.py --verify evidence-pack-xxx/
```

---

## Regulatory Alignment

| Regulation | Requirement | SRP Capability |
|------------|-------------|----------------|
| **EU AI Act Art. 12** | Automatic logging for high-risk AI | ✓ GEN_ATTEMPT + GEN_DENY events |
| **EU DSA Art. 35** | Risk mitigation measures | ✓ Refusal statistics with proof |
| **TAKE IT DOWN Act** | 48-hour removal proof | ✓ "Never generated" evidence |
| **CSAM Prevention** | Child protection records | ✓ CSAM_RISK category tracking |

### Compliance Note

> **This PoC demonstrates cryptographic verifiability of refusal events.**
>
> **External anchoring (blockchain/TSA) is optional in this PoC** — recommended for production deployments where long-term non-repudiation is required.
>
> **The goal is audit defensibility, not legal advice or complete regulatory compliance.** Consult legal counsel for jurisdiction-specific requirements.

---

## Implementation Notes

### Event ID Format

All event IDs use **UUID v7** (time-ordered) for:
- Natural chronological ordering
- Distributed generation without coordination
- Timestamp extraction for audit trails

### Policy ID Format

Policy IDs in this PoC use reverse-domain notation:
```
cap.example.safe-refusal.v1
cap.veritaschain.child-safety.v2.3
```

> **Note:** The format shown here is illustrative. Production implementations may use different conventions (e.g., `POL-CATEGORY-vX.Y`). The specification is intentionally flexible on this point.

### Prompt Privacy

**Original prompts are NEVER stored.** Only SHA-256 hashes are recorded, enabling:
- Verification that a specific prompt was processed
- Privacy protection (irreversible hash)
- GDPR Article 17 compliance (no personal data in logs)

---

## The Message

> **We don't just block harmful generations.**
> **We prove that they never happened.**

Current AI safety is trust-based: "We have filters. Trust us."

SRP is verification-based: "We have filters. Here's the cryptographic proof they worked."

**Verify, Don't Trust.**

---

## Repository Structure

```
cap-srp-poc/
├── README.md                 # This file
├── Cap-srp-world-first-evidence-report.md  # Prior art assessment
├── SECURITY.md               # Security policy
├── spec/
│   └── CAP-SRP-Extension.md  # Formal specification
├── src/
│   ├── __init__.py
│   └── srp_core.py           # Core implementation
├── examples/
│   └── demo_scenarios.py     # Grok-scenario demonstrations
├── tests/
│   └── test_srp.py           # Test suite (20+ tests)
├── requirements.txt
├── LICENSE                   # CC BY 4.0
└── CONTRIBUTING.md
```

---

## License

CC BY 4.0 International

---

## Contact

- **Website**: https://veritaschain.org
- **Email**: standards@veritaschain.org
- **GitHub**: https://github.com/veritaschain
- **Specification**: [CAP-SRP Extension](spec/CAP-SRP-Extension.md)

---

## Related Documents

- [VAP Framework Specification v1.1](https://github.com/veritaschain/vap-spec)
- [CAP Basic Specification v0.1](https://github.com/veritaschain/cap-spec)
- [VCP Protocol Specification v1.1](https://github.com/veritaschain/vcp-spec)

---

**© 2025-2026 VeritasChain Standards Organization. All rights reserved.**
