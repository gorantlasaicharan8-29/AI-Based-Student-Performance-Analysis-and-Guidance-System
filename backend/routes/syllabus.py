"""
routes/syllabus.py - Syllabus Management & AI Study Recommendation API.

Endpoints:
  Teacher:
    GET  /api/syllabus/subjects                  → subjects with syllabus status
    GET  /api/syllabus/<subject_id>              → full syllabus (all 6 units)
    POST /api/syllabus/<subject_id>              → save/update full 6-unit syllabus
    GET  /api/syllabus/teacher/weak-areas        → unit-wise weak students

  Student:
    GET  /api/syllabus/recommendations           → AI unit recommendations per subject

  HOD:
    GET  /api/syllabus/hod/unit-analysis         → department-wide unit difficulty
"""

import json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from database import db, User, Student, Subject, Mark, Unit, Topic

syllabus_bp = Blueprint("syllabus", __name__, url_prefix="/api/syllabus")

# ── Performance classification thresholds ─────────────────────────────────────
PERF_HIGH   = 75   # marks >= 75
PERF_MEDIUM = 50   # 50 <= marks < 75
# PERF_LOW  = < 50

# ── Unit recommendation map (rule-based) ──────────────────────────────────────
UNIT_RECOMMENDATION = {
    "Low": {
        "units":    [1, 2, 3],
        "priority": "High",
        "goal":     "Build basic understanding",
        "message":  "Focus on Unit 1 and Unit 2 to strengthen fundamentals, then move to Unit 3.",
    },
    "Medium": {
        "units":    [3, 4, 5],
        "priority": "Medium",
        "goal":     "Improve scoring areas",
        "message":  "Revise Unit 3 and Unit 4 for better scoring, then practise Unit 5.",
    },
    "High": {
        "units":    [5, 6],
        "priority": "Low",
        "goal":     "Advanced learning and practice",
        "message":  "Practise advanced topics from Unit 5 and Unit 6 to maximise your grade.",
    },
}


def _classify_performance(marks: float) -> str:
    if marks >= PERF_HIGH:
        return "High"
    elif marks >= PERF_MEDIUM:
        return "Medium"
    return "Low"


