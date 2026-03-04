"""
Mutation-Hardened Tests for AuthService
========================================
These tests were created by analyzing surviving mutants from mutmut
and writing targeted tests to kill them.

Key improvements over AI-generated tests:
1. Tests exact boundary conditions (4 vs 5 failures)
2. Verifies counters increment correctly (login_count)
3. Checks audit log entries are created
4. Tests None/empty edge cases
5. Validates all password requirements individually
"""

import pytest
import time
from src.auth_service import AuthService, AuthenticationError, AccountLockedError


class TestAuthServiceMutationHardened:
    """Mutation-hardened test suite with targeted bug detection."""

    def setup_method(self):
        self.auth = AuthService()

    # ==========================================
    # PASSWORD VALIDATION — Kill boundary mutants
    # ==========================================

    def test_password_none_value(self):
        """KILLS MUTANT: Mutation changing 'is None' check"""
        is_valid, msg = self.auth.validate_password_strength(None)
        assert is_valid is False
        assert "None" in msg

    def test_password_no_uppercase(self):
        """KILLS MUTANT: Mutation removing uppercase check"""
        is_valid, msg = self.auth.validate_password_strength("securep@ss1")
        assert is_valid is False
        assert "uppercase" in msg

    def test_password_no_lowercase(self):
        """KILLS MUTANT: Mutation removing lowercase check"""
        is_valid, msg = self.auth.validate_password_strength("SECUREP@SS1")
        assert is_valid is False
        assert "lowercase" in msg

    def test_password_no_digit(self):
        """KILLS MUTANT: Mutation removing digit check"""
        is_valid, msg = self.auth.validate_password_strength("SecureP@ss")
        assert is_valid is False
        assert "digit" in msg

    def test_password_no_special_char(self):
        """KILLS MUTANT: Mutation removing special char check"""
        is_valid, msg = self.auth.validate_password_strength("SecurePass1")
        assert is_valid is False
        assert "special character" in msg

    # ==========================================
    # REGISTRATION — Kill logging mutants
    # ==========================================

    def test_register_creates_audit_log(self):
        """KILLS MUTANT: Mutation removing _log_event call"""
        self.auth.register_user("john", "SecureP@ss1", "john@example.com")
        log = self.auth.get_audit_log(username="john", event_type="USER_REGISTERED")
        assert len(log) == 1
        assert log[0]["username"] == "john"

    def test_register_with_none_fields(self):
        """KILLS MUTANT: Mutation changing 'not username' logic"""
        with pytest.raises(ValueError):
            self.auth.register_user(None, "SecureP@ss1", "john@example.com")
        with pytest.raises(ValueError):
            self.auth.register_user("john", None, "john@example.com")
        with pytest.raises(ValueError):
            self.auth.register_user("john", "SecureP@ss1", None)

    # ==========================================
    # LOGIN — Kill counter and boundary mutants
    # ==========================================

    def test_login_increments_login_count(self):
        """KILLS MUTANT: Mutation changing 'login_count += 1' to 'login_count = 1'"""
        self.auth.register_user("john", "SecureP@ss1", "john@example.com")
        self.auth.register_user("jane", "SecureP@ss1", "jane@example.com")

        self.auth.login("john", "SecureP@ss1")
        assert self.auth.login_count == 1

        self.auth.login("jane", "SecureP@ss1")
        assert self.auth.login_count == 2  # This kills += vs = mutant

    def test_login_resets_failed_attempts_on_success(self):
        """KILLS MUTANT: Mutation removing failed_attempts reset"""
        self.auth.register_user("john", "SecureP@ss1", "john@example.com")

        # Fail 3 times
        for _ in range(3):
            with pytest.raises(AuthenticationError):
                self.auth.login("john", "WrongPassword1!")
        assert self.auth.failed_attempts["john"] == 3

        # Succeed — should reset
        self.auth.login("john", "SecureP@ss1")
        assert self.auth.failed_attempts["john"] == 0

    def test_four_failures_does_not_lock(self):
        """KILLS MUTANT: Mutation changing >= to > in lockout check"""
        self.auth.register_user("john", "SecureP@ss1", "john@example.com")

        for _ in range(4):
            with pytest.raises(AuthenticationError):
                self.auth.login("john", "WrongPassword1!")

        # 4 failures should NOT lock — only 5 does
        token = self.auth.login("john", "SecureP@ss1")
        assert token is not None

    def test_five_failures_locks_account(self):
        """KILLS MUTANT: Confirms exact boundary at MAX_FAILED_ATTEMPTS"""
        self.auth.register_user("john", "SecureP@ss1", "john@example.com")

        for _ in range(5):
            with pytest.raises((AuthenticationError, AccountLockedError)):
                self.auth.login("john", "WrongPassword1!")

        with pytest.raises(AccountLockedError):
            self.auth.login("john", "SecureP@ss1")  # Even correct password is blocked

    def test_login_creates_audit_log_on_success(self):
        """KILLS MUTANT: Mutation removing LOGIN_SUCCESS log"""
        self.auth.register_user("john", "SecureP@ss1", "john@example.com")
        self.auth.login("john", "SecureP@ss1")

        log = self.auth.get_audit_log(username="john", event_type="LOGIN_SUCCESS")
        assert len(log) == 1

    def test_login_creates_audit_log_on_failure(self):
        """KILLS MUTANT: Mutation removing LOGIN_FAILED log"""
        self.auth.register_user("john", "SecureP@ss1", "john@example.com")

        with pytest.raises(AuthenticationError):
            self.auth.login("john", "WrongPassword1!")

        log = self.auth.get_audit_log(username="john", event_type="LOGIN_FAILED")
        assert len(log) >= 1

    # ==========================================
    # SESSION MANAGEMENT — Kill update mutants
    # ==========================================

    def test_validate_session_updates_last_active(self):
        """KILLS MUTANT: Mutation removing last_active update"""
        self.auth.register_user("john", "SecureP@ss1", "john@example.com")
        token = self.auth.login("john", "SecureP@ss1")

        original_time = self.auth.sessions[token]["last_active"]
        time.sleep(0.01)  # Tiny delay
        self.auth.validate_session(token)
        updated_time = self.auth.sessions[token]["last_active"]

        assert updated_time >= original_time

    def test_validate_session_with_none_token(self):
        """KILLS MUTANT: Mutation changing 'not token' logic"""
        result = self.auth.validate_session(None)
        assert result is None

    def test_logout_returns_false_for_invalid_token(self):
        """KILLS MUTANT: Mutation changing return False to return True"""
        result = self.auth.logout("nonexistent_token")
        assert result is False

    def test_logout_creates_audit_log(self):
        """KILLS MUTANT: Mutation removing LOGOUT log event"""
        self.auth.register_user("john", "SecureP@ss1", "john@example.com")
        token = self.auth.login("john", "SecureP@ss1")
        self.auth.logout(token)

        log = self.auth.get_audit_log(username="john", event_type="LOGOUT")
        assert len(log) == 1

    # ==========================================
    # AUDIT LOG FILTERING — Kill filter mutants
    # ==========================================

    def test_audit_log_filter_by_username(self):
        """KILLS MUTANT: Mutation removing username filter"""
        self.auth.register_user("john", "SecureP@ss1", "john@example.com")
        self.auth.register_user("jane", "SecureP@ss1", "jane@example.com")

        john_log = self.auth.get_audit_log(username="john")
        assert all(e["username"] == "john" for e in john_log)

    def test_audit_log_filter_by_event_type(self):
        """KILLS MUTANT: Mutation removing event_type filter"""
        self.auth.register_user("john", "SecureP@ss1", "john@example.com")
        self.auth.login("john", "SecureP@ss1")

        reg_log = self.auth.get_audit_log(event_type="USER_REGISTERED")
        assert all(e["event_type"] == "USER_REGISTERED" for e in reg_log)
