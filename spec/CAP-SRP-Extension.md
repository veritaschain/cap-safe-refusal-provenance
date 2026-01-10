# CAP-SRP: Safe Refusal Provenance Extension

## Extension Specification v0.2

**Document ID:** VSO-CAP-SRP-EXT-001  
**Status:** Draft Specification  
**Version:** 0.2.0  
**Date:** 2026-01-10  
**Maintainer:** VeritasChain Standards Organization (VSO)  
**License:** CC BY 4.0 International  
**Base Specification:** CAP Basic Specification v0.1

---

## Executive Summary

**SRP (Safe Refusal Provenance)** extends CAP (Content / Creative AI Profile) to provide cryptographic evidence of AI content moderation decisions—specifically, proof that harmful generation requests were **received, evaluated, and refused**.

### PoC Definition

> **This specification defines events that prove a generation request was received AND refused.**
>
> **The resulting evidence pack contains no unsafe prompts or NSFW outputs.**
>
> **Any third party can verify integrity and completeness using hash-chain + signatures.**

### The Core Problem

Current AI systems have a fundamental audit gap:

| Event Type | Current Systems | With SRP |
|------------|-----------------|----------|
| Generation allowed | ✓ Logged | ✓ Logged |
| Generation refused | ✗ No record | ✓ Cryptographically proven |

When regulators ask "Prove your safeguards worked," existing systems cannot answer. SRP closes this gap.

---

## 1. Introduction

### 1.1 Background

The December 2025–January 2026 Grok incident exposed a critical weakness in AI content moderation: **there is no standard way to prove that dangerous content was NOT generated**.

xAI claimed to have safeguards, but could not provide:
- Evidence that specific requests were refused
- Proof that refusal logs weren't tampered with
- Verification that "all" dangerous requests were blocked (not selectively logged)

### 1.2 Solution

SRP introduces two key event types:

1. **GEN_ATTEMPT** — Records that a generation request was received
2. **GEN_DENY** — Records that the request was refused (with reason)

The critical audit invariant:
> **Every GEN_ATTEMPT MUST have exactly one corresponding GEN or GEN_DENY event.**

This prevents selective logging attacks where operators only show favorable outcomes.

### 1.3 Conformance Language

Keywords per RFC 2119:
- **MUST** / **SHALL**: Absolute requirement
- **SHOULD** / **RECOMMENDED**: Recommended with valid exceptions
- **MAY** / **OPTIONAL**: Truly optional

---

## 2. Event Model

### 2.1 Event Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     SRP Event Lifecycle                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Request Received                                               │
│       │                                                         │
│       ▼                                                         │
│  ┌─────────────────┐                                           │
│  │  GEN_ATTEMPT    │ ← MUST be recorded for every request      │
│  └────────┬────────┘                                           │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                           │
│  │ Risk Assessment │                                           │
│  │ ├─ CSAM check   │                                           │
│  │ ├─ NCII check   │                                           │
│  │ ├─ Violence     │                                           │
│  │ └─ Policy match │                                           │
│  └────────┬────────┘                                           │
│           │                                                     │
│           ├─────────────────────┐                              │
│           │                     │                               │
│           ▼                     ▼                               │
│    Risk < Threshold      Risk >= Threshold                     │
│           │                     │                               │
│           ▼                     ▼                               │
│      ┌─────────┐          ┌─────────┐                         │
│      │   GEN   │          │ GEN_DENY│                         │
│      │ (allow) │          │ (refuse)│                         │
│      └─────────┘          └─────────┘                         │
│                                                                 │
│  INVARIANT: count(GEN_ATTEMPT) == count(GEN) + count(GEN_DENY) │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Event Type Registry

| Code | Event Type | Phase | Description |
|------|------------|-------|-------------|
| 0x0400 | `GEN_ATTEMPT` | Pre-generation | Generation request received |
| 0x0401 | `GEN_DENY` | Decision | Generation refused |
| 0x0402 | `GEN_WARN` | Decision | Allowed with warning |
| 0x0403 | `GEN_ESCALATE` | Decision | Escalated to human review |
| 0x0404 | `GEN_QUARANTINE` | Decision | Generated but quarantined |
| 0x0410 | `GEN` | Output | Generation completed |

### 2.3 Event Linking

GEN_DENY (and other outcome events) MUST include an `attemptId` field referencing the corresponding GEN_ATTEMPT:

```
GEN_ATTEMPT (id: "abc-123")
     │
     └──► GEN_DENY (attemptId: "abc-123")
```

---

## 3. Data Model

