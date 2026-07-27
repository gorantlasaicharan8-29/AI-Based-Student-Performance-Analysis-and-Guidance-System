"""
add_marks.py - Add subject marks for the 4 named students.
Run from project root: python backend/add_marks.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from database import db, User, Student, Subject, Mark

# ── Marks data for each student ────────────────────────────────────────────────
# Format: email -> { subject_name: (marks, attendance, assignment_score) }
STUDENT_MARKS = {
    "gorantlasaicharan@gmail.com": {
        "Data Structures":    (88, 92, 90),
        "Operating Systems":  (74, 80, 78),
        "Database Management":(91, 88, 93),
        "Computer Networks":  (65, 75, 70),
        "Algorithms":         (85, 90, 88),
    },
    "sowmith@gmail.com": {
        "Data Structures":    (55, 68, 60),
        "Operating Systems":  (48, 60, 50),
        "Database Management":(62, 72, 65),
        "Computer Networks":  (44, 55, 48),
        "Algorithms":         (58, 65, 55),
    },
    "guna@gmail.com": {
        "Data Structures":    (72, 80, 75),
        "Operating Systems":  (66, 74, 68),
        "Database Management":(78, 85, 80),
        "Computer Networks":  (70, 78, 72),
        "Algorithms":         (75, 82, 76),
    },
    "chaitanya@gmail.com": {
        "Data Structures":    (93, 95, 95),
        "Operating Systems":  (88, 90, 90),
        "Database Management":(96, 94, 97),
        "Computer Networks":  (85, 88, 86),
        "Algorithms":         (91, 93, 92),
    },
}


def add_marks():
    app = create_app()
    with app.app_context():
        total_added = 0
        total_skipped = 0

        for email, subjects_data in STUDENT_MARKS.items():
            # Get user
            user = User.query.filter_by(email=email).first()
            if not user:
                print(f"  [SKIP] User not found: {email}")
                continue

            # Get student profile
            student = Student.query.filter_by(user_id=user.id).first()
            if not student:
                print(f"  [SKIP] Student profile not found for: {email}")
                continue

            print(f"\n  [{user.name}] (Roll: {student.roll_number})")

            for subject_name, (marks, attendance, assignment_score) in subjects_data.items():
                # Find subject in DB
                subject = Subject.query.filter_by(name=subject_name).first()
                if not subject:
                    print(f"    [SKIP] Subject not found: {subject_name}")
                    continue

                # Check if mark already exists
                existing = Mark.query.filter_by(
                    student_id=student.id,
                    subject_id=subject.id
                ).first()

                if existing:
                    # Update existing mark
                    existing.marks = marks
                    existing.attendance = attendance
                    existing.assignment_score = assignment_score
                    print(f"    [UPDATE] {subject_name:<25} Marks:{marks:>3}  Att:{attendance:>3}%  Assign:{assignment_score:>3}")
                else:
                    # Insert new mark
                    db.session.add(Mark(
                        student_id=student.id,
                        subject_id=subject.id,
                        marks=marks,
                        attendance=attendance,
                        assignment_score=assignment_score,
                    ))
                    print(f"    [ADD]    {subject_name:<25} Marks:{marks:>3}  Att:{attendance:>3}%  Assign:{assignment_score:>3}")
                    total_added += 1

        db.session.commit()

        print(f"\n{'='*60}")
        print(f"  DONE: {total_added} mark record(s) added/updated.")
        print(f"{'='*60}")
        print("""
  Summary:
  Gorantla Sai Charan  - Strong performer, avg ~80%
  Sowmith              - Needs improvement, avg ~53%
  Guna Sekhar          - Average performer, avg ~72%
  Chaitanya            - Top performer, avg ~91%
""")


if __name__ == "__main__":
    add_marks()
