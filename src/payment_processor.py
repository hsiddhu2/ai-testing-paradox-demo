"""
Payment Processor Module
========================
A high-risk module that demonstrates why governance is essential.
Handles payments, refunds, and fraud detection.
"""

import logging
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class PaymentStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"
    REFUNDED = "refunded"
    FLAGGED = "flagged"


class PaymentProcessor:
    """
    Payment processor with fraud detection and governance hooks.
    This module is intentionally marked as HIGH RISK for governance purposes.
    """

    RISK_LEVEL = "HIGH"
    MAX_TRANSACTION_AMOUNT = 10000.00
    FRAUD_THRESHOLD = 5000.00
    DAILY_LIMIT = 25000.00

    def __init__(self):
        self.transactions = []
        self.daily_totals = {}    # {date_str: total_amount}
        self.blocked_cards = set()
        self.audit_trail = []

    def _log_transaction(self, action, details):
        """Record an audit trail entry."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details,
            "requires_review": self.RISK_LEVEL == "HIGH"
        }
        self.audit_trail.append(entry)
        logger.info(f"PAYMENT: {action} - {details}")
        return entry

    def validate_card_number(self, card_number):
        """Validate card number using Luhn algorithm."""
        if not card_number or not isinstance(card_number, str):
            return False

        digits = card_number.replace(" ", "").replace("-", "")

        if not digits.isdigit() or len(digits) < 13 or len(digits) > 19:
            return False

        # Luhn algorithm
        total = 0
        reverse_digits = digits[::-1]
        for i, d in enumerate(reverse_digits):
            n = int(d)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n

        return total % 10 == 0

    def assess_fraud_risk(self, amount, card_number, merchant_category):
        """
        Assess fraud risk score (0-100). Higher = more risky.
        Returns (risk_score, risk_factors).
        """
        risk_score = 0
        risk_factors = []

        if amount > self.FRAUD_THRESHOLD:
            risk_score += 30
            risk_factors.append(f"High amount: ${amount:.2f}")

        if card_number in self.blocked_cards:
            risk_score += 50
            risk_factors.append("Card is on blocked list")

        high_risk_categories = ["gambling", "crypto", "wire_transfer"]
        if merchant_category in high_risk_categories:
            risk_score += 25
            risk_factors.append(f"High-risk category: {merchant_category}")

        today = datetime.now().strftime("%Y-%m-%d")
        daily_total = self.daily_totals.get(today, 0) + amount
        if daily_total > self.DAILY_LIMIT:
            risk_score += 20
            risk_factors.append(f"Daily limit exceeded: ${daily_total:.2f}")

        # Cap at 100
        risk_score = min(risk_score, 100)

        self._log_transaction("FRAUD_ASSESSMENT",
                            f"Score: {risk_score}, Factors: {risk_factors}")
        return risk_score, risk_factors

    def process_payment(self, amount, card_number, merchant_category="retail"):
        """
        Process a payment. Returns transaction dict.
        Requires governance approval for amounts > FRAUD_THRESHOLD.
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")

        if amount > self.MAX_TRANSACTION_AMOUNT:
            raise ValueError(
                f"Amount ${amount:.2f} exceeds maximum ${self.MAX_TRANSACTION_AMOUNT:.2f}"
            )

        if not self.validate_card_number(card_number):
            self._log_transaction("PAYMENT_DECLINED", "Invalid card number")
            return {"status": PaymentStatus.DECLINED, "reason": "Invalid card"}

        risk_score, risk_factors = self.assess_fraud_risk(
            amount, card_number, merchant_category
        )

        transaction = {
            "id": len(self.transactions) + 1,
            "amount": amount,
            "card_last_four": card_number[-4:],
            "merchant_category": merchant_category,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "timestamp": datetime.now().isoformat()
        }

        if risk_score >= 50:
            transaction["status"] = PaymentStatus.FLAGGED
            transaction["requires_human_review"] = True
            self._log_transaction("PAYMENT_FLAGGED",
                                f"Risk score {risk_score}: {risk_factors}")
        elif risk_score >= 30:
            transaction["status"] = PaymentStatus.FLAGGED
            transaction["requires_human_review"] = True
            self._log_transaction("PAYMENT_REVIEW_NEEDED",
                                f"Moderate risk score {risk_score}")
        else:
            transaction["status"] = PaymentStatus.APPROVED
            transaction["requires_human_review"] = False
            today = datetime.now().strftime("%Y-%m-%d")
            self.daily_totals[today] = self.daily_totals.get(today, 0) + amount
            self._log_transaction("PAYMENT_APPROVED", f"Amount: ${amount:.2f}")

        self.transactions.append(transaction)
        return transaction

    def process_refund(self, transaction_id, reason):
        """Process a refund for a transaction. Always requires audit."""
        matching = [t for t in self.transactions if t["id"] == transaction_id]

        if not matching:
            raise ValueError(f"Transaction {transaction_id} not found")

        transaction = matching[0]

        if transaction["status"] == PaymentStatus.REFUNDED:
            raise ValueError("Transaction already refunded")

        transaction["status"] = PaymentStatus.REFUNDED
        transaction["refund_reason"] = reason
        transaction["refund_timestamp"] = datetime.now().isoformat()

        self._log_transaction("REFUND_PROCESSED",
                            f"Transaction {transaction_id}: {reason}")
        return transaction
