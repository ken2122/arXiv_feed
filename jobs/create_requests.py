import json

def save_meta_requests(papers, new_run):
    requests_metas_buffer = []
    for paper in papers:
        prompt = f"""You are a specialist research analyst in Web3, DeFi, cryptography, and distributed systems.

    Your task:
    From the paper below (Title + Summary + Link), evaluate how useful each paper is for understanding investment opportunities or technological advantages within the Web3 / crypto / DeFi ecosystem.
    Rate each paper on a five-level scale: Highest / High / Medium / Low / Lowest.

    "Useful" means:

    - Improves understanding of new cryptographic primitives relevant to blockchain performance or security
    - Enhances scalability: distributed systems, P2P networking, consensus mechanisms
    - Advances in zero knowledge, MPC, PQC that could impact future L1/L2 chains
    - DeFi modeling, AMMs, MEV, risk models, liquidity dynamics
    - Smart contract security, attack vectors, economic incentives
    - Token economics, mechanism design for decentralized systems
    - Quantum threats to blockchain or cryptography
    - Any breakthrough that meaningfully improves decentralization, scalability, privacy, or composability

    Output instructions:

    - Output each JSON object in JSON Lines format (one line per paper).

    {{
        "title": title of the paper (in Japanese),
        "summary": A concise summary of the paper (in Japanese),
        "impact_level": "Highest|High|Medium|Low|Lowest",
        "why_matters": An array (JSON array) containing 2–4 bullet points explaining why this paper matters for Web3 investment
    }}

    - Do not output anything except valid JSON object in JSON Lines.
    - "title", "summary", "why_matters" text in the output must be written in Japanese.

    Paper:
    title: {paper['title']}
    summary: {paper['summary']}
    link: {paper['link']}
    """

        entry = {
            "custom_id": paper["link"].rstrip("/").split("/")[-1],
            "method": "POST",
            "url": "/v1/responses",
            "body": {
                "model": "gpt-5-mini",
                "input": prompt
            }
        }
        requests_metas_buffer.append(json.dumps(entry) + "\n")
    with open(f"data/json/feed/requests_metas_{new_run}.jsonl", "w") as f:
        f.write(("".join(requests_metas_buffer)))

    print(f"data/json/feed/requests_metas_{new_run}.jsonl Saved")

def create_institutions_requests(block):
    prompt = f'''You are an affiliation-extraction tool.

Your task:
Given raw LaTeX author/affiliation blocks, extract **only the institution names** and return them in JSON.

Output format:
Return a JSON object in JSON Lines format with the following field:

`{{"institutions": ["Institution A", "Institution B", ...]}}`

Rules:

- Extract only real organization names (universities, research labs, institutes, companies, departments that belong to real institutions).
- Do NOT include:
  - city, state, country (unless explicitly part of the official institution name),
  - departments _unless they are the highest identifiable institution in the block_,
  - emails, ORCID IDs, footnotes, symbols, or metadata.
- Expand LaTeX macros (e.g., `\institution{{...}} → ...`, `\affiliation{{...}} → ...`).
- Remove all LaTeX commands, braces, font/style commands, and comments.
- If multiple institutions appear in the input, extract all of them in the order they appear.
- If the same institution appears multiple times, deduplicate it.
- If no recognizable institution is found, return an empty list.
- Do not hallucinate institutions; extract only what is explicitly stated.
- Do not output anything except valid JSON object in JSON Lines.

Example blocks:

```
[
    "%\n\institution{{Université Grenoble-Alpes, CNRS, Inria, Grenoble INP, LIG}}\n\city{{Grenoble}}\n\country{{France}}",
    "%\n\institution{{University of Tsukuba}}\n\city{{Tsukuba}}\n\country{{Japan}}",
    "%\n\institution{{Université Grenoble-Alpes, CNRS, Inria, Grenoble INP, LIG}}\n\city{{Grenoble}}\n\country{{France}}",
    "Southern Illinois University"  
]
```

Example Output:
`{{"institutions": ["Université Grenoble-Alpes", "CNRS", "Inria", "Grenoble INP", "LIG", "University of Tsukuba", "Southern Illinois University"]}}`

blocks:
{block["institutions"]}
'''

    entry = {
        "custom_id": block["id"],
        "method": "POST",
        "url": "/v1/responses",
        "body": {
            "model": "gpt-5-nano",
            "input": prompt
        }
    }

    return json.dumps(entry) + "\n"



def save_institutions_requests(blocks, new_run):
    requests_institutions_buffer = []

    for block in blocks:
        if not block["institutions"]:
            continue
        requests_institutions_buffer.append(create_institutions_requests(block))

    with open(f"data/json/feed/requests_institutions_{new_run}.jsonl", "w") as f:
        f.write(("".join(requests_institutions_buffer)))

    print(f"data/json/feed/requests_institutions_{new_run}.jsonl Saved")