# app/modules/module1_genai/pipeline.py

from app.modules.module1_genai.pdf_loader      import extract_text_from_pdf
from app.modules.module1_genai.skill_extractor import extract_skills
from app.modules.module1_genai.llm_service     import extract_skills_ai, extract_candidate_name
from app.modules.module1_genai.role_matcher    import match_roles
from app.modules.module1_genai.ats_scorer      import calculate_ats_score


# ── Clean + deduplicate skills ────────────────────────────
def clean_skills(skills: list) -> list:
    cleaned = []
    seen    = set()

    for s in skills:
        s = s.strip()
        key = s.lower()

        if (
            2 < len(s) < 30
            and not s.isdigit()
            and key not in seen
        ):
            cleaned.append(s.title())
            seen.add(key)

    return sorted(cleaned)


# ── MAIN PIPELINE ─────────────────────────────────────────
def run_module1_pipeline(file) -> dict:

    # Step 1 — extract text
    text = extract_text_from_pdf(file)

    if not text or not text.strip():
        return {
            "name":           "",
            "ats_score":      0,
            "grade":          "Poor",
            "grade_color":    "red",
            "feedback":       "Could not extract text from PDF. Try a different file.",
            "improvements":   [],
            "breakdown":      {},
            "total_skills":   0,
            "skills_found":   [],
            "roles":          [],
            "resume_text":    "",
            "resume_preview": ""
        }

    # Step 2 — extract candidate name (AI)
    try:
        name = extract_candidate_name(text)
    except Exception:
        name = ""

    # Step 3 — extract skills (static keyword match)
    static_skills = extract_skills(text)

    # Step 4 — AI skill extraction via Groq
    try:
        ai_skills = extract_skills_ai(text)
    except Exception:
        ai_skills = []

    # Step 5 — merge + clean
    skills = clean_skills(static_skills + ai_skills)

    # Step 6 — role matching
    roles = match_roles(skills)

    # Step 7 — real ATS scoring (hybrid)
    ats_result = calculate_ats_score(skills, roles, text)

    print(f"✅ Pipeline done — name: '{name}', skills: {len(skills)}, ats: {ats_result['ats_score']}")

    return {
        # ── Candidate ──
        "name":           name,

        # ── ATS ──
        "ats_score":      ats_result["ats_score"],
        "grade":          ats_result["grade"],
        "grade_color":    ats_result["grade_color"],
        "feedback":       ats_result["feedback"],
        "improvements":   ats_result["improvements"],
        "breakdown":      ats_result["breakdown"],

        # ── Skills ──
        "total_skills":   len(skills),
        "skills_found":   skills,

        # ── Roles ──
        "roles":          roles[:5],

        # ── Resume text (stored in report_store, NOT in session cookie) ──
        "resume_text":    text,
        "resume_preview": text[:300].strip() + "..."
    }