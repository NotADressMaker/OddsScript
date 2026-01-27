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
    return poisson_cdf(threshold, total_lambda, max_k=max_k)


def poisson_prob_push(total_lambda: float, line: float) -> float:
    if line % 1 != 0:
        return 0.0
    return poisson_pmf(int(line), total_lambda)


# ----------------------------
# Standard return container
# ----------------------------

@dataclass
class BetResult:
    bet_type: str                 # "MONEY" | "SPREAD" | "TOTAL"
    pick: str                     # ex: "HOME", "AWAY", "HOME +1.5", "UNDER 6.5"
    prob: float                   # win probability of THIS pick
    fair_odds: int                # fair American odds
    market_odds: Optional[float]  # market American odds, if supplied
    implied_prob: Optional[float]
    edge: Optional[float]
    ev_per_1: Optional[float]     # EV per $1 risked
    details: Dict[str, Any]       # model votes, raw outputs, etc.


# ----------------------------
# NHLAnalytics (no ensemble)
# ----------------------------

class NHLAnalytics:
    """
    Uses three independent models:
      - power_model
      - similar_model
      - tree_model

    Each model can be optional; we average whatever is available.
    """

    def __init__(
        self,
        power_model: Optional[Any] = None,
        tree_model: Optional[Any] = None,
        similar_model: Optional[Any] = None,
    ):
        self.power = power_model
        self.tree = tree_model
        self.similar = similar_model

    # ----------------------------
    # Public API: MONEY
    # ----------------------------

    def predict_moneyline(
        self,
        home_team: str,
        away_team: str,
        features: Dict[str, float],
        market_home_odds: Optional[float] = None,
        market_away_odds: Optional[float] = None,
    ) -> Dict[str, BetResult]:

        votes, probs, raw = self._collect_moneyline_votes(home_team, away_team, features)
        p_home = self._avg_prob_or_default(probs, default=0.5)
        p_home = self._clamp(p_home, 0.01, 0.99)
        p_away = 1.0 - p_home

        details = {
            "home_team": home_team,
            "away_team": away_team,
            "model_votes": votes,
            "model_probs_home": probs,
            "convergence_count": self._convergence_count(votes),
            "raw": raw,
        }

        return {
            "HOME": self._make_bet_result("MONEY", "HOME", p_home, market_home_odds, details),
            "AWAY": self._make_bet_result("MONEY", "AWAY", p_away, market_away_odds, details),
        }

    # ----------------------------
    # Public API: SPREAD / PUCKLINE
    # ----------------------------

    def predict_spread(
        self,
        home_team: str,
        away_team: str,
        features: Dict[str, float],
        line_home: float,
        line_away: float,
        market_home_odds: Optional[float] = None,
        market_away_odds: Optional[float] = None,
    ) -> Dict[str, BetResult]:

        votes, probs, raw = self._collect_spread_votes(home_team, away_team, features, line_home, line_away)
        p_home_cover = self._avg_prob_or_default(probs, default=0.5)
        p_home_cover = self._clamp(p_home_cover, 0.01, 0.99)
        p_away_cover = 1.0 - p_home_cover

        details = {
            "home_team": home_team,
            "away_team": away_team,
            "line_home": line_home,
            "line_away": line_away,
            "model_votes": votes,
            "model_probs_home_cover": probs,
            "convergence_count": self._convergence_count(votes),
            "raw": raw,
        }

        return {
            "HOME": self._make_bet_result("SPREAD", f"HOME {line_home:+.1f}", p_home_cover, market_home_odds, details),
            "AWAY": self._make_bet_result("SPREAD", f"AWAY {line_away:+.1f}", p_away_cover, market_away_odds, details),
        }

    # ----------------------------
    # Public API: TOTAL
    # ----------------------------

    def predict_total(
        self,
        home_team: str,
        away_team: str,
        features: Dict[str, float],
        total_line: float,
        market_over_odds: Optional[float] = None,
        market_under_odds: Optional[float] = None,
        max_goals_sum: int = 25,
    ) -> Dict[str, BetResult]:

        # expected goals: try model-provided, else use feature proxy
        home_xg, away_xg, xg_source = self._expected_goals(home_team, away_team, features)
        lam_total = home_xg + away_xg

        p_over = poisson_prob_over_line(lam_total, total_line, max_k=max_goals_sum)
        p_under = poisson_prob_under_line(lam_total, total_line, max_k=max_goals_sum)
        p_push = poisson_prob_push(lam_total, total_line)

        details = {
            "home_team": home_team,
            "away_team": away_team,
            "home_xg": home_xg,
            "away_xg": away_xg,
            "expected_total": lam_total,
            "total_line": total_line,
            "p_push": p_push,
            "xg_source": xg_source,
        }

        return {
            "OVER": self._make_bet_result("TOTAL", f"OVER {total_line:.1f}", p_over, market_over_odds, details),
            "UNDER": self._make_bet_result("TOTAL", f"UNDER {total_line:.1f}", p_under, market_under_odds, details),
        }

    # ----------------------------
    # Convergence helpers
    # ----------------------------

    def convergence_summary(self, votes: Dict[str, str]) -> Dict[str, Any]:
        """
        votes: {"power": "HOME", "tree": "AWAY", "similar": "HOME"} etc.
        """
        counts: Dict[str, int] = {}
        for v in votes.values():
            counts[v] = counts.get(v, 0) + 1
        best_pick = max(counts.items(), key=lambda kv: kv[1])[0] if counts else None
        return {"counts": counts, "best_pick": best_pick, "max_count": counts.get(best_pick, 0) if best_pick else 0}

    # ----------------------------
    # Legacy compatibility (if other scripts call these)
    # ----------------------------

    @staticmethod
    def calculate_moneyline_probability(team_strength_diff: float) -> float:
        """
        Simple logistic from strength differential (legacy helper).
        If older tooling calls this, it still works.
        """
        # logistic scale tuned gently
        return 1.0 / (1.0 + math.exp(-0.9 * team_strength_diff))

    @staticmethod
    def calculate_puckline_probability(team_strength_diff: float, puckline: float = -1.5) -> float:
        """
        Legacy helper: rough conversion from strength diff to cover probability.
        """
        # harder to cover -1.5, easier to cover +1.5
        line_adj = 0.35 if puckline < 0 else -0.20
        base = 1.0 / (1.0 + math.exp(-0.85 * (team_strength_diff + line_adj)))
        return float(max(0.01, min(0.99, base)))

    # ----------------------------
    # Internal vote/prob collection
    # ----------------------------

    def _collect_moneyline_votes(
        self,
        home_team: str,
        away_team: str,
        features: Dict[str, float],
    ) -> Tuple[Dict[str, str], Dict[str, float], Dict[str, Any]]:
        votes: Dict[str, str] = {}
        probs_home: Dict[str, float] = {}
        raw: Dict[str, Any] = {}

        # Power model
        if self.power is not None:
            out = self._safe_call(self.power, ["predict_moneyline", "predict_game", "predict"], home_team, away_team, features)
            raw["power"] = out
            p = self._extract_home_prob(out)
            if p is not None:
                probs_home["power"] = p
                votes["power"] = "HOME" if p >= 0.5 else "AWAY"

        # Similar games model
        if self.similar is not None:
            out = self._safe_call(self.similar, ["predict_moneyline", "predict_game", "predict"], home_team, away_team, features)
            raw["similar"] = out
            p = self._extract_home_prob(out)
            if p is not None:
                probs_home["similar"] = p
                votes["similar"] = "HOME" if p >= 0.5 else "AWAY"

        # Decision tree model
        if self.tree is not None:
            out = self._safe_call(self.tree, ["predict_moneyline", "predict_game", "predict"], home_team, away_team, features)
            raw["tree"] = out
            p = self._extract_home_prob(out)
            if p is not None:
                probs_home["tree"] = p
                votes["tree"] = "HOME" if p >= 0.5 else "AWAY"
            else:
                # fallback: if tree returns label+confidence
                lbl, conf = self._extract_label_conf(out)
                if lbl is not None and conf is not None:
                    if lbl.upper() in ("HOME", home_team.upper()):
                        probs_home["tree"] = conf
                        votes["tree"] = "HOME"
                    elif lbl.upper() in ("AWAY", away_team.upper()):
                        probs_home["tree"] = 1.0 - conf
                        votes["tree"] = "AWAY"

        return votes, probs_home, raw

    def _collect_spread_votes(
        self,
        home_team: str,
        away_team: str,
        features: Dict[str, float],
        line_home: float,
        line_away: float,
    ) -> Tuple[Dict[str, str], Dict[str, float], Dict[str, Any]]:
        votes: Dict[str, str] = {}
        probs_home_cover: Dict[str, float] = {}
        raw: Dict[str, Any] = {}

        # Power model
        if self.power is not None:
            out = self._safe_call(self.power, ["predict_spread", "predict_puckline", "predict_game"], home_team, away_team, features, line_home, line_away)
            raw["power"] = out
            p = self._extract_home_cover_prob(out)
            if p is not None:
                probs_home_cover["power"] = p
                votes["power"] = f"HOME {line_home:+.1f}" if p >= 0.5 else f"AWAY {line_away:+.1f}"

        # Similar model
        if self.similar is not None:
            out = self._safe_call(self.similar, ["predict_spread", "predict_puckline", "predict_game"], home_team, away_team, features, line_home, line_away)
            raw["similar"] = out
            p = self._extract_home_cover_prob(out)
            if p is not None:
                probs_home_cover["similar"] = p
                votes["similar"] = f"HOME {line_home:+.1f}" if p >= 0.5 else f"AWAY {line_away:+.1f}"

        # Tree model
        if self.tree is not None:
            out = self._safe_call(self.tree, ["predict_spread", "predict_puckline", "predict_game"], home_team, away_team, features, line_home, line_away)
            raw["tree"] = out
            p = self._extract_home_cover_prob(out)
            if p is not None:
                probs_home_cover["tree"] = p
                votes["tree"] = f"HOME {line_home:+.1f}" if p >= 0.5 else f"AWAY {line_away:+.1f}"
            else:
                lbl, conf = self._extract_label_conf(out)
                if lbl is not None and conf is not None:
                    # interpret lbl as which side covers
                    if "HOME" in lbl.upper():
                        probs_home_cover["tree"] = conf
                        votes["tree"] = f"HOME {line_home:+.1f}"
                    elif "AWAY" in lbl.upper():
                        probs_home_cover["tree"] = 1.0 - conf
                        votes["tree"] = f"AWAY {line_away:+.1f}"

        return votes, probs_home_cover, raw

    # ----------------------------
    # Expected goals (for totals)
    # ----------------------------

    def _expected_goals(self, home_team: str, away_team: str, features: Dict[str, float]) -> Tuple[float, float, str]:
        """
        Try to pull expected goals from a model if available. Otherwise compute from features.

        If your models provide something like:
          {"home_xg": 3.1, "away_xg": 2.8}
        we'll use it.

        Fallback uses feature proxies:
          xgf_total_proxy, xgf_diff, home_advantage, gsax_diff, pace_proxy
        """
        # try power model first
        for model_name, model in (("power", self.power), ("similar", self.similar), ("tree", self.tree)):
            if model is None:
                continue
            out = self._safe_call(model, ["predict_expected_goals", "predict_xg", "expected_goals"], home_team, away_team, features)
            if isinstance(out, dict):
                hxg = out.get("home_xg")
                axg = out.get("away_xg")
                if hxg is not None and axg is not None:
                    return float(hxg), float(axg), f"{model_name}.method"

        # fallback computation
        # baseline total around modern NHL scoring
        base_total = 6.1

        xgf_total = float(features.get("xgf_total_proxy", base_total))
        # gently pull total toward xgf_total_proxy if present
        total = 0.65 * base_total + 0.35 * xgf_total

        # pace tweak (very light)
        pace = float(features.get("pace_proxy", 50.0))
        total += (pace - 50.0) * 0.01  # small

        # split total between teams using xgf_diff and home_advantage
        xgf_diff = float(features.get("xgf_diff", features.get("xgf_diff", 0.0))) if "xgf_diff" in features else float(features.get("xgf_diff", 0.0))
        # if you used the newer feature file, it's "xgf_diff"; if older, maybe "xg_diff"
        if "xgf_diff" in features:
            strength = float(features.get("xgf_diff", 0.0))
        elif "xg_diff" in features:
            strength = float(features.get("xg_diff", 0.0))
        else:
            strength = 0.0

        home_adv = float(features.get("home_advantage", 0.25))
        goalie = float(features.get("gsax_diff", 0.0))

        # distribute: more strength/home_adv -> more home share
        share = 0.5 + 0.06 * strength + 0.05 * home_adv + 0.02 * goalie
        share = self._clamp(share, 0.35, 0.65)

        home_xg = total * share
        away_xg = total - home_xg

        # clamp sane ranges
        home_xg = self._clamp(home_xg, 1.2, 5.5)
        away_xg = self._clamp(away_xg, 1.2, 5.5)

        return float(home_xg), float(away_xg), "feature_proxy"

    # ----------------------------
    # Parsing helpers (robust to different model outputs)
    # ----------------------------

    @staticmethod
    def _safe_call(model: Any, method_names: List[str], *args) -> Any:
        for name in method_names:
            if hasattr(model, name):
                fn = getattr(model, name)
                try:
                    return fn(*args)
                except TypeError:
                    # allow models that accept fewer args
                    try:
                        return fn(*args[:2])
                    except Exception:
                        continue
                except Exception:
                    continue
        return None

    @staticmethod
    def _extract_home_prob(out: Any) -> Optional[float]:
        if not isinstance(out, dict):
            return None
        for k in ("home_win_prob", "p_home", "home_prob", "prob_home", "win_prob_home"):
            if k in out and out[k] is not None:
                try:
                    return float(out[k])
                except Exception:
                    pass
        return None

    @staticmethod
    def _extract_home_cover_prob(out: Any) -> Optional[float]:
        if not isinstance(out, dict):
            return None
        for k in ("home_cover_prob", "p_home_cover", "home_spread_prob", "prob_home_cover"):
            if k in out and out[k] is not None:
                try:
                    return float(out[k])
                except Exception:
                    pass
        return None

    @staticmethod
    def _extract_label_conf(out: Any) -> Tuple[Optional[str], Optional[float]]:
        if not isinstance(out, dict):
            return None, None
        lbl = out.get("prediction") or out.get("pick") or out.get("label")
        conf = out.get("confidence") or out.get("prob") or out.get("p")
        try:
            conf_val = float(conf) if conf is not None else None
        except Exception:
            conf_val = None
        return (str(lbl) if lbl is not None else None), conf_val

    # ----------------------------
    # Output builder
    # ----------------------------

    def _make_bet_result(
        self,
        bet_type: str,
        pick: str,
        prob: float,
        market_odds: Optional[float],
        details: Dict[str, Any],
    ) -> BetResult:
        prob = float(prob)
        prob = self._clamp(prob, 0.001, 0.999)
        fair = prob_to_american(prob)

        implied = edge = ev = None
        if market_odds is not None:
            implied = american_to_implied_prob(float(market_odds))
            edge = prob - implied
            ev = expected_value_per_1_risk(prob, float(market_odds))

        return BetResult(
            bet_type=bet_type,
            pick=pick,
            prob=prob,
            fair_odds=fair,
            market_odds=market_odds,
            implied_prob=implied,
            edge=edge,
            ev_per_1=ev,
            details=details,
        )

    @staticmethod
    def _avg_prob_or_default(probs: Dict[str, float], default: float = 0.5) -> float:
        if not probs:
            return default
        return sum(probs.values()) / float(len(probs))

    @staticmethod
    def _convergence_count(votes: Dict[str, str]) -> int:
        if not votes:
            return 0
        counts: Dict[str, int] = {}
        for v in votes.values():
            counts[v] = counts.get(v, 0) + 1
        return max(counts.values())

    @staticmethod
    def _clamp(x: float, lo: float, hi: float) -> float:
        return float(max(lo, min(hi, x)))
