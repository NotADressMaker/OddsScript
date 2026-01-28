# lib/nhl_feature_engineering.py
"""
NHL Feature Engineering Module
Generates advanced features for NHL prediction models.

Design goals:
- Stable defaults (won't crash if stats missing)
- Consistent naming (diff features + optional raw features)
- Adds totals-friendly features (pace / expected total proxies)
"""

from typing import Dict, Any


class NHLFeatureEngineering:
    @staticmethod
    def create_game_features(
        home_data: Dict[str, Any],
        away_data: Dict[str, Any],
        home_rest_days: int = 1,
        away_rest_days: int = 1,
        home_travel_zones: int = 0,
        away_travel_zones: int = 0,
        home_goalie_gsax: float = 0.0,
        away_goalie_gsax: float = 0.0,
        referee_goal_modifier: float = 1.0,
        referee_home_bias: float = 0.0,
        *,
        include_raw: bool = True,
    ) -> Dict[str, float]:
        """
        Create a feature dictionary for NHL game prediction.

        Args:
            home_data: Dict with home team stats (xgf, xga, corsi_pct, fenwick_pct, pp_pct, pk_pct, etc.)
            away_data: Dict with away team stats
            home_rest_days, away_rest_days: Rest days (0 = B2B, 1 = normal, etc.)
            home_travel_zones, away_travel_zones: Time zones crossed
            home_goalie_gsax, away_goalie_gsax: Starting goalie GSAx (Goals Saved Above Expected)
            referee_goal_modifier: Multiplicative total-goal adjustment driven by referee tendencies
            referee_home_bias: Home-leaning ref impact applied to goal share
            include_raw: If True, include some non-differential features too (useful for trees)

        Returns:
            Dict[str, float] of engineered features.
        """
        f: Dict[str, float] = {}

        # ----------------------------
        # Pull inputs with defaults
        # ----------------------------
        home_xgf = float(home_data.get("xgf", 0.0))
        away_xgf = float(away_data.get("xgf", 0.0))

        home_xga = float(home_data.get("xga", 0.0))
        away_xga = float(away_data.get("xga", 0.0))

        home_corsi = float(home_data.get("corsi_pct", 50.0))
        away_corsi = float(away_data.get("corsi_pct", 50.0))

        home_fenwick = float(home_data.get("fenwick_pct", 50.0))
        away_fenwick = float(away_data.get("fenwick_pct", 50.0))

        home_pp = float(home_data.get("pp_pct", 20.0))
        away_pp = float(away_data.get("pp_pct", 20.0))

        home_pk = float(home_data.get("pk_pct", 80.0))
        away_pk = float(away_data.get("pk_pct", 80.0))

        home_form = float(home_data.get("recent_win_pct", 0.5))
        away_form = float(away_data.get("recent_win_pct", 0.5))

        home_hd = float(home_data.get("high_danger_xg_pct", 50.0))
        away_hd = float(away_data.get("high_danger_xg_pct", 50.0))

        home_rush_reb = float(home_data.get("rush_rebound_pct", 0.0))
        away_rush_reb = float(away_data.get("rush_rebound_pct", 0.0))

        pdo_home = float(home_data.get("pdo", 100.0))
        pdo_away = float(away_data.get("pdo", 100.0))

        # ----------------------------
        # Core differentials
        # ----------------------------
        f["xgf_diff"] = home_xgf - away_xgf
        f["xga_diff"] = home_xga - away_xga
        f["corsi_diff"] = home_corsi - away_corsi
        f["fenwick_diff"] = home_fenwick - away_fenwick

        # Totals-friendly proxies
        # (Simple proxies: use as features, not as literal expected goals)
        f["xgf_total_proxy"] = home_xgf + away_xgf
        f["xga_total_proxy"] = home_xga + away_xga
        f["pace_proxy"] = (home_corsi + away_corsi) / 2.0  # shot share isn't pace, but correlates loosely with control/flow
        f["shot_share_abs_gap"] = abs(home_corsi - away_corsi)

        # Goaltending
        f["gsax_diff"] = float(home_goalie_gsax) - float(away_goalie_gsax)

        # Referee tendencies
        f["referee_goal_modifier"] = float(referee_goal_modifier)
        f["referee_home_bias"] = float(referee_home_bias)

        # ----------------------------
        # Special teams
        # ----------------------------
        f["pp_diff"] = home_pp - away_pp
        f["pk_diff"] = home_pk - away_pk
        # Matchup-style feature (keep, but name it clearly)
        f["st_matchup_pp_minus_pk"] = home_pp - away_pk

        # ----------------------------
        # Situational / rest / travel
        # ----------------------------
        f["rest_diff"] = float(home_rest_days - away_rest_days)

        # Travel penalties (keep both and a combined diff)
        # Penalty per time zone crossed (tunable)
        travel_weight = -0.15
        f["travel_penalty_home"] = float(home_travel_zones) * travel_weight
        f["travel_penalty_away"] = float(away_travel_zones) * travel_weight
        f["travel_diff"] = float(home_travel_zones - away_travel_zones) * travel_weight

        # Home-ice: since this function is called with home/away already, default to on.
        # You can override by passing home_data={"is_home": False} for neutral sites if needed.
        is_home = bool(home_data.get("is_home", True))
        f["home_advantage"] = 0.25 if is_home else 0.0

        # Form
        f["form_diff"] = home_form - away_form

        # High-danger & rush/rebound
        f["high_danger_diff"] = home_hd - away_hd
        f["rush_rebound_diff"] = home_rush_reb - away_rush_reb

        # PDO regression expectation:
        # If home PDO > 100, expect slight negative regression; if away PDO > 100, expect away negative regression
        f["pdo_regression"] = (pdo_home - 100.0) * -0.03 + (pdo_away - 100.0) * 0.03
        f["pdo_diff"] = pdo_home - pdo_away

        # ----------------------------
        # Optional raw features (useful for trees / interpretation)
        # ----------------------------
        if include_raw:
            f["home_form"] = home_form
            f["away_form"] = away_form
            f["home_pp"] = home_pp
            f["away_pp"] = away_pp
            f["home_pk"] = home_pk
            f["away_pk"] = away_pk
            f["home_corsi"] = home_corsi
            f["away_corsi"] = away_corsi
            f["home_fenwick"] = home_fenwick
            f["away_fenwick"] = away_fenwick
            f["home_goalie_gsax"] = float(home_goalie_gsax)
            f["away_goalie_gsax"] = float(away_goalie_gsax)

        return f
