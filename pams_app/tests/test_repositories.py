import unittest
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db


class RepositoryTestCase(unittest.TestCase):
    #Base class: points database.DB_PATH at a fresh temp file per test.

    def setUp(self):
        self._tmp_fd, self._tmp_path = tempfile.mkstemp(suffix=".db")
        os.close(self._tmp_fd)
        os.remove(self._tmp_path)  # init_db will recreate it
        self._original_db_path = db.DB_PATH
        db.DB_PATH = self._tmp_path
        db.init_db(reset=True)

        # Import repositories AFTER patching DB_PATH so its module-level
        import repositories as repo
        import models as m
        import security as sec
        import validators as v
        self.repo = repo
        self.m = m
        self.sec = sec
        self.v = v

        self.user_repo = repo.UserRepository()
        self.tenant_repo = repo.TenantRepository()
        self.apartment_repo = repo.ApartmentRepository()
        self.lease_repo = repo.LeaseRepository()
        self.maintenance_repo = repo.MaintenanceRepository()
        self.billing_repo = repo.BillingRepository()
        self.report_repo = repo.ReportRepository()

        # seed minimal users for tests
        self.frontdesk = self.user_repo.create_user(
            "test.frontdesk", "Password", "Test Frontdesk",
            "frontdesk@example.com", "FrontDeskStaff", "Bristol",
            current_user=_AdminBootstrap()
        )
        self.finance = self.user_repo.create_user(
            "test.finance", "Password", "Test Finance",
            "finance@example.com", "FinanceManager", "Bristol",
            current_user=_AdminBootstrap()
        )
        self.maintenance = self.user_repo.create_user(
            "test.maint", "Password", "Test Maintenance",
            "maint@example.com", "MaintenanceStaff", "Bristol",
            current_user=_AdminBootstrap()
        )
        self.admin = self.user_repo.create_user(
            "test.admin", "Password", "Test Admin",
            "admin@example.com", "Administrator", "Bristol",
            current_user=_AdminBootstrap()
        )
        self.manager = self.user_repo.create_user(
            "test.manager", "Password", "Test Manager",
            "manager@example.com", "Manager", "Bristol",
            current_user=_AdminBootstrap()
        )

    def tearDown(self):
        db.DB_PATH = self._original_db_path
        if os.path.exists(self._tmp_path):
            os.remove(self._tmp_path)


class _AdminBootstrap:
    #Stand-in user with Administrator role, used only to seed test fixtures.
    role = "Administrator"


class TestUserRepository(RepositoryTestCase):
    def test_authenticate_with_correct_credentials_succeeds(self):
        user = self.user_repo.authenticate("test.frontdesk", "Password")
        self.assertIsNotNone(user)
        self.assertEqual(user.role, "FrontDeskStaff")

    def test_authenticate_with_wrong_password_fails(self):
        user = self.user_repo.authenticate("test.frontdesk", "WrongPassword")
        self.assertIsNone(user)

    def test_authenticate_with_unknown_username_fails(self):
        user = self.user_repo.authenticate("nobody", "Password")
        self.assertIsNone(user)

    def test_non_administrator_cannot_create_users(self):
        with self.assertRaises(self.sec.PermissionError_):
            self.user_repo.create_user(
                "rogue.user", "Password", "Rogue User", "rogue@example.com",
                "Administrator", "Bristol", current_user=self.frontdesk
            )


