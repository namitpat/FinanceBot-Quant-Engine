# core/forecast_risk.py
#
# Computes forecast-integrated risk by combining:
#   1. TFT model output (predicted_return, predicted_direction)
#   2. Sentiment signal (recency-weighted FinBERT+DeBERTa+VADER ensemble)
#
# NOT a TFT feature — sentiment is a post-inference risk adjustment layer.

from dataclasses import dataclass
from typing import Optional


@dataclass
class ForecastRiskResult:
    # Raw inputs
    predicted_return:       float
    predicted_direction:    str          # "UP" or "DOWN"
    historical_vol:         float
    expected_shortfall:     float
    sentiment_score:        float        # -1 to +1
    sentiment_label:        str          # POSITIVE / NEUTRAL / NEGATIVE

    # Derived
    forecast_vol_ratio:     float        # how large is the predicted move vs. normal?
    direction_confidence:   str          # HIGH / MODERATE / LOW
    signal_alignment:       str          # ALIGNED / CONFLICTING / NEUTRAL
    alignment_detail:       str          # human-readable explanation
    forecast_risk_score:    float        # 0+ composite score (higher = riskier)
    forecast_risk_label:    str          # LOW / MODERATE / HIGH
    sentiment_adjustment:   float        # multiplier applied (0.8 / 1.0 / 1.2)


class ForecastRiskEngine:
    """
    Combines TFT prediction with sentiment to produce a forecast-integrated
    risk score and signal alignment assessment.
    """

    def compute_forecast_integrated_risk(
        self,
        historical_vol:       float,
        expected_shortfall:   float,
        predicted_prices:     Optional[list] = None,   # kept for backward compatibility
        predicted_return:     float = 0.0,
        predicted_direction:  str   = "UP",
        sentiment_score:      float = 0.0,
        sentiment_label:      str   = "NEUTRAL",
    ) -> dict:
        """
        Main entry point called by risk_service.full_analysis().

        Returns a dict (not ForecastRiskResult) for easy JSON serialization
        and backward compatibility with existing ctx.forecast_risk usage.
        """

        result = self._compute(
            historical_vol      = historical_vol,
            expected_shortfall  = expected_shortfall,
            predicted_return    = predicted_return,
            predicted_direction = predicted_direction,
            sentiment_score     = sentiment_score,
            sentiment_label     = sentiment_label,
        )

        # Return as dict — all keys the report builder accesses
        return {
            "forecast_integrated_risk":  result.forecast_risk_score,
            "forecast_risk_label":       result.forecast_risk_label,
            "forecast_vol_ratio":        result.forecast_vol_ratio,
            "direction_confidence":      result.direction_confidence,
            "signal_alignment":          result.signal_alignment,
            "alignment_detail":          result.alignment_detail,
            "sentiment_score":           result.sentiment_score,
            "sentiment_label":           result.sentiment_label,
            "sentiment_adjustment":      result.sentiment_adjustment,
            "predicted_return":          result.predicted_return,
            "predicted_direction":       result.predicted_direction,
        }

    def _compute(
        self,
        historical_vol:      float,
        expected_shortfall:  float,
        predicted_return:    float,
        predicted_direction: str,
        sentiment_score:     float,
        sentiment_label:     str,
    ) -> ForecastRiskResult:

        # ── 1. Forecast volatility ratio ─────────────────────────────────
        # How large is the predicted move relative to the asset's normal daily vol?
        # > 1.0 means the model expects an unusually large move
        vol_safe = max(historical_vol, 1e-6)
        forecast_vol_ratio = abs(predicted_return) / vol_safe

        # ── 2. Direction confidence from vol ratio ────────────────────────
        # A large predicted move is more "decisive" than a small one
        if forecast_vol_ratio > 1.5:
            direction_confidence = "HIGH"
        elif forecast_vol_ratio > 0.7:
            direction_confidence = "MODERATE"
        else:
            direction_confidence = "LOW"

        # ── 3. Signal alignment ───────────────────────────────────────────
        # Do the TFT direction and sentiment agree?
        tft_bullish  = predicted_direction.upper() == "UP"
        sent_bullish = sentiment_score > 0.05
        sent_bearish = sentiment_score < -0.05
        sent_neutral = not sent_bullish and not sent_bearish

        if sent_neutral:
            alignment       = "NEUTRAL"
            alignment_adj   = 1.0
            alignment_detail = (
                f"Sentiment is neutral ({sentiment_score:+.3f}). "
                f"No directional confirmation or contradiction from news flow."
            )
        elif (tft_bullish and sent_bullish) or (not tft_bullish and sent_bearish):
            alignment       = "ALIGNED"
            alignment_adj   = 0.85   # agreement reduces uncertainty → lower risk
            alignment_detail = (
                f"TFT model ({predicted_direction}) and news sentiment ({sentiment_label}, "
                f"score {sentiment_score:+.3f}) agree. "
                f"Dual-signal confirmation — higher directional confidence."
            )
        else:
            alignment       = "CONFLICTING"
            alignment_adj   = 1.25   # disagreement increases uncertainty → higher risk
            alignment_detail = (
                f"TFT model predicts {predicted_direction} but news sentiment is "
                f"{sentiment_label} (score {sentiment_score:+.3f}). "
                f"Conflicting signals increase uncertainty. "
                f"Consider reducing position size until signals converge."
            )

        # ── 4. Sentiment intensity adjustment ────────────────────────────
        # Strong sentiment (either direction) amplifies the signal
        abs_sent = abs(sentiment_score)
        if abs_sent > 0.5:
            intensity_adj = 1.15
        elif abs_sent > 0.2:
            intensity_adj = 1.0
        else:
            intensity_adj = 0.9

        sentiment_adjustment = round(alignment_adj * intensity_adj, 3)

        # ── 5. Composite forecast risk score ─────────────────────────────
        # Base: how extreme is CVaR amplified by the predicted move size
        # Adjusted: by whether sentiment confirms or contradicts
        base_risk    = abs(expected_shortfall) * (1 + forecast_vol_ratio)
        forecast_risk_score = base_risk * sentiment_adjustment

        # ── 6. Risk label ─────────────────────────────────────────────────
        if forecast_risk_score < 0.05:
            forecast_risk_label = "LOW"
        elif forecast_risk_score < 0.12:
            forecast_risk_label = "MODERATE"
        else:
            forecast_risk_label = "HIGH"

        return ForecastRiskResult(
            predicted_return      = predicted_return,
            predicted_direction   = predicted_direction,
            historical_vol        = historical_vol,
            expected_shortfall    = expected_shortfall,
            sentiment_score       = sentiment_score,
            sentiment_label       = sentiment_label,
            forecast_vol_ratio    = round(forecast_vol_ratio, 4),
            direction_confidence  = direction_confidence,
            signal_alignment      = alignment,
            alignment_detail      = alignment_detail,
            forecast_risk_score   = round(forecast_risk_score, 4),
            forecast_risk_label   = forecast_risk_label,
            sentiment_adjustment  = sentiment_adjustment,
        )