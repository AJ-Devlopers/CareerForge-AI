# app/modules/module3_agents/answer_evaluator.py
"""
Answer Evaluator Agent
Deep-dives into interview performance across all attempts.
Produces:
- Per-round detailed analysis
- Cross-round patterns
- Specific improvement actions per weakness
- Strengths to highlight
"""

import os
import re
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def run_answer_evaluator(state: dict) -> dict:
    """
    Input:  state with interview_results, role, skills
    Output: interview_analysis dict
    """
    interview_results = state.get("interview_results", [])
    role              = state.get("role", "Software Engineer")
    skills            = state.get("skills_found", [])
    weak_areas        = state.get("weak_areas", [])

    if not interview_results:
        return {
            "interview_analysis": {
                "has_data": False,
                "message": "No interview attempts found. Complete at least one interview round in Module 2.",
                "per_round": [],
                "patterns": [],
                "priority_actions": [],
                "readiness_score": 0,
            }
        }

    # ── Per-round analysis ────────────────────────────────────
    per_round = []
    for ir in interview_results:
        round_analysis = _analyze_round(ir, role)
        per_round.append(round_analysis)

    # ── Cross-round patterns + priority actions ───────────────
    patterns, priority_actions = _find_patterns(interview_results, role, weak_areas, skills)

    # ── Readiness score ───────────────────────────────────────
    valid_scores = [r.get("score", 0) for r in interview_results if r.get("score", 0) > 0]
    avg_score    = sum(valid_scores) / len(valid_scores) if valid_scores else 0
    readiness    = min(100, round(avg_score * 1.05))  # slight boost for attempting

    return {
        "interview_analysis": {
            "has_data":       True,
            "per_round":      per_round,
            "patterns":       patterns,
            "priority_actions": priority_actions,
            "readiness_score": readiness,
            "avg_score":      round(avg_score),
            "total_rounds":   len(interview_results),
        }
    }


def _analyze_round(ir: dict, role: str) -> dict:
    """Enrich a single interview result with AI analysis."""
    score    = ir.get("score", 0)
    round_t  = ir.get("round", "").replace("_", " ").title()
    grade    = ir.get("grade", "")
    summary  = ir.get("summary", "")
    bd       = ir.get("breakdown", {})
    strengths    = ir.get("strengths", [])
    improvements = ir.get("improvements", [])

    # Find weakest and strongest breakdown area
    bd_scored = []
    for key, val in bd.items():
        if isinstance(val, dict):
            s = val.get("score", 0)
            m = val.get("max", 20)
            bd_scored.append({
                "name":    key.replace("_", " ").title(),
                "score":   s,
                "max":     m,
                "pct":     round((s/m)*100) if m > 0 else 0,
                "comment": val.get("comment", ""),
            })

    bd_scored.sort(key=lambda x: x["pct"])
    weakest  = bd_scored[:2]  if bd_scored else []
    strongest = bd_scored[-2:] if bd_scored else []

    # Generate a 1-line coaching tip for this round
    tip = _get_round_tip(round_t, score, weakest, role)

    return {
        "round":      ir.get("round", ""),
        "round_label": round_t,
        "score":      score,
        "grade":      grade,
        "summary":    summary,
        "breakdown":  bd_scored,
        "weakest":    weakest,
        "strongest":  strongest,
        "strengths":  strengths,
        "improvements": improvements,
        "coaching_tip": tip,
    }


def _get_round_tip(round_label, score, weakest, role):
    if score >= 80:
        return f"Excellent {round_label}! Maintain this level — you're interview-ready."
    if not weakest:
        return f"Focus on depth and specificity in your {round_label} answers."

    weak_name = weakest[0].get("name", "this area")
    prompt = f"""Give ONE specific, actionable coaching tip (1 sentence) to improve '{weak_name}' in a {round_label} for a {role} role. Be direct and practical."""

    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.3
        )
        return res.choices[0].message.content.strip()
    except Exception:
        return f"Focus on improving {weak_name} with specific examples from your experience."


def _find_patterns(interview_results, role, weak_areas, skills):
    """Use LLM to find cross-round patterns and generate priority actions."""
    if not interview_results:
        return [], []

    # Summarize all rounds
    rounds_summary = []
    for ir in interview_results:
        rounds_summary.append(
            f"- {ir.get('round','').replace('_',' ').title()}: {ir.get('score',0)}/100 ({ir.get('grade','')})"
            f" | Strengths: {', '.join(ir.get('strengths',[])[:2])}"
            f" | Improvements: {', '.join(ir.get('improvements',[])[:2])}"
        )

    prompt = f"""Analyze these interview results for a {role} candidate and identify patterns.

Results:
{chr(10).join(rounds_summary)}

Overall weak areas: {', '.join(weak_areas[:4]) if weak_areas else 'none'}
Skills: {', '.join(skills[:8]) if skills else 'unknown'}

Return ONLY valid JSON (no markdown):
{{
  "patterns": [
    "<1-sentence pattern observation>",
    "<another pattern>",
    "<another pattern>"
  ],
  "priority_actions": [
    {{
      "action": "<specific action to take>",
      "why": "<1 sentence why this will improve scores>",
      "timeframe": "<e.g. This week>",
      "impact": "<High|Medium>"
    }}
  ]
}}

Generate 3 patterns and 4 priority actions."""

    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.3
        )
        raw = res.choices[0].message.content.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        data = json.loads(raw)
        return data.get("patterns", []), data.get("priority_actions", [])
    except Exception as e:
        print(f"answer_evaluator patterns error: {e}")
        return (
            ["Practice answering with the STAR method for consistency."],
            [{"action": "Do 2 mock interviews per week",
              "why": "Repetition builds confidence and reduces hesitation.",
              "timeframe": "This week",
              "impact": "High"}]
        )