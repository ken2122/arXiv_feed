import asyncio
from services.arXiv_service import fetch_arxiv_papers, filter_papers_by_keywords
from services.openAI_outputs_service import create_openAI_outputs, load_openAI_outputs
from services.LaTeX_service import async_main_institutions
from jobs.create_requests import save_meta_requests, save_institutions_requests
from jobs.save_feed import save_feed
from services.create_markdown import save_markdown
from services.slack_service import send_slack_message
from utils.utils import load_state


if __name__ == "__main__":
    # feed , new_run = fetch_arxiv_papers()
    # filtered_feed = filter_papers_by_keywords(feed)

    # save_feed(filtered_feed, new_run)
    # save_meta_requests(filtered_feed, new_run)
    # blocks = asyncio.run(async_main_institutions(filtered_feed))
    # save_institutions_requests(blocks, new_run)

    new_run = load_state()
    with open(f"data/json/feed/feed_{new_run}.jsonl", "r", encoding="utf-8") as f:
        feedLines = f.readlines()
    # create_openAI_outputs(f"institutions_{new_run}")
    # create_openAI_outputs(f"metas_{new_run}")

    insts = load_openAI_outputs(f"institutions_{new_run}")
    metas = load_openAI_outputs(f"metas_{new_run}")

    md_texts = save_markdown(feedLines, metas, insts, new_run)
    send_slack_message(md_texts)
