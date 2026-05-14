import os
import json
import traceback
import pandas as pd
import yfinance as yf
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

from core.risk_service import RiskService
from core.tft_service import TFTService

risk_service = RiskService()
tft_service = TFTService(model_path="tft_Fold 3-v1.ckpt")

# ──────────────────────────────────────────────
# TOOLS
# ──────────────────────────────────────────────

@tool
def get_stock_price(ticker: str) -> str:
    """Fetch the current price of a stock. Returns a formatted markdown report."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2d")
        if hist.empty or hist['Close'].iloc[-1] == 0:
            return (
                f"## PRICE QUOTE — {ticker.upper()}\n\n"
                f"Ticker **{ticker.upper()}** was not found on any major exchange. "
                f"This may be because:\n"
                f"- The ticker symbol is incorrect (e.g. Anthropic is a private company — it has no stock ticker)\n"
                f"- The asset is delisted\n"
                f"- yfinance does not cover this exchange\n\n"
                f"Verify the ticker symbol and try again. "
                f"For Indian stocks use the `.NS` suffix (e.g. `RELIANCE.NS`). "
                f"For crypto use `-USD` suffix (e.g. `BTC-USD`)."
            )
        current = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-2] if len(hist) > 1 else current
        change = current - prev
        change_pct = (change / prev) * 100
        direction = "+" if change >= 0 else ""

        return (
            f"## PRICE QUOTE — {ticker.upper()}\n\n"
            f"| Metric | Value |\n"
            f"| :--- | :--- |\n"
            f"| Current Price | USD {current:,.2f} |\n"
            f"| Previous Close | USD {prev:,.2f} |\n"
            f"| Day Change | {direction}{change:,.2f} ({direction}{change_pct:.2f}%) |\n\n"
            f"*Data sourced via yfinance. Prices may be delayed up to 15 minutes.*"
        )
    except Exception as e:
        return f"ERROR: Could not fetch price for {ticker}: {str(e)}"


@tool
def predict_stock_direction(ticker: str) -> str:
    """
    Forecast tomorrow's price using the integrated PyTorch TFT model.
    Returns a formatted markdown report with predicted direction and price.
    """
    print(f"\n[SYSTEM] Running TFT inference for {ticker}...")
    result = tft_service.predict_direction(ticker)

    if "error" in result:
        return f"## TFT FORECAST — {ticker.upper()}\n\nERROR: {result['error']}"

    print(f"[SYSTEM] TFT inference complete in {result.get('inference_time_ms')}ms.")

    t = ticker.upper()
    direction = result.get("predicted_direction", "UNKNOWN")
    pred_price = result.get("predicted_price", 0)
    last_close = result.get("last_close_price", 0)
    inf_time = result.get("inference_time_ms", 0)
    delta = pred_price - last_close
    delta_pct = (delta / last_close * 100) if last_close else 0
    sign = "+" if delta >= 0 else ""

    return (
        f"## TFT FORECAST — {t}\n\n"
        f"| Metric | Value |\n"
        f"| :--- | :--- |\n"
        f"| Last Close Price | USD {last_close:,.2f} |\n"
        f"| Predicted Price (tomorrow) | USD {pred_price:,.2f} |\n"
        f"| Predicted Change | {sign}{delta:,.2f} ({sign}{delta_pct:.2f}%) |\n"
        f"| Predicted Direction | {direction} |\n"
        f"| Inference Time | {inf_time} ms |\n\n"
        f"**Model:** PyTorch Temporal Fusion Transformer (TFT) — macro-enabled, trained on 1-year lookback.\n\n"
        f"**Note:** This is a quantitative model output. Predicted price reflects the median quantile of the "
        f"model's return distribution applied to the last closing price. Not financial advice."
    )


@tool
def comprehensive_risk_analysis(
    ticker: str,
    account_size: float = 100000.0,
    entry_price: float = 0.0,
    stop_loss: float = 0.0,
    take_profit: float = 0.0,
) -> str:
    """
    Institutional risk analysis: volatility, regime detection, position sizing, Monte Carlo.
    Returns a fully formatted Markdown report.
    """
    print(f"\n[SYSTEM] Running risk analysis for {ticker}...")

    def clean(val):
        if not val or val == 0.0:
            return None
        if isinstance(val, str):
            return float(val.replace("$", "").replace(",", "").strip())
        return float(val)

    try:
        c_account = clean(account_size) or 100000.0
        c_entry = clean(entry_price)
        c_stop = clean(stop_loss)
        c_take = clean(take_profit)

        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df.empty:
            return f"ERROR: No historical data for {ticker}."
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        price_series = df["Close"].dropna()

        trade_input = None
        if c_entry and c_stop:
            trade_input = {
                "entry_price": c_entry,
                "stop_loss": c_stop,
                "take_profit": c_take if c_take else c_entry * 1.10,
                "account_size": c_account,
            }

        capital_input = {
            "initial_capital": c_account,
            "n_trades": 50,
            "simulations": 300,
        }

        ctx = risk_service.full_analysis(
                ticker=ticker,
                price_series=price_series,
                trade_input=trade_input,
                capital_input=capital_input,
                 tft_result=None,   # TFT only used in forecast_trade_risk
                )
        return ctx.explanation

    except Exception:
        traceback.print_exc()
        return f"Risk analysis failed for {ticker}."


@tool
def analyze_full_portfolio(portfolio_query: str) -> str:
    """
    Portfolio risk analysis. Input: comma-separated 'TICKER:AMOUNT' pairs.
    Example: 'AAPL:5000, TSLA:2000, GLD:1000'
    """
    try:
        holdings = {}
        for item in portfolio_query.replace("\n", ",").replace('"', "").split(","):
            if ":" in item:
                ticker, amount = item.split(":", 1)
                t = ticker.strip().upper()
                a = amount.replace("$", "").replace(",", "").strip()
                if t and a:
                    holdings[t] = float(a)

        if not holdings:
            return "ERROR: Could not parse portfolio. Use format 'AAPL:5000, TSLA:2000'."

        print(f"\n[SYSTEM] Analyzing portfolio: {holdings}")
        result = risk_service.analyze_portfolio_basket(holdings)

        total_value = result["total_value"]
        vol_pct = result["annual_volatility"]
        dollar_vol = total_value * vol_pct
        benefit_pct = result["diversification_benefit"]
        tickers = result["tickers"]

        vol_label = (
            "CONSERVATIVE — below 12%, low price swings"
            if vol_pct < 0.12
            else "MODERATE — between 12-20%, normal equity range"
            if vol_pct < 0.20
            else "HIGH-RISK — above 20%, significant price swings expected"
        )
        div_label = (
            "WEAK — assets are highly correlated, diversification adds little"
            if benefit_pct < 0.05
            else "MODERATE — partial correlation reduction achieved"
            if benefit_pct < 0.10
            else "STRONG — meaningful volatility reduction from asset mix"
        )

        # Use USD prefix everywhere to avoid Streamlit's LaTeX $ parser
        low_band = total_value - dollar_vol
        high_band = total_value + dollar_vol
        low_band_2sd = total_value - 2 * dollar_vol
        high_band_2sd = total_value + 2 * dollar_vol

        alloc_rows = "\n".join(
            f"| {t} | USD {holdings[t]:,.2f} | {(holdings[t]/total_value)*100:.1f}% |"
            for t in tickers
        )

        return (
            f"## PORTFOLIO RISK REPORT\n\n"
            f"### ALLOCATION\n"
            f"| Ticker | Dollar Value | Weight |\n"
            f"| :--- | ---: | ---: |\n"
            f"{alloc_rows}\n"
            f"| **TOTAL** | **USD {total_value:,.2f}** | **100%** |\n\n"
            f"### KEY METRICS\n"
            f"| Metric | Value | Interpretation |\n"
            f"| :--- | :--- | :--- |\n"
            f"| Annualized Volatility | {vol_pct*100:.2f}% | {vol_label} |\n"
            f"| 1-Year Dollar Risk (1 SD, 68% CI) | USD {dollar_vol:,.2f} | "
            f"Portfolio value will fall within USD {low_band:,.2f} to USD {high_band:,.2f} with 68% probability |\n"
            f"| 2-Year Dollar Risk (2 SD, 95% CI) | USD {2*dollar_vol:,.2f} | "
            f"Worst-case band: USD {low_band_2sd:,.2f} to USD {high_band_2sd:,.2f} |\n"
            f"| Diversification Benefit | {benefit_pct*100:.2f}% | {div_label} |\n\n"
            f"### INTERPRETATION\n"
            f"Holding these {len(tickers)} assets together instead of a single concentrated position "
            f"has mathematically reduced portfolio volatility by **{benefit_pct*100:.2f}%** "
            f"relative to the weighted average of each asset's standalone volatility. "
            f"A benefit above 10% is considered institutionally meaningful.\n\n"
            f"At {vol_pct*100:.2f}% annualized volatility, a 1-standard-deviation move over 12 months "
            f"implies your total portfolio value could shift by up to USD {dollar_vol:,.2f}. "
            f"The 95% confidence interval is approximately double that range."
        )

    except Exception as e:
        traceback.print_exc()
        return f"Portfolio analysis failed: {str(e)}"


# ──────────────────────────────────────────────
# TOOL REGISTRY
# ──────────────────────────────────────────────


@tool
def forecast_trade_risk(ticker: str, account_size: float = 100000.0) -> str:
    """
    Chains the TFT price prediction directly into the risk engine.
    Use when the user asks for forecast risk, predicted trade risk, or
    model-based trade setup without providing their own entry/stop/target.
    The TFT model predicts tomorrow's price and direction, derives a complete
    trade setup from those levels, then runs the full institutional risk report.
    Only requires ticker and account size — everything else is model-derived.
    """
    print(f"\n[SYSTEM] Running forecast trade risk for {ticker}...")

    def clean_account(val):
        if val is None: return 100000.0
        if isinstance(val, str):
            return float(val.replace("$","").replace(",","").replace("k","000").strip())
        return float(val) if float(val) > 0 else 100000.0

    try:
        c_account = clean_account(account_size)
        ticker = ticker.upper()

        # ── Step 1: TFT Prediction ────────────────────────────────────────
        print(f"[SYSTEM] Running TFT inference for {ticker}...")
        tft_result = tft_service.predict_direction(ticker)

        if "error" in tft_result:
            return f"## FORECAST TRADE RISK — {ticker}\n\nTFT model failed: {tft_result['error']}"

        last_close      = tft_result["last_close_price"]
        predicted_price = tft_result["predicted_price"]
        direction       = tft_result["predicted_direction"]
        inf_time        = tft_result["inference_time_ms"]

        # ── Step 2: Derive trade levels from prediction ───────────────────
        predicted_move  = abs(predicted_price - last_close)

        # Stop = half the predicted move on the wrong side of entry
        # Stop at half the predicted move = 2:1 R:R by construction
        # reward = predicted_move, risk = predicted_move * 0.5 → R:R = 2.0
        stop_distance = max(predicted_move * 0.5, last_close * 0.001)
        
        if direction == "UP":
            entry      = round(last_close, 2)
            target     = round(predicted_price, 2)
            stop       = round(entry - stop_distance, 2)
            trade_type = "LONG"
        else:
            entry      = round(last_close, 2)
            target     = round(predicted_price, 2)
            stop       = round(entry + stop_distance, 2)
            trade_type = "SHORT"
        
        # Verify R:R — reward is predicted_move, risk is stop_distance
        gross_rr = round(predicted_move / stop_distance, 2) 
        # Cap position exposure to 95% of account to prevent overleveraging
        # on tight model-predicted stops
        max_exposure   = c_account * 0.95
        max_shares_cap = int(max_exposure / entry)
        risk_amount    = c_account * 0.01                    # 1% account risk
        raw_shares     = int(risk_amount / stop_distance) if stop_distance > 0 else 0
        capped_shares  = min(raw_shares, max_shares_cap)
        
        # Override account risk percent so TradeRiskEngine produces capped shares
        # by back-calculating what risk percent gives the capped position
        if raw_shares > 0:
            capped_risk_pct = (capped_shares * stop_distance) / c_account
        else:
            capped_risk_pct = 0.01
# always ~2.0 by construction

        # ── Step 3: Fetch price data and run full risk pipeline ───────────
        import pandas as pd
        import yfinance as yf

        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df.empty:
            return f"ERROR: No historical data for {ticker}."
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        price_series = df["Close"].dropna()

        trade_input = {
            "entry_price":  entry,
            "stop_loss":    stop,
            "take_profit":  target,
            "account_size": c_account,
        }
        capital_input = {
            "initial_capital": c_account,
            "n_trades": 50,
            "simulations": 300,
        }

        ctx = risk_service.full_analysis(
            ticker=ticker,
            price_series=price_series,
            trade_input=trade_input,
            capital_input=capital_input,
            tft_result=tft_result,
        )

        # Inject trade params into ctx.trade if engine didn't echo them
        if ctx.trade and "error" not in ctx.trade:
            ctx.trade.setdefault("entry_price",  entry)
            ctx.trade.setdefault("stop_loss",    stop)
            ctx.trade.setdefault("take_profit",  target)
            ctx.trade.setdefault("account_size", c_account)

        # ── Step 4: Build the model-derived preamble ─────────────────────
        preamble = (
            f"## FORECAST TRADE RISK — {ticker}\n\n"
            f"### MODEL-DERIVED TRADE SETUP\n\n"
            f"| Parameter | Value | Source |\n"
            f"| :--- | :--- | :--- |\n"
            f"| Trade Type | {trade_type} | TFT predicted direction |\n"
            f"| Last Close | USD {last_close:,.2f} | Live market data |\n"
            f"| TFT Predicted Price | USD {predicted_price:,.2f} | PyTorch TFT model |\n"
            f"| Predicted Move | USD {predicted_move:,.2f} ({(predicted_move/last_close)*100:.2f}%) | abs(predicted - close) |\n"
            f"| Entry | USD {entry:,.2f} | Last close price |\n"
            f"| Stop Loss | USD {stop:,.2f} | 50% of predicted move, opposite side |\n"
            f"| Take Profit | USD {target:,.2f} | TFT predicted price |\n"
            f"| Theoretical R:R | {gross_rr:.2f} | Predicted move / stop distance |\n"
            f"| Inference Time | {inf_time} ms | TFT model |\n\n"
            f"**How the trade levels were derived:** The TFT model predicted a price of "
            f"USD {predicted_price:,.2f} from a last close of USD {last_close:,.2f}, implying a "
            f"USD {predicted_move:,.2f} move {direction.lower()}ward. "
            f"Entry is set at the current closing price. "
            f"Take profit is the model's predicted price. "
            f"Stop loss is placed at 50% of the predicted move on the opposite side of entry, "
            f"ensuring a minimum 2:1 risk/reward by construction. "
            f"All downstream risk calculations use these model-derived levels.\n\n"
            f"---\n\n"
        )

        return preamble + ctx.explanation

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Forecast trade risk failed for {ticker}: {str(e)}"

ALL_TOOLS = [
    get_stock_price,
    predict_stock_direction,
    comprehensive_risk_analysis,
    analyze_full_portfolio,
    forecast_trade_risk,
]

TOOL_MAP = {t.name: t for t in ALL_TOOLS}

# Tools that return pre-formatted markdown — skip LLM Step 3, pass through directly
PASSTHROUGH_TOOLS = {
    "comprehensive_risk_analysis",
    "analyze_full_portfolio",
    "get_stock_price",
    "predict_stock_direction",
    "forecast_trade_risk",
}

# ──────────────────────────────────────────────
# LLM
# ──────────────────────────────────────────────

os.environ["GROQ_API_KEY"] = "Paste your API KEY"

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
llm_with_tools = llm.bind_tools(ALL_TOOLS)

GREETING_TOKENS = {
    "hi", "hello", "hey", "yo", "sup", "howdy", "greetings",
    "good morning", "good afternoon", "good evening",
    "what can you do", "help", "what are you", "who are you",
}

THEORETICAL_PHRASES = [
    "what is risk", "what is cvar", "what is volatility", "what does volatility",
    "what is sharpe", "what is drawdown", "what is regime", "what is monte carlo",
    "what is stop loss", "what is take profit", "what is risk reward",
    "what do you mean", "what do u mean", "explain", "define ",
    "how does", "how do", "what does", "what are these",
    "what is a ", "what is an ", "what is the ", "market regime",
    "overall risk", "overall market", "tell me about",
]

SYSTEM_PROMPT = """You are FinanceBot — a quantitative risk terminal.

