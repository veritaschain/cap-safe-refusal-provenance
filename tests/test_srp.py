#!/usr/bin/env python3
"""
CAP-SRP Test Suite

Comprehensive tests for the Safe Refusal Provenance core module.
Tests cover event creation, chain integrity, completeness verification,
and evidence pack generation.

Author: VeritasChain Standards Organization (VSO)
License: CC BY 4.0 International
"""

import sys
import json
import hashlib
import tempfile
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.srp_core import (
    SRPLogger, RiskCategory, ModelDecision, InputType,
    GenAttemptEvent, GenDenyEvent, GenEvent, uuid7
)


class TestSRPCore:
    """Test cases for SRP core functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.logger = SRPLogger(
            model_version="test-model-v1.0",
            policy_id="cap.test.policy.v1"
        )
    
    # =========================================================================
    # Initialization Tests
    # =========================================================================
    
    def test_logger_initialization(self):
        """Test SRP logger initializes correctly."""
        assert self.logger.model_version == "test-model-v1.0"
        assert self.logger.policy_id == "cap.test.policy.v1"
        assert self.logger.chain_id is not None
        assert len(self.logger.events) == 0
        assert self.logger.current_hash == self.logger.GENESIS_HASH
    
    def test_uuid7_generation(self):
        """Test UUID v7 generation produces valid UUIDs."""
        id1 = uuid7()
        id2 = uuid7()
        assert id1 != id2  # Should be unique
        assert len(str(id1)) == 36  # Standard UUID format
    
    # =========================================================================
    # Hashing Tests
    # =========================================================================
    
    def test_content_hashing(self):
        """Test content hashing produces consistent results."""
        hash1 = SRPLogger.hash_content("test prompt")
        hash2 = SRPLogger.hash_content("test prompt")
        assert hash1 == hash2
        assert hash1.startswith("sha256:")
        assert len(hash1) == 7 + 64
    
    def test_different_content_different_hash(self):
        """Test different content produces different hashes."""
        hash1 = SRPLogger.hash_content("prompt 1")
        hash2 = SRPLogger.hash_content("prompt 2")
        assert hash1 != hash2
    
    def test_bytes_hashing(self):
        """Test binary content hashing."""
        data = b"test image bytes"
        hash_result = SRPLogger.hash_bytes(data)
        assert hash_result.startswith("sha256:")
        assert len(hash_result) == 7 + 64
    
    # =========================================================================
    # GEN_ATTEMPT Tests
    # =========================================================================
    
    def test_log_attempt_basic(self):
        """Test basic attempt logging."""
        attempt = self.logger.log_attempt(
            prompt="test prompt",
            input_type=InputType.TEXT
        )
        
        assert attempt.event_type == "GEN_ATTEMPT"
        assert attempt.prompt_hash.startswith("sha256:")
        assert attempt.policy_id == self.logger.policy_id
        assert attempt.model_version == self.logger.model_version
        assert attempt.event_hash.startswith("sha256:")
    
    def test_log_attempt_with_image(self):
        """Test attempt logging with reference image."""
        attempt = self.logger.log_attempt(
            prompt="edit this image",
            input_type=InputType.TEXT_IMAGE,
            reference_image=b"test image bytes"
        )
        
        assert attempt.reference_image_hash is not None
        assert attempt.reference_image_hash.startswith("sha256:")
        assert attempt.input_type == "text+image"
    
    def test_log_attempt_with_session(self):
        """Test attempt logging with session tracking."""
        attempt = self.logger.log_attempt(
            prompt="test",
            session_id="session-123",
            actor_id="user-456"
        )
        
        assert attempt.session_id == "session-123"
        assert attempt.actor_hash is not None
        assert attempt.actor_hash.startswith("sha256:")
    
    # =========================================================================
    # GEN_DENY Tests
    # =========================================================================
    
    def test_log_denial_basic(self):
        """Test basic denial logging."""
        attempt = self.logger.log_attempt(prompt="dangerous")
        denial = self.logger.log_denial(
            attempt_id=attempt.event_id,
            risk_category=RiskCategory.CSAM_RISK,
            risk_score=0.95,
            refusal_reason="Test refusal"
        )
        
        assert denial.event_type == "GEN_DENY"
        assert denial.attempt_id == attempt.event_id
        assert denial.risk_category == "CSAM_RISK"
        assert denial.risk_score == 0.95
        assert denial.model_decision == "DENY"
    
    def test_log_denial_with_subcategories(self):
        """Test denial with risk subcategories."""
        attempt = self.logger.log_attempt(prompt="test")
        denial = self.logger.log_denial(
            attempt_id=attempt.event_id,
            risk_category=RiskCategory.NCII_RISK,
            risk_score=0.88,
            refusal_reason="Test",
            risk_sub_categories=["CAT1", "CAT2"]
        )
        
        assert denial.risk_sub_categories == ["CAT1", "CAT2"]
    
    def test_log_denial_human_override(self):
        """Test denial with human override flag."""
        attempt = self.logger.log_attempt(prompt="test")
        denial = self.logger.log_denial(
            attempt_id=attempt.event_id,
            risk_category=RiskCategory.OTHER,
            risk_score=0.5,
            refusal_reason="Manual review",
            human_override=True
        )
        
        assert denial.human_override == True
    
    # =========================================================================
    # GEN (Allow) Tests
    # =========================================================================
    
    def test_log_generation(self):
        """Test successful generation logging."""
        attempt = self.logger.log_attempt(prompt="safe prompt")
        gen = self.logger.log_generation(
            attempt_id=attempt.event_id,
            output_data=b"generated image bytes"
        )
        
        assert gen.event_type == "GEN"
        assert gen.attempt_id == attempt.event_id
        assert gen.output_hash.startswith("sha256:")
    
    # =========================================================================
    # Convenience Method Tests
    # =========================================================================
    
    def test_log_refusal_convenience(self):
        """Test combined ATTEMPT + DENY convenience method."""
        attempt, denial = self.logger.log_refusal(
            prompt="dangerous prompt",
            risk_category=RiskCategory.CSAM_RISK,
            risk_score=0.95,
            refusal_reason="Test"
        )
        
        assert attempt.event_type == "GEN_ATTEMPT"
        assert denial.event_type == "GEN_DENY"
        assert denial.attempt_id == attempt.event_id
    
    # =========================================================================
    # Chain Integrity Tests
    # =========================================================================
    
    def test_chain_linkage(self):
        """Test events are properly linked in chain."""
        attempt1 = self.logger.log_attempt(prompt="prompt 1")
        denial1 = self.logger.log_denial(
            attempt_id=attempt1.event_id,
            risk_category=RiskCategory.CSAM_RISK,
            risk_score=0.9,
            refusal_reason="Reason"
        )
        attempt2 = self.logger.log_attempt(prompt="prompt 2")
        
        assert attempt1.previous_hash == self.logger.GENESIS_HASH
        assert denial1.previous_hash == attempt1.event_hash
        assert attempt2.previous_hash == denial1.event_hash
    
    def test_chain_integrity_valid(self):
        """Test chain verification passes for valid chain."""
        for i in range(5):
            attempt, _ = self.logger.log_refusal(
                prompt=f"prompt {i}",
                risk_category=RiskCategory.CSAM_RISK,
                risk_score=0.9,
                refusal_reason=f"Reason {i}"
            )
        
        assert self.logger.verify_chain_integrity() == True
    
    def test_chain_integrity_tampered(self):
        """Test chain verification fails for tampered chain."""
        self.logger.log_refusal(
            prompt="prompt 1",
            risk_category=RiskCategory.CSAM_RISK,
            risk_score=0.9,
            refusal_reason="Reason"
        )
        
        # Tamper with event hash
        self.logger.events[0].event_hash = "sha256:" + "a" * 64
        
        assert self.logger.verify_chain_integrity() == False
    
    # =========================================================================
    # Completeness Tests
    # =========================================================================
    
    def test_completeness_valid(self):
        """Test completeness verification passes when all attempts have outcomes."""
        for i in range(3):
            self.logger.log_refusal(
                prompt=f"prompt {i}",
                risk_category=RiskCategory.CSAM_RISK,
                risk_score=0.9,
                refusal_reason="Reason"
            )
        
        # Add one allowed
        attempt = self.logger.log_attempt(prompt="safe")
        self.logger.log_generation(attempt.event_id, b"output")
        
        result = self.logger.verify_completeness()
        assert result["complete"] == True
        assert result["totalAttempts"] == 4
        assert result["totalOutcomes"] == 4
    
    def test_completeness_missing_outcome(self):
        """Test completeness fails when attempt lacks outcome."""
        # Log attempt without outcome
        self.logger.log_attempt(prompt="orphan prompt")
        
        result = self.logger.verify_completeness()
        assert result["complete"] == False
        assert len(result["unmatchedAttempts"]) == 1
    
    def test_completeness_orphan_outcome(self):
        """Test completeness detects orphan outcomes."""
        # Create denial with non-existent attempt ID
        denial = GenDenyEvent(
            attempt_id="non-existent-attempt-id",
            risk_category="CSAM_RISK",
            risk_score=0.9,
            refusal_reason="Orphan",
            previous_hash=self.logger.current_hash
        )
        denial.event_hash = self.logger._compute_event_hash(denial)
        self.logger.events.append(denial)
        
        result = self.logger.verify_completeness()
        assert result["complete"] == False
        assert len(result["orphanOutcomes"]) == 1
    
    # =========================================================================
    # Statistics Tests
    # =========================================================================
    
    def test_statistics_basic(self):
        """Test statistics generation."""
        for _ in range(2):
            self.logger.log_refusal(
                prompt="csam",
                risk_category=RiskCategory.CSAM_RISK,
                risk_score=0.9,
                refusal_reason="Reason"
            )
        self.logger.log_refusal(
            prompt="ncii",
            risk_category=RiskCategory.NCII_RISK,
            risk_score=0.8,
            refusal_reason="Reason"
        )
        attempt = self.logger.log_attempt(prompt="safe")
        self.logger.log_generation(attempt.event_id, b"output")
        
        stats = self.logger.get_statistics()
        
        assert stats["totalAttempts"] == 4
        assert stats["totalRefusals"] == 3
        assert stats["totalAllowed"] == 1
        assert stats["byCategory"]["CSAM_RISK"] == 2
        assert stats["byCategory"]["NCII_RISK"] == 1
        assert stats["chainIntegrity"] == "VERIFIED"
        assert stats["completenessCheck"] == "PASSED"
    
    # =========================================================================
    # Serialization Tests
    # =========================================================================
    
    def test_event_to_json(self):
        """Test event JSON serialization."""
        attempt, _ = self.logger.log_refusal(
            prompt="test",
            risk_category=RiskCategory.CSAM_RISK,
            risk_score=0.9,
            refusal_reason="Test"
        )
        
        json_str = attempt.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["eventType"] == "GEN_ATTEMPT"
        assert "eventHash" in parsed
    
    def test_event_to_dict_camelcase(self):
        """Test event dictionary uses camelCase keys."""
        attempt = self.logger.log_attempt(prompt="test")
        d = attempt.to_dict()
        
        assert "eventType" in d
        assert "promptHash" in d
        assert "previousHash" in d
        # Ensure snake_case NOT present
        assert "event_type" not in d
    
    # =========================================================================
    # Edge Case Tests
    # =========================================================================
    
    def test_refusal_reason_truncation(self):
        """Test long refusal reasons are truncated."""
        long_reason = "x" * 1000
        _, denial = self.logger.log_refusal(
            prompt="test",
            risk_category=RiskCategory.CSAM_RISK,
            risk_score=0.9,
            refusal_reason=long_reason
        )
        
        assert len(denial.refusal_reason) <= 500
    
    def test_risk_score_rounding(self):
        """Test risk scores are rounded to 4 decimal places."""
        _, denial = self.logger.log_refusal(
            prompt="test",
            risk_category=RiskCategory.CSAM_RISK,
            risk_score=0.123456789,
            refusal_reason="Test"
        )
        
        assert denial.risk_score == 0.1235
    
    def test_all_risk_categories(self):
        """Test all risk categories can be used."""
        categories = list(RiskCategory)
        for cat in categories:
            _, denial = self.logger.log_refusal(
                prompt=f"test {cat.value}",
                risk_category=cat,
                risk_score=0.9,
                refusal_reason="Test"
            )
            assert denial.risk_category == cat.value
    
    def test_all_input_types(self):
        """Test all input types can be used."""
        input_types = list(InputType)
        for it in input_types:
            attempt = self.logger.log_attempt(
                prompt=f"test {it.value}",
                input_type=it
            )
            assert attempt.input_type == it.value
    
    # =========================================================================
    # Evidence Pack Tests
    # =========================================================================
    
    def test_evidence_pack_export(self, tmp_path=None):
        """Test evidence pack export creates correct structure."""
        if tmp_path is None:
            tmp_path = Path(tempfile.mkdtemp())
        
        # Add some events
        for i in range(3):
            self.logger.log_refusal(
                prompt=f"test {i}",
                risk_category=RiskCategory.CSAM_RISK,
                risk_score=0.9,
                refusal_reason=f"Test {i}"
            )
        
        pack_path = self.logger.export_evidence_pack(str(tmp_path))
        pack_dir = Path(pack_path)
        
        # Check structure
        assert (pack_dir / "manifest.json").exists()
        assert (pack_dir / "events").is_dir()
        assert (pack_dir / "chain" / "hash_chain.json").exists()
        assert (pack_dir / "statistics" / "refusal_stats.json").exists()
        assert (pack_dir / "verification" / "merkle_root.json").exists()
        assert (pack_dir / "verification" / "instructions.md").exists()
        
        # Check manifest
        with open(pack_dir / "manifest.json") as f:
            manifest = json.load(f)
        assert manifest["eventCount"] == 6  # 3 attempts + 3 denials
        assert manifest["chainIntegrity"] == "VERIFIED"
        assert manifest["completenessCheck"] == "PASSED"
        
        # Check events directory
        event_files = list((pack_dir / "events").glob("*.json"))
        assert len(event_files) == 6


def run_tests():
    """Run all tests (pytest-free mode)."""
    test = TestSRPCore()
    tests_passed = 0
    tests_failed = 0
    
    test_methods = [m for m in dir(test) if m.startswith("test_")]
    
    print("CAP-SRP Test Suite")
    print("=" * 60)
    
    for method_name in sorted(test_methods):
        test.setup_method()
        method = getattr(test, method_name)
        
        try:
            # Handle tmp_path parameter
            if "tmp_path" in method.__code__.co_varnames:
                with tempfile.TemporaryDirectory() as tmp:
                    method(Path(tmp))
            else:
                method()
            print(f"  ✓ {method_name}")
            tests_passed += 1
        except AssertionError as e:
            print(f"  ✗ {method_name}: {e}")
            tests_failed += 1
        except Exception as e:
            print(f"  ✗ {method_name}: {type(e).__name__}: {e}")
            tests_failed += 1
    
    print("=" * 60)
    print(f"Results: {tests_passed} passed, {tests_failed} failed")
    return tests_failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
