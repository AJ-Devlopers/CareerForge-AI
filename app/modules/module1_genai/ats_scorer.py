import os
import re
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ── Cache to avoid repeated LLM calls ────────────────────
LLM_CACHE = {}


# =========================================================
# 🔹 SECTION 1 — KEYWORD & SKILLS SCORE (max 25)
# =========================================================
def score_skills_keywords(skills: list, text: str) -> dict:
    """
    Real ATS: not just skill count but skill RELEVANCE and DENSITY.
    """
    text_lower = text.lower()

    # Tier 1 — high value skills (2 pts each, max 16)
    tier1 = [
        "machine learning", "deep learning", "nlp", "langchain",
        "tensorflow", "pytorch", "docker", "kubernetes",
        "aws", "azure", "gcp", "fastapi", "django",
        "react", "microservices", "ci/cd", "langraph",
        "chromadb", "huggingface", "transformers"
    ]

    # Tier 2 — standard skills (1 pt each, max 9)
    tier2 = [
        "python", "java", "sql", "javascript", "git",
        "linux", "rest api", "flask", "mongodb", "postgresql",
        "typescript", "nodejs", "graphql", "redis", "spark"
    ]

    tier1_found = [s for s in tier1 if s in text_lower]
    tier2_found = [s for s in tier2 if s in text_lower]

    tier1_score = min(len(tier1_found) * 2, 16)
    tier2_score = min(len(tier2_found) * 1, 9)

    raw = tier1_score + tier2_score
    final = min(raw, 25)

    return {
        "score": final,
        "max": 25,
        "label": "Skills & Keywords",
        "tier1_found": tier1_found,
        "tier2_found": tier2_found,
        "details": f"{len(tier1_found)} high-value + {len(tier2_found)} standard skills"
    }


# =========================================================
# 🔹 SECTION 2 — RESUME STRUCTURE / SECTIONS (max 15)
# =========================================================
def score_resume_structure(text: str) -> dict:
    """
    Real ATS: checks if all critical resume sections exist.
    Missing sections = heavy penalty.
    """
    text_lower = text.lower()

    sections = {
        "contact":     ["email", "phone", "linkedin", "github", "contact"],
        "education":   ["education", "degree", "university", "college", "b.tech", "btech", "bachelor"],
        "experience":  ["experience", "internship", "work", "employment", "job"],
        "skills":      ["skills", "technical skills", "technologies", "tools"],
        "projects":    ["projects", "project", "built", "developed", "created"],
        "achievements":["achievement", "award", "certification", "certifications", "courses"]
    }

    weights = {
        "contact":      3,
        "education":    3,
        "experience":   3,
        "skills":       2,
        "projects":     2,
        "achievements": 2
    }

    found = {}
    total = 0

    for section, keywords in sections.items():
        present = any(k in text_lower for k in keywords)
        found[section] = present
        if present:
            total += weights[section]

    missing = [s for s, v in found.items() if not v]

    return {
        "score": min(total, 15),
        "max": 15,
        "label": "Resume Structure",
        "sections_found": [s for s, v in found.items() if v],
        "sections_missing": missing,
        "details": f"{len([v for v in found.values() if v])}/6 sections detected"
    }


# =========================================================
# 🔹 SECTION 3 — QUANTIFICATION & IMPACT (max 15)
# =========================================================
def score_quantification(text: str) -> dict:
    """
    Real ATS: resumes with numbers/metrics rank significantly higher.
    e.g. "improved speed by 40%" vs "improved speed"
    """
    text_lower = text.lower()

    score = 0

    # Check for numbers/metrics in resume
    number_pattern = re.findall(r'\b\d+[\%\+]?\b', text)
    metric_count = len(number_pattern)

    if metric_count >= 10:
        score += 7
    elif metric_count >= 5:
        score += 5
    elif metric_count >= 2:
        score += 3
    elif metric_count >= 1:
        score += 1

    # Impact phrases
    impact_phrases = [
        "reduced", "improved", "increased", "optimized",
        "achieved", "delivered", "generated", "saved",
        "accelerated", "boosted", "scaled", "automated"
    ]
    impact_found = [p for p in impact_phrases if p in text_lower]
    score += min(len(impact_found) * 1, 8)

    return {
        "score": min(score, 15),
        "max": 15,
        "label": "Quantification & Impact",
        "metrics_found": metric_count,
        "impact_verbs": len(impact_found),
        "details": f"{metric_count} numbers found, {len(impact_found)} impact verbs"
    }