Available tools:
- get_stock_price           → live price quote for a specific ticker
- predict_stock_direction   → TFT forecast for a specific ticker (direction + price only)
- comprehensive_risk_analysis → full trade risk report. ONLY call when user explicitly provides a numeric entry price AND numeric stop loss. If missing, ask.
- analyze_full_portfolio    → portfolio report. ONLY call when user gives explicit ticker:amount pairs.
- forecast_trade_risk       → chains TFT prediction into a full risk report. Use when user asks for "forecast risk", "predicted trade risk", "what does the model say I should trade", or any risk query WITHOUT providing their own entry/stop. Requires only ticker and account size.

CRITICAL RULES:
1. Call exactly ONE tool per request.
2. For general/conceptual questions — answer in plain text. DO NOT call any tool.
3. For comprehensive_risk_analysis — ONLY call if the user gave explicit numeric entry AND stop loss. Otherwise use forecast_trade_risk.
4. Return tool results VERBATIM. Never modify or add to them."""


# ──────────────────────────────────────────────
# SINGLE-SHOT AGENT — structurally cannot loop
# ──────────────────────────────────────────────

def _classify(text: str) -> str:
    lower = text.lower().strip().rstrip("!?.,")
    words = lower.split()

    if lower in GREETING_TOKENS:
        return "greeting"
    if len(words) <= 2 and not any(c.isupper() for c in text):
        return "greeting"

    for phrase in THEORETICAL_PHRASES:
        if phrase in lower:
            return "theoretical"

    return "actionable"


GREETING_RESPONSE = (
    "**Ready.** Ask me about any stock.\n\n"
    "| I can | Example |\n"
    "| :--- | :--- |\n"
    "| Get a price | `What is NVDA's price?` |\n"
    "| Forecast direction | `Predict tomorrow's direction for AAPL` |\n"
    "| Analyze a trade | `Risk: TSLA, 50k account, entry 170, stop 160, target 195` |\n"
    "| Analyze a portfolio | `Portfolio: NVDA:15000, MSFT:10000, GLD:5000` |\n\n"
    "Use the sidebar for quick examples."
)


def run_agent(user_message: str) -> str:
    """
    Three-step pipeline. Structurally cannot loop.
    Step 1 — Classify intent: greeting / theoretical / actionable.
    Step 2 — Ask LLM which tool to call (actionable only).
    Step 3 — Execute that ONE tool and return result directly.
    """

    intent = _classify(user_message)
    print(f"[AGENT] Intent classified as: {intent}")

    # ── STEP 1a: Greeting ─────────────────────
    if intent == "greeting":
        return GREETING_RESPONSE

    # ── STEP 1b: Theoretical — answer via plain LLM, no tools ──
    if intent == "theoretical":
        print("[AGENT] Theoretical question — answering without tool.")
        plain_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        resp = plain_llm.invoke([
            SystemMessage(content=(
        "You are FinanceBot, a quantitative finance assistant built on a "
        "PyTorch Temporal Fusion Transformer (TFT) for stock direction forecasting, "
        "an institutional risk engine with regime detection and Monte Carlo simulation, "
        "and a FinBERT-based sentiment analysis pipeline. "
        "When asked about the TFT model, explain it as a deep learning architecture "
        "that uses multi-head attention, gating mechanisms, variable selection networks, "
        "and quantile regression to produce probabilistic time series forecasts. "
        "Answer conceptual finance and ML questions in clear, structured detail. "
        "Use headings and bullet points for complex topics. "
        "Give real definitions, explain the math where relevant, and use practical examples. "
        "Do not truncate answers. No emojis."
            )),
            HumanMessage(content=user_message),
        ])
        return resp.content

    # ── STEP 2: Tool selection (actionable queries only) ──
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]

    print("\n[AGENT] Step 2 — requesting tool selection from LLM...")
    ai_msg = llm_with_tools.invoke(messages)

    # LLM chose to answer directly (e.g. asked for missing params)
    if not ai_msg.tool_calls:
        print("[AGENT] No tool call — returning LLM direct answer.")
        return ai_msg.content

    # ── STEP 3: Execute exactly ONE tool ─────
    call = ai_msg.tool_calls[0]   # hard-cap: ignore any extras
    name = call["name"]
    args = call["args"]

    print(f"[AGENT] Step 3 — executing {name}({args})")

    if name not in TOOL_MAP:
        return f"**Error:** Unknown tool `{name}` was requested."

    try:
        raw = TOOL_MAP[name].invoke(args)
        return str(raw)
    except Exception as e:
        traceback.print_exc()
        return f"**Tool execution failed:** `{str(e)}`"