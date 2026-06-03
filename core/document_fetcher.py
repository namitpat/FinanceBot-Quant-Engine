# core/document_fetcher.py
#
# Fetches SEC EDGAR filings (10-K, 10-Q, 8-K) for the 30 training tickers.
# Extracts clean text from all useful document blocks including EX-99.1
# press releases which contain actual earnings data.
#
# Called once by build_index.py to build the FAISS index.

import os
import re
import json
import time
import html
import traceback

from pathlib import Path
from typing import List, Dict

from sec_edgar_downloader import Downloader

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────

DEFAULT_TICKERS = [
    "AAPL", "ABBV", "AMZN", "BAC",  "CAT",
    "COST", "CVX",  "DUK",  "GE",   "GOOGL",
    "HD",   "JNJ",  "JPM",  "LLY",  "MA",
    "META", "MRK",  "MSFT", "NEE",  "NVDA",
    "PG",   "SO",   "TMUS", "UNH",  "UNP",
    "V",    "VZ",   "WFC",  "WMT",  "XOM",
]

FILING_TYPES   = ["10-K", "10-Q", "8-K"]
LIMIT_PER_TYPE = {
    "10-K": 3,
    "10-Q": 12,
    "8-K":  25,
}

CHUNK_SIZE    = 300
CHUNK_OVERLAP = 50
DOWNLOAD_DIR  = "./sec_filings"
SEC_EMAIL     = "namitmiyani@gmail.com"

# Document types to extract — includes exhibits with real earnings content
USEFUL_TYPES = re.compile(
    r"<TYPE>(8-K|10-K|10-Q|10-K/A|10-Q/A|"
    r"EX-99\.1|EX-99\.2|EX-13|EX-23)",
    re.IGNORECASE
)

# Document types to skip entirely
SKIP_TYPES = re.compile(
    r"<TYPE>(GRAPHIC|ZIP|EXCEL|XML|XBRL|EX-101|"
    r"\.XSD|\.CAL|\.DEF|\.LAB|\.PRE|R\d+\.HTM)",
    re.IGNORECASE
)

# ──────────────────────────────────────────────
# TEXT EXTRACTION
# ──────────────────────────────────────────────

