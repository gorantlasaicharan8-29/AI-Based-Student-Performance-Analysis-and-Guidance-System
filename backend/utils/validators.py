"""
utils/validators.py - Input validation utilities.
All user-supplied data is validated here before touching the DB.
"""

import re
from datetime import datetime


def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    return True, ""


def validate_marks(marks: float, max_marks: float = 100.0) -> tuple[bool, str]:
    try:
        marks = float(marks)
        if marks < 0 or marks > max_marks:
            return False, f"Marks must be between 0 and {max_marks}."
        return True, ""
    except (TypeError, ValueError):
        return False, "Marks must be a valid number."


def validate_attendance(attendance: float) -> tuple[bool, str]:
    try:
        attendance = float(attendance)
        if attendance < 0 or attendance > 100:
            return False, "Attendance must be between 0 and 100."
        return True, ""
    except (TypeError, ValueError):
        return False, "Attendance must be a valid number."


def validate_roll_number(roll: str) -> tuple[bool, str]:
    if not roll or len(roll.strip()) < 3:
        return False, "Roll number must be at least 3 characters."
    if len(roll) > 30:
        return False, "Roll number too long (max 30 characters)."
    return True, ""


def validate_required_fields(data: dict, fields: list) -> tuple[bool, str]:
    """Check that all required fields are present and non-empty."""
    for field in fields:
        if field not in data or data[field] is None or str(data[field]).strip() == "":
            return False, f"Field '{field}' is required."
    return True, ""


def validate_deadline(deadline_str: str) -> tuple[bool, str]:
    """Validate ISO format deadline string."""
    try:
        dt = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
        if dt < datetime.utcnow():
            return False, "Deadline must be in the future."
        return True, ""
    except Exception:
        return False, "Invalid deadline format. Use ISO 8601 (YYYY-MM-DDTHH:MM:SS)."


def validate_role(role: str) -> bool:
    return role in {"student", "teacher", "hod"}


def sanitize_string(s: str, max_len: int = 500) -> str:
    """Basic sanitization — strip whitespace and limit length."""
    return str(s).strip()[:max_len]
