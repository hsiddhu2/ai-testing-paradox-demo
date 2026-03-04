"""
User Manager Tests
==================
"""

import pytest
from src.user_manager import UserManager


class TestUserManager:

    def setup_method(self):
        self.um = UserManager()

    def test_create_profile(self):
        profile = self.um.create_profile("john", "John Doe", "Engineering")
        assert profile["display_name"] == "John Doe"
        assert profile["is_active"] is True

    def test_create_duplicate_profile(self):
        self.um.create_profile("john", "John Doe", "Engineering")
        with pytest.raises(ValueError, match="already exists"):
            self.um.create_profile("john", "John Again", "Engineering")

    def test_default_role_is_viewer(self):
        self.um.create_profile("john", "John Doe", "Engineering")
        assert "viewer" in self.um.role_assignments["john"]

    def test_assign_role_by_admin(self):
        self.um.create_profile("admin_user", "Admin", "IT")
        self.um.role_assignments["admin_user"].add("admin")
        self.um.create_profile("john", "John Doe", "Engineering")

        roles = self.um.assign_role("john", "editor", "admin_user")
        assert "editor" in roles

    def test_assign_role_without_admin_fails(self):
        self.um.create_profile("john", "John Doe", "Engineering")
        self.um.create_profile("jane", "Jane Doe", "Engineering")

        with pytest.raises(PermissionError):
            self.um.assign_role("jane", "editor", "john")

    def test_assign_invalid_role(self):
        self.um.create_profile("admin_user", "Admin", "IT")
        self.um.role_assignments["admin_user"].add("admin")
        self.um.create_profile("john", "John Doe", "Engineering")

        with pytest.raises(ValueError, match="Invalid role"):
            self.um.assign_role("john", "superadmin", "admin_user")

    def test_has_permission(self):
        self.um.create_profile("john", "John Doe", "Engineering")
        assert self.um.has_permission("john", "viewer") is True
        assert self.um.has_permission("john", "admin") is False

    def test_deactivate_user(self):
        self.um.create_profile("admin_user", "Admin", "IT")
        self.um.role_assignments["admin_user"].add("admin")
        self.um.create_profile("john", "John Doe", "Engineering")

        result = self.um.deactivate_user("john", "admin_user")
        assert result is True
        assert self.um.users["john"]["is_active"] is False

    def test_get_users_by_department(self):
        self.um.create_profile("john", "John Doe", "Engineering")
        self.um.create_profile("jane", "Jane Doe", "Engineering")
        self.um.create_profile("bob", "Bob Smith", "Marketing")

        eng_users = self.um.get_users_by_department("Engineering")
        assert len(eng_users) == 2
        assert "john" in eng_users
        assert "bob" not in eng_users

    def test_activity_log_tracking(self):
        self.um.create_profile("john", "John Doe", "Engineering")
        assert len(self.um.activity_log) >= 1
        assert self.um.activity_log[0]["action"] == "PROFILE_CREATED"
