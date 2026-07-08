import hashlib
import hmac
import os
import functools

PBKDF2_ITERATIONS = 200_000


def hash_password(plain_password: str, salt: bytes = None) -> tuple:
    """Return (hash_hex, salt_hex) for the given plain text password."""
    if salt is None:
        salt = os.urandom(16)
    pw_hash = hashlib.pbkdf2_hmac(
        "sha256", plain_password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return pw_hash.hex(), salt.hex()


def verify_password(plain_password: str, stored_hash_hex: str, salt_hex: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    candidate_hash, _ = hash_password(plain_password, salt)
    # Constant-time comparison to avoid timing errors
    return hmac.compare_digest(candidate_hash, stored_hash_hex)


#  Role-based access  

PERMISSIONS = {
    "FrontDeskStaff": {
        "register_tenant", "view_tenant", "register_maintenance_request",
        "register_complaint", "handle_student_request", "view_apartments",
        "assign_apartment",
    },
    "FinanceManager": {
        "generate_invoice", "record_payment", "send_late_notice",
        "view_financial_report", "view_tenant",
    },
    "MaintenanceStaff": {
        "view_maintenance_requests", "prioritise_request", "resolve_request",
        "log_maintenance_cost",
    },
    "Administrator": {
        "manage_user_accounts", "manage_apartments", "track_lease_agreements",
        "generate_branch_report", "view_tenant", "view_apartments",
        "assign_apartment",
    },
    "Manager": {
        "view_occupancy_report", "generate_performance_report",
        "expand_to_new_city", "view_financial_report", "view_apartments",
    },
}


class PermissionError_(Exception):
    """Raised when a user attempts an action outside their role's permissions."""
    pass


def has_permission(role: str, action: str) -> bool:
    return action in PERMISSIONS.get(role, set())


def requires_role(action: str):
    """Decorator used on repository / service methods to enforce RBAC.

    The decorated function must accept a `current_user` keyword/positional
    argument that exposes a `.role` attribute.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if current_user is None:
                for a in args:
                    if hasattr(a, "role"):
                        current_user = a
                        break
            if current_user is None or not has_permission(current_user.role, action):
                raise PermissionError_(
                    f"User does not have permission to perform '{action}'"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator
