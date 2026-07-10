import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pams.db")


def get_connection():
    """Return a new SQLite connection with foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS branches (
    branch_location TEXT PRIMARY KEY,
    created_date    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    user_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    salt            TEXT NOT NULL,
    full_name       TEXT NOT NULL,
    email           TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN
                        ('FrontDeskStaff','FinanceManager','MaintenanceStaff',
                         'Administrator','Manager')),
    branch_location TEXT NOT NULL REFERENCES branches(branch_location),
    is_active       INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS apartments (
    apartment_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_location    TEXT NOT NULL REFERENCES branches(branch_location),
    apartment_type     TEXT NOT NULL,
    monthly_rent       REAL NOT NULL CHECK (monthly_rent > 0),
    num_rooms          INTEGER NOT NULL CHECK (num_rooms > 0),
    student_eligible   INTEGER NOT NULL DEFAULT 0,
    status             TEXT NOT NULL DEFAULT 'available' CHECK (status IN
                        ('available','occupied','maintenance'))
);
CREATE INDEX IF NOT EXISTS idx_apartments_branch ON apartments(branch_location);
CREATE INDEX IF NOT EXISTS idx_apartments_status ON apartments(status);

CREATE TABLE IF NOT EXISTS tenants (
    tenant_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    ni_number       TEXT UNIQUE NOT NULL,
    full_name       TEXT NOT NULL,
    phone           TEXT NOT NULL,
    email           TEXT NOT NULL,
    occupation      TEXT,
    references_info TEXT,
    is_student      INTEGER NOT NULL DEFAULT 0,
    study_level     TEXT CHECK (study_level IN
                        ('Undergraduate','Masters','PhD') OR study_level IS NULL),
    offer_letter_ref TEXT,
    paired_tenant_id INTEGER REFERENCES tenants(tenant_id),
    branch_location    TEXT NOT NULL REFERENCES branches(branch_location),
    registered_date TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tenants_branch ON tenants(branch_location);

CREATE TABLE IF NOT EXISTS leases (
    lease_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id       INTEGER NOT NULL REFERENCES tenants(tenant_id),
    apartment_id    INTEGER NOT NULL REFERENCES apartments(apartment_id),
    start_date      TEXT NOT NULL,
    end_date        TEXT NOT NULL,
    discount_rate   REAL NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'active' CHECK (status IN
                        ('active','terminated','expired')),
    termination_date TEXT,
    termination_penalty REAL
);
CREATE INDEX IF NOT EXISTS idx_leases_tenant ON leases(tenant_id);
CREATE INDEX IF NOT EXISTS idx_leases_apartment ON leases(apartment_id);

CREATE TABLE IF NOT EXISTS maintenance_requests (
    request_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id       INTEGER NOT NULL REFERENCES tenants(tenant_id),
    apartment_id    INTEGER NOT NULL REFERENCES apartments(apartment_id),
    description     TEXT NOT NULL,
    priority        TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN
                        ('low','medium','high')),
    reported_date   TEXT NOT NULL,
    scheduled_date  TEXT,
    resolved_date   TEXT,
    status          TEXT NOT NULL DEFAULT 'open' CHECK (status IN
                        ('open','scheduled','resolved')),
    total_cost      REAL,
    tenant_share    REAL,
    time_taken_hours REAL,
    logged_by       INTEGER REFERENCES users(user_id)
);
CREATE INDEX IF NOT EXISTS idx_maintenance_status ON maintenance_requests(status);

CREATE TABLE IF NOT EXISTS invoices (
    invoice_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    lease_id        INTEGER NOT NULL REFERENCES leases(lease_id),
    amount          REAL NOT NULL CHECK (amount >= 0),
    issue_date      TEXT NOT NULL,
    due_date        TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN
                        ('pending','paid','late'))
);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);

CREATE TABLE IF NOT EXISTS payments (
    payment_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id      INTEGER NOT NULL REFERENCES invoices(invoice_id),
    amount          REAL NOT NULL CHECK (amount > 0),
    payment_date    TEXT NOT NULL,
    method          TEXT NOT NULL DEFAULT 'bank_transfer'
);

CREATE TABLE IF NOT EXISTS audit_log (
    log_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER REFERENCES users(user_id),
    action          TEXT NOT NULL,
    timestamp       TEXT NOT NULL
);
"""


def init_db(reset: bool = False):
    """Create the database schema. If reset is True, delete any existing file first."""
    if reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = get_connection()
    conn.executescript(SCHEMA)
    for b in ("Bristol", "Cardiff", "London", "Manchester"):
        conn.execute(
            "INSERT OR IGNORE INTO branches (branch_location, created_date) VALUES (?, DATE('now'))",
            (b,)
        )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db(reset=True)
    print(f"Database initialised at {DB_PATH}")