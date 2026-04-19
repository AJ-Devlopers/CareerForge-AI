from .pdf_loader import extract_text
from .skill_extractor import extract_skills
from .role_matcher import match_roles
from .llm_service import generate_role_explanation


def run_module1(file_bytes):

    # 1. Extract text from PDF
    text = extract_text(file_bytes)

    # 2. Extract skills
    skills = extract_skills(text)

    # 3. Match roles
    roles = match_roles(skills)

    # 4. Add Groq explanations
    final_roles = []
    for role in roles[:5]:
        role_data = {
            "role": role["role"],
            "match": role["match"],
            "description": generate_role_explanation(role["role"])
        }
        final_roles.append(role_data)

    return {
        "skills": skills,
        "roles": final_roles
    }