def _require_role(*roles):
    """Decorator: ensure JWT role is in allowed roles."""
    from functools import wraps
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get("role") not in roles:
                return jsonify({"error": f"Access restricted to: {', '.join(roles)}"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# TEACHER — view subjects with syllabus status
# ─────────────────────────────────────────────────────────────────────────────
@syllabus_bp.route("/subjects", methods=["GET"])
@_require_role("teacher", "hod")
def list_subjects_with_status():
    """Return all subjects showing how many units are already saved."""
    claims = get_jwt()
    dept = request.args.get("department") or claims.get("department")
    query = Subject.query
    if dept:
        query = query.filter_by(department=dept)
    subjects = query.all()

    result = []
    for s in subjects:
        units_saved = len(s.units)
        result.append({
            **s.to_dict(),
            "units_saved": units_saved,
            "syllabus_complete": units_saved == 6,
        })
    return jsonify({"subjects": result}), 200


# ─────────────────────────────────────────────────────────────────────────────
# TEACHER — get full syllabus for one subject
# ─────────────────────────────────────────────────────────────────────────────
@syllabus_bp.route("/<int:subject_id>", methods=["GET"])
@jwt_required()
def get_syllabus(subject_id):
    subject = Subject.query.get(subject_id)
    if not subject:
        return jsonify({"error": "Subject not found"}), 404

    # Return all 6 unit slots (even if not yet filled)
    units_map = {u.unit_number: u for u in subject.units}
    units_out = []
    for n in range(1, 7):
        if n in units_map:
            units_out.append(units_map[n].to_dict())
        else:
            units_out.append({
                "id": None,
                "subject_id": subject_id,
                "unit_number": n,
                "title": f"Unit {n}",
                "topics": [],
            })

    return jsonify({
        "subject":  subject.to_dict(),
        "units":    units_out,
        "complete": len(subject.units) == 6,
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# TEACHER — save / update full 6-unit syllabus
# ─────────────────────────────────────────────────────────────────────────────
@syllabus_bp.route("/<int:subject_id>", methods=["POST"])
@_require_role("teacher", "hod")
def save_syllabus(subject_id):
    """
    Accepts JSON body:
    {
      "units": [
        { "unit_number": 1, "title": "Introduction", "topics": ["Topic A", "Topic B"] },
        ...  (up to 6)
      ]
    }
    """
    subject = Subject.query.get(subject_id)
    if not subject:
        return jsonify({"error": "Subject not found"}), 404

    data = request.get_json()
    if not data or "units" not in data:
        return jsonify({"error": "'units' array is required"}), 400

    units_data = data["units"]
    if len(units_data) > 6:
        return jsonify({"error": "Maximum 6 units allowed per subject"}), 400

    saved_units = []
    for ud in units_data:
        num   = int(ud.get("unit_number", 0))
        title = str(ud.get("title", f"Unit {num}")).strip()[:200]
        topics_list = ud.get("topics", [])

        if not (1 <= num <= 6):
            return jsonify({"error": f"unit_number must be between 1 and 6 (got {num})"}), 400

        # Upsert unit
        unit = Unit.query.filter_by(subject_id=subject_id, unit_number=num).first()
        if unit:
            unit.title = title
            # Clear old topics
            for t in unit.topics:
                db.session.delete(t)
        else:
            unit = Unit(subject_id=subject_id, unit_number=num, title=title)
            db.session.add(unit)
        db.session.flush()

        # Add topics
        for idx, topic_name in enumerate(topics_list):
            t_name = str(topic_name).strip()[:300]
            if t_name:
                db.session.add(Topic(unit_id=unit.id, name=t_name, order=idx))

        db.session.flush()
        saved_units.append(unit.to_dict())

    db.session.commit()
    return jsonify({
        "message": f"{len(saved_units)} unit(s) saved for {subject.name}",
        "units":   saved_units,
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# STUDENT — AI-based unit recommendations per subject
# ─────────────────────────────────────────────────────────────────────────────
@syllabus_bp.route("/recommendations", methods=["GET"])
@_require_role("student")
def get_recommendations():
    """
    For the logged-in student, look at their marks per subject,
    classify performance, and recommend units based on the rule engine.
    """
    user_id  = int(get_jwt_identity())
    student  = Student.query.filter_by(user_id=user_id).first()
    if not student:
        return jsonify({"error": "Student profile not found"}), 404

    student_marks = Mark.query.filter_by(student_id=student.id).all()
    if not student_marks:
        return jsonify({"recommendations": [], "message": "No marks found yet."}), 200

    recommendations = []
    for mark in student_marks:
        subject = mark.subject
        if not subject:
            continue

        perf_level = _classify_performance(mark.marks)
        rule       = UNIT_RECOMMENDATION[perf_level]

        # Fetch the recommended unit details from DB
        recommended_units = []
        for unit_num in rule["units"]:
            unit = Unit.query.filter_by(subject_id=subject.id, unit_number=unit_num).first()
            if unit:
                recommended_units.append(unit.to_dict())
            else:
                # Syllabus not yet uploaded — return placeholder
                recommended_units.append({
                    "id":          None,
                    "unit_number": unit_num,
                    "title":       f"Unit {unit_num}",
                    "topics":      [],
                })

        recommendations.append({
            "subject_id":          subject.id,
            "subject_name":        subject.name,
            "marks":               mark.marks,
            "attendance":          mark.attendance,
            "performance_level":   perf_level,
            "priority":            rule["priority"],
            "goal":                rule["goal"],
            "message":             rule["message"],
            "recommended_units":   recommended_units,
            "recommended_unit_numbers": rule["units"],
        })

    # Sort: High priority first
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    recommendations.sort(key=lambda r: priority_order.get(r["priority"], 3))

    return jsonify({
        "student":         student.to_dict(),
        "recommendations": recommendations,
        "total_subjects":  len(recommendations),
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# TEACHER — view unit-wise weak areas for their students
# ─────────────────────────────────────────────────────────────────────────────
@syllabus_bp.route("/teacher/weak-areas", methods=["GET"])
@_require_role("teacher", "hod")
def teacher_weak_areas():
    """
    Returns each subject → list of students with Low/Medium performance
    mapped to recommended units, so teacher can see where to focus.
    """
    claims = get_jwt()
    dept   = request.args.get("department") or claims.get("department")

    subjects = Subject.query.filter_by(department=dept).all() if dept else Subject.query.all()
    result   = []

    for subject in subjects:
        unit_weakness = {}  # unit_num -> list of student names

        marks = Mark.query.filter_by(subject_id=subject.id).all()
        for mark in marks:
            perf  = _classify_performance(mark.marks)
            rule  = UNIT_RECOMMENDATION[perf]
            sname = mark.student.user.name if mark.student and mark.student.user else "Unknown"

            for unit_num in rule["units"]:
                unit = Unit.query.filter_by(subject_id=subject.id, unit_number=unit_num).first()
                unit_title = unit.title if unit else f"Unit {unit_num}"
                key = f"{unit_num}|{unit_title}"
                unit_weakness.setdefault(key, {"unit_number": unit_num,
                                               "unit_title": unit_title,
                                               "students": [],
                                               "priority": rule["priority"]})
                unit_weakness[key]["students"].append({
                    "name":        sname,
                    "marks":       mark.marks,
                    "performance": perf,
                })

        if unit_weakness:
            result.append({
                "subject_id":   subject.id,
                "subject_name": subject.name,
                "unit_weaknesses": sorted(unit_weakness.values(),
                                          key=lambda x: x["unit_number"]),
            })

    return jsonify({"weak_area_report": result}), 200


# ─────────────────────────────────────────────────────────────────────────────
# HOD — department-wide unit difficulty analysis
# ─────────────────────────────────────────────────────────────────────────────
@syllabus_bp.route("/hod/unit-analysis", methods=["GET"])
@_require_role("hod")
def hod_unit_analysis():
    """
    Aggregate how many students fall Low/Medium/High per unit across all subjects.
    Highlights 'most difficult' units (most Low performers).
    """
    dept     = request.args.get("department")
    subjects = Subject.query.filter_by(department=dept).all() if dept else Subject.query.all()
    analysis = []

    for subject in subjects:
        unit_stats = {}  # unit_num -> {low, medium, high, students}

        for n in range(1, 7):
            unit = Unit.query.filter_by(subject_id=subject.id, unit_number=n).first()
            unit_stats[n] = {
                "unit_number":  n,
                "unit_title":   unit.title if unit else f"Unit {n}",
                "topics_count": len(unit.topics) if unit else 0,
                "low":          0,
                "medium":       0,
                "high":         0,
                "low_students": [],
            }

        marks = Mark.query.filter_by(subject_id=subject.id).all()
        for mark in marks:
            perf  = _classify_performance(mark.marks)
            rule  = UNIT_RECOMMENDATION[perf]
            sname = mark.student.user.name if mark.student and mark.student.user else "?"

            for unit_num in rule["units"]:
                if unit_num in unit_stats:
                    unit_stats[unit_num][perf.lower()] += 1
                    if perf == "Low":
                        unit_stats[unit_num]["low_students"].append(sname)

        # Sort units by number of LOW students desc (most difficult first)
        sorted_units = sorted(unit_stats.values(),
                              key=lambda u: u["low"], reverse=True)

        analysis.append({
            "subject_id":   subject.id,
            "subject_name": subject.name,
            "total_marks":  len(marks),
            "units":        sorted_units,
            "most_difficult_unit": sorted_units[0] if sorted_units else None,
        })

    return jsonify({"unit_analysis": analysis}), 200
