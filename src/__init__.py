"""
CAP-SRP: Safe Refusal Provenance

A cryptographic audit framework for AI content moderation decisions.
Proves that harmful content was refused, not just claimed to be refused.

Part of the VAP (Verifiable AI Provenance) ecosystem.

Author: VeritasChain Standards Organization (VSO)
License: CC BY 4.0 International
Website: https://veritaschain.org
"""

from .srp_core import (
    SRPLogger,
    RiskCategory,
    ModelDecision,
    InputType,
    GenAttemptEvent,
    GenDenyEvent,
    GenEvent,
    uuid7
)

__version__ = "0.2.0"
__author__ = "VeritasChain Standards Organization"
__license__ = "CC BY 4.0"

__all__ = [
    "SRPLogger",
    "RiskCategory",
    "ModelDecision",
    "InputType",
    "GenAttemptEvent",
    "GenDenyEvent",
    "GenEvent",
    "uuid7"
]
