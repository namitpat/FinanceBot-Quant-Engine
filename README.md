# FinanceBot — Quantitative Risk Engine 📈🤖

An autonomous, institutional-grade quantitative AI agent built with **LangGraph**, **PyTorch**, and **Llama-3**. 

FinanceBot bridges the gap between conversational AI and rigorous financial mathematics. Unlike standard financial chatbots that merely summarize text, this system autonomously orchestrates a deterministic Python backend to execute deep learning time-series forecasts, Monte Carlo capital survival simulations, and dynamic portfolio covariance analyses.

![FinanceBot UI Screenshot](docs/screenshot.png) *(Note: Add a screenshot of your Streamlit UI and link it here!)*

## 🧠 System Architecture

The project utilizes a strict ReAct (Reasoning and Acting) agentic workflow to prevent LLM hallucinations, ensuring all mathematical outputs are hardcoded and deterministically calculated by the backend before being presented to the user.

* **Agent Framework:** LangGraph / LangChain
* **LLM Engine:** Llama-3.3-70B (via Groq API for ultra-low latency)
* **Forecasting Engine:** PyTorch Temporal Fusion Transformer (TFT)
* **Market Data Feeds:** `yfinance`
* **Frontend:** Streamlit (Custom CSS "Terminal" aesthetic)

## 🚀 Key Features

* **🔮 Deep Learning Forecasting (TFT):** Integrates a pre-trained PyTorch Temporal Fusion Transformer to predict next-day asset prices and directional movements based on a 1-year historical lookback.
* **🛡️ Institutional Trade Risk Analysis:** Calculates precise Value at Risk (VaR), Expected Shortfall (CVaR), and outputs exact position sizing based on user-defined stop losses and account sizes to maintain strict risk-to-reward (R:R) ratios.
* **🎲 Monte Carlo Capital Simulation:** Runs 300 independent paths of 50 sequential trades using historical return distributions to output localized "Risk of Ruin" and Maximum Drawdown estimates.
* **📊 Portfolio Aggregation:** Computes covariance matrices across user holdings to determine annualized volatility bands (68% and 95% Confidence Intervals) and exact mathematical diversification benefits.
* **📉 Dynamic Regime Detection:** Evaluates daily return dispersion to classify market regimes (High Volatility, Low Volatility, Normal) and dynamically adjusts recommended risk allocations.
* **🎓 Financial Educator Mode:** Gracefully handles non-ticker theory questions (e.g., "What is CVaR?") bypassing quantitative tools to provide textbook-quality theoretical explanations.

## 💻 Installation & Setup

**1. Clone the repository**
```bash
git clone [https://github.com/](https://github.com/)[Your-Username]/FinanceBot-Quant-Engine.git
cd FinanceBot-Quant-Engine
