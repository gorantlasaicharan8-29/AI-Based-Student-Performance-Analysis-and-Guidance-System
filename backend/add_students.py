"""
add_students.py - One-time script to add specific student accounts.
Run from the project root:  python backend/add_students.py
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from database import db, User, Student, Notification

# ── Students to add ────────────────────────────────────────────────────────────
NEW_STUDENTS = [
    {
        "name": "Gorantla Sai Charan",
        "email": "gorantlasaicharan@gmail.com",
        "password": "sai1234",
        "roll_number": "CS2024001",
        "department": "Computer Science",
        "semester": 4,
        "batch": "2024",
    },
    {
        "name": "Charan Kumar",
        "email": "charankumar@gmail.com",
        "password": "charan1234",
        "roll_number": "CS2024002",
        "department": "Computer Science",
        "semester": 4,
        "batch": "2024",
    },
    {
        "name": "Ganesh",
        "email": "ganesh@gmail.com",
        "password": "ganesh1234",
        "roll_number": "CS2024003",
        "department": "Computer Science",
        "semester": 4,
        "batch": "2024",
    },
]


def add_students():
    app = create_app()
    with app.app_context():
        added = 0
        skipped = 0

        for s_data in NEW_STUDENTS:
            # Skip if email already exists
            if User.query.filter_by(email=s_data["email"]).first():
                print(f"  [SKIP] {s_data['name']} — email already exists: {s_data['email']}")
                skipped += 1
                continue

            # Skip if roll number already exists
            if Student.query.filter_by(roll_number=s_data["roll_number"]).first():
                print(f"  [SKIP] {s_data['name']} — roll number taken: {s_data['roll_number']}")
                skipped += 1
                continue

            # Create user account
            user = User(
                name=s_data["name"],
                email=s_data["email"],
                role="student",
                department=s_data["department"],
                is_active=True,
            )
            user.set_password(s_data["password"])
            db.session.add(user)
            db.session.flush()  # get user.id

            # Create student profile
            student = Student(
                user_id=user.id,
                roll_number=s_data["roll_number"],
                department=s_data["department"],
                semester=s_data["semester"],
                batch=s_data.get("batch"),
            )
            db.session.add(student)

            # Welcome notification
            db.session.add(Notification(
                user_id=user.id,
                title="Welcome to AI Student Performance System!",
                message=f"Hello {user.name}! Your student account is ready. Login to explore your dashboard.",
                notification_type="success",
            ))

            print(f"  [ADD]  {s_data['name']:<25} | {s_data['email']:<35} | Roll: {s_data['roll_number']}")
            added += 1

        db.session.commit()

        print(f"\n{'='*60}")
        print(f"  DONE: {added} student(s) added, {skipped} already existed.")
        print(f"{'='*60}")
        print("\n  Login credentials:")
        print(f"  {'Name':<25} {'Email':<35} Password")
        print(f"  {'-'*25} {'-'*35} {'-'*15}")
        for s in NEW_STUDENTS:
            print(f"  {s['name']:<25} {s['email']:<35} {s['password']}")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    add_students()