class TestTenantRepository(RepositoryTestCase):
    def test_frontdesk_can_register_tenant(self):
        tenant = self.tenant_repo.register_tenant(
            "AB123456C", "Jane Smith", "07911000000", "jane@example.com",
            "Teacher", "ref", "Bristol", current_user=self.frontdesk
        )
        self.assertIsNotNone(tenant.tenant_id)

    def test_finance_manager_cannot_register_tenant(self):
        with self.assertRaises(self.sec.PermissionError_):
            self.tenant_repo.register_tenant(
                "AB123456C", "Jane Smith", "07911000000", "jane@example.com",
                "Teacher", "ref", "Bristol", current_user=self.finance
            )

    def test_bad_ni_number_rejected_even_for_authorised_role(self):
        with self.assertRaises(self.v.ValidationError):
            self.tenant_repo.register_tenant(
                "INVALID-NI", "Jane Smith", "07911000000", "jane@example.com",
                "Teacher", "ref", "Bristol", current_user=self.frontdesk
            )

    def test_student_tenant_round_trips_with_correct_fields(self):
        tenant = self.tenant_repo.register_tenant(
            "EC234567C", "Tom Fletcher", "07911234567", "tom@example.com",
            "Student", "ref", "London", is_student=True,
            study_level="Masters", offer_letter_ref="OFFER-001",
            current_user=self.frontdesk
        )
        fetched = self.tenant_repo.get_tenant_object(tenant.tenant_id)
        self.assertTrue(fetched.is_student)
        self.assertEqual(fetched.study_level, "Masters")


class TestLeaseAndMaintenanceFlow(RepositoryTestCase):
    def setUp(self):
        super().setUp()
        self.apartment = self.apartment_repo.add_apartment(
            "Bristol", "One-bedroom flat", 850.0, 1, True, current_user=self.admin
        )
        self.tenant = self.tenant_repo.register_tenant(
            "AB123456C", "Jane Smith", "07911000000", "jane@example.com",
            "Teacher", "ref", "Bristol", current_user=self.frontdesk
        )
        self.student = self.tenant_repo.register_tenant(
            "EC234567C", "Tom Fletcher", "07911234567", "tom@example.com",
            "Student", "ref", "Bristol", is_student=True,
            study_level="Undergraduate", offer_letter_ref="OFFER-001",
            current_user=self.frontdesk
        )

    def test_creating_lease_marks_apartment_occupied(self):
        lease = self.lease_repo.create_lease(
            self.tenant.tenant_id, self.apartment.apartment_id,
            "2026-01-01", "2026-12-31", current_user=self.frontdesk
        )
        rows = self.apartment_repo.list_apartments()
        occupied = [r for r in rows if r["apartment_id"] == self.apartment.apartment_id][0]
        self.assertEqual(occupied["status"], "occupied")
        self.assertEqual(lease.status, "active")

    def test_student_lease_exceeding_max_duration_rejected(self):
        with self.assertRaises(self.v.ValidationError):
            self.lease_repo.create_lease(
                self.student.tenant_id, self.apartment.apartment_id,
                "2026-01-01", "2030-01-01",  # 4 years, > 2 allowed for undergrad
                current_user=self.frontdesk
            )

    def test_early_termination_applies_ten_percent_penalty_and_frees_apartment(self):
        lease = self.lease_repo.create_lease(
            self.tenant.tenant_id, self.apartment.apartment_id,
            "2026-01-01", "2026-12-31", current_user=self.frontdesk
        )
        penalty, _ = self.lease_repo.terminate_lease_early(
            lease.lease_id, "2026-06-01", current_user=self.frontdesk
        )
        self.assertAlmostEqual(penalty, 85.0)  # 10% of 850
        rows = self.apartment_repo.list_apartments()
        freed = [r for r in rows if r["apartment_id"] == self.apartment.apartment_id][0]
        self.assertEqual(freed["status"], "available")

    def test_maintenance_request_resolution_charges_non_student_five_percent(self):
        req = self.maintenance_repo.log_request(
            self.tenant.tenant_id, self.apartment.apartment_id,
            "Leaking tap", current_user=self.frontdesk
        )
        share = self.maintenance_repo.resolve_request(
            req.request_id, "2026-02-01", 200.0, 1.5, current_user=self.maintenance
        )
        self.assertAlmostEqual(share, 10.0)

    def test_maintenance_request_resolution_charges_student_nothing(self):
        req = self.maintenance_repo.log_request(
            self.student.tenant_id, self.apartment.apartment_id,
            "Broken window", current_user=self.frontdesk
        )
        share = self.maintenance_repo.resolve_request(
            req.request_id, "2026-02-01", 200.0, 1.5, current_user=self.maintenance
        )
        self.assertEqual(share, 0.0)

    def test_frontdesk_cannot_resolve_maintenance_request(self):
        req = self.maintenance_repo.log_request(
            self.tenant.tenant_id, self.apartment.apartment_id,
            "Leaking tap", current_user=self.frontdesk
        )
        with self.assertRaises(self.sec.PermissionError_):
            self.maintenance_repo.resolve_request(
                req.request_id, "2026-02-01", 200.0, 1.5, current_user=self.frontdesk
            )


