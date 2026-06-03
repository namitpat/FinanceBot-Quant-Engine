# test_sentiment.py
import sys
sys.path.insert(0, ".")

print("Testing SentimentService...")
from core.sentiment_service import SentimentService

svc = SentimentService()

# First call will take 60-90 seconds — FinBERT + DeBERTa downloading
print("\nFetching sentiment for TSLA (this will be slow first time)...")
result = svc.get_sentiment_features("TSLA", days=7)

print(f"\nScore:     {result['score']}")
print(f"Label:     {result['label']}")
print(f"Articles:  {result['articles_analyzed']}")
print(f"Available: {result['data_available']}")