"""
routes/student.py - Student-facing API routes.
Covers: profile, marks, predictions, assignments, submissions, notifications, reports.
"""

import json
import io
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from database import db, User, Student, Subject, Mark, Assignment, Submission, Prediction, Notification
from utils.validators import validate_marks, validate_attendance, validate_required_fields, sanitize_string
from utils.file_handler import save_uploaded_file, allowed_file
from utils.report_gen import generate_student_report

student_bp = Blueprint("student", __name__, url_prefix="/api/student")


def require_student(fn):
    """Decorator: ensure JWT belongs to a student."""
    from functools import wraps

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get("role") != "student":
            return jsonify({"error": "Student access required"}), 403
        return fn(*args, **kwargs)

    return wrapper


def get_student_or_404(user_id: int):
    user = User.query.get(user_id)
    if not user or not user.student_profile:
        return None, jsonify({"error": "Student profile not found"}), 404
    return user.student_profile, None, None


# ─── Profile ──────────────────────────────────────────────────────────────────

@student_bp.route("/profile", methods=["GET"])
@require_student
def get_profile():
    user_id = int(get_jwt_identity())
    student, err, code = get_student_or_404(user_id)
    if err:
        return err, code
    return jsonify({"student": student.to_dict()}), 200


@student_bp.route("/profile", methods=["PUT"])
@require_student
def update_profile():
    user_id = int(get_jwt_identity())
    student, err, code = get_student_or_404(user_id)
    if err:
        return err, code
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    if "semester" in data:
        student.semester = int(data["semester"])
    if "batch" in data:
        student.batch = sanitize_string(data["batch"], 20)
    if "name" in data:
        student.user.name = sanitize_string(data["name"], 100)
    db.session.commit()
    return jsonify({"message": "Profile updated", "student": student.to_dict()}), 200


# ─── Marks ────────────────────────────────────────────────────────────────────

@student_bp.route("/marks", methods=["GET"])
@require_student
def get_marks():
    user_id = int(get_jwt_identity())
    student, err, code = get_student_or_404(user_id)
    if err:
        return err, code

    marks = Mark.query.filter_by(student_id=student.id).all()
    marks_list = [m.to_dict() for m in marks]

    # Compute analytics
    analytics = _compute_analytics(marks_list)
    return jsonify({"marks": marks_list, "analytics": analytics}), 200


@student_bp.route("/marks", methods=["POST"])
@require_student
def add_marks():
    """Students can self-report marks (teachers can also enter marks via teacher routes)."""
    user_id = int(get_jwt_identity())
    student, err, code = get_student_or_404(user_id)
    if err:
        return err, code

    data = request.get_json()
    ok, msg = validate_required_fields(data, ["subject_id", "marks"])
    if not ok:
        return jsonify({"error": msg}), 400

    ok, msg = validate_marks(data["marks"])
    if not ok:
        return jsonify({"error": msg}), 400

    if "attendance" in data:
        ok, msg = validate_attendance(data["attendance"])
        if not ok:
            return jsonify({"error": msg}), 400

    subject = Subject.query.get(data["subject_id"])
    if not subject:
        return jsonify({"error": "Subject not found"}), 404

    # Check if mark already exists for this student+subject
    existing = Mark.query.filter_by(student_id=student.id, subject_id=data["subject_id"]).first()
    if existing:
        existing.marks = float(data["marks"])
        existing.attendance = float(data.get("attendance", existing.attendance))
        existing.assignment_score = float(data.get("assignment_score", existing.assignment_score))
        existing.recorded_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Marks updated", "mark": existing.to_dict()}), 200

    mark = Mark(
        student_id=student.id,
        subject_id=data["subject_id"],
        marks=float(data["marks"]),
        attendance=float(data.get("attendance", 0)),
        assignment_score=float(data.get("assignment_score", 0)),
    )
    db.session.add(mark)
    db.session.commit()
    return jsonify({"message": "Marks added", "mark": mark.to_dict()}), 201


# ─── Performance Analytics ────────────────────────────────────────────────────

