"""
routes/teacher.py - Teacher-facing API routes.
Covers: student list, marks entry, assignment CRUD, submission review, notifications.
"""

import json
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from database import db, User, Student, Subject, Mark, Assignment, Submission, Notification
from utils.validators import (
    validate_marks, validate_attendance, validate_required_fields, sanitize_string
)
from utils.file_handler import save_uploaded_file, delete_file

teacher_bp = Blueprint("teacher", __name__, url_prefix="/api/teacher")


def require_teacher(fn):
    from functools import wraps
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get("role") not in ("teacher", "hod"):
            return jsonify({"error": "Teacher access required"}), 403
        return fn(*args, **kwargs)
    return wrapper


# ─── Students ─────────────────────────────────────────────────────────────────

@teacher_bp.route("/students", methods=["GET"])
@require_teacher
def get_students():
    """List all students (optionally filtered by department)."""
    claims = get_jwt()
    dept_filter = request.args.get("department") or claims.get("department")
    query = Student.query.join(User).filter(User.is_active == True)
    if dept_filter:
        query = query.filter(Student.department == dept_filter)
    students = query.order_by(Student.roll_number).all()
    return jsonify({"students": [s.to_dict() for s in students], "total": len(students)}), 200


@teacher_bp.route("/students/<int:student_id>", methods=["GET"])
@require_teacher
def get_student_detail(student_id):
    """Get full detail of a single student including marks and latest prediction."""
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404
    marks = [m.to_dict() for m in Mark.query.filter_by(student_id=student.id).all()]
    # Fetch latest prediction directly
    from database import Prediction
    latest_pred = (
        Prediction.query.filter_by(student_id=student.id)
        .order_by(Prediction.created_at.desc()).first()
    )
    return jsonify({
        "student": student.to_dict(),
        "marks": marks,
        "latest_prediction": latest_pred.to_dict() if latest_pred else None,
    }), 200


# ─── Marks Entry (by teacher) ─────────────────────────────────────────────────

@teacher_bp.route("/students/<int:student_id>/marks", methods=["POST"])
@require_teacher
def enter_marks(student_id):
    """Teacher enters/updates marks for a student."""
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Accept list of mark records or single record
    entries = data if isinstance(data, list) else [data]
    saved = []

    for entry in entries:
        ok, msg = validate_required_fields(entry, ["subject_id", "marks"])
        if not ok:
            return jsonify({"error": msg}), 400

        ok, msg = validate_marks(entry["marks"])
        if not ok:
            return jsonify({"error": f"Subject {entry.get('subject_id')}: {msg}"}), 400

        subject = Subject.query.get(entry["subject_id"])
        if not subject:
            return jsonify({"error": f"Subject {entry['subject_id']} not found"}), 404

        existing = Mark.query.filter_by(student_id=student.id, subject_id=entry["subject_id"]).first()
        if existing:
            existing.marks = float(entry["marks"])
            existing.attendance = float(entry.get("attendance", existing.attendance))
            existing.assignment_score = float(entry.get("assignment_score", existing.assignment_score))
            existing.recorded_at = datetime.utcnow()
            saved.append(existing.to_dict())
        else:
            if "attendance" in entry:
                ok, msg = validate_attendance(entry["attendance"])
                if not ok:
                    return jsonify({"error": msg}), 400
            mark = Mark(
                student_id=student.id,
                subject_id=entry["subject_id"],
                marks=float(entry["marks"]),
                attendance=float(entry.get("attendance", 0)),
                assignment_score=float(entry.get("assignment_score", 0)),
            )
            db.session.add(mark)
            db.session.flush()
            saved.append(mark.to_dict())

    # Notify student
    teacher_id = int(get_jwt_identity())
    teacher = User.query.get(teacher_id)
    notif = Notification(
        user_id=student.user_id,
        title="📊 Marks Updated",
        message=f"Your marks have been updated by {teacher.name if teacher else 'your teacher'}.",
        notification_type="info",
    )
    db.session.add(notif)
    db.session.commit()

    return jsonify({"message": f"{len(saved)} mark record(s) saved", "marks": saved}), 201


# ─── Subjects ─────────────────────────────────────────────────────────────────

