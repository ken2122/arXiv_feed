import os
import json5
import math
from datetime import date, timedelta
from typing import List


STATE_FILE = "data/json/state.json"
TARGET_LEVELS = ["Highest", "High", "highest", "high", "HIGHEST", "HIGH"]


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"last_run": "2025-10-21 00:00:00"}
    return json5.load(open(STATE_FILE))["last_run"]


def get_last_month_yyyy_mm() -> str:
    today = date.today()
    first_day_this_month = today.replace(day=1)
    last_month = first_day_this_month - timedelta(days=1)
    return last_month.strftime("%Y/%m")


# ----------------------------------
# 配列を n 件ずつに分割する
# ----------------------------------
def chunker(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def split_metadata_evenly(
    metadata_list: List[dict],
    max_chunk_size: int = 40
) -> List[List[dict]]:
    """
    メタデータを「最大max_chunk_size」を超えない範囲で
    できるだけ均等に分割する
    """
    total = len(metadata_list)
    if total == 0:
        return []

    # チャンク数を決定
    chunk_count = math.ceil(total / max_chunk_size)

    # 均等サイズ計算
    base_size = total // chunk_count
    remainder = total % chunk_count

    chunks = []
    start = 0

    for i in range(chunk_count):
        # 余りは前から1件ずつ配る
        size = base_size + (1 if i < remainder else 0)
        end = start + size
        chunks.append(metadata_list[start:end])
        start = end

    return chunks


def is_high_impact_or_above(impact_level):
    return impact_level in TARGET_LEVELS