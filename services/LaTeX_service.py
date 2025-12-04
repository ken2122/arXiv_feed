import os, tarfile, re, sys
import random
from typing import List, Dict
from traceback import format_exc
from math import log
import asyncio
import aiohttp
from concurrent.futures import ProcessPoolExecutor
import tarfile
import tempfile
from utils.utils import chunker

class LatexExtractionError(Exception):
    def __init__(self, message, error_code=None):
        super().__init__(message)
        self.error_code = error_code


def extract_tex(files: dict) -> dict:
    # .tex のみ抽出
    tex_files = {name: text for name, text in files.items() if name.endswith(".tex")}
    if not tex_files:
        raise LatexExtractionError(
            "No .tex files in source tarball.",
            error_code="NO_TEX_FILES"
        )
    return tex_files


def extract_brace_block(text: str, start_index: int) -> tuple[str, int]:
    """
    text[start_index] が `{` であることを前提に、
    対応する `}` までの部分文字列を返す。
    ネスト無限対応。改行や LaTeX コマンドも問題なし。
    戻り値は (ブロック文字列, ブロック終了位置)
    """
    
    depth = 0
    i = start_index
    while i < len(text):
        c = text[i]

        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == -1:
                # ブロック全体を返す（外側の {} を含む）
                return text[start_index:i]

        i += 1

    # 対応する } が無い場合
    return None


def extract_pat_blocks(tex: str, pattern: str) -> list[str]:
    """
    \cmd{ ... } の最上位ブロックをすべて抽出する。
    cmd には "author" や "affiliation" などを入れる。
    """

    blocks = []

    for m in re.finditer(pattern, tex):
        start = m.end()  # { の位置
        block = extract_brace_block(tex, start)
        if block:
            blocks.append(block)

    return blocks


def extract_institutions(tex: str) -> list:
    """
    arXiv TeX から所属候補を最大限拾う。
    """

    affiliations = []

    # ---------- (1) 構造ブロック ----------

    # 無限ネスト対応
    # NEST = r"(?:[^{}]|\{(?R)\})*"
    NEST = r"(?:[^{}]|\{(?R)\})*?"


    # -----------------------------
    # 1) 共通テンプレート（1 引数 / 2 引数）
    # -----------------------------
    TEMPLATE_COMMON = [
        # 2 引数版: \cmd{arg1}{arg2}
        rf"\\{{cmd}}\s*\{{.*?\}}\s*\{{",

        # 1 引数版: \cmd{arg}
        rf"\\{{cmd}}\s*\{{",

        # オプション付き: \cmd[opt]{arg}
        rf"\\{{cmd}}\s*\[[^\]]*\]\s*\{{",
    ]

    # -----------------------------
    # 2) 対象コマンド一覧
    # -----------------------------
    CMD_LIST = [
        "affiliation",
        "affiliations",
        "affil",
        "address",
        "institute",
        "altaffiliation",
        "institution",
    ]

    # REVTeX 系
    CMD_LIST += [
        "affiliation\\*",   # \affiliation* もOK
    ]

    # IEEE / elsarticle / JHEP / others
    CMD_LIST += [
        "email",
        "IEEEauthorblockA",
        "IEEEauthorblockN",
        "tnotetext",
        "inst",
        "thanks",
    ]

    # author （特殊マクロ、1種類だが他と同じ構造を採用）
    CMD_LIST += [
        "author",
    ]

    # その他
    CMD_LIST += [
        "mlsysaffiliation",
        "icmlaffiliation",
    ]

    # -----------------------------
    # 3) テンプレートを展開して AFF_RE_LIST を構築
    # -----------------------------
    AFF_RE_LIST = []

    # 1/2 引数テンプレートを持つコマンド
    for cmd in CMD_LIST:
        for tmpl in TEMPLATE_COMMON:
            AFF_RE_LIST.append(
                tmpl.replace("{cmd}", cmd)
            )

    for pat in AFF_RE_LIST:
        affiliations.extend(extract_pat_blocks(tex, pat))

    return affiliations


# ----------------------------------
# tar 展開（別プロセスで実行される関数）
# ----------------------------------
def extract_tar_from_path(path: str) -> dict:
    """別プロセスで実行：tar 展開 → dict にして返す"""
    files = {}
    with tarfile.open(path, "r:*") as tar:
        for m in tar.getmembers():
            if m.isfile():
                f = tar.extractfile(m)
                if f:
                    try:
                        files[m.name] = f.read().decode("utf-8", errors="ignore")
                    except Exception:
                        pass
    return files


# ----------------------------------
# メイン async 処理：tarball を streaming DL
# ----------------------------------
sem = asyncio.Semaphore(5)

