# PAMS — Paragon Apartment Management System

A desktop application (Python + Tkinter + SQLite) built for the Advanced
Systems Development case study

## Running it

Requires Python 3.10+ with Tkinter (bundled with the standard Windows/macOS
installers; on Linux install via `sudo apt install python3-tk` if missing).
No third-party packages are required — everything uses the standard library.

```bash
python3 seed_data.py   # creates pams.db and loads mock data (run once, or
                        # again any time you want to reset to a clean demo state)
python3 main.py         # launches the desktop app
```

Demo logins (username / password), one per role:

| Username         | Role             | Branch     |
| ---------------- | ---------------- | ---------- |
| fdesk.bristol    | FrontDeskStaff   | Bristol    |
| fdesk.cardiff    | FrontDeskStaff   | Cardiff    |
| finance.london   | FinanceManager   | London     |
| maint.manchester | MaintenanceStaff | Manchester |
| admin.bristol    | Administrator    | Bristol    |
| manager.hq       | Manager          | London     |

Password for every account: `Password`

## Architecture

The codebase is layered to match the class diagram
and to keep business logic independently testable :

```
database.py       SQLite schema + connection helper
models.py         OOP domain classes (User hierarchy, Tenant/Student,
                   Apartment, Lease, MaintenanceRequest, Invoice, Payment).
                   All validation happens here via validators.py, so it is
                   impossible to construct an object with bad data.
validators.py      Reusable field-level validation rules (NI number, email,
                   phone, dates, positive numbers, branch names, etc.)
security.py        Password hashing (PBKDF2-HMAC-SHA256 + per-user salt) and
                   role-based access control (RBAC) via the @requires_role
                   decorator and a PERMISSIONS table.
repositories.py    Data-access layer. Bridges models.py objects and SQLite,
                   enforces RBAC on sensitive operations, and implements the
                   business rules from the brief (20% student discount, 10%
                   early-termination penalty, 5%/0% maintenance cost share,
                   max lease duration per study level, late invoice detection).
seed_data.py        Populates the database with realistic mock tenants,
                   students, apartments, leases, invoices and maintenance
                   requests across all four branches.
gui_app.py          Tkinter desktop GUI. Thin presentation layer only — it
                   calls the repository layer and displays results; it
                   contains no business logic itself.
main.py             Application entry point.
```

## Key Features

- **Account / User management**: five roles (FrontDeskStaff, FinanceManager,
  MaintenanceStaff, Administrator, Manager) implemented as a Python
  inheritance hierarchy (`User` base class), with passwords hashed and RBAC
  enforced centrally in `security.py` — not duplicated per screen.
- **Tenant management**: `Tenant`/`Student` classes, early termination with
  10% penalty, student 20% discount, max lease duration (2 years
  undergrad/masters, 4 years PhD) enforced in `Student.validate_lease_duration`.
- **Apartment management**: registration with location/type/rent/rooms/student
  eligibility, occupancy tracked via `status`.
- **Payment & billing**: invoice generation, payment recording (receipts only
  — no real payment gateway, as specified), automatic late-status detection.
- **Reporting**: occupancy by branch/status, financial summary (collected vs
  pending rent, maintenance costs).
- **Maintenance**: request lifecycle (open → scheduled → resolved), cost and
  time logging, 5%/0% tenant cost share by student status.
- **Non-functional requirements**:
  - _Security_: hashed + salted passwords, RBAC, parameterised SQL throughout
    (no string-built queries), input validation at the model boundary.
  - _Efficiency_: indexed columns for the fields most queried in reporting
    (branch_location, status); thin GUI layer with no business logic to keep
    screens responsive.
  - _Scalability_: layered architecture (GUI / repository / model / database)
    means the SQLite backend could be swapped for a client-server database
    (e.g. PostgreSQL) without changing the GUI or model layers.

## Agile methodology note

This project was developed iteratively in short cycles, each delivering a
vertical slice rather than one layer at a time:

1. **Sprint 1 — Foundations**: schema design (`database.py`), validation
   rules, and password/RBAC security, agreed against the class diagram from
   Element 1.
2. **Sprint 2 — Domain logic**: `models.py` and `repositories.py`,
   implementing the case-study business rules (discounts, penalties,
   maintenance cost split) with manual smoke testing against the sequence
   diagrams produced in Element 1.
3. **Sprint 3 — Mock data & demoability**: `seed_data.py`, so every
   subsequent increment could be demonstrated against realistic data rather
   than an empty database.
4. **Sprint 4 — GUI**: `gui_app.py`, one role's screens at a time
   (Front-desk → Finance → Maintenance → Administrator → Manager), each
   screen built directly against its repository methods.
5. **Sprint 5 — Testing & hardening**: Element 3 test suite (see
   `tests/`), with deliberate bad-data inputs to confirm the validation
   layer rejects them.