### 3.1 GEN_ATTEMPT Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://veritaschain.org/schemas/cap/srp/gen-attempt.json",
  "title": "CAP-SRP GEN_ATTEMPT Event",
  "type": "object",
  "required": [
    "eventType",
    "eventId",
    "timestamp",
    "promptHash",
    "policyId",
    "modelVersion",
    "previousHash"
  ],
  "properties": {
    "eventType": {
      "const": "GEN_ATTEMPT",
      "description": "Event type identifier"
    },
    "eventId": {
      "type": "string",
      "format": "uuid",
      "description": "UUID v7 (time-ordered) for this event"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 with millisecond precision"
    },
    "promptHash": {
      "type": "string",
      "pattern": "^sha256:[a-f0-9]{64}$",
      "description": "SHA-256 hash of input prompt (privacy-preserving)"
    },
    "referenceImageHash": {
      "type": "string",
      "pattern": "^sha256:[a-f0-9]{64}$",
      "description": "SHA-256 hash of reference image if provided (OPTIONAL)"
    },
    "inputType": {
      "type": "string",
      "enum": ["text", "image", "text+image", "video", "audio"],
      "description": "Type of input provided"
    },
    "policyId": {
      "type": "string",
      "description": "Policy identifier governing this request"
    },
    "modelVersion": {
      "type": "string",
      "description": "Model identifier and version"
    },
    "sessionId": {
      "type": "string",
      "format": "uuid",
      "description": "Session identifier for correlation (OPTIONAL)"
    },
    "actorHash": {
      "type": "string",
      "pattern": "^sha256:[a-f0-9]{64}$",
      "description": "Anonymized hash of user/actor identifier (OPTIONAL)"
    },
    "previousHash": {
      "type": "string",
      "pattern": "^sha256:[a-f0-9]{64}$",
      "description": "Hash of previous event in chain"
    },
    "eventHash": {
      "type": "string",
      "pattern": "^sha256:[a-f0-9]{64}$",
      "description": "SHA-256 hash of this event"
    },
    "signature": {
      "type": "string",
      "pattern": "^ed25519:[a-zA-Z0-9+/=]+$",
      "description": "Ed25519 signature of eventHash"
    }
  }
}
```

### 3.2 GEN_DENY Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://veritaschain.org/schemas/cap/srp/gen-deny.json",
  "title": "CAP-SRP GEN_DENY Event",
  "type": "object",
  "required": [
    "eventType",
    "eventId",
    "timestamp",
    "attemptId",
    "riskCategory",
    "riskScore",
    "modelDecision",
    "previousHash"
  ],
  "properties": {
    "eventType": {
      "const": "GEN_DENY"
    },
    "eventId": {
      "type": "string",
      "format": "uuid",
      "description": "UUID v7 for this event"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "attemptId": {
      "type": "string",
      "format": "uuid",
      "description": "References the GEN_ATTEMPT this responds to"
    },
    "riskCategory": {
      "type": "string",
      "enum": [
        "CSAM_RISK",
        "NCII_RISK",
        "MINOR_SEXUALIZATION",
        "REAL_PERSON_DEEPFAKE",
        "VIOLENCE_EXTREME",
        "HATE_CONTENT",
        "TERRORIST_CONTENT",
        "SELF_HARM_PROMOTION",
        "OTHER"
      ]
    },
    "riskSubCategories": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Additional risk flags"
    },
    "riskScore": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "description": "Confidence score for risk assessment"
    },
    "refusalReason": {
      "type": "string",
      "maxLength": 500,
      "description": "Human-readable explanation"
    },
    "modelDecision": {
      "type": "string",
      "enum": ["DENY", "WARN", "ESCALATE", "QUARANTINE"]
    },
    "humanOverride": {
      "type": "boolean",
      "default": false,
      "description": "Whether a human overrode the model decision"
    },
    "previousHash": {
      "type": "string",
      "pattern": "^sha256:[a-f0-9]{64}$"
    },
    "eventHash": {
      "type": "string",
      "pattern": "^sha256:[a-f0-9]{64}$"
    },
    "signature": {
      "type": "string",
      "pattern": "^ed25519:[a-zA-Z0-9+/=]+$"
    }
  }
}
```

### 3.3 Risk Category Definitions

| Category | Code | Description | Legal Reference |
|----------|------|-------------|-----------------|
| `CSAM_RISK` | 0x01 | Child sexual abuse material risk | 18 U.S.C. §2256, EU 2011/93/EU |
| `NCII_RISK` | 0x02 | Non-consensual intimate imagery | TAKE IT DOWN Act (2025) |
| `MINOR_SEXUALIZATION` | 0x03 | Sexualization of minors | EU DSA Article 35 |
| `REAL_PERSON_DEEPFAKE` | 0x04 | Non-consensual deepfake of real person | EU AI Act Article 52 |
| `VIOLENCE_EXTREME` | 0x05 | Extreme violence/gore | Criminal codes |
| `HATE_CONTENT` | 0x06 | Hate speech/discrimination | EU DSA, national laws |
| `TERRORIST_CONTENT` | 0x07 | Terrorist content | EU TCO Regulation |
| `SELF_HARM_PROMOTION` | 0x08 | Self-harm promotion | Platform policies |
| `OTHER` | 0xFF | Other policy violation | Custom definition |

