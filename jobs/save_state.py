import json

def save_state(new_run):
    new_state = {
        "last_run": new_run
    }
    with open("data/json/state.json", "w", encoding="utf-8") as f:
        json.dump(new_state, f, ensure_ascii=False, indent=2)