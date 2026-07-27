# AI-Based Student Performance Analysis and Guidance System
## Complete Project Reference — Saved 04 May 2026

---

## 📁 Project Location
```
c:\Users\goran\OneDrive\Desktop\AI-Based Student Performance Analysis and Guidance System\
```

## 💾 Backup Files (Desktop)
| File | Contents |
|------|---------|
| `AI_Student_System_CODE_BACKUP_20260504_2042.zip` | All 38 source code files |
| `AI_Student_System_BACKUP_*.zip` | Full backup (may have DB lock warning — code is intact) |

---

## 🚀 How to Run the System
```bash
# From project root folder:
python backend/app.py

# Then open browser:
http://localhost:5000
```

---

## 🔐 All Login Credentials

### Students
| Name | Email | Password | Roll No |
|------|-------|----------|---------|
| Gorantla Sai Charan | gorantlasaicharan@gmail.com | sai1234 | CS2024003 |
| Sowmith | sowmith@gmail.com | sowmith1234 | CS2024004 |
| Guna Sekhar | guna@gmail.com | guna1234 | CS2024005 |
| Chaitanya | chaitanya@gmail.com | chaitu1234 | CS2024006 |

### Teacher
| Name | Email | Password |
|------|-------|----------|
| Chitra.M | chitramec@gmail.com | chitra1234 |

### HOD
| Name | Email | Password |
|------|-------|----------|
| Ananth.S | ananth@gmail.com | ananth1234 |

---

## 📊 Student Marks Data (Pre-loaded)

### Subjects (5 CS Subjects, Semester 4)
- Data Structures
- Operating Systems
- Database Management
- Computer Networks
- Algorithms

### Per-Student Performance
| Student | Avg Marks | Profile |
|---------|-----------|---------|
| Gorantla Sai Charan | ~80% | Strong |
| Sowmith | ~53% | Needs Improvement |
| Guna Sekhar | ~72% | Average |
| Chaitanya | ~91% | Top Performer |

---

## 📂 Complete File Structure

```
AI-Based Student Performance Analysis and Guidance System/
│
├── backend/
│   ├── app.py                    ← Flask app factory + seeding
│   ├── config.py                 ← Config (DB URI, JWT secret)
│   ├── database.py               ← All SQLAlchemy models
│   ├── add_students.py           ← Student seeding script
│   ├── add_marks.py              ← Marks seeding script
│   │
│   ├── routes/
│   │   ├── auth.py               ← Login / Register / JWT
│   │   ├── student.py            ← Student API endpoints
│   │   ├── teacher.py            ← Teacher API endpoints
│   │   ├── hod.py                ← HOD API endpoints
│   │   └── syllabus.py           ← NEW: Syllabus & Recommendations API
│   │
│   ├── ml/
│   │   ├── predictor.py          ← Random Forest ML model
│   │   └── guidance.py           ← Study guidance generator
│   │
│   └── utils/
│       ├── validators.py         ← Input validation helpers
│       ├── file_handler.py       ← File upload handler
│       └── report_gen.py         ← PDF report generator
│
├── frontend/
│   ├── index.html                ← Login page (Role Picker UI)
│   │
│   ├── student/
│   │   └── index.html            ← Student dashboard
│   │
│   ├── teacher/
│   │   └── index.html            ← Teacher dashboard
│   │
│   ├── hod/
│   │   └── index.html            ← HOD dashboard
│   │
│   ├── css/
│   │   ├── main.css              ← Global styles + variables
│   │   ├── dashboard.css         ← Dashboard layout styles
│   │   └── login.css             ← Login page styles
│   │
│   ├── js/
│   │   ├── api.js                ← Central API client (all endpoints)
│   │   ├── utils.js              ← Shared utilities (toast, modal, etc.)
│   │   ├── student.js            ← Student dashboard logic
│   │   ├── teacher.js            ← Teacher dashboard logic
│   │   ├── hod.js                ← HOD dashboard logic
│   │   ├── teacher_syllabus.js   ← NEW: Syllabus editor + weak areas
│   │   └── hod_syllabus.js       ← NEW: Unit difficulty heat map
│   │
│   └── images/
│       ├── mahendra-logo.jpg     ← Mahendra Educational Institutions logo
│       └── logo.png              ← Graduation cap icon
│
└── requirements.txt              ← Python dependencies
```

---

## 🗄️ Database Models

| Table | Description |
|-------|-------------|
| `users` | Students, Teachers, HODs |
| `students` | Student profiles (roll no, dept, sem) |
| `subjects` | CS subjects |
| `units` | **NEW** — 6 units per subject (syllabus) |
| `topics` | **NEW** — Topics per unit |
| `marks` | Subject-wise marks per student |
| `assignments` | Teacher-created assignments |
| `submissions` | Student submissions |
| `predictions` | ML AI predictions |
| `notifications` | In-app notifications |

---

## 🧠 Syllabus & AI Recommendation Module (NEW)

### Syllabus Structure
- Each subject has **exactly 6 units**
- Each unit has a title + multiple topics
- Pre-seeded for all 5 CS subjects

### AI Recommendation Logic (Rule-Based)
| Student Marks | Performance | Recommended Units | Priority |
|---------------|-------------|-------------------|----------|
| < 50 | Low | Units 1, 2, 3 | 🔴 High |
| 50 – 74 | Medium | Units 3, 4, 5 | 🟡 Medium |
| ≥ 75 | High | Units 5, 6 | 🟢 Low |

### API Endpoints
| Method | URL | Role | Purpose |
|--------|-----|------|---------|
| GET | `/api/syllabus/subjects` | Teacher/HOD | List subjects with syllabus status |
| GET | `/api/syllabus/<id>` | All | Get 6-unit syllabus for a subject |
| POST | `/api/syllabus/<id>` | Teacher/HOD | Save/update 6-unit syllabus |
| GET | `/api/syllabus/recommendations` | Student | Get AI unit recommendations |
| GET | `/api/syllabus/teacher/weak-areas` | Teacher/HOD | Unit-wise weak student report |
| GET | `/api/syllabus/hod/unit-analysis` | HOD | Department unit difficulty heat map |

---

## 🎨 UI Features

### Login Page
- Mahendra Educational Institutions logo
- 3 role cards: Student / Teacher / HOD
- Click role → login form slides in
- Register → automatically switches to login

### Student Dashboard (6 sections)
1. 🏠 Overview — stats + charts + subject table
2. 📊 My Marks — detailed marks with progress bars
3. 🤖 AI Prediction — Run Random Forest prediction
4. 🧭 Guidance Plan — personalized study advice
5. **📚 Study Units** — AI unit recommendations per subject ← NEW
6. 📋 Assignments — view & submit assignments

### Teacher Dashboard (7 sections)
1. 🏠 Overview — student performance table
2. 👨‍🎓 Students — full student list + detail modal
3. 📊 Enter Marks — enter/update subject marks
4. 📋 Assignments — create/manage assignments
5. 📤 Submissions — review student submissions
6. 📚 Subjects — add subjects
7. **📝 Syllabus** — 6-unit editor per subject ← NEW
8. **⚠️ Weak Areas** — unit-wise weak student report ← NEW

### HOD Dashboard (8 sections)
1. 🏠 Dashboard — stats + grade/risk charts
2. 📈 Analytics — subject & trend charts
3. 👨‍🎓 All Students — full searchable list
4. ⚠️ At-Risk Students — high risk alerts
5. ⭐ Top Performers — grade A students
6. 📋 All Assignments — all assignments view
7. 👩‍🏫 Teachers — teacher list
8. **📊 Unit Analysis** — unit difficulty heat map ← NEW

---

## 🔧 Python Dependencies
```
flask
flask-sqlalchemy
flask-jwt-extended
flask-bcrypt
flask-cors
scikit-learn
pandas
numpy
reportlab
python-dotenv
```

Install with: `pip install -r requirements.txt`

---

## ⚙️ Key Configuration (backend/config.py)
- Database: SQLite (`backend/student_system.db`)
- JWT Secret: configured in config.py
- Upload folder: `backend/uploads/`
- Server: `http://localhost:5000`

---

> **Last Updated:** 04 May 2026, 20:40 IST
> **Status:** ✅ Fully functional — all features implemented and tested
