import os, json, json5, glob
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.utils import get_last_month_yyyy_mm
from config.paths import DATA_PATH_RULE

def save_feed(feed, run_date):
    buffer = []

    for paper in feed:
        link = paper["link"]
        entry = {
            "custom_id": link.rstrip("/").split("/")[-1],
            "link": link,
            "categories": ", ".join([t.term for t in paper["tags"]])
        }
        buffer.append(json.dumps(entry) + "\n")

    path = DATA_PATH_RULE.build(
        target_date=run_date,
        data_type="jsonl",
        file_name="feed",
    )
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "w") as f:
        f.write(("".join(buffer)))
    print(f"{path} Saved")


def integration_feed(run_date):
    integrated_feed = []
    for path in sorted(glob.glob("data/**/feed_*.jsonl", recursive=True)):
        print(f"processing {path}")
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                integrated_feed.append(json5.loads(line))
    return integrated_feed


def load_custom_ids(integrated_feed):
    """jsonl から custom_id の集合を作る"""
    ids = set()
    for paper in integrated_feed:
        ids.add(paper["custom_id"])
    return ids


def filter_feed_by_custom_id(feed, custom_ids):
    filtered_feed = []
    for paper in feed:
        custom_id = paper["link"].rstrip("/").split("/")[-1]
        if custom_id not in custom_ids:
            filtered_feed.append(paper)
    return filtered_feed


def process_file(index, path):
    print(f"processing {path}")
    results = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            outer = json5.loads(line)
            msg_content = outer["response"]["body"]["output"][1]["content"][0]["text"]
            inner = json5.loads(msg_content)
            results.append(inner)

    # インデックス付きで返す
    return index, results


def create_metas_monthly(max_workers=16):
    last_month = get_last_month_yyyy_mm()
    paths = sorted(glob.glob(f"data/{last_month}/jsonl/outputs_metas_*.jsonl"))
    monthly_metas = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(process_file, idx, path)
            for idx, path in enumerate(paths)
        ]

        # 完了順ではなく index で整理
        ordered_results = [None] * len(paths)
        for future in as_completed(futures):
            index, results = future.result()
            ordered_results[index] = results

    # append 順序を完全再現
    for results in ordered_results:
        monthly_metas.extend(results)

    return monthly_metas
