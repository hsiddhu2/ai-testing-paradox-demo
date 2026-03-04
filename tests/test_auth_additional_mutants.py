"""
Additional Tests to Kill Remaining Critical Mutants
====================================================
These tests target specific behavioral mutants that survived:
- Constant value changes (MIN_PASSWORD_LENGTH)
- Boundary condition operators (< vs <=)
- Logic inversions (return False vs True)
"""

import pytest
from src.auth_service import AuthService, AuthenticationError, AccountLockedError


class TestAuthAdditionalMutantKillers:
    """Tests targeting specific surviving mutants."""

    def setup_method(self):
        self.auth = AuthService()

    # ==========================================
    # Kill MIN_PASSWORD_LENGTH constant mutant
    # ==========================================

    def test_password_exactly_8_chars_is_valid(self):
        """
        KILLS MUTANT: MIN_PASSWORD_LENGTH = 8 → 9
        An 8-character password meeting all requirements should be valid.
        If MIN_PASSWORD_LENGTH is changed to 9, this test will fail.
        """
        password = "Abcd!123"  # Exactly 8 chars, meets all requirements
        is_valid, msg = self.auth.validate_password_strength(password)
        assert is_valid is True
        assert msg == "Password meets all requirements"

    def test_password_7_chars_is_invalid(self):
        """
        KILLS MUTANT: Confirms boundary at exactly 8 characters.
        7 chars should fail even if it meets other requirements.
        """
        password = "Abc!123"  # 7 chars
        is_valid, msg = self.auth.validate_password_strength(password)
        assert is_valid is False
        assert "at least 8" in msg

    # ==========================================
    # Kill boundary operator mutant (< vs <=)
    # ==========================================

    def test_password_length_boundary_less_than_not_equal(self):
        """
        KILLS MUTANT: len(password) < MIN_PASSWORD_LENGTH → <=
        This ensures the operator is strictly less-than, not less-than-or-equal.
        An 8-char password should pass, not fail.
        """
        # This test overlaps with test_password_exactly_8_chars_is_valid
        # but explicitly documents the boundary operator
        password = "Secure1!"  # Exactly 8 chars
        is_valid, _ = self.auth.validate_password_strength(password)
        assert is_valid is True

    # ==========================================
    # Kill special character validation inversion
    # ==========================================

    def test_password_without_special_char_must_fail(self):
        """
        KILLS MUTANT: return False → return True in special char check
        A password without special chars MUST fail validation.
        """
        password = "SecurePass123"  # No special char
        is_valid, msg = self.auth.validate_password_strength(password)
        assert is_valid is False  # Must be False, not True
        assert "special character" in msg

    def test_password_with_special_char_must_pass(self):
        """
        KILLS MUTANT: Confirms special char check returns correct boolean.
        A password WITH special chars should pass (along with other requirements).
        """
        password = "SecureP@ss1"  # Has special char
        is_valid, msg = self.auth.validate_password_strength(password)
        assert is_valid is True
        assert msg == "Password meets all requirements"

    # ==========================================
    # Kill MAX_FAILED_ATTEMPTS constant mutant
    # ==========================================

    def test_lockout_happens_at_exactly_5_attempts(self):
        """
        KILLS MUTANT: MAX_FAILED_ATTEMPTS = 5 → 6
        Account should lock after exactly 5 failed attempts, not 6.
        """
        self.auth.register_user("john", "SecureP@ss1", "john@example.com")
        
        # Make exactly 5 failed attempts
        for i in range(5):
            with pytest.raises((AuthenticationError, AccountLockedError)):
                self.auth.login("john", "WrongPassword1!")
        
        # 6th attempt should be blocked due to lockout
        with pytest.raises(AccountLockedError) as exc_info:
            self.auth.login("john", "WrongPassword1!")
        
        assert "locked" in str(exc_info.value).lower()

    # ==========================================
    # Kill LOCKOUT_DURATION_MINUTES constant mutant
    # ==========================================

    def test_lockout_duration_is_30_minutes(self):
        """
        KILLS MUTANT: LOCKOUT_DURATION_MINUTES = 30 → 31
        Verifies the lockout duration constant is exactly 30 minutes.
        """
        from datetime import datetime, timedelta
        
        self.auth.register_user("john", "SecureP@ss1", "john@example.com")
        
        # Trigger lockout
        for _ in range(5):
            try:
                self.auth.login("john", "WrongPassword1!")
            except (AuthenticationError, AccountLockedError):
                pass
        
        # Check lockout_until is set to 30 minutes from now
        lockout_time = self.auth.lockout_until["john"]
        now = datetime.now()
        expected_duration = timedelta(minutes=30)
        actual_duration = lockout_time - now
        
        # Allow 1 second tolerance for test execution time
        assert abs(actual_duration.total_seconds() - expected_duration.total_seconds()) < 1
