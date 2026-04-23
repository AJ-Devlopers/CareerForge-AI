# app/modules/module3_agents/suggestion_agent.py
"""
Suggestion Agent
Generates:
1. Resume improvement suggestions with DETAILED expandable plans
2. Project ideas with full implementation guide
3. Overall career tips

Each suggestion has a 'detail_plan' field with topic-by-topic breakdown
so the frontend can show a rich expandable dropdown.
"""

import os
import re
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def run_suggestion_agent(state: dict) -> dict:
    """
    Returns:
        suggestions   - list of resume improvement objects (with detail_plan)
        project_ideas - list of project dicts (with implementation steps)
        overall_tips  - list of career tip strings
    """
    role      = state.get("role", "Software Engineer")
    skills    = state.get("skills_found", [])
    ats_score = state.get("ats_score", 0)
    weak_areas = state.get("weak_areas", [])
    improvements = state.get("improvements", [])  # from module1 ATS scorer
    goal      = state.get("goal", "Get hired")

    suggestions   = _generate_suggestions(role, skills, ats_score, weak_areas, improvements, goal)
    project_ideas = _generate_projects(role, skills, goal)
    overall_tips  = _generate_tips(role, weak_areas, goal)

    return {
        "suggestions":   suggestions,
        "project_ideas": project_ideas,
        "overall_tips":  overall_tips,
        # Also keep for PDF
        "resume_suggestions": [s.get("title", "") + " — " + s.get("summary", "")
                                for s in suggestions],
    }


def _generate_suggestions(role, skills, ats, weak_areas, improvements, goal):
    prompt = f"""You are a senior resume coach. Generate 5 detailed resume improvement suggestions.

Role: {role}
Current Skills: {', '.join(skills[:12]) if skills else 'unknown'}
ATS Score: {ats}/100
Weak Interview Areas: {', '.join(weak_areas[:4]) if weak_areas else 'none'}
Goal: {goal}
Existing improvement notes: {'; '.join(improvements[:3]) if improvements else 'none'}

Return ONLY valid JSON array (no markdown):

[
  {{
    "id": 1,
    "category": "<one of: Skills|Projects|Structure|Metrics|Keywords|Experience|Education>",
    "title": "<short actionable title e.g. 'Add Quantified Metrics'>",
    "summary": "<1 sentence describing the suggestion>",
    "priority": "<High|Medium|Low>",
    "detail_plan": {{
      "why": "<2 sentences explaining why this matters for ATS and recruiters>",
      "topics": [
        {{
          "topic": "<specific topic/area e.g. 'Bullet Point Rewrites'>",
          "description": "<2-3 sentences: exactly what to do, concrete examples>",
          "examples": ["<example before/after or specific example 1>", "<example 2>"],
          "time_needed": "<e.g. 30 minutes>"
        }}
      ],
      "quick_wins": ["<immediate action 1>", "<immediate action 2>", "<immediate action 3>"]
    }}
  }}
]

Make each suggestion SPECIFIC to {role}. Include concrete examples."""

    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2500,
            temperature=0.3
        )
        raw = res.choices[0].message.content.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        return json.loads(raw)
    except Exception as e:
        print(f"suggestion_agent suggestions error: {e}")
        return _fallback_suggestions(role)


def _generate_projects(role, skills, goal):
    prompt = f"""Generate 3 portfolio project ideas for a {role} candidate.
Goal: {goal}
Skills: {', '.join(skills[:10]) if skills else 'general'}

Return ONLY valid JSON array (no markdown):
[
  {{
    "title": "<project name>",
    "description": "<2 sentences about what it does>",
    "skills_used": ["<skill1>", "<skill2>", "<skill3>"],
    "impact": "<why this impresses recruiters for {role}>",
    "difficulty": "<Beginner|Intermediate|Advanced>",
    "time_estimate": "<e.g. 2-3 weeks>",
    "implementation_steps": [
      {{
        "step": 1,
        "title": "<step title>",
        "description": "<what to build/do in this step>",
        "duration": "<e.g. 2 days>"
      }}
    ],
    "tech_stack": ["<tech1>", "<tech2>"],
    "github_topics": ["<topic1>", "<topic2>"]
  }}
]"""

    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.4
        )
        raw = res.choices[0].message.content.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        return json.loads(raw)
    except Exception as e:
        print(f"suggestion_agent projects error: {e}")
        return []


def _generate_tips(role, weak_areas, goal):
    prompt = f"""Give 4 specific, actionable career tips for someone targeting {role}.
Goal: {goal}
Their weak areas: {', '.join(weak_areas[:3]) if weak_areas else 'general improvement needed'}

Return ONLY a JSON array of 4 tip strings. Each tip should be 1-2 sentences. No markdown."""

    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.4
        )
        raw = res.choices[0].message.content.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        return json.loads(raw)
    except Exception:
        return [
            f"Practice mock interviews specifically for {role} roles at least 3x per week.",
            "Build at least one end-to-end project that solves a real-world problem.",
            "Optimize your LinkedIn profile with role-specific keywords.",
            "Network actively — 70% of jobs are filled through referrals."
        ]


def _fallback_suggestions(role):
    return [
        {
            "id": 1,
            "category": "Metrics",
            "title": "Add Quantified Impact",
            "summary": "Replace vague descriptions with numbers and measurable results.",
            "priority": "High",
            "detail_plan": {
                "why": "ATS and recruiters prioritize resumes with measurable achievements. Numbers make impact concrete and credible.",
                "topics": [
                    {
                        "topic": "Bullet Point Rewrites",
                        "description": "Change each bullet from 'Worked on X' to 'Built X that improved Y by Z%'. Focus on outcomes.",
                        "examples": ["Before: 'Developed APIs' → After: 'Developed 12 REST APIs serving 50K+ daily requests'"],
                        "time_needed": "1-2 hours"
                    }
                ],
                "quick_wins": ["Add percentages to at least 3 bullets", "Mention team size", "Include time frames"]
            }
        },
        {
            "id": 2,
            "category": "Keywords",
            "title": f"Add {role}-Specific Keywords",
            "summary": "Include role-specific technical terms to pass ATS filters.",
            "priority": "High",
            "detail_plan": {
                "why": f"Many companies use ATS that filter resumes by keywords. {role} positions have specific required terms.",
                "topics": [
                    {
                        "topic": "Keyword Research",
                        "description": "Analyze 5-10 job descriptions for your target role and extract repeating technical terms.",
                        "examples": ["Copy exact tool names from JDs", "Include acronyms AND full forms"],
                        "time_needed": "30 minutes"
                    }
                ],
                "quick_wins": ["Add a dedicated 'Skills' section", "Mirror JD language", "Include certifications"]
            }
        }
    ]