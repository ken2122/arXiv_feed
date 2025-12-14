import requests
import traceback
from config import settings
from utils.utils import chunker

CHAT_URL = settings.CHAT_URL
CHAT_TOKEN = settings.CHAT_TOKEN
CHAT_USER_ID = settings.CHAT_USER_ID
ROOM_ID = settings.ROOM_ID


# ----------------------------------
# メッセージ送信（スレッド開始＋スレッド内投稿）
# ----------------------------------
def send_message(md_texts, date_str):
    url = CHAT_URL
    headers = {
        "X-Auth-Token": CHAT_TOKEN,
        "X-User-Id": CHAT_USER_ID,
        "Content-type": "application/json"
    }
    BATCH_SIZE = 4

    try:
        # ==============================
        # ① スレッド開始（date_str を投稿）
        # ==============================
        payload_first = {
            "roomId": ROOM_ID,
            "text": date_str
        }

        res_first = requests.post(url, json=payload_first, headers=headers)
        data_first = res_first.json()

        if res_first.status_code != 200 or not data_first.get("success"):
            print(f"[ERROR] スレッド開始に失敗: {res_first.status_code}, {res_first.text}")
            return

        # parent message id（tmid）
        thread_id = data_first["message"]["_id"]
        print(f"[INFO] スレッド作成成功")

        # ==============================
        # ② 4件ずつスレッドに投稿
        # ==============================
        for batch in chunker(md_texts, BATCH_SIZE):
            text = ''.join(batch)

            payload = {
                "roomId": "693afcb09b3c65a274a21713",
                "text": text,
                "tmid": thread_id,
                "parseUrls": False
            }

            res = requests.post(url, json=payload, headers=headers)
            data = res.json()

            if res.status_code == 200 and data.get("success"):
                print("[INFO] スレッド内に送信成功")
            else:
                print(f"[ERROR] スレッド内送信失敗: {res.status_code}, {res.text}")

    except Exception as e:
        print("[EXCEPTION] send_message 中に例外発生")
        print(traceback.format_exc())
