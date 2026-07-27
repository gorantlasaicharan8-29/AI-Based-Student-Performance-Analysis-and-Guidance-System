import sys, os
sys.path.insert(0, os.path.abspath('.'))
from app import create_app
from database import db, User, Student, Notification

app = create_app()
with app.app_context():
    students = [
        {
            "name": "Sowmith",
            "email": "sowmith@gmail.com",
            "password": "sowmith123",
            "roll_number": "CS2024004",
            "department": "Computer Science",
            "semester": 4,
            "batch": "2024",
        },
        {
            "name": "Shaik Ashik",
            "email": "shaikashik@gmail.com",
            "password": "ashik123",
            "roll_number": "CS2024005",
            "department": "Computer Science",
            "semester": 4,
            "batch": "2024",
        },
    ]

    added = 0
    for s in students:
        if User.query.filter_by(email=s["email"]).first():
            print("[SKIP] " + s["name"] + " - email already exists.")
            continue
        if Student.query.filter_by(roll_number=s["roll_number"]).first():
            print("[SKIP] " + s["name"] + " - roll number already taken.")
            continue

        user = User(
            name=s["name"],
            email=s["email"],
            role="student",
            department=s["department"],
            is_active=True
        )
        user.set_password(s["password"])
        db.session.add(user)
        db.session.flush()

        student = Student(
            user_id=user.id,
            roll_number=s["roll_number"],
            department=s["department"],
            semester=s["semester"],
            batch=s["batch"]
        )
        db.session.add(student)

        db.session.add(Notification(
            user_id=user.id,
            title="Welcome to AI Student Performance System!",
            message="Hello " + user.name + "! Your student account is ready. Login to explore your dashboard.",
            notification_type="success"
        ))
        print("[ADD]  " + s["name"] + " | " + s["email"] + " | Roll: " + s["roll_number"])
        added += 1

    db.session.commit()
    print("")
    print("=" * 55)
    print("  DONE: " + str(added) + " student(s) added successfully.")
    print("=" * 55)
    print("")
    print("  Login credentials:")
    print("  Sowmith    | sowmith@gmail.com     | sowmith123")
    print("  Shaik Ashik| shaikashik@gmail.com  | ashik123")
