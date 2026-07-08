import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pams_app.models as m
import pams_app.validators as v


VALID_TENANT_KWARGS = dict(
    tenant_id=None, ni_number="AB123456C", full_name="John Carter",
    phone="07911123456", email="john.carter@example.com",
    occupation="Accountant", references_info="Employer reference",
    branch_location="Bristol",
)

VALID_STUDENT_KWARGS = dict(
    tenant_id=None, ni_number="EC234567C", full_name="Tom Fletcher",
    phone="07911234567", email="tom.fletcher@example.com",
    occupation="Undergraduate student", references_info="University reference",
    branch_location="London", study_level="Undergraduate",
    offer_letter_ref="UCL-OFFER-2025-0114",
)


class TestTenantCreation(unittest.TestCase):
    def test_valid_tenant_created(self):
        tenant = m.Tenant(**VALID_TENANT_KWARGS)
        self.assertEqual(tenant.ni_number, "AB123456C")
        self.assertFalse(tenant.is_student)

    def test_invalid_ni_number_rejected(self):
        bad = dict(VALID_TENANT_KWARGS, ni_number="NOT-VALID")
        with self.assertRaises(v.ValidationError):
            m.Tenant(**bad)

    def test_invalid_email_rejected(self):
        bad = dict(VALID_TENANT_KWARGS, email="not-an-email")
        with self.assertRaises(v.ValidationError):
            m.Tenant(**bad)

    def test_invalid_phone_rejected(self):
        bad = dict(VALID_TENANT_KWARGS, phone="call-me-maybe")
        with self.assertRaises(v.ValidationError):
            m.Tenant(**bad)

    def test_invalid_branch_rejected(self):
        bad = dict(VALID_TENANT_KWARGS, branch_location="Atlantis")
        with self.assertRaises(v.ValidationError):
            m.Tenant(**bad)

    def test_empty_full_name_rejected(self):
        bad = dict(VALID_TENANT_KWARGS, full_name="   ")
        with self.assertRaises(v.ValidationError):
            m.Tenant(**bad)


class TestTenantBusinessRules(unittest.TestCase):
    def test_early_termination_penalty_is_ten_percent(self):
        tenant = m.Tenant(**VALID_TENANT_KWARGS)
        self.assertAlmostEqual(tenant.early_termination_penalty(1000), 100.0)

    def test_early_termination_penalty_rejects_negative_rent(self):
        tenant = m.Tenant(**VALID_TENANT_KWARGS)
        with self.assertRaises(v.ValidationError):
            tenant.early_termination_penalty(-500)

    def test_non_student_maintenance_share_is_five_percent(self):
        tenant = m.Tenant(**VALID_TENANT_KWARGS)
        self.assertAlmostEqual(tenant.maintenance_share(200), 10.0)

    def test_non_student_maintenance_share_rejects_negative_cost(self):
        tenant = m.Tenant(**VALID_TENANT_KWARGS)
        with self.assertRaises(v.ValidationError):
            tenant.maintenance_share(-50)


class TestStudentCreation(unittest.TestCase):
    def test_valid_student_created(self):
        student = m.Student(**VALID_STUDENT_KWARGS)
        self.assertTrue(student.is_student)
        self.assertEqual(student.max_years_allowed, 2)

    def test_phd_student_max_years_is_four(self):
        kwargs = dict(VALID_STUDENT_KWARGS, study_level="PhD",
                       ni_number="GH345678C")
        student = m.Student(**kwargs)
        self.assertEqual(student.max_years_allowed, 4)

    def test_invalid_study_level_rejected(self):
        bad = dict(VALID_STUDENT_KWARGS, study_level="Foundation Year")
        with self.assertRaises(v.ValidationError):
            m.Student(**bad)

    def test_missing_offer_letter_rejected(self):
        bad = dict(VALID_STUDENT_KWARGS, offer_letter_ref="")
        with self.assertRaises(v.ValidationError):
            m.Student(**bad)

    def test_invalid_ni_number_still_rejected_for_subclass(self):
        bad = dict(VALID_STUDENT_KWARGS, ni_number="BAD")
        with self.assertRaises(v.ValidationError):
            m.Student(**bad)


