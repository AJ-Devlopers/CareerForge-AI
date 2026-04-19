import json
from app.modules.module1_genai.llm_service import enhance_role_skills

# 🔹 Load role-skill mapping
with open("app/data/roles_skills_map.json") as f:
    ROLE_MAP = json.load(f)

# 🔥 Cache to avoid repeated AI calls
ROLE_CACHE = {}


def match_roles(skills):

    results = []

    # 🔹 normalize user skills
    user_skills = [s.lower() for s in skills]

    for role, required_skills in ROLE_MAP.items():

        # base skills
        required = [s.lower() for s in required_skills]

        # 🔥 AI enhancement (cached)
        if role not in ROLE_CACHE:
            extra_skills = enhance_role_skills(role, required)
            ROLE_CACHE[role] = extra_skills
        else:
            extra_skills = ROLE_CACHE[role]

        # merge base + AI skills
        required = list(set(required + extra_skills))

        # 🔹 match calculation
        matched = len(set(user_skills) & set(required))

        if len(required) == 0:
            match_percent = 0
        else:
            match_percent = int((matched / len(required)) * 100)

        # 🔹 boost for strong overlap
        if matched >= 3:
            match_percent += 10

        # cap at 100
        match_percent = min(match_percent, 100)

        results.append({
            "role": role,
            "match": match_percent,
            "matched_skills": matched  # 🔥 useful for UI/debug
        })

    # 🔹 sort by best match
    results.sort(key=lambda x: x["match"], reverse=True)

    return results[:5]