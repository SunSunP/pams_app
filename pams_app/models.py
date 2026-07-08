from datetime import datetime
import pams_app.validators as v


#  Users & roles (inheritance hierarchy) 

class User:
    """Base class for all system users. Concrete roles subclass this."""

    ROLE_NAME = "User"

    def __init__(self, user_id, username, full_name, email, branch_location,
                 is_active=True):
        self.user_id = user_id
        self.username = v.validate_non_empty(username, "username")
        self.full_name = v.validate_non_empty(full_name, "full_name")
        self.email = v.validate_email(email)
        self.branch_location = v.validate_branch(branch_location)
        self.is_active = bool(is_active)

    @property
    def role(self):
        return self.ROLE_NAME

    def __repr__(self):
        return f"<{self.role} {self.username} ({self.branch_location})>"


class FrontDeskStaff(User):
    ROLE_NAME = "FrontDeskStaff"


class FinanceManager(User):
    ROLE_NAME = "FinanceManager"


class MaintenanceStaff(User):
    ROLE_NAME = "MaintenanceStaff"


class Administrator(User):
    ROLE_NAME = "Administrator"


class Manager(User):
    ROLE_NAME = "Manager"


ROLE_CLASSES = {
    "FrontDeskStaff": FrontDeskStaff,
    "FinanceManager": FinanceManager,
    "MaintenanceStaff": MaintenanceStaff,
    "Administrator": Administrator,
    "Manager": Manager,
}


def build_user(role: str, **kwargs) -> User:
    """Factory that instantiates the correct User subclass for a given role."""
    cls = ROLE_CLASSES.get(role)
    if cls is None:
        raise v.ValidationError(f"Unknown role '{role}'")
    return cls(**kwargs)


#  Tenant & Student (inheritance) 

MAX_YEARS_BY_LEVEL = {"Undergraduate": 2, "Masters": 2, "PhD": 4}
STUDENT_DISCOUNT_RATE = 0.20
STUDENT_MAINTENANCE_SHARE = 0.0
NON_STUDENT_MAINTENANCE_SHARE = 0.05
EARLY_TERMINATION_PENALTY_RATE = 0.10
EARLY_TERMINATION_NOTICE_DAYS = 30


class Tenant:
    def __init__(self, tenant_id, ni_number, full_name, phone, email,
                 occupation, references_info, branch_location,
                 registered_date=None):
        self.tenant_id = tenant_id
        self.ni_number = v.validate_ni_number(ni_number)
        self.full_name = v.validate_non_empty(full_name, "full_name")
        self.phone = v.validate_phone(phone)
        self.email = v.validate_email(email)
        self.occupation = occupation or ""
        self.references_info = references_info or ""
        self.branch_location = v.validate_branch(branch_location)
        self.registered_date = registered_date or datetime.today().strftime("%Y-%m-%d")

    @property
    def is_student(self):
        return False

    def early_termination_penalty(self, monthly_rent):
        rent = v.validate_positive_number(monthly_rent, "monthly_rent")
        return round(rent * EARLY_TERMINATION_PENALTY_RATE, 2)

    def maintenance_share(self, total_cost):
        cost = v.validate_non_negative_number(total_cost, "total_cost")
        return round(cost * NON_STUDENT_MAINTENANCE_SHARE, 2)

    def __repr__(self):
        return f"<Tenant {self.full_name} ({self.ni_number})>"


