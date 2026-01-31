#!/usr/bin/env python3
"""
Sport-Specific Feature Engineering

Helpers for creating features tailored to each sport.
"""

from typing import List, Dict, Optional, Tuple


class NBAFeatures:
    """NBA-specific feature engineering"""

    @staticmethod
    def create_rating_differential(team_off_rtg: float, team_def_rtg: float,
                                   opp_off_rtg: float, opp_def_rtg: float) -> float:
        """
        Calculate net rating differential

        Args:
            team_off_rtg: Team offensive rating (points per 100 possessions)
            team_def_rtg: Team defensive rating
            opp_off_rtg: Opponent offensive rating
            opp_def_rtg: Opponent defensive rating

        Returns:
            Net rating differential
        """
        team_net = team_off_rtg - team_def_rtg
        opp_net = opp_off_rtg - opp_def_rtg
        return team_net - opp_net

    @staticmethod
    def create_rest_advantage(team_days_rest: int, opp_days_rest: int) -> int:
        """Calculate rest days advantage"""
        return team_days_rest - opp_days_rest

    @staticmethod
    def create_pace_factor(team_pace: float, opp_pace: float) -> float:
        """Calculate average pace for the game"""
        return (team_pace + opp_pace) / 2

    @staticmethod
    def create_four_factors_score(efg_pct: float, tov_pct: float,
                                  orb_pct: float, ftr: float) -> float:
        """
        Dean Oliver's Four Factors score

        Args:
            efg_pct: Effective field goal percentage
            tov_pct: Turnover percentage
            orb_pct: Offensive rebound percentage
            ftr: Free throw rate

        Returns:
            Weighted four factors score
        """
        return (efg_pct * 0.40) - (tov_pct * 0.25) + (orb_pct * 0.20) + (ftr * 0.15)

    @staticmethod
    def create_four_factors_differential(team_efg_pct: float, team_tov_pct: float,
                                         team_orb_pct: float, team_ftr: float,
                                         opp_efg_pct: float, opp_tov_pct: float,
                                         opp_orb_pct: float, opp_ftr: float) -> float:
        """
        Calculate four factors differential between team and opponent

        Returns:
            Team four factors score minus opponent four factors score
        """
        team_score = NBAFeatures.create_four_factors_score(
            team_efg_pct, team_tov_pct, team_orb_pct, team_ftr
        )
        opp_score = NBAFeatures.create_four_factors_score(
            opp_efg_pct, opp_tov_pct, opp_orb_pct, opp_ftr
        )
        return team_score - opp_score


class NFLFeatures:
    """NFL-specific feature engineering"""

    @staticmethod
    def create_dvoa_differential(team_off_dvoa: float, team_def_dvoa: float,
                                 opp_off_dvoa: float, opp_def_dvoa: float) -> float:
        """Calculate DVOA differential"""
        team_total = team_off_dvoa - team_def_dvoa
        opp_total = opp_off_dvoa - opp_def_dvoa
        return team_total - opp_total

    @staticmethod
    def create_weather_factor(temperature: float, wind_speed: float,
                             precipitation: float) -> float:
        """
        Create weather impact factor

        Args:
            temperature: Temperature in Fahrenheit
            wind_speed: Wind speed in mph
            precipitation: 0-1 scale (0=none, 1=heavy)

        Returns:
            Weather factor (0=ideal, 1=terrible)
        """
        # Cold penalty
        temp_factor = 0
        if temperature < 32:
            temp_factor = (32 - temperature) / 50

        # Wind penalty
        wind_factor = max(0, (wind_speed - 10) / 30)

        # Combine factors
        weather = (temp_factor * 0.3) + (wind_factor * 0.4) + (precipitation * 0.3)
        return min(1.0, weather)

    @staticmethod
    def create_rest_advantage(team_days_rest: int, opp_days_rest: int) -> int:
        """Calculate rest advantage (important in NFL)"""
        return team_days_rest - opp_days_rest


