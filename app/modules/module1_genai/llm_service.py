# app/modules/module1_genai/llm_service.py

import os
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ── Cache to avoid repeated LLM calls ────────────────────
LLM_CACHE = {}


# =========================================================
# 🔹 1. EXTRACT CANDIDATE NAME FROM RESUME
# =========================================================
def extract_candidate_name(text: str) -> str:
    """
    Extracts the candidate's full name from resume text.
    Looks at the first 500 chars where the name usually appears.
    """
    prompt = f"""Extract only the candidate's full name from this resume.

Rules:
- Return ONLY the full name (e.g. "John Smith")
- No explanation, no punctuation, no labels
- If no name found, return empty string

Resume (first section):
{text[:500]}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
            temperature=0.1
        )
        name = response.choices[0].message.content.strip()

        # Sanity check — reject if it looks like a sentence or is too long
        if len(name) > 60 or '\n' in name or len(name.split()) > 5:
            return ""

        # Reject if it contains obvious non-name words
        bad_words = ["resume", "curriculum", "vitae", "cv", "objective", "summary", "email", "phone"]
        if any(w in name.lower() for w in bad_words):
            return ""

        return name

    except Exception as e:
        print(f"⚠️ Name extraction error: {e}")
        return ""


# =========================================================
# 🔹 2. EXTRACT SKILLS FROM RESUME (AI)
# =========================================================
def extract_skills_ai(text: str) -> list:
    """
    AI-based skill extraction to supplement static keyword matching.
    """
    prompt = f"""Extract ONLY technical skills from the following resume.

Rules:
- Return ONLY comma-separated skills
- No explanation
- No sentences
- Example: Python, SQL, Machine Learning, Docker

Resume:
{text[:2000]}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )

        output = response.choices[0].message.content.strip()

        skills = [
            s.strip().title()
            for s in output.split(",")
            if s.strip()
        ]

        return list(set(skills))

    except Exception:
        return []


# =========================================================
# 🔹 3. GENERATE ROLE EXPLANATION
# =========================================================
def generate_role_explanation(role: str) -> str:
    """
    Explains a job role in 2-3 simple lines for a student.
    """
    prompt = f"""You are a career advisor.

Explain the role "{role}" in 2-3 simple lines for a student.
Keep it clear and practical."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()

    except Exception:
        return "Description not available"


# =========================================================
# 🔹 4. GENERATE SKILLS FOR A NEW ROLE (USER INPUT ROLE)
# =========================================================
def generate_role_skills(role: str) -> list:
    """
    Returns a list of technical skills required for a given role.
    Used by the custom role analysis endpoint.
    """
    prompt = f"""List technical skills required for a {role}.

Rules:
- Only technical skills
- Comma separated
- No explanation

Example:
Python, SQL, Docker, APIs"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )

        output = response.choices[0].message.content.strip()

        skills = [
            s.strip().lower()
            for s in output.split(",")
            if s.strip()
        ]

        return list(set(skills))

    except Exception:
        return []


# =========================================================
# 🔹 5. ENHANCE EXISTING ROLE SKILLS (AI IMPROVEMENT)
# =========================================================
def enhance_role_skills(role: str, existing_skills: list) -> list:
    """
    Suggests additional skills for a role beyond what's already listed.
    Used by role_matcher.py to expand the required skills set.
    """
    prompt = f"""You are an expert career assistant.

Given:
Role: {role}
Current skills: {", ".join(existing_skills)}

Suggest additional relevant technical skills.

Rules:
- Only NEW skills (no repetition)
- Comma separated
- No explanation"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )

        output = response.choices[0].message.content.strip()

        extra_skills = [
            s.strip().lower()
            for s in output.split(",")
            if s.strip()
        ]

        return list(set(extra_skills))

    except Exception:
        return []