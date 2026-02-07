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
                New optional keys: shot_attempts_per_60, rush_chances_per_60, neutral_zone_transition_pct,
                pp_opportunities_per_game, goalie_sv_pct, goalie_hd_sv_pct, goalie_md_sv_pct, goalie_ld_sv_pct
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

        # PP/PK efficiency features
        home_pp_opp = float(home_data.get("pp_opportunities_per_game", 3.0))
        away_pp_opp = float(away_data.get("pp_opportunities_per_game", 3.0))
        # Estimated PP goals: opportunities * (team PP% + opp PK allow %) / 2
        home_pp_xg = home_pp_opp * ((home_pp / 100.0) + (1.0 - away_pk / 100.0)) / 2.0
        away_pp_xg = away_pp_opp * ((away_pp / 100.0) + (1.0 - home_pk / 100.0)) / 2.0
        f["pp_xg_total"] = home_pp_xg + away_pp_xg
        f["pp_xg_diff"] = home_pp_xg - away_pp_xg

        # ----------------------------
        # Pace & Tempo features
        # ----------------------------
        home_sa60 = float(home_data.get("shot_attempts_per_60", 60.0))
        away_sa60 = float(away_data.get("shot_attempts_per_60", 60.0))
        home_rush60 = float(home_data.get("rush_chances_per_60", 5.0))
        away_rush60 = float(away_data.get("rush_chances_per_60", 5.0))
        home_nz = float(home_data.get("neutral_zone_transition_pct", 50.0))
        away_nz = float(away_data.get("neutral_zone_transition_pct", 50.0))

        avg_sa60 = (home_sa60 + away_sa60) / 2.0
        avg_rush60 = (home_rush60 + away_rush60) / 2.0
        avg_nz = (home_nz + away_nz) / 2.0

        f["avg_shot_attempts_per_60"] = avg_sa60
        f["avg_rush_chances_per_60"] = avg_rush60
        f["avg_nz_transition_pct"] = avg_nz
        f["sa60_diff"] = home_sa60 - away_sa60
        f["rush60_diff"] = home_rush60 - away_rush60
        f["nz_transition_diff"] = home_nz - away_nz

        # Composite pace score
        sa_score = (avg_sa60 - 60.0) / 10.0
        rush_score = (avg_rush60 - 5.0) / 2.0
        nz_score = (avg_nz - 50.0) / 10.0
        f["pace_score"] = sa_score * 0.45 + rush_score * 0.30 + nz_score * 0.25

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

        # B2B and rest flags (binary features for tree models)
        f["home_is_b2b"] = 1.0 if home_rest_days == 0 else 0.0
        f["away_is_b2b"] = 1.0 if away_rest_days == 0 else 0.0
        f["home_well_rested"] = 1.0 if home_rest_days >= 3 else 0.0
        f["away_well_rested"] = 1.0 if away_rest_days >= 3 else 0.0

        # Combined rest-travel modifier
        # B2B on road with travel = major penalty
        home_rest_score = 0.0
        if home_rest_days == 0:
            home_rest_score -= 0.20
            if home_travel_zones >= 2:
                home_rest_score -= 0.15
        elif home_rest_days >= 3:
            home_rest_score += 0.12
        away_rest_score = 0.0
        if away_rest_days == 0:
            away_rest_score -= 0.20
            if away_travel_zones >= 2:
                away_rest_score -= 0.15
        elif away_rest_days >= 3:
            away_rest_score += 0.12
        f["rest_travel_score_home"] = home_rest_score
        f["rest_travel_score_away"] = away_rest_score
        f["rest_travel_diff"] = home_rest_score - away_rest_score

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
        # Goalie quality features
        # ----------------------------
        home_goalie_sv = float(home_data.get("goalie_sv_pct", 0.905))
        away_goalie_sv = float(away_data.get("goalie_sv_pct", 0.905))
        home_goalie_hd = float(home_data.get("goalie_hd_sv_pct", 0.820))
        away_goalie_hd = float(away_data.get("goalie_hd_sv_pct", 0.820))

        f["goalie_sv_diff"] = home_goalie_sv - away_goalie_sv
        f["goalie_hd_sv_diff"] = home_goalie_hd - away_goalie_hd

        # Adjusted goalie quality (weighted by zone)
        home_goalie_md = float(home_data.get("goalie_md_sv_pct", 0.910))
        away_goalie_md = float(away_data.get("goalie_md_sv_pct", 0.910))
        home_goalie_ld = float(home_data.get("goalie_ld_sv_pct", 0.980))
        away_goalie_ld = float(away_data.get("goalie_ld_sv_pct", 0.980))
        home_adj_sv = home_goalie_hd * 0.45 + home_goalie_md * 0.30 + home_goalie_ld * 0.25
        away_adj_sv = away_goalie_hd * 0.45 + away_goalie_md * 0.30 + away_goalie_ld * 0.25
        f["goalie_adj_sv_diff"] = home_adj_sv - away_adj_sv

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
            f["home_sa60"] = home_sa60
            f["away_sa60"] = away_sa60
            f["home_rush60"] = home_rush60
            f["away_rush60"] = away_rush60
            f["home_nz_pct"] = home_nz
            f["away_nz_pct"] = away_nz

        return f
