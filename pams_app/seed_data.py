from datetime import date, timedelta
import pams_app.database as db
import pams_app.security as sec
import pams_app.repositories as repo

BRANCHES = ["Bristol", "Cardiff", "London", "Manchester"]

USERS = [
    # username, password, full_name, email, role, branch
    ("fdesk.bristol", "Password", "Alice Front", "alice.front@paragon.co.uk", "FrontDeskStaff", "Bristol"),
    ("fdesk.cardiff", "Password", "Owen Reece", "owen.reece@paragon.co.uk", "FrontDeskStaff", "Cardiff"),
    ("finance.london", "Password", "Priya Shah", "priya.shah@paragon.co.uk", "FinanceManager", "London"),
    ("maint.manchester", "Password", "Sam Doyle", "sam.doyle@paragon.co.uk", "MaintenanceStaff", "Manchester"),
    ("admin.bristol", "Password", "Helen Cross", "helen.cross@paragon.co.uk", "Administrator", "Bristol"),
    ("manager.hq", "Password", "David Kelly", "david.kelly@paragon.co.uk", "Manager", "London"),
]

TENANTS = [
    # ni, name, phone, email, occupation, refs, branch, is_student, study_level, offer_letter
    ("AB123456C", "John Carter", "07911123456", "john.carter@example.com",
     "Accountant", "Previous landlord reference on file", "Bristol", False, None, None),
    ("AC234567C", "Maria Lopez", "07911234567", "maria.lopez@example.com",
     "Nurse", "Employer reference on file", "Cardiff", False, None, None),
    ("AE345678C", "Tom Fletcher", "07911345678", "tom.fletcher@example.com",
     "Undergraduate student", "University reference", "London", True, "Undergraduate", "UCL-OFFER-2025-0114"),
    ("AG456789C", "Aisha Khan", "07911456789", "aisha.khan@example.com",
     "Master's student", "University reference", "Manchester", True, "Masters", "UOM-OFFER-2025-0876"),
    ("AH567890C", "Liam O'Brien", "07911567890", "liam.obrien@example.com",
     "PhD student", "University reference", "Bristol", True, "PhD", "UOB-OFFER-2025-0341"),
]

APARTMENTS = [
    # branch, type, rent, rooms, student_eligible
    ("Bristol", "One-bedroom flat", 850.0, 1, True),
    ("Bristol", "Two-bedroom house", 1200.0, 2, False),
    ("Cardiff", "Studio", 650.0, 1, True),
    ("London", "Two-bedroom flat", 1800.0, 2, True),
    ("London", "Three-bedroom house", 2400.0, 3, False),
    ("Manchester", "One-bedroom flat", 750.0, 1, True),
    ("Manchester", "Two-bedroom house", 1100.0, 2, False),
]


