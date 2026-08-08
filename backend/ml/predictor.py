"""
ml/predictor.py - Machine Learning prediction engine.

Uses Random Forest (primary) + Decision Tree (secondary) to predict:
  - Final grade: A / B / C / Fail
  int(input("enterr the following attribute to the following i"))
  - Risk level: Low / Medium / High

Provides Explainable AI: key factors affecting the prediction.
"""

import os
import json
import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score

# ─── Feature names used for Explainable AI ────────────────────────────────────
FEATURE_NAMES = [
    "average_marks",
    "average_attendance",
    "average_assignment_score",
    "num_weak_subjects",
    "num_strong_subjects",
    "completion_rate",
    "semester",
]

# ─── Grade thresholds (rule-based fallback) ────────────────────────────────────
GRADE_THRESHOLDS = {"A": 85, "B": 70, "C": 50}


def compute_grade_from_marks(avg_marks: float) -> str:
    """Rule-based grade computation used for training data generation."""
    if avg_marks >= 85:
        return "A"
    elif avg_marks >= 70:
        return "B"
    elif avg_marks >= 50:
        return "C"
    return "Fail"


def compute_risk_from_features(avg_marks: float, avg_attendance: float, num_weak: int) -> str:
    """Rule-based risk computation used for training data generation."""
    score = 0
    if avg_marks < 50:
        score += 3
    elif avg_marks < 65:
        score += 1
    if avg_attendance < 60:
        score += 3
    elif avg_attendance < 75:
        score += 1
    if num_weak >= 3:
        score += 2
    elif num_weak >= 1:
        score += 1

    if score >= 5:
        return "High"
    elif score >= 2:
        return "Medium"
    return "Low"


def generate_synthetic_training_data(n_samples: int = 2000):
    """
    Generate synthetic training data since we don't have real historical data yet.
    In production, this would be replaced with real historical student records.
    """
    np.random.seed(42)
    X, y_grade, y_risk = [], [], []

    for _ in range(n_samples):
        avg_marks = np.random.uniform(20, 100)
        avg_attendance = np.random.uniform(40, 100)
        avg_assignment = np.random.uniform(30, 100)
        num_weak = int(np.random.poisson(max(0, (60 - avg_marks) / 15)))
        num_weak = min(num_weak, 8)
        num_strong = int(np.random.poisson(max(0, (avg_marks - 60) / 12)))
        num_strong = min(num_strong, 8)
        completion_rate = np.random.uniform(0.4, 1.0)
        semester = np.random.randint(1, 9)

        # Add noise to make it realistic
        avg_marks += np.random.normal(0, 3)
        avg_marks = np.clip(avg_marks, 0, 100)

        features = [avg_marks, avg_attendance, avg_assignment, num_weak, num_strong, completion_rate, semester]
        X.append(features)
        y_grade.append(compute_grade_from_marks(avg_marks))
        y_risk.append(compute_risk_from_features(avg_marks, avg_attendance, num_weak))

    return np.array(X), y_grade, y_risk


