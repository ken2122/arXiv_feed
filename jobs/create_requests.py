import json

def save_meta_requests(papers, new_run):
    requests_metas_buffer = []
    for paper in papers:
        prompt = f"""You are a specialist research analyst in Web3, DeFi, cryptography, and distributed systems.

Your task:
From the paper below (Title + Summary + Link), evaluate how useful each paper is for understanding investment opportunities or technological advantages within the Web3 / crypto / DeFi ecosystem.
Rate each paper on a five-level scale: Highest / High / Medium / Low / Lowest.

"Useful" means:

- Introduces or significantly improves cryptographic primitives with clear relevance to blockchain security, performance, or trust minimization.
- Advances scalability or robustness of decentralized systems, including consensus mechanisms, P2P networking, data availability, or fault tolerance under adversarial or permissionless settings.
- Contributes to zero-knowledge proofs, MPC, or post-quantum cryptography in ways that are plausibly integrable into future L1/L2 or cross-chain architectures.
- Provides novel or practically relevant models of DeFi systems, including AMMs, MEV, liquidation dynamics, risk modeling, or liquidity incentives.
- Improves understanding of smart contract security, economic attack vectors, incentive misalignment, or protocol-level exploits.
- Advances token economics or mechanism design specifically tailored to decentralized, trust-minimized systems.
- Analyzes or mitigates quantum-era threats to blockchain or cryptographic assumptions.
- Represents a non-trivial or step-change improvement (not merely incremental optimization) that could materially enhance decentralization, scalability, privacy, security, or composability.
- Demonstrates potential for real-world protocol adoption, implementation, or influence on future blockchain designs, rather than being purely theoretical with no clear Web3 applicability.

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


def save_create_topics_requests(chunks):
    requests_monthly_buffer = []
    for i, chunk in enumerate(chunks):
        prompt = f"""あなたは最先端技術動向を整理し、**後続の統合処理（意味的統合・構造整理）に耐える情報単位**を設計するリサーチアナリストです。  
以下に与えられる複数の論文メタデータ（最大 40 件）を俯瞰し、**個別論文の評価や重要度判断は行わず**、論文群に共通して現れている研究テーマ・設計思想・論点構造を抽出してください。

# 入力

- 各論文には以下の情報が含まれます
  - title（タイトル）
  - summary（概要）

# タスク

1. 40 件全体を横断的に分析し、以下を満たす「トピック候補」を抽出してください。

   - 単一論文ではなく、**複数論文に共通して現れる研究テーマ・課題・設計思想**
   - もしくは、**同一の問題設定に対する異なるアプローチが複数見られるテーマ**

2. 各トピック候補について、**評価・将来予測を行わず**、論文群から読み取れる事実関係と構造のみを整理してください。

# 出力形式（厳守）

- 箇条書きで **5〜10 件程度** のトピック候補を出力すること
- 各トピック候補は以下の構造で記述すること

```
## {{トピック候補名}}（簡潔な名詞句・20 文字以内を推奨）

- 概要：（複数論文に共通する研究テーマ・問題設定・技術的方向性を 1〜2 文で記述）

- 主な論点／アプローチ：（論文群で繰り返し現れる設計観点・技術的工夫・前提条件を箇条書き）

- 論点の差異・前提の違い（あれば）：（同一テーマ内で見られるアプローチ差・モデル仮定差・スコープ差など）

- 研究スコープ層：（主に扱っているレイヤーを選択：プロトコル層／実装・運用層／理論モデル層／経済・インセンティブ層／横断）

- 関連分野：（PQC / ZK / FHE / 分散システム / ML / 暗号理論 など、一般分野名で）
```

# 注意点（重要）

- **注目度・有望性・成熟度・未解決性といった評価は一切行わないこと**
- 元トピック間に見られる前提の緊張・設計上のトレードオフ・対立的関係は、**評価を伴わない限り、事実として明示してよい**
- 「課題」「分岐」といった表現を用いる場合も、**未解決・重要と断定せず**、「前提差」「設計選択の違い」として記述してください
- 各論文の詳細説明や個別手法の掘り下げは不要。  
  **必ず複数論文に共通する流れ・論点として抽象化**してください
- トピック名・概要は、**以下のいずれか 1 軸で一般化**してください（混在させない）
  - 技術課題軸
  - アーキテクチャ／設計思想軸
  - 応用・ユースケース軸
