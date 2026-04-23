# app/modules/module3_agents/report_agent.py
"""
Report Agent
Structures raw candidate data into a clean, enriched report dict.
Calculates overall scores, identifies weak areas, and prepares
context for downstream agents.
"""

import os
import re
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def run_report_agent(state: dict) -> dict:
    """
    Input:  state with raw data (skills, ats, interview_results, etc.)
    Output: enriched 'report' dict + derived fields
    """
    skills           = state.get("skills_found", [])
    interview_results = state.get("interview_results", [])
    ats_score        = state.get("ats_score", 0)
    role             = state.get("role", "")
    candidate_name   = state.get("candidate_name", "")

    # ── Compute overall interview score ───────────────────────
    valid_scores = [r.get("score", 0) for r in interview_results if r.get("score", 0) > 0]
    overall_interview_score = round(sum(valid_scores) / len(valid_scores)) if valid_scores else 0

    # ── Identify weak interview areas ─────────────────────────
    weak_areas    = []
    strong_areas  = []
    all_breakdown_items = {}

    for ir in interview_results:
        bd = ir.get("breakdown", {})
        for key, val in bd.items():
            if isinstance(val, dict):
                s = val.get("score", 0)
                m = val.get("max", 20)
                if m > 0:
                    pct = (s / m) * 100
                    label = key.replace("_", " ").title()
                    if label not in all_breakdown_items:
                        all_breakdown_items[label] = []
                    all_breakdown_items[label].append(pct)

    for label, pcts in all_breakdown_items.items():
        avg = sum(pcts) / len(pcts)
        if avg < 55:
            weak_areas.append(label)
        elif avg >= 75:
            strong_areas.append(label)

    # ── Combined score (ATS + Interview) ──────────────────────
    if overall_interview_score > 0:
        combined_score = round((ats_score * 0.4) + (overall_interview_score * 0.6))
    else:
        combined_score = ats_score

    # ── Grade ─────────────────────────────────────────────────
    if combined_score >= 85:
        grade = "Excellent"
    elif combined_score >= 70:
        grade = "Good"
    elif combined_score >= 55:
        grade = "Average"
    elif combined_score >= 40:
        grade = "Below Average"
    else:
        grade = "Needs Work"

    # ── AI-generated profile summary ──────────────────────────
    summary = _generate_summary(
        candidate_name, role, ats_score, overall_interview_score,
        skills, weak_areas, strong_areas, state.get("goal", "")
    )

    report = {
        "candidate_name":         candidate_name,
        "role":                   role,
        "ats_score":              ats_score,
        "overall_interview_score": overall_interview_score,
        "combined_score":         combined_score,
        "grade":                  grade,
        "skills_found":           skills,
        "interview_results":      interview_results,
        "weak_areas":             weak_areas,
        "strong_areas":           strong_areas,
        "profile_summary":        summary,
        "total_attempts":         len(interview_results),
    }

    return {
        "report":                   report,
        "overall_interview_score":  overall_interview_score,
        "combined_score":           combined_score,
        "grade":                    grade,
        "weak_areas":               weak_areas,
        "strong_areas":             strong_areas,
        "profile_summary":          summary,
    }


def _generate_summary(name, role, ats, interview_score, skills, weak, strong, goal):
    prompt = f"""Write a 2-3 sentence professional profile summary for a candidate report.

Candidate: {name or 'the candidate'}
Target Role: {role}
ATS Score: {ats}/100
Interview Score: {interview_score}/100
Key Skills: {', '.join(skills[:8]) if skills else 'not provided'}
Strong Areas: {', '.join(strong[:3]) if strong else 'none identified'}
Weak Areas: {', '.join(weak[:3]) if weak else 'none identified'}
Goal: {goal}

Rules:
- Professional, encouraging tone
- Mention specific strengths
- 2-3 sentences max
- No fluff, no clichés"""

    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
            temperature=0.4
        )
        return res.choices[0].message.content.strip()
    except Exception:
        return f"{name or 'The candidate'} is targeting a {role} role with an ATS score of {ats}/100."