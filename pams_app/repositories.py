from datetime import datetime
import database as db
import models as m
import security as sec
import validators as v


#  Users 

class UserRepository:
    def authenticate(self, username, password):
        conn = db.get_connection()
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? AND is_active = 1", (username,)
        ).fetchone()
        conn.close()
        if row and sec.verify_password(password, row["password_hash"], row["salt"]):
            return m.build_user(
                row["role"], user_id=row["user_id"], username=row["username"],
                full_name=row["full_name"], email=row["email"],
                branch_location=row["branch_location"], is_active=row["is_active"]
            )
        return None

    @sec.requires_role("manage_user_accounts")
    def create_user(self, username, password, full_name, email, role,
                     branch_location, current_user=None):
        user = m.build_user(
            role, user_id=None, username=username, full_name=full_name,
            email=email, branch_location=branch_location
        )
        pw_hash, salt = sec.hash_password(password)
        conn = db.get_connection()
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, salt, full_name, email, "
            "role, branch_location) VALUES (?,?,?,?,?,?,?)",
            (user.username, pw_hash, salt, user.full_name, user.email,
             role, user.branch_location)
        )
        conn.commit()
        user.user_id = cur.lastrowid
        conn.close()
        return user

    def list_users(self, branch_location=None):
        conn = db.get_connection()
        if branch_location:
            rows = conn.execute(
                "SELECT * FROM users WHERE branch_location = ?", (branch_location,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM users").fetchall()
        conn.close()
        return rows


#  Tenants 

class TenantRepository:
    @sec.requires_role("register_tenant")
    def register_tenant(self, ni_number, full_name, phone, email, occupation,
                         references_info, branch_location, is_student=False,
                         study_level=None, offer_letter_ref=None,
                         paired_tenant_id=None, current_user=None):
        if is_student:
            tenant = m.Student(
                None, ni_number, full_name, phone, email, occupation,
                references_info, branch_location, study_level=study_level,
                offer_letter_ref=offer_letter_ref, paired_tenant_id=paired_tenant_id
            )
        else:
            tenant = m.Tenant(
                None, ni_number, full_name, phone, email, occupation,
                references_info, branch_location
            )
        conn = db.get_connection()
        cur = conn.execute(
            "INSERT INTO tenants (ni_number, full_name, phone, email, occupation, "
            "references_info, is_student, study_level, offer_letter_ref, "
            "paired_tenant_id, branch_location, registered_date) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (tenant.ni_number, tenant.full_name, tenant.phone, tenant.email,
             tenant.occupation, tenant.references_info, int(is_student),
             study_level, offer_letter_ref, paired_tenant_id, branch_location,
             tenant.registered_date)
        )
        conn.commit()
        tenant.tenant_id = cur.lastrowid
        conn.close()
        return tenant

    def list_tenants(self, branch_location=None):
        conn = db.get_connection()
        if branch_location:
            rows = conn.execute(
                "SELECT * FROM tenants WHERE branch_location = ?", (branch_location,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM tenants").fetchall()
        conn.close()
        return rows

    def get_tenant_object(self, tenant_id):
        conn = db.get_connection()
        row = conn.execute(
            "SELECT * FROM tenants WHERE tenant_id = ?", (tenant_id,)
        ).fetchone()
        conn.close()
        if row is None:
            return None
        if row["is_student"]:
            return m.Student(
                row["tenant_id"], row["ni_number"], row["full_name"], row["phone"],
                row["email"], row["occupation"], row["references_info"],
                row["branch_location"], registered_date=row["registered_date"],
                study_level=row["study_level"], offer_letter_ref=row["offer_letter_ref"],
                paired_tenant_id=row["paired_tenant_id"]
            )
        return m.Tenant(
            row["tenant_id"], row["ni_number"], row["full_name"], row["phone"],
            row["email"], row["occupation"], row["references_info"],
            row["branch_location"], registered_date=row["registered_date"]
        )


#  Apartments 

class ApartmentRepository:
    @sec.requires_role("manage_apartments")
    def add_apartment(self, branch_location, apartment_type, monthly_rent,
                       num_rooms, student_eligible=False, current_user=None):
        apt = m.Apartment(None, branch_location, apartment_type, monthly_rent,
                           num_rooms, student_eligible)
        conn = db.get_connection()
        cur = conn.execute(
            "INSERT INTO apartments (branch_location, apartment_type, monthly_rent, "
            "num_rooms, student_eligible, status) VALUES (?,?,?,?,?,'available')",
            (apt.branch_location, apt.apartment_type, apt.monthly_rent,
             apt.num_rooms, int(apt.student_eligible))
        )
        conn.commit()
        apt.apartment_id = cur.lastrowid
        conn.close()
        return apt

    def list_apartments(self, branch_location=None, status=None):
        conn = db.get_connection()
        query = "SELECT * FROM apartments WHERE 1=1"
        params = []
        if branch_location:
            query += " AND branch_location = ?"
            params.append(branch_location)
        if status:
            query += " AND status = ?"
            params.append(status)
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return rows

    def set_status(self, apartment_id, status):
        v.validate_choice(status, m.Apartment.VALID_STATUS, "status")
        conn = db.get_connection()
        conn.execute(
            "UPDATE apartments SET status = ? WHERE apartment_id = ?",
            (status, apartment_id)
        )
        conn.commit()
        conn.close()


#  Leases 

class LeaseRepository:
    def __init__(self):
        self.tenant_repo = TenantRepository()
        self.apartment_repo = ApartmentRepository()

    @sec.requires_role("assign_apartment")
    def create_lease(self, tenant_id, apartment_id, start_date, end_date,
                      current_user=None):
        tenant = self.tenant_repo.get_tenant_object(tenant_id)
        if tenant is None:
            raise v.ValidationError(f"No tenant with id {tenant_id}")
        discount_rate = m.STUDENT_DISCOUNT_RATE if tenant.is_student else 0.0
        if tenant.is_student:
            tenant.validate_lease_duration(start_date, end_date)
        lease = m.Lease(None, tenant_id, apartment_id, start_date, end_date,
                         discount_rate=discount_rate)
        conn = db.get_connection()
        cur = conn.execute(
            "INSERT INTO leases (tenant_id, apartment_id, start_date, end_date, "
            "discount_rate, status) VALUES (?,?,?,?,?,'active')",
            (tenant_id, apartment_id, start_date, end_date, discount_rate)
        )
        conn.commit()
        lease.lease_id = cur.lastrowid
        conn.close()
        self.apartment_repo.set_status(apartment_id, "occupied")
        return lease

    def list_leases(self):
        conn = db.get_connection()
        rows = conn.execute(
            "SELECT l.*, t.full_name AS tenant_name, a.apartment_type, "
            "a.branch_location, a.monthly_rent FROM leases l "
            "JOIN tenants t ON l.tenant_id = t.tenant_id "
            "JOIN apartments a ON l.apartment_id = a.apartment_id"
        ).fetchall()
        conn.close()
        return rows

    def terminate_lease_early(self, lease_id, termination_date, current_user=None):
        conn = db.get_connection()
        row = conn.execute(
            "SELECT l.*, a.monthly_rent FROM leases l "
            "JOIN apartments a ON l.apartment_id = a.apartment_id "
            "WHERE l.lease_id = ?", (lease_id,)
        ).fetchone()
        if row is None:
            conn.close()
            raise v.ValidationError(f"No lease with id {lease_id}")
        tenant = self.tenant_repo.get_tenant_object(row["tenant_id"])
        lease = m.Lease(row["lease_id"], row["tenant_id"], row["apartment_id"],
                         row["start_date"], row["end_date"], row["discount_rate"],
                         row["status"])
        penalty, gave_enough_notice = lease.terminate_early(
            termination_date, row["monthly_rent"], tenant
        )
        conn.execute(
            "UPDATE leases SET status='terminated', termination_date=?, "
            "termination_penalty=? WHERE lease_id=?",
            (termination_date, penalty, lease_id)
        )
        conn.commit()
        conn.close()
        self.apartment_repo.set_status(row["apartment_id"], "available")
        return penalty, gave_enough_notice


#  Maintenance 

class MaintenanceRepository:
    def __init__(self):
        self.tenant_repo = TenantRepository()

    @sec.requires_role("register_maintenance_request")
    def log_request(self, tenant_id, apartment_id, description, priority="medium",
                     current_user=None):
        req = m.MaintenanceRequest(None, tenant_id, apartment_id, description,
                                    priority=priority,
                                    logged_by=getattr(current_user, "user_id", None))
        conn = db.get_connection()
        cur = conn.execute(
            "INSERT INTO maintenance_requests (tenant_id, apartment_id, description, "
            "priority, reported_date, status, logged_by) VALUES (?,?,?,?,?,'open',?)",
            (tenant_id, apartment_id, req.description, req.priority,
             req.reported_date, req.logged_by)
        )
        conn.commit()
        req.request_id = cur.lastrowid
        conn.close()
        return req

    def list_requests(self, status=None):
        conn = db.get_connection()
        if status:
            rows = conn.execute(
                "SELECT * FROM maintenance_requests WHERE status = ?", (status,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM maintenance_requests").fetchall()
        conn.close()
        return rows

    @sec.requires_role("resolve_request")
    def resolve_request(self, request_id, resolved_date, total_cost,
                         time_taken_hours, current_user=None):
        conn = db.get_connection()
        row = conn.execute(
            "SELECT * FROM maintenance_requests WHERE request_id = ?", (request_id,)
        ).fetchone()
        if row is None:
            conn.close()
            raise v.ValidationError(f"No maintenance request with id {request_id}")
        tenant = self.tenant_repo.get_tenant_object(row["tenant_id"])
        req = m.MaintenanceRequest(
            row["request_id"], row["tenant_id"], row["apartment_id"],
            row["description"], row["reported_date"], row["priority"], row["status"]
        )
        tenant_share = req.resolve(resolved_date, total_cost, time_taken_hours, tenant)
        conn.execute(
            "UPDATE maintenance_requests SET status='resolved', resolved_date=?, "
            "total_cost=?, tenant_share=?, time_taken_hours=? WHERE request_id=?",
            (resolved_date, req.total_cost, tenant_share, req.time_taken_hours, request_id)
        )
        conn.commit()
        conn.close()
        return tenant_share


#  Billing 

class BillingRepository:
    @sec.requires_role("generate_invoice")
    def generate_invoice(self, lease_id, due_date, current_user=None):
        conn = db.get_connection()
        lease_row = conn.execute(
            "SELECT l.*, a.monthly_rent FROM leases l "
            "JOIN apartments a ON l.apartment_id = a.apartment_id "
            "WHERE l.lease_id = ?", (lease_id,)
        ).fetchone()
        if lease_row is None:
            conn.close()
            raise v.ValidationError(f"No lease with id {lease_id}")
        amount = round(lease_row["monthly_rent"] * (1 - lease_row["discount_rate"]), 2)
        issue_date = datetime.today().strftime("%Y-%m-%d")
        invoice = m.Invoice(None, lease_id, amount, issue_date, due_date)
        cur = conn.execute(
            "INSERT INTO invoices (lease_id, amount, issue_date, due_date, status) "
            "VALUES (?,?,?,?,'pending')",
            (lease_id, amount, issue_date, due_date)
        )
        conn.commit()
        invoice.invoice_id = cur.lastrowid
        conn.close()
        return invoice

    @sec.requires_role("record_payment")
    def record_payment(self, invoice_id, amount, method="bank_transfer", current_user=None):
        conn = db.get_connection()
        try:
            row = conn.execute("SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id,)).fetchone()
            if row is None:
                raise v.ValidationError(f"No invoice with id {invoice_id}")
            invoice = m.Invoice(row["invoice_id"], row["lease_id"], row["amount"],
                                row["issue_date"], row["due_date"], row["status"])
            invoice.record_payment(amount)
            payment_date = datetime.today().strftime("%Y-%m-%d")
            payment = m.Payment(None, invoice_id, amount, payment_date, method)
            conn.execute(
                "INSERT INTO payments (invoice_id, amount, payment_date, method) "
                "VALUES (?,?,?,?)", (invoice_id, payment.amount, payment_date, method)
            )
            conn.execute(
                "UPDATE invoices SET status='paid' WHERE invoice_id=?", (invoice_id,)
            )
            conn.commit()
            return payment
        finally:
            conn.close()

    def refresh_late_invoices(self):
        #Marks any pending invoice past its due date as 'late' 
        conn = db.get_connection()
        today = datetime.today().strftime("%Y-%m-%d")
        cur = conn.execute(
            "UPDATE invoices SET status='late' WHERE status='pending' AND due_date < ?",
            (today,)
        )
        conn.commit()
        updated = cur.rowcount
        conn.close()
        return updated

    def list_invoices(self, status=None):
        conn = db.get_connection()
        if status:
            rows = conn.execute(
                "SELECT * FROM invoices WHERE status = ?", (status,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM invoices").fetchall()
        conn.close()
        return rows


#  Reporting 

class ReportRepository:
    @sec.requires_role("view_occupancy_report")
    def occupancy_report(self, branch_location=None, current_user=None):
        conn = db.get_connection()
        query = ("SELECT branch_location, status, COUNT(*) AS total "
                  "FROM apartments WHERE 1=1")
        params = []
        if branch_location:
            query += " AND branch_location = ?"
            params.append(branch_location)
        query += " GROUP BY branch_location, status"
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return rows

    @sec.requires_role("view_financial_report")
    def financial_summary(self, current_user=None):
        conn = db.get_connection()
        collected = conn.execute(
            "SELECT COALESCE(SUM(amount),0) AS total FROM invoices WHERE status='paid'"
        ).fetchone()["total"]
        pending = conn.execute(
            "SELECT COALESCE(SUM(amount),0) AS total FROM invoices WHERE status IN "
            "('pending','late')"
        ).fetchone()["total"]
        maintenance_cost = conn.execute(
            "SELECT COALESCE(SUM(total_cost),0) AS total FROM maintenance_requests "
            "WHERE status='resolved'"
        ).fetchone()["total"]
        conn.close()
        return {
            "collected_rent": collected,
            "pending_rent": pending,
            "maintenance_cost": maintenance_cost,
        }
