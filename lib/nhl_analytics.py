# lib/nhl_analytics.py
"""
NHL Analytics + Betting Interface (NO ENSEMBLE)
- Uses 3 models directly: Power Rankings, Similar Games, Decision Tree
- Standardizes outputs for MONEYLINE / SPREAD (puckline) / TOTAL (O/U)
- Designed to plug cleanly into SportsBetLang "MONEY / SPREAD / TOTAL" language

Outputs include:
  - pick
  - probability (win prob of the pick)
  - fair odds (American)
  - implied prob / edge / EV when market odds supplied
  - model votes + convergence (how many models agree)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Optional, Any, List, Tuple


# ----------------------------
# Odds + EV utilities
# ----------------------------

def american_to_implied_prob(odds: float) -> float:
    if odds == 0:
        raise ValueError("American odds cannot be 0")
    if odds > 0:
        return 100.0 / (odds + 100.0)
    return (-odds) / ((-odds) + 100.0)


def prob_to_american(prob: float) -> int:
    prob = float(prob)
    if prob <= 0.0 or prob >= 1.0:
        raise ValueError("Probability must be between 0 and 1 (exclusive).")
    if prob > 0.5:
        return int(-round((prob / (1 - prob)) * 100))
    return int(round(((1 - prob) / prob) * 100))


def payout_per_1_risk(odds: float) -> float:
    if odds > 0:
        return odds / 100.0
    return 100.0 / (-odds)


def expected_value_per_1_risk(prob_win: float, odds: float) -> float:
    profit = payout_per_1_risk(odds)
    return prob_win * profit - (1.0 - prob_win)


# ----------------------------
# Poisson helpers (for totals)
# ----------------------------

def poisson_pmf(k: int, lam: float) -> float:
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def poisson_cdf(k: int, lam: float, max_k: int = 25) -> float:
    k = int(k)
    total = 0.0
    for i in range(0, min(k, max_k) + 1):
        total += poisson_pmf(i, lam)
    return total


def poisson_prob_over_line(total_lambda: float, line: float, max_k: int = 25) -> float:
    # 6.5 -> over means >= 7
    if line % 1 == 0.5:
        threshold = int(math.floor(line) + 1)
        p_le = poisson_cdf(threshold - 1, total_lambda, max_k=max_k)
        return max(0.0, 1.0 - p_le)
    # integer line: over means >= line+1
    threshold = int(line) + 1
    p_le = poisson_cdf(threshold - 1, total_lambda, max_k=max_k)
    return max(0.0, 1.0 - p_le)


def poisson_prob_under_line(total_lambda: float, line: float, max_k: int = 25) -> float:
    # 6.5 -> under means <= 6
    if line % 1 == 0.5:
        threshold = int(math.floor(line))
        return poisson_cdf(threshold, total_lambda, max_k=max_k)
    # integer line: under means <= line-1 (push at line)
    threshold = int(line) - 1
    return poisson_cdf(threshold, total_lambda,
