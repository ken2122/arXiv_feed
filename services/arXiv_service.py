import re
import sys
import json
from datetime import datetime
import requests
import feedparser
from utils.utils import load_state

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
    "blockchain", "distributed ledger", "decentralized ledger", "web3",
    "on-chain", "off-chain", "smart contract",

    # === Protocol / Architecture ===
    "layer-2", "L2", "rollup", "optimistic rollup", "zk-rollup",
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
    "zk", "arithmetic circuit",
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

def fetch_arxiv_papers():
    categories = CATEGORIES["to_filter"] + CATEGORIES["no_filter"]
    query = " OR ".join([f"cat:{c}" for c in categories])
    url = (
        "http://export.arxiv.org/api/query?"
        f"search_query={query}"
        "&sortBy=lastUpdatedDate"
        "&sortOrder=descending"
        # "&id_list=2401.09947v3"
        "&start=0&max_results=500"
    )
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        feed = feedparser.parse(response.text)
        last_run = datetime.fromisoformat(load_state())
    except Exception as e:
        print(str(e))
        sys.exit()
    new_run = feed.entries[0].updated
    new_state = {
        "last_run": new_run
    }

    with open("data/json/state.json", "w", encoding="utf-8") as f:
        json.dump(new_state, f, ensure_ascii=False, indent=2)
    return [
        e for e in feed.entries
        if datetime.fromisoformat(e.updated) > last_run
    ], new_run

# ===============================
# Filtering
# ===============================

def filter_papers_by_keywords(entries):
    results = []

    # 単語境界の正規表現パターンを事前に作成
    patterns = [re.compile(rf"\b{re.escape(k)}\b", re.IGNORECASE) for k in KEYWORDS]

    for entry in entries:
        # -----------------------------
        # ① カテゴリ(term) の抽出
        # -----------------------------
        tags = [t.term for t in entry.tags] if hasattr(entry, "tags") else []

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
        text = (entry.title + " " + entry.summary)

        if any(p.search(text) for p in patterns):
            results.append(entry)

    return results
