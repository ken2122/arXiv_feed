import requests
import json
from config import settings
from utils.utils import chunker

WEBHOOK_URL = settings.SLACK_WEBHOOK_URL

def send_slack_message(md_texts):
    BATCH_SIZE = 4
    with open("data/log/Slack_log.txt", "a", encoding="utf-8") as f:
        for batch in chunker(md_texts, BATCH_SIZE):
            payload = {"text": ''.join(batch)}

            response = requests.post(
                WEBHOOK_URL,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                f.write(f"Slack succeeded: {response.status_code}, {response.text}\n")
            else:
                f.write(f"Slack failed: {response.status_code}, {response.text}\n")

