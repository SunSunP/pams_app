import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import validators as v


class TestNiNumberValidation(unittest.TestCase):
    def test_valid_ni_number_accepted(self):
        self.assertEqual(v.validate_ni_number("AB123456C"), "AB123456C")

    def test_lowercase_ni_number_normalised_to_uppercase(self):
        self.assertEqual(v.validate_ni_number("ab123456c"), "AB123456C")

    def test_empty_ni_number_rejected(self):
        with self.assertRaises(v.ValidationError):
            v.validate_ni_number("")

    def test_none_ni_number_rejected(self):
        with self.assertRaises(v.ValidationError):
            v.validate_ni_number(None)

    def test_too_short_ni_number_rejected(self):
        with self.assertRaises(v.ValidationError):
            v.validate_ni_number("AB123C")

    def test_disallowed_prefix_rejected(self):
        # 'D', 'F', 'I', 'Q', 'U', 'V' are never valid first/second letters
        with self.assertRaises(v.ValidationError):
            v.validate_ni_number("QQ123456C")

    def test_invalid_suffix_letter_rejected(self):
        # Suffix must be A-D
        with self.assertRaises(v.ValidationError):
            v.validate_ni_number("AB123456Z")

    def test_sql_injection_style_string_rejected(self):
        with self.assertRaises(v.ValidationError):
            v.validate_ni_number("'; DROP TABLE tenants; --")


class TestEmailValidation(unittest.TestCase):
    def test_valid_email_accepted(self):
        self.assertEqual(v.validate_email("Jane.Doe@Example.com"), "jane.doe@example.com")

    def test_missing_at_symbol_rejected(self):
        with self.assertRaises(v.ValidationError):
            v.validate_email("jane.doe.example.com")

    def test_missing_domain_rejected(self):
        with self.assertRaises(v.ValidationError):
            v.validate_email("jane.doe@")

    def test_empty_email_rejected(self):
        with self.assertRaises(v.ValidationError):
            v.validate_email("")


class TestPhoneValidation(unittest.TestCase):
    def test_valid_uk_mobile_accepted(self):
        self.assertEqual(v.validate_phone("07911123456"), "07911123456")

    def test_international_format_accepted(self):
        self.assertEqual(v.validate_phone("+447911123456"), "+447911123456")

    def test_letters_in_phone_rejected(self):
        with self.assertRaises(v.ValidationError):
            v.validate_phone("0791-PHONE")

    def test_too_short_phone_rejected(self):
        with self.assertRaises(v.ValidationError):
            v.validate_phone("123")


class TestNumberValidation(unittest.TestCase):
    def test_positive_number_accepted(self):
        self.assertEqual(v.validate_positive_number("850.50", "monthly_rent"), 850.50)

    def test_zero_rejected_as_positive(self):
        with self.assertRaises(v.ValidationError):
            v.validate_positive_number(0, "monthly_rent")

    def test_negative_number_rejected_as_positive(self):
        with self.assertRaises(v.ValidationError):
            v.validate_positive_number(-100, "monthly_rent")

    def test_non_numeric_string_rejected(self):
        with self.assertRaises(v.ValidationError):
            v.validate_positive_number("abc", "monthly_rent")

    def test_non_negative_allows_zero(self):
        self.assertEqual(v.validate_non_negative_number(0, "total_cost"), 0.0)

    def test_non_negative_rejects_negative(self):
        with self.assertRaises(v.ValidationError):
            v.validate_non_negative_number(-1, "total_cost")


class TestDateValidation(unittest.TestCase):
    def test_valid_date_accepted(self):
        self.assertEqual(v.validate_date("2026-06-30", "start_date"), "2026-06-30")

    def test_malformed_date_rejected(self):
        with self.assertRaises(v.ValidationError):
            v.validate_date("30/06/2026", "start_date")

    def test_impossible_date_rejected(self):
        with self.assertRaises(v.ValidationError):
            v.validate_date("2026-02-30", "start_date")

    def test_date_range_end_before_start_rejected(self):
        with self.assertRaises(v.ValidationError):
            v.validate_date_range("2026-06-30", "2026-01-01")

    def test_date_range_equal_dates_rejected(self):
        with self.assertRaises(v.ValidationError):
            v.validate_date_range("2026-06-30", "2026-06-30")

    def test_date_range_valid_accepted(self):
        v.validate_date_range("2026-01-01", "2026-06-30")  # should not raise


class TestBranchValidation(unittest.TestCase):
    def test_valid_branch_accepted(self):
        self.assertEqual(v.validate_branch("Bristol"), "Bristol")

    def test_unknown_branch_rejected(self):
        with self.assertRaises(v.ValidationError):
            v.validate_branch("Birmingham")

    def test_case_sensitive_branch_rejected(self):
        with self.assertRaises(v.ValidationError):
            v.validate_branch("bristol")


if __name__ == "__main__":
    unittest.main()
