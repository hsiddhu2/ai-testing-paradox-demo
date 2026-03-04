"""
User Manager Module
===================
User profile management with role-based access control.
Moderate complexity — good for showing hotspot analysis.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class UserManager:
    """Manages user profiles and role-based access control."""

    VALID_ROLES = {"admin", "editor", "viewer", "auditor"}

    def __init__(self):
        self.users = {}
        self.role_assignments = {}  # {username: set of roles}
        self.activity_log = []

    def create_profile(self, username, display_name, department):
        """Create a user profile."""
        if not username or not display_name:
            raise ValueError("Username and display name are required")

        if username in self.users:
            raise ValueError(f"User '{username}' already exists")

        self.users[username] = {
            "display_name": display_name,
            "department": department,
            "created_at": datetime.now().isoformat(),
            "is_active": True
        }
        self.role_assignments[username] = {"viewer"}  # Default role
        self._log_activity(username, "PROFILE_CREATED")
        return self.users[username]

    def assign_role(self, username, role, assigned_by):
        """Assign a role to a user. Requires the assigner to have admin role."""
        if username not in self.users:
            raise ValueError(f"User '{username}' not found")

        if role not in self.VALID_ROLES:
            raise ValueError(f"Invalid role '{role}'. Valid: {self.VALID_ROLES}")

        if assigned_by not in self.role_assignments:
            raise ValueError(f"Assigner '{assigned_by}' not found")

        if "admin" not in self.role_assignments.get(assigned_by, set()):
            raise PermissionError(f"User '{assigned_by}' lacks admin privileges")

        self.role_assignments[username].add(role)
        self._log_activity(username, f"ROLE_ASSIGNED: {role} by {assigned_by}")
        return self.role_assignments[username]

    def has_permission(self, username, required_role):
        """Check if a user has a specific role."""
        if username not in self.role_assignments:
            return False
        return required_role in self.role_assignments[username]

    def deactivate_user(self, username, deactivated_by):
        """Deactivate a user account."""
        if username not in self.users:
            raise ValueError(f"User '{username}' not found")

        if not self.has_permission(deactivated_by, "admin"):
            raise PermissionError("Only admins can deactivate users")

        self.users[username]["is_active"] = False
        self._log_activity(username, f"DEACTIVATED by {deactivated_by}")
        return True

    def get_users_by_department(self, department):
        """Get all active users in a department."""
        return {
            name: profile for name, profile in self.users.items()
            if profile["department"] == department and profile["is_active"]
        }

    def _log_activity(self, username, action):
        """Log user management activity."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "action": action
        }
        self.activity_log.append(entry)
        logger.info(f"USER_MGMT: {action} for {username}")
        return entry
