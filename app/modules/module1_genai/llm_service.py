import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# 🔹 1. EXTRACT SKILLS FROM RESUME (AI)
def extract_skills_ai(text):

    prompt = f"""
    Extract ONLY technical skills from the following resume.

    Rules:
    - Return ONLY comma-separated skills
    - No explanation
    - No sentences
    - Example: Python, SQL, Machine Learning, Docker

    Resume:
    {text[:2000]}
    """

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


# 🔹 2. GENERATE ROLE EXPLANATION
def generate_role_explanation(role):

    prompt = f"""
    You are a career advisor.

    Explain the role "{role}" in 2-3 simple lines for a student.
    Keep it clear and practical.
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content.strip()

    except Exception:
        return "Description not available"


# 🔹 3. GENERATE SKILLS FOR A NEW ROLE (USER INPUT ROLE)
def generate_role_skills(role):

    prompt = f"""
    List technical skills required for a {role}.

    Rules:
    - Only technical skills
    - Comma separated
    - No explanation

    Example:
    Python, SQL, Docker, APIs
    """

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


# 🔹 4. ENHANCE EXISTING ROLE SKILLS (AI IMPROVEMENT)
def enhance_role_skills(role, existing_skills):

    prompt = f"""
    You are an expert career assistant.

    Given:
    Role: {role}
    Current skills: {", ".join(existing_skills)}

    Suggest additional relevant technical skills.

    Rules:
    - Only NEW skills (no repetition)
    - Comma separated
    - No explanation
    """

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