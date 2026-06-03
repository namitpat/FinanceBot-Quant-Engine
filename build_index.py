# build_index.py
#
# ONE-TIME SCRIPT — run this once to build the FAISS index.
# After this script completes, the app uses the saved index at query time.
#
# Runtime estimate: 3-6 hours (SEC download) + 5-10 mins (GPU embedding)
# Disk space needed: ~8GB during download, ~500MB final index
#
# Usage:
#   python build_index.py               # full build, all 30 tickers
#   python build_index.py --test        # test with AAPL only (fast)
#   python build_index.py --resume      # resume interrupted build

import os
import sys
import json
import time
import argparse
import numpy as np
import faiss
import torch

from sentence_transformers import SentenceTransformer
from core.document_fetcher import fetch_all_tickers, fetch_filings_for_ticker, DEFAULT_TICKERS

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
INDEX_PATH      = "financial_index.faiss"
CHUNKS_PATH     = "financial_chunks.json"
PROGRESS_FILE   = "rag_chunks_progress.json"
BATCH_SIZE      = 256      # chunks per embedding batch (GPU: 512, CPU: 64)
DEVICE          = "cuda" if torch.cuda.is_available() else "cpu"

print(f"\n{'='*60}")
print(f"FinanceBot RAG Index Builder")
print(f"Device: {DEVICE}")
print(f"{'='*60}\n")


# ──────────────────────────────────────────────
# STEP 1 — FETCH DOCUMENTS
# ──────────────────────────────────────────────

def fetch_documents(test_mode: bool = False, resume: bool = True) -> list:
    """
    Download SEC filings and return list of chunk dicts.
    Saves progress after each ticker so you can resume if interrupted.
    """
    if test_mode:
        print("[Step 1] TEST MODE — fetching AAPL 8-K only...")
        chunks = fetch_filings_for_ticker("AAPL", filing_types=["8-K"])
        print(f"[Step 1] Test complete. Got {len(chunks)} chunks.")
        return chunks

    # Check if we already have a complete chunk file
    if os.path.exists(CHUNKS_PATH) and not resume:
        print(f"[Step 1] Found existing {CHUNKS_PATH} — skipping download.")
        with open(CHUNKS_PATH, "r") as f:
            return json.load(f)

    print(f"[Step 1] Fetching filings for {len(DEFAULT_TICKERS)} tickers...")
    print(f"         This will take 3-6 hours. Progress saved after each ticker.")
    print(f"         If interrupted, run with --resume to continue.\n")

    chunks = fetch_all_tickers(
        tickers=DEFAULT_TICKERS,
        save_progress=resume,
        progress_file=PROGRESS_FILE,
    )

    print(f"\n[Step 1] Download complete. Total chunks: {len(chunks)}")
    return chunks


# ──────────────────────────────────────────────
# STEP 2 — EMBED CHUNKS
# ──────────────────────────────────────────────

