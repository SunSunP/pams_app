import re
from datetime import datetime

NI_PATTERN = re.compile(r"^[A-CEGHJ-PR-TW-Z]{2}\d{6}[A-D]$", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_PATTERN = re.compile(r"^\+?\d{7,15}$")


class ValidationError(Exception):
    pass


def validate_ni_number(value: str) -> str:
    if not value or not NI_PATTERN.match(value.strip()):
        raise ValidationError(f"Invalid UK National Insurance number: '{value}'")
    return value.strip().upper()


def validate_email(value: str) -> str:
    if not value or not EMAIL_PATTERN.match(value.strip()):
        raise ValidationError(f"Invalid email address: '{value}'")
    return value.strip().lower()


def validate_phone(value: str) -> str:
    if not value or not PHONE_PATTERN.match(value.strip()):
        raise ValidationError(f"Invalid phone number: '{value}'")
    return value.strip()


def validate_non_empty(value: str, field_name: str) -> str:
    if value is None or not str(value).strip():
        raise ValidationError(f"{field_name} cannot be empty")
    return str(value).strip()


def validate_positive_number(value, field_name: str):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be numeric, got '{value}'")
    if number <= 0:
        raise ValidationError(f"{field_name} must be greater than zero, got {number}")
    return number


def validate_non_negative_number(value, field_name: str):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be numeric, got '{value}'")
    if number < 0:
        raise ValidationError(f"{field_name} cannot be negative, got {number}")
    return number


def validate_date(value: str, field_name: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except (TypeError, ValueError):
        raise ValidationError(
            f"{field_name} must be a valid date in YYYY-MM-DD format, got '{value}'"
        )
    return value


def validate_date_range(start: str, end: str):
    validate_date(start, "start_date")
    validate_date(end, "end_date")
    if datetime.strptime(end, "%Y-%m-%d") <= datetime.strptime(start, "%Y-%m-%d"):
        raise ValidationError("end_date must be after start_date")


def validate_branch(value: str) -> str:
    allowed = {"Bristol", "Cardiff", "London", "Manchester"}
    if value not in allowed:
        raise ValidationError(f"branch_location must be one of {allowed}, got '{value}'")
    return value


def validate_choice(value, allowed: set, field_name: str):
    if value not in allowed:
        raise ValidationError(f"{field_name} must be one of {allowed}, got '{value}'")
    return value
