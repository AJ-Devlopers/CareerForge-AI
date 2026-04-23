# app/report_generator/report_builder.py
"""
Report Builder
Assembles all data needed for the PDF report and calls pdf_report.generate_pdf().

This is the single entry point that module3.py calls for PDF generation.
It keeps module3.py clean — no PDF logic lives there.
"""

from app.report_generator.pdf_report import generate_pdf


def build_pdf_report(
    candidate_name:    str,
    ats_score:         int,
    skills_found:      list,
    interview_results: list,
    roadmap_data:      dict,
) -> bytes:
    """
    Thin orchestrator:
    1. Enriches roadmap_data with any missing derived fields
    2. Delegates to pdf_report.generate_pdf()
    3. Returns raw PDF bytes

    Args:
        candidate_name:    Full name from resume
        ats_score:         ATS score 0-100
        skills_found:      List of skill strings
        interview_results: List of interview result dicts from session
        roadmap_data:      Full roadmap dict returned by /module3/generate-roadmap

    Returns:
        bytes: Complete PDF file content
    """

    # ── Compute derived fields if not already in roadmap_data ──
    if "overall_interview_score" not in roadmap_data:
        valid = [r.get("score", 0) for r in interview_results
                if r.get("score", 0) > 0]
        roadmap_data["overall_interview_score"] = (
            round(sum(valid) / len(valid)) if valid else 0
        )

    if "combined_score" not in roadmap_data:
        ov = roadmap_data.get("overall_interview_score", 0)
        if ov:
            roadmap_data["combined_score"] = round(ats_score * 0.4 + ov * 0.6)
        else:
            roadmap_data["combined_score"] = ats_score

    if "grade" not in roadmap_data or not roadmap_data["grade"]:
        cs = roadmap_data.get("combined_score", ats_score)
        if cs >= 85:   roadmap_data["grade"] = "Excellent"
        elif cs >= 70: roadmap_data["grade"] = "Good"
        elif cs >= 55: roadmap_data["grade"] = "Average"
        elif cs >= 40: roadmap_data["grade"] = "Below Average"
        else:          roadmap_data["grade"] = "Needs Work"

    # ── Delegate to PDF generator ──────────────────────────────
    return generate_pdf(
        candidate_name=candidate_name,
        ats_score=ats_score,
        skills_found=skills_found,
        interview_results=interview_results,
        roadmap_data=roadmap_data,
    )