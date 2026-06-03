# core/rag_service.py
#
# Loads the FAISS index built by build_index.py and answers financial
# document queries using semantic retrieval + LLM synthesis.
#
# Called at query time by the search_financial_documents tool in agent.py.

import os
import json
import numpy as np
import faiss
import torch
import warnings

warnings.filterwarnings("ignore")

from sentence_transformers import SentenceTransformer
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────

EMBEDDING_MODEL = "all-MiniLM-L6-v2"   # 384-dim, fast, good quality
INDEX_PATH      = "financial_index.faiss"
CHUNKS_PATH     = "financial_chunks.json"
TOP_K           = 8                      # number of chunks to retrieve per query
DEVICE          = "cuda" if torch.cuda.is_available() else "cpu"


# ──────────────────────────────────────────────
# RAG SERVICE
# ──────────────────────────────────────────────

class RAGService:
    """
    Semantic search over indexed SEC filings + LLM synthesis.

    Singleton pattern — models load once at startup.
    """

    _instance = None

    def __init__(self):
        print(f"[RAG] Loading embedding model ({EMBEDDING_MODEL}) on {DEVICE}...")
        self.embedder = SentenceTransformer(EMBEDDING_MODEL, device=DEVICE)

        print("[RAG] Loading FAISS index...")
        if not os.path.exists(INDEX_PATH):
            raise FileNotFoundError(
                f"FAISS index not found at {INDEX_PATH}. "
                f"Run build_index.py first."
            )
        self.index = faiss.read_index(INDEX_PATH)

        print("[RAG] Loading chunk metadata...")
        if not os.path.exists(CHUNKS_PATH):
            raise FileNotFoundError(
                f"Chunk metadata not found at {CHUNKS_PATH}. "
                f"Run build_index.py first."
            )
        with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)

        self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

        print(f"[RAG] Ready. Index has {self.index.ntotal} vectors, "
              f"{len(self.chunks)} chunks.")

    @classmethod
    def get_instance(cls) -> "RAGService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── Core retrieval ────────────────────────
    def _embed_query(self, query: str) -> np.ndarray:
        """Convert query text to embedding vector."""
        vec = self.embedder.encode([query], normalize_embeddings=True)
        return vec.astype(np.float32)

    def _retrieve(self, query: str, ticker: str = None, top_k: int = TOP_K):
        """
        Search FAISS for the top-k most relevant chunks.
        If ticker is provided, filters to that ticker's documents.
        """
        query_vec = self._embed_query(query)
        # Search more candidates if filtering by ticker
        search_k = top_k * 10 if ticker else top_k
        search_k = min(search_k, self.index.ntotal)

        distances, indices = self.index.search(query_vec, search_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.chunks):
                continue
            chunk = self.chunks[idx]

            # Filter by ticker if specified
            if ticker and chunk.get("ticker", "").upper() != ticker.upper():
                continue

            results.append({
                "text":      chunk["text"],
                "ticker":    chunk.get("ticker", ""),
                "form_type": chunk.get("form_type", ""),
                "source":    chunk.get("source", ""),
                "score":     float(1 / (1 + dist)),  # convert L2 distance to similarity
            })

            if len(results) >= top_k:
                break

        return results

    # ── LLM synthesis ─────────────────────────
    def _synthesize(self, query: str, chunks: list, ticker: str = None) -> str:
        """
        Pass retrieved chunks to the LLM and get a grounded answer.
        The LLM cannot answer from its own knowledge — only from the chunks.
        """
        if not chunks:
            return (
                f"No relevant documents found in the financial knowledge base"
                f"{' for ' + ticker if ticker else ''}. "
                f"Try rephrasing your query or asking about a different topic."
            )

        # Build context block
        context_parts = []
        for i, c in enumerate(chunks):
            context_parts.append(
                f"[Source {i+1}: {c['ticker']} {c['form_type']} — {c['source']}]\n"
                f"{c['text']}"
            )
        context = "\n\n".join(context_parts)

        system = (
            "You are a financial document analyst specializing in SEC filings. "
            "Answer the user's question using ONLY the provided document excerpts. "
            "Look carefully for dollar amounts, percentages, and numeric figures — "
            "they are often in dense tables or surrounded by legal language. "
            "If you find ANY numbers related to the query, always report them with "
            "their exact values and the period they refer to. "
            "If the answer is truly not present, say so explicitly. "
            "Always cite which source (Source 1, Source 2, etc.) your answer comes from. "
            "No emojis. No financial advice disclaimers in your answer body."
                    )

        user_msg = (
            f"Document excerpts:\n\n{context}\n\n"
            f"Question: {query}"
        )

        response = self.llm.invoke([
            SystemMessage(content=system),
            HumanMessage(content=user_msg),
        ])

        return response.content

    # ── Public API ────────────────────────────
    def search(self, query: str, ticker: str = None) -> str:
        """
        Main entry point called by the agent tool.
        Returns a formatted answer with source citations.
        """
        print(f"[RAG] Query: '{query}' | Ticker filter: {ticker or 'none'}")

        chunks = self._retrieve(query, ticker=ticker)
        print(f"[RAG] Retrieved {len(chunks)} chunks")

        answer = self._synthesize(query, chunks, ticker=ticker)

        # Build source list for the report footer
        if chunks:
            sources = []
            seen    = set()
            for c in chunks:
                key = f"{c['ticker']} {c['form_type']}"
                if key not in seen:
                    sources.append(f"- {c['ticker']} {c['form_type']} ({c['source']})")
                    seen.add(key)

            source_block = "\n".join(sources)

            return (
                f"## DOCUMENT SEARCH — {ticker.upper() if ticker else 'ALL TICKERS'}\n\n"
                f"**Query:** {query}\n\n"
                f"---\n\n"
                f"{answer}\n\n"
                f"---\n\n"
                f"**Sources consulted ({len(chunks)} excerpts):**\n{source_block}\n\n"
                f"*Answers are derived from SEC filings (10-K, 10-Q, 8-K). "
                f"Not financial advice.*"
            )

        return answer

    def get_stats(self) -> dict:
        """Return index statistics."""
        ticker_counts = {}
        form_counts   = {}
        for c in self.chunks:
            t = c.get("ticker", "unknown")
            f = c.get("form_type", "unknown")
            ticker_counts[t] = ticker_counts.get(t, 0) + 1
            form_counts[f]   = form_counts.get(f, 0) + 1

        return {
            "total_chunks":  len(self.chunks),
            "total_vectors": self.index.ntotal,
            "tickers":       len(ticker_counts),
            "by_form":       form_counts,
        }