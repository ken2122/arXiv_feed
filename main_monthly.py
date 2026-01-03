import asyncio, json5
from services.arXiv_service import fetch_arxiv_papers, filter_papers_by_keywords
from services.openAI_outputs_service import create_openAI_outputs, load_openAI_outputs
from services.LaTeX_service import async_main_institutions
from jobs.create_requests import save_create_topics_requests, save_integration_topics_requests
from jobs.save_feed import create_metas_monthly
from services.create_markdown import create_markdown_monthly
from services.send_message_service import send_message
from utils.utils import load_state, split_metadata_evenly


if __name__ == "__main__":
    metas_monthly = create_metas_monthly()
    md_metas_monthly = create_markdown_monthly(metas_monthly)
    chunks = split_metadata_evenly(md_metas_monthly)
    save_create_topics_requests(chunks)   

    create_openAI_outputs(f"create_topics")

    topics = []
    with open("data/json/feed/outputs_create_topics.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            outer = json5.loads(line)
            msg_content = outer["response"]["body"]["output"][1]["content"][0]["text"]
            topics.append(msg_content)
    save_integration_topics_requests("\n".join(topics))

    create_openAI_outputs(f"integration_topics")

    with open("data/json/feed/outputs_integration_topics.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            outer = json5.loads(line)
            msg_content = outer["response"]["body"]["output"][1]["content"][0]["text"]

    with open("data/md/outputs_integration_topics.md", "w", encoding="utf-8") as f:
        f.write(msg_content)