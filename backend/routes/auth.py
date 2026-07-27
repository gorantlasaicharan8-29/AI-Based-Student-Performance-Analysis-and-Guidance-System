"""
routes/auth.py - Authentication routes (login, register, logout).
Handles role-based JWT token issuance for Student, Teacher, and HOD.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from database import db, User, Student, Notification
from utils.validators import (
    validate_email, validate_password, validate_role,
    validate_required_fields, validate_roll_number, sanitize_string
)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate user and return JWT token."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    ok, msg = validate_required_fields(data, ["email", "password"])
    if not ok:
        return jsonify({"error": msg}), 400

    email = data["email"].strip().lower()
    password = data["password"]

    user = User.query.filter_by(email=email, is_active=True).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    additional_claims = {"role": user.role, "department": user.department or ""}
    token = create_access_token(identity=str(user.id), additional_claims=additional_claims)

    user_dict = user.to_dict()
    # Add student profile id if student
    if user.role == "student" and user.student_profile:
        user_dict["student_id"] = user.student_profile.id
        user_dict["roll_number"] = user.student_profile.roll_number

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": user_dict,
    }), 200


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user (student/teacher/hod)."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    ok, msg = validate_required_fields(data, ["name", "email", "password", "role"])
    if not ok:
        return jsonify({"error": msg}), 400

    if not validate_email(data["email"]):
        return jsonify({"error": "Invalid email address"}), 400

    ok, msg = validate_password(data["password"])
    if not ok:
        return jsonify({"error": msg}), 400

    if not validate_role(data["role"]):
        return jsonify({"error": "Role must be: student, teacher, or hod"}), 400

    email = data["email"].strip().lower()
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    # Create user
    user = User(
        name=sanitize_string(data["name"], 100),
        email=email,
        role=data["role"],
        department=sanitize_string(data.get("department", ""), 100) or None,
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.flush()  # get user.id

    # Create student profile if role is student
    if data["role"] == "student":
        ok, msg = validate_required_fields(data, ["roll_number", "department"])
        if not ok:
            db.session.rollback()
            return jsonify({"error": msg}), 400

        ok, msg = validate_roll_number(data["roll_number"])
        if not ok:
            db.session.rollback()
            return jsonify({"error": msg}), 400

        if Student.query.filter_by(roll_number=data["roll_number"]).first():
            db.session.rollback()
            return jsonify({"error": "Roll number already exists"}), 409

        student = Student(
            user_id=user.id,
            roll_number=data["roll_number"].strip().upper(),
            department=sanitize_string(data["department"], 100),
            semester=int(data.get("semester", 1)),
            batch=sanitize_string(data.get("batch", ""), 20) or None,
        )
        db.session.add(student)

    # Welcome notification
    notif = Notification(
        user_id=user.id,
        title="Welcome to AI Student Performance System!",
        message=f"Hello {user.name}, your {user.role} account has been created successfully.",
        notification_type="success",
    )
    db.session.add(notif)
    db.session.commit()

    return jsonify({
        "message": "Registration successful",
        "user": user.to_dict(),
    }), 201


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    """Get the currently authenticated user's profile."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = user.to_dict()
    if user.role == "student" and user.student_profile:
        data["student_id"] = user.student_profile.id
        data["roll_number"] = user.student_profile.roll_number
        data["semester"] = user.student_profile.semester

    return jsonify({"user": data}), 200


@auth_bp.route("/change-password", methods=["PUT"])
@jwt_required()
def change_password():
    """Change user password."""
    user_id = int(get_jwt_identity())
    data = request.get_json()

    ok, msg = validate_required_fields(data, ["old_password", "new_password"])
    if not ok:
        return jsonify({"error": msg}), 400

    user = User.query.get(user_id)
    if not user.check_password(data["old_password"]):
        return jsonify({"error": "Current password is incorrect"}), 400

    ok, msg = validate_password(data["new_password"])
    if not ok:
        return jsonify({"error": msg}), 400

    user.set_password(data["new_password"])
    db.session.commit()
    return jsonify({"message": "Password changed successfully"}), 200
