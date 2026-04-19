# 🔹 Static skill database
SKILLS_DB = [
    "python", "java", "c++", "sql", "mongodb",
    "machine learning", "deep learning", "nlp",
    "data analysis", "pandas", "numpy",
    "django", "flask", "fastapi",
    "html", "css", "javascript", "react",
    "docker", "kubernetes", "git",
    "linux", "aws", "azure"
]


def extract_skills(text):

    found_skills = set()

    text = text.lower()

    for skill in SKILLS_DB:
        if skill in text:
            found_skills.add(skill.title())

    return list(found_skills)