@teacher_bp.route("/subjects", methods=["GET"])
@require_teacher
def get_subjects():
    dept = request.args.get("department")
    query = Subject.query
    if dept:
        query = query.filter_by(department=dept)
    subjects = query.all()
    return jsonify({"subjects": [s.to_dict() for s in subjects]}), 200


@teacher_bp.route("/subjects", methods=["POST"])
@require_teacher
def add_subject():
    data = request.get_json()
    ok, msg = validate_required_fields(data, ["name", "department"])
    if not ok:
        return jsonify({"error": msg}), 400
    existing = Subject.query.filter_by(name=data["name"], department=data["department"]).first()
    if existing:
        return jsonify({"error": "Subject already exists for this department"}), 409
    subject = Subject(
        name=sanitize_string(data["name"], 100),
        department=sanitize_string(data["department"], 100),
        semester=int(data.get("semester", 1)),
        max_marks=float(data.get("max_marks", 100)),
    )
    db.session.add(subject)
    db.session.commit()
    return jsonify({"message": "Subject created", "subject": subject.to_dict()}), 201


# ─── Assignments ──────────────────────────────────────────────────────────────

@teacher_bp.route("/assignments", methods=["GET"])
@require_teacher
def get_assignments():
    teacher_id = int(get_jwt_identity())
    claims = get_jwt()
    # HOD sees all, teacher sees own
    if claims.get("role") == "hod":
        assignments = Assignment.query.order_by(Assignment.created_at.desc()).all()
    else:
        assignments = Assignment.query.filter_by(teacher_id=teacher_id).order_by(Assignment.created_at.desc()).all()
    return jsonify({"assignments": [a.to_dict() for a in assignments]}), 200


@teacher_bp.route("/assignments", methods=["POST"])
@require_teacher
def create_assignment():
    teacher_id = int(get_jwt_identity())
    json_data = request.get_json(silent=True) or {}
    title = request.form.get("title") or json_data.get("title")
    description = request.form.get("description") or json_data.get("description", "")
    deadline_str = request.form.get("deadline") or json_data.get("deadline")
    target_dept = request.form.get("target_department") or json_data.get("target_department")
    target_student = request.form.get("target_student_id") or json_data.get("target_student_id")

    if not title:
        return jsonify({"error": "Title is required"}), 400

    deadline = None
    if deadline_str:
        try:
            deadline = datetime.fromisoformat(deadline_str.replace("Z", "+00:00").replace("+00:00", ""))
        except Exception:
            return jsonify({"error": "Invalid deadline format"}), 400

    file_path, original_filename = None, None
    if "file" in request.files and request.files["file"].filename:
        try:
            file_path, original_filename = save_uploaded_file(
                request.files["file"],
                current_app.config["UPLOAD_FOLDER"],
                subfolder="assignments",
            )
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    assignment = Assignment(
        teacher_id=teacher_id,
        title=sanitize_string(title, 200),
        description=sanitize_string(description, 2000),
        deadline=deadline,
        file_path=file_path,
        original_filename=original_filename,
        target_department=sanitize_string(target_dept, 100) if target_dept else None,
        target_student_id=int(target_student) if target_student else None,
    )
    db.session.add(assignment)
    db.session.flush()

    # Notify relevant students
    _notify_students_for_assignment(assignment, teacher_id)

    db.session.commit()
    return jsonify({"message": "Assignment created", "assignment": assignment.to_dict()}), 201


@teacher_bp.route("/assignments/<int:assignment_id>", methods=["PUT"])
@require_teacher
def update_assignment(assignment_id):
    teacher_id = int(get_jwt_identity())
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    claims = get_jwt()
    if assignment.teacher_id != teacher_id and claims.get("role") != "hod":
        return jsonify({"error": "Not authorized to edit this assignment"}), 403

    data = request.get_json() or {}
    if "title" in data:
        assignment.title = sanitize_string(data["title"], 200)
    if "description" in data:
        assignment.description = sanitize_string(data["description"], 2000)
    if "deadline" in data:
        try:
            assignment.deadline = datetime.fromisoformat(data["deadline"].replace("Z", ""))
        except Exception:
            return jsonify({"error": "Invalid deadline format"}), 400
    if "is_active" in data:
        assignment.is_active = bool(data["is_active"])

    db.session.commit()
    return jsonify({"message": "Assignment updated", "assignment": assignment.to_dict()}), 200


