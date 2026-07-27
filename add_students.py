"""
add_students.py - One-time script to add specific student accounts.
Run from the project root: python add_students.py
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app import create_app
from backend.database import db, User, Student, Notification

# ── Students to add ────────────────────────────────────────────────────────────
NEW_STUDENTS = [
    {
        "name": "Gorantla Sai Charan",
        "email": "gorantlasaicharan@gmail.com",
        "password": "sai1234",
        "roll_number": "CS2024003",
        "department": "Computer Science",
        "semester": 4,
        "batch": "2024",
    },
    {
        "name": "Sowmith",
        "email": "sowmith@gmail.com",
        "password": "sowmith1234",
        "roll_number": "CS2024004",
        "department": "Computer Science",
        "semester": 4,
        "batch": "2024",
    },
    {
        "name": "Guna Sekhar",
        "email": "guna@gmail.com",
        "password": "guna1234",
        "roll_number": "CS2024005",
        "department": "Computer Science",
        "semester": 4,
        "batch": "2024",
    },
    {
        "name": "Chaitanya",
        "email": "chaitanya@gmail.com",
        "password": "chaitu1234",
        "roll_number": "CS2024006",
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
            # Check if email already exists
            if User.query.filter_by(email=s_data["email"]).first():
                print(f"  [SKIP] {s_data['name']} — email already exists: {s_data['email']}")
                skipped += 1
                continue

            # Check roll number
            if Student.query.filter_by(roll_number=s_data["roll_number"]).first():
                print(f"  [SKIP] {s_data['name']} — roll number already exists: {s_data['roll_number']}")
                skipped += 1
                continue

            # Create user
            user = User(
                name=s_data["name"],
                email=s_data["email"],
                role="student",
                department=s_data["department"],
                is_active=True,
            )
            user.set_password(s_data["password"])
            db.session.add(user)
            db.session.flush()

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
            notif = Notification(
                user_id=user.id,
                title="Welcome to AI Student Performance System!",
                message=f"Hello {user.name}! Your student account is ready. Explore your dashboard.",
                notification_type="success",
            )
            db.session.add(notif)

            print(f"  [ADD]  {s_data['name']} ({s_data['email']}) — Roll: {s_data['roll_number']}")
            added += 1

        db.session.commit()
        print(f"\n✅ Done! {added} student(s) added, {skipped} skipped.")
        print("\nStudent login credentials:")
        print("-" * 55)
        for s in NEW_STUDENTS:
            print(f"  {s['name']:<25} {s['email']:<35} Pass: {s['password']}")
        print("-" * 55)


if __name__ == "__main__":
    add_students()
