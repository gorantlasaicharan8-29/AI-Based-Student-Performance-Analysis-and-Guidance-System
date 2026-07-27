"""
ml/guidance.py - Personalized guidance and recommendation engine.

Generates study plans, subject-focused recommendations,
and improvement strategies based on student performance data.
"""


# ─── Recommendation templates ─────────────────────────────────────────────────

WEAK_SUBJECT_STRATEGIES = {
    "general": [
        "Schedule daily 1-hour focused sessions for this subject",
        "Review lecture notes within 24 hours of each class",
        "Solve previous years' question papers",
        "Form or join a study group for peer learning",
        "Visit teacher during office hours for clarification",
    ],
    "attendance": [
        "Prioritize attending all classes for this subject",
        "If absent, obtain notes from classmates immediately",
        "Watch recorded lectures or online resources to cover missed content",
    ],
}

GRADE_STRATEGIES = {
    "A": [
        "Maintain your excellent performance — consistency is key",
        "Consider mentoring struggling peers to reinforce your knowledge",
        "Explore advanced topics and research opportunities",
        "Participate in academic competitions and olympiads",
        "Start preparing for competitive exams and higher studies",
    ],
    "B": [
        "Identify the 2–3 topics where you lose most marks and focus there",
        "Practice time management during exams",
        "Improve your answer presentation and structure",
        "Target distinction in your strongest subjects",
        "Regular revision will help consolidate your understanding",
    ],
    "C": [
        "Create a structured weekly study timetable",
        "Prioritize understanding fundamentals before advanced topics",
        "Seek help from teachers for subjects you find difficult",
        "Reduce distractions and increase focused study time",
        "Track your daily progress to stay motivated",
    ],
    "Fail": [
        "Immediate intervention required — meet with academic advisor",
        "Focus exclusively on understanding basic concepts first",
        "Attend all remedial/extra classes offered",
        "Set realistic daily study goals and stick to them",
        "Consider tutoring support for failing subjects",
        "Improve attendance immediately — it directly affects understanding",
    ],
}

RISK_STRATEGIES = {
    "High": [
        "⚠️ Academic intervention urgently needed",
        "Schedule immediate counseling session with HOD/advisor",
        "Create an emergency study plan with measurable weekly goals",
        "Notify parents/guardians about academic situation",
        "Explore institutional support resources (tutoring, counseling)",
    ],
    "Medium": [
        "Warning: Performance trending downward — act now",
        "Re-evaluate time management and study habits",
        "Increase study hours for underperforming subjects",
        "Maintain minimum 75% attendance in all subjects",
        "Submit all pending assignments to recover marks",
    ],
    "Low": [
        "Great job maintaining low academic risk!",
        "Stay consistent with your study schedule",
        "Challenge yourself with extra-curricular academic activities",
        "Help peers who may be struggling",
    ],
}

ATTENDANCE_TIPS = {
    "critical": [  # < 60%
        "🚨 Attendance is critically low — risk of being barred from exams",
        "Contact your department immediately to explain absences",
        "Attend every remaining class without exception",
        "Request makeup sessions or additional assignments to compensate",
    ],
    "low": [  # 60-75%
        "Attendance is below the required 75% threshold",
        "Aim to attend all upcoming classes",
        "Set daily attendance reminders on your phone",
        "Inform teachers in advance if you must miss a class",
    ],
    "good": [  # >= 75%
        "Good attendance — keep it up!",
        "Aim for perfect attendance in remaining sessions",
    ],
}


