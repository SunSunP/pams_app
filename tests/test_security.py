import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import security as sec


class TestPasswordHashing(unittest.TestCase):
    def test_correct_password_verifies(self):
        pw_hash, salt = sec.hash_password("Pass123!")
        self.assertTrue(sec.verify_password("Pass123!", pw_hash, salt))

    def test_wrong_password_fails(self):
        pw_hash, salt = sec.hash_password("Pass123!")
        self.assertFalse(sec.verify_password("WrongPassword", pw_hash, salt))

    def test_password_is_never_stored_in_plain_text(self):
        pw_hash, salt = sec.hash_password("Pass123!")
        self.assertNotEqual(pw_hash, "Pass123!")
        self.assertNotIn("Pass123!", pw_hash)

    def test_same_password_produces_different_hash_with_different_salt(self):
        hash1, salt1 = sec.hash_password("Pass123!")
        hash2, salt2 = sec.hash_password("Pass123!")
        self.assertNotEqual(salt1, salt2)
        self.assertNotEqual(hash1, hash2)

    def test_empty_password_still_produces_a_hash_not_an_exception(self):
        # An empty password should be rejected at the GUI/form-validation
        pw_hash, salt = sec.hash_password("")
        self.assertTrue(sec.verify_password("", pw_hash, salt))
        self.assertFalse(sec.verify_password("anything", pw_hash, salt))


class TestRolePermissions(unittest.TestCase):
    def test_frontdesk_can_register_tenant(self):
        self.assertTrue(sec.has_permission("FrontDeskStaff", "register_tenant"))

    def test_frontdesk_cannot_record_payment(self):
        self.assertFalse(sec.has_permission("FrontDeskStaff", "record_payment"))

    def test_finance_manager_can_record_payment(self):
        self.assertTrue(sec.has_permission("FinanceManager", "record_payment"))

    def test_finance_manager_cannot_register_tenant(self):
        self.assertFalse(sec.has_permission("FinanceManager", "register_tenant"))

    def test_maintenance_staff_cannot_manage_user_accounts(self):
        self.assertFalse(sec.has_permission("MaintenanceStaff", "manage_user_accounts"))

    def test_administrator_can_manage_user_accounts(self):
        self.assertTrue(sec.has_permission("Administrator", "manage_user_accounts"))

    def test_unknown_role_has_no_permissions(self):
        self.assertFalse(sec.has_permission("SuperUser", "manage_user_accounts"))

    def test_unknown_action_is_denied(self):
        self.assertFalse(sec.has_permission("Administrator", "delete_entire_database"))


class FakeUser:
    def __init__(self, role):
        self.role = role


class TestRequiresRoleDecorator(unittest.TestCase):
    def test_decorator_allows_permitted_role(self):
        @sec.requires_role("register_tenant")
        def do_thing(current_user=None):
            return "done"

        result = do_thing(current_user=FakeUser("FrontDeskStaff"))
        self.assertEqual(result, "done")

    def test_decorator_blocks_unpermitted_role(self):
        @sec.requires_role("register_tenant")
        def do_thing(current_user=None):
            return "done"

        with self.assertRaises(sec.PermissionError_):
            do_thing(current_user=FakeUser("MaintenanceStaff"))

    def test_decorator_blocks_when_no_user_supplied(self):
        @sec.requires_role("register_tenant")
        def do_thing(current_user=None):
            return "done"

        with self.assertRaises(sec.PermissionError_):
            do_thing()


if __name__ == "__main__":
    unittest.main()
