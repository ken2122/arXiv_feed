import os, json, json5, glob
from concurrent.futures import ThreadPoolExecutor, as_completed
from config.paths import DATA_PATH_RULE

def save_feed(feed, new_run_date):
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
        target_date=new_run_date,
        data_type="jsonl",
        file_name="feed",
    )
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "w") as f:
        f.write(("".join(buffer)))
    print(f"{path} Saved")


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
    paths = sorted(glob.glob("data/json/feed/outputs_metas_2025-12-*.jsonl"))
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
