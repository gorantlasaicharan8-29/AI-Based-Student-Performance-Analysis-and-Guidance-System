"""
routes/hod.py - HOD (Head of Department) API routes.
Full department oversight: all students, all teachers, analytics, trends.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import func
from database import db, User, Student, Subject, Mark, Assignment, Submission, Prediction

hod_bp = Blueprint("hod", __name__, url_prefix="/api/hod")


def require_hod(fn):
    from functools import wraps
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get("role") != "hod":
            return jsonify({"error": "HOD access required"}), 403
        return fn(*args, **kwargs)
    return wrapper


# ─── Overview Dashboard ───────────────────────────────────────────────────────

@hod_bp.route("/overview", methods=["GET"])
@require_hod
def get_overview():
    """High-level dashboard: student counts, predictions, assignment stats."""
    dept_filter = request.args.get("department")

    student_query = Student.query.join(User).filter(User.is_active == True)
    if dept_filter:
        student_query = student_query.filter(Student.department == dept_filter)

    students = student_query.all()
    student_ids = [s.id for s in students]

    # Prediction stats
    if student_ids:
        all_preds = (
            db.session.query(Prediction)
            .filter(Prediction.student_id.in_(student_ids))
            .order_by(Prediction.created_at.desc())
            .all()
        )
        seen_students = set()
        preds = []
        for p in all_preds:
            if p.student_id not in seen_students:
                seen_students.add(p.student_id)
                preds.append(p)
    else:
        preds = []

    grade_dist = {"A": 0, "B": 0, "C": 0, "Fail": 0}
    risk_dist = {"Low": 0, "Medium": 0, "High": 0}
    for p in preds:
        grade_dist[p.grade] = grade_dist.get(p.grade, 0) + 1
        risk_dist[p.risk_level] = risk_dist.get(p.risk_level, 0) + 1

    # Assignment stats
    assignment_count = Assignment.query.filter_by(is_active=True).count()
    submission_count = Submission.query.count()
    teacher_count = User.query.filter_by(role="teacher", is_active=True).count()

    # Avg marks per department
    dept_avg = _get_department_averages()

    return jsonify({
        "total_students": len(students),
        "total_teachers": teacher_count,
        "total_assignments": assignment_count,
        "total_submissions": submission_count,
        "grade_distribution": grade_dist,
        "risk_distribution": risk_dist,
        "department_averages": dept_avg,
        "at_risk_count": risk_dist.get("High", 0),
        "top_performers_count": grade_dist.get("A", 0),
    }), 200


# ─── Students (full access) ───────────────────────────────────────────────────

@hod_bp.route("/students", methods=["GET"])
@require_hod
def get_all_students():
    """Get all students with optional filters."""
    dept = request.args.get("department")
    subject_id = request.args.get("subject_id")
    performance = request.args.get("performance")  # strong | weak | average
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    query = Student.query.join(User).filter(User.is_active == True)
    if dept:
        query = query.filter(Student.department == dept)

    students = query.order_by(Student.roll_number).all()

    result = []
    for s in students:
        marks = [m.to_dict() for m in Mark.query.filter_by(student_id=s.id).all()]
        avg = sum(m["marks"] for m in marks) / len(marks) if marks else 0

        # Filter by performance level
        if performance == "strong" and avg <= 75:
            continue
        if performance == "weak" and avg >= 50:
            continue
        if performance == "average" and (avg < 50 or avg > 75):
            continue

        pred = (
            Prediction.query.filter_by(student_id=s.id)
            .order_by(Prediction.created_at.desc()).first()
        )

        result.append({
            **s.to_dict(),
            "average_marks": round(avg, 2),
            "num_subjects": len(marks),
            "grade": pred.grade if pred else None,
            "risk_level": pred.risk_level if pred else None,
        })

    # Pagination
    total = len(result)
    start = (page - 1) * per_page
    paginated = result[start:start + per_page]

    return jsonify({
        "students": paginated,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }), 200


@hod_bp.route("/students/<int:student_id>", methods=["GET"])
@require_hod
def get_student_full(student_id):
    """Full student data: profile, marks, predictions, submissions."""
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404

    marks = [m.to_dict() for m in Mark.query.filter_by(student_id=student.id).all()]
    predictions = [p.to_dict() for p in Prediction.query.filter_by(student_id=student.id).order_by(Prediction.created_at.desc()).all()]
    submissions = [s.to_dict() for s in Submission.query.filter_by(student_id=student.id).all()]

    return jsonify({
        "student": student.to_dict(),
        "marks": marks,
        "predictions": predictions,
        "submissions": submissions,
    }), 200


# ─── At-Risk Students ─────────────────────────────────────────────────────────

@hod_bp.route("/at-risk", methods=["GET"])
@require_hod
def get_at_risk_students():
    """List students with High risk level, newest prediction per student."""
    dept = request.args.get("department")

    query = (
        db.session.query(Student, Prediction)
        .join(Prediction, Student.id == Prediction.student_id)
        .join(User, Student.user_id == User.id)
        .filter(Prediction.risk_level == "High", User.is_active == True)
    )
    if dept:
        query = query.filter(Student.department == dept)

    results = query.order_by(Prediction.created_at.desc()).all()
    seen = set()
    at_risk = []
    for student, pred in results:
        if student.id not in seen:
            seen.add(student.id)
            at_risk.append({**student.to_dict(), "prediction": pred.to_dict()})

    return jsonify({"at_risk_students": at_risk, "count": len(at_risk)}), 200


# ─── Top Performers ───────────────────────────────────────────────────────────

@hod_bp.route("/top-performers", methods=["GET"])
@require_hod
def get_top_performers():
    dept = request.args.get("department")
    limit = int(request.args.get("limit", 10))

    query = Student.query.join(User).filter(User.is_active == True)
    if dept:
        query = query.filter(Student.department == dept)

    students = query.all()
    performers = []
    for s in students:
        marks = Mark.query.filter_by(student_id=s.id).all()
        if not marks:
            continue
        avg = sum(m.marks for m in marks) / len(marks)
        performers.append({"student": s.to_dict(), "average_marks": round(avg, 2)})

    performers.sort(key=lambda x: x["average_marks"], reverse=True)
    return jsonify({"top_performers": performers[:limit]}), 200


# ─── Department Analytics ─────────────────────────────────────────────────────

@hod_bp.route("/analytics/department", methods=["GET"])
@require_hod
def get_department_analytics():
    """Per-department: student count, avg marks, grade distribution."""
    dept_averages = _get_department_averages()
    dept_grade_dist = _get_department_grade_distribution()

    return jsonify({
        "department_averages": dept_averages,
        "department_grade_distribution": dept_grade_dist,
    }), 200


@hod_bp.route("/analytics/subjects", methods=["GET"])
@require_hod
def get_subject_analytics():
    """Subject-wise average marks across all students."""
    dept = request.args.get("department")
    results = (
        db.session.query(Subject.name, func.avg(Mark.marks).label("avg_marks"),
                         func.count(Mark.id).label("count"))
        .join(Mark, Subject.id == Mark.subject_id)
    )
    if dept:
        results = results.filter(Subject.department == dept)
    results = results.group_by(Subject.id).all()

    return jsonify({
        "subjects": [
            {"subject": r.name, "average_marks": round(r.avg_marks, 2), "student_count": r.count}
            for r in results
        ]
    }), 200


@hod_bp.route("/analytics/trends", methods=["GET"])
@require_hod
def get_trends():
    """Academic trends: prediction grade over time, risk counts."""
    from sqlalchemy import func as sa_func
    import calendar

    predictions = Prediction.query.order_by(Prediction.created_at).all()
    monthly = {}
    for p in predictions:
        key = p.created_at.strftime("%Y-%m")
        if key not in monthly:
            monthly[key] = {"month": key, "A": 0, "B": 0, "C": 0, "Fail": 0, "High_Risk": 0}
        monthly[key][p.grade] = monthly[key].get(p.grade, 0) + 1
        if p.risk_level == "High":
            monthly[key]["High_Risk"] += 1

    return jsonify({"trends": list(monthly.values())}), 200


# ─── Assignment Monitoring ────────────────────────────────────────────────────

@hod_bp.route("/assignments", methods=["GET"])
@require_hod
def get_all_assignments():
    """View all assignments by all teachers."""
    assignments = Assignment.query.order_by(Assignment.created_at.desc()).all()
    result = []
    for a in assignments:
        a_dict = a.to_dict()
        a_dict["submission_rate"] = (
            f"{len(a.submissions) / max(1, _count_target_students(a)) * 100:.1f}%"
        )
        result.append(a_dict)
    return jsonify({"assignments": result}), 200


# ─── Teachers ─────────────────────────────────────────────────────────────────

@hod_bp.route("/teachers", methods=["GET"])
@require_hod
def get_teachers():
    dept = request.args.get("department")
    query = User.query.filter_by(role="teacher", is_active=True)
    if dept:
        query = query.filter_by(department=dept)
    teachers = query.all()
    result = []
    for t in teachers:
        assigned = Assignment.query.filter_by(teacher_id=t.id).count()
        result.append({**t.to_dict(), "assignments_created": assigned})
    return jsonify({"teachers": result}), 200


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_department_averages() -> list:
    results = (
        db.session.query(Student.department, func.avg(Mark.marks).label("avg"))
        .join(Mark, Student.id == Mark.student_id)
        .group_by(Student.department)
        .all()
    )
    return [{"department": r.department, "average_marks": round(r.avg, 2)} for r in results]


def _get_department_grade_distribution() -> dict:
    students = Student.query.join(User).filter(User.is_active == True).all()
    dist = {}
    for s in students:
        if s.department not in dist:
            dist[s.department] = {"A": 0, "B": 0, "C": 0, "Fail": 0, "No Prediction": 0}
        pred = Prediction.query.filter_by(student_id=s.id).order_by(Prediction.created_at.desc()).first()
        if pred:
            dist[s.department][pred.grade] = dist[s.department].get(pred.grade, 0) + 1
        else:
            dist[s.department]["No Prediction"] += 1
    return dist


def _count_target_students(assignment: Assignment) -> int:
    if assignment.target_student_id:
        return 1
    if assignment.target_department:
        return Student.query.filter_by(department=assignment.target_department).count()
    return Student.query.count()
