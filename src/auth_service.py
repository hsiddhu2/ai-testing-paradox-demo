"""
Authentication Service Module
=============================
A realistic authentication module with multiple behaviors that
AI-generated tests often miss. Used to demonstrate the gap between
code coverage and mutation testing kill rate.
"""

import hashlib
import logging
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class AccountLockedError(Exception):
    """Raised when account is locked due to too many failed attempts."""
    pass


class AuthService:
    """
    Authentication service with login, lockout, password validation,
    session management, and audit logging.
    """

    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30
    MIN_PASSWORD_LENGTH = 8
    SESSION_TIMEOUT_HOURS = 24

    def __init__(self):
        self.users = {}           # {username: {password_hash, email, created_at}}
        self.failed_attempts = {} # {username: count}
        self.lockout_until = {}   # {username: datetime}
        self.sessions = {}        # {token: {username, created_at, last_active}}
        self.audit_log = []       # List of audit events
        self.login_count = 0      # Total successful logins

    def _hash_password(self, password):
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def _log_event(self, event_type, username, details=""):
        """Log an audit event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "username": username,
            "details": details
        }
        self.audit_log.append(event)
        logger.info(f"AUTH_EVENT: {event_type} for user {username}: {details}")
        return event

    def validate_password_strength(self, password):
        """
        Validate password strength. Returns (is_valid, message).
        Requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if password is None:
            return False, "Password cannot be None"

        if len(password) < self.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters"

        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"

        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"

        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"

        return True, "Password meets all requirements"

    def register_user(self, username, password, email):
        """Register a new user."""
        if not username or not password or not email:
            raise ValueError("Username, password, and email are required")

        if username in self.users:
            raise ValueError(f"Username '{username}' is already taken")

        is_valid, message = self.validate_password_strength(password)
        if not is_valid:
            raise ValueError(f"Weak password: {message}")

        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
            raise ValueError("Invalid email format")

        self.users[username] = {
            "password_hash": self._hash_password(password),
            "email": email,
            "created_at": datetime.now().isoformat()
        }
        self._log_event("USER_REGISTERED", username, f"Email: {email}")
        return True

    def _is_account_locked(self, username):
        """Check if an account is currently locked."""
        if username in self.lockout_until:
            if datetime.now() < self.lockout_until[username]:
                return True
            else:
                del self.lockout_until[username]
                self.failed_attempts[username] = 0
                self._log_event("ACCOUNT_UNLOCKED", username, "Lockout period expired")
                return False
        return False

    def login(self, username, password):
        """
        Authenticate a user. Returns a session token on success.
        Tracks failed attempts and locks account after MAX_FAILED_ATTEMPTS.
        """
        if not username or not password:
            raise ValueError("Username and password are required")

        if self._is_account_locked(username):
            remaining = (self.lockout_until[username] - datetime.now()).seconds // 60
            self._log_event("LOGIN_BLOCKED", username, f"Account locked for {remaining} more minutes")
            raise AccountLockedError(
                f"Account is locked. Try again in {remaining} minutes."
            )

        if username not in self.users:
            self._log_event("LOGIN_FAILED", username, "Unknown user")
            raise AuthenticationError("Invalid username or password")

        if self.users[username]["password_hash"] != self._hash_password(password):
            self.failed_attempts[username] = self.failed_attempts.get(username, 0) + 1
            attempts = self.failed_attempts[username]
            remaining_attempts = self.MAX_FAILED_ATTEMPTS - attempts

            if attempts >= self.MAX_FAILED_ATTEMPTS:
                self.lockout_until[username] = datetime.now() + timedelta(
                    minutes=self.LOCKOUT_DURATION_MINUTES
                )
                self._log_event("ACCOUNT_LOCKED", username,
                              f"Locked after {attempts} failed attempts")
                raise AccountLockedError(
                    f"Account locked after {self.MAX_FAILED_ATTEMPTS} failed attempts. "
                    f"Try again in {self.LOCKOUT_DURATION_MINUTES} minutes."
                )

            self._log_event("LOGIN_FAILED", username,
                          f"Attempt {attempts}/{self.MAX_FAILED_ATTEMPTS}")
            raise AuthenticationError(
                f"Invalid username or password. {remaining_attempts} attempts remaining."
            )

        # Successful login
        self.failed_attempts[username] = 0
        self.login_count += 1
        token = hashlib.sha256(
            f"{username}{datetime.now().isoformat()}".encode()
        ).hexdigest()

        self.sessions[token] = {
            "username": username,
            "created_at": datetime.now(),
            "last_active": datetime.now()
        }

        self._log_event("LOGIN_SUCCESS", username,
                       f"Session token: {token[:8]}... | Total logins: {self.login_count}")
        return token

    def validate_session(self, token):
        """Validate a session token. Returns username if valid."""
        if not token or token not in self.sessions:
            return None

        session = self.sessions[token]
        elapsed = datetime.now() - session["created_at"]

        if elapsed > timedelta(hours=self.SESSION_TIMEOUT_HOURS):
            del self.sessions[token]
            self._log_event("SESSION_EXPIRED", session["username"],
                          f"Session expired after {elapsed.seconds // 3600} hours")
            return None

        session["last_active"] = datetime.now()
        return session["username"]

    def logout(self, token):
        """Log out a user by invalidating their session."""
        if token in self.sessions:
            username = self.sessions[token]["username"]
            del self.sessions[token]
            self._log_event("LOGOUT", username, "User logged out")
            return True
        return False

    def get_audit_log(self, username=None, event_type=None):
        """Retrieve audit log entries, optionally filtered."""
        entries = self.audit_log
        if username:
            entries = [e for e in entries if e["username"] == username]
        if event_type:
            entries = [e for e in entries if e["event_type"] == event_type]
        return entries