@teacher_bp.route("/assignments/<int:assignment_id>", methods=["DELETE"])
@require_teacher
def delete_assignment(assignment_id):
    teacher_id = int(get_jwt_identity())
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    claims = get_jwt()
    if assignment.teacher_id != teacher_id and claims.get("role") != "hod":
        return jsonify({"error": "Not authorized"}), 403

    if assignment.file_path:
        delete_file(current_app.config["UPLOAD_FOLDER"], assignment.file_path)

    db.session.delete(assignment)
    db.session.commit()
    return jsonify({"message": "Assignment deleted"}), 200


# ─── Submissions (review) ─────────────────────────────────────────────────────

@teacher_bp.route("/assignments/<int:assignment_id>/submissions", methods=["GET"])
@require_teacher
def get_submissions(assignment_id):
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404
    subs = Submission.query.filter_by(assignment_id=assignment_id).all()
    return jsonify({
        "assignment": assignment.to_dict(),
        "submissions": [s.to_dict() for s in subs],
        "total_submitted": len(subs),
    }), 200


@teacher_bp.route("/submissions/<int:submission_id>/review", methods=["PUT"])
@require_teacher
def review_submission(submission_id):
    sub = Submission.query.get(submission_id)
    if not sub:
        return jsonify({"error": "Submission not found"}), 404
    data = request.get_json() or {}
    sub.status = data.get("status", "reviewed")
    sub.grade = data.get("grade")
    sub.feedback = sanitize_string(data.get("feedback", ""), 1000)
    sub.reviewed_at = datetime.utcnow()
    db.session.commit()

    # Notify student
    notif = Notification(
        user_id=sub.student.user_id,
        title="📝 Submission Reviewed",
        message=f"Your submission for '{sub.assignment.title}' has been reviewed. Grade: {sub.grade or 'N/A'}",
        notification_type="success",
    )
    db.session.add(notif)
    db.session.commit()
    return jsonify({"message": "Submission reviewed", "submission": sub.to_dict()}), 200


# ─── File Download ────────────────────────────────────────────────────────────

@teacher_bp.route("/assignments/<int:assignment_id>/download", methods=["GET"])
@jwt_required()
def download_assignment_file(assignment_id):
    import os
    assignment = Assignment.query.get(assignment_id)
    if not assignment or not assignment.file_path:
        return jsonify({"error": "File not found"}), 404
    full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], assignment.file_path)
    if not os.path.exists(full_path):
        return jsonify({"error": "File not found on disk"}), 404
    return send_file(full_path, as_attachment=True, download_name=assignment.original_filename)


@teacher_bp.route("/submissions/<int:submission_id>/download", methods=["GET"])
@require_teacher
def download_submission_file(submission_id):
    import os
    sub = Submission.query.get(submission_id)
    if not sub or not sub.file_path:
        return jsonify({"error": "File not found"}), 404
    full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], sub.file_path)
    if not os.path.exists(full_path):
        return jsonify({"error": "File not found on disk"}), 404
    return send_file(full_path, as_attachment=True, download_name=sub.original_filename)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _notify_students_for_assignment(assignment: Assignment, teacher_id: int):
    """Send notifications to students when a new assignment is created."""
    teacher = User.query.get(teacher_id)
    teacher_name = teacher.name if teacher else "Teacher"

    if assignment.target_student_id:
        student = Student.query.get(assignment.target_student_id)
        if student:
            db.session.add(Notification(
                user_id=student.user_id,
                title="📋 New Assignment",
                message=f"'{assignment.title}' assigned by {teacher_name}. Deadline: {assignment.deadline or 'No deadline'}",
                notification_type="info",
            ))
    else:
        # Notify all students in department
        query = Student.query
        if assignment.target_department:
            query = query.filter_by(department=assignment.target_department)
        for student in query.all():
            db.session.add(Notification(
                user_id=student.user_id,
                title="📋 New Assignment",
                message=f"'{assignment.title}' assigned by {teacher_name}. Deadline: {assignment.deadline or 'No deadline'}",
                notification_type="info",
            ))
