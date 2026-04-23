# app/modules/module3_agents/agent_graph.py
"""
Orchestrates all Module 3 agents in sequence:
1. report_agent     → collects and structures user data
2. suggestion_agent → generates resume/profile improvement suggestions
3. roadmap_agent    → builds the phased learning roadmap
4. answer_evaluator → evaluates interview performance in depth

Each agent returns a dict that is merged into a shared state.
"""

import asyncio
from typing import Optional

from app.modules.module3_agents.report_agent     import run_report_agent
from app.modules.module3_agents.suggestion_agent import run_suggestion_agent
from app.modules.module3_agents.roadmap_agent    import run_roadmap_agent
from app.modules.module3_agents.answer_evaluator import run_answer_evaluator


# ── Shared state type ─────────────────────────────────────────
class AgentState(dict):
    """Simple dict subclass that tracks which agents have run."""
    pass


async def run_module3_pipeline(
    role:             str,
    duration:         str,
    goal:             str,
    candidate_name:   str,
    ats_score:        int,
    skills_found:     list,
    interview_results: list,
    improvements:     list,
    breakdown:        dict,
    resume_text:      str = "",
) -> dict:
    """
    Full async pipeline. Runs agents in dependency order:
    report → suggestion + answer_evaluator (parallel) → roadmap

    Returns a merged state dict with all agent outputs.
    """

    state = AgentState({
        "role":              role,
        "duration":          duration,
        "goal":              goal,
        "candidate_name":    candidate_name,
        "ats_score":         ats_score,
        "skills_found":      skills_found,
        "interview_results": interview_results,
        "improvements":      improvements,
        "breakdown":         breakdown,
        "resume_text":       resume_text,
        # outputs (filled by agents)
        "report":            {},
        "suggestions":       [],
        "project_ideas":     [],
        "overall_tips":      [],
        "roadmap_phases":    [],
        "interview_analysis": {},
        "total_weeks":       0,
        "errors":            [],
    })

    # ── Step 1: Report agent (structures everything) ──────────
    try:
        report_out = await asyncio.to_thread(run_report_agent, state)
        state.update(report_out)
    except Exception as e:
        state["errors"].append(f"report_agent: {e}")

    # ── Step 2: Parallel — suggestions + interview eval ───────
    tasks = [
        asyncio.to_thread(run_suggestion_agent, state),
        asyncio.to_thread(run_answer_evaluator,  state),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for res in results:
        if isinstance(res, Exception):
            state["errors"].append(str(res))
        elif isinstance(res, dict):
            state.update(res)

    # ── Step 3: Roadmap agent (uses suggestion outputs) ───────
    try:
        roadmap_out = await asyncio.to_thread(run_roadmap_agent, state)
        state.update(roadmap_out)
    except Exception as e:
        state["errors"].append(f"roadmap_agent: {e}")

    return dict(state)


def run_pipeline_sync(
    role:             str,
    duration:         str,
    goal:             str,
    candidate_name:   str,
    ats_score:        int,
    skills_found:     list,
    interview_results: list,
    improvements:     list,
    breakdown:        dict,
    resume_text:      str = "",
) -> dict:
    """Synchronous wrapper for FastAPI endpoints that can't use await."""
    return asyncio.run(run_module3_pipeline(
        role=role,
        duration=duration,
        goal=goal,
        candidate_name=candidate_name,
        ats_score=ats_score,
        skills_found=skills_found,
        interview_results=interview_results,
        improvements=improvements,
        breakdown=breakdown,
        resume_text=resume_text,
    ))