def seed():
    db.init_db(reset=True)
    conn = db.get_connection()

    user_repo = repo.UserRepository()
    for username, password, full_name, email, role, branch in USERS:
        pw_hash, salt = sec.hash_password(password)
        conn.execute(
            "INSERT INTO users (username, password_hash, salt, full_name, email, "
            "role, branch_location) VALUES (?,?,?,?,?,?,?)",
            (username, pw_hash, salt, full_name, email, role, branch)
        )
    conn.commit()

    apt_ids = []
    for branch, atype, rent, rooms, student_ok in APARTMENTS:
        cur = conn.execute(
            "INSERT INTO apartments (branch_location, apartment_type, monthly_rent, "
            "num_rooms, student_eligible, status) VALUES (?,?,?,?,?,'available')",
            (branch, atype, rent, rooms, int(student_ok))
        )
        apt_ids.append(cur.lastrowid)
    conn.commit()

    tenant_ids = []
    today = date.today()
    for (ni, name, phone, email, occ, refs, branch, is_student,
         study_level, offer_ref) in TENANTS:
        cur = conn.execute(
            "INSERT INTO tenants (ni_number, full_name, phone, email, occupation, "
            "references_info, is_student, study_level, offer_letter_ref, "
            "paired_tenant_id, branch_location, registered_date) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (ni, name, phone, email, occ, refs, int(is_student), study_level,
             offer_ref, None, branch, today.strftime("%Y-%m-%d"))
        )
        tenant_ids.append(cur.lastrowid)
    conn.commit()

    # Create a lease for each tenant against a matching-branch apartment
    lease_pairs = [
        (tenant_ids[0], apt_ids[1], 0.0),   # John Carter -> Bristol 2-bed, non-student
        (tenant_ids[1], apt_ids[2], 0.0),   # Maria Lopez -> Cardiff studio, non-student
        (tenant_ids[2], apt_ids[3], 0.20),  # Tom Fletcher -> London 2-bed, student discount
        (tenant_ids[3], apt_ids[5], 0.20),  # Aisha Khan -> Manchester 1-bed, student
        (tenant_ids[4], apt_ids[0], 0.20),  # Liam O'Brien -> Bristol 1-bed, PhD student
    ]
    lease_ids = []
    for tenant_id, apartment_id, discount in lease_pairs:
        start = today - timedelta(days=60)
        end = today + timedelta(days=300)
        cur = conn.execute(
            "INSERT INTO leases (tenant_id, apartment_id, start_date, end_date, "
            "discount_rate, status) VALUES (?,?,?,?,?,'active')",
            (tenant_id, apartment_id, start.strftime("%Y-%m-%d"),
             end.strftime("%Y-%m-%d"), discount)
        )
        lease_ids.append(cur.lastrowid)
        conn.execute(
            "UPDATE apartments SET status='occupied' WHERE apartment_id=?",
            (apartment_id,)
        )
    conn.commit()

    # Invoices: one paid, one pending, one deliberately overdue/late
    invoice_plan = [
        (lease_ids[0], 850.0, today - timedelta(days=40), today - timedelta(days=10), "paid"),
        (lease_ids[1], 650.0, today - timedelta(days=10), today + timedelta(days=20), "pending"),
        (lease_ids[2], 1440.0, today - timedelta(days=45), today - timedelta(days=15), "late"),
    ]
    for lease_id, amount, issue, due, status in invoice_plan:
        cur = conn.execute(
            "INSERT INTO invoices (lease_id, amount, issue_date, due_date, status) "
            "VALUES (?,?,?,?,?)",
            (lease_id, amount, issue.strftime("%Y-%m-%d"), due.strftime("%Y-%m-%d"), status)
        )
        if status == "paid":
            conn.execute(
                "INSERT INTO payments (invoice_id, amount, payment_date, method) "
                "VALUES (?,?,?,?)",
                (cur.lastrowid, amount, (due - timedelta(days=2)).strftime("%Y-%m-%d"),
                 "bank_transfer")
            )
    conn.commit()

    # Maintenance requests: one open, one resolved (non-student), one resolved (student)
    conn.execute(
        "INSERT INTO maintenance_requests (tenant_id, apartment_id, description, "
        "priority, reported_date, status) VALUES (?,?,?,?,?,'open')",
        (tenant_ids[0], apt_ids[1], "Leaking kitchen tap", "medium",
         today.strftime("%Y-%m-%d"))
    )
    conn.execute(
        "INSERT INTO maintenance_requests (tenant_id, apartment_id, description, "
        "priority, reported_date, status, resolved_date, total_cost, tenant_share, "
        "time_taken_hours) VALUES (?,?,?,?,?,'resolved',?,?,?,?)",
        (tenant_ids[1], apt_ids[2], "Broken window latch", "low",
         (today - timedelta(days=20)).strftime("%Y-%m-%d"),
         (today - timedelta(days=18)).strftime("%Y-%m-%d"), 120.0, 6.0, 1.5)
    )
    conn.execute(
        "INSERT INTO maintenance_requests (tenant_id, apartment_id, description, "
        "priority, reported_date, status, resolved_date, total_cost, tenant_share, "
        "time_taken_hours) VALUES (?,?,?,?,?,'resolved',?,?,?,?)",
        (tenant_ids[2], apt_ids[3], "Heating not working", "high",
         (today - timedelta(days=12)).strftime("%Y-%m-%d"),
         (today - timedelta(days=11)).strftime("%Y-%m-%d"), 300.0, 0.0, 3.0)
    )
    conn.commit()
    conn.close()
    print("Mock data seeded successfully.")
    print("Demo logins (username / password):")
    for username, password, _, _, role, branch in USERS:
        print(f"  {username:18s} / {password:10s}  ({role}, {branch})")


if __name__ == "__main__":
    seed()
