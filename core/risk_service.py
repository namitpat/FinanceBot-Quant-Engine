# # core/risk_service.py

# import numpy as np
# import pandas as pd
# import yfinance as yf

# from core.risk_sentinel import RiskSentinel
# from core.portfolio import PortfolioRisk
# from core.trade_risk import TradeRiskEngine
# from core.recommender import RecommendationEngine
# from core.explainer import RiskExplainer
# from core.forecast_risk import ForecastRiskEngine
# from core.regime_engine import RegimeEngine
# from core.risk_decomposition import RiskDecomposition
# from core.capital_simulator import CapitalSimulator
# from core.context import RiskContext
# from core.sentiment_service import SentimentService


# class RiskService:
#     def __init__(self):
#         self.asset_engine = RiskSentinel()
#         self.portfolio_engine = PortfolioRisk()
#         self.trade_engine = TradeRiskEngine()
#         self.recommender = RecommendationEngine()
#         self.explainer = RiskExplainer()
#         self.forecast_engine = ForecastRiskEngine()
#         self.regime_engine = RegimeEngine()
#         self.decomposition_engine = RiskDecomposition()
#         self.capital_simulator = CapitalSimulator()
#         self.sentiment_service = SentimentService()

#     # ────────────────────────────────────────────
#     # Portfolio Basket Analysis
#     # ────────────────────────────────────────────
#     def analyze_portfolio_basket(self, holdings: dict):
#         """
#         holdings: {"AAPL": 5000, "TSLA": 3000, "GLD": 2000}
#         """
#         tickers = list(holdings.keys())

#         data = yf.download(tickers, period="1y", progress=False)['Close']
#         if isinstance(data, pd.Series):
#             data = data.to_frame(name=tickers[0])

#         returns = data.pct_change().dropna()

#         total_value = sum(holdings.values())
#         weights = np.array([holdings[t] / total_value for t in tickers])

#         cov_matrix = returns.cov() * 252
#         portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
#         portfolio_volatility = np.sqrt(portfolio_variance)

#         individual_vols = [returns[t].std() * np.sqrt(252) for t in tickers]
#         weighted_avg_vol = sum(v * w for v, w in zip(individual_vols, weights))
#         benefit = (weighted_avg_vol - portfolio_volatility) / (weighted_avg_vol + 1e-8)

#         return {
#             "total_value": total_value,
#             "annual_volatility": float(portfolio_volatility),
#             "diversification_benefit": float(benefit),
#             "tickers": tickers,
#         }

#     # ────────────────────────────────────────────
#     # Asset Risk
#     # ────────────────────────────────────────────
#     def evaluate_asset(self, ticker, price_series):
#         metrics = self.asset_engine.assess_asset(price_series)
#         recommendation = self.recommender.recommend_asset(metrics)
#         explanation = self.explainer.explain_asset(ticker, metrics)
#         return {"metrics": metrics, "recommendation": recommendation, "explanation": explanation}

#     # ────────────────────────────────────────────
#     # Trade Risk (basic)
#     # ────────────────────────────────────────────
#     def evaluate_trade(self, **kwargs):
#         metrics = self.trade_engine.calculate_trade(**kwargs)
#         recommendation = self.recommender.recommend_trade(metrics)
#         explanation = self.explainer.explain_trade(metrics)
#         return {"metrics": metrics, "recommendation": recommendation, "explanation": explanation}

#     # ────────────────────────────────────────────
#     # Trade Risk (regime-aware)
#     # ────────────────────────────────────────────
#     def evaluate_trade_with_context(self, price_series, **kwargs):
#         regime = self.evaluate_regime(price_series)
#         adjusted_risk = self.regime_engine.adaptive_risk_percent(regime["regime"])
#         kwargs["risk_percent"] = adjusted_risk
#         metrics = self.trade_engine.calculate_trade(**kwargs)
#         explanation = (
#             self.explainer.explain_trade(metrics)
#             + f"\n\nMarket Regime: {regime['regime']}"
#             + f"\nAdjusted Risk %: {adjusted_risk * 100:.2f}%"
#         )
#         return {
#             "metrics": metrics,
#             "regime": regime,
#             "adjusted_risk_percent": adjusted_risk,
#             "explanation": explanation,
#         }

#     # ────────────────────────────────────────────
#     # Regime
#     # ────────────────────────────────────────────
#     def evaluate_regime(self, price_series):
#         returns = self.asset_engine.compute_log_returns(price_series)
#         return self.regime_engine.detect_regime(returns)

#     # ────────────────────────────────────────────
#     # Risk Contribution
#     # ────────────────────────────────────────────
#     def evaluate_risk_contribution(self, price_dict, weights):
#         return self.decomposition_engine.compute_marginal_risk_contribution(price_dict, weights)

#     # ────────────────────────────────────────────
#     # Capital Survival
#     # ────────────────────────────────────────────
#     def evaluate_capital_survival(self, price_series, initial_capital=100000):
#         returns = self.asset_engine.compute_log_returns(price_series).dropna()
#         if len(returns) < 20:
#             return {"ruin_probability": 0.0, "median_final_capital": initial_capital}
#         vol = returns.std()
#         regime_info = self.regime_engine.detect_regime(returns)
#         regime = regime_info["regime"]
#         win_rate = max(0.3, min(0.7, 0.6 - vol))
#         reward_risk_ratio = {"high_vol": 1.5, "low_vol": 2.5}.get(regime, 2.0)
#         results = self.capital_simulator.simulate_with_context(
#             ctx=None,
#             initial_capital=initial_capital,
#             returns=returns,
#             n_sim=300,
#             n_trades=100,
#         )
#         results["derived_win_rate"] = win_rate
#         results["regime"] = regime
#         results["volatility"] = float(vol)
#         return results

#     # ────────────────────────────────────────────
#     # FULL PIPELINE
#     # ────────────────────────────────────────────
#     def full_analysis(
#         self,
#         ticker,
#         price_series,
#         predicted_prices=None,
#         trade_input=None,
#         capital_input=None,
#         tft_result=None,      # dict from tft_service.predict_direction()
#     ):
#         ctx = RiskContext(ticker)
#         ctx.price_series = price_series
#         ctx.predicted_prices = predicted_prices

#         # 1. Asset Risk
#         ctx.asset_metrics = self.asset_engine.assess_asset(price_series)

#         # 2. Regime Detection
#         returns = self.asset_engine.compute_log_returns(price_series).dropna()
#         ctx.regime = self.regime_engine.detect_regime(returns)

#         # 3. Adaptive Risk
#         ctx.adjusted_risk_percent = self.regime_engine.adaptive_risk_percent(
#             ctx.regime["regime"]
#         )
#         ctx.asset_metrics["regime_adjusted_risk_score"] = ctx.asset_metrics[
#             "risk_score"
#         ] * (1 + ctx.adjusted_risk_percent)

#         # 4. Sentiment Analysis
#         ctx.sentiment = self.sentiment_service.get_sentiment_features(ticker, days=30)

