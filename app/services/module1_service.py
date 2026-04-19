from app.modules.module1_genai.pipeline import run_module1_pipeline


async def process_resume(file):
    """
    Service layer for Module 1.
    Delegates full logic to pipeline.
    """

    try:
        result = run_module1_pipeline(file)
        return result

    except Exception as e:
        return {
            "ats_score": 0,
            "total_skills": 0,
            "skills_found": [],
            "roles": [],
            "error": str(e)
        }