class StudentPredictor:
    """
    Main ML prediction class.
    Wraps Random Forest models for grade and risk prediction.
    """

    def __init__(self, model_path: str = None):
        self.model_path = model_path
        self.grade_model = None
        self.risk_model = None
        self.grade_encoder = LabelEncoder()
        self.risk_encoder = LabelEncoder()
        self.is_trained = False
        self._load_or_train()

    def _load_or_train(self):
        """Load pre-trained model or train a new one."""
        if self.model_path and os.path.exists(self.model_path):
            try:
                self._load_model()
                return
            except Exception as e:
                print(f"[Predictor] Could not load model: {e}. Retraining...")

        self.train()

    def train(self):
        """Train Random Forest models on synthetic (or real) data."""
        print("[Predictor] Generating training data...")
        X, y_grade, y_risk = generate_synthetic_training_data(n_samples=3000)

        # Encode labels
        y_grade_enc = self.grade_encoder.fit_transform(y_grade)
        y_risk_enc = self.risk_encoder.fit_transform(y_risk)

        X_train, X_test, yg_train, yg_test, yr_train, yr_test = train_test_split(
            X, y_grade_enc, y_risk_enc, test_size=0.2, random_state=42
        )

        # Train grade model (Random Forest)
        print("[Predictor] Training grade model (Random Forest)...")
        self.grade_model = RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
        )
        self.grade_model.fit(X_train, yg_train)
        grade_acc = accuracy_score(yg_test, self.grade_model.predict(X_test))
        print(f"[Predictor] Grade model accuracy: {grade_acc:.2%}")

        # Train risk model (Random Forest)
        print("[Predictor] Training risk model (Random Forest)...")
        self.risk_model = RandomForestClassifier(
            n_estimators=100, max_depth=8, random_state=42, n_jobs=-1
        )
        self.risk_model.fit(X_train, yr_train)
        risk_acc = accuracy_score(yr_test, self.risk_model.predict(X_test))
        print(f"[Predictor] Risk model accuracy: {risk_acc:.2%}")

        self.is_trained = True

        # Persist model
        if self.model_path:
            self._save_model()

    def _save_model(self):
        """Pickle the trained models to disk."""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, "wb") as f:
            pickle.dump(
                {
                    "grade_model": self.grade_model,
                    "risk_model": self.risk_model,
                    "grade_encoder": self.grade_encoder,
                    "risk_encoder": self.risk_encoder,
                },
                f,
            )
        print(f"[Predictor] Model saved to {self.model_path}")

    def _load_model(self):
        """Load pickled models from disk."""
        with open(self.model_path, "rb") as f:
            data = pickle.load(f)
        self.grade_model = data["grade_model"]
        self.risk_model = data["risk_model"]
        self.grade_encoder = data["grade_encoder"]
        self.risk_encoder = data["risk_encoder"]
        self.is_trained = True
        print("[Predictor] Model loaded from disk.")

    def build_feature_vector(self, student_marks: list) -> dict:
        """
        Compute features from a list of mark dicts.
        Each dict: {subject_name, marks, attendance, assignment_score}
        Returns feature dict and analytics.
        """
        if not student_marks:
            return None

        all_marks = [m["marks"] for m in student_marks]
        all_attendance = [m["attendance"] for m in student_marks]
        all_assignment = [m["assignment_score"] for m in student_marks]

        avg_marks = np.mean(all_marks)
        avg_attendance = np.mean(all_attendance)
        avg_assignment = np.mean(all_assignment)
        num_weak = sum(1 for m in all_marks if m < 50)
        num_strong = sum(1 for m in all_marks if m > 75)
        completion_rate = sum(1 for a in all_assignment if a > 0) / max(len(all_assignment), 1)

        weak_subjects = [
            m["subject_name"] for m in student_marks if m["marks"] < 50
        ]
        strong_subjects = [
            m["subject_name"] for m in student_marks if m["marks"] > 75
        ]

        return {
            "features": [avg_marks, avg_attendance, avg_assignment, num_weak, num_strong, completion_rate, 1],
            "analytics": {
                "average_marks": round(avg_marks, 2),
                "average_attendance": round(avg_attendance, 2),
                "average_assignment_score": round(avg_assignment, 2),
                "num_weak_subjects": num_weak,
                "num_strong_subjects": num_strong,
                "weak_subjects": weak_subjects,
                "strong_subjects": strong_subjects,
                "total_marks": round(sum(all_marks), 2),
                "completion_rate": round(completion_rate * 100, 1),
            },
        }

    def predict(self, student_marks: list, semester: int = 1) -> dict:
        """
        Main prediction method.
        Returns grade, risk_level, confidence, key_factors, analytics.
        """
        if not self.is_trained:
            raise RuntimeError("Model is not trained yet.")

        feature_data = self.build_feature_vector(student_marks)
        if feature_data is None:
            raise ValueError("No marks data provided for prediction.")

        features = feature_data["features"]
        features[6] = semester  # update semester
        X = np.array([features])

        # Grade prediction
        grade_pred_enc = self.grade_model.predict(X)[0]
        grade_proba = self.grade_model.predict_proba(X)[0]
        grade = self.grade_encoder.inverse_transform([grade_pred_enc])[0]
        grade_confidence = float(np.max(grade_proba))

        # Risk prediction
        risk_pred_enc = self.risk_model.predict(X)[0]
        risk = self.risk_encoder.inverse_transform([risk_pred_enc])[0]

        # Explainable AI: feature importance → human-readable factors
        factors = self._get_key_factors(features, grade, risk)

        return {
            "grade": grade,
            "risk_level": risk,
            "confidence": round(grade_confidence * 100, 1),
            "factors": factors,
            "analytics": feature_data["analytics"],
        }

    def _get_key_factors(self, features: list, grade: str, risk: str) -> list:
        """
        Generate human-readable explanation for the prediction
        based on feature importances and thresholds.
        """
        avg_marks, avg_attendance, avg_assignment, num_weak, num_strong, completion_rate, semester = features
        factors = []

        # Marks analysis
        if avg_marks >= 85:
            factors.append({"factor": "Excellent academic marks", "impact": "positive", "value": f"{avg_marks:.1f}%"})
        elif avg_marks >= 70:
            factors.append({"factor": "Good academic marks", "impact": "positive", "value": f"{avg_marks:.1f}%"})
        elif avg_marks >= 50:
            factors.append({"factor": "Average academic marks — room for improvement", "impact": "neutral", "value": f"{avg_marks:.1f}%"})
        else:
            factors.append({"factor": "Low marks — immediate attention needed", "impact": "negative", "value": f"{avg_marks:.1f}%"})

        # Attendance analysis
        if avg_attendance < 60:
            factors.append({"factor": "Critical attendance shortage", "impact": "negative", "value": f"{avg_attendance:.1f}%"})
        elif avg_attendance < 75:
            factors.append({"factor": "Attendance below recommended threshold", "impact": "negative", "value": f"{avg_attendance:.1f}%"})
        else:
            factors.append({"factor": "Good attendance record", "impact": "positive", "value": f"{avg_attendance:.1f}%"})

        # Weak subjects
        if num_weak > 0:
            factors.append({"factor": f"{int(num_weak)} subject(s) below passing threshold", "impact": "negative", "value": f"{int(num_weak)} subjects"})

        # Strong subjects
        if num_strong > 0:
            factors.append({"factor": f"{int(num_strong)} subject(s) above distinction threshold", "impact": "positive", "value": f"{int(num_strong)} subjects"})

        # Assignment completion
        if completion_rate < 0.6:
            factors.append({"factor": "Low assignment completion rate", "impact": "negative", "value": f"{completion_rate*100:.0f}%"})
        elif completion_rate >= 0.9:
            factors.append({"factor": "Excellent assignment completion", "impact": "positive", "value": f"{completion_rate*100:.0f}%"})

        return factors