#         # 5. Forecast Risk (TFT + Sentiment combined)
#         ctx.forecast_risk = None
#         if tft_result and not tft_result.get("error"):
#             predicted_return = (
#                 (tft_result["predicted_price"] - tft_result["last_close_price"])
#                 / max(tft_result["last_close_price"], 1e-6)
#             )
#             ctx.forecast_risk = self.forecast_engine.compute_forecast_integrated_risk(
#                 historical_vol      = ctx.asset_metrics["volatility"],
#                 expected_shortfall  = ctx.asset_metrics["expected_shortfall"],
#                 predicted_return    = predicted_return,
#                 predicted_direction = tft_result.get("predicted_direction", "UP"),
#                 sentiment_score     = ctx.sentiment.get("score", 0.0),
#                 sentiment_label     = ctx.sentiment.get("label", "NEUTRAL"),
#             )
#         elif predicted_prices is not None:
#             # backward compat — old call path without tft_result
#             ctx.forecast_risk = self.forecast_engine.compute_forecast_integrated_risk(
#                 historical_vol      = ctx.asset_metrics["volatility"],
#                 expected_shortfall  = ctx.asset_metrics["expected_shortfall"],
#                 predicted_return    = 0.0,
#                 predicted_direction = "UP",
#                 sentiment_score     = ctx.sentiment.get("score", 0.0),
#                 sentiment_label     = ctx.sentiment.get("label", "NEUTRAL"),
#             )

#         # 6. Trade Analysis
#         # 6. Trade Analysis
#         ctx.trade = None
#         if trade_input:
#             ctx.trade = self.trade_engine.calculate_trade_with_context(
#                 ctx,
#                 entry_price=trade_input["entry_price"],
#                 stop_loss=trade_input["stop_loss"],
#                 take_profit=trade_input["take_profit"],
#                 account_size=trade_input["account_size"],
#             )
#             if ctx.trade and "error" not in ctx.trade:
#                 ctx.trade["entry_price"]  = trade_input["entry_price"]
#                 ctx.trade["stop_loss"]    = trade_input["stop_loss"]
#                 ctx.trade["take_profit"]  = trade_input["take_profit"]
#                 ctx.trade["account_size"] = trade_input["account_size"]
        
#                 # ── Exposure cap ─────────────────────────────────────────
#                 # Prevents overleveraging when stop distance is very tight
#                 # (common in model-derived trades with small predicted moves)
#                 max_exposure   = trade_input["account_size"] * 0.95
#                 entry          = trade_input["entry_price"]
#                 max_shares     = int(max_exposure / entry) if entry > 0 else 9999
        
#                 if ctx.trade["position_size"] > max_shares:
#                     original        = ctx.trade["position_size"]
#                     ctx.trade["position_size"]   = max_shares
#                     ctx.trade["total_exposure"]  = round(max_shares * entry, 2)
#                     ctx.trade["capital_risk_percent"] = round(
#                         (max_shares * ctx.trade["risk_per_share"] / trade_input["account_size"]) * 100, 2
#                     )
#                     print(f"[RISK] Position capped: {original} → {max_shares} shares (exposure limit)")
#         # 7. Capital Simulation
#         ctx.capital = None
#         if capital_input:
#             sim_returns = self.asset_engine.compute_log_returns(price_series).dropna()
#             ctx.capital = self.capital_simulator.simulate_with_context(
#                 ctx=ctx,
#                 returns=sim_returns,
#                 initial_capital=capital_input.get("initial_capital", 100000),
#                 n_trades=capital_input.get("n_trades", 50),
#                 n_sim=capital_input.get("simulations", 300),
#             )

#         # 8. Composite Risk Score
#         forecast_component = (
#             ctx.forecast_risk["forecast_integrated_risk"]
#             if ctx.forecast_risk
#             else ctx.asset_metrics["volatility"]
#         )
#         dd = ctx.capital.get("avg_drawdown", 0.5) if ctx.capital else 0.5
#         capital_component = max(0, 1 - dd)
#         ctx.summary_score = (
#             0.4 * ctx.asset_metrics["risk_score"]
#             + 0.2 * forecast_component
#             + 0.1 * capital_component
#         )

#         # 9. Risk Label
#         if ctx.summary_score < 0.05:   ctx.summary_label = "LOW RISK"
#         elif ctx.summary_score < 0.12: ctx.summary_label = "MODERATE RISK"
#         else:                           ctx.summary_label = "HIGH RISK"

#         # 10. Recommendation
#         ctx.recommendation = self.recommender.recommend_asset(ctx.asset_metrics)

#         # 11. Build Report
#         ctx.explanation = self._build_report(ctx, ticker)
#         return ctx

#     # ────────────────────────────────────────────
#     # Report Builder
#     # ────────────────────────────────────────────
#     def _build_report(self, ctx, ticker: str) -> str:
#         ticker = ticker.upper()
#         vol = ctx.asset_metrics.get("volatility", 0)
#         risk_score = ctx.asset_metrics.get("risk_score", 0)
#         es = ctx.asset_metrics.get("expected_shortfall", 0)
#         regime_name = ctx.regime.get("regime", "UNKNOWN").upper()
#         adj_risk_pct = ctx.adjusted_risk_percent * 100

#         # ── REGIME EXPLANATION ──────────────────
#         regime_explanations = {
#             "HIGH_VOL": (
#                 "HIGH VOLATILITY — The asset's recent price swings are statistically elevated. "
#                 "The regime engine has detected daily return dispersion above normal thresholds. "
#                 f"Adaptive risk allocation has been reduced to {adj_risk_pct:.1f}% of account per trade."
#             ),
#             "LOW_VOL": (
#                 "LOW VOLATILITY — The market is in a compression phase. "
#                 "Price action is tight and mean-reverting. "
#                 f"Standard allocation of {adj_risk_pct:.1f}% per trade is acceptable."
#             ),
#             "NORMAL_VOL": (
#                 "NORMAL VOLATILITY — Asset is trading within historical norms. "
#                 f"Risk allocation set to {adj_risk_pct:.1f}% of account per trade."
#             ),
#         }
#         regime_text = regime_explanations.get(
#             regime_name,
#             f"Regime: {regime_name}. Adjusted risk allocation: {adj_risk_pct:.1f}%."
#         )

#         # ── ASSET RISK SECTION ───────────────────
#         vol_annualized = vol * (252 ** 0.5)
#         es_pct = es * 100

#         lines = [
#             f"## INSTITUTIONAL RISK REPORT — {ticker}",
#             "",
#             "---",
#             "",
#             "### SECTION 1 — ASSET RISK PROFILE",
#             "",
#             f"| Metric | Raw Value | Annualized | Interpretation |",
#             f"| :--- | :--- | :--- | :--- |",
#             f"| Daily Volatility | {vol:.4f} | {vol_annualized:.4f} ({vol_annualized*100:.2f}%/yr) | {'HIGH — handle with reduced size' if vol_annualized > 0.30 else 'MODERATE — standard caution' if vol_annualized > 0.15 else 'LOW — stable asset'} |",
#             f"| Expected Shortfall (CVaR) | {es:.4f} | — | On your worst 5% of trading days, expect to lose at least {es_pct:.2f}% of the position value |",
#             f"| Risk Score (0–1) | {risk_score:.4f} | — | {'> 0.6 = High intrinsic risk' if risk_score > 0.6 else '0.3-0.6 = Moderate' if risk_score > 0.3 else '< 0.3 = Low'} |",
#             f"| Composite Risk Label | — | — | {ctx.summary_label} |",
#             "",
#             "**Daily Volatility explained:** A daily vol of {:.4f} means the asset moves roughly {:.2f}% per day on average (1 standard deviation). ".format(vol, vol * 100)
#             + "Annualized, this implies your position value could swing by {:.2f}% over a full year within normal market conditions.".format(vol_annualized * 100),
#             "",
#             "**Expected Shortfall (CVaR) explained:** This is not your average loss — it is the *expected magnitude* of loss "
#             f"conditioned on being in the worst 5% of outcomes. A CVaR of {es_pct:.2f}% means: "
#             f"in a tail-risk scenario, you should plan for losing at least {es_pct:.2f}% of the position in a single session.",
#             "",
#             "---",
#             "",
#             "### SECTION 2 — SENTIMENT AND FORECAST ALIGNMENT",
#             "",
#         ]

