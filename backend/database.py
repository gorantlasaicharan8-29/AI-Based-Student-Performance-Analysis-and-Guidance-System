"""
database.py - SQLAlchemy models and DB initialization.
All tables for the AI Student Performance System are defined here.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()


# ─────────────────────────────────────────────────────────────────────────────
# User Model (Student / Teacher / HOD)
# ─────────────────────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # student | teacher | hod
    department = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    student_profile = db.relationship("Student", back_populates="user", uselist=False)
    assigned_tasks = db.relationship("Assignment", back_populates="teacher", foreign_keys="Assignment.teacher_id")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "department": self.department,
            "created_at": self.created_at.isoformat(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Student Profile
# ─────────────────────────────────────────────────────────────────────────────
class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    roll_number = db.Column(db.String(30), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.Integer, default=1)
    batch = db.Column(db.String(20), nullable=True)

    # Relationships
    user = db.relationship("User", back_populates="student_profile")
    marks = db.relationship("Mark", back_populates="student", cascade="all, delete-orphan")
    submissions = db.relationship("Submission", back_populates="student", cascade="all, delete-orphan")
    predictions = db.relationship("Prediction", back_populates="student", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.user.name if self.user else None,
            "email": self.user.email if self.user else None,
            "roll_number": self.roll_number,
            "department": self.department,
            "semester": self.semester,
            "batch": self.batch,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Subject
# ─────────────────────────────────────────────────────────────────────────────
class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.Integer, default=1)
    max_marks = db.Column(db.Float, default=100.0)

    marks = db.relationship("Mark", back_populates="subject")
    units = db.relationship("Unit", back_populates="subject", cascade="all, delete-orphan",
                            order_by="Unit.unit_number")


    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "department": self.department,
            "semester": self.semester,
            "max_marks": self.max_marks,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Unit (6 units per subject — syllabus structure)
# ─────────────────────────────────────────────────────────────────────────────
class Unit(db.Model):
    __tablename__ = "units"

    id            = db.Column(db.Integer, primary_key=True)
    subject_id    = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    unit_number   = db.Column(db.Integer, nullable=False)   # 1 – 6
    title         = db.Column(db.String(200), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    topics  = db.relationship("Topic", back_populates="unit",
                               cascade="all, delete-orphan", order_by="Topic.order")
    subject = db.relationship("Subject", back_populates="units")

    __table_args__ = (
        db.UniqueConstraint("subject_id", "unit_number", name="uq_subject_unit"),
        db.CheckConstraint("unit_number BETWEEN 1 AND 6", name="ck_unit_number_range"),
    )

    def to_dict(self):
        return {
            "id":          self.id,
            "subject_id":  self.subject_id,
            "unit_number": self.unit_number,
            "title":       self.title,
            "topics":      [t.to_dict() for t in self.topics],
        }


# ─────────────────────────────────────────────────────────────────────────────
# Topic (many topics per unit)
# ─────────────────────────────────────────────────────────────────────────────
class Topic(db.Model):
    __tablename__ = "topics"

    id      = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey("units.id"), nullable=False)
    name    = db.Column(db.String(300), nullable=False)
    order   = db.Column(db.Integer, default=0)

    unit = db.relationship("Unit", back_populates="topics")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "order": self.order}




# ─────────────────────────────────────────────────────────────────────────────
# Mark (subject-wise marks per student)
# ─────────────────────────────────────────────────────────────────────────────
class Mark(db.Model):
    __tablename__ = "marks"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    marks = db.Column(db.Float, nullable=False)
    attendance = db.Column(db.Float, default=0.0)   # percentage 0-100
    assignment_score = db.Column(db.Float, default=0.0)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student", back_populates="marks")
    subject = db.relationship("Subject", back_populates="marks")

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "subject_id": self.subject_id,
            "subject_name": self.subject.name if self.subject else None,
            "marks": self.marks,
            "attendance": self.attendance,
            "assignment_score": self.assignment_score,
            "recorded_at": self.recorded_at.isoformat(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Assignment (created by teachers)
# ─────────────────────────────────────────────────────────────────────────────
class Assignment(db.Model):
    __tablename__ = "assignments"

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    deadline = db.Column(db.DateTime, nullable=True)
    file_path = db.Column(db.String(500), nullable=True)
    original_filename = db.Column(db.String(300), nullable=True)
    target_department = db.Column(db.String(100), nullable=True)  # None = all
    target_student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    teacher = db.relationship("User", back_populates="assigned_tasks", foreign_keys=[teacher_id])
    submissions = db.relationship("Submission", back_populates="assignment", cascade="all, delete-orphan")
    target_student = db.relationship("Student", foreign_keys=[target_student_id])

    def to_dict(self):
        return {
            "id": self.id,
            "teacher_id": self.teacher_id,
            "teacher_name": self.teacher.name if self.teacher else None,
            "title": self.title,
            "description": self.description,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "file_path": self.file_path,
            "original_filename": self.original_filename,
            "target_department": self.target_department,
            "target_student_id": self.target_student_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "submission_count": len(self.submissions),
            "is_active": self.is_active,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Submission (students submit work)
# ─────────────────────────────────────────────────────────────────────────────
class Submission(db.Model):
    __tablename__ = "submissions"

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    file_path = db.Column(db.String(500), nullable=True)
    original_filename = db.Column(db.String(300), nullable=True)
    status = db.Column(db.String(30), default="submitted")  # submitted | reviewed | graded
    grade = db.Column(db.Float, nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    assignment = db.relationship("Assignment", back_populates="submissions")
    student = db.relationship("Student", back_populates="submissions")

    def to_dict(self):
        return {
            "id": self.id,
            "assignment_id": self.assignment_id,
            "assignment_title": self.assignment.title if self.assignment else None,
            "student_id": self.student_id,
            "student_name": self.student.user.name if self.student and self.student.user else None,
            "roll_number": self.student.roll_number if self.student else None,
            "file_path": self.file_path,
            "original_filename": self.original_filename,
            "status": self.status,
            "grade": self.grade,
            "feedback": self.feedback,
            "submitted_at": self.submitted_at.isoformat(),
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }


# ─────────────────────────────────────────────────────────────────────────────
# ML Prediction record
# ─────────────────────────────────────────────────────────────────────────────
class Prediction(db.Model):
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    grade = db.Column(db.String(10), nullable=False)          # A / B / C / Fail
    risk_level = db.Column(db.String(10), nullable=False)     # Low / Medium / High
    confidence = db.Column(db.Float, nullable=True)
    factors = db.Column(db.Text, nullable=True)               # JSON string
    recommendations = db.Column(db.Text, nullable=True)       # JSON string
    average_marks = db.Column(db.Float, nullable=True)
    average_attendance = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student", back_populates="predictions")

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "student_id": self.student_id,
            "grade": self.grade,
            "risk_level": self.risk_level,
            "confidence": self.confidence,
            "factors": json.loads(self.factors) if self.factors else [],
            "recommendations": json.loads(self.recommendations) if self.recommendations else [],
            "average_marks": self.average_marks,
            "average_attendance": self.average_attendance,
            "created_at": self.created_at.isoformat(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Notification
# ─────────────────────────────────────────────────────────────────────────────
class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notification_type = db.Column(db.String(50), default="info")  # info | warning | success

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
            "notification_type": self.notification_type,
        }