async def download_and_extract(entry, session, executor):
    """
    - tarball をストリーミング DL（RAM に全読み込みしない）
    - 完成した temp file の path を CPU プロセスに渡して tar 展開
    """
    url = entry["link"].replace("abs", "e-print")

    async with sem:  
        # temp file を使い streaming で書く
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
            async with session.get(url) as resp:
                resp.raise_for_status()

                async for chunk in resp.content.iter_chunked(1024 * 64):
                    if b"<html>\n     <head>\n       <title>arXiv reCAPTCHA</title>" in chunk:
                        raise LatexExtractionError(
                            "arXiv reCAPTCHA.",
                            error_code="RE_CAPTCHA"
                        )
                    tmp.write(chunk)

    # CPU bound: 別プロセスへ
    loop = asyncio.get_event_loop()
    files = await loop.run_in_executor(executor, extract_tar_from_path, tmp_path)

    return files


# -----------------------------
# 全 .tex 走査 → 組織情報ブロック収集
# -----------------------------

def extract_institutions_from_all_tex(tex_files: dict) -> list:
    """
    arXiv の全 .tex を走査して
    affiliation/author ブロックをすべて抽出する処理。
    main.tex 推定は行わない。
    """

    all_affiliations = []

    for fname, text in tex_files.items():
        blocks = extract_institutions(text)
        if blocks:
            all_affiliations.extend(blocks)

    if not all_affiliations:
        raise LatexExtractionError(
            "No affiliation blocks found in any .tex files",
            error_code="NO_INSTITUTIONS"
        )

    # 重複除去しつつ順序維持
    uniq = list(dict.fromkeys(all_affiliations))

    return uniq


# -----------------------------
# institutionsを抽出できなかった .tex を保存
# -----------------------------

def save_failed_tex(id, tex_files):
    #  保存ディレクトリ名生成
    save_dir = os.path.join("data/log/failed_tex", id)
    os.makedirs(save_dir, exist_ok=True)
    # files を保存
    for filename, content in tex_files.items():
        path = os.path.join(save_dir, filename)
        # 必要なサブディレクトリを作成
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # content が text か bytes かに対応
        mode = "wb" if isinstance(content, bytes) else "w"
        with open(path, mode, encoding=None if mode == "wb" else "utf-8") as f:
            f.write(content)


# ----------------------------------
# fetch_institutions (元の関数と互換)
# ----------------------------------
async def fetch_institutions_async(entry, session, executor):
    id = entry["link"].rstrip("/").split("/")[-1]
    tex_files = []
    institutions = []
    # ★ reCAPTCHA 回避：人間的アクセス間隔を作る
    await asyncio.sleep(random.uniform(0.2, 1.3))

    try:
        files = await download_and_extract(entry, session, executor)
        tex_files = extract_tex(files)
        # LaTeX を解析
        loop = asyncio.get_running_loop()
        institutions = await loop.run_in_executor(
            executor,
            extract_institutions_from_all_tex,
            tex_files
        )
        save_failed_tex(id, tex_files)
    except LatexExtractionError as e:
        with open("data/log/LaTeX_error_log.txt", "a", encoding="utf-8") as f:
            f.write(f"{format_exc()}\n")
            f.write(f"url:{entry['link']}\n")
            f.write(f"{'-'*80}\n")
        if e.error_code == "NO_INSTITUTIONS":
            save_failed_tex(id, tex_files)
        elif e.error_code == "RE_CAPTCHA":
            print(str(e))
            sys.exit()
    except Exception:
        with open("data/log/LaTeX_error_log.txt", "a", encoding="utf-8") as f:
            f.write(f"{format_exc()}\n")
            f.write(f"url:{entry['link']}\n")
            f.write(f"{'-'*80}\n")
    return {
        "id": id,
        "institutions": institutions,
    }


# ----------------------------------
# Run（1バッチ）を実行
# ----------------------------------

USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",

    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",

    # Linux Mac
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",

    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",

    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",

    # Safari Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]

async def run_single_batch(entries_batch):
    # --- UA をバッチ単位で選ぶ ---
    ua = random.choice(USER_AGENTS)

    # --- セッション構築（UA と Cookie 新規） ---
    connector = aiohttp.TCPConnector(
        limit=50,
        force_close=False,
        enable_cleanup_closed=True
    )
    timeout = aiohttp.ClientTimeout(
        total=300,
        connect=15,
        sock_connect=15,
        sock_read=90
    )
    cookie_jar = aiohttp.CookieJar()
    executor = ProcessPoolExecutor(max_workers=4)

    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        cookie_jar=cookie_jar,
        headers={"User-Agent": ua},  
    ) as session:

        tasks = [
            fetch_institutions_async(entry, session, executor)
            for entry in entries_batch
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

    return results


# ----------------------------------
# メイン：300件 × 複数 run を実行
# ----------------------------------
async def async_main_institutions(entries):
    BATCH_SIZE = 300

    all_results = []

    for idx, batch in enumerate(chunker(entries, BATCH_SIZE)):
        print(f"\n=== RUN {idx+1} / (size {len(batch)}) ===")
        run_results = await run_single_batch(batch)
        all_results.extend(run_results)

    return all_results