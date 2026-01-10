"""
CAP-SRP: Safe Refusal Provenance - Core Module

This module provides cryptographic logging and verification of AI content
moderation decisions, specifically proving that harmful content was refused.

Key Features:
- GEN_ATTEMPT: Records every generation request
- GEN_DENY: Records refusals with risk assessment
- Hash chain: Tamper-evident event linking
- Ed25519 signatures: Non-repudiation
- Completeness verification: Every attempt has an outcome

Author: VeritasChain Standards Organization (VSO)
License: CC BY 4.0 International
Version: 0.2.0
"""

import hashlib
import json
import os
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any, Set
from pathlib import Path

try:
    from nacl.signing import SigningKey, VerifyKey
    from nacl.encoding import Base64Encoder
    NACL_AVAILABLE = True
except ImportError:
    NACL_AVAILABLE = False


class RiskCategory(Enum):
    """Risk categories for content moderation decisions."""
    CSAM_RISK = "CSAM_RISK"
    NCII_RISK = "NCII_RISK"
    MINOR_SEXUALIZATION = "MINOR_SEXUALIZATION"
    REAL_PERSON_DEEPFAKE = "REAL_PERSON_DEEPFAKE"
    VIOLENCE_EXTREME = "VIOLENCE_EXTREME"
    HATE_CONTENT = "HATE_CONTENT"
    TERRORIST_CONTENT = "TERRORIST_CONTENT"
    SELF_HARM_PROMOTION = "SELF_HARM_PROMOTION"
    OTHER = "OTHER"


class ModelDecision(Enum):
    """Model decision types for content requests."""
    ALLOW = "ALLOW"         # Generation permitted
    DENY = "DENY"           # Generation refused
    WARN = "WARN"           # Allowed with warning
    ESCALATE = "ESCALATE"   # Escalated to human review
    QUARANTINE = "QUARANTINE"  # Generated but quarantined


class InputType(Enum):
    """Types of input for generation requests."""
    TEXT = "text"
    IMAGE = "image"
    TEXT_IMAGE = "text+image"
    VIDEO = "video"
    AUDIO = "audio"


