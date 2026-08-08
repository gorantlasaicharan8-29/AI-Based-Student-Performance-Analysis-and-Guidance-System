"""
config.py - Central configuration for the AI Student Performance System.
All settings are read from environment variables or use sensible defaults.
"""

import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "ai-student-system-super-secret-key-2024")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-key-ai-student-2024")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)

    # ── Database ──────────────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:Root%402026%23@localhost:3306/student_performance_db"
    )
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 300}
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── File Uploads ──────────────────────────────────────────────────────────
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "png", "jpg", "jpeg", "txt", "zip", "xlsx", "xls"}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # ── ML Model ──────────────────────────────────────────────────────────────
    ML_MODEL_PATH = os.path.join(BASE_DIR, "ml", "saved_model.pkl")

    # ── Departments ───────────────────────────────────────────────────────────
    DEPARTMENTS = [
        "Computer Science",
        "Information Technology",
        "Electronics",
        "Mechanical",
        "Civil",
        "Electrical",
    ]

    # ── Grade Thresholds ──────────────────────────────────────────────────────
    GRADE_THRESHOLDS = {"A": 85, "B": 70, "C": 50, "Fail": 0}
    STRONG_SUBJECT_THRESHOLD = 75
    WEAK_SUBJECT_THRESHOLD = 50
