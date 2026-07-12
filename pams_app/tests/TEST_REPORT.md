# Element 3 — Test report

## Strategy

Testing is split into two layers, matching the system's architecture:

1. **Automated tests** (`unittest`, Python's standard library — no extra
   install required) exercise `validators.py`, `models.py`, `security.py`
   and `repositories.py` directly. This is where most of the "deliberately
   input out-of-range or incorrect data" requirement is satisfied, because
   it's fast to run dozens of bad-data cases without manually typing them
   into the GUI each time.
2. **Manual GUI tests** (see `manual_gui_test_checklist.md`) confirm the
   same validation is actually wired up to the screens a user interacts
   with, not just to the underlying classes. Screenshot these for the
   report.

Each automated test is also a regression check: if a future change to
`models.py` or `repositories.py` accidentally allows bad data through again,
the test suite will fail and catch it immediately.

## How to run

```bash
cd pams_app
python3 -m unittest discover -s tests -v
```

(No `pip install` needed — everything uses the Python standard library
`unittest` module, so the test suite runs the same way on any marker's
machine without extra setup.)

## Coverage summary

| Test file              | What it covers                                                                                                                                                                                                                                                                       | Test count |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------- |
| `test_validators.py`   | Field-level validation: NI number, email, phone, dates, positive/non-negative numbers, branch names — including malformed input and an SQL-injection-style string                                                                                                                    | 28         |
| `test_models.py`       | Object construction rejects bad data (negative rent, zero rooms, invalid status/priority/study level, end date before start date, etc.); business rule calculations (20% student discount, 10% early-termination penalty, 5%/0% maintenance cost split, 2/4-year max lease duration) | 39         |
| `test_security.py`     | Password hashing never stores plain text, wrong password fails, salts differ per user, RBAC permission table and `@requires_role` decorator both block and allow correctly                                                                                                           | 16         |
| `test_repositories.py` | End-to-end flows against a disposable temp SQLite database: tenant registration, lease creation/termination, maintenance resolution, invoice generation/payment, late-invoice detection — each combined with an RBAC check that the wrong role is blocked                            | 33         |
| **Total**              |                                                                                                                                                                                                                                                                                      | **116**    |

All 116 tests currently pass. Full console output is saved in
`test_run_output.txt` in this folder — screenshot that file (or your own
terminal re-run of it) as evidence for the report, alongside the GUI
screenshots from the manual checklist.

## Example test case

| Test ID | Class / method under test                       | Input                                                                                         | Expected output                                                                        | Actual output                                                                                        |
| ------- | ----------------------------------------------- | --------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| TC-01   | `models.Apartment.__init__`                     | `monthly_rent = -100`                                                                         | Raises `ValidationError("monthly_rent must be greater than zero, got -100.0")`         | Raised as expected — see `test_negative_rent_rejected` in `test_models.py` and `test_run_output.txt` |
| TC-02   | `models.Student.validate_lease_duration`        | Undergraduate student, lease from `2026-01-01` to `2029-06-30` (~3.5 years; max allowed is 2) | Raises `ValidationError` describing the duration exceeded                              | Raised as expected — see `test_undergraduate_lease_exceeding_two_years_rejected`                     |
| TC-03   | `repositories.BillingRepository.record_payment` | Invoice amount £650.00, payment submitted = £500.00                                           | Raises `ValidationError("Payment amount 500.0 is less than the invoice amount 650.0")` | Raised as expected — see `test_underpayment_rejected`                                                |
| TC-04   | `repositories.TenantRepository.register_tenant` | Called with `current_user` = a `FinanceManager`                                               | Raises `PermissionError_` (RBAC blocks the wrong role)                                 | Raised as expected — see `test_finance_manager_cannot_register_tenant`                               |

Use this table format (Test ID / class·method / input / expected / actual)
as the template for the full test-case table in your report — every method
in `test_validators.py`, `test_models.py`, `test_security.py` and
`test_repositories.py` maps to one row.

## Known limitations

- The GUI layer (`gui_app.py`) itself isn't covered by automated tests,
  since Tkinter requires a display and isn't reliably testable headlessly.
  It's covered instead by the manual checklist, which is why both layers
  are included in this report.
- Tests use a disposable temporary database (created and destroyed per test
  in `test_repositories.py`) so they never touch or corrupt the demo
  `pams.db` created by `seed_data.py`.