def generate_study_plan(analytics: dict, grade: str, risk: str) -> dict:
    """
    Generate a personalized study plan based on student analytics.

    Args:
        analytics: dict with avg_marks, avg_attendance, weak_subjects, strong_subjects, etc.
        grade: predicted grade (A/B/C/Fail)
        risk: risk level (Low/Medium/High)

    Returns:
        dict with daily_plan, recommendations, weak_subject_plans, priority_actions
    """
    avg_marks = analytics.get("average_marks", 0)
    avg_attendance = analytics.get("average_attendance", 0)
    weak_subjects = analytics.get("weak_subjects", [])
    strong_subjects = analytics.get("strong_subjects", [])
    completion_rate = analytics.get("completion_rate", 100)

    # ── Daily study hour recommendations ────────────────────────────────────
    if grade == "Fail" or risk == "High":
        daily_hours = 5
    elif grade == "C" or risk == "Medium":
        daily_hours = 4
    elif grade == "B":
        daily_hours = 3
    else:
        daily_hours = 2

    # ── Weekly study plan ────────────────────────────────────────────────────
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekly_plan = []

    # Distribute weak subjects across the week (give them more slots)
    if weak_subjects:
        for i, day in enumerate(days[:5]):  # Weekdays
            focus = weak_subjects[i % len(weak_subjects)]
            weekly_plan.append(
                {"day": day, "focus": f"📚 {focus} (Weak area — priority)", "hours": daily_hours}
            )
        weekly_plan.append(
            {"day": "Saturday", "focus": "📝 Revision + Practice Tests", "hours": max(2, daily_hours - 1)}
        )
        weekly_plan.append(
            {"day": "Sunday", "focus": "🔄 Review weak areas + Rest", "hours": max(1, daily_hours - 2)}
        )
    else:
        subjects_cycle = strong_subjects if strong_subjects else ["General Studies"]
        for i, day in enumerate(days):
            focus = subjects_cycle[i % len(subjects_cycle)]
            weekly_plan.append(
                {"day": day, "focus": f"⭐ {focus} (Maintain excellence)", "hours": daily_hours}
            )

    # ── Weak subject action plans ────────────────────────────────────────────
    weak_subject_plans = {}
    for subj in weak_subjects:
        weak_subject_plans[subj] = {
            "subject": subj,
            "action": f"Spend extra 30 minutes daily on {subj}",
            "strategies": WEAK_SUBJECT_STRATEGIES["general"][:3],
            "goal": "Achieve minimum 50% marks in next assessment",
        }

    # ── Priority actions ─────────────────────────────────────────────────────
    priority_actions = []

    if avg_attendance < 60:
        priority_actions.extend(ATTENDANCE_TIPS["critical"])
    elif avg_attendance < 75:
        priority_actions.extend(ATTENDANCE_TIPS["low"])

    if completion_rate < 70:
        priority_actions.append("🗂️ Complete all pending assignments immediately")
        priority_actions.append("Set submission reminders for upcoming deadlines")

    priority_actions.extend(GRADE_STRATEGIES.get(grade, GRADE_STRATEGIES["C"])[:3])

    # ── Overall recommendations ──────────────────────────────────────────────
    recommendations = []
    recommendations.extend(RISK_STRATEGIES.get(risk, [])[:3])
    recommendations.extend(GRADE_STRATEGIES.get(grade, [])[:2])

    if weak_subjects:
        recommendations.append(
            f"Focus particularly on: {', '.join(weak_subjects[:3])}"
        )

    return {
        "daily_study_hours": daily_hours,
        "weekly_plan": weekly_plan,
        "priority_actions": priority_actions[:6],
        "recommendations": recommendations[:6],
        "weak_subject_plans": weak_subject_plans,
        "motivational_message": _get_motivational_message(grade, risk),
        "attendance_status": _get_attendance_status(avg_attendance),
    }


def _get_motivational_message(grade: str, risk: str) -> str:
    messages = {
        ("A", "Low"): "🌟 Outstanding! You are a top performer. Keep inspiring others!",
        ("B", "Low"): "💪 Great work! A little more effort and you'll reach the top!",
        ("C", "Medium"): "📖 You have potential! Focus and consistency will take you far.",
        ("C", "High"): "⚡ Time to act! Every day of effort brings you closer to success.",
        ("Fail", "High"): "🔥 Don't give up! Many successful people faced setbacks. Start today!",
    }
    return messages.get(
        (grade, risk),
        "🎯 Stay focused, stay consistent. Your hard work will pay off!",
    )


def _get_attendance_status(attendance: float) -> dict:
    if attendance < 60:
        return {"status": "critical", "color": "#ef4444", "message": f"Critical: {attendance:.1f}% — Below minimum"}
    elif attendance < 75:
        return {"status": "low", "color": "#f59e0b", "message": f"Low: {attendance:.1f}% — Below recommended 75%"}
    elif attendance < 90:
        return {"status": "good", "color": "#10b981", "message": f"Good: {attendance:.1f}%"}
    return {"status": "excellent", "color": "#6366f1", "message": f"Excellent: {attendance:.1f}%"}
