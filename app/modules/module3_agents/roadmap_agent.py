# app/modules/module3_agents/roadmap_agent.py
"""
Roadmap Agent
Builds a detailed, phased learning roadmap using:
- Role target
- Duration / goal
- Weak areas from interview analysis
- Current skills (to avoid re-teaching)
- Suggestion agent outputs (to align roadmap with suggestions)

Each phase has multiple steps with detailed topic breakdowns.
"""

import os
import re
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def run_roadmap_agent(state: dict) -> dict:
    """
    Input:  full state (role, duration, goal, skills, weak_areas, suggestions)
    Output: roadmap_phases list + total_weeks
    """
    role       = state.get("role", "Software Engineer")
    duration   = state.get("duration", "3 months")
    goal       = state.get("goal", "Get hired")
    skills     = state.get("skills_found", [])
    weak_areas = state.get("weak_areas", [])
    suggestions = state.get("suggestions", [])

    # Extract suggestion titles to align roadmap
    sug_titles = [s.get("title", "") for s in suggestions[:5]]

    phases = _build_phases(role, duration, goal, skills, weak_areas, sug_titles)

    # Calculate total weeks from phases
    total_weeks = sum(p.get("duration_weeks", 1) for p in phases)

    return {
        "roadmap_phases": phases,
        "total_weeks":    total_weeks,
    }


def _build_phases(role, duration, goal, skills, weak_areas, sug_titles):
    # Determine number of phases from duration
    dur_lower = duration.lower()
    if "1 month" in dur_lower:
        num_phases = 2
    elif "2 month" in dur_lower:
        num_phases = 3
    elif "6 month" in dur_lower:
        num_phases = 5
    elif "12 month" in dur_lower:
        num_phases = 6
    else:  # 3 months default
        num_phases = 4

    prompt = f"""You are a senior career coach. Build a detailed learning roadmap.

Role: {role}
Duration: {duration}
Goal: {goal}
Current Skills (skip basics): {', '.join(skills[:12]) if skills else 'unknown'}
Weak interview areas to address: {', '.join(weak_areas[:4]) if weak_areas else 'none'}
Resume improvements to include: {', '.join(sug_titles[:3]) if sug_titles else 'general'}

Create exactly {num_phases} phases. Return ONLY valid JSON (no markdown):

[
  {{
    "phase": 1,
    "title": "<phase title e.g. Foundation>",
    "emoji": "<single relevant emoji>",
    "color": "<one of: amber|green|blue|purple|red|teal>",
    "duration_weeks": <integer>,
    "focus": "<one line describing this phase's focus>",
    "goal": "<what the candidate achieves by end of this phase>",
    "steps": [
      {{
        "day_range": "<e.g. Week 1, Days 1-7>",
        "title": "<step title>",
        "description": "<2-3 sentences describing what to do>",
        "topics": [
          {{
            "name": "<topic name e.g. Python Data Structures>",
            "subtopics": ["<subtopic 1>", "<subtopic 2>", "<subtopic 3>"],
            "resources": ["<specific resource e.g. CS50 Python>", "<resource 2>"],
            "practice": "<specific practice task>",
            "hours": <estimated hours as integer>
          }}
        ],
        "milestone": "<concrete deliverable at end of this step>",
        "checkpoint": "<how to verify you've completed this step>"
      }}
    ]
  }}
]

RULES:
- Each phase: 2-4 steps
- Each step: 1-3 topics with specific subtopics
- Be SPECIFIC to {role} — no generic advice
- Skip skills the candidate already has
- Address weak interview areas directly
- Make milestones concrete and verifiable"""

    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.25
        )
        raw = res.choices[0].message.content.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        phases = json.loads(raw)

        # Validate structure
        for i, phase in enumerate(phases):
            if "phase" not in phase:
                phase["phase"] = i + 1
            if "color" not in phase:
                colors = ["amber", "green", "blue", "purple", "red", "teal"]
                phase["color"] = colors[i % len(colors)]
            if "emoji" not in phase:
                phase["emoji"] = ["🚀", "📚", "🔧", "🎯", "💎", "⭐"][i % 6]

        return phases

    except Exception as e:
        print(f"roadmap_agent error: {e}")
        return _fallback_phases(role, duration)


def _fallback_phases(role, duration):
    return [
        {
            "phase": 1,
            "title": "Foundation",
            "emoji": "🚀",
            "color": "amber",
            "duration_weeks": 4,
            "focus": f"Build core fundamentals for {role}",
            "goal": "Have solid foundation in required technologies",
            "steps": [
                {
                    "day_range": "Week 1-2",
                    "title": "Core Concepts",
                    "description": f"Master the fundamental concepts required for {role}.",
                    "topics": [
                        {
                            "name": "Technical Foundations",
                            "subtopics": ["Data Structures", "Algorithms", "System Design Basics"],
                            "resources": ["LeetCode Easy problems", "CS fundamentals course"],
                            "practice": "Solve 2 problems daily",
                            "hours": 20
                        }
                    ],
                    "milestone": "Complete 20 LeetCode Easy problems",
                    "checkpoint": "Can explain core concepts in interview setting"
                }
            ]
        },
        {
            "phase": 2,
            "title": "Practice & Apply",
            "emoji": "🔧",
            "color": "green",
            "duration_weeks": 4,
            "focus": "Build projects and practice interviews",
            "goal": "Have 2 portfolio projects and pass mock interviews",
            "steps": [
                {
                    "day_range": "Week 5-8",
                    "title": "Build Projects",
                    "description": f"Build 2 real-world projects targeting {role} requirements.",
                    "topics": [
                        {
                            "name": "Project Development",
                            "subtopics": ["Planning", "Implementation", "Deployment"],
                            "resources": ["GitHub", "Vercel/Heroku"],
                            "practice": "Daily commits to GitHub",
                            "hours": 40
                        }
                    ],
                    "milestone": "2 deployed projects with documentation",
                    "checkpoint": "Can walkthrough projects in interview"
                }
            ]
        }
    ]