import json5
from utils.utils import is_high_impact_or_above

# md 出力
def save_markdown(feedLines, metas, insts, new_run):
    highs = []
    others = []
    for line in feedLines:
        entry = json5.loads(line)

        cid = entry["custom_id"]
        link = entry["link"]
        categories = entry["categories"]

        # ---- institutions (outputs_institutions.jsonl) ----
        institutions = insts.get(cid, {}).get("institutions", [])

        # ---- meta summary / impact / why_matters (outputs_metas.jsonl) ----
        meta = metas[cid]
        title = meta.get("title", "")
        summary = meta.get("summary", "")
        impact_level = meta.get("impact_level", "")
        why_matters = meta.get("why_matters", [])

        if is_high_impact_or_above(impact_level):
            papers = highs
        else:
            papers = others

        inst_block = "\n".join(f"- {inst}" for inst in institutions)
        why_block = "\n".join(f"- {mat}" for mat in why_matters)

        # ---- Markdown 出力 ----
        content = f"""# {title}
{link}

## institutions
{inst_block}

## summary
{summary}

## impact_level: {impact_level}

## why_matters
{why_block}

## categories
{categories}

"""

        papers.append(content)
    
    with open(f"data/md/output_high_{new_run}.md", "w", encoding="utf-8", errors="surrogatepass") as out_high, \
        open(f"data/md/output_other_{new_run}.md", "w", encoding="utf-8", errors="surrogatepass") as out_other:
        out_high.write(''.join(highs))
        print(f"data/md/output_high_{new_run}.md saved")
        out_other.write(''.join(others))
        print(f"data/md/output_other_{new_run}.md saved")

    return highs


def create_markdown_monthly(metas):
    highs = []
    for meta in metas:

        title = meta.get("title", "")
        summary = meta.get("summary", "")
        impact_level = meta.get("impact_level", "")

        if is_high_impact_or_above(impact_level):
            # ---- Markdown 出力 ----
            content = f"""## {title}

### summary
{summary}

"""
            highs.append(content)

    return highs