# simple in-memory store 
chat_history = []  # list of dicts: {name, role, text, timestamp}

def add_message(msg: dict):
    chat_history.append(msg)

def get_history():
    return chat_history