# =========================================================
# 🔹 SECTION 4 — ACTION VERBS QUALITY (max 10)
# =========================================================
def score_action_verbs(text: str) -> dict:
    """
    Real ATS: strong action verbs = higher ranking.
    Weak verbs like "helped", "assisted" score lower.
    """
    text_lower = text.lower()

    strong_verbs = [
        "architected", "engineered", "spearheaded", "orchestrated",
        "deployed", "implemented", "developed", "designed",
        "built", "created", "launched", "integrated",
        "optimized", "automated", "scaled", "led", "mentored"
    ]

    weak_verbs = [
        "helped", "assisted", "participated", "supported",
        "worked on", "involved in", "responsible for"
    ]

    strong_found = [v for v in strong_verbs if v in text_lower]
    weak_found   = [v for v in weak_verbs if v in text_lower]

    score = min(len(strong_found) * 1, 10)
    score = max(0, score - len(weak_found))

    return {
        "score": min(score, 10),
        "max": 10,
        "label": "Action Verbs",
        "strong_count": len(strong_found),
        "weak_count": len(weak_found),
        "details": f"{len(strong_found)} strong verbs, {len(weak_found)} weak verbs"
    }


# =========================================================
# 🔹 SECTION 5 — EDUCATION RELEVANCE (max 10)
# =========================================================
def score_education(text: str) -> dict:
    """
    Real ATS: checks degree level, CGPA, relevant field.
    """
    text_lower = text.lower()
    score = 0

    # Degree level
    if any(k in text_lower for k in ["b.tech", "btech", "b.e", "bachelor of technology"]):
        score += 4
    elif any(k in text_lower for k in ["m.tech", "mtech", "master", "mba"]):
        score += 5
    elif any(k in text_lower for k in ["diploma", "12th", "hsc"]):
        score += 2

    # Relevant field
    if any(k in text_lower for k in ["computer science", "cse", "information technology", "it", "software"]):
        score += 3

    # CGPA / GPA
    cgpa_match = re.search(r'(?:cgpa|gpa)[:\s]*([0-9]\.[0-9]+)', text_lower)
    if cgpa_match:
        cgpa = float(cgpa_match.group(1))
        if cgpa >= 8.5:
            score += 3
        elif cgpa >= 7.5:
            score += 2
        elif cgpa >= 6.5:
            score += 1

    return {
        "score": min(score, 10),
        "max": 10,
        "label": "Education",
        "details": "Degree, field relevance, and CGPA evaluated"
    }


# =========================================================
# 🔹 SECTION 6 — ROLE MATCH SCORE (max 15)
# =========================================================
def score_role_match(roles: list) -> dict:
    """
    Real ATS: how well the resume matches the target role.
    """
    if not roles:
        return {"score": 0, "max": 15, "label": "Role Match", "details": "No roles matched"}

    top_match = roles[0]["match"]
    second_match = roles[1]["match"] if len(roles) > 1 else 0

    # Weighted: top role matters most
    raw = int((top_match * 0.7 + second_match * 0.3) / 100 * 15)

    return {
        "score": min(raw, 15),
        "max": 15,
        "label": "Role Match",
        "top_role": roles[0]["role"],
        "top_pct": top_match,
        "details": f"Best match: {roles[0]['role']} at {top_match}%"
    }


# =========================================================
# 🔹 SECTION 7 — LLM DEEP ANALYSIS (max 10)
# =========================================================
def llm_deep_score(text: str, skills: list) -> dict:
    """
    Groq LLM evaluates what rule-based scoring misses:
    - Project real-world impact
    - Writing quality and clarity
    - Overall professional impression
    """
    cache_key = text[:400]
    if cache_key in LLM_CACHE:
        cached = LLM_CACHE[cache_key]
        return {
            "score": cached,
            "max": 10,
            "label": "AI Deep Analysis",
            "details": "Cached result",
            "from_cache": True
        }

    prompt = f"""
You are a senior ATS (Applicant Tracking System) evaluating a resume.
Rate this resume on the following criteria from 0 to 10:

1. Project real-world impact (are projects meaningful or just tutorials?)
2. Writing clarity and professionalism
3. Overall ATS optimization

Skills detected: {', '.join(skills[:10])}

Resume (first 1000 chars):
{text[:1000]}

STRICT RULES:
- Return ONLY a single integer from 0 to 10
- No explanation, no text, just the number
- Example output: 7
"""

    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5,
            temperature=0.1
        )
        output = res.choices[0].message.content.strip()
        match  = re.search(r'\b([0-9]|10)\b', output)
        score  = int(match.group()) if match else 5
        score  = max(0, min(score, 10))

    except Exception as e:
        print(f"LLM Score Error: {e}")
        score = 5

    LLM_CACHE[cache_key] = score

    return {
        "score": score,
        "max": 10,
        "label": "AI Deep Analysis",
        "details": "Groq LLaMA3 evaluated project quality and writing",
        "from_cache": False
    }