### 3.4 Policy ID Format

Policy identifiers in this PoC use reverse-domain notation:

```
cap.{organization}.{policy-name}.v{version}
```

Examples:
- `cap.example.safe-refusal.v1`
- `cap.veritaschain.child-safety.v2.3`

> **Implementation Note:** This format is illustrative. Production systems may use alternative conventions (e.g., `POL-CATEGORY-vX.Y` or URIs). The specification intentionally does not mandate a specific format to allow organizational flexibility.

---

## 4. Hash Chain & Integrity

### 4.1 Chain Structure

All events are linked in a single hash chain:

```
Event 0 (Genesis)
    │
    ├── previousHash: sha256:0000...0000
    ├── eventHash: sha256:a1b2...
    │
    ▼
Event 1 (GEN_ATTEMPT)
    │
    ├── previousHash: sha256:a1b2...
    ├── eventHash: sha256:c3d4...
    │
    ▼
Event 2 (GEN_DENY)
    │
    ├── previousHash: sha256:c3d4...
    ├── eventHash: sha256:e5f6...
    │
    ...
```

### 4.2 Event Hash Computation

```
1. Create event object without eventHash and signature fields
2. JSON-canonicalize per RFC 8785 (JCS)
3. Encode as UTF-8 bytes
4. Compute SHA-256
5. Prefix with "sha256:"
```

### 4.3 Signature Generation

```
1. Obtain eventHash
2. Sign with Ed25519 private key
3. Base64-encode signature
4. Prefix with "ed25519:"
```

### 4.4 External Anchoring (OPTIONAL)

For production deployments requiring long-term non-repudiation:

```json
{
  "eventType": "AUDIT_ANCHOR",
  "timestamp": "2026-01-10T24:00:00Z",
  "merkleRoot": "sha256:3a7f4e8b...",
  "anchor": {
    "type": "ethereum",
    "txHash": "0x7fe4c...",
    "blockNumber": 21504987
  }
}
```

Supported anchor types:
- `ethereum` — Ethereum mainnet transaction
- `rfc3161` — RFC 3161 Timestamp Authority
- `github_release` — GitHub release with timestamp

> **PoC Note:** External anchoring is optional in this PoC. The hash chain and signatures provide sufficient integrity for demonstration purposes. Production deployments SHOULD implement external anchoring for regulatory submissions.

---

## 5. Completeness Verification

### 5.1 The Completeness Invariant

> **For every `GEN_ATTEMPT` event, there MUST exist exactly one outcome event (`GEN`, `GEN_DENY`, `GEN_WARN`, `GEN_ESCALATE`, or `GEN_QUARANTINE`) with a matching `attemptId`.**

This prevents:
- Hiding successful generations of harmful content
- Selectively logging only refusals
- Claiming refusals that never had corresponding attempts

### 5.2 Verification Algorithm

```python
def verify_completeness(events):
    attempts = {e.eventId for e in events if e.eventType == "GEN_ATTEMPT"}
    outcomes = {e.attemptId for e in events if e.eventType in OUTCOME_TYPES}
    
    unmatched_attempts = attempts - outcomes
    orphan_outcomes = outcomes - attempts
    
    return len(unmatched_attempts) == 0 and len(orphan_outcomes) == 0
```

---

## 6. Evidence Pack Structure

### 6.1 Directory Layout

```
evidence-pack-{chain_id}/
├── manifest.json           # Pack metadata
├── events/
│   ├── 0001-gen_attempt.json
│   ├── 0002-gen_deny.json
│   └── ...
├── chain/
│   └── hash_chain.json     # Complete chain
├── statistics/
│   └── refusal_stats.json  # Aggregated metrics
└── verification/
    ├── merkle_root.json    # For external anchoring
    └── instructions.md     # Verification guide
```

### 6.2 Statistics File

The `refusal_stats.json` is typically the first document reviewed by auditors:

```json
{
  "period": {
    "start": "2026-01-01T00:00:00Z",
    "end": "2026-01-31T23:59:59Z"
  },
  "totalAttempts": 1000000,
  "totalRefusals": 2847,
  "totalAllowed": 997153,
  "refusalRate": 0.002847,
  "completenessCheck": "PASSED",
  "byCategory": {
    "CSAM_RISK": 12,
    "NCII_RISK": 1523,
    "MINOR_SEXUALIZATION": 89,
    "REAL_PERSON_DEEPFAKE": 956
  },
  "chainIntegrity": "VERIFIED"
}
```

