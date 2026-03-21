"""
utils/pdf_generator.py - Generate professional PDF reports using reportlab.
"""
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT


# ─── Color Palette ─────────────────────────────────────────────────────────────
PRIMARY    = colors.HexColor("#667eea")
SECONDARY  = colors.HexColor("#764ba2")
SUCCESS    = colors.HexColor("#27ae60")
DANGER     = colors.HexColor("#e74c3c")
WARNING    = colors.HexColor("#f39c12")
LIGHT_GRAY = colors.HexColor("#f8f9fa")
DARK       = colors.HexColor("#1a1a2e")
MID_GRAY   = colors.HexColor("#555555")


def get_styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle("title", parent=base["Normal"],
            fontSize=22, fontName="Helvetica-Bold",
            textColor=DARK, spaceAfter=4, alignment=TA_LEFT),
        "subtitle": ParagraphStyle("subtitle", parent=base["Normal"],
            fontSize=11, fontName="Helvetica",
            textColor=MID_GRAY, spaceAfter=16),
        "h1": ParagraphStyle("h1", parent=base["Normal"],
            fontSize=13, fontName="Helvetica-Bold",
            textColor=PRIMARY, spaceBefore=14, spaceAfter=6),
        "h2": ParagraphStyle("h2", parent=base["Normal"],
            fontSize=11, fontName="Helvetica-Bold",
            textColor=DARK, spaceBefore=8, spaceAfter=4),
        "body": ParagraphStyle("body", parent=base["Normal"],
            fontSize=10, fontName="Helvetica",
            textColor=DARK, spaceAfter=4, leading=14),
        "bullet": ParagraphStyle("bullet", parent=base["Normal"],
            fontSize=10, fontName="Helvetica",
            textColor=DARK, spaceAfter=3, leftIndent=16, leading=13),
        "small": ParagraphStyle("small", parent=base["Normal"],
            fontSize=8, fontName="Helvetica",
            textColor=MID_GRAY, spaceAfter=2),
        "badge_green": ParagraphStyle("badge_green", parent=base["Normal"],
            fontSize=10, fontName="Helvetica-Bold",
            textColor=SUCCESS),
        "badge_red": ParagraphStyle("badge_red", parent=base["Normal"],
            fontSize=10, fontName="Helvetica-Bold",
            textColor=DANGER),
        "center": ParagraphStyle("center", parent=base["Normal"],
            fontSize=10, fontName="Helvetica",
            textColor=MID_GRAY, alignment=TA_CENTER),
    }
    return styles


def score_color(score):
    if score >= 7: return SUCCESS
    if score >= 5: return WARNING
    return DANGER


