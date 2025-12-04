import json

def save_feed(feed, new_run):
    buffer = []

    for paper in feed:
        link = paper["link"]
        entry = {
            "custom_id": link.rstrip("/").split("/")[-1],
            "link": link,
            "categories": ", ".join([t.term for t in paper["tags"]])
        }
        buffer.append(json.dumps(entry) + "\n")

    with open(f"data/json/feed/feed_{new_run}.jsonl", "w") as f:
        f.write(("".join(buffer)))
    print(f"feed_{new_run}.jsonl Saved")