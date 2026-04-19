def match_roles(skills):

    roles_map = {
        "ML Engineer": ["python", "machine learning", "deep learning"],
        "Backend Developer": ["python", "fastapi", "sql"],
        "Frontend Developer": ["react", "javascript", "css"],
        "Data Scientist": ["python", "sql", "machine learning"]
    }

    results = []

    for role, required in roles_map.items():
        matched = len(set(skills) & set(required))
        total = len(required)

        score = int((matched / total) * 100) if total > 0 else 0

        results.append({
            "role": role,
            "match": score
        })

    return sorted(results, key=lambda x: x["match"], reverse=True)