# =========================================================
# 🔹 MAIN FUNCTION — HYBRID ATS SCORER
# =========================================================
def calculate_ats_score(skills: list, roles: list, text: str) -> dict:
    """
    Real-world hybrid ATS scoring system.

    Breakdown (total = 100):
    ┌─────────────────────────────────┬──────┐
    │ Component                       │ Max  │
    ├─────────────────────────────────┼──────┤
    │ Skills & Keywords               │  25  │
    │ Resume Structure / Sections     │  15  │
    │ Quantification & Impact         │  15  │
    │ Role Match                      │  15  │
    │ Action Verbs Quality            │  10  │
    │ Education Relevance             │  10  │
    │ AI Deep Analysis (Groq)         │  10  │
    ├─────────────────────────────────┼──────┤
    │ TOTAL                           │ 100  │
    └─────────────────────────────────┴──────┘
    """

    # Run all scorers
    s1 = score_skills_keywords(skills, text)
    s2 = score_resume_structure(text)
    s3 = score_quantification(text)
    s4 = score_action_verbs(text)
    s5 = score_education(text)
    s6 = score_role_match(roles)
    s7 = llm_deep_score(text, skills)

    components = [s1, s2, s3, s4, s5, s6, s7]

    total = sum(c["score"] for c in components)
    total = min(total, 100)

    # ATS grade
    if total >= 85:
        grade = "Excellent"
        grade_color = "green"
        feedback = "Your resume is highly ATS-optimized. You should pass most filters."
    elif total >= 70:
        grade = "Good"
        grade_color = "blue"
        feedback = "Your resume is solid. A few improvements will make it stronger."
    elif total >= 55:
        grade = "Average"
        grade_color = "amber"
        feedback = "Your resume passes basic filters but needs improvement in key areas."
    elif total >= 40:
        grade = "Below Average"
        grade_color = "orange"
        feedback = "Many ATS systems may reject this resume. Focus on the weak areas."
    else:
        grade = "Poor"
        grade_color = "red"
        feedback = "This resume needs significant work to pass ATS screening."

    # Generate specific improvement tips
    improvements = []
    if s1["score"] < 15:
        improvements.append("Add more relevant technical skills — focus on Tier 1 tools like Docker, AWS, FastAPI")
    if s2["score"] < 10:
        missing = s2.get("sections_missing", [])
        if missing:
            improvements.append(f"Add missing sections: {', '.join(missing)}")
    if s3["score"] < 8:
        improvements.append("Add quantifiable metrics — e.g. 'Improved speed by 40%', 'Served 1000+ users'")
    if s4["score"] < 5:
        improvements.append("Replace weak verbs (helped, assisted) with strong ones (built, engineered, deployed)")
    if s5["score"] < 6:
        improvements.append("Mention your CGPA, degree name, and relevant field clearly")
    if s6["score"] < 8:
        improvements.append(f"Strengthen skills for '{roles[0]['role'] if roles else 'target role'}' — check missing skills")

    return {
        "ats_score":    total,
        "grade":        grade,
        "grade_color":  grade_color,
        "feedback":     feedback,
        "improvements": improvements,
        "breakdown": {
            "skills_keywords":   {"score": s1["score"], "max": s1["max"], "details": s1["details"]},
            "resume_structure":  {"score": s2["score"], "max": s2["max"], "details": s2["details"]},
            "quantification":    {"score": s3["score"], "max": s3["max"], "details": s3["details"]},
            "action_verbs":      {"score": s4["score"], "max": s4["max"], "details": s4["details"]},
            "education":         {"score": s5["score"], "max": s5["max"], "details": s5["details"]},
            "role_match":        {"score": s6["score"], "max": s6["max"], "details": s6["details"]},
            "ai_analysis":       {"score": s7["score"], "max": s7["max"], "details": s7["details"]},
        }
    }