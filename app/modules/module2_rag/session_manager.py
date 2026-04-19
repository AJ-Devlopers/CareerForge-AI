SESSION = {}

def create_session(session_id):
    SESSION[session_id] = {
        "history": []
    }

def add_message(session_id, role, content):
    SESSION[session_id]["history"].append({
        "role": role,
        "content": content
    })

def get_history(session_id):
    return SESSION[session_id]["history"]