@student_bp.route("/performance", methods=["GET"])
@require_student
def get_performance():
    user_id = int(get_jwt_identity())
    student, err, code = get_student_or_404(user_id)
    if err:
        return err, code

    marks = Mark.query.filter_by(student_id=student.id).all()
    marks_list = [m.to_dict() for m in marks]
    analytics = _compute_analytics(marks_list)

    # Latest prediction
    latest_pred = (
        Prediction.query.filter_by(student_id=student.id)
        .order_by(Prediction.created_at.desc())
        .first()
    )

    return jsonify({
        "student": student.to_dict(),
        "marks": marks_list,
        "analytics": analytics,
        "latest_prediction": latest_pred.to_dict() if latest_pred else None,
    }), 200


# ─── ML Prediction ────────────────────────────────────────────────────────────

@student_bp.route("/predict", methods=["POST"])
@require_student
def predict_performance():
    from flask import current_app
    user_id = int(get_jwt_identity())
    student, err, code = get_student_or_404(user_id)
    if err:
        return err, code

    marks = Mark.query.filter_by(student_id=student.id).all()
    if not marks:
        return jsonify({"error": "No marks data found. Please add marks first."}), 400

    marks_list = [m.to_dict() for m in marks]
    predictor = current_app.predictor
    guidance_engine = current_app.guidance_engine

    try:
        result = predictor.predict(marks_list, semester=student.semester)
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500

    # Generate guidance
    from ml.guidance import generate_study_plan
    guidance = generate_study_plan(result["analytics"], result["grade"], result["risk_level"])

    # Save prediction to DB
    pred = Prediction(
        student_id=student.id,
        grade=result["grade"],
        risk_level=result["risk_level"],
        confidence=result["confidence"],
        factors=json.dumps(result["factors"]),
        recommendations=json.dumps(guidance["recommendations"]),
        average_marks=result["analytics"]["average_marks"],
        average_attendance=result["analytics"]["average_attendance"],
    )
    db.session.add(pred)

    # Notification for high risk
    if result["risk_level"] == "High":
        notif = Notification(
            user_id=user_id,
            title="⚠️ High Academic Risk Detected",
            message="Your performance indicates high academic risk. Check the guidance section for an action plan.",
            notification_type="warning",
        )
        db.session.add(notif)

    db.session.commit()

    return jsonify({
        "prediction": result,
        "guidance": guidance,
        "prediction_id": pred.id,
    }), 200


# ─── Assignments (view & submit) ──────────────────────────────────────────────

@student_bp.route("/assignments", methods=["GET"])
@require_student
def get_assignments():
    user_id = int(get_jwt_identity())
    student, err, code = get_student_or_404(user_id)
    if err:
        return err, code

    # Get assignments for student's department or individually assigned
    assignments = Assignment.query.filter(
        Assignment.is_active == True,
        db.or_(
            Assignment.target_department == student.department,
            Assignment.target_department == None,
            Assignment.target_student_id == student.id,
        )
    ).order_by(Assignment.created_at.desc()).all()

    result = []
    for a in assignments:
        a_dict = a.to_dict()
        # Check if student has submitted
        sub = Submission.query.filter_by(assignment_id=a.id, student_id=student.id).first()
        a_dict["submitted"] = sub is not None
        a_dict["submission"] = sub.to_dict() if sub else None
        result.append(a_dict)

    return jsonify({"assignments": result}), 200


