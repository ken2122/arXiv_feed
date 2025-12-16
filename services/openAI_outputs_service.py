import time
import json
import json5
from openai import OpenAI  
from config import settings
client = OpenAI(api_key=settings.OPENAI_API_KEY)

def create_openAI_outputs(fileName):
    # ① JSONLファイルをアップロード
    uploaded = client.files.create(
        file=open(f"data/json/feed/requests_{fileName}.jsonl", "rb"),
        purpose="batch"
    )
    file_id = uploaded.id

    # ② バッチ作成
    batch = client.batches.create(
        input_file_id=file_id,
        endpoint="/v1/responses",
        completion_window="24h"
    )

    batch_id = batch.id

    # ③ ステータス監視
    while True:
        info = client.batches.retrieve(batch_id)
        print("Batch status:", info.status)

        if info.status == "completed":
            output_file_id = info.output_file_id
            result = client.files.content(output_file_id)

            with open(f"data/json/feed/outputs_{fileName}.jsonl", "wb") as f:
                f.write(result.read())

            print("Result downloaded.")
            break

        elif info.status in ["failed", "cancelled"]:
            print("Batch failed.")
            break

        time.sleep(120)

def load_openAI_outputs(fileName):
    results = {}

    # 読み込む
    with open(f"data/json/feed/outputs_{fileName}.jsonl", "r", encoding="utf-8") as f:
        lines = f.readlines()

    modified = False  # 書き換えが起きたかどうか

    for idx, line in enumerate(lines):
        raw_line = line.strip()
        if not raw_line:
            continue

        outer = json5.loads(raw_line)

        # 普通のパス
        try:
            msg_content = outer["response"]["body"]["output"][1]["content"][0]["text"]
            inner = extract_valid_json_objects(msg_content)
            inner = json5.loads(inner)
            results[outer["custom_id"]] = inner
            continue  # OK なので次の行へ

        except Exception:
            # inner JSON が壊れている
            try:
                print("fix_json_with_gpt開始")
                fixed_inner = fix_json_with_gpt(inner)
                inner = extract_valid_json_objects(fixed_inner)
                new_outer = outer.copy()
                new_outer["response"]["body"]["output"][1]["content"][0]["text"] = inner

                # outer も再度 JSON として整形して保存
                fixed_outer_line = json.dumps(new_outer, ensure_ascii=False)
                lines[idx] = fixed_outer_line + "\n"
                modified = True

                # 修復後の JSON をロードして results に入れる
                inner = json5.loads(inner)
                results[outer["custom_id"]] = inner

            except Exception:
                print(f"整形失敗：{inner}")
                # 修復してもダメならスキップ
                continue

    # 必要なら batch_output.jsonl を上書き
    if modified:
        with open(f"data/json/feed/outputs_{fileName}.jsonl", "w", encoding="utf-8") as f:
            f.writelines(lines)

    return results

def extract_valid_json_objects(text):
    stack = 0
    start_idx = None
    for i, ch in enumerate(text):
        if ch == '{':
            if stack == 0:
                start_idx = i
            stack += 1
        elif ch == '}':
            if stack > 0:
                stack -= 1
            if stack == 0 and start_idx is not None:
                candidate = text[start_idx:i+1]
                return candidate

def fix_json_with_gpt(text):
    """GPT-5-nano に壊れた JSON を修復させる"""
    prompt = f"""
You are a JSON repair tool.
The text you will receive contains broken JSON.
Your role is to fix it so that it becomes valid JSON without changing the content.

Your output must consist of only the fully corrected JSON.
Do not output anything except valid JSON object.

Broken JSON:
{text}
"""

    try:
        resp = client.responses.create(
            model="gpt-5-mini",
            input=prompt,
            max_output_tokens=8000,
        )

        return resp.output_text

    except Exception as e:
        print("=" * 80)
        print("❌ GPT JSON 修復中にエラーが発生しました")
        print("- エラータイプ:", type(e))
        print("- エラーメッセージ:", str(e))
        print("=" * 80)
        return None
