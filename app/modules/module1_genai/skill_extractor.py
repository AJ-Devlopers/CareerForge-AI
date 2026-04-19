import spacy

nlp = spacy.load("en_core_web_sm")

SKILLS = [
    "python", "java", "c++", "sql",
    "machine learning", "deep learning",
    "fastapi", "django", "react",
    "docker", "html", "css", "javascript"
]

def extract_skills(text):
    text = text.lower()
    found = []

    for skill in SKILLS:
        if skill in text:
            found.append(skill)

    return list(set(found))