class TestBillingFlow(RepositoryTestCase):
    def setUp(self):
        super().setUp()
        self.apartment = self.apartment_repo.add_apartment(
            "Bristol", "Studio", 650.0, 1, False, current_user=self.admin
        )
        self.tenant = self.tenant_repo.register_tenant(
            "AB123456C", "Jane Smith", "07911000000", "jane@example.com",
            "Teacher", "ref", "Bristol", current_user=self.frontdesk
        )
        self.lease = self.lease_repo.create_lease(
            self.tenant.tenant_id, self.apartment.apartment_id,
            "2026-01-01", "2026-12-31", current_user=self.frontdesk
        )

    def test_invoice_amount_matches_apartment_rent_when_no_discount(self):
        invoice = self.billing_repo.generate_invoice(
            self.lease.lease_id, "2026-07-31", current_user=self.finance
        )
        self.assertAlmostEqual(invoice.amount, 650.0)

    def test_underpayment_rejected(self):
        invoice = self.billing_repo.generate_invoice(
            self.lease.lease_id, "2026-07-31", current_user=self.finance
        )
        with self.assertRaises(self.v.ValidationError):
            self.billing_repo.record_payment(
                invoice.invoice_id, 500.0, current_user=self.finance
            )

    def test_full_payment_marks_invoice_paid(self):
        invoice = self.billing_repo.generate_invoice(
            self.lease.lease_id, "2026-07-31", current_user=self.finance
        )
        self.billing_repo.record_payment(
            invoice.invoice_id, 650.0, current_user=self.finance
        )
        rows = self.billing_repo.list_invoices()
        updated = [r for r in rows if r["invoice_id"] == invoice.invoice_id][0]
        self.assertEqual(updated["status"], "paid")

    def test_overdue_invoice_flagged_late_on_refresh(self):
        invoice = self.billing_repo.generate_invoice(
            self.lease.lease_id, "2020-01-01",  # already in the past
            current_user=self.finance
        )
        updated_count = self.billing_repo.refresh_late_invoices()
        self.assertGreaterEqual(updated_count, 1)
        rows = self.billing_repo.list_invoices()
        flagged = [r for r in rows if r["invoice_id"] == invoice.invoice_id][0]
        self.assertEqual(flagged["status"], "late")

    def test_maintenance_staff_cannot_generate_invoice(self):
        with self.assertRaises(self.sec.PermissionError_):
            self.billing_repo.generate_invoice(
                self.lease.lease_id, "2026-07-31", current_user=self.maintenance
            )


class TestReportRepository(RepositoryTestCase):
    def test_manager_can_view_occupancy_report(self):
        rows = self.report_repo.occupancy_report(current_user=self.manager)
        self.assertIsInstance(rows, list)

    def test_frontdesk_cannot_view_occupancy_report(self):
        with self.assertRaises(self.sec.PermissionError_):
            self.report_repo.occupancy_report(current_user=self.frontdesk)

    def test_financial_summary_returns_expected_keys(self):
        summary = self.report_repo.financial_summary(current_user=self.manager)
        self.assertEqual(
            set(summary.keys()), {"collected_rent", "pending_rent", "maintenance_cost"}
        )


if __name__ == "__main__":
    unittest.main()
