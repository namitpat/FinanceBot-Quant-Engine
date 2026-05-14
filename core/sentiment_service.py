# core/sentiment_service.py
#
# Wraps the NewsSentimentEngine from financial_sentiment.ipynb (Dhruv's work)
# into a clean interface that returns per-day sentiment scores for a ticker.
#
# Integration point: called by agent.py tool → feeds into forecast_risk.py
# NOT fed into TFT features (model was trained without sentiment — would crash).

import datetime
import math
import warnings
import requests
import pandas as pd
import numpy as np
import torch

warnings.filterwarnings("ignore")

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    pipeline,
)
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────

FINNHUB_API_KEY   = "d2vhh09r01qm5lo8bhb0d2vhh09r01qm5lo8bhbg"  # from teammate's notebook
FINNHUB_NEWS_URL  = "https://finnhub.io/api/v1/company-news"

FINBERT_MODEL     = "ProsusAI/finbert"
# deberta-v3-base is NOT fine-tuned for sentiment — replaced with a fine-tuned variant
DEBERTA_MODEL     = "cardiffnlp/twitter-roberta-base-sentiment-latest"

DEVICE = 0 if torch.cuda.is_available() else -1

HALF_LIFE_DAYS = 7.0  # recency decay from teammate's notebook

# Sector keyword map — from teammate's relevance scoring logic
SECTOR_KEYWORDS = {
    "tech":  ["chip", "ai", "software", "data", "cloud", "semiconductor",
               "internet", "iphone", "device", "nvidia", "google", "apple", "microsoft"],
    "auto":  ["ev", "battery", "vehicle", "car", "autonomous", "tesla"],
    "finance": ["bank", "rate", "fed", "interest", "credit", "loan", "earnings", "revenue"],
    "macro": ["inflation", "interest", "fed", "market", "recession",
              "trade", "stocks", "economy", "gdp"],
}

TICKER_SECTOR_MAP = {
    "AAPL": "tech",  "MSFT": "tech",  "NVDA": "tech",
    "GOOGL": "tech", "META": "tech",  "AMZN": "tech",
    "TSLA": "auto",  "F": "auto",     "GM": "auto",
    "GS": "finance", "JPM": "finance","BAC": "finance",
    "SPY": "macro",  "QQQ": "tech",
}


# ──────────────────────────────────────────────
# HELPERS  (from teammate's notebook)
# ──────────────────────────────────────────────

def _recency_weight(days_old: float, half_life: float = HALF_LIFE_DAYS) -> float:
    """Exponential decay — more recent news gets higher weight."""
    return math.exp(-math.log(2) * (days_old / half_life))


def _label_to_numeric(label: str, score: float) -> float:
    """Convert POS/NEG/NEU + confidence into a signed float."""
    lbl = label.upper()
    if "POS" in lbl:  return  score
    if "NEG" in lbl:  return -score
    return 0.0


def _relevance_score(text: str, ticker: str, sector: str) -> int:
    """
    From teammate's market relevance layer:
      3 = direct ticker/company mention
      2 = same sector keyword
      1 = macro keyword
      0 = irrelevant
    """
    lower = text.lower()
    if ticker.lower() in lower:
        return 3
    if any(kw in lower for kw in SECTOR_KEYWORDS.get(sector, [])):
        return 2
    if any(kw in lower for kw in SECTOR_KEYWORDS["macro"]):
        return 1
    return 0


def _relevance_weight(relevance: int) -> float:
    return {3: 1.0, 2: 0.7, 1: 0.4, 0: 0.0}[relevance]


def _intensity_weight(sentiment_score: float) -> float:
    """Strong signals get a small boost."""
    a = abs(sentiment_score)
    if a > 0.7: return 1.2
    if a > 0.3: return 1.0
    return 0.8


# ──────────────────────────────────────────────
# CORE ENGINE  (adapted from teammate's class)
# ──────────────────────────────────────────────