#         # ── SENTIMENT + FORECAST RISK BLOCK ─────
#         if ctx.forecast_risk:
#             fr = ctx.forecast_risk
#             sent_score  = fr.get("sentiment_score", 0.0)
#             sent_label  = fr.get("sentiment_label", "NEUTRAL")
#             alignment   = fr.get("signal_alignment", "NEUTRAL")
#             align_detail = fr.get("alignment_detail", "")
#             dir_conf    = fr.get("direction_confidence", "MODERATE")
#             fr_label    = fr.get("forecast_risk_label", "MODERATE")
#             fr_score    = fr.get("forecast_integrated_risk", 0.0)
#             vol_ratio   = fr.get("forecast_vol_ratio", 0.0)
#             pred_dir    = fr.get("predicted_direction", "N/A")
#             sent_adj    = fr.get("sentiment_adjustment", 1.0)
#             n_articles  = ctx.sentiment.get("articles_analyzed", 0)

#             lines += [
#                 f"| Metric | Value | Interpretation |",
#                 f"| :--- | :--- | :--- |",
#                 f"| News Sentiment | {sent_score:+.4f} ({sent_label}) | "
#                 f"{'Bullish news flow supports upward price movement' if sent_label == 'POSITIVE' else 'Bearish news flow adds downward pressure' if sent_label == 'NEGATIVE' else 'News flow is neutral — no directional pressure'} |",
#                 f"| Articles Analyzed | {n_articles} | Articles from past 30 days via Finnhub, scored by FinBERT + DeBERTa + VADER ensemble |",
#                 f"| TFT Predicted Direction | {pred_dir} | Output from the PyTorch Temporal Fusion Transformer |",
#                 f"| Signal Alignment | {alignment} | "
#                 f"{'TFT and news sentiment point in the same direction — higher confidence' if alignment == 'ALIGNED' else 'TFT and sentiment disagree — treat with caution' if alignment == 'CONFLICTING' else 'Sentiment is flat — no confirmation or contradiction'} |",
#                 f"| Forecast Vol Ratio | {vol_ratio:.2f}x | Predicted move is {vol_ratio:.2f}x the asset normal daily volatility |",
#                 f"| Direction Confidence | {dir_conf} | Based on size of predicted return relative to historical vol |",
#                 f"| Sentiment Risk Adjustment | {sent_adj:.2f}x | Applied to base CVaR risk — below 1.0 reduces risk, above 1.0 increases it |",
#                 f"| Forecast Risk Score | {fr_score:.4f} ({fr_label}) | CVaR * (1 + vol ratio) * sentiment adjustment |",
#                 "",
#                 f"**Signal alignment detail:** {align_detail}",
#                 "",
#             ]
#         else:
#             lines += [
#                 "TFT forecast not available for this query. Run a prediction first to see sentiment and forecast alignment.",
#                 "",
#             ]

#         lines += [
#             "---",
#             "",
#             "### SECTION 3 — MARKET REGIME",
#             "",
#             regime_text,
#             "",
#         ]

#         # ── TRADE SECTION ────────────────────────
#         if ctx.trade and "error" not in ctx.trade:
#             t = ctx.trade
#             rr = t.get("risk_reward_ratio", 0)
#             pos_size = t.get("position_size", 0)
#             exposure = t.get("total_exposure", 0)
#             entry = t.get("entry_price", 0)
#             stop = t.get("stop_loss", 0)
#             take = t.get("take_profit", 0)
#             dollar_risk   = abs(entry - stop) * pos_size if entry and stop and pos_size else 0
#             dollar_reward = abs(take - entry) * pos_size if take and entry and pos_size else 0

#             if rr < 1.95:
#                 rr_quality = "POOR — below the institutional minimum of 2.0"
#                 rr_action = "Do not take this trade at current levels. Widen take profit or tighten stop loss."
#             elif rr < 3:
#                 rr_quality = "ACCEPTABLE — meets minimum threshold"
#                 rr_action = "Proceed with caution. Tightening stop loss or widening take profit would improve quality."
#             else:
#                 rr_quality = "STRONG — exceeds institutional standard"
#                 rr_action = "Trade setup is structurally sound at current levels."

#             # Break-even win rate from RR
#             breakeven_wr = (1 / (1 + rr)) * 100

#             lines += [
#                 "---",
#                 "",
#                 "### SECTION 4 — TRADE ARCHITECTURE",
#                 "",
#                 "| Parameter | Value |",
#                 "| :--- | :--- |",
#                 f"| Entry Price | USD {entry:,.2f} |",
#                 f"| Stop Loss | USD {stop:,.2f} |",
#                 f"| Take Profit | USD {take:,.2f} |",
#                 f"| Position Size | {pos_size} shares |",
#                 f"| Total Exposure | USD {exposure:,.2f} |",
#                 f"| Dollar Risk (max loss) | USD {dollar_risk:,.2f} |",
#                 f"| Dollar Reward (max gain) | USD {dollar_reward:,.2f} |",
#                 f"| Risk/Reward Ratio | {rr:.2f} |",
#                 f"| Trade Quality | {rr_quality} |",
#                 "",
#                 f"**Position size explained:** The model calculated {pos_size} shares based on your account size and the "
#                 f"distance between entry (USD {entry:,.2f}) and stop loss (USD {stop:,.2f}). "
#                 f"This ensures maximum downside exposure of USD {dollar_risk:,.2f} if the stop is hit.",
#                 "",
#                 f"**Risk/Reward ({rr:.2f}) explained:** You are risking USD {dollar_risk:,.2f} to potentially make USD {dollar_reward:,.2f}. "
#                 f"With a {rr:.2f} R:R ratio, you only need to win {breakeven_wr:.1f}% of your trades to break even over a large sample. "
#                 f"{rr_action}",
#                 "",
#             ]
#             if ctx.capital:
#                 print(f"[DEBUG] capital dict keys: {ctx.capital.keys()}")
#                 print(f"[DEBUG] capital values: {ctx.capital}")

#             # ── MONTE CARLO SECTION ──────────────
#             if ctx.capital:
#                 avg_dd      = ctx.capital.get("avg_drawdown", None)
#                 median_final = ctx.capital.get("median_final_capital", None)
#                 # Derive survival and ruin from avg_drawdown
#                 # Convention: drawdown > 50% of account = ruin threshold
#                 ruin_prob = float(avg_dd) / 0.5 if avg_dd is not None else None
#                 ruin_prob = min(ruin_prob, 1.0) if ruin_prob is not None else None
#                 survival   = (1.0 - ruin_prob) if ruin_prob is not None else None
#                 n_trades = 50
#                 account = t.get("account_size", ctx.capital.get("initial_capital", 100000))

#                 # survival_rate and ruin_probability come from CapitalSimulator as 0–1 floats
#                 survival_str = f"{survival * 100:.1f}%" if survival is not None else "not computed"
#                 avg_dd_str = f"{avg_dd * 100:.2f}%" if avg_dd is not None else "not computed"
#                 median_str = f"USD {median_final:,.2f}" if median_final is not None else "not computed"
#                 ruin_str = f"{ruin_prob * 100:.2f}%" if ruin_prob is not None else "not computed"

