# lib/nhl_feature_engineering.py
"""
NHL Feature Engineering Module
Generates advanced features for NHL prediction models
"""

import math
from typing import Dict, List, Optional


class NHLFeatureEngineering:
    @staticmethod
    def create_game_features(
        home_data: Dict,
        away_data: Dict,
        home_rest_days: int = 1,
        away_rest_days: int = 1,
        home_travel_zones: int = 0,
        away_travel_zones: int = 0,
        home_goalie_gsax: float = 0.0,
        away_goalie_gsax: float = 0.0
    ) -> Dict[str, float]:
        """
        Create a feature dictionary for NHL game prediction

        Args:
            home_data: Dict with home team stats (xgf, xga, corsi, etc.)
            away_data: Dict with away team stats
            home_rest_days, away_rest_days: Rest days (0 = B2B, 1 = normal, etc.)
            home_travel_zones, away_travel_zones: Time zones crossed
            home_goalie_gsax, away_goalie_gsax: Starting goalie GSAx

        Returns:
            Dict of engineered features
        """
        features: Dict[str, float] = {}

        # Core differentials
        features['xg_diff'] = float(home_data.get('xgf', 0)) - float(away_data.get('xgf', 0))
        features['xga_diff'] = float(home_data.get('xga', 0)) - float(away_data.get('xga', 0))
        features['corsi_diff'] = float(home_data.get('corsi_pct', 50)) - float(away_data.get('corsi_pct', 50))
        features['fenwick_diff'] = float(home_data.get('fenwick_pct', 50)) - float(away_data.get('fenwick_pct', 50))

        # Goaltending
        features['gsax_diff'] = float(home_goalie_gsax) - float(away_goalie_gsax)

        # Special teams (simple proxy: home PP minus away PK)
        features['pp_pk_diff'] = float(home_data.get('pp_pct', 20)) - float(away_data.get('pk_pct', 80))

        # Situational / rest / travel
        features['rest_diff'] = float(home_rest_days - away_rest_days)
        features['travel_penalty_home'] = float(home_travel_zones) * -0.15
        features['travel_penalty_away'] = float(away_travel_zones) * -0.15

        # Home-ice + recent form
        # Set home_data['is_home']=True when the team is at home.
        features['home_advantage'] = 0.25 if bool(home_data.get('is_home', False)) else 0.0
        features['home_form'] = float(home_data.get('recent_win_pct', 0.5))
        features['away_form'] = float(away_data.get('recent_win_pct', 0.5))

        # High-danger & rush/rebound bonuses
        features['high_danger_diff'] = (
            float(home_data.get('high_danger_xg_pct', 50)) -
            float(away_data.get('high_danger_xg_pct', 50))
        )
        features['rush_rebound_diff'] = (
            float(home_data.get('rush_rebound_pct', 0)) -
            float(away_data.get('rush_rebound_pct', 0))
        )

        # PDO regression expectation
        pdo_home = float(home_data.get('pdo', 100))
        pdo_away = float(away_data.get('pdo', 100))
        features['pdo_regression'] = (pdo_home - 100) * -0.03 + (pdo_away - 100) * 0.03

        return features
