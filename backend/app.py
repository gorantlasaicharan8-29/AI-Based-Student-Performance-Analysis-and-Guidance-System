"""
app.py - Flask application entry point.
Initializes the app, database, JWT, ML models, and all API routes.
"""

import os
import sys

# Ensure backend/ is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, send_from_directory
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from config import Config
from database import db, bcrypt, User, Student, Subject


def create_app(config_class=Config):
    app = Flask(__name__, static_folder="../frontend", static_url_path="/static")
    app.config.from_object(config_class)

    # ── Extensions ────────────────────────────────────────────────────────────
    db.init_app(app)
    bcrypt.init_app(app)
    JWTManager(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ── Ensure upload directory exists ────────────────────────────────────────
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "assignments"), exist_ok=True)
    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "submissions"), exist_ok=True)

    # ── ML Model (loaded once at startup) ────────────────────────────────────
    from ml.predictor import StudentPredictor
    from ml.guidance import generate_study_plan
    app.predictor = StudentPredictor(model_path=app.config["ML_MODEL_PATH"])
    app.guidance_engine = generate_study_plan

    # ── Register Blueprints ───────────────────────────────────────────────────
    from routes.auth import auth_bp
    from routes.student import student_bp
    from routes.teacher import teacher_bp
    from routes.hod import hod_bp
    from routes.syllabus import syllabus_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(hod_bp)
    app.register_blueprint(syllabus_bp)

    # ── Database Init ─────────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()
        _seed_initial_data(app)

    # ── Health Check ──────────────────────────────────────────────────────────
    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "message": "AI Student Performance System running"}), 200

    # ── Serve Frontend HTML ───────────────────────────────────────────────────
    @app.route("/")
    def serve_index():
        return send_from_directory("../frontend", "index.html")

    @app.route("/student/")
    @app.route("/student")
    def serve_student():
        return send_from_directory("../frontend/student", "index.html")

    @app.route("/teacher/")
    @app.route("/teacher")
    def serve_teacher():
        return send_from_directory("../frontend/teacher", "index.html")

    @app.route("/hod/")
    @app.route("/hod")
    def serve_hod():
        return send_from_directory("../frontend/hod", "index.html")

    @app.route("/<path:path>")
    def serve_static(path):
        """Serve frontend static files (CSS, JS, etc.)."""
        frontend_dir = os.path.join(os.path.dirname(__file__), "../frontend")
        full = os.path.join(frontend_dir, path)
        if os.path.exists(full) and os.path.isfile(full):
            return send_from_directory(frontend_dir, path)
        return send_from_directory(frontend_dir, "index.html")

    # ── JWT Error Handlers ────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app


def _seed_initial_data(app):
    """Seed demo accounts and subjects if DB is empty."""
    if User.query.count() > 0:
        return  # Already seeded

    print("[Seed] Creating demo accounts and subjects...")

    from database import Notification

    # ── HOD Account ───────────────────────────────────────────────────────────
    hod = User(name="Dr. Rajesh Kumar", email="hod@college.edu", role="hod", department="Computer Science")
    hod.set_password("hod123")
    db.session.add(hod)

    # ── Teacher Accounts ──────────────────────────────────────────────────────
    teachers = [
        User(name="Prof. Anita Sharma", email="teacher@college.edu", role="teacher", department="Computer Science"),
        User(name="Prof. Vijay Patel", email="teacher2@college.edu", role="teacher", department="Information Technology"),
    ]
    for t in teachers:
        t.set_password("teacher123")
        db.session.add(t)

    # ── Subjects ──────────────────────────────────────────────────────────────
    subjects_data = [
        ("Data Structures", "Computer Science", 4),
        ("Operating Systems", "Computer Science", 4),
        ("Database Management", "Computer Science", 4),
        ("Computer Networks", "Computer Science", 4),
        ("Algorithms", "Computer Science", 4),
        ("Web Technologies", "Information Technology", 3),
        ("Software Engineering", "Information Technology", 3),
        ("Python Programming", "Information Technology", 3),
    ]
    for name, dept, sem in subjects_data:
        s = Subject(name=name, department=dept, semester=sem, max_marks=100)
        db.session.add(s)

    # ── Welcome Notifications for staff ───────────────────────────────────────
    db.session.flush()
    for u_email in ["teacher@college.edu", "hod@college.edu"]:
        u = User.query.filter_by(email=u_email).first()
        if u:
            db.session.add(Notification(
                user_id=u.id,
                title="Welcome to AI Student Performance System!",
                message=f"Hello {u.name}! Your {u.role} account is ready. Explore your dashboard.",
                notification_type="success",
            ))

    db.session.commit()
    print("[Seed] Demo accounts created successfully.")
    print("  HOD:     hod@college.edu     / hod123")
    print("  Teacher: teacher@college.edu / teacher123")
    print("  [INFO]   No student accounts seeded — add students via the system.")
    _seed_demo_syllabus()


