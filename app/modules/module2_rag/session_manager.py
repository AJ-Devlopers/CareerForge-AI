"""
session_manager.py
In-memory session store. Each key is role+round combo
so different rounds never share history.
"""

SESSION: dict = {}


def create_session(session_id: str, force_reset: bool = False):
    """Create session if it doesn't exist. Pass force_reset=True to wipe."""
    if session_id not in SESSION or force_reset:
        SESSION[session_id] = {"history": []}


def add_message(session_id: str, role: str, content: str):
    if session_id not in SESSION:
        create_session(session_id)
    SESSION[session_id]["history"].append({
        "role":    role,
        "content": content
    })


def get_history(session_id: str) -> list:
    if session_id not in SESSION:
        create_session(session_id)
    return SESSION[session_id]["history"]


def reset_session(session_id: str):
    """Hard reset — clears history."""
    SESSION[session_id] = {"history": []}