class NHLFeatures:
    """NHL-specific feature engineering"""

    @staticmethod
    def create_expected_goals_differential(team_xgf_avg: float, team_xga_avg: float,
                                          opp_xgf_avg: float, opp_xga_avg: float) -> float:
        """Calculate expected goals differential"""
        team_xg_net = team_xgf_avg - team_xga_avg
        opp_xg_net = opp_xgf_avg - opp_xga_avg
        return team_xg_net - opp_xg_net

    @staticmethod
    def create_pdo_regression_factor(team_pdo: float, opp_pdo: float) -> float:
        """
        PDO regression factor (PDO tends to regress to 100)

        Args:
            team_pdo: Team PDO (save% + shooting%)
            opp_pdo: Opponent PDO

        Returns:
            Expected regression impact
        """
        team_regression = (100 - team_pdo) * 0.3
        opp_regression = (100 - opp_pdo) * 0.3
        return team_regression - opp_regression

    @staticmethod
    def create_goalie_advantage(team_gsax: float, opp_gsax: float) -> float:
        """
        Goals Saved Above Expected advantage

        Args:
            team_gsax: Team goalie GSAx
            opp_gsax: Opponent goalie GSAx

        Returns:
            Goalie advantage
        """
        return team_gsax - opp_gsax


class MLBFeatures:
    """MLB-specific feature engineering"""

    @staticmethod
    def create_pitcher_quality_differential(team_pitcher_era: float,
                                           team_pitcher_whip: float,
                                           opp_pitcher_era: float,
                                           opp_pitcher_whip: float) -> float:
        """
        Calculate pitcher quality differential

        Lower is better for ERA and WHIP, so we invert
        """
        team_quality = (1 / team_pitcher_era) + (1 / team_pitcher_whip)
        opp_quality = (1 / opp_pitcher_era) + (1 / opp_pitcher_whip)
        return team_quality - opp_quality

    @staticmethod
    def create_park_adjusted_runs(team_runs: float, park_factor: float) -> float:
        """
        Adjust runs for park factor

        Args:
            team_runs: Team runs per game
            park_factor: Park factor (1.0=neutral, >1=hitter friendly, <1=pitcher friendly)

        Returns:
            Park-adjusted runs
        """
        return team_runs * park_factor

    @staticmethod
    def create_weather_factor(temperature: float, wind_direction: str,
                             wind_speed: float) -> float:
        """
        MLB weather impact

        Args:
            temperature: Temperature in Fahrenheit
            wind_direction: 'in', 'out', 'cross'
            wind_speed: Wind speed in mph

        Returns:
            Run scoring adjustment factor
        """
        # Warm weather increases scoring
        temp_factor = 1.0
        if temperature > 80:
            temp_factor = 1.0 + ((temperature - 80) / 200)
        elif temperature < 60:
            temp_factor = 1.0 - ((60 - temperature) / 200)

        # Wind impact
        wind_factor = 1.0
        if wind_direction == 'out':
            wind_factor = 1.0 + (wind_speed / 100)
        elif wind_direction == 'in':
            wind_factor = 1.0 - (wind_speed / 100)

        return temp_factor * wind_factor


class CollegeFootballFeatures:
    """College Football specific features"""

    @staticmethod
    def create_conference_adjusted_rating(team_rating: float,
                                         conference_strength: float) -> float:
        """
        Adjust rating for conference strength

        Args:
            team_rating: Team rating (SP+, FPI, etc.)
            conference_strength: Conference rating (1-5, 5=strongest)

        Returns:
            Conference-adjusted rating
        """
        return team_rating * (conference_strength / 3.0)

    @staticmethod
    def create_rivalry_factor(is_rivalry: bool, rating_differential: float) -> float:
        """
        Rivalry games tend to be closer

        Args:
            is_rivalry: True if rivalry game
            rating_differential: Difference in team ratings

        Returns:
            Adjusted rating differential
        """
        if is_rivalry:
            # Compress the spread in rivalry games
            return rating_differential * 0.6
        return rating_differential

    @staticmethod
    def create_matchup_factor(team_conference: str, opp_conference: str,
                             power_five_conferences: List[str]) -> float:
        """
        Conference matchup factor

        Args:
            team_conference: Team's conference
            opp_conference: Opponent's conference
            power_five_conferences: List of Power 5 conferences

        Returns:
            Matchup factor
        """
        team_p5 = team_conference in power_five_conferences
        opp_p5 = opp_conference in power_five_conferences

        if team_p5 and opp_p5:
            return 1.0  # Even matchup
        elif team_p5 and not opp_p5:
            return 1.2  # P5 vs G5
        elif not team_p5 and opp_p5:
            return 0.8  # G5 vs P5
        else:
            return 1.0  # G5 vs G5


