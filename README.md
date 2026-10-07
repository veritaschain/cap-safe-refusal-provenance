# CAP-SRP: Safe Refusal Provenance PoC

**Tamper-evident evidence of recorded generation attempts and reported refusals.**

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

This first-party, legacy PoC illustrates request/outcome logging and Evidence Pack export. The examples simulate decisions; they do not run or validate a model's safety filters. No generated images or real personal data are needed.

## Canonical specifications and status

**CAP means Content / Creative AI Profile**, a domain profile of the **Verifiable AI Provenance Framework (VAP)**. SRP means **Safe Refusal Provenance**.

- [CAP v1.0 — released specification](https://github.com/veritaschain/cap-spec/blob/main/docs/CAP-Specification-v1.0.md)
- [VAP v1.2 — framework specification](https://github.com/veritaschain/vap-spec/blob/main/spec/v1.2/VAP_Framework_Specification.md) (currently Draft 3)
- [CAP v1.0 / VAP v1.2 Draft 3 conformance mapping](https://github.com/veritaschain/cap-spec/blob/main/docs/conformance/CAP-v1.0-VAP-v1.2-Draft3-Conformance-Mapping.md) — **review draft**
- [Minimal change proposal](https://github.com/veritaschain/cap-spec/blob/main/docs/conformance/CAP-VAP-v1.2-Minimal-Change-Proposal.md) — **unadopted**

**Status checked 2026-10-08 JST:** the mapping is published for review, but identifies unresolved normative divergences. **CAP v1.0 conformance to VAP v1.2 has not been established.** Neither publication of the mapping nor this PoC establishes conformance or certification. CAP v1.0 remains the released CAP specification; the proposal does not amend it. This repository demonstrates selected SRP mechanisms and does not claim full CAP v1.0 or VAP v1.2 conformance.

In particular, CAP v1.0 permits optional external anchoring at Bronze, whereas VAP v1.2 INT-006 requires it at every conformance level. Signed batch scope, continuity, policy binding and data-model requirements also remain unresolved. A local hash chain, Merkle root or passing PoC test is not a substitute for those requirements.

This is a **first-party PoC**, not independent implementation evidence. The [canonical CAP implementation disclosure](https://github.com/veritaschain/cap-spec#implementation-status-mandatory-disclosure) reports zero external implementations and zero Evidence Packs accepted in proceedings as of September 2026.

## What the current implementation can and cannot verify

| Capability | Current implementation | Boundary |
| --- | --- | --- |
| Request/refusal records | `GEN_ATTEMPT` and `GEN_DENY`, linked by attempt ID; `GEN` for reported generation | Evidence of the producer's recorded statements, not proof of actual model behavior |
| Hash-chain check | `verify_chain_integrity()` recomputes event hashes and checks links | Local self-consistency; a rewritten unanchored chain can be internally consistent |
| Ed25519 signing | PyNaCl signs events when installed | Without PyNaCl signatures are disabled; the chain check does not verify signatures or authenticate the producer |
| Outcome coverage | `verify_completeness()` compares sets of attempt IDs and outcome references | **Does not count duplicate outcomes**; a PASS does not prove exactly one terminal outcome per attempt |
| Evidence Pack export | Events, chain, statistics and verification notes | No independent validation or automatic regulatory acceptance |
| External anchoring | Export is marked `NOT_ANCHORED` | No authenticated external timestamp or VAP AnchorRecord verification |
| Standalone pack verification | `--verify` is a placeholder | It prints “Standalone verification not yet implemented”; do not use it as a successful verification command |

The file named `verification/merkle_root.json` contains a **SHA-256 digest of concatenated event-hash strings**, not an RFC 6962 Merkle tree or inclusion proofs. The filename is retained for compatibility. No signing public key is exported in the pack, so independent signature verification requires separately obtained, authenticated key material and a separate verifier.

## Completeness Invariant: scope and limits

The canonical CAP relationship is:

```text
COUNT(GEN_ATTEMPT) = COUNT(GEN) + COUNT(GEN_DENY) + COUNT(GEN_ERROR)
```

For a closed set of recorded attempts, outcomes must be linked by attempt ID and checked for missing, orphan and duplicate outcomes. **Equal aggregate counts alone are insufficient.** Attempts still in progress, or outcomes crossing a time-window boundary, must be distinguished from missing terminal outcomes; a failed check does not by itself prove fraud.

**Independent completeness claims cover recorded and externally anchored requests, at anchor/batch granularity.** Hashes, signatures, full batch scope and independently authenticated commitments must be verified separately. A Merkle inclusion proof shows membership of one event, not completeness of the entire batch.

What these mechanisms cannot establish:

- **Pre-measurement drops:** a request never recorded as `GEN_ATTEMPT` leaves nothing to detect.
- **Uncommitted omissions:** removing an attempt and its outcome together can preserve the count equation. Local self-consistency does not establish a complete history without an independent commitment.
- **Truth of the underlying decision:** signed records attribute a statement to a key; they do not establish that the producer accurately described model execution or used adequate safeguards.
- **Universal non-generation or safety:** a recorded `GEN_DENY` does not prove that harmful content never existed or was never generated elsewhere. SRP records decisions after the fact; it does not itself block, filter or prevent generation.

These limits follow the canonical CAP README and VAP v1.2 §§1.6, 4.1.7 and 11.1. See the mapping for the distinction between SRP attempt/outcome checks and VAP anchored-batch completeness.

### Legacy implementation differences

The canonical CAP invariant includes `GEN_ERROR`. This legacy PoC has no `GEN_ERROR` event implementation and treats `GEN_WARN`, `GEN_ESCALATE` and `GEN_QUARANTINE` as outcomes in its set-based coverage check. Those intermediate decisions must not be assumed equivalent to canonical terminal outcomes. The current demo constructs `GEN` and `GEN_DENY` records only.

The local event model uses fields such as `eventType`, `attemptId` and `previousHash`. It is not a VAP v1.2 envelope. Documentation alignment does not change event serialization, historical signatures or released CAP requirements.

## Quick Start

```bash
git clone https://github.com/veritaschain/cap-safe-refusal-provenance.git
cd cap-safe-refusal-provenance

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Synthetic request/outcome scenarios and Evidence Pack export
python examples/demo_scenarios.py

# Existing implementation tests
python tests/test_srp.py
```

Installing `requirements.txt` enables PyNaCl signing. Running without it is hash-chain-only behavior, not signature verification. Neither the demo nor test success establishes CAP/VAP conformance.

### Local checks through the Python API

```python
from src.srp_core import SRPLogger, RiskCategory

logger = SRPLogger(model_version="demo-model", policy_id="cap.example.safe-refusal.v1")
logger.log_refusal(
    prompt="synthetic test request",
    risk_category=RiskCategory.OTHER,
    risk_score=0.9,
    refusal_reason="Synthetic policy decision for demonstration",
)
print(logger.verify_chain_integrity())  # Hashes and links only
print(logger.verify_completeness())    # Set-based outcome coverage only
```

## Evidence Pack

The demo writes packs under `output/evidence-pack-<chain_id>/`:

| Path | Content |
| --- | --- |
| `manifest.json` | Producer-generated metadata and local check results |
| `events/` | Individual serialized records |
| `chain/hash_chain.json` | Supplied event sequence |
| `statistics/refusal_stats.json` | Counts and categories derived from that sequence |
| `verification/merkle_root.json` | Legacy aggregate digest, explicitly unanchored |
| `verification/instructions.md` | Limited local checks and verification caveats |

For independent assessment, recompute hashes, check links, verify signatures against authenticated keys, check outcome multiplicity and terminality, and compare complete declared scope against authenticated external commitments. **The PoC does not automate that complete workflow.** Manifest labels and statistics are not independently verified evidence by themselves.

## Prompt privacy

Event prompt fields contain hashes rather than plaintext prompts. Hashes can still be linkable or susceptible to guessing; they do not automatically anonymize personal data or establish GDPR Article 17 compliance. Free-text reasons and other metadata also require privacy review.

## Regulatory relevance and legal scope

Refusal records may support assessment of logging, oversight and audit obligations, including EU AI Act Article 12 where applicable. They do not establish fulfillment of those obligations, content-removal duties, retention periods or GDPR erasure requirements. A timestamp is not a retention system, and hashing a prompt does not automatically anonymize personal data.

> **Legal scope (VAP v1.2 §1.6).** VAP and its domain profiles define mechanisms for producing **cryptographically verifiable evidence** of AI system decisions. Conformance to VAP or any profile: (a) does **not** constitute compliance with the EU AI Act, GDPR, MiFID II/III, CAT Rule 613, NIS2, FDA SaMD guidance, or any other law or regulation; (b) does **not** constitute a legal determination that any technical mechanism (including crypto-shredding) satisfies a specific legal obligation; (c) does **not** warrant the correctness, fairness, or safety of the underlying AI decisions — only the integrity, completeness (at anchor granularity), and attributability of their records. VAP generates evidence; competent authorities and courts evaluate it.

External anchoring is omitted in this PoC. This is an implementation limitation, not an exception to VAP v1.2's all-level anchoring requirement. Refusal records do not prove that removal or transparency obligations no longer apply.

## Historical documents and current references

- [CAP v1.0 canonical specification](https://github.com/veritaschain/cap-spec/blob/main/docs/CAP-Specification-v1.0.md) and [VAP v1.2 framework](https://github.com/veritaschain/vap-spec/blob/main/spec/v1.2/VAP_Framework_Specification.md) govern current reference terminology and scope.
- [Local SRP extension v0.2](spec/CAP-SRP-Extension.md) and [local CAP v0.2](spec/CAP-Specification-v0_2.md) are historical drafts, not current canonical specifications. Their older versions, diagrams and requirements are retained as historical records.
- [Prior-art report](Cap-srp-world-first-evidence-report.md) is historical research, not a current “world's first” claim, independent validation or proof of universal non-generation.
- [CAP-SRP dashboard/library](https://github.com/veritaschain/cap-srp) is a separate PoC with `GEN_ERROR` and additional checks; it also does not claim VAP v1.2 conformance.

## Repository guide

- `src/srp_core.py`: legacy event logging, local checks and export
- `examples/demo_scenarios.py`: synthetic scenario demonstration
- `tests/test_srp.py`: implementation tests
- `spec/`: historical drafts
- [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md)

## License and contact

[CC BY 4.0 International](LICENSE). VeritasChain Standards Organization (VSO).

- Website: https://veritaschain.org
- Email: standards@veritaschain.org
- GitHub: https://github.com/veritaschain/cap-safe-refusal-provenance

*Verify recorded decisions; do not infer unobserved behavior.*
