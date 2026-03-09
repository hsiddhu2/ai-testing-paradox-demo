"""
Payment Processor Tests — With Governance Annotations
======================================================
Demonstrates human-in-the-loop governance by marking tests
that require human review for high-risk scenarios.
"""

import pytest
from src.payment_processor import PaymentProcessor, PaymentStatus


class TestPaymentProcessor:

    def setup_method(self):
        self.pp = PaymentProcessor()
        # Valid test card number (passes Luhn): 4532015112830366
        self.valid_card = "4532015112830366"

    # --- Card Validation ---

    def test_valid_card_number(self):
        assert self.pp.validate_card_number(self.valid_card) is True

    def test_invalid_card_number(self):
        assert self.pp.validate_card_number("1234567890123456") is False

    def test_card_with_spaces(self):
        assert self.pp.validate_card_number("4532 0151 1283 0366") is True

    def test_card_none(self):
        assert self.pp.validate_card_number(None) is False

    def test_card_empty(self):
        assert self.pp.validate_card_number("") is False

    def test_card_too_short(self):
        assert self.pp.validate_card_number("123") is False

    # --- Payment Processing ---

    def test_process_normal_payment(self):
        result = self.pp.process_payment(50.00, self.valid_card)
        assert result["status"] == PaymentStatus.APPROVED
        assert result["requires_human_review"] is False

    def test_process_payment_negative_amount(self):
        with pytest.raises(ValueError, match="positive"):
            self.pp.process_payment(-10.00, self.valid_card)

    def test_process_payment_zero_amount(self):
        with pytest.raises(ValueError, match="positive"):
            self.pp.process_payment(0, self.valid_card)

    def test_process_payment_exceeds_max(self):
        with pytest.raises(ValueError, match="exceeds maximum"):
            self.pp.process_payment(15000.00, self.valid_card)

    def test_process_payment_invalid_card(self):
        # Use a card that fails Luhn algorithm validation
        result = self.pp.process_payment(50.00, "1234567890123456")
        assert result["status"] == PaymentStatus.DECLINED
        assert result["reason"] == "Invalid card"

    # --- Fraud Detection & Governance ---

    def test_high_amount_triggers_review(self):
        """GOVERNANCE: Amounts above FRAUD_THRESHOLD require human review."""
        result = self.pp.process_payment(6000.00, self.valid_card)
        assert result["status"] == PaymentStatus.FLAGGED
        assert result["requires_human_review"] is True

    def test_high_risk_category_triggers_review(self):
        """GOVERNANCE: High-risk merchant categories require human review."""
        result = self.pp.process_payment(100.00, self.valid_card, "gambling")
        assert result["risk_score"] >= 25

    def test_blocked_card_flagged(self):
        """GOVERNANCE: Blocked cards must be flagged."""
        self.pp.blocked_cards.add(self.valid_card)
        result = self.pp.process_payment(50.00, self.valid_card)
        assert result["status"] == PaymentStatus.FLAGGED
        assert result["requires_human_review"] is True

    def test_daily_limit_tracking(self):
        """Verify daily totals are tracked correctly."""
        self.pp.process_payment(100.00, self.valid_card)
        self.pp.process_payment(200.00, self.valid_card)
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        assert self.pp.daily_totals[today] == 300.00

    # --- Audit Trail ---

    def test_audit_trail_populated(self):
        """GOVERNANCE: All transactions must create audit entries."""
        self.pp.process_payment(50.00, self.valid_card)
        assert len(self.pp.audit_trail) >= 1
        assert self.pp.audit_trail[-1]["requires_review"] is True  # HIGH risk level

    # --- Refunds ---

    def test_process_refund(self):
        result = self.pp.process_payment(50.00, self.valid_card)
        refund = self.pp.process_refund(result["id"], "Customer request")
        assert refund["status"] == PaymentStatus.REFUNDED

    def test_refund_nonexistent_transaction(self):
        with pytest.raises(ValueError, match="not found"):
            self.pp.process_refund(999, "Reason")

    def test_double_refund_prevented(self):
        """GOVERNANCE: Double refunds must be prevented."""
        result = self.pp.process_payment(50.00, self.valid_card)
        self.pp.process_refund(result["id"], "First refund")
        with pytest.raises(ValueError, match="already refunded"):
            self.pp.process_refund(result["id"], "Second refund")