class NewsSentimentEngine:
    """
    Three-model ensemble sentiment engine.
    Based on Dhruv's NewsSentimentEngine in financial_sentiment.ipynb.
    Adapted to:
      - fix DeBERTa model (base → fine-tuned)
      - return a date-indexed Series instead of a flat DataFrame
      - accept a Finnhub key at construction time
    """

    _instance = None  # singleton — models are expensive to load

    def __init__(self, finnhub_key: str = FINNHUB_API_KEY):
        self.finnhub_key = finnhub_key
        self.vader = SentimentIntensityAnalyzer()

        print("[SentimentEngine] Loading FinBERT...")
        self.tok1    = AutoTokenizer.from_pretrained(FINBERT_MODEL)
        self.model1  = AutoModelForSequenceClassification.from_pretrained(FINBERT_MODEL)
        self.pipe1   = pipeline("sentiment-analysis", model=self.model1,
                                tokenizer=self.tok1, device=DEVICE,
                                truncation=True, max_length=512)

        # REPLACE with:
        print("[SentimentEngine] Loading RoBERTa sentiment model...")
        try:
            self.tok2 = AutoTokenizer.from_pretrained(DEBERTA_MODEL)
        except Exception:
            self.tok2 = AutoTokenizer.from_pretrained(DEBERTA_MODEL, use_fast=False)
        self.model2  = AutoModelForSequenceClassification.from_pretrained(DEBERTA_MODEL)
        self.pipe2   = pipeline("sentiment-analysis", model=self.model2,
                                tokenizer=self.tok2, device=DEVICE,
                                truncation=True, max_length=512)

        print("[SentimentEngine] Ready.")

    @classmethod
    def get_instance(cls) -> "NewsSentimentEngine":
        """Singleton loader — prevents reloading models on every tool call."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── Finnhub fetch ─────────────────────────
    def _fetch_news(self, ticker: str, days: int) -> pd.DataFrame:
        end   = datetime.date.today()
        start = end - datetime.timedelta(days=days)
        url   = (
            f"{FINNHUB_NEWS_URL}?symbol={ticker}"
            f"&from={start}&to={end}&token={self.finnhub_key}"
        )
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, list) or len(data) == 0:
                return pd.DataFrame()
            df = pd.DataFrame(data)
            df["date"] = pd.to_datetime(df["datetime"], unit="s").dt.date
            return df
        except Exception as e:
            print(f"[SentimentEngine] Finnhub fetch failed: {e}")
            return pd.DataFrame()

    # ── Per-article scoring ───────────────────
    def _score_articles(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df

        # build text from headline + summary
        def _text(row):
            parts = []
            if pd.notnull(row.get("headline")): parts.append(str(row["headline"]))
            if pd.notnull(row.get("summary")):  parts.append(str(row["summary"])[:300])
            return " ".join(parts)[:512]

        df = df.copy()
        df["text"] = df.apply(_text, axis=1)
        texts = df["text"].tolist()

        # FinBERT
        m1 = self.pipe1(texts, batch_size=16)
        df["m1_label"] = [r["label"].upper() for r in m1]
        df["m1_score"] = [r["score"]          for r in m1]

        # DeBERTa
        m2 = self.pipe2(texts, batch_size=16)
        df["m2_label"] = [("POS" if "POS" in r["label"].upper() else
                           "NEG" if "NEG" in r["label"].upper() else "NEU")
                          for r in m2]
        df["m2_score"] = [r["score"] for r in m2]

        # VADER
        df["vader"] = df["text"].apply(
            lambda t: self.vader.polarity_scores(t)["compound"]
        )

        # Ensemble  (45 / 35 / 20 — from teammate's weights)
        df["ensemble"] = (
            0.45 * df.apply(lambda r: _label_to_numeric(r["m1_label"], r["m1_score"]), axis=1) +
            0.35 * df.apply(lambda r: _label_to_numeric(r["m2_label"], r["m2_score"]), axis=1) +
            0.20 * df["vader"]
        )

        return df

    # ── Public API ────────────────────────────
    def get_daily_sentiment(
        self,
        ticker: str,
        days: int = 30,
    ) -> pd.Series:
        """
        Returns a pd.Series indexed by date (datetime.date objects),
        values are recency-and-relevance-weighted sentiment scores in [-1, +1].

        Used by SentimentService.get_sentiment_features().
        """
        sector = TICKER_SECTOR_MAP.get(ticker.upper(), "macro")

        df = self._fetch_news(ticker, days=days)
        if df.empty:
            return pd.Series(dtype=float)

        df = self._score_articles(df)

        # Relevance weighting
        df["relevance"]    = df["text"].apply(lambda t: _relevance_score(t, ticker, sector))
        df["rel_weight"]   = df["relevance"].apply(_relevance_weight)
        df["int_weight"]   = df["ensemble"].apply(_intensity_weight)
        df["final_score"]  = df["ensemble"] * df["rel_weight"] * df["int_weight"]

        # Filter irrelevant articles
        df = df[df["relevance"] > 0]
        if df.empty:
            return pd.Series(dtype=float)

        # Recency weight
        now = pd.Timestamp.utcnow().date()
        df["days_old"]    = df["date"].apply(lambda d: (now - d).days)
        df["recency_w"]   = df["days_old"].apply(_recency_weight)
        df["weighted"]    = df["final_score"] * df["recency_w"]

        # Aggregate per day (weighted mean)
        grouped = df.groupby("date").apply(
            lambda g: g["weighted"].sum() / g["recency_w"].sum()
        )
        return grouped.sort_index()

    def get_latest_score(self, ticker: str, days: int = 7) -> dict:
        """
        Single-call method used by the risk report.
        Returns a dict with the latest sentiment score and metadata.
        """
        series = self.get_daily_sentiment(ticker, days=days)

        if series.empty:
            return {
                "score": 0.0,
                "label": "NEUTRAL",
                "articles_analyzed": 0,
                "data_available": False,
            }

        latest_score = float(series.iloc[-1])
        n_articles   = len(self._fetch_news(ticker, days=days))

        if latest_score >  0.05: label = "POSITIVE"
        elif latest_score < -0.05: label = "NEGATIVE"
        else:                       label = "NEUTRAL"

        return {
            "score":             round(latest_score, 4),
            "label":             label,
            "articles_analyzed": n_articles,
            "data_available":    True,
            "series":            series,   # full time series, used by forecast_risk
        }


# ──────────────────────────────────────────────
# THIN SERVICE WRAPPER  (called from risk_service)
# ──────────────────────────────────────────────

class SentimentService:
    """
    Thin wrapper so risk_service.py imports one clean object.
    Uses the singleton engine so models load only once at startup.
    """

    def __init__(self):
        # Lazy-load on first call — don't block startup
        self._engine = None

    def _get_engine(self) -> NewsSentimentEngine:
        if self._engine is None:
            self._engine = NewsSentimentEngine.get_instance()
        return self._engine

    def get_sentiment_features(self, ticker: str, days: int = 30) -> dict:
        """
        Called by risk_service.full_analysis().
        Returns everything the forecast_risk and report builder need.
        """
        try:
            return self._get_engine().get_latest_score(ticker, days=days)
        except Exception as e:
            print(f"[SentimentService] Failed for {ticker}: {e}")
            return {
                "score":             0.0,
                "label":             "NEUTRAL",
                "articles_analyzed": 0,
                "data_available":    False,
            }