class CollegeBasketballFeatures:
    """College Basketball specific features"""

    @staticmethod
    def create_efficiency_margin(team_off_eff: float, team_def_eff: float,
                                opp_off_eff: float, opp_def_eff: float) -> float:
        """Calculate efficiency margin (KenPom style)"""
        team_margin = team_off_eff - team_def_eff
        opp_margin = opp_off_eff - opp_def_eff
        return team_margin - opp_margin

    @staticmethod
    def create_tempo_differential(team_tempo: float, opp_tempo: float) -> float:
        """Calculate tempo differential"""
        return team_tempo - opp_tempo

    @staticmethod
    def create_tournament_experience_factor(games_played: int,
                                           final_four_appearances: int,
                                           championship_appearances: int) -> float:
        """
        Tournament experience factor

        Args:
            games_played: Total tournament games played
            final_four_appearances: Number of Final Four appearances
            championship_appearances: Number of championship game appearances

        Returns:
            Experience score
        """
        return (games_played * 0.1) + (final_four_appearances * 2) + (championship_appearances * 5)

    @staticmethod
    def create_seed_upset_factor(higher_seed: int, lower_seed: int) -> float:
        """
        Historical upset probability based on seed differential

        Args:
            higher_seed: Higher seed number (e.g., 1, 2)
            lower_seed: Lower seed number (e.g., 15, 16)

        Returns:
            Upset difficulty factor
        """
        seed_diff = lower_seed - higher_seed

        # Historical upset rates
        if seed_diff == 15:  # 1 vs 16
            return 0.01
        elif seed_diff == 7:  # 5 vs 12
            return 0.36
        elif seed_diff == 1:  # 8 vs 9
            return 0.48
        else:
            # Linear interpolation
            return min(0.50, seed_diff * 0.05)


class SoccerFeatures:
    """Soccer-specific feature engineering"""

    @staticmethod
    def create_goal_expectancy(team_xg_avg: float, opp_def_xg_avg: float) -> float:
        """
        Expected goals for team in this match

        Args:
            team_xg_avg: Team's average xG per game
            opp_def_xg_avg: Opponent's average xG conceded per game

        Returns:
            Expected goals for this match
        """
        return (team_xg_avg + opp_def_xg_avg) / 2

    @staticmethod
    def create_btts_probability(team_gf_avg: float, team_ga_avg: float,
                               opp_gf_avg: float, opp_ga_avg: float,
                               team_clean_sheet_pct: float,
                               opp_clean_sheet_pct: float) -> float:
        """
        Both Teams To Score probability

        Args:
            team_gf_avg: Team goals for average
            team_ga_avg: Team goals against average
            opp_gf_avg: Opponent goals for average
            opp_ga_avg: Opponent goals against average
            team_clean_sheet_pct: Team clean sheet percentage
            opp_clean_sheet_pct: Opponent clean sheet percentage

        Returns:
            BTTS probability
        """
        # Probability team scores
        team_scores = (1 - opp_clean_sheet_pct) * (team_gf_avg / 1.5)
        team_scores = min(0.95, team_scores)

        # Probability opponent scores
        opp_scores = (1 - team_clean_sheet_pct) * (opp_gf_avg / 1.5)
        opp_scores = min(0.95, opp_scores)

        # Both score
        return team_scores * opp_scores

    @staticmethod
    def create_league_adjustment(base_value: float, league: str) -> float:
        """
        Adjust for league characteristics

        Args:
            base_value: Base predicted value
            league: League name

        Returns:
            League-adjusted value
        """
        # Different leagues have different characteristics
        league_factors = {
            'epl': 1.0,         # English Premier League (baseline)
            'bundesliga': 1.15,  # Higher scoring
            'serie_a': 0.90,    # Lower scoring, more defensive
            'la_liga': 1.05,    # Slightly higher scoring
            'ligue_1': 0.95,    # Slightly lower scoring
        }

        factor = league_factors.get(league.lower(), 1.0)
        return base_value * factor