class TestStudentBusinessRules(unittest.TestCase):
    def test_student_discount_is_twenty_percent(self):
        student = m.Student(**VALID_STUDENT_KWARGS)
        self.assertAlmostEqual(student.discounted_rent(1000), 800.0)

    def test_student_pays_zero_maintenance_share(self):
        student = m.Student(**VALID_STUDENT_KWARGS)
        self.assertEqual(student.maintenance_share(500), 0.0)

    def test_student_lease_within_max_duration_accepted(self):
        student = m.Student(**VALID_STUDENT_KWARGS)  # Undergraduate, max 2 years
        student.validate_lease_duration("2026-01-01", "2027-12-31")  # ~2 yrs, should not raise

    def test_undergraduate_lease_exceeding_two_years_rejected(self):
        student = m.Student(**VALID_STUDENT_KWARGS)  # Undergraduate, max 2 years
        with self.assertRaises(v.ValidationError):
            student.validate_lease_duration("2026-01-01", "2029-06-30")  # ~3.5 yrs

    def test_phd_lease_within_four_years_accepted(self):
        kwargs = dict(VALID_STUDENT_KWARGS, study_level="PhD", ni_number="JK456789C")
        student = m.Student(**kwargs)
        student.validate_lease_duration("2026-01-01", "2029-12-31")  # ~4 yrs, should not raise

    def test_phd_lease_exceeding_four_years_rejected(self):
        kwargs = dict(VALID_STUDENT_KWARGS, study_level="PhD", ni_number="LM567890C")
        student = m.Student(**kwargs)
        with self.assertRaises(v.ValidationError):
            student.validate_lease_duration("2026-01-01", "2031-01-01")  # 5 yrs


class TestApartment(unittest.TestCase):
    def test_valid_apartment_created(self):
        apt = m.Apartment(None, "Bristol", "One-bedroom flat", 850.0, 1, True)
        self.assertEqual(apt.status, "available")

    def test_negative_rent_rejected(self):
        with self.assertRaises(v.ValidationError):
            m.Apartment(None, "Bristol", "Studio", -100, 1)

    def test_zero_rooms_rejected(self):
        with self.assertRaises(v.ValidationError):
            m.Apartment(None, "Bristol", "Studio", 500, 0)

    def test_negative_rooms_rejected(self):
        with self.assertRaises(v.ValidationError):
            m.Apartment(None, "Bristol", "Studio", 500, -2)

    def test_invalid_status_rejected(self):
        with self.assertRaises(v.ValidationError):
            m.Apartment(None, "Bristol", "Studio", 500, 1, status="haunted")

    def test_invalid_branch_rejected(self):
        with self.assertRaises(v.ValidationError):
            m.Apartment(None, "Narnia", "Studio", 500, 1)


class TestLease(unittest.TestCase):
    def test_valid_lease_created(self):
        lease = m.Lease(None, 1, 1, "2026-01-01", "2026-12-31")
        self.assertEqual(lease.status, "active")

    def test_end_date_before_start_date_rejected(self):
        with self.assertRaises(v.ValidationError):
            m.Lease(None, 1, 1, "2026-12-31", "2026-01-01")

    def test_negative_discount_rate_rejected(self):
        with self.assertRaises(v.ValidationError):
            m.Lease(None, 1, 1, "2026-01-01", "2026-12-31", discount_rate=-0.1)

    def test_invalid_status_rejected(self):
        with self.assertRaises(v.ValidationError):
            m.Lease(None, 1, 1, "2026-01-01", "2026-12-31", status="on_hold")

    def test_terminate_early_calculates_penalty(self):
        lease = m.Lease(None, 1, 1, "2026-01-01", "2027-12-31")
        tenant = m.Tenant(**VALID_TENANT_KWARGS)
        penalty, _ = lease.terminate_early("2026-08-01", 1000, tenant)
        self.assertAlmostEqual(penalty, 100.0)
        self.assertEqual(lease.status, "terminated")

    def test_terminate_after_end_date_rejected(self):
        lease = m.Lease(None, 1, 1, "2026-01-01", "2026-06-30")
        tenant = m.Tenant(**VALID_TENANT_KWARGS)
        with self.assertRaises(v.ValidationError):
            lease.terminate_early("2026-12-31", 1000, tenant)


