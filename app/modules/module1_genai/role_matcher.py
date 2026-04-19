import json
from app.modules.module1_genai.llm_service import enhance_role_skills

with open("app/data/roles_skills_map.json") as f:
    ROLE_MAP = json.load(f)

ROLE_CACHE = {}

def match_roles(skills):
    results = []
    user_skills = [s.lower() for s in skills]

    for role, required_skills in ROLE_MAP.items():
        required = [s.lower() for s in required_skills]

        # 🔥 AI enhancement (safe)
        if role not in ROLE_CACHE:
            extra = enhance_role_skills(role, required) or []
            ROLE_CACHE[role] = extra
        else:
            extra = ROLE_CACHE[role]

        required = list(set(required + extra))

        matched = sorted(list(set(user_skills) & set(required)))
        missing = sorted(list(set(required) - set(user_skills)))

        match_percent = int((len(matched) / len(required)) * 100) if required else 0

        if len(matched) >= 3:
            match_percent += 10

        match_percent = min(match_percent, 100)

        results.append({
            "role": role,
            "match": match_percent,
            "matched_skills": matched,
            "missing_skills": missing[:5],
            "total_required": len(required)
        })

    results.sort(key=lambda x: x["match"], reverse=True)
    return results[:5]