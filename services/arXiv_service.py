import re
import sys
import json
from datetime import datetime
import requests
import feedparser
from utils.utils import load_state

CATEGORIES = {
    "to_filter": [
        "quant-ph",
        "math.NT",
        "q-fin.EC",
        "q-fin.TR",
        "q-fin.PR",
        "q-fin.ST",
        "q-fin.MF",
    ],
    "no_filter": [
        "cs.CR",
        "cs.DC",
        "cs.NI",
    ]
}


KEYWORDS = [
    "blockchain", "distributed ledger", "decentralized ledger", "web3",
    "on-chain", "off-chain", "smart contract", "cryptocurrency", "cryptoasset",
    "token", "tokenomics", "consensus", "proof-of-work", "proof-of-stake",
    "validator", "finality", "Byzantine", "Byzantine fault tolerant",
    "zero-knowledge", "zk", "zkSNARK", "zkSTARK", "multi-party computation", "MPC",

    "defi", "decentralized finance", "decentralised finance",
    "dex", "amm", "automated market maker", "yield farming",
    "liquidity mining", "liquidity provider",
    "mev", "miner extractable value", "maximal extractable value",
    "liquidation", "stablecoin", "oracle", "staking",
    "liquid staking", "re-staking", "bridge", "cross-chain",
    "lending protocol", "borrowing protocol",

    "token design", "token mechanism", "mechanism design",
    "incentive mechanism", "incentive compatibility",
    "auction", "game-theoretic", "game theory",
    "equilibrium", "nash equilibrium",
    "staking model", "consensus market model",
    "security budget", "slashing",

    "cryptographic", "cryptography", "post-quantum", "PQC",
    "lattice", "LWE", "RLWE", "homomorphic", "FHE",
    "secure multi-party computation",

    "zero-knowledge proof", "polynomial commitment",
    "KZG commitment", "sum-check", "Plonk", "Halo",

    "quantum-resistant", "quantum safe", "quantum attack",
    "Shor", "Grover",

    "elliptic curve", "elliptic curve cryptography",
    "ECC", "number theoretic transform", "NTT",
    "finite field", "modular arithmetic",

    "distributed system", "distributed consensus", "p2p",
    "peer-to-peer", "Sybil attack", "51% attack",
    "censorship resistance", "fork choice",
    "network latency", "adversarial model"
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