---

## 7. Privacy Considerations

### 7.1 Prompt Hashing (REQUIRED)

Original prompts MUST NOT be stored. Only SHA-256 hashes are recorded.

```python
# ✓ Correct
prompt_hash = "sha256:" + hashlib.sha256(prompt.encode()).hexdigest()

# ✗ Prohibited
prompt_text = prompt  # Never store raw prompts
```

### 7.2 Actor Anonymization (RECOMMENDED)

If user identifiers are recorded:
- Use irreversible hashes, OR
- Apply k-anonymity (k ≥ 5), OR
- Use pseudonymization with secured key

### 7.3 GDPR Compliance

This design supports GDPR Article 17 (right to erasure):
- No personal data in event fields
- Hash-based references are not "personal data" under typical interpretation
- Deletion requests can be honored without breaking chain integrity

---

## 8. Regulatory Alignment

### 8.1 EU AI Act Article 12

| Requirement | SRP Capability |
|-------------|----------------|
| Automatic logging | GEN_ATTEMPT + outcome events |
| Lifetime retention | Hash chain with external anchoring |
| Traceability | attemptId linking |
| Human oversight records | humanOverride field |

### 8.2 EU DSA Article 35

| Requirement | SRP Capability |
|-------------|----------------|
| Risk mitigation measures | GEN_DENY as mitigation evidence |
| Audit trail | Complete event chain |
| Reporting | statistics/refusal_stats.json |

### 8.3 TAKE IT DOWN Act

| Requirement | SRP Capability |
|-------------|----------------|
| 48-hour response | Timestamp proof |
| Removal evidence | "Never generated" via GEN_DENY |
| Victim notification | Shareable evidence pack |

### 8.4 Compliance Note

> This specification demonstrates cryptographic verifiability of refusal events. External anchoring is optional in PoC implementations but RECOMMENDED for production regulatory submissions.
>
> This specification provides technical capabilities for audit defensibility. It does not constitute legal advice. Consult legal counsel for jurisdiction-specific compliance requirements.

---

## 9. Third-Party Verification

### 9.1 Verification Steps (< 2 minutes)

1. **Verify hash chain:**
   ```
   For each event[n]:
     assert event[n].previousHash == event[n-1].eventHash
   ```

2. **Verify event hashes:**
   ```
   For each event:
     computed = sha256(canonicalize(event without hash/sig))
     assert computed == event.eventHash
   ```

3. **Verify signatures (if Ed25519 key available):**
   ```
   For each event:
     assert ed25519_verify(pubkey, event.eventHash, event.signature)
   ```

4. **Verify completeness:**
   ```
   assert all GEN_ATTEMPTs have matching outcomes
   assert no orphan outcomes exist
   ```

5. **Optional: Verify external anchor:**
   ```
   assert merkle_root in anchor.reference
   ```

### 9.2 What Verification Proves

✓ Events have not been modified after creation  
✓ Events have not been deleted from the chain  
✓ Events have not been reordered  
✓ Every generation attempt has a recorded outcome  
✓ Refusals actually occurred at the claimed times  

---

## Appendix A: Example Event Sequence

### Scenario: CSAM Risk Detection and Refusal

```json
// Event 1: Generation attempt received
{
  "eventType": "GEN_ATTEMPT",
  "eventId": "019467a1-0001-7000-0000-000000000001",
  "timestamp": "2026-01-10T14:23:45.100Z",
  "promptHash": "sha256:7f83b165...",
  "inputType": "text+image",
  "policyId": "cap.example.safe-refusal.v1",
  "modelVersion": "img-gen-v4.2.1",
  "previousHash": "sha256:00000000...",
  "eventHash": "sha256:a1b2c3d4..."
}

// Event 2: Refusal decision
{
  "eventType": "GEN_DENY",
  "eventId": "019467a1-0001-7000-0000-000000000002",
  "timestamp": "2026-01-10T14:23:45.150Z",
  "attemptId": "019467a1-0001-7000-0000-000000000001",
  "riskCategory": "CSAM_RISK",
  "riskSubCategories": ["MINOR_DETECTED", "SEXUALIZED_CONTEXT"],
  "riskScore": 0.97,
  "refusalReason": "Minor detected in reference image with sexualized prompt",
  "modelDecision": "DENY",
  "humanOverride": false,
  "previousHash": "sha256:a1b2c3d4...",
  "eventHash": "sha256:e5f6g7h8..."
}
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-01-10 | VSO | Initial draft |
| 0.2.0 | 2026-01-10 | VSO | Added GEN_ATTEMPT, completeness verification, compliance notes |

---

**© 2025-2026 VeritasChain Standards Organization. All rights reserved.**

This specification is published under CC BY 4.0 International License.