class TestMaintenanceRequest(unittest.TestCase):
    def test_empty_description_rejected(self):
        with self.assertRaises(v.ValidationError):
            m.MaintenanceRequest(None, 1, 1, "   ")

    def test_invalid_priority_rejected(self):
        with self.assertRaises(v.ValidationError):
            m.MaintenanceRequest(None, 1, 1, "Leaking tap", priority="urgent!!")

    def test_resolve_sets_correct_share_for_non_student(self):
        req = m.MaintenanceRequest(None, 1, 1, "Leaking tap")
        tenant = m.Tenant(**VALID_TENANT_KWARGS)
        share = req.resolve("2026-07-01", 200, 2, tenant)
        self.assertAlmostEqual(share, 10.0)
        self.assertEqual(req.status, "resolved")

    def test_resolve_sets_zero_share_for_student(self):
        req = m.MaintenanceRequest(None, 1, 1, "Broken window")
        student = m.Student(**VALID_STUDENT_KWARGS)
        share = req.resolve("2026-07-01", 200, 2, student)
        self.assertEqual(share, 0.0)

    def test_resolve_rejects_negative_cost(self):
        req = m.MaintenanceRequest(None, 1, 1, "Leaking tap")
        tenant = m.Tenant(**VALID_TENANT_KWARGS)
        with self.assertRaises(v.ValidationError):
            req.resolve("2026-07-01", -50, 2, tenant)


class TestInvoiceAndPayment(unittest.TestCase):
    def test_valid_invoice_created(self):
        inv = m.Invoice(None, 1, 850.0, "2026-06-01", "2026-06-30")
        self.assertEqual(inv.status, "pending")

    def test_negative_amount_rejected(self):
        with self.assertRaises(v.ValidationError):
            m.Invoice(None, 1, -10, "2026-06-01", "2026-06-30")

    def test_malformed_due_date_rejected(self):
        with self.assertRaises(v.ValidationError):
            m.Invoice(None, 1, 850.0, "2026-06-01", "not-a-date")

    def test_mark_late_if_overdue(self):
        inv = m.Invoice(None, 1, 850.0, "2026-01-01", "2026-01-31")
        status = inv.mark_late_if_overdue(today="2026-02-15")
        self.assertEqual(status, "late")

    def test_not_marked_late_before_due_date(self):
        inv = m.Invoice(None, 1, 850.0, "2026-06-01", "2026-06-30")
        status = inv.mark_late_if_overdue(today="2026-06-10")
        self.assertEqual(status, "pending")

    def test_payment_less_than_invoice_amount_rejected(self):
        inv = m.Invoice(None, 1, 850.0, "2026-06-01", "2026-06-30")
        with self.assertRaises(v.ValidationError):
            inv.record_payment(500.0)

    def test_full_payment_marks_invoice_paid(self):
        inv = m.Invoice(None, 1, 850.0, "2026-06-01", "2026-06-30")
        inv.record_payment(850.0)
        self.assertEqual(inv.status, "paid")

    def test_payment_with_zero_amount_rejected(self):
        with self.assertRaises(v.ValidationError):
            m.Payment(None, 1, 0, "2026-06-30")

    def test_payment_with_negative_amount_rejected(self):
        with self.assertRaises(v.ValidationError):
            m.Payment(None, 1, -20, "2026-06-30")


if __name__ == "__main__":
    unittest.main()