def _seed_demo_syllabus():
    """Add 6-unit syllabus for each CS subject if not already present."""
    from database import Unit, Topic
    if Unit.query.count() > 0:
        return
    print("[Seed] Creating demo syllabus (6 units per subject)...")

    SYLLABUS = {
        "Data Structures": [
            (1, "Introduction to Data Structures",    ["Arrays", "Linked Lists", "Stacks", "Queues"]),
            (2, "Trees and Binary Trees",              ["Binary Tree", "BST", "Tree Traversals", "AVL Trees"]),
            (3, "Graphs",                              ["Graph Representation", "BFS", "DFS", "Shortest Path"]),
            (4, "Hashing",                             ["Hash Functions", "Collision Resolution", "Hash Tables"]),
            (5, "Heaps and Priority Queues",           ["Min-Heap", "Max-Heap", "Heap Sort", "Priority Queue"]),
            (6, "Advanced Topics",                    ["Tries", "Segment Trees", "Disjoint Sets", "Complexity Analysis"]),
        ],
        "Operating Systems": [
            (1, "OS Fundamentals",                    ["OS Structure", "System Calls", "OS Types"]),
            (2, "Process Management",                 ["Process States", "PCB", "Scheduling Algorithms"]),
            (3, "Memory Management",                  ["Paging", "Segmentation", "Virtual Memory"]),
            (4, "File Systems",                       ["File Concepts", "Directory Structure", "Allocation Methods"]),
            (5, "Deadlocks",                          ["Deadlock Conditions", "Prevention", "Banker's Algorithm"]),
            (6, "I/O and Security",                  ["I/O Hardware", "Disk Scheduling", "Protection & Security"]),
        ],
        "Database Management": [
            (1, "Introduction to DBMS",               ["DBMS Concepts", "ER Model", "Relational Model"]),
            (2, "SQL Fundamentals",                   ["DDL", "DML", "SELECT Queries", "Joins"]),
            (3, "Normalization",                      ["1NF", "2NF", "3NF", "BCNF"]),
            (4, "Transactions & Concurrency",         ["ACID Properties", "Serializability", "Locks"]),
            (5, "Indexing & Query Optimization",      ["B-Tree Index", "Query Plans", "Optimization Techniques"]),
            (6, "Advanced Database Topics",           ["NoSQL", "Distributed DB", "Data Warehousing"]),
        ],
        "Computer Networks": [
            (1, "Network Fundamentals",               ["OSI Model", "TCP/IP Model", "Topologies"]),
            (2, "Data Link Layer",                    ["Framing", "Error Detection", "MAC Protocols"]),
            (3, "Network Layer",                      ["IP Addressing", "Subnetting", "Routing Protocols"]),
            (4, "Transport Layer",                    ["TCP", "UDP", "Flow Control", "Congestion Control"]),
            (5, "Application Layer",                  ["HTTP", "DNS", "FTP", "SMTP", "DHCP"]),
            (6, "Network Security",                  ["Cryptography", "Firewalls", "VPN", "SSL/TLS"]),
        ],
        "Algorithms": [
            (1, "Algorithm Analysis",                 ["Time Complexity", "Space Complexity", "Big-O Notation"]),
            (2, "Sorting & Searching",                ["Merge Sort", "Quick Sort", "Binary Search"]),
            (3, "Divide and Conquer",                 ["Strassen's Algorithm", "Closest Pair", "FFT"]),
            (4, "Dynamic Programming",               ["Memoization", "LCS", "Knapsack", "Matrix Chain"]),
            (5, "Greedy Algorithms",                  ["Huffman Coding", "Kruskal", "Prim's Algorithm"]),
            (6, "NP-Completeness",                   ["P vs NP", "NP-Hard Problems", "Approximation Algorithms"]),
        ],
    }

    from database import Subject
    for subject_name, units_data in SYLLABUS.items():
        subject = Subject.query.filter_by(name=subject_name).first()
        if not subject:
            continue
        for unit_num, title, topics in units_data:
            unit = Unit(subject_id=subject.id, unit_number=unit_num, title=title)
            db.session.add(unit)
            db.session.flush()
            for idx, topic_name in enumerate(topics):
                db.session.add(Topic(unit_id=unit.id, name=topic_name, order=idx))
    db.session.commit()
    print("[Seed] Demo syllabus created for all 5 CS subjects.")


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV", "production") == "development"
    print("\n" + "="*60)
    print(" AI Student Performance System")
    print(f" URL: http://localhost:{port}")
    print("="*60 + "\n")
    app.run(debug=debug, host="0.0.0.0", port=port)