def _extract_text_from_file(filepath: Path) -> str:
    """
    Extract actual filing content from SEC full-submission.txt.
    Pulls all useful document blocks including EX-99.1 press releases
    which contain the actual earnings figures and business commentary.
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read()

        # ── Find all DOCUMENT blocks ──────────────────────────────────
        documents = re.findall(
            r"<DOCUMENT>(.*?)</DOCUMENT>",
            raw,
            flags=re.DOTALL | re.IGNORECASE
        )

        collected_texts = []

        for doc in documents:
            # Skip graphics, XBRL, ZIP and other binary/schema docs
            if SKIP_TYPES.search(doc):
                continue
            # Only keep useful filing types and exhibits
            if not USEFUL_TYPES.search(doc):
                continue

            # Extract <TEXT> section — the actual content
            text_match = re.search(
                r"<TEXT>(.*?)</TEXT>",
                doc,
                flags=re.DOTALL | re.IGNORECASE
            )
            if not text_match:
                continue

            candidate = text_match.group(1).strip()
            # Skip tiny sections (usually just headers)
            if len(candidate) < 500:
                continue

            collected_texts.append(candidate)

        if not collected_texts:
            return ""

        # Join all useful sections into one text block
        combined = " ".join(collected_texts)

        # ── Strip all HTML/SGML tags ──────────────────────────────────
        combined = re.sub(r"<[^>]+>", " ", combined)

        # ── Decode HTML entities (&#160; → space, &#8217; → ') ───────
        combined = html.unescape(combined)

        # ── Remove XBRL member name spam ──────────────────────────────
        # Patterns like: aapl:A1.375NotesDue2024Member
        combined = re.sub(
            r"\b[a-zA-Z]{2,6}:[A-Za-z0-9\.\-]+"
            r"(?:Member|Axis|Domain|Table|LineItems|Abstract)\b",
            " ", combined
        )
        # XBRL date prefixes like aapl-20231102
        combined = re.sub(r"\b[a-z]{2,6}-\d{8}\b", " ", combined)

        # ── Remove SEC metadata boilerplate ───────────────────────────
        junk_patterns = [
            r"ACCESSION NUMBER:", r"CONFORMED SUBMISSION TYPE:",
            r"PUBLIC DOCUMENT COUNT:", r"FILED AS OF DATE:",
            r"DATE AS OF CHANGE:", r"CENTRAL INDEX KEY:",
            r"STANDARD INDUSTRIAL CLASSIFICATION:", r"IRS NUMBER:",
            r"STATE OF INCORPORATION:", r"FISCAL YEAR END:",
            r"SEC FILE NUMBER:", r"FILM NUMBER:",
        ]
        for pattern in junk_patterns:
            combined = re.sub(pattern, " ", combined, flags=re.IGNORECASE)

        # ── Remove exchange name spam (NASDAQ NASDAQ NASDAQ...) ───────
        combined = re.sub(r"\b(NASDAQ|NYSE|AMEX)\b\s*", " ", combined)

        # ── Remove long number sequences (accession numbers etc.) ─────
        combined = re.sub(r"\b\d{8,}\b", " ", combined)
        # ── Remove repeated date spam (XBRL inline dates) ────────────
        combined = re.sub(r"(\b\d{4}-\d{2}-\d{2}\b\s*){2,}", " ", combined)

        # ── Remove XBRL namespace prefixes (us-gaap:, dei:, etc.) ────
        combined = re.sub(
            r"\b(us-gaap|us|dei|ifrs|srt|invest|country|currency|exch)[:\-]\S*",
            " ", combined, flags=re.IGNORECASE
        )

        # ── Remove true/false XBRL value spam ────────────────────────
        combined = re.sub(
            r"\b(true|false)\b", " ", combined, flags=re.IGNORECASE
        )

        # ── Remove non-ASCII characters ───────────────────────────────
        combined = re.sub(r"[^\x00-\x7F]+", " ", combined)

        # ── Final whitespace cleanup ──────────────────────────────────
        combined = re.sub(r"\s+", " ", combined)
        combined = combined.strip()

        return combined

    except Exception as e:
        print(f"[Fetcher] Extraction failed for {filepath.name}: {e}")
        traceback.print_exc()
        return ""


# ──────────────────────────────────────────────
# CHUNKING
# ──────────────────────────────────────────────

def _chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> List[str]:
    """
    Split text into overlapping word-based chunks.
    300-word chunks with 50-word overlap gives good retrieval granularity.
    """
    if not text or len(text.strip()) < 200:
        return []

    words  = text.split()
    chunks = []
    start  = 0

    while start < len(words):
        end   = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        if len(chunk.strip()) > 100:
            chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


# ──────────────────────────────────────────────
# FILE SELECTION
# ──────────────────────────────────────────────

def _find_primary_document(filing_dir: Path) -> Path:
    """
    Find the main filing file in a downloaded directory.
    Prefers full-submission.txt which contains all document blocks.
    Skips index/header files.
    """
    skip_patterns = [
        "hdr.sgml", "index", "filing-details",
        "xsl", "rss", "graphic", "schema",
        "cal", "lab", "pre", "def",
    ]

    candidates = []
    for pattern in ["*.txt", "*.htm", "*.html"]:
        for f in filing_dir.glob(pattern):
            name = f.name.lower()
            if any(x in name for x in skip_patterns):
                continue
            if f.stat().st_size < 2000:
                continue
            candidates.append(f)

    if not candidates:
        return None

    # Prefer full-submission.txt — contains all document blocks
    for c in candidates:
        if "full-submission" in c.name.lower():
            return c

    # Fallback: largest file
    return max(candidates, key=lambda x: x.stat().st_size)


# ──────────────────────────────────────────────
# FETCH ONE TICKER
# ──────────────────────────────────────────────

def fetch_filings_for_ticker(
    ticker: str,
    download_dir: str = DOWNLOAD_DIR,
    filing_types: List[str] = None,
) -> List[Dict]:
    """
    Downloads filings for one ticker and returns a list of chunk dicts.

    Each dict:
      text       : 300-word chunk of clean filing text
      ticker     : e.g. "AAPL"
      form_type  : e.g. "8-K"
      source     : filename
      chunk_id   : sequential integer
    """
    if filing_types is None:
        filing_types = FILING_TYPES

    dl = Downloader("FinanceBotRAG", SEC_EMAIL, download_dir)

    all_chunks = []
    chunk_id   = 0

    for form in filing_types:
        limit = LIMIT_PER_TYPE.get(form, 5)
        print(f"  [{ticker}] Downloading {limit} {form} filings...")

        try:
            dl.get(form, ticker, limit=limit)
            time.sleep(0.5)
        except Exception as e:
            print(f"  [{ticker}] Download failed for {form}: {e}")
            continue

        base = (
            Path(download_dir)
            / "sec-edgar-filings"
            / ticker
            / form
        )

        if not base.exists():
            print(f"  [{ticker}] No directory found for {form}")
            continue

        filing_dirs = [d for d in base.iterdir() if d.is_dir()]
        print(f"  [{ticker}] Found {len(filing_dirs)} {form} filings")

        for filing_dir in filing_dirs:
            try:
                primary = _find_primary_document(filing_dir)
                if primary is None:
                    continue

                text = _extract_text_from_file(primary)

                if not text or len(text) < 200:
                    continue

                chunks = _chunk_text(text)
                if not chunks:
                    continue

                for chunk in chunks:
                    all_chunks.append({
                        "text":      chunk,
                        "ticker":    ticker.upper(),
                        "form_type": form,
                        "source":    primary.name,
                        "chunk_id":  chunk_id,
                    })
                    chunk_id += 1

                # Delete raw file to save disk space
                try:
                    primary.unlink()
                except Exception:
                    pass

            except Exception as e:
                print(f"  [{ticker}] Filing parse error: {e}")
                traceback.print_exc()
                continue

        print(f"  [{ticker}] {form} complete → {chunk_id} total chunks")

    return all_chunks


# ──────────────────────────────────────────────
# FETCH ALL TICKERS
# ──────────────────────────────────────────────

def fetch_all_tickers(
    tickers: List[str] = None,
    download_dir: str = DOWNLOAD_DIR,
    save_progress: bool = True,
    progress_file: str = "rag_chunks_progress.json",
) -> List[Dict]:
    """
    Fetches filings for all tickers.
    Saves progress after each ticker so you can resume if interrupted.
    """
    if tickers is None:
        tickers = DEFAULT_TICKERS

    all_chunks = []
    completed  = set()

    if save_progress and os.path.exists(progress_file):
        print(f"[Fetcher] Resuming from {progress_file}...")
        with open(progress_file, "r") as f:
            saved = json.load(f)
        all_chunks = saved.get("chunks", [])
        completed  = set(saved.get("completed_tickers", []))
        print(f"[Fetcher] Loaded {len(all_chunks):,} chunks "
              f"from {len(completed)} completed tickers")

    remaining = [t for t in tickers if t not in completed]
    print(f"[Fetcher] Fetching {len(remaining)} remaining tickers...\n")

    for i, ticker in enumerate(remaining):
        print(f"\n[Fetcher] [{i+1}/{len(remaining)}] Processing {ticker}...")
        try:
            chunks = fetch_filings_for_ticker(ticker, download_dir)
            all_chunks.extend(chunks)
            completed.add(ticker)
            print(f"[Fetcher] {ticker} done — "
                  f"{len(chunks):,} chunks. "
                  f"Running total: {len(all_chunks):,}")

            if save_progress:
                with open(progress_file, "w") as f:
                    json.dump({
                        "chunks":             all_chunks,
                        "completed_tickers":  list(completed),
                    }, f)

        except Exception as e:
            print(f"[Fetcher] ERROR on {ticker}: {e}")
            traceback.print_exc()
            continue

    print(f"\n[Fetcher] Complete. Total chunks: {len(all_chunks):,}")
    return all_chunks


# ──────────────────────────────────────────────
# QUICK TEST
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("Testing fetcher on AAPL 8-K only...\n")

    chunks = fetch_filings_for_ticker("AAPL", filing_types=["8-K"])

    print(f"\n{'='*60}")
    print(f"Total chunks: {len(chunks)}")

    if chunks:
        print(f"\nSample chunk (first 500 chars):")
        print(chunks[0]["text"][:500])
        print(f"\nMetadata: "
              f"ticker={chunks[0]['ticker']} "
              f"form={chunks[0]['form_type']} "
              f"source={chunks[0]['source']}")

        # Show a later chunk to verify content quality
        if len(chunks) > 10:
            print(f"\nChunk #10 preview:")
            print(chunks[10]["text"][:300])