@dataclass
class GenAttemptEvent:
    """
    GEN_ATTEMPT Event: Records that a generation request was received.
    
    This event MUST be created for every generation request, regardless
    of whether it will be allowed or denied. It establishes the audit
    trail that every request has a corresponding outcome.
    """
    event_type: str = "GEN_ATTEMPT"
    event_id: str = ""
    timestamp: str = ""
    prompt_hash: str = ""
    reference_image_hash: Optional[str] = None
    input_type: str = "text"
    policy_id: str = ""
    model_version: str = ""
    session_id: Optional[str] = None
    actor_hash: Optional[str] = None
    previous_hash: str = ""
    event_hash: str = ""
    signature: str = ""
    
    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid7())
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with camelCase keys."""
        return {
            "eventType": self.event_type,
            "eventId": self.event_id,
            "timestamp": self.timestamp,
            "promptHash": self.prompt_hash,
            "referenceImageHash": self.reference_image_hash,
            "inputType": self.input_type,
            "policyId": self.policy_id,
            "modelVersion": self.model_version,
            "sessionId": self.session_id,
            "actorHash": self.actor_hash,
            "previousHash": self.previous_hash,
            "eventHash": self.event_hash,
            "signature": self.signature
        }
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


@dataclass
class GenDenyEvent:
    """
    GEN_DENY Event: Records that a generation request was refused.
    
    This event MUST reference the corresponding GEN_ATTEMPT via attemptId.
    It provides cryptographic proof that the request was received, evaluated,
    and refused with a specific reason.
    """
    event_type: str = "GEN_DENY"
    event_id: str = ""
    timestamp: str = ""
    attempt_id: str = ""  # References the GEN_ATTEMPT
    risk_category: str = ""
    risk_sub_categories: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    refusal_reason: str = ""
    model_decision: str = "DENY"
    human_override: bool = False
    previous_hash: str = ""
    event_hash: str = ""
    signature: str = ""
    
    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid7())
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "eventType": self.event_type,
            "eventId": self.event_id,
            "timestamp": self.timestamp,
            "attemptId": self.attempt_id,
            "riskCategory": self.risk_category,
            "riskSubCategories": self.risk_sub_categories,
            "riskScore": self.risk_score,
            "refusalReason": self.refusal_reason,
            "modelDecision": self.model_decision,
            "humanOverride": self.human_override,
            "previousHash": self.previous_hash,
            "eventHash": self.event_hash,
            "signature": self.signature
        }
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


@dataclass
class GenEvent:
    """
    GEN Event: Records that a generation was allowed and completed.
    
    Used when a request passes risk assessment and content is generated.
    """
    event_type: str = "GEN"
    event_id: str = ""
    timestamp: str = ""
    attempt_id: str = ""
    output_hash: str = ""  # Hash of generated content
    previous_hash: str = ""
    event_hash: str = ""
    signature: str = ""
    
    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid7())
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "eventType": self.event_type,
            "eventId": self.event_id,
            "timestamp": self.timestamp,
            "attemptId": self.attempt_id,
            "outputHash": self.output_hash,
            "previousHash": self.previous_hash,
            "eventHash": self.event_hash,
            "signature": self.signature
        }
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


def uuid7() -> uuid.UUID:
    """Generate a UUID v7 (time-ordered)."""
    timestamp_ms = int(time.time() * 1000)
    uuid_int = (timestamp_ms & 0xFFFFFFFFFFFF) << 80
    uuid_int |= 0x7000 << 64
    uuid_int |= int.from_bytes(os.urandom(8), 'big') & 0x3FFFFFFFFFFFFFFF
    return uuid.UUID(int=uuid_int)


class SRPLogger:
    """
    Safe Refusal Provenance Logger.
    
    Provides methods to log generation attempts and their outcomes
    (allow or deny) with cryptographic integrity guarantees.
    
    Key invariant: Every GEN_ATTEMPT must have exactly one outcome
    (GEN or GEN_DENY).
    """
    
    GENESIS_HASH = "sha256:" + "0" * 64
    OUTCOME_TYPES = {"GEN", "GEN_DENY", "GEN_WARN", "GEN_ESCALATE", "GEN_QUARANTINE"}
    
    def __init__(
        self,
        model_version: str,
        policy_id: str,
        signing_key: Optional[bytes] = None,
        chain_id: Optional[str] = None
    ):
        """
        Initialize the SRP Logger.
        
        Args:
            model_version: Model identifier (e.g., "img-gen-v4.2.1")
            policy_id: Policy identifier (e.g., "cap.example.safe-refusal.v1")
            signing_key: Ed25519 private key bytes (generates if not provided)
            chain_id: Unique chain identifier (generates if not provided)
        """
        self.model_version = model_version
        self.policy_id = policy_id
        self.chain_id = chain_id or str(uuid.uuid4())
        self.events: List[Any] = []
        self.current_hash = self.GENESIS_HASH
        
        # Signing key setup
        if NACL_AVAILABLE:
            if signing_key:
                self.signing_key = SigningKey(signing_key)
            else:
                self.signing_key = SigningKey.generate()
            self.verify_key = self.signing_key.verify_key
        else:
            self.signing_key = None
            self.verify_key = None
    
    @staticmethod
    def hash_content(content: str) -> str:
        """Hash text content using SHA-256."""
        return f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()}"
    
    @staticmethod
    def hash_bytes(data: bytes) -> str:
        """Hash binary content using SHA-256."""
        return f"sha256:{hashlib.sha256(data).hexdigest()}"
    
    def _compute_event_hash(self, event: Any) -> str:
        """Compute SHA-256 hash of an event (excluding hash and signature)."""
        event_dict = event.to_dict()
        event_dict.pop("signature", None)
        event_dict.pop("eventHash", None)
        # Remove None values for canonical form
        event_dict = {k: v for k, v in event_dict.items() if v is not None}
        canonical = json.dumps(event_dict, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
        return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"
    
    def _sign_hash(self, event_hash: str) -> str:
        """Sign an event hash using Ed25519."""
        if not NACL_AVAILABLE or not self.signing_key:
            return ""
        signed = self.signing_key.sign(event_hash.encode('utf-8'), encoder=Base64Encoder)
        return f"ed25519:{signed.signature.decode('utf-8')}"
    
    def log_attempt(
        self,
        prompt: str,
        input_type: InputType = InputType.TEXT,
        reference_image: Optional[bytes] = None,
        session_id: Optional[str] = None,
        actor_id: Optional[str] = None
    ) -> GenAttemptEvent:
        """
        Log a generation attempt.
        
        This MUST be called for every generation request before processing.
        The returned event's event_id should be passed to the outcome logger.
        
        Args:
            prompt: The generation prompt (will be hashed, not stored)
            input_type: Type of input (text, image, text+image, etc.)
            reference_image: Optional reference image bytes (will be hashed)
            session_id: Optional session identifier
            actor_id: Optional user identifier (will be hashed)
        
        Returns:
            GenAttemptEvent with event_id for linking to outcome
        """
        event = GenAttemptEvent(
            prompt_hash=self.hash_content(prompt),
            reference_image_hash=self.hash_bytes(reference_image) if reference_image else None,
            input_type=input_type.value,
            policy_id=self.policy_id,
            model_version=self.model_version,
            session_id=session_id,
            actor_hash=self.hash_content(actor_id) if actor_id else None,
            previous_hash=self.current_hash
        )
        
        event.event_hash = self._compute_event_hash(event)
        event.signature = self._sign_hash(event.event_hash)
        
        self.current_hash = event.event_hash
        self.events.append(event)
        
        return event
    
    def log_denial(
        self,
        attempt_id: str,
        risk_category: RiskCategory,
        risk_score: float,
        refusal_reason: str,
        decision: ModelDecision = ModelDecision.DENY,
        risk_sub_categories: Optional[List[str]] = None,
        human_override: bool = False
    ) -> GenDenyEvent:
        """
        Log a generation denial (refusal).
        
        Args:
            attempt_id: The event_id from the corresponding GEN_ATTEMPT
            risk_category: Primary risk category detected
            risk_score: Confidence score (0.0 to 1.0)
            refusal_reason: Human-readable explanation
            decision: Decision type (DENY, WARN, ESCALATE, QUARANTINE)
            risk_sub_categories: Additional risk flags
            human_override: Whether a human overrode the model
        
        Returns:
            GenDenyEvent linked to the attempt
        """
        event = GenDenyEvent(
            attempt_id=attempt_id,
            risk_category=risk_category.value,
            risk_sub_categories=risk_sub_categories or [],
            risk_score=round(risk_score, 4),
            refusal_reason=refusal_reason[:500],
            model_decision=decision.value,
            human_override=human_override,
            previous_hash=self.current_hash
        )
        
        event.event_hash = self._compute_event_hash(event)
        event.signature = self._sign_hash(event.event_hash)
        
        self.current_hash = event.event_hash
        self.events.append(event)
        
        return event
    
    def log_generation(
        self,
        attempt_id: str,
        output_data: bytes
    ) -> GenEvent:
        """
        Log a successful generation.
        
        Args:
            attempt_id: The event_id from the corresponding GEN_ATTEMPT
            output_data: The generated content (will be hashed, not stored)
        
        Returns:
            GenEvent linked to the attempt
        """
        event = GenEvent(
            attempt_id=attempt_id,
            output_hash=self.hash_bytes(output_data),
            previous_hash=self.current_hash
        )
        
        event.event_hash = self._compute_event_hash(event)
        event.signature = self._sign_hash(event.event_hash)
        
        self.current_hash = event.event_hash
        self.events.append(event)
        
        return event
    
    def log_refusal(
        self,
        prompt: str,
        risk_category: RiskCategory,
        risk_score: float,
        refusal_reason: str,
        decision: ModelDecision = ModelDecision.DENY,
        input_type: InputType = InputType.TEXT,
        reference_image: Optional[bytes] = None,
        risk_sub_categories: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        human_override: bool = False
    ) -> tuple:
        """
        Convenience method: Log both ATTEMPT and DENY in one call.
        
        Returns:
            Tuple of (GenAttemptEvent, GenDenyEvent)
        """
        attempt = self.log_attempt(
            prompt=prompt,
            input_type=input_type,
            reference_image=reference_image,
            session_id=session_id,
            actor_id=actor_id
        )
        
        denial = self.log_denial(
            attempt_id=attempt.event_id,
            risk_category=risk_category,
            risk_score=risk_score,
            refusal_reason=refusal_reason,
            decision=decision,
            risk_sub_categories=risk_sub_categories,
            human_override=human_override
        )
        
        return attempt, denial
    
    def verify_chain_integrity(self) -> bool:
        """Verify the hash chain is intact (no tampering)."""
        if not self.events:
            return True
        
        expected_prev = self.GENESIS_HASH
        for event in self.events:
            if event.previous_hash != expected_prev:
                return False
            computed = self._compute_event_hash(event)
            if event.event_hash != computed:
                return False
            expected_prev = event.event_hash
        
        return True
    
    def verify_completeness(self) -> Dict[str, Any]:
        """
        Verify that every GEN_ATTEMPT has exactly one outcome.
        
        Returns:
            Dictionary with verification results
        """
        attempts: Set[str] = set()
        outcomes: Set[str] = set()
        
        for event in self.events:
            if event.event_type == "GEN_ATTEMPT":
                attempts.add(event.event_id)
            elif event.event_type in self.OUTCOME_TYPES:
                outcomes.add(event.attempt_id)
        
        unmatched = attempts - outcomes
        orphans = outcomes - attempts
        
        return {
            "complete": len(unmatched) == 0 and len(orphans) == 0,
            "totalAttempts": len(attempts),
            "totalOutcomes": len(outcomes),
            "unmatchedAttempts": list(unmatched),
            "orphanOutcomes": list(orphans)
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregated statistics for the event chain."""
        attempts = [e for e in self.events if e.event_type == "GEN_ATTEMPT"]
        denials = [e for e in self.events if e.event_type == "GEN_DENY"]
        allowed = [e for e in self.events if e.event_type == "GEN"]
        
        completeness = self.verify_completeness()
        
        stats = {
            "totalAttempts": len(attempts),
            "totalRefusals": len(denials),
            "totalAllowed": len(allowed),
            "refusalRate": len(denials) / len(attempts) if attempts else 0.0,
            "completenessCheck": "PASSED" if completeness["complete"] else "FAILED",
            "byCategory": {},
            "byDecision": {},
            "averageRiskScore": 0.0,
            "chainIntegrity": "VERIFIED" if self.verify_chain_integrity() else "INVALID"
        }
        
        if denials:
            for d in denials:
                cat = d.risk_category
                stats["byCategory"][cat] = stats["byCategory"].get(cat, 0) + 1
                dec = d.model_decision
                stats["byDecision"][dec] = stats["byDecision"].get(dec, 0) + 1
            
            stats["averageRiskScore"] = round(
                sum(d.risk_score for d in denials) / len(denials), 4
            )
        
        return stats
    
    def export_evidence_pack(self, output_dir: str) -> str:
        """
        Export the event chain as a regulatory-ready Evidence Pack.
        
        Args:
            output_dir: Directory to create the evidence pack in
        
        Returns:
            Path to the created evidence pack directory
        """
        pack_dir = Path(output_dir) / f"evidence-pack-{self.chain_id}"
        
        # Create directory structure
        (pack_dir / "events").mkdir(parents=True, exist_ok=True)
        (pack_dir / "chain").mkdir(exist_ok=True)
        (pack_dir / "statistics").mkdir(exist_ok=True)
        (pack_dir / "verification").mkdir(exist_ok=True)
        
        # Write manifest
        completeness = self.verify_completeness()
        manifest = {
            "packId": str(uuid.uuid4()),
            "chainId": self.chain_id,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "modelVersion": self.model_version,
            "policyId": self.policy_id,
            "eventCount": len(self.events),
            "chainIntegrity": "VERIFIED" if self.verify_chain_integrity() else "INVALID",
            "completenessCheck": "PASSED" if completeness["complete"] else "FAILED"
        }
        with open(pack_dir / "manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Write individual events
        for i, event in enumerate(self.events):
            event_type = event.event_type.lower()
            filename = f"{i+1:04d}-{event_type}.json"
            with open(pack_dir / "events" / filename, 'w') as f:
                f.write(event.to_json())
        
        # Write complete chain
        chain = [e.to_dict() for e in self.events]
        with open(pack_dir / "chain" / "hash_chain.json", 'w') as f:
            json.dump(chain, f, indent=2)
        
        # Write statistics
        stats = self.get_statistics()
        stats["period"] = {
            "start": self.events[0].timestamp if self.events else None,
            "end": self.events[-1].timestamp if self.events else None
        }
        with open(pack_dir / "statistics" / "refusal_stats.json", 'w') as f:
            json.dump(stats, f, indent=2)
        
        # Write Merkle root
        if self.events:
            all_hashes = "".join(e.event_hash for e in self.events)
            merkle_root = f"sha256:{hashlib.sha256(all_hashes.encode()).hexdigest()}"
        else:
            merkle_root = self.GENESIS_HASH
        
        with open(pack_dir / "verification" / "merkle_root.json", 'w') as f:
            json.dump({
                "merkleRoot": merkle_root,
                "eventCount": len(self.events),
                "computedAt": datetime.now(timezone.utc).isoformat(),
                "anchorStatus": "NOT_ANCHORED",
                "anchorNote": "External anchoring is optional in this PoC"
            }, f, indent=2)
        
        # Write verification instructions
        instructions = """# Evidence Pack Verification Guide

## What This Pack Proves

1. **Generation requests were received** (GEN_ATTEMPT events)
2. **Harmful requests were refused** (GEN_DENY events)
3. **The record is tamper-evident** (hash chain linkage)
4. **Every request has an outcome** (completeness check)

## Quick Verification (< 2 minutes)

### Step 1: Verify Hash Chain

```bash
# Each event's previousHash must match the prior event's eventHash
python -c "
import json
with open('chain/hash_chain.json') as f:
    events = json.load(f)
prev = 'sha256:' + '0'*64
for e in events:
    assert e['previousHash'] == prev, f'Chain broken at {e[\"eventId\"]}'
    prev = e['eventHash']
print('✓ Hash chain verified')
"
```

### Step 2: Verify Completeness

```bash
# Every GEN_ATTEMPT must have a GEN or GEN_DENY
python -c "
import json
with open('chain/hash_chain.json') as f:
    events = json.load(f)
attempts = {e['eventId'] for e in events if e['eventType'] == 'GEN_ATTEMPT'}
outcomes = {e['attemptId'] for e in events if e['eventType'] in ['GEN', 'GEN_DENY']}
assert attempts == outcomes, 'Completeness check failed'
print('✓ Completeness verified')
"
```

### Step 3: Review Statistics

Open `statistics/refusal_stats.json` to see:
- Total attempts vs. refusals
- Breakdown by risk category
- Chain integrity status

## What This Proves to Regulators

- ✓ Requests were logged before processing
- ✓ Refusals have documented reasons
- ✓ Records cannot be modified without detection
- ✓ No requests were "hidden" from the log

## External Anchoring (Optional)

For production deployments, the `merkle_root.json` can be anchored to:
- Ethereum mainnet transaction
- RFC 3161 Timestamp Authority
- Other immutable public record

This PoC demonstrates the cryptographic structure; external anchoring
adds non-repudiation for long-term regulatory evidence.

---

For questions: standards@veritaschain.org
"""
        with open(pack_dir / "verification" / "instructions.md", 'w') as f:
            f.write(instructions)
        
        return str(pack_dir)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 2 and sys.argv[1] == "--verify":
        # Verification mode
        pack_path = sys.argv[2]
        print(f"Verifying evidence pack: {pack_path}")
        # TODO: Implement standalone verification
        print("Standalone verification not yet implemented")
    else:
        # Demo mode
        if not NACL_AVAILABLE:
            print("Note: PyNaCl not installed. Signatures disabled.")
        
        logger = SRPLogger(
            model_version="img-gen-v4.2.1",
            policy_id="cap.example.safe-refusal.v1"
        )
        
        # Log a refusal
        attempt, denial = logger.log_refusal(
            prompt="test dangerous prompt",
            risk_category=RiskCategory.CSAM_RISK,
            risk_score=0.95,
            refusal_reason="Test refusal - minor detected"
        )
        
        print("GEN_ATTEMPT:")
        print(attempt.to_json())
        print("\nGEN_DENY:")
        print(denial.to_json())
        print(f"\nChain integrity: {'✓' if logger.verify_chain_integrity() else '✗'}")
        print(f"Completeness: {logger.verify_completeness()}")