@student_bp.route("/assignments/<int:assignment_id>/submit", methods=["POST"])
@require_student
def submit_assignment(assignment_id):
    user_id = int(get_jwt_identity())
    student, err, code = get_student_or_404(user_id)
    if err:
        return err, code

    assignment = Assignment.query.get(assignment_id)
    if not assignment or not assignment.is_active:
        return jsonify({"error": "Assignment not found"}), 404

    # Check deadline
    if assignment.deadline and datetime.utcnow() > assignment.deadline:
        return jsonify({"error": "Submission deadline has passed"}), 400

    # Check duplicate
    existing = Submission.query.filter_by(assignment_id=assignment_id, student_id=student.id).first()

    file_path, original_filename = None, None
    if "file" in request.files:
        try:
            file_path, original_filename = save_uploaded_file(
                request.files["file"],
                current_app.config["UPLOAD_FOLDER"],
                subfolder="submissions",
            )
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    if existing:
        if file_path:
            existing.file_path = file_path
            existing.original_filename = original_filename
        existing.submitted_at = datetime.utcnow()
        existing.status = "submitted"
        db.session.commit()
        return jsonify({"message": "Submission updated", "submission": existing.to_dict()}), 200

    sub = Submission(
        assignment_id=assignment_id,
        student_id=student.id,
        file_path=file_path,
        original_filename=original_filename,
    )
    db.session.add(sub)
    db.session.commit()
    return jsonify({"message": "Assignment submitted successfully", "submission": sub.to_dict()}), 201


# ─── Notifications ────────────────────────────────────────────────────────────

@student_bp.route("/notifications", methods=["GET"])
@require_student
def get_notifications():
    user_id = int(get_jwt_identity())
    notifs = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).limit(20).all()
    unread = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    return jsonify({"notifications": [n.to_dict() for n in notifs], "unread_count": unread}), 200


@student_bp.route("/notifications/read-all", methods=["PUT"])
@require_student
def mark_notifications_read():
    user_id = int(get_jwt_identity())
    Notification.query.filter_by(user_id=user_id, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"message": "All notifications marked as read"}), 200


# ─── PDF Report ───────────────────────────────────────────────────────────────

@student_bp.route("/report/pdf", methods=["GET"])
def download_report():
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    elif request.args.get("token"):
        token = request.args.get("token")

    if not token:
        return jsonify({"error": "Missing authorization token"}), 401

    try:
        from flask_jwt_extended import decode_token
        decoded = decode_token(token)
        user_id = int(decoded["sub"])
        role = decoded.get("role")
        if role != "student":
            return jsonify({"error": "Student access required"}), 403
    except Exception as e:
        return jsonify({"error": f"Invalid token: {str(e)}"}), 401

    student, err, code = get_student_or_404(user_id)
    if err:
        return err, code

    marks = [m.to_dict() for m in Mark.query.filter_by(student_id=student.id).all()]
    pred = (
        Prediction.query.filter_by(student_id=student.id)
        .order_by(Prediction.created_at.desc()).first()
    )
    prediction_dict = pred.to_dict() if pred else {}

    from ml.guidance import generate_study_plan
    guidance = {}
    if pred:
        guidance = generate_study_plan(
            {"average_marks": pred.average_marks or 0, "average_attendance": pred.average_attendance or 0,
             "weak_subjects": [], "strong_subjects": [], "completion_rate": 100},
            pred.grade, pred.risk_level
        )

    student_data = student.to_dict()
    try:
        pdf_bytes = generate_student_report(student_data, marks, prediction_dict, guidance)
    except Exception as e:
        return jsonify({"error": f"Report generation failed: {str(e)}"}), 500

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"report_{student.roll_number}.pdf",
    )


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _compute_analytics(marks_list: list) -> dict:
    """Compute performance analytics from a list of mark dicts."""
    if not marks_list:
        return {}
    all_marks = [m["marks"] for m in marks_list]
    all_att = [m["attendance"] for m in marks_list]
    all_assign = [m["assignment_score"] for m in marks_list]
    total = sum(all_marks)
    avg = total / len(all_marks)
    strong = [m for m in marks_list if m["marks"] > 75]
    weak = [m for m in marks_list if m["marks"] < 50]
    return {
        "total_marks": round(total, 2),
        "average_marks": round(avg, 2),
        "average_attendance": round(sum(all_att) / len(all_att), 2),
        "average_assignment_score": round(sum(all_assign) / len(all_assign), 2),
        "strong_subjects": [m["subject_name"] for m in strong],
        "weak_subjects": [m["subject_name"] for m in weak],
        "num_strong": len(strong),
        "num_weak": len(weak),
        "subject_count": len(marks_list),
    }
