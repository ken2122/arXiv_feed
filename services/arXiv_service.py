import re
import sys
import json
from datetime import datetime
import requests
import feedparser
from typing import Pattern
from utils.utils import load_state
import random
import time

CATEGORIES = {
    "to_filter": [
        "cs.NI",
        "cs.LO",
        "cs.GT",
        "math.NT",
        "q-fin.TR"
    ],
    "no_filter": [
        "cs.CR",
        "cs.DC"
    ]
}


KEYWORDS = [
    # === Core Web3 ===
    "blockchain", "distributed ledger", "decentralized ledger",
    "web3", "Web3.0", "on-chain", "off-chain", "smart contract",

    # === Protocol / Architecture ===
    "layer1", "layer-1", "L1", "layer2", "layer-2", "L2",
    "rollup", "optimistic rollup", "zk-rollup",
    "state channel", "plasma",
    "data availability", "DA layer",
    "execution layer", "settlement layer",
    "blockchain protocol", "consensus protocol",
    "fork-choice rule", "finality gadget",

    # === Consensus / Security ===
    "proof-of-work", "proof-of-stake",
    "validator set", "slashing condition",
    "Byzantine fault tolerant", "Sybil attack", "51% attack",
    "long-range attack", "nothing at stake", "grinding attack",
    "economic security", "cryptoeconomic",

    # === Cryptography (Web3 Context) ===
    "zero-knowledge", "zkSNARK", "zkSTARK",
    "zk", "zkp", "arithmetic circuit",
    "polynomial commitment", "KZG commitment",
    "multi-party computation", "MPC",
    "post-quantum", "PQC", "quantum-resistant",
    "Fully Homomorphic Encryption", "FHE",

    # === DeFi / Mechanism ===
    "decentralized finance", "defi",
    "dex", "automated market maker", "amm",
    "liquidity mining", "staking reward",
    "governance token", "tokenomics",
    "mechanism design", "incentive compatibility",

    # === Smart Contract / Verification ===
    "smart contract security",
    "formal verification", "model checking",
    "reentrancy", "gas optimization",

    # === Ecosystem / Real Systems ===
    "Ethereum", "EVM", "Solidity",
    "Bitcoin", "Lightning Network",
    "Cosmos", "IBC",
    "Polkadot", "Substrate",
]

def to_datetime(dt):
    return datetime(*dt[:6])

# ===============================
# arXiv API fetch
# ===============================
ARXIV_API = "https://export.arxiv.org/api/query"

HEADERS = {
    "User-Agent": "arxiv-paper-collector/1.0"
}


def fetch_arxiv_papers(
    max_results=500,
    last_run=datetime.fromisoformat("1999-01-01T00:00:00+00:00"),
    id_list=None,
):
    categories = CATEGORIES["to_filter"] + CATEGORIES["no_filter"]

    query = " OR ".join(
        f"cat:{category}"
        for category in categories
    )

    params = {
        "search_query": query,
        "sortBy": "lastUpdatedDate",
        "sortOrder": "descending",
        "start": 0,
        "max_results": max_results,
    }

    if id_list:
        params["id_list"] = id_list

    # arXiv ToU: <= 1 request per 3 seconds
    time.sleep(random.uniform(3, 10))

    max_retries = 5

    for attempt in range(max_retries):
        try:
            response = requests.get(
                ARXIV_API,
                params=params,
                headers=HEADERS,
                timeout=60,
            )

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")

                if retry_after:
                    wait = int(retry_after)
                else:
                    wait = min(300, 30 * (2 ** attempt))

                print(
                    f"arXiv rate limit hit "
                    f"(attempt={attempt+1}/{max_retries}), "
                    f"sleeping {wait}s..."
                )

                time.sleep(wait)
                continue

            response.raise_for_status()

            feed = feedparser.parse(response.text)

            return [
                entry
                for entry in feed.entries
                if datetime.fromisoformat(entry.updated) > last_run
            ]

        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise

            wait = min(300, 10 * (2 ** attempt))

            print(
                f"Request failed: {e} "
                f"(attempt={attempt+1}/{max_retries}), "
                f"retrying in {wait}s..."
            )

            time.sleep(wait)

    raise RuntimeError("Failed to fetch arXiv feed after retries")

# ===============================
# Filtering
# ===============================

def keyword_to_regex(keyword: str) -> Pattern:
    """
    キーワードを検索用regexに変換
    """
    kw = keyword.strip()

    # - _ space を同一視
    escaped = re.escape(kw)
    pattern = re.sub(
        r"(\\-|_|\\\s)+",
        r"[-_\\s]+",
        escaped
    )
    if (len(kw)) >= 5:
        return re.compile(pattern, re.IGNORECASE)
    else:
        return re.compile(rf"\b{pattern}\b", re.IGNORECASE)

def filter_papers_by_keywords(entries):
    results = []

    # 単語境界の正規表現パターンを事前に作成
    patterns = [keyword_to_regex(k) for k in KEYWORDS]

    for entry in entries:
        # -----------------------------
        # ① カテゴリ(term) の抽出
        # -----------------------------
        tags = [t.term for t in entry["tags"]] if hasattr(entry, "tags") else []

        # -----------------------------
        # ② # 条件
        #  to_filter ⊂ tags か？
        #  no_filter ∩ tags = ∅ か？
        # -----------------------------
        has_to_filter = any(cat in tags for cat in CATEGORIES["to_filter"])
        has_no_filter = any(cat in tags for cat in CATEGORIES["no_filter"])

        # → 両方の条件を満たさなければ KEYWORDS 判定不要
        if not (has_to_filter and not has_no_filter):
            results.append(entry)
            continue

        # -----------------------------
        # ③ キーワードフィルタ
        # -----------------------------
        text = (entry["title"] + " " + entry["summary"])
        if any(p.search(text) for p in patterns):
            results.append(entry)

    return results