def embed_chunks(chunks: list, batch_size: int = BATCH_SIZE) -> np.ndarray:
    """
    Convert all text chunks into embedding vectors using sentence-transformers.
    Uses GPU if available — RTX 4060 will process 50k chunks in ~5 minutes.
    """
    print(f"\n[Step 2] Embedding {len(chunks)} chunks on {DEVICE}...")
    print(f"         Model: {EMBEDDING_MODEL}")
    print(f"         Batch size: {batch_size}")

    model = SentenceTransformer(EMBEDDING_MODEL, device=DEVICE)

    texts = [c["text"] for c in chunks]
    total = len(texts)
    all_embeddings = []

    start_time = time.time()

    for i in range(0, total, batch_size):
        batch = texts[i : i + batch_size]
        embeddings = model.encode(
            batch,
            normalize_embeddings=True,   # L2 normalize for cosine similarity
            show_progress_bar=False,
        )
        all_embeddings.append(embeddings)

        # Progress report every 10 batches
        if (i // batch_size) % 10 == 0:
            done    = min(i + batch_size, total)
            elapsed = time.time() - start_time
            rate    = done / elapsed if elapsed > 0 else 0
            eta     = (total - done) / rate if rate > 0 else 0
            print(f"  Embedded {done}/{total} chunks "
                  f"({done/total*100:.1f}%) — "
                  f"ETA: {eta/60:.1f} min")

    embeddings_matrix = np.vstack(all_embeddings).astype(np.float32)
    elapsed = time.time() - start_time
    print(f"[Step 2] Embedding complete in {elapsed/60:.1f} min. "
          f"Shape: {embeddings_matrix.shape}")

    return embeddings_matrix


# ──────────────────────────────────────────────
# STEP 3 — BUILD FAISS INDEX
# ──────────────────────────────────────────────

def build_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    """
    Build a FAISS IndexFlatIP (inner product = cosine similarity on normalized vectors).
    For 50k vectors at 384 dims, flat index is fast enough at query time (~5ms).
    """
    print(f"\n[Step 3] Building FAISS index...")

    dim   = embeddings.shape[1]   # 384 for all-MiniLM-L6-v2
    index = faiss.IndexFlatIP(dim)   # inner product on normalized = cosine similarity
    index.add(embeddings)

    print(f"[Step 3] Index built. Total vectors: {index.ntotal}, Dimensions: {dim}")
    return index


# ──────────────────────────────────────────────
# STEP 4 — SAVE TO DISK
# ──────────────────────────────────────────────

def save_artifacts(index: faiss.Index, chunks: list):
    """Save the FAISS index and chunk metadata to disk."""
    print(f"\n[Step 4] Saving artifacts...")

    faiss.write_index(index, INDEX_PATH)
    print(f"  Saved FAISS index → {INDEX_PATH} "
          f"({os.path.getsize(INDEX_PATH) / 1e6:.1f} MB)")

    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)
    print(f"  Saved chunk metadata → {CHUNKS_PATH} "
          f"({os.path.getsize(CHUNKS_PATH) / 1e6:.1f} MB)")


# ──────────────────────────────────────────────
# STEP 5 — VERIFY
# ──────────────────────────────────────────────

def verify_index():
    """Quick sanity check — load the index and run a test query."""
    print(f"\n[Step 5] Verifying index...")

    from core.rag_service import RAGService
    svc = RAGService.get_instance()

    test_query  = "Apple iPhone revenue growth"
    result      = svc.search(test_query, ticker="AAPL")

    print(f"\nTest query: '{test_query}'")
    print(f"Result preview:\n{result[:500]}...")

    stats = svc.get_stats()
    print(f"\nIndex statistics:")
    print(f"  Total chunks:  {stats['total_chunks']:,}")
    print(f"  Total vectors: {stats['total_vectors']:,}")
    print(f"  Tickers:       {stats['tickers']}")
    print(f"  By form type:  {stats['by_form']}")


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Build FinanceBot RAG index")
    parser.add_argument("--test",   action="store_true",
                        help="Test mode: AAPL 8-K only (fast)")
    parser.add_argument("--resume", action="store_true", default=True,
                        help="Resume interrupted build (default: True)")
    parser.add_argument("--skip-download", action="store_true",
                        help="Skip download, use existing chunks file")
    args = parser.parse_args()

    total_start = time.time()

    # Step 1 — Fetch documents
    if args.skip_download and os.path.exists(CHUNKS_PATH):
        print(f"[Step 1] Skipping download, loading {CHUNKS_PATH}...")
        with open(CHUNKS_PATH, "r") as f:
            chunks = json.load(f)
        print(f"[Step 1] Loaded {len(chunks):,} chunks from disk.")
    else:
        chunks = fetch_documents(test_mode=args.test, resume=args.resume)

    if not chunks:
        print("ERROR: No chunks fetched. Check your internet connection and SEC EDGAR access.")
        sys.exit(1)

    print(f"\nTotal chunks to index: {len(chunks):,}")

    # Step 2 — Embed
    batch = 512 if DEVICE == "cuda" else 64
    embeddings = embed_chunks(chunks, batch_size=batch)

    # Step 3 — Build FAISS index
    index = build_faiss_index(embeddings)

    # Step 4 — Save
    save_artifacts(index, chunks)

    # Step 5 — Verify
    verify_index()

    # Summary
    elapsed = time.time() - total_start
    print(f"\n{'='*60}")
    print(f"Build complete in {elapsed/60:.1f} minutes")
    print(f"Index: {INDEX_PATH}")
    print(f"Metadata: {CHUNKS_PATH}")
    print(f"Total chunks indexed: {len(chunks):,}")
    print(f"{'='*60}")
    print(f"\nYou can now run: python -m streamlit run app.py")


if __name__ == "__main__":
    main()