class Student(Tenant):
    def __init__(self, *args, study_level, offer_letter_ref,
                 paired_tenant_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.study_level = v.validate_choice(
            study_level, set(MAX_YEARS_BY_LEVEL.keys()), "study_level"
        )
        self.offer_letter_ref = v.validate_non_empty(
            offer_letter_ref, "offer_letter_ref"
        )
        self.paired_tenant_id = paired_tenant_id

    @property
    def is_student(self):
        return True

    @property
    def max_years_allowed(self):
        return MAX_YEARS_BY_LEVEL[self.study_level]

    def discounted_rent(self, monthly_rent):
        rent = v.validate_positive_number(monthly_rent, "monthly_rent")
        return round(rent * (1 - STUDENT_DISCOUNT_RATE), 2)

    def maintenance_share(self, total_cost):
        # Students pay nothing towards maintenance costs.
        v.validate_non_negative_number(total_cost, "total_cost")
        return 0.0

    def validate_lease_duration(self, start_date, end_date):
        v.validate_date_range(start_date, end_date)
        years = (datetime.strptime(end_date, "%Y-%m-%d") -
                 datetime.strptime(start_date, "%Y-%m-%d")).days / 365.25
        if years > self.max_years_allowed + 0.05:  # small tolerance
            raise v.ValidationError(
                f"Lease duration ({years:.1f} yrs) exceeds the maximum "
                f"{self.max_years_allowed} years allowed for {self.study_level} students"
            )


#  Apartment 

class Apartment:
    VALID_STATUS = {"available", "occupied", "maintenance"}

    def __init__(self, apartment_id, branch_location, apartment_type,
                 monthly_rent, num_rooms, student_eligible=False,
                 status="available"):
        self.apartment_id = apartment_id
        self.branch_location = v.validate_branch(branch_location)
        self.apartment_type = v.validate_non_empty(apartment_type, "apartment_type")
        self.monthly_rent = v.validate_positive_number(monthly_rent, "monthly_rent")
        self.num_rooms = int(v.validate_positive_number(num_rooms, "num_rooms"))
        self.student_eligible = bool(student_eligible)
        self.status = v.validate_choice(status, self.VALID_STATUS, "status")

    def __repr__(self):
        return f"<Apartment #{self.apartment_id} {self.apartment_type} {self.branch_location}>"


#  Lease 

class Lease:
    VALID_STATUS = {"active", "terminated", "expired"}

    def __init__(self, lease_id, tenant_id, apartment_id, start_date, end_date,
                 discount_rate=0.0, status="active",
                 termination_date=None, termination_penalty=None):
        v.validate_date_range(start_date, end_date)
        self.lease_id = lease_id
        self.tenant_id = tenant_id
        self.apartment_id = apartment_id
        self.start_date = start_date
        self.end_date = end_date
        self.discount_rate = v.validate_non_negative_number(discount_rate, "discount_rate")
        self.status = v.validate_choice(status, self.VALID_STATUS, "status")
        self.termination_date = termination_date
        self.termination_penalty = termination_penalty

    def terminate_early(self, termination_date, monthly_rent, tenant: Tenant):
        v.validate_date(termination_date, "termination_date")
        if datetime.strptime(termination_date, "%Y-%m-%d") >= \
                datetime.strptime(self.end_date, "%Y-%m-%d"):
            raise v.ValidationError("termination_date must be before the lease end_date")
        notice_days = (datetime.strptime(termination_date, "%Y-%m-%d") -
                       datetime.today()).days
        # Penalty still applies per the business rule even if notice is short
        self.termination_penalty = tenant.early_termination_penalty(monthly_rent)
        self.termination_date = termination_date
        self.status = "terminated"
        return self.termination_penalty, notice_days >= EARLY_TERMINATION_NOTICE_DAYS


#  MaintenanceRequest 

class MaintenanceRequest:
    VALID_PRIORITY = {"low", "medium", "high"}
    VALID_STATUS = {"open", "scheduled", "resolved"}

    def __init__(self, request_id, tenant_id, apartment_id, description,
                 reported_date=None, priority="medium", status="open",
                 scheduled_date=None, resolved_date=None, total_cost=None,
                 tenant_share=None, time_taken_hours=None, logged_by=None):
        self.request_id = request_id
        self.tenant_id = tenant_id
        self.apartment_id = apartment_id
        self.description = v.validate_non_empty(description, "description")
        self.reported_date = reported_date or datetime.today().strftime("%Y-%m-%d")
        self.priority = v.validate_choice(priority, self.VALID_PRIORITY, "priority")
        self.status = v.validate_choice(status, self.VALID_STATUS, "status")
        self.scheduled_date = scheduled_date
        self.resolved_date = resolved_date
        self.total_cost = total_cost
        self.tenant_share = tenant_share
        self.time_taken_hours = time_taken_hours
        self.logged_by = logged_by

    def resolve(self, resolved_date, total_cost, time_taken_hours, tenant: Tenant):
        v.validate_date(resolved_date, "resolved_date")
        cost = v.validate_non_negative_number(total_cost, "total_cost")
        hours = v.validate_non_negative_number(time_taken_hours, "time_taken_hours")
        self.resolved_date = resolved_date
        self.total_cost = cost
        self.time_taken_hours = hours
        self.tenant_share = tenant.maintenance_share(cost)
        self.status = "resolved"
        return self.tenant_share


#  Invoice & Payment 

class Invoice:
    VALID_STATUS = {"pending", "paid", "late"}

    def __init__(self, invoice_id, lease_id, amount, issue_date, due_date,
                 status="pending"):
        self.invoice_id = invoice_id
        self.lease_id = lease_id
        self.amount = v.validate_non_negative_number(amount, "amount")
        v.validate_date(issue_date, "issue_date")
        v.validate_date(due_date, "due_date")
        self.issue_date = issue_date
        self.due_date = due_date
        self.status = v.validate_choice(status, self.VALID_STATUS, "status")

    def mark_late_if_overdue(self, today=None):
        today = today or datetime.today().strftime("%Y-%m-%d")
        if self.status == "pending" and \
                datetime.strptime(today, "%Y-%m-%d") > datetime.strptime(self.due_date, "%Y-%m-%d"):
            self.status = "late"
        return self.status

    def record_payment(self, amount):
        paid = v.validate_positive_number(amount, "amount")
        if paid < self.amount:
            raise v.ValidationError(
                f"Payment amount {paid} is less than the invoice amount {self.amount}"
            )
        self.status = "paid"


class Payment:
    def __init__(self, payment_id, invoice_id, amount, payment_date,
                 method="bank_transfer"):
        self.payment_id = payment_id
        self.invoice_id = invoice_id
        self.amount = v.validate_positive_number(amount, "amount")
        v.validate_date(payment_date, "payment_date")
        self.payment_date = payment_date
        self.method = v.validate_non_empty(method, "method")
