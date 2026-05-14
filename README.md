# QuantSentinel — AI Financial Intelligence System

> Quantitative finance terminal built on a PyTorch Temporal Fusion Transformer, institutional risk pipeline, and FinBERT-powered sentiment analysis.

---

## Demo

[![QuantSentinel Demo](https://img.youtube.com/vi/oAjEuWgfQ4E/maxresdefault.jpg)](https://www.youtube.com/watch?v=oAjEuWgfQ4E)

Click the image above to watch the full demo video.


> To embed directly: upload the video to YouTube, then replace the badge link above with:
> `[![Demo](https://img.youtube.com/vi/YOUR_VIDEO_ID/0.jpg)](https://www.youtube.com/watch?v=YOUR_VIDEO_ID)`

---

## What it does

| Query | What you get |
|:---|:---|
| `What is NVDA's price?` | Live price, previous close, day change |
| `Predict tomorrow's direction for TSLA` | TFT model forecast — direction + predicted price |
| `Forecast trade risk for MSFT with a $100k account` | Model-derived trade setup + full risk report |
| `Risk: TSLA, $50k, entry $170, stop $160, target $195` | Manual trade risk with sentiment context |
| `Portfolio: NVDA:15000, MSFT:10000, GLD:5000` | Volatility, diversification benefit, dollar risk bands |
| `What is CVaR?` | Plain-language finance explanation |

---

## Architecture

```
User Query (Streamlit UI)
        |
   _classify() ── greeting/theoretical ── plain LLM response
        |
   actionable
        |
   LLM selects one tool (single-shot, cannot loop)
        |
   ┌──────────────────────────────────────────────────┐
   │  get_stock_price          →  yfinance live        │
   │  predict_stock_direction  →  PyTorch TFT model    │
   │  forecast_trade_risk      →  TFT + RiskService    │
   │  comprehensive_risk_analysis → RiskService        │
   │  analyze_full_portfolio   →  PortfolioRisk        │
   └──────────────────────────────────────────────────┘
        |
   Formatted Markdown report returned directly to chat
```

The agent replaces LangGraph's `create_react_agent` with a structurally loop-free three-step pipeline — intent classification, single tool selection, direct result passthrough. No LLM reformatting step, no hallucination, no token waste.

---

## Risk Report Structure

Every trade query generates a 6-section institutional report:

| Section | Content |
|:---|:---|
| 1 — Asset Risk Profile | Daily volatility, annualized vol, CVaR, risk score |
| 2 — Sentiment & Forecast Alignment | FinBERT + RoBERTa + VADER ensemble on 30 days of news, aligned against TFT direction |
| 3 — Market Regime | Regime detection (high/normal/low vol), adaptive risk allocation |
| 4 — Trade Architecture | Position size, exposure, dollar risk/reward, R:R ratio |
| 5 — Monte Carlo Simulation | 300-path capital simulation, survival rate, max drawdown, ruin probability |
| 6 — Recommendation | Composite risk score (40% vol + 20% forecast + 10% capital) |

---

## Tech Stack

| Layer | Technology |
|:---|:---|
| Forecasting | PyTorch, pytorch-forecasting (TFT) |
| Sentiment | ProsusAI/FinBERT, cardiffnlp/RoBERTa, VADER |
| News data | Finnhub API |
| Market data | yfinance |
| LLM | Llama 3.3 70B via Groq |
| Agent | LangChain (tool binding) |
| UI | Streamlit |
| Risk engine | NumPy, Pandas, SciPy |

---

## Setup

**Requirements:** Python 3.10+, CUDA GPU recommended

```bash
git clone https://github.com/namitpatel3006/QuantSentinel
cd QuantSentinel

conda create -n tft_env python=3.10
conda activate tft_env
pip install -r requirements.txt
```

Create a `.env` file or set environment variables:

```bash
# Windows
set GROQ_API_KEY=your_key_here

# Linux / macOS
export GROQ_API_KEY=your_key_here
```

The TFT model checkpoint (`tft_Fold 3-v1.ckpt`) is too large for GitHub. Download it from:
**[Google Drive / HuggingFace link here]** and place it in the project root.

```bash
python -m streamlit run app.py
```

---

## Project Structure

```
.
├── app.py                    # Streamlit UI
├── agent.py                  # Single-shot agent + tool definitions
├── requirements.txt
└── core/
    ├── tft_service.py        # TFT inference pipeline
    ├── risk_service.py       # Full risk analysis orchestrator
    ├── sentiment_service.py  # FinBERT + RoBERTa + VADER ensemble
    ├── forecast_risk.py      # TFT + sentiment alignment scoring
    ├── risk_sentinel.py      # Volatility and CVaR
    ├── regime_engine.py      # Market regime detection
    ├── trade_risk.py         # Position sizing and R:R
    ├── capital_simulator.py  # Monte Carlo simulation
    ├── portfolio.py          # Portfolio volatility
    └── context.py            # RiskContext dataclass
```

---

## Limitations

- TFT predicts next-day direction only. Multi-step forecasting is not yet implemented.
- Monte Carlo uses historical return distributions, not trade-specific stop/target simulation.
- Groq free tier: 100k tokens/day. Heavy usage will hit this limit.
- yfinance data may be delayed up to 15 minutes during market hours.
- Finnhub free tier: 60 API calls/minute.

---

## Authors

**Namit Patel** — TFT model, risk pipeline, agent architecture, Streamlit UI
**Dhruv** — Sentiment analysis engine (FinBERT + DeBERTa + VADER ensemble)

Sardar Patel Institute of Technology, Mumbai — B.E. Computer Engineering, 2026