class HorseRacingFeatures:
    """Horse Racing specific features"""

    @staticmethod
    def create_speed_figure_trend(last_3_figures: List[float]) -> float:
        """
        Calculate speed figure trend (improving/declining)

        Args:
            last_3_figures: Last 3 speed figures (most recent first)

        Returns:
            Trend score (positive=improving, negative=declining)
        """
        if len(last_3_figures) < 3:
            return 0.0

        # Calculate trend
        trend = (last_3_figures[0] - last_3_figures[2]) / 2
        return trend

    @staticmethod
    def create_post_position_factor(post_position: int, field_size: int,
                                   distance_furlongs: float) -> float:
        """
        Post position advantage/disadvantage

        Args:
            post_position: Post position (1-12+)
            field_size: Number of horses in race
            distance_furlongs: Race distance

        Returns:
            Post position factor (1.0=neutral, <1=disadvantage, >1=advantage)
        """
        # Inside posts (1-3) are generally good for sprints
        if distance_furlongs <= 7:
            if post_position <= 3:
                return 1.1
            elif post_position >= field_size - 2:
                return 0.9
        # Outside posts have advantage in routes (more room)
        else:
            if post_position >= 5:
                return 1.05
            elif post_position == 1:
                return 0.95

        return 1.0

    @staticmethod
    def create_jockey_trainer_combo_factor(jockey_win_pct: float,
                                          trainer_win_pct: float,
                                          combo_wins: int,
                                          combo_starts: int) -> float:
        """
        Jockey-Trainer combination factor

        Args:
            jockey_win_pct: Jockey overall win percentage
            trainer_win_pct: Trainer overall win percentage
            combo_wins: Wins together
            combo_starts: Starts together

        Returns:
            Combo factor
        """
        # Individual factors
        base = (jockey_win_pct + trainer_win_pct) / 2

        # Combo bonus
        if combo_starts >= 10:
            combo_pct = combo_wins / combo_starts
            # If combo is better than individual averages, bonus
            if combo_pct > base:
                return base * 1.1

        return base

    @staticmethod
    def create_surface_suitability(horse_dirt_record: Tuple[int, int],
                                   horse_turf_record: Tuple[int, int],
                                   surface: str) -> float:
        """
        Surface suitability factor

        Args:
            horse_dirt_record: (wins, starts) on dirt
            horse_turf_record: (wins, starts) on turf
            surface: 'dirt' or 'turf'

        Returns:
            Surface suitability score
        """
        if surface == 'dirt' and horse_dirt_record[1] > 0:
            return horse_dirt_record[0] / horse_dirt_record[1]
        elif surface == 'turf' and horse_turf_record[1] > 0:
            return horse_turf_record[0] / horse_turf_record[1]
        return 0.15  # Default win rate if no experience


# Convenient access dictionary
SPORT_FEATURES = {
    'nba': NBAFeatures,
    'nfl': NFLFeatures,
    'nhl': NHLFeatures,
    'mlb': MLBFeatures,
    'cfb': CollegeFootballFeatures,
    'cbb': CollegeBasketballFeatures,
    'soccer': SoccerFeatures,
    'horse_racing': HorseRacingFeatures
}


def get_sport_features(sport: str):
    """
    Get sport-specific feature engineering class

    Args:
        sport: Sport name ('nba', 'nfl', etc.)

    Returns:
        Sport feature engineering class

    Example:
        >>> features = get_sport_features('nba')
        >>> rating_diff = features.create_rating_differential(112, 108, 110, 109)
    """
    sport_lower = sport.lower()
    if sport_lower not in SPORT_FEATURES:
        raise ValueError(f"Unknown sport: {sport}. Available: {list(SPORT_FEATURES.keys())}")

    return SPORT_FEATURES[sport_lower]
