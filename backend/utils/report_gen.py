"""
utils/report_gen.py - PDF report generation for student performance.
Uses ReportLab to generate structured PDF reports.
"""

import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def generate_student_report(student_data: dict, marks_data: list, prediction: dict, guidance: dict) -> bytes:
    """
    Generate a PDF performance report for a student.
    Returns bytes of the PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    elements = []

    # ── Title ────────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#6366f1"),
        spaceAfter=6,
        alignment=TA_CENTER,
    )
    sub_style = ParagraphStyle(
        "SubTitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=4,
        alignment=TA_CENTER,
    )

    elements.append(Paragraph("AI Student Performance Report", title_style))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}", sub_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#6366f1")))
    elements.append(Spacer(1, 0.2 * inch))

    # ── Student Info ─────────────────────────────────────────────────────────
    section_style = ParagraphStyle("Section", parent=styles["Heading2"], fontSize=13,
                                    textColor=colors.HexColor("#1e293b"), spaceAfter=6)
    body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, spaceAfter=3)

    elements.append(Paragraph("Student Information", section_style))
    info_data = [
        ["Name", student_data.get("name", "N/A"), "Roll Number", student_data.get("roll_number", "N/A")],
        ["Department", student_data.get("department", "N/A"), "Semester", str(student_data.get("semester", "N/A"))],
        ["Email", student_data.get("email", "N/A"), "Report Date", datetime.now().strftime("%Y-%m-%d")],
    ]
    info_table = Table(info_data, colWidths=[1.2 * inch, 2.5 * inch, 1.2 * inch, 2.0 * inch])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#ede9fe")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#ede9fe")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.2 * inch))

    # ── Subject-wise Marks ───────────────────────────────────────────────────
    if marks_data:
        elements.append(Paragraph("Subject-wise Performance", section_style))
        marks_table_data = [["Subject", "Marks (/100)", "Attendance (%)", "Assignment", "Status"]]
        for m in marks_data:
            marks_val = m.get("marks") if m.get("marks") is not None else 0.0
            att_val = m.get("attendance") if m.get("attendance") is not None else 0.0
            assign_val = m.get("assignment_score") if m.get("assignment_score") is not None else 0.0
            status = "✓ Strong" if marks_val > 75 else ("✗ Weak" if marks_val < 50 else "→ Average")
            marks_table_data.append([
                m.get("subject_name", "N/A"),
                f"{marks_val:.1f}",
                f"{att_val:.1f}%",
                f"{assign_val:.1f}",
                status,
            ])

        marks_table = Table(marks_table_data, colWidths=[2.2 * inch, 1.1 * inch, 1.3 * inch, 1.0 * inch, 1.2 * inch])
        marks_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ]))
        elements.append(marks_table)
        elements.append(Spacer(1, 0.2 * inch))

    # ── Prediction ───────────────────────────────────────────────────────────
    if prediction:
        elements.append(Paragraph("AI Prediction Results", section_style))
        analytics = prediction.get("analytics", {})
        avg_m = analytics.get("average_marks") if analytics.get("average_marks") is not None else 0.0
        avg_att = analytics.get("average_attendance") if analytics.get("average_attendance") is not None else 0.0
        conf = prediction.get("confidence") if prediction.get("confidence") is not None else 0.0
        pred_data = [
            ["Predicted Grade", str(prediction.get("grade", "N/A")), "Risk Level", str(prediction.get("risk_level", "N/A"))],
            ["Average Marks", f"{avg_m:.1f}%", "Confidence", f"{conf:.1f}%"],
            ["Avg Attendance", f"{avg_att:.1f}%", "Weak Subjects", str(analytics.get("num_weak_subjects", 0))],
        ]
        pred_table = Table(pred_data, colWidths=[1.5 * inch, 2.0 * inch, 1.5 * inch, 2.0 * inch])
        pred_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#ede9fe")),
            ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#ede9fe")),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(pred_table)
        elements.append(Spacer(1, 0.15 * inch))

        # Key factors
        factors = prediction.get("factors", [])
        if factors:
            elements.append(Paragraph("Key Factors", ParagraphStyle("KF", parent=styles["Heading3"], fontSize=11)))
            for f in factors[:5]:
                icon = "+" if f.get("impact") == "positive" else ("-" if f.get("impact") == "negative" else "~")
                elements.append(Paragraph(
                    f"  {icon} {f.get('factor', '')} — {f.get('value', '')}",
                    body_style
                ))
        elements.append(Spacer(1, 0.15 * inch))

    # ── Recommendations ──────────────────────────────────────────────────────
    if guidance:
        elements.append(Paragraph("Personalized Recommendations", section_style))
        recs = guidance.get("recommendations", [])
        for i, rec in enumerate(recs[:6], 1):
            elements.append(Paragraph(f"  {i}. {rec}", body_style))

        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph(
            guidance.get("motivational_message", ""),
            ParagraphStyle("Motivate", parent=styles["Normal"], fontSize=10,
                           textColor=colors.HexColor("#6366f1"), italic=True)
        ))

    # ── Footer ───────────────────────────────────────────────────────────────
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))
    elements.append(Paragraph(
        "AI-Based Student Performance Analysis and Guidance System — Confidential",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8,
                       textColor=colors.HexColor("#94a3b8"), alignment=TA_CENTER)
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()
