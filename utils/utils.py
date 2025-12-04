import os
import json5

STATE_FILE = "data/json/state.json"


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"last_run": "2025-10-21 00:00:00"}
    return json5.load(open(STATE_FILE))["last_run"]


# ----------------------------------
# 配列を n 件ずつに分割する
# ----------------------------------
def chunker(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]