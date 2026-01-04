import asyncio
from datetime import datetime
from config.paths import DATA_PATH_RULE
from services.arXiv_service import fetch_arxiv_papers, filter_papers_by_keywords
from services.openAI_outputs_service import create_openAI_outputs, load_openAI_outputs
from services.LaTeX_service import async_main_institutions
from jobs.create_requests import save_meta_requests, save_institutions_requests
from jobs.save_feed import save_feed, integration_feed, load_custom_ids, filter_feed_by_custom_id
from services.create_markdown import save_markdown
from services.send_message_service import send_message
from utils.utils import load_state


if __name__ == "__main__":
    last_run = datetime.fromisoformat(load_state())
    normalized = last_run.replace(hour=0, minute=0, second=0, microsecond=0)

    feed = fetch_arxiv_papers(max_results=2000)
    filtered_feed = filter_papers_by_keywords(feed)

    integrated_feed = integration_feed(normalized)
    custom_ids = load_custom_ids(integrated_feed)

    filtered_feed_by_custom_id = filter_feed_by_custom_id(filtered_feed, custom_ids)
    save_feed(filtered_feed_by_custom_id, normalized)

    save_meta_requests(filtered_feed_by_custom_id, normalized)
    blocks = asyncio.run(async_main_institutions(filtered_feed_by_custom_id))
    save_institutions_requests(blocks, normalized)

    path = DATA_PATH_RULE.build(
        target_date=normalized,
        data_type="jsonl",
        file_name="feed",
    )
    with open(path, "r", encoding="utf-8") as f:
        feedLines = f.readlines()
    create_openAI_outputs("institutions", normalized)
    create_openAI_outputs("metas", normalized)

    insts = load_openAI_outputs("institutions", normalized)
    metas = load_openAI_outputs("metas", normalized)

    md_texts = save_markdown(feedLines, metas, insts, normalized)
    send_message(md_texts, normalized.strftime("%Y-%m-%dT%H:%M:%SZ"))