def generate_report_pdf(candidate: dict, analysis: dict, job_role: str) -> bytes:
    """
    Generate a complete professional PDF report for a candidate.
    Returns PDF as bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75*inch, rightMargin=0.75*inch,
        topMargin=0.75*inch, bottomMargin=0.75*inch,
    )

    styles = get_styles()
    story = []
    W = 7.0 * inch  # usable width

    # ── Header Banner ────────────────────────────────────────────────────────
    name = candidate.get("name") or "Unknown Candidate"
    email = candidate.get("email") or "N/A"
    phone = candidate.get("phone") or "N/A"
    experience = candidate.get("experience_years") or 0
    score = analysis.get("score") or 0
    match_pct = analysis.get("match_percentage") or 0
    shortlisted = analysis.get("shortlisted", False)
    rank = analysis.get("rank")

    # Header table
    status_text = "SHORTLISTED" if shortlisted else "NOT SHORTLISTED"
    status_color = SUCCESS if shortlisted else DANGER

    header_data = [[
        Paragraph(f"<b>{name}</b>", ParagraphStyle("hn", fontSize=18,
            fontName="Helvetica-Bold", textColor=colors.white)),
        Paragraph(f"<b>{status_text}</b>", ParagraphStyle("hs", fontSize=12,
            fontName="Helvetica-Bold", textColor=colors.white, alignment=TA_RIGHT)),
    ]]
    header_table = Table(header_data, colWidths=[W*0.65, W*0.35])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PRIMARY),
        ("PADDING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8))

    # Contact info row
    contact_data = [[
        Paragraph(f"Email: {email}", styles["small"]),
        Paragraph(f"Phone: {phone}", styles["small"]),
        Paragraph(f"Experience: {experience} years", styles["small"]),
        Paragraph(f"Role: {job_role}", styles["small"]),
    ]]
    contact_table = Table(contact_data, colWidths=[W/4]*4)
    contact_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
    ]))
    story.append(contact_table)
    story.append(Spacer(1, 14))

    # ── Score Breakdown ───────────────────────────────────────────────────────
    story.append(Paragraph("Score Breakdown", styles["h1"]))
    story.append(HRFlowable(width=W, thickness=1, color=PRIMARY, spaceAfter=8))

    skill_score = analysis.get("skill_match_score") or 0
    exp_score = analysis.get("experience_match_score") or 0
    kw_score = analysis.get("keyword_match_score") or 0

    score_data = [
        ["Metric", "Score", "Rating"],
        ["Overall Score", f"{score:.1f} / 10",
         "Excellent" if score >= 8 else "Good" if score >= 6 else "Fair" if score >= 4 else "Poor"],
        ["Match Percentage", f"{match_pct:.1f}%", ""],
        ["Skill Match", f"{skill_score:.1f} / 10", ""],
        ["Experience Match", f"{exp_score:.1f} / 10", ""],
        ["Keyword Match", f"{kw_score:.1f} / 10", ""],
    ]

    score_table = Table(score_data, colWidths=[W*0.45, W*0.25, W*0.30])
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SECONDARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
        ("FONTNAME", (0, 1), (0, 1), "Helvetica-Bold"),
        ("TEXTCOLOR", (1, 1), (1, 1), score_color(score)),
        ("FONTNAME", (1, 1), (1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (1, 1), (1, 1), 12),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 14))

    # ── Skills ────────────────────────────────────────────────────────────────
    skills = candidate.get("skills") or []
    if skills:
        story.append(Paragraph("Skills", styles["h1"]))
        story.append(HRFlowable(width=W, thickness=1, color=PRIMARY, spaceAfter=6))
        # Display skills in a wrapped grid
        skills_text = "  |  ".join(skills[:24])
        story.append(Paragraph(skills_text, styles["body"]))
        story.append(Spacer(1, 10))

    # ── Education & Work History ───────────────────────────────────────────────
    edu = candidate.get("education") or []
    companies = candidate.get("companies") or []

    if edu or companies:
        left_content = []
        right_content = []

        if edu:
            left_content.append(Paragraph("Education", styles["h2"]))
            for e in edu:
                left_content.append(Paragraph(f"• {e}", styles["bullet"]))

        if companies:
            right_content.append(Paragraph("Work History", styles["h2"]))
            for c in companies:
                right_content.append(Paragraph(f"• {c}", styles["bullet"]))
        else:
            right_content.append(Paragraph("Work History", styles["h2"]))
            right_content.append(Paragraph("No work experience listed.", styles["bullet"]))

        two_col = Table([[left_content, right_content]], colWidths=[W*0.5, W*0.5])
        two_col.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(two_col)
        story.append(Spacer(1, 10))

    # ── AI Reasoning ──────────────────────────────────────────────────────────
    reasoning = analysis.get("reasoning") or ""
    if reasoning and "unavailable" not in reasoning.lower():
        story.append(Paragraph("AI Assessment", styles["h1"]))
        story.append(HRFlowable(width=W, thickness=1, color=PRIMARY, spaceAfter=6))
        story.append(Paragraph(reasoning, styles["body"]))
        story.append(Spacer(1, 10))

    # ── Strengths & Weaknesses ────────────────────────────────────────────────
    strengths = [s for s in (analysis.get("strengths") or []) if s]
    weaknesses = [w for w in (analysis.get("weaknesses") or []) if w]

    story.append(Paragraph("Strengths & Weaknesses", styles["h1"]))
    story.append(HRFlowable(width=W, thickness=1, color=PRIMARY, spaceAfter=6))

    sw_left = [Paragraph("Strengths", ParagraphStyle("sh", fontSize=11,
        fontName="Helvetica-Bold", textColor=SUCCESS, spaceAfter=4))]
    if strengths:
        for s in strengths:
            sw_left.append(Paragraph(f"✓  {s}", ParagraphStyle("sl", fontSize=10,
                fontName="Helvetica", textColor=DARK, spaceAfter=3, leftIndent=8, leading=13)))
    else:
        sw_left.append(Paragraph("No strength data available.", styles["bullet"]))

    sw_right = [Paragraph("Areas for Improvement", ParagraphStyle("wh", fontSize=11,
        fontName="Helvetica-Bold", textColor=DANGER, spaceAfter=4))]
    if weaknesses:
        for w in weaknesses:
            sw_right.append(Paragraph(f"•  {w}", ParagraphStyle("wl", fontSize=10,
                fontName="Helvetica", textColor=DARK, spaceAfter=3, leftIndent=8, leading=13)))
    else:
        sw_right.append(Paragraph("No weakness data available.", styles["bullet"]))

    sw_table = Table([[sw_left, sw_right]], colWidths=[W*0.5, W*0.5])
    sw_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#f0fff4")),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#fff5f5")),
        ("PADDING", (0, 0), (-1, -1), 10),
        ("BOX", (0, 0), (0, 0), 0.5, SUCCESS),
        ("BOX", (1, 0), (1, 0), 0.5, DANGER),
    ]))
    story.append(sw_table)
    story.append(Spacer(1, 14))

    # ── ATS Analysis ──────────────────────────────────────────────────────────
    missing_kw = analysis.get("ats_missing_keywords") or []
    suggestions = analysis.get("ats_suggestions") or []

    story.append(Paragraph("ATS Keyword Analysis", styles["h1"]))
    story.append(HRFlowable(width=W, thickness=1, color=PRIMARY, spaceAfter=6))

    if missing_kw:
        story.append(Paragraph("Missing Keywords:", styles["h2"]))
        story.append(Paragraph("  |  ".join(missing_kw), ParagraphStyle("kw",
            fontSize=9, fontName="Helvetica", textColor=DANGER,
            spaceAfter=8, leading=14)))
    else:
        story.append(Paragraph("No major ATS keyword gaps found.", ParagraphStyle("ok",
            fontSize=10, fontName="Helvetica-Bold", textColor=SUCCESS, spaceAfter=8)))

    if suggestions:
        story.append(Paragraph("Improvement Suggestions:", styles["h2"]))
        for sug in suggestions:
            if sug:
                story.append(Paragraph(f"  {chr(8594)}  {sug}", styles["bullet"]))
    story.append(Spacer(1, 14))

    # ── Recommendation ────────────────────────────────────────────────────────
    story.append(Paragraph("Final Recommendation", styles["h1"]))
    story.append(HRFlowable(width=W, thickness=1, color=PRIMARY, spaceAfter=8))

    rec_text = (
        f"<b>{name}</b> is <b>recommended for further review</b> for the {job_role} role. "
        f"The candidate achieved an overall score of <b>{score:.1f}/10</b> with a "
        f"<b>{match_pct:.1f}% match</b> to the job requirements."
        if shortlisted else
        f"<b>{name}</b> does not currently meet the minimum threshold for the {job_role} role. "
        f"The candidate achieved a score of <b>{score:.1f}/10</b> with a "
        f"<b>{match_pct:.1f}% match</b>. Consider for future openings after skill development."
    )

    rec_style = ParagraphStyle("rec", fontSize=10, fontName="Helvetica",
        textColor=DARK, leading=15, spaceAfter=6,
        borderColor=status_color, borderWidth=1, borderPadding=10,
        backColor=colors.HexColor("#f0fff4") if shortlisted else colors.HexColor("#fff5f5"))
    story.append(Paragraph(rec_text, rec_style))
    story.append(Spacer(1, 16))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width=W, thickness=0.5, color=MID_GRAY, spaceAfter=6))
    story.append(Paragraph(
        "Generated by AI Resume Analyzer  •  Powered by FastAPI + Streamlit",
        styles["center"]
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()