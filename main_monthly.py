import json5
from datetime import datetime
from config.paths import DATA_PATH_RULE
from services.openAI_outputs_service import create_openAI_outputs
from jobs.create_requests import save_create_topics_requests, save_integration_topics_requests
from jobs.save_feed import create_metas_monthly
from services.create_markdown import create_markdown_monthly
from utils.utils import load_state, split_metadata_evenly


if __name__ == "__main__":
    last_run = datetime.fromisoformat(load_state())
    metas_monthly = create_metas_monthly()
    md_metas_monthly = create_markdown_monthly(metas_monthly)
    chunks = split_metadata_evenly(md_metas_monthly)
    save_create_topics_requests(chunks, last_run)   

    create_openAI_outputs("create_topics", last_run)

    topics = []
    outputs_create_topics_path = DATA_PATH_RULE.build(
        target_date=last_run,
        data_type="jsonl",
        file_name="outputs_create_topics",
    )
    with open(outputs_create_topics_path, "r", encoding="utf-8") as f:
        for line in f:
            outer = json5.loads(line)
            msg_content = outer["response"]["body"]["output"][1]["content"][0]["text"]
            topics.append(msg_content)
    save_integration_topics_requests("\n".join(topics), last_run)

    create_openAI_outputs("integration_topics", last_run)

    outputs_integration_topics_path = DATA_PATH_RULE.build(
        target_date=last_run,
        data_type="jsonl",
        file_name="outputs_integration_topics",
    )
    with open(outputs_integration_topics_path, "r", encoding="utf-8") as f:
        for line in f:
            outer = json5.loads(line)
            msg_content = outer["response"]["body"]["output"][1]["content"][0]["text"]

    integration_topics_md_path = DATA_PATH_RULE.build(
        target_date=last_run,
        data_type="md",
        file_name="outputs_integration_topics",
    )
    with open(integration_topics_md_path, "w", encoding="utf-8") as f:
        f.write(msg_content)