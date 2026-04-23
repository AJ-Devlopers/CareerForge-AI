# app/routers/module3.py
"""
Module 3 Router — Report & Roadmap
All PDF generation is handled by app/modules/report_generator/report_builder.py
All roadmap/suggestion logic is handled by app/modules/module3_agents/
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from io import BytesIO
import os
from app.routers.module1 import report_store

from app.report_generator.report_builder import build_pdf_report

load_dotenv()
router    = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# ── PAGE ─────────────────────────────────────────────────────
@router.get("/module3", response_class=HTMLResponse)
def module3_page(request: Request):
    from app.routers.module1 import report_store

    session_id        = request.session.get("session_id")
    stored            = report_store.get(session_id, {})
    interview_results = request.session.get("interview_results", [])

    candidate_name = stored.get("name", "")
    ats_score      = stored.get("ats_score", 0)
    skills_found   = stored.get("skills_found", [])
    roles          = stored.get("roles", [])
    improvements   = stored.get("improvements", [])
    breakdown      = stored.get("breakdown", {})

    # Default role — prefer top module1 match, fallback to first interview
    default_role = ""
    if roles:
        default_role = roles[0].get("role", "")
    elif interview_results:
        default_role = interview_results[0].get("role", "")

    # Overall interview score
    valid_scores = [r.get("score", 0) for r in interview_results
                    if r.get("score", 0) > 0]
    overall_interview_score = (
        round(sum(valid_scores) / len(valid_scores)) if valid_scores else 0
    )

    return templates.TemplateResponse(
        request=request,
        name="module3.html",
        context={
            "request":                 request,
            "candidate_name":          candidate_name,
            "ats_score":               ats_score,
            "skills_found":            skills_found,
            "roles":                   roles[:5],
            "interview_results":       interview_results,
            "overall_interview_score": overall_interview_score,
            "improvements":            improvements,
            "breakdown":               breakdown,
            "default_role":            default_role,
        }
    )


# ── GENERATE ROADMAP ─────────────────────────────────────────
@router.post("/module3/generate-roadmap")
async def generate_roadmap(request: Request):
    """
    Runs the full agent pipeline:
    report_agent → suggestion_agent + answer_evaluator → roadmap_agent
    Returns everything the frontend needs to render the report.
    """
    from app.routers.module1 import report_store
    from app.modules.module3_agents.agent_graph import run_module3_pipeline

    data = await request.json()
    role     = data.get("role", "Software Engineer")
    duration = data.get("duration", "3 months")
    goal     = data.get("goal", "Get hired")

    session_id        = request.session.get("session_id")
    stored            = report_store.get(session_id, {})
    interview_results = request.session.get("interview_results", [])

    try:
        result = await run_module3_pipeline(
            role=role,
            duration=duration,
            goal=goal,
            candidate_name=stored.get("name", ""),
            ats_score=stored.get("ats_score", 0),
            skills_found=stored.get("skills_found", []),
            interview_results=interview_results,
            improvements=stored.get("improvements", []),
            breakdown=stored.get("breakdown", {}),
            resume_text=stored.get("resume_text", ""),
        )

        valid_scores = [r.get("score", 0) for r in interview_results
                        if r.get("score", 0) > 0]
        overall = round(sum(valid_scores) / len(valid_scores)) if valid_scores else 0

        return JSONResponse({
            # Core fields
            "role":                    role,
            "duration":                duration,
            "goal":                    goal,
            "total_weeks":             result.get("total_weeks", 0),
            # Agent outputs
            "phases":                  result.get("roadmap_phases", []),
            "suggestions":             result.get("suggestions", []),
            "project_ideas":           result.get("project_ideas", []),
            "overall_tips":            result.get("overall_tips", []),
            "interview_analysis":      result.get("interview_analysis", {}),
            "profile_summary":         result.get("profile_summary", ""),
            # Scores + grade
            "combined_score":          result.get("combined_score", 0),
            "grade":                   result.get("grade", ""),
            "overall_interview_score": overall,
            # Weak/strong areas (used by frontend for tips)
            "weak_areas":              result.get("weak_areas", []),
            "strong_areas":            result.get("strong_areas", []),
            # Debug
            "errors":                  result.get("errors", []),
        })

    except Exception as e:
        print(f"❌ module3 pipeline error: {e}")
        import traceback; traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)


# ── DOWNLOAD PDF ─────────────────────────────────────────────
@router.post("/module3/download-pdf")
async def download_pdf(request: Request):
    """
    Generates and streams the PDF report.
    All PDF logic lives in app/modules/report_generator/report_builder.py
    """
    

    data              = await request.json()
    roadmap_data      = data.get("roadmap", {})

    session_id        = request.session.get("session_id")
    stored            = report_store.get(session_id, {})
    interview_results = request.session.get("interview_results", [])

    candidate_name = stored.get("name", "Candidate")
    ats_score      = stored.get("ats_score", 0)
    skills_found   = stored.get("skills_found", [])

    try:
        pdf_bytes = build_pdf_report(
            candidate_name=candidate_name,
            ats_score=ats_score,
            skills_found=skills_found,
            interview_results=interview_results,
            roadmap_data=roadmap_data,
        )
    except Exception as e:
        print(f"❌ PDF generation error: {e}")
        import traceback; traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)

    safe_name = (candidate_name or "career").replace(" ", "_").lower()
    filename  = f"careerforge_{safe_name}_report.pdf"

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )