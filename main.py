import asyncio
from datetime import datetime
from config.paths import DATA_PATH_RULE
from services.arXiv_service import fetch_arxiv_papers, filter_papers_by_keywords
from services.openAI_outputs_service import create_openAI_outputs, load_openAI_outputs
from services.LaTeX_service import async_main_institutions
from jobs.create_requests import save_meta_requests, save_institutions_requests
from jobs.save_feed import save_feed
from jobs.save_state import save_state
from services.create_markdown import save_markdown
from services.send_message_service import send_message
from utils.utils import load_state


if __name__ == "__main__":
    last_run = datetime.fromisoformat(load_state())
    feed = fetch_arxiv_papers(last_run=last_run)
    new_run = feed[0].updated
    new_run_date = datetime.fromisoformat(new_run)
    save_state(new_run)
    filtered_feed = filter_papers_by_keywords(feed)

    save_feed(filtered_feed, new_run_date)
    save_meta_requests(filtered_feed, new_run_date)
    blocks = asyncio.run(async_main_institutions(filtered_feed))
    save_institutions_requests(blocks, new_run_date)

    path = DATA_PATH_RULE.build(
        target_date=new_run_date,
        data_type="jsonl",
        file_name="feed",
    )
    with open(path, "r", encoding="utf-8") as f:
        feedLines = f.readlines()
    create_openAI_outputs("institutions", new_run_date)
    create_openAI_outputs("metas", new_run_date)

    insts = load_openAI_outputs("institutions", new_run_date)
    metas = load_openAI_outputs("metas", new_run_date)

    md_texts = save_markdown(feedLines, metas, insts, new_run_date)
    send_message(md_texts, new_run)