- 後続ステップで統合されることを前提とし、**固有名詞・プロジェクト名・論文名の多用は避け**、一般概念で表現してください

# 論文メタデータ
{''.join(chunk)}
"""

        entry = {
            "custom_id": f"monthly_part_{i+1}",
            "method": "POST",
            "url": "/v1/responses",
            "body": {
                "model": "gpt-5-mini",
                "input": prompt
            }
        }
        requests_monthly_buffer.append(json.dumps(entry) + "\n")
    with open(f"data/json/feed/requests_create_topics.jsonl", "w") as f:
        f.write(("".join(requests_monthly_buffer)))

    print(f"data/json/feed/requests_create_topics.jsonl Saved")


def save_integration_topics_requests(topics_md):
    prompt = f"""あなたは最先端研究動向を俯瞰し、**複数のトピック候補を意味的に統合・正規化する**メタ分析アナリストです。

以下に与えられるのは、論文数百件を元に

- 評価や将来予測を含まず
- 論文群に共通する「研究テーマ・論点構造・前提差」

として抽出された複数のトピック候補（70〜100 件程）です。

これらは粒度・表現・切り口にばらつきがあり、一部は **重複・包含・近接関係** にあります。

あなたの役割は、**新しい解釈・重要度判断・評価を一切加えず**、後続の上位分析（総括・注視点抽出）が行いやすいように、研究テーマ群を**構造的に整理・統合**することです。

# タスク

1. 意味的に近い、または以下の関係にあるトピック候補をグルーピングしてください。

   - 同一または類似の研究課題を扱っている
   - 共通する設計思想・前提モデルを持つ
   - 主な論点が大きく重なっている
   - 一方が他方を包含する関係にある

2. 各グループについて、**抽象度を一段階上げた「統合トピック」**を作成してください。

3. 統合トピックごとに、トピック候補 で与えられた情報を再配置する形で、以下を整理してください。

4. 明らかに他と統合しづらいトピックは、無理にまとめず「周辺・補助的トピック」として分離してください。

# 出力形式（厳守）

- 箇条書きで **10〜20 件程度** の「統合トピック」を出力すること
- 各統合トピックは、以下の構造で記述すること

```
## {{統合トピック名}}（研究課題・設計思想レベルの名詞句）

- 含まれる元トピック：（トピック候補名を簡潔に列挙）

- 統合の観点：（どの論点・設計思想・問題設定の共通性に基づいて統合したかを 1 行で）

- 共通する研究の流れ：（元トピックの「概要」「主な論点」を統合し、論文群に共通する研究テーマ・設計方向を 1〜2 文で記述）

- 内部の論点差異・設計分岐（あれば）：（元トピックに見られる前提差・アプローチ差・スコープ差を整理）

- 主な研究スコープ層：（プロトコル層／実装・運用層／理論モデル層／経済・インセンティブ層／横断）

- 周辺・補助的トピックがある場合は、以下の形式で最後にまとめてください

### 周辺・補助的トピック

{{トピック名}}：（他の統合トピックと統合しなかった理由を、評価を含めず 1 行で）
```

# 注意点（重要）

- **評価・優劣・重要度・成熟度・将来性の判断は一切行わないこと**
- 元トピック間に見られる前提の緊張・設計上のトレードオフ・対立的関係は、**評価を伴わない限り、事実として明示してよい**
- トピック候補 の内容を「要約し直す」のではなく、**重複・包含・近接関係を整理し、再構造化すること**が目的です
- 統合トピック名は、個別技術名ではなく**研究課題・設計思想・問題設定レベル**で命名してください
- 「研究スコープ層」は、元トピック群で最も支配的なものを選択し、複数にまたがる場合は「横断」としてください
- 判断に迷う場合は、無理に統合せず構造を保ったまま分離してください

# トピック候補
{topics_md}
"""

    entry = {
        "custom_id": f"monthly_part_1",
        "method": "POST",
        "url": "/v1/responses",
        "body": {
            "model": "gpt-5",
            "input": prompt
        }
    }
    with open(f"data/json/feed/requests_integration_topics.jsonl", "w") as f:
        f.write(json.dumps(entry))

    print(f"data/json/feed/requests_integration_topics.jsonl Saved")