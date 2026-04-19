from app.modules.module1_genai.pdf_loader import extract_text_from_pdf
from app.modules.module1_genai.skill_extractor import extract_skills
from app.modules.module1_genai.llm_service import extract_skills_ai
from app.modules.module1_genai.role_matcher import match_roles


# 🔹 Clean skills
def clean_skills(skills):
    cleaned = []

    for s in skills:
        s = s.strip()

        if 2 < len(s) < 30 and not s.isdigit():
            cleaned.append(s.title())

    return list(set(cleaned))


# 🔥 MAIN PIPELINE FUNCTION
def run_module1_pipeline(file):

    # 🔹 1. Extract text
    text = extract_text_from_pdf(file)

    if not text or not text.strip():
        return {
            "ats_score": 0,
            "total_skills": 0,
            "skills_found": [],
            "roles": []
        }

    # 🔹 2. Static + AI skills
    static_skills = extract_skills(text)
    ai_skills = extract_skills_ai(text)

    # 🔹 3. Merge + clean
    skills = clean_skills(static_skills + ai_skills)
    skills.sort()

    # 🔹 4. Role matching
    roles = match_roles(skills)

    # 🔹 5. ATS score
    ats_score = min(len(skills) * 8 + 20, 95)

    return {
        "ats_score": ats_score,
        "total_skills": len(skills),
        "skills_found": skills,
        "roles": roles
    }