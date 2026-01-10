#!/usr/bin/env python3
"""
CAP-SRP Demo Scenarios: Safe Refusal Provenance in Action

This demo shows how SRP would have recorded the refusals that should
have happened during the December 2025 - January 2026 Grok incident.

Key demonstration:
- Every request creates a GEN_ATTEMPT first
- Dangerous requests are followed by GEN_DENY
- Safe requests are followed by GEN
- Third parties can verify completeness

Author: VeritasChain Standards Organization (VSO)
License: CC BY 4.0 International
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.srp_core import (
    SRPLogger, RiskCategory, ModelDecision, InputType
)


def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_event_pair(attempt, outcome, scenario: str):
    """Print a summary of an ATTEMPT→OUTCOME pair."""
    print(f"\n📋 {scenario}")
    print(f"   ATTEMPT ID: {attempt.event_id[:36]}...")
    print(f"   Prompt Hash: {attempt.prompt_hash[:50]}...")
    
    if outcome.event_type == "GEN_DENY":
        print(f"   ───────────────────────────────────────────────")
        print(f"   OUTCOME: ❌ DENIED")
        print(f"   Risk Category: {outcome.risk_category}")
        print(f"   Risk Score: {outcome.risk_score:.0%}")
        print(f"   Reason: {outcome.refusal_reason[:50]}...")
    else:
        print(f"   ───────────────────────────────────────────────")
        print(f"   OUTCOME: ✓ ALLOWED")
        print(f"   Output Hash: {outcome.output_hash[:50]}...")


def scenario_1_csam_prevention(logger: SRPLogger):
    """
    Scenario 1: CSAM Risk Detection
    
    A request involving a reference image of a minor with sexual context.
    This is the most serious category and should be blocked with high confidence.
    """
    print_header("Scenario 1: CSAM Prevention")
    
    attempt, denial = logger.log_refusal(
        prompt="teenage girl in swimsuit at beach photoshoot",
        risk_category=RiskCategory.CSAM_RISK,
        risk_score=0.97,
        refusal_reason="Minor detected in prompt context. Age estimation indicates subject under 18. Blocked per child safety policy.",
        input_type=InputType.TEXT,
        risk_sub_categories=["AGE_UNDER_18", "SEXUALIZED_CONTEXT", "SWIMWEAR_REQUEST"]
    )
    
    print_event_pair(attempt, denial, "CSAM Risk - Blocked")
    
    print("\n   📊 Regulatory significance:")
    print("   • 18 U.S.C. §2256 compliance documented")
    print("   • Request-to-denial timing provable")
    print("   • No content was generated (ATTEMPT has no GEN, only GEN_DENY)")


def scenario_2_ncii_celebrity(logger: SRPLogger):
    """
    Scenario 2: Non-Consensual Intimate Imagery (Celebrity)
    
    Attempting to generate intimate imagery of a real public figure.
    """
    print_header("Scenario 2: Celebrity NCII Prevention")
    
    attempt, denial = logger.log_refusal(
        prompt="famous female singer in revealing lingerie",
        risk_category=RiskCategory.REAL_PERSON_DEEPFAKE,
        risk_score=0.89,
        refusal_reason="Public figure detected via facial recognition embedding. Non-consensual intimate imagery blocked per TAKE IT DOWN Act compliance.",
        risk_sub_categories=["CELEBRITY_DETECTED", "NSFW_CONTEXT", "NO_CONSENT"]
    )
    
    print_event_pair(attempt, denial, "Celebrity Deepfake - Blocked")
    
    print("\n   📊 Regulatory significance:")
    print("   • TAKE IT DOWN Act: No 48-hour removal needed (never generated)")
    print("   • EU AI Act Article 52: Deepfake obligation avoided")
    print("   • Victim can receive cryptographic proof of non-generation")


def scenario_3_digital_undressing(logger: SRPLogger):
    """
    Scenario 3: "Digital Undressing" Attack
    
    This was the core attack vector in the Grok incident: uploading a
    person's photo and requesting clothing removal/reduction.
    """
    print_header("Scenario 3: Digital Undressing Prevention")
    
    # Simulate uploaded reference image
    reference_image = b"<simulated uploaded photo bytes>"
    
    attempt, denial = logger.log_refusal(
        prompt="edit her clothes to bikini",
        risk_category=RiskCategory.NCII_RISK,
        risk_score=0.94,
        refusal_reason="Clothing removal request detected on uploaded person image. Non-consensual intimate imagery policy violation.",
        input_type=InputType.TEXT_IMAGE,
        reference_image=reference_image,
        risk_sub_categories=["UPLOADED_PERSON", "CLOTHING_REMOVAL", "NO_SUBJECT_CONSENT"]
    )
    
    print_event_pair(attempt, denial, "Digital Undressing - Blocked")
    
    print("\n   📊 Key evidence preserved:")
    print("   • Reference image hash recorded (not the image itself)")
    print("   • Attack pattern documented")
    print("   • Timestamp proves refusal timing")


def scenario_4_batch_attack(logger: SRPLogger):
    """
    Scenario 4: Batch Attack Detection
    
    During the Grok incident, 6,700+ images were generated per hour.
    SRP records patterns of abuse attempts from the same session.
    """
    print_header("Scenario 4: Batch Attack Pattern")
    
    session_id = "suspicious-session-abc123"
    attack_prompts = [
        ("woman in underwear", RiskCategory.NCII_RISK),
        ("girl in bikini", RiskCategory.MINOR_SEXUALIZATION),
        ("female in lingerie", RiskCategory.NCII_RISK),
        ("teenager at beach", RiskCategory.MINOR_SEXUALIZATION),
        ("lady in revealing outfit", RiskCategory.NCII_RISK),
    ]
    
    print(f"\n   Session ID: {session_id}")
    print(f"   Attack pattern: {len(attack_prompts)} escalating requests\n")
    
    for i, (prompt, category) in enumerate(attack_prompts):
        attempt, denial = logger.log_refusal(
            prompt=prompt,
            risk_category=category,
            risk_score=0.85 + (i * 0.02),  # Escalating risk
            refusal_reason=f"Pattern detected: Request {i+1}/5 from session with abuse indicators.",
            session_id=session_id,
            risk_sub_categories=["BATCH_PATTERN", "ESCALATING_BEHAVIOR"]
        )
        print(f"   Request {i+1}: {category.value} → DENIED (risk: {denial.risk_score:.0%})")
    
    print("\n   📊 Pattern analysis enabled:")
    print("   • Same session linked across attempts")
    print("   • Escalating risk scores documented")
    print("   • Evidence for account suspension / law enforcement")


def scenario_5_legitimate_request(logger: SRPLogger):
    """
    Scenario 5: Legitimate Request (ALLOWED)
    
    Demonstrates that SRP also records allowed generations,
    proving the system doesn't just log refusals selectively.
    """
    print_header("Scenario 5: Legitimate Request (Allowed)")
    
    # Log the attempt
    attempt = logger.log_attempt(
        prompt="a beautiful sunset over mountains with birds flying",
        input_type=InputType.TEXT
    )
    
    # Simulate low-risk assessment → allow generation
    simulated_output = b"<simulated generated image bytes>"
    gen_event = logger.log_generation(
        attempt_id=attempt.event_id,
        output_data=simulated_output
    )
    
    print_event_pair(attempt, gen_event, "Safe Landscape - Allowed")
    
    print("\n   📊 Why this matters:")
    print("   • Proves we log ALL attempts, not just denials")
    print("   • Auditors can verify: ATTEMPT count = DENY + ALLOW count")
    print("   • Prevents accusation of selective logging")


def generate_compliance_report(logger: SRPLogger):
    """Generate a formatted compliance report."""
    print_header("Compliance Report")
    
    stats = logger.get_statistics()
    completeness = logger.verify_completeness()
    
    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │              CAP-SRP COMPLIANCE REPORT                          │
    │              Evidence of Safe Refusal Provenance                │
    ├─────────────────────────────────────────────────────────────────┤
    """)
    
    print(f"    Chain Integrity:      {stats['chainIntegrity']}")
    print(f"    Completeness Check:   {stats['completenessCheck']}")
    print(f"    Total Attempts:       {stats['totalAttempts']}")
    print(f"    Total Refusals:       {stats['totalRefusals']}")
    print(f"    Total Allowed:        {stats['totalAllowed']}")
    print(f"    Refusal Rate:         {stats['refusalRate']:.2%}")
    print(f"    Avg Risk Score:       {stats['averageRiskScore']:.0%}")
    
    print("\n    Refusals by Category:")
    for cat, count in sorted(stats['byCategory'].items(), key=lambda x: -x[1]):
        pct = count / stats['totalRefusals'] * 100 if stats['totalRefusals'] else 0
        bar = "█" * int(pct / 5)
        print(f"      {cat:25s}: {count:3d} ({pct:5.1f}%) {bar}")
    
    print("""
    ├─────────────────────────────────────────────────────────────────┤
    │  VERIFICATION                                                   │
    │                                                                 │
    │  • Hash chain: Every event linked to predecessor                │
    │  • Completeness: Every ATTEMPT has exactly one outcome          │
    │  • Signatures: Ed25519 non-repudiation (if PyNaCl installed)    │
    │                                                                 │
    │  External anchoring: Optional (recommended for production)      │
    └─────────────────────────────────────────────────────────────────┘
    """)


def main():
    """Run the complete SRP demonstration."""
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║   CAP-SRP: Safe Refusal Provenance Demo                          ║
    ║   "Proving that harmful generations never happened"               ║
    ║                                                                   ║
    ║   Demonstrating ATTEMPT → OUTCOME audit trail                    ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    # Initialize logger
    logger = SRPLogger(
        model_version="safe-img-gen-v1.0",
        policy_id="cap.example.safe-refusal.v1"
    )
    
    print(f"🔧 Initialized SRP Logger")
    print(f"   Model: {logger.model_version}")
    print(f"   Policy: {logger.policy_id}")
    print(f"   Chain ID: {logger.chain_id}")
    
    # Run scenarios
    scenario_1_csam_prevention(logger)
    scenario_2_ncii_celebrity(logger)
    scenario_3_digital_undressing(logger)
    scenario_4_batch_attack(logger)
    scenario_5_legitimate_request(logger)
    
    # Generate report
    generate_compliance_report(logger)
    
    # Export evidence pack
    print_header("Exporting Evidence Pack")
    
    output_dir = Path(__file__).parent.parent / "output"
    pack_path = logger.export_evidence_pack(str(output_dir))
    
    print(f"\n   ✅ Evidence Pack created: {pack_path}")
    print("""
   📁 Contents:
      • manifest.json       - Pack metadata
      • events/             - Individual event records
      • chain/              - Complete hash chain
      • statistics/         - Aggregated metrics (auditor focus)
      • verification/       - Instructions + Merkle root
    """)
    
    # Final message
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║   KEY TAKEAWAY                                                    ║
    ║                                                                   ║
    ║   This PoC demonstrates:                                         ║
    ║   1. Every request creates a GEN_ATTEMPT first                   ║
    ║   2. Dangerous requests get GEN_DENY (with proof)                ║
    ║   3. Safe requests get GEN (also recorded)                       ║
    ║   4. Auditors can verify completeness mathematically             ║
    ║                                                                   ║
    ║   "We don't just block harmful generations.                      ║
    ║    We PROVE that they never happened."                           ║
    ║                                                                   ║
    ║   Verify, Don't Trust.                                           ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    # Verification summary
    integrity = logger.verify_chain_integrity()
    completeness = logger.verify_completeness()
    
    print(f"🔐 Final Verification:")
    print(f"   Chain Integrity: {'✓ VALID' if integrity else '✗ INVALID'}")
    print(f"   Completeness: {'✓ PASSED' if completeness['complete'] else '✗ FAILED'}")
    print(f"   Total Events: {len(logger.events)}")
    print(f"   Chain Head: {logger.current_hash[:50]}...")


if __name__ == "__main__":
    main()
