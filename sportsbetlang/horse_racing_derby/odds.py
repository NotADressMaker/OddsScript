from __future__ import annotations

import numpy as np
import pandas as pd


class OddsConverter:
    @staticmethod
    def probability_to_decimal_odds(probability):
        p = np.clip(probability, 1e-6, 1 - 1e-6)
        return 1.0 / p

    @staticmethod
    def compare_market_vs_true_odds(df: pd.DataFrame, prob_col: str = "true_win_probability") -> pd.DataFrame:
        out = df.copy()
        out["true_decimal_odds"] = OddsConverter.probability_to_decimal_odds(out[prob_col])
        out["edge_probability"] = out[prob_col] - out["market_implied_prob"]
        out["edge_odds_decimal"] = out["market_odds_decimal"] - out["true_decimal_odds"]
        out["is_value_bet"] = out["edge_probability"] > 0
        return out