#                 lines += [
#                     "---",
#                     "",
#                     "### SECTION 5 — MONTE CARLO CAPITAL SIMULATION (300 paths, 50 trades)",
#                     "",
#                     "| Metric | Value | What It Means |",
#                     "| :--- | :--- | :--- |",
#                     f"| Survival Rate | {survival_str} | Percentage of simulated 50-trade sequences that did NOT hit ruin |",
#                     f"| Average Max Drawdown | {avg_dd_str} | Average worst-case peak-to-trough decline across all 300 paths |",
#                     f"| Median Final Capital | {median_str} | The midpoint outcome — 50% of simulations ended above this value |",
#                     f"| Ruin Probability | {ruin_str} | Probability of losing enough capital to be unable to continue trading |",
#                     "",
#                     f"**Simulation context:** 300 independent paths were simulated, each running {n_trades} sequential trades "
#                     f"using {ticker}'s historical return distribution and the current market regime ({regime_name}). "
#                     f"Starting capital for each path: USD {account:,.2f}.",
#                     "",
#                 ]
#                 if avg_dd is not None:
#                     dd_dollar = account * avg_dd
#                     lines.append(
#                         f"**Drawdown in dollar terms:** An average max drawdown of {avg_dd_str} on a USD {account:,.2f} account "
#                         f"translates to an expected worst-case decline of approximately USD {dd_dollar:,.2f} during a losing streak."
#                     )
#                     lines.append("")
#             else:
#                 lines += [
#                     "---",
#                     "",
#                     "### SECTION 5 — MONTE CARLO CAPITAL SIMULATION",
#                     "",
#                     "Simulation not computed — capital input was not provided.",
#                     "",
#                 ]

#         elif ctx.trade and "error" in ctx.trade:
#             lines += [
#                 "---",
#                 "",
#                 "### SECTION 4 — TRADE ARCHITECTURE",
#                 "",
#                 f"ERROR: {ctx.trade['error']}",
#                 "",
#             ]
#         else:
#             # No trade input — asset-only report
#             lines += [
#                 "---",
#                 "",
#                 "### SECTION 4 — TRADE ARCHITECTURE",
#                 "",
#                 "No trade parameters provided. Supply entry price, stop loss, and take profit for a full trade evaluation.",
#                 "",
#             ]

#         # ── RECOMMENDATION ───────────────────────
#         lines += [
#             "---",
#             "",
#             "### SECTION 6 — RECOMMENDATION",
#             "",
#             f"**Engine output:** {ctx.recommendation}",
#             "",
#             f"**Overall risk classification:** {ctx.summary_label} (composite score: {ctx.summary_score:.4f})",
#             "",
#             "*Composite score is weighted: 40% asset volatility, 20% forecast risk, 10% capital survival. "
#             "Scores below 0.02 = Low Risk. 0.02-0.05 = Moderate. Above 0.05 = High.*",
#         ]

#         return "\n".join(lines)

# core/risk_service.py

import numpy as np
import pandas as pd
import yfinance as yf

from core.risk_sentinel import RiskSentinel
from core.portfolio import PortfolioRisk
from core.trade_risk import TradeRiskEngine
from core.recommender import RecommendationEngine
from core.explainer import RiskExplainer
from core.forecast_risk import ForecastRiskEngine
from core.regime_engine import RegimeEngine
from core.risk_decomposition import RiskDecomposition
from core.capital_simulator import CapitalSimulator
from core.context import RiskContext
from core.sentiment_service import SentimentService


# ──────────────────────────────────────────────────────────────────────────────
# Sentiment helpers
# ──────────────────────────────────────────────────────────────────────────────

def _sentiment_multiplier(sentiment_score: float, trade_direction: str) -> float:
    """
    Returns a risk multiplier based on sentiment vs trade direction.

    Long + positive sentiment  → multiplier < 1  (sentiment reduces risk)
    Long + negative sentiment  → multiplier > 1  (sentiment increases risk)
    Short + positive sentiment → multiplier > 1  (sentiment is a headwind for shorts)
    Short + negative sentiment → multiplier < 1  (sentiment is a tailwind for shorts)

    Cap: multiplier is clipped to [0.70, 1.30] so extreme scores never dominate.
    """
    direction_sign = 1 if trade_direction.upper() == "LONG" else -1
    # sentiment_score ∈ [-1, +1]; negative score on a LONG → multiply risk up
    raw = 1.0 - direction_sign * sentiment_score * 0.30
    return float(np.clip(raw, 0.70, 1.30))


def _sentiment_size_factor(sentiment_score: float, trade_direction: str) -> float:
    """
    Returns a position-size scaling factor based on sentiment alignment.

    Aligned (bullish long / bearish short)    → factor up to 1.20
    Conflicting (bearish long / bullish short) → factor down to 0.80
    Neutral                                   → 1.00

    Cap: clipped to [0.80, 1.20] to prevent wild swings.
    """
    direction_sign = 1 if trade_direction.upper() == "LONG" else -1
    raw = 1.0 + direction_sign * sentiment_score * 0.20
    return float(np.clip(raw, 0.80, 1.20))


def _sentiment_target_adjustment(sentiment_score: float, trade_direction: str,
                                  take_profit: float) -> float:
    """
    Suggests a sentiment-adjusted take-profit.

    Bullish sentiment on LONG  → suggest extending target by up to 10 %
    Bearish sentiment on LONG  → suggest pulling target in by up to 10 %
    Opposite for SHORT.
    """
    direction_sign = 1 if trade_direction.upper() == "LONG" else -1
    factor = 1.0 + direction_sign * sentiment_score * 0.10
    return round(take_profit * factor, 2)


def _detect_trade_direction(entry: float, stop: float) -> str:
    """Infer trade direction from entry vs stop (stop below entry = LONG)."""
    return "LONG" if stop < entry else "SHORT"


class RiskService:
    def __init__(self):
        self.asset_engine = RiskSentinel()
        self.portfolio_engine = PortfolioRisk()
        self.trade_engine = TradeRiskEngine()
        self.recommender = RecommendationEngine()
        self.explainer = RiskExplainer()
        self.forecast_engine = ForecastRiskEngine()
        self.regime_engine = RegimeEngine()
        self.decomposition_engine = RiskDecomposition()
        self.capital_simulator = CapitalSimulator()
        self.sentiment_service = SentimentService()

    # ────────────────────────────────────────────
    # Portfolio Basket Analysis
    # ────────────────────────────────────────────
    def analyze_portfolio_basket(self, holdings: dict):
        """
        holdings: {"AAPL": 5000, "TSLA": 3000, "GLD": 2000}
        """
        tickers = list(holdings.keys())

        data = yf.download(tickers, period="1y", progress=False)['Close']
        if isinstance(data, pd.Series):
            data = data.to_frame(name=tickers[0])

        returns = data.pct_change().dropna()

        total_value = sum(holdings.values())
        weights = np.array([holdings[t] / total_value for t in tickers])

        cov_matrix = returns.cov() * 252
        portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
        portfolio_volatility = np.sqrt(portfolio_variance)

        individual_vols = [returns[t].std() * np.sqrt(252) for t in tickers]
        weighted_avg_vol = sum(v * w for v, w in zip(individual_vols, weights))
        benefit = (weighted_avg_vol - portfolio_volatility) / (weighted_avg_vol + 1e-8)

        return {
            "total_value": total_value,
            "annual_volatility": float(portfolio_volatility),
            "diversification_benefit": float(benefit),
            "tickers": tickers,
        }

    # ────────────────────────────────────────────
    # Asset Risk
    # ────────────────────────────────────────────
    def evaluate_asset(self, ticker, price_series):
        metrics = self.asset_engine.assess_asset(price_series)
        recommendation = self.recommender.recommend_asset(metrics)
        explanation = self.explainer.explain_asset(ticker, metrics)
        return {"metrics": metrics, "recommendation": recommendation, "explanation": explanation}

    # ────────────────────────────────────────────
    # Trade Risk (basic)
    # ────────────────────────────────────────────
    def evaluate_trade(self, **kwargs):
        metrics = self.trade_engine.calculate_trade(**kwargs)
        recommendation = self.recommender.recommend_trade(metrics)
        explanation = self.explainer.explain_trade(metrics)
        return {"metrics": metrics, "recommendation": recommendation, "explanation": explanation}

    # ────────────────────────────────────────────
    # Trade Risk (regime-aware)
    # ────────────────────────────────────────────
    def evaluate_trade_with_context(self, price_series, **kwargs):
        regime = self.evaluate_regime(price_series)
        adjusted_risk = self.regime_engine.adaptive_risk_percent(regime["regime"])
        kwargs["risk_percent"] = adjusted_risk
        metrics = self.trade_engine.calculate_trade(**kwargs)
        explanation = (
            self.explainer.explain_trade(metrics)
            + f"\n\nMarket Regime: {regime['regime']}"
            + f"\nAdjusted Risk %: {adjusted_risk * 100:.2f}%"
        )
        return {
            "metrics": metrics,
            "regime": regime,
            "adjusted_risk_percent": adjusted_risk,
            "explanation": explanation,
        }

    # ────────────────────────────────────────────
    # Regime
    # ────────────────────────────────────────────
    def evaluate_regime(self, price_series):
        returns = self.asset_engine.compute_log_returns(price_series)
        return self.regime_engine.detect_regime(returns)

    # ────────────────────────────────────────────
    # Risk Contribution
    # ────────────────────────────────────────────
    def evaluate_risk_contribution(self, price_dict, weights):
        return self.decomposition_engine.compute_marginal_risk_contribution(price_dict, weights)

    # ────────────────────────────────────────────
    # Capital Survival
    # ────────────────────────────────────────────
    def evaluate_capital_survival(self, price_series, initial_capital=100000):
        returns = self.asset_engine.compute_log_returns(price_series).dropna()
        if len(returns) < 20:
            return {"ruin_probability": 0.0, "median_final_capital": initial_capital}
        vol = returns.std()
        regime_info = self.regime_engine.detect_regime(returns)
        regime = regime_info["regime"]
        win_rate = max(0.3, min(0.7, 0.6 - vol))
        reward_risk_ratio = {"high_vol": 1.5, "low_vol": 2.5}.get(regime, 2.0)
        results = self.capital_simulator.simulate_with_context(
            ctx=None,
            initial_capital=initial_capital,
            returns=returns,
            n_sim=300,
            n_trades=100,
        )
        results["derived_win_rate"] = win_rate
        results["regime"] = regime
        results["volatility"] = float(vol)
        return results

    # ────────────────────────────────────────────
    # FULL PIPELINE
    # ────────────────────────────────────────────
    def full_analysis(
        self,
        ticker,
        price_series,
        predicted_prices=None,
        trade_input=None,
        capital_input=None,
        tft_result=None,      # dict from tft_service.predict_direction()
    ):
        ctx = RiskContext(ticker)
        ctx.price_series = price_series
        ctx.predicted_prices = predicted_prices

        # 1. Asset Risk
        ctx.asset_metrics = self.asset_engine.assess_asset(price_series)

        # 2. Regime Detection
        returns = self.asset_engine.compute_log_returns(price_series).dropna()
        ctx.regime = self.regime_engine.detect_regime(returns)

        # 3. Adaptive Risk
        ctx.adjusted_risk_percent = self.regime_engine.adaptive_risk_percent(
            ctx.regime["regime"]
        )
        ctx.asset_metrics["regime_adjusted_risk_score"] = ctx.asset_metrics[
            "risk_score"
        ] * (1 + ctx.adjusted_risk_percent)

        # 4. Sentiment Analysis
        ctx.sentiment = self.sentiment_service.get_sentiment_features(ticker, days=30)

        # ── Determine trade direction for sentiment calculations ──────────
        #    Available as soon as we know trade_input; used in steps 5, 6, 8.
        trade_direction = "LONG"   # default assumption
        if trade_input:
            trade_direction = _detect_trade_direction(
                trade_input["entry_price"], trade_input["stop_loss"]
            )
        elif tft_result and not tft_result.get("error"):
            trade_direction = tft_result.get("predicted_direction", "UP")
            trade_direction = "LONG" if trade_direction == "UP" else "SHORT"

        sentiment_score  = ctx.sentiment.get("score", 0.0)
        sent_label       = ctx.sentiment.get("label", "NEUTRAL")

        # ── Pre-compute sentiment factors (used in steps 6 and 8) ─────────
        ctx.sentiment_multiplier  = _sentiment_multiplier(sentiment_score, trade_direction)
        ctx.sentiment_size_factor = _sentiment_size_factor(sentiment_score, trade_direction)
        ctx.trade_direction       = trade_direction

        # 5. Forecast Risk (TFT + Sentiment combined)
        ctx.forecast_risk = None
        if tft_result and not tft_result.get("error"):
            predicted_return = (
                (tft_result["predicted_price"] - tft_result["last_close_price"])
                / max(tft_result["last_close_price"], 1e-6)
            )
            ctx.forecast_risk = self.forecast_engine.compute_forecast_integrated_risk(
                historical_vol      = ctx.asset_metrics["volatility"],
                expected_shortfall  = ctx.asset_metrics["expected_shortfall"],
                predicted_return    = predicted_return,
                predicted_direction = tft_result.get("predicted_direction", "UP"),
                sentiment_score     = sentiment_score,
                sentiment_label     = sent_label,
            )
        elif predicted_prices is not None:
            # backward compat — old call path without tft_result
            ctx.forecast_risk = self.forecast_engine.compute_forecast_integrated_risk(
                historical_vol      = ctx.asset_metrics["volatility"],
                expected_shortfall  = ctx.asset_metrics["expected_shortfall"],
                predicted_return    = 0.0,
                predicted_direction = "UP",
                sentiment_score     = sentiment_score,
                sentiment_label     = sent_label,
            )
        else:
            # ── Manual trade path: no TFT → build a sentiment-adjusted
            #    forecast component from pure volatility + sentiment ────────
            base_vol = ctx.asset_metrics["volatility"]
            ctx.forecast_risk = {
                "forecast_integrated_risk" : base_vol * ctx.sentiment_multiplier,
                "sentiment_score"          : sentiment_score,
                "sentiment_label"          : sent_label,
                "sentiment_adjustment"     : ctx.sentiment_multiplier,
                "predicted_direction"      : trade_direction,
                "signal_alignment"         : self._compute_alignment(sentiment_score, trade_direction),
                "alignment_detail"         : self._compute_alignment_detail(sentiment_score, trade_direction),
                "direction_confidence"     : "N/A — manual trade",
                "forecast_vol_ratio"       : 0.0,
                "forecast_risk_label"      : (
                    "HIGH" if base_vol * ctx.sentiment_multiplier > 0.03
                    else "MODERATE" if base_vol * ctx.sentiment_multiplier > 0.015
                    else "LOW"
                ),
            }

        # 6. Trade Analysis + Sentiment-adjusted position size
        ctx.trade = None
        if trade_input:
            ctx.trade = self.trade_engine.calculate_trade_with_context(
                ctx,
                entry_price=trade_input["entry_price"],
                stop_loss=trade_input["stop_loss"],
                take_profit=trade_input["take_profit"],
                account_size=trade_input["account_size"],
            )
            if ctx.trade and "error" not in ctx.trade:
                ctx.trade["entry_price"]  = trade_input["entry_price"]
                ctx.trade["stop_loss"]    = trade_input["stop_loss"]
                ctx.trade["take_profit"]  = trade_input["take_profit"]
                ctx.trade["account_size"] = trade_input["account_size"]

                # ── Exposure cap ─────────────────────────────────────────
                max_exposure   = trade_input["account_size"] * 0.95
                entry          = trade_input["entry_price"]
                max_shares     = int(max_exposure / entry) if entry > 0 else 9999

                if ctx.trade["position_size"] > max_shares:
                    original        = ctx.trade["position_size"]
                    ctx.trade["position_size"]   = max_shares
                    ctx.trade["total_exposure"]  = round(max_shares * entry, 2)
                    ctx.trade["capital_risk_percent"] = round(
                        (max_shares * ctx.trade["risk_per_share"] / trade_input["account_size"]) * 100, 2
                    )
                    print(f"[RISK] Position capped: {original} → {max_shares} shares (exposure limit)")

                # ── Sentiment position-size adjustment ────────────────────
                # Applied AFTER the exposure cap so we never exceed the cap.
                base_size    = ctx.trade["position_size"]
                sent_size    = int(base_size * ctx.sentiment_size_factor)
                sent_size    = max(1, min(sent_size, max_shares))   # stay within cap

                ctx.trade["sentiment_adjusted_size"]     = sent_size
                ctx.trade["sentiment_size_factor"]       = ctx.sentiment_size_factor
                ctx.trade["sentiment_adjusted_exposure"] = round(sent_size * entry, 2)
                ctx.trade["sentiment_adjusted_risk_dollar"] = round(
                    sent_size * ctx.trade.get("risk_per_share", abs(entry - trade_input["stop_loss"])), 2
                )

                # ── Sentiment take-profit suggestion ──────────────────────
                ctx.trade["suggested_take_profit"] = _sentiment_target_adjustment(
                    sentiment_score, trade_direction, trade_input["take_profit"]
                )

                print(
                    f"[SENTIMENT] Direction={trade_direction} | Score={sentiment_score:+.4f} "
                    f"({sent_label}) | SizeFactor={ctx.sentiment_size_factor:.2f} | "
                    f"Base={base_size} → SentAdj={sent_size} shares | "
                    f"SuggestedTP={ctx.trade['suggested_take_profit']}"
                )

        # 7. Capital Simulation
        ctx.capital = None
        if capital_input:
            sim_returns = self.asset_engine.compute_log_returns(price_series).dropna()
            ctx.capital = self.capital_simulator.simulate_with_context(
                ctx=ctx,
                returns=sim_returns,
                initial_capital=capital_input.get("initial_capital", 100000),
                n_trades=capital_input.get("n_trades", 50),
                n_sim=capital_input.get("simulations", 300),
            )

        # 8. Composite Risk Score
        #    Manual trades use the sentiment-adjusted forecast component instead
        #    of raw volatility, so negative sentiment on a LONG actually raises
        #    the composite score (and vice-versa).
        forecast_component = (
            ctx.forecast_risk["forecast_integrated_risk"]
            if ctx.forecast_risk
            else ctx.asset_metrics["volatility"]
        )
        dd = ctx.capital.get("avg_drawdown", 0.5) if ctx.capital else 0.5
        capital_component = max(0, 1 - dd)
        ctx.summary_score = (
            0.4 * ctx.asset_metrics["risk_score"]
            + 0.2 * forecast_component
            + 0.1 * capital_component
        )

        # 9. Risk Label
        if ctx.summary_score < 0.05:   ctx.summary_label = "LOW RISK"
        elif ctx.summary_score < 0.12: ctx.summary_label = "MODERATE RISK"
        else:                           ctx.summary_label = "HIGH RISK"

        # 10. Recommendation
        ctx.recommendation = self.recommender.recommend_asset(ctx.asset_metrics)

        # 11. Build Report
        ctx.explanation = self._build_report(ctx, ticker)
        return ctx

    # ────────────────────────────────────────────
    # Alignment helpers
    # ────────────────────────────────────────────
    def _compute_alignment(self, sentiment_score: float, trade_direction: str) -> str:
        """ALIGNED / CONFLICTING / NEUTRAL based on score magnitude and direction."""
        threshold = 0.10
        if abs(sentiment_score) < threshold:
            return "NEUTRAL"
        direction_sign = 1 if trade_direction == "LONG" else -1
        return "ALIGNED" if (direction_sign * sentiment_score) > 0 else "CONFLICTING"

    def _compute_alignment_detail(self, sentiment_score: float, trade_direction: str) -> str:
        alignment = self._compute_alignment(sentiment_score, trade_direction)
        label = "POSITIVE" if sentiment_score > 0.10 else "NEGATIVE" if sentiment_score < -0.10 else "NEUTRAL"
        if alignment == "ALIGNED":
            return (
                f"News sentiment is {label} ({sentiment_score:+.4f}) and the trade is {trade_direction}. "
                "Sentiment supports the trade direction — confidence is higher."
            )
        if alignment == "CONFLICTING":
            return (
                f"News sentiment is {label} ({sentiment_score:+.4f}) but the trade is {trade_direction}. "
                "Sentiment is a headwind — position size has been reduced and risk is elevated."
            )
        return (
            f"News sentiment is essentially flat ({sentiment_score:+.4f}). "
            "No significant directional pressure from news flow."
        )

    # ────────────────────────────────────────────
    # Report Builder
    # ────────────────────────────────────────────
    def _build_report(self, ctx, ticker: str) -> str:
        ticker = ticker.upper()
        vol = ctx.asset_metrics.get("volatility", 0)
        risk_score = ctx.asset_metrics.get("risk_score", 0)
        es = ctx.asset_metrics.get("expected_shortfall", 0)
        regime_name = ctx.regime.get("regime", "UNKNOWN").upper()
        adj_risk_pct = ctx.adjusted_risk_percent * 100

        # ── REGIME EXPLANATION ──────────────────
        regime_explanations = {
            "HIGH_VOL": (
                "HIGH VOLATILITY — The asset's recent price swings are statistically elevated. "
                "The regime engine has detected daily return dispersion above normal thresholds. "
                f"Adaptive risk allocation has been reduced to {adj_risk_pct:.1f}% of account per trade."
            ),
            "LOW_VOL": (
                "LOW VOLATILITY — The market is in a compression phase. "
                "Price action is tight and mean-reverting. "
                f"Standard allocation of {adj_risk_pct:.1f}% per trade is acceptable."
            ),
            "NORMAL_VOL": (
                "NORMAL VOLATILITY — Asset is trading within historical norms. "
                f"Risk allocation set to {adj_risk_pct:.1f}% of account per trade."
            ),
        }
        regime_text = regime_explanations.get(
            regime_name,
            f"Regime: {regime_name}. Adjusted risk allocation: {adj_risk_pct:.1f}%."
        )

        # ── ASSET RISK SECTION ───────────────────
        vol_annualized = vol * (252 ** 0.5)
        es_pct = es * 100

        lines = [
            f"## INSTITUTIONAL RISK REPORT — {ticker}",
            "",
            "---",
            "",
            "### SECTION 1 — ASSET RISK PROFILE",
            "",
            f"| Metric | Raw Value | Annualized | Interpretation |",
            f"| :--- | :--- | :--- | :--- |",
            f"| Daily Volatility | {vol:.4f} | {vol_annualized:.4f} ({vol_annualized*100:.2f}%/yr) | {'HIGH — handle with reduced size' if vol_annualized > 0.30 else 'MODERATE — standard caution' if vol_annualized > 0.15 else 'LOW — stable asset'} |",
            f"| Expected Shortfall (CVaR) | {es:.4f} | — | On your worst 5% of trading days, expect to lose at least {es_pct:.2f}% of the position value |",
            f"| Risk Score (0–1) | {risk_score:.4f} | — | {'> 0.6 = High intrinsic risk' if risk_score > 0.6 else '0.3-0.6 = Moderate' if risk_score > 0.3 else '< 0.3 = Low'} |",
            f"| Composite Risk Label | — | — | {ctx.summary_label} |",
            "",
            "**Daily Volatility explained:** A daily vol of {:.4f} means the asset moves roughly {:.2f}% per day on average (1 standard deviation). ".format(vol, vol * 100)
            + "Annualized, this implies your position value could swing by {:.2f}% over a full year within normal market conditions.".format(vol_annualized * 100),
            "",
            "**Expected Shortfall (CVaR) explained:** This is not your average loss — it is the *expected magnitude* of loss "
            f"conditioned on being in the worst 5% of outcomes. A CVaR of {es_pct:.2f}% means: "
            f"in a tail-risk scenario, you should plan for losing at least {es_pct:.2f}% of the position in a single session.",
            "",
            "---",
            "",
            "### SECTION 2 — SENTIMENT AND FORECAST ALIGNMENT",
            "",
        ]

        # ── SENTIMENT + FORECAST RISK BLOCK ─────────────────────────────────
        if ctx.forecast_risk:
            fr             = ctx.forecast_risk
            sent_score     = fr.get("sentiment_score", 0.0)
            sent_label_val = fr.get("sentiment_label", "NEUTRAL")
            alignment      = fr.get("signal_alignment", "NEUTRAL")
            align_detail   = fr.get("alignment_detail", "")
            dir_conf       = fr.get("direction_confidence", "MODERATE")
            fr_label       = fr.get("forecast_risk_label", "MODERATE")
            fr_score       = fr.get("forecast_integrated_risk", 0.0)
            vol_ratio      = fr.get("forecast_vol_ratio", 0.0)
            pred_dir       = fr.get("predicted_direction", ctx.trade_direction)
            sent_adj       = fr.get("sentiment_adjustment", ctx.sentiment_multiplier)
            n_articles     = ctx.sentiment.get("articles_analyzed", 0)

            # ── Sentiment action on this trade ───────────────────────────────
            is_tft_trade = (
                hasattr(ctx, "tft_result") or
                fr.get("direction_confidence", "") != "N/A — manual trade"
            )

            if abs(sent_score) < 0.10:
                sent_impact_label = "NEUTRAL — no size or target adjustment"
            elif self._compute_alignment(sent_score, ctx.trade_direction) == "ALIGNED":
                sent_impact_label = "POSITIVE ALIGNMENT — size scaled up, target extended"
            else:
                sent_impact_label = "NEGATIVE ALIGNMENT — size scaled down, target pulled in"

            lines += [
                f"| Metric | Value | Interpretation |",
                f"| :--- | :--- | :--- |",
                f"| News Sentiment | {sent_score:+.4f} ({sent_label_val}) | "
                f"{'Bullish news flow supports upward price movement' if sent_label_val == 'POSITIVE' else 'Bearish news flow adds downward pressure' if sent_label_val == 'NEGATIVE' else 'News flow is neutral — no directional pressure'} |",
                f"| Articles Analyzed | {n_articles} | Articles from past 30 days via Finnhub, scored by FinBERT + DeBERTa + VADER ensemble |",
                f"| Trade Direction | {ctx.trade_direction} | {'TFT model output' if is_tft_trade else 'User defined (inferred from entry vs stop)'} |",
                f"| Signal Alignment | {alignment} | "
                f"{'Sentiment and trade direction agree — confidence is higher' if alignment == 'ALIGNED' else 'Sentiment opposes trade direction — treat with caution' if alignment == 'CONFLICTING' else 'Sentiment is flat — no confirmation or contradiction'} |",
                f"| Sentiment Risk Multiplier | {sent_adj:.2f}x | Applied to forecast risk component in composite score — above 1.0 raises risk, below 1.0 lowers it |",
                f"| Sentiment Size Factor | {ctx.sentiment_size_factor:.2f}x | {'Position size scaled UP — sentiment aligned with trade' if ctx.sentiment_size_factor > 1.0 else 'Position size scaled DOWN — sentiment conflicts with trade' if ctx.sentiment_size_factor < 1.0 else 'No size adjustment at neutral sentiment'} |",
                f"| Forecast Risk Score | {fr_score:.4f} ({fr_label}) | Sentiment-adjusted risk component used in composite score |",
            ]

            if vol_ratio > 0:
                lines.append(
                    f"| Forecast Vol Ratio | {vol_ratio:.2f}x | Predicted move is {vol_ratio:.2f}x the asset normal daily volatility |"
                )
                lines.append(
                    f"| Direction Confidence | {dir_conf} | Based on size of predicted return relative to historical vol |"
                )

            lines += [
                "",
                f"**Signal alignment detail:** {align_detail}",
                "",
                f"**Sentiment impact on this trade:** {sent_impact_label}.",
                "",
            ]

            # Suggested target adjustment (only when trade exists)
            if ctx.trade and "suggested_take_profit" in ctx.trade:
                orig_tp    = ctx.trade.get("take_profit", 0)
                sug_tp     = ctx.trade["suggested_take_profit"]
                tp_diff    = sug_tp - orig_tp
                tp_diff_pct = (tp_diff / orig_tp * 100) if orig_tp else 0
                sign        = "+" if tp_diff >= 0 else ""
                lines += [
                    f"**Sentiment-suggested take profit:** USD {sug_tp:,.2f} "
                    f"({sign}{tp_diff:,.2f} / {sign}{tp_diff_pct:.2f}% vs your original target of USD {orig_tp:,.2f}). "
                    f"This reflects the degree to which news sentiment {'supports' if tp_diff >= 0 else 'undermines'} "
                    f"the probability of reaching your original target.",
                    "",
                ]

        else:
            lines += [
                "TFT forecast not available for this query. Run a prediction first to see sentiment and forecast alignment.",
                "",
            ]

        lines += [
            "---",
            "",
            "### SECTION 3 — MARKET REGIME",
            "",
            regime_text,
            "",
        ]

        # ── TRADE SECTION ────────────────────────────────────────────────────
        if ctx.trade and "error" not in ctx.trade:
            t         = ctx.trade
            rr        = t.get("risk_reward_ratio", 0)
            pos_size  = t.get("position_size", 0)
            sent_size = t.get("sentiment_adjusted_size", pos_size)
            exposure  = t.get("total_exposure", 0)
            entry     = t.get("entry_price", 0)
            stop      = t.get("stop_loss", 0)
            take      = t.get("take_profit", 0)
            sug_tp    = t.get("suggested_take_profit", take)
            size_fac  = t.get("sentiment_size_factor", 1.0)
            sent_exp  = t.get("sentiment_adjusted_exposure", exposure)
            sent_risk = t.get("sentiment_adjusted_risk_dollar", 0)

            dollar_risk   = abs(entry - stop) * pos_size if entry and stop and pos_size else 0
            dollar_reward = abs(take - entry) * pos_size if take and entry and pos_size else 0

            # R:R using sentiment-adjusted position
            sent_dollar_risk   = abs(entry - stop) * sent_size if entry and stop and sent_size else dollar_risk
            sent_dollar_reward = abs(take - entry) * sent_size if take and entry and sent_size else dollar_reward

            if rr < 1.95:
                rr_quality = "POOR — below the institutional minimum of 2.0"
                rr_action  = "Do not take this trade at current levels. Widen take profit or tighten stop loss."
            elif rr < 3:
                rr_quality = "ACCEPTABLE — meets minimum threshold"
                rr_action  = "Proceed with caution. Tightening stop loss or widening take profit would improve quality."
            else:
                rr_quality = "STRONG — exceeds institutional standard"
                rr_action  = "Trade setup is structurally sound at current levels."

            breakeven_wr = (1 / (1 + rr)) * 100

            # Size change label
            if sent_size > pos_size:
                size_change_note = f"↑ Increased from {pos_size} (sentiment aligned with trade)"
            elif sent_size < pos_size:
                size_change_note = f"↓ Reduced from {pos_size} (sentiment conflicts with trade)"
            else:
                size_change_note = f"Unchanged (neutral sentiment)"

            lines += [
                "---",
                "",
                "### SECTION 4 — TRADE ARCHITECTURE",
                "",
                "| Parameter | Base Value | Sentiment-Adjusted | Note |",
                "| :--- | :--- | :--- | :--- |",
                f"| Entry Price | USD {entry:,.2f} | USD {entry:,.2f} | Fixed — sentiment does not move entry |",
                f"| Stop Loss | USD {stop:,.2f} | USD {stop:,.2f} | Fixed — sentiment does not move stop |",
                f"| Take Profit | USD {take:,.2f} | USD {sug_tp:,.2f} | Suggested based on sentiment alignment |",
                f"| Position Size | {pos_size} shares | {sent_size} shares | {size_change_note} |",
                f"| Total Exposure | USD {exposure:,.2f} | USD {sent_exp:,.2f} | Sentiment size × entry price |",
                f"| Dollar Risk (max loss) | USD {dollar_risk:,.2f} | USD {sent_dollar_risk:,.2f} | Risk if stop is hit |",
                f"| Dollar Reward (max gain) | USD {dollar_reward:,.2f} | USD {sent_dollar_reward:,.2f} | Reward if target is hit |",
                f"| Risk/Reward Ratio | {rr:.2f} | {rr:.2f} | R:R unchanged — levels not moved |",
                f"| Trade Quality | {rr_quality} | | |",
                "",
                f"**Position size explained:** The base model calculated {pos_size} shares. "
                f"Sentiment adjustment ({size_fac:.2f}x) {'increased' if sent_size > pos_size else 'reduced' if sent_size < pos_size else 'left unchanged'} "
                f"this to {sent_size} shares. "
                f"At {sent_size} shares, maximum downside exposure is USD {sent_dollar_risk:,.2f} if the stop is hit.",
                "",
                f"**Risk/Reward ({rr:.2f}) explained:** You are risking USD {sent_dollar_risk:,.2f} to potentially make USD {sent_dollar_reward:,.2f} "
                f"(using sentiment-adjusted size). With a {rr:.2f} R:R, you need to win at least {breakeven_wr:.1f}% "
                f"of trades to break even. {rr_action}",
                "",
            ]

            # ── MONTE CARLO SECTION ──────────────────────────────────────────
            if ctx.capital:
                avg_dd       = ctx.capital.get("avg_drawdown", None)
                median_final = ctx.capital.get("median_final_capital", None)
                ruin_prob    = float(avg_dd) / 0.5 if avg_dd is not None else None
                ruin_prob    = min(ruin_prob, 1.0) if ruin_prob is not None else None
                survival     = (1.0 - ruin_prob) if ruin_prob is not None else None
                n_trades     = 50
                account      = t.get("account_size", ctx.capital.get("initial_capital", 100000))

                survival_str  = f"{survival * 100:.1f}%"  if survival     is not None else "not computed"
                avg_dd_str    = f"{avg_dd * 100:.2f}%"    if avg_dd       is not None else "not computed"
                median_str    = f"USD {median_final:,.2f}" if median_final is not None else "not computed"
                ruin_str      = f"{ruin_prob * 100:.2f}%" if ruin_prob    is not None else "not computed"

                lines += [
                    "---",
                    "",
                    "### SECTION 5 — MONTE CARLO CAPITAL SIMULATION (300 paths, 50 trades)",
                    "",
                    "| Metric | Value | What It Means |",
                    "| :--- | :--- | :--- |",
                    f"| Survival Rate | {survival_str} | Percentage of simulated 50-trade sequences that did NOT hit ruin |",
                    f"| Average Max Drawdown | {avg_dd_str} | Average worst-case peak-to-trough decline across all 300 paths |",
                    f"| Median Final Capital | {median_str} | The midpoint outcome — 50% of simulations ended above this value |",
                    f"| Ruin Probability | {ruin_str} | Probability of losing enough capital to be unable to continue trading |",
                    "",
                    f"**Simulation context:** 300 independent paths were simulated, each running {n_trades} sequential trades "
                    f"using {ticker}'s historical return distribution and the current market regime ({regime_name}). "
                    f"Starting capital for each path: USD {account:,.2f}.",
                    "",
                ]
                if avg_dd is not None:
                    dd_dollar = account * avg_dd
                    lines.append(
                        f"**Drawdown in dollar terms:** An average max drawdown of {avg_dd_str} on a USD {account:,.2f} account "
                        f"translates to an expected worst-case decline of approximately USD {dd_dollar:,.2f} during a losing streak."
                    )
                    lines.append("")
            else:
                lines += [
                    "---",
                    "",
                    "### SECTION 5 — MONTE CARLO CAPITAL SIMULATION",
                    "",
                    "Simulation not computed — capital input was not provided.",
                    "",
                ]

        elif ctx.trade and "error" in ctx.trade:
            lines += [
                "---",
                "",
                "### SECTION 4 — TRADE ARCHITECTURE",
                "",
                f"ERROR: {ctx.trade['error']}",
                "",
            ]
        else:
            lines += [
                "---",
                "",
                "### SECTION 4 — TRADE ARCHITECTURE",
                "",
                "No trade parameters provided. Supply entry price, stop loss, and take profit for a full trade evaluation.",
                "",
            ]

        # ── RECOMMENDATION ───────────────────────────────────────────────────
        lines += [
            "---",
            "",
            "### SECTION 6 — RECOMMENDATION",
            "",
            f"**Engine output:** {ctx.recommendation}",
            "",
            f"**Overall risk classification:** {ctx.summary_label} (composite score: {ctx.summary_score:.4f})",
            "",
            "*Composite score is weighted: 40% asset volatility, 20% sentiment-adjusted forecast risk, "
            "10% capital survival. Scores below 0.05 = Low Risk. 0.05–0.12 = Moderate. Above 0.12 = High.*",
            "",
            "**Sentiment-driven suggestions for this trade:**",
        ]

        # Dynamic suggestions block
        if ctx.forecast_risk:
            sent_score = ctx.forecast_risk.get("sentiment_score", 0.0)
            alignment  = self._compute_alignment(sent_score, ctx.trade_direction)

            if alignment == "CONFLICTING":
                lines += [
                    "- ⚠️  Sentiment conflicts with your trade direction. Consider waiting for news flow to improve before entering.",
                    "- ⚠️  Position size has been reduced automatically. You may reduce it further or skip this trade.",
                    "- ⚠️  Your suggested take profit has been pulled in. A smaller target improves the probability of being hit under bearish news conditions.",
                ]
            elif alignment == "ALIGNED":
                lines += [
                    "- ✅  Sentiment aligns with trade direction — this is a higher-confidence setup.",
                    "- ✅  Position size has been scaled up. Confirm you are comfortable with the increased dollar exposure.",
                    f"- ✅  Consider using the sentiment-extended take profit (USD {ctx.trade.get('suggested_take_profit', 'N/A'):,.2f} if available) to capture additional upside.",
                ]
            else:
                lines += [
                    "- ℹ️  Sentiment is neutral — no additional edge or headwind from news flow.",
                    "- ℹ️  Position size and take profit are unchanged. Rely on technical and regime analysis.",
                ]

        lines.append("")
        return "\n".join(lines)