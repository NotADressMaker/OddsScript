#!/usr/bin/env python3
"""
Sport-Specific ML Models

Pre-configured machine learning models tailored for each sport,
integrated with sport-specific analytics.
"""

from typing import List, Dict, Optional, Tuple
from lib.model_builder import Model, ModelBuilder, DataHelper
from lib.ml_models import RandomForest, DecisionTree, NeuralNetwork


class NBAModels:
    """Machine learning models for NBA betting"""

    @staticmethod
    def game_winner_model() -> Model:
        """
        Predict NBA game winners

        Expected features:
        - team_offensive_rating
        - team_defensive_rating
        - opponent_offensive_rating
        - opponent_defensive_rating
        - home_court (1/0)
        - rest_days_team
        - rest_days_opponent
        - pace
        """
        return (Model()
                .named("NBA Game Winner")
                .for_classification()
                .using_random_forest(n_trees=150, max_depth=12)
                .with_features([
                    'team_offensive_rating',
                    'team_defensive_rating',
                    'opponent_offensive_rating',
                    'opponent_defensive_rating',
                    'home_court',
                    'rest_days_team',
                    'rest_days_opponent',
                    'pace'
                ])
                .with_normalization('standard'))

    @staticmethod
    def spread_model() -> Model:
        """
        Predict NBA spread coverage

        Expected features:
        - rating_differential (team - opponent)
        - spread
        - home_court
        - rest_advantage (team_rest - opp_rest)
        - pace_differential
        """
        return (Model()
                .named("NBA Spread Coverage")
                .for_classification()
                .using_random_forest(n_trees=200, max_depth=15)
                .with_features([
                    'rating_differential',
                    'spread',
                    'home_court',
                    'rest_advantage',
                    'pace_differential'
                ])
                .with_normalization('standard'))

    @staticmethod
    def total_points_model() -> Model:
        """
        Predict NBA total points

        Expected features:
        - team_ppg
        - opponent_ppg
        - pace
        - pace_differential
        - defensive_efficiency_combined
        - offensive_efficiency_combined
        - team_offensive_rating
        - opponent_offensive_rating
        - team_defensive_rating
        - opponent_defensive_rating
        - home_court
        - rest_advantage
        """
        return (Model()
                .named("NBA Total Points")
                .for_regression()
                .using_random_forest(n_trees=150, max_depth=18)
                .with_features([
                    'team_ppg',
                    'opponent_ppg',
                    'pace',
                    'pace_differential',
                    'defensive_efficiency_combined',
                    'offensive_efficiency_combined',
                    'team_offensive_rating',
                    'opponent_offensive_rating',
                    'team_defensive_rating',
                    'opponent_defensive_rating',
                    'home_court',
                    'rest_advantage'
                ])
                .with_normalization('standard'))

    @staticmethod
    def player_points_model() -> Model:
        """
        Predict player points

        Expected features:
        - player_ppg
        - minutes_avg
        - usage_rate
        - matchup_defensive_rating
        - home_court
        """
        return (Model()
                .named("NBA Player Points")
                .for_regression()
                .using_random_forest(n_trees=100, max_depth=15)
                .with_features([
                    'player_ppg',
                    'minutes_avg',
                    'usage_rate',
                    'matchup_defensive_rating',
                    'home_court'
                ])
                .with_normalization('minmax'))


class NFLModels:
    """Machine learning models for NFL betting"""

    @staticmethod
    def game_winner_model() -> Model:
        """
        Predict NFL game winners

        Expected features:
        - team_offensive_dvoa
        - team_defensive_dvoa
        - opponent_offensive_dvoa
        - opponent_defensive_dvoa
        - home_field (1/0)
        - weather_factor
        - rest_days_team
        - rest_days_opponent
        """
        return (Model()
                .named("NFL Game Winner")
                .for_classification()
                .using_random_forest(n_trees=180, max_depth=14)
                .with_features([
                    'team_offensive_dvoa',
                    'team_defensive_dvoa',
                    'opponent_offensive_dvoa',
                    'opponent_defensive_dvoa',
                    'home_field',
                    'weather_factor',
                    'rest_days_team',
                    'rest_days_opponent'
                ])
                .with_normalization('standard'))

    @staticmethod
    def spread_model() -> Model:
        """
        Predict NFL spread coverage

        Expected features:
        - dvoa_differential
        - spread
        - home_field
        - weather_factor
        - rest_advantage
        """
        return (Model()
                .named("NFL Spread Coverage")
                .for_classification()
                .using_random_forest(n_trees=200, max_depth=16)
                .with_features([
                    'dvoa_differential',
                    'spread',
                    'home_field',
                    'weather_factor',
                    'rest_advantage'
                ])
                .with_normalization('standard'))

    @staticmethod
    def total_points_model() -> Model:
        """
        Predict NFL total points

        Expected features:
        - team_ppg
        - opponent_ppg
        - team_yards_per_play
        - opponent_yards_per_play
        - weather_factor
        - pace
        """
        return (Model()
                .named("NFL Total Points")
                .for_regression()
                .using_random_forest(n_trees=150, max_depth=18)
                .with_features([
                    'team_ppg',
                    'opponent_ppg',
                    'team_yards_per_play',
                    'opponent_yards_per_play',
                    'weather_factor',
                    'pace'
                ])
                .with_normalization('standard'))


class NHLModels:
    """Machine learning models for NHL betting"""

    @staticmethod
    def game_winner_model() -> Model:
        """
        Predict NHL game winners

        Expected features:
        - team_goals_for_avg
        - team_goals_against_avg
        - opponent_goals_for_avg
        - opponent_goals_against_avg
        - team_corsi_for_pct
        - opponent_corsi_for_pct
        - team_save_pct
        - opponent_save_pct
        - home_ice (1/0)
        """
        return (Model()
                .named("NHL Game Winner")
                .for_classification()
                .using_random_forest(n_trees=150, max_depth=12)
                .with_features([
                    'team_goals_for_avg',
                    'team_goals_against_avg',
                    'opponent_goals_for_avg',
                    'opponent_goals_against_avg',
                    'team_corsi_for_pct',
                    'opponent_corsi_for_pct',
                    'team_save_pct',
                    'opponent_save_pct',
                    'home_ice'
                ])
                .with_normalization('standard'))

    @staticmethod
    def puck_line_model() -> Model:
        """
        Predict NHL puck line coverage (1.5 goals)

        Expected features:
        - expected_goals_differential
        - puck_line
        - home_ice
        - goalie_gsax_team
        - goalie_gsax_opponent
        """
        return (Model()
                .named("NHL Puck Line Coverage")
                .for_classification()
                .using_random_forest(n_trees=180, max_depth=14)
                .with_features([
                    'expected_goals_differential',
                    'puck_line',
                    'home_ice',
                    'goalie_gsax_team',
                    'goalie_gsax_opponent'
                ])
                .with_normalization('standard'))

    @staticmethod
    def total_goals_model() -> Model:
        """
        Predict NHL total goals

        Expected features:
        - team_goals_for_avg
        - opponent_goals_for_avg
        - team_expected_goals_avg
        - opponent_expected_goals_avg
        - team_save_pct
        - opponent_save_pct
        """
        return (Model()
                .named("NHL Total Goals")
                .for_regression()
                .using_random_forest(n_trees=140, max_depth=16)
                .with_features([
                    'team_goals_for_avg',
                    'opponent_goals_for_avg',
                    'team_expected_goals_avg',
                    'opponent_expected_goals_avg',
                    'team_save_pct',
                    'opponent_save_pct'
                ])
                .with_normalization('standard'))


class MLBModels:
    """Machine learning models for MLB betting"""

    @staticmethod
    def game_winner_model() -> Model:
        """
        Predict MLB game winners

        Expected features:
        - team_runs_per_game
        - opponent_runs_per_game
        - pitcher_era
        - opponent_pitcher_era
        - pitcher_whip
        - opponent_pitcher_whip
        - team_batting_avg
        - opponent_batting_avg
        - home_field (1/0)
        - park_factor
        """
        return (Model()
                .named("MLB Game Winner")
                .for_classification()
                .using_random_forest(n_trees=160, max_depth=13)
                .with_features([
                    'team_runs_per_game',
                    'opponent_runs_per_game',
                    'pitcher_era',
                    'opponent_pitcher_era',
                    'pitcher_whip',
                    'opponent_pitcher_whip',
                    'team_batting_avg',
                    'opponent_batting_avg',
                    'home_field',
                    'park_factor'
                ])
                .with_normalization('standard'))

    @staticmethod
    def run_line_model() -> Model:
        """
        Predict MLB run line coverage (1.5 runs)

        Expected features:
        - run_differential
        - run_line
        - pitcher_quality_differential
        - home_field
        - park_factor
        """
        return (Model()
                .named("MLB Run Line Coverage")
                .for_classification()
                .using_random_forest(n_trees=170, max_depth=15)
                .with_features([
                    'run_differential',
                    'run_line',
                    'pitcher_quality_differential',
                    'home_field',
                    'park_factor'
                ])
                .with_normalization('standard'))

    @staticmethod
    def total_runs_model() -> Model:
        """
        Predict MLB total runs

        Expected features:
        - team_runs_per_game
        - opponent_runs_per_game
        - pitcher_era
        - opponent_pitcher_era
        - park_factor
        - weather_factor
        """
        return (Model()
                .named("MLB Total Runs")
                .for_regression()
                .using_random_forest(n_trees=150, max_depth=17)
                .with_features([
                    'team_runs_per_game',
                    'opponent_runs_per_game',
                    'pitcher_era',
                    'opponent_pitcher_era',
                    'park_factor',
                    'weather_factor'
                ])
                .with_normalization('standard'))


class CollegeFootballModels:
    """Machine learning models for College Football betting"""

    @staticmethod
    def game_winner_model() -> Model:
        """
        Predict CFB game winners

        Expected features:
        - team_sp_plus_rating
        - opponent_sp_plus_rating
        - conference_strength_team
        - conference_strength_opponent
        - home_field (1/0)
        - rivalry_game (1/0)
        """
        return (Model()
                .named("CFB Game Winner")
                .for_classification()
                .using_random_forest(n_trees=180, max_depth=14)
                .with_features([
                    'team_sp_plus_rating',
                    'opponent_sp_plus_rating',
                    'conference_strength_team',
                    'conference_strength_opponent',
                    'home_field',
                    'rivalry_game'
                ])
                .with_normalization('standard'))

    @staticmethod
    def spread_model() -> Model:
        """
        Predict CFB spread coverage

        Expected features:
        - rating_differential
        - spread
        - conference_matchup_factor
        - home_field
        - rivalry_game
        """
        return (Model()
                .named("CFB Spread Coverage")
                .for_classification()
                .using_random_forest(n_trees=200, max_depth=16)
                .with_features([
                    'rating_differential',
                    'spread',
                    'conference_matchup_factor',
                    'home_field',
                    'rivalry_game'
                ])
                .with_normalization('standard'))

    @staticmethod
    def total_points_model() -> Model:
        """
        Predict CFB total points

        Expected features:
        - team_ppg
        - opponent_ppg
        - pace_factor
        - defensive_efficiency_combined
        """
        return (Model()
                .named("CFB Total Points")
                .for_regression()
                .using_random_forest(n_trees=160, max_depth=18)
                .with_features([
                    'team_ppg',
                    'opponent_ppg',
                    'pace_factor',
                    'defensive_efficiency_combined'
                ])
                .with_normalization('standard'))


class CollegeBasketballModels:
    """Machine learning models for College Basketball betting"""

    @staticmethod
    def game_winner_model() -> Model:
        """
        Predict CBB game winners

        Expected features:
        - team_kenpom_rating
        - opponent_kenpom_rating
        - team_offensive_efficiency
        - team_defensive_efficiency
        - opponent_offensive_efficiency
        - opponent_defensive_efficiency
        - home_court (1/0)
        - conference_strength_team
        - conference_strength_opponent
        """
        return (Model()
                .named("CBB Game Winner")
                .for_classification()
                .using_random_forest(n_trees=170, max_depth=13)
                .with_features([
                    'team_kenpom_rating',
                    'opponent_kenpom_rating',
                    'team_offensive_efficiency',
                    'team_defensive_efficiency',
                    'opponent_offensive_efficiency',
                    'opponent_defensive_efficiency',
                    'home_court',
                    'conference_strength_team',
                    'conference_strength_opponent'
                ])
                .with_normalization('standard'))

    @staticmethod
    def spread_model() -> Model:
        """
        Predict CBB spread coverage

        Expected features:
        - efficiency_margin
        - spread
        - home_court
        - tempo_differential
        """
        return (Model()
                .named("CBB Spread Coverage")
                .for_classification()
                .using_random_forest(n_trees=190, max_depth=15)
                .with_features([
                    'efficiency_margin',
                    'spread',
                    'home_court',
                    'tempo_differential'
                ])
                .with_normalization('standard'))

    @staticmethod
    def march_madness_upset_model() -> Model:
        """
        Predict March Madness upsets

        Expected features:
        - seed_differential (lower - higher)
        - kenpom_rating_differential
        - tournament_experience_team
        - tournament_experience_opponent
        - pace_differential
        """
        return (Model()
                .named("March Madness Upset Predictor")
                .for_classification()
                .using_random_forest(n_trees=200, max_depth=14)
                .with_features([
                    'seed_differential',
                    'kenpom_rating_differential',
                    'tournament_experience_team',
                    'tournament_experience_opponent',
                    'pace_differential'
                ])
                .with_normalization('standard'))


class SoccerModels:
    """Machine learning models for Soccer betting"""

    @staticmethod
    def three_way_result_model() -> Model:
        """
        Predict soccer 3-way result (home/draw/away)

        Expected features:
        - team_expected_goals_avg
        - opponent_expected_goals_avg
        - team_goals_for_avg
        - team_goals_against_avg
        - opponent_goals_for_avg
        - opponent_goals_against_avg
        - home_advantage (1/0)
        - league_home_draw_away_factor

        Note: Output will be 0=away, 1=draw, 2=home
        """
        return (Model()
                .named("Soccer 3-Way Result")
                .for_classification()
                .using_neural_network(
                    hidden_layers=[15, 10],
                    learning_rate=0.05,
                    epochs=1500
                )
                .with_features([
                    'team_expected_goals_avg',
                    'opponent_expected_goals_avg',
                    'team_goals_for_avg',
                    'team_goals_against_avg',
                    'opponent_goals_for_avg',
                    'opponent_goals_against_avg',
                    'home_advantage',
                    'league_home_draw_away_factor'
                ])
                .with_normalization('standard'))

    @staticmethod
    def btts_model() -> Model:
        """
        Predict Both Teams To Score

        Expected features:
        - team_goals_for_avg
        - opponent_goals_for_avg
        - team_clean_sheet_pct
        - opponent_clean_sheet_pct
        - league_btts_frequency
        """
        return (Model()
                .named("Soccer BTTS")
                .for_classification()
                .using_random_forest(n_trees=140, max_depth=12)
                .with_features([
                    'team_goals_for_avg',
                    'opponent_goals_for_avg',
                    'team_clean_sheet_pct',
                    'opponent_clean_sheet_pct',
                    'league_btts_frequency'
                ])
                .with_normalization('standard'))

    @staticmethod
    def total_goals_model() -> Model:
        """
        Predict total goals in match

        Expected features:
        - team_goals_for_avg
        - opponent_goals_for_avg
        - team_expected_goals_avg
        - opponent_expected_goals_avg
        - league_avg_goals
        """
        return (Model()
                .named("Soccer Total Goals")
                .for_regression()
                .using_random_forest(n_trees=130, max_depth=16)
                .with_features([
                    'team_goals_for_avg',
                    'opponent_goals_for_avg',
                    'team_expected_goals_avg',
                    'opponent_expected_goals_avg',
                    'league_avg_goals'
                ])
                .with_normalization('standard'))


class HorseRacingModels:
    """Machine learning models for Horse Racing betting"""

    @staticmethod
    def win_probability_model() -> Model:
        """
        Predict horse win probability

        Expected features:
        - speed_figure
        - post_position
        - jockey_win_pct
        - trainer_win_pct
        - track_condition_factor
        - class_level
        - days_since_last_race
        - career_earnings
        """
        return (Model()
                .named("Horse Racing Win Probability")
                .for_classification()
                .using_random_forest(n_trees=200, max_depth=16)
                .with_features([
                    'speed_figure',
                    'post_position',
                    'jockey_win_pct',
                    'trainer_win_pct',
                    'track_condition_factor',
                    'class_level',
                    'days_since_last_race',
                    'career_earnings'
                ])
                .with_normalization('minmax'))

    @staticmethod
    def exacta_model() -> Model:
        """
        Predict top 2 finishers (for exacta betting)

        Expected features:
        - horse1_speed_figure
        - horse2_speed_figure
        - horse1_post_position
        - horse2_post_position
        - horse1_jockey_win_pct
        - horse2_jockey_win_pct
        - distance_suitability_horse1
        - distance_suitability_horse2
        """
        return (Model()
                .named("Horse Racing Exacta")
                .for_classification()
                .using_random_forest(n_trees=220, max_depth=18)
                .with_features([
                    'horse1_speed_figure',
                    'horse2_speed_figure',
                    'horse1_post_position',
                    'horse2_post_position',
                    'horse1_jockey_win_pct',
                    'horse2_jockey_win_pct',
                    'distance_suitability_horse1',
                    'distance_suitability_horse2'
                ])
                .with_normalization('minmax'))

    @staticmethod
    def speed_rating_predictor() -> Model:
        """
        Predict horse's speed rating for this race

        Expected features:
        - last_speed_figure
        - avg_speed_figure_l3
        - track_surface_performance
        - distance_performance
        - jockey_trainer_combo_factor
        """
        return (Model()
                .named("Horse Racing Speed Rating")
                .for_regression()
                .using_random_forest(n_trees=180, max_depth=17)
                .with_features([
                    'last_speed_figure',
                    'avg_speed_figure_l3',
                    'track_surface_performance',
                    'distance_performance',
                    'jockey_trainer_combo_factor'
                ])
                .with_normalization('minmax'))


# Convenient access dictionary
SPORT_MODELS = {
    'nba': NBAModels,
    'nfl': NFLModels,
    'nhl': NHLModels,
    'mlb': MLBModels,
    'cfb': CollegeFootballModels,
    'cbb': CollegeBasketballModels,
    'soccer': SoccerModels,
    'horse_racing': HorseRacingModels
}


def get_sport_model(sport: str, model_type: str) -> Model:
    """
    Get a sport-specific model

    Args:
        sport: Sport name ('nba', 'nfl', 'nhl', 'mlb', 'cfb', 'cbb', 'soccer', 'horse_racing')
        model_type: Model type ('game_winner', 'spread', 'total_points', etc.)

    Returns:
        Configured Model instance

    Example:
        >>> model = get_sport_model('nba', 'spread_model')
        >>> model.train(X_train, y_train)
        >>> model.print_performance(X_test, y_test)
    """
    sport_lower = sport.lower()

    if sport_lower not in SPORT_MODELS:
        raise ValueError(f"Unknown sport: {sport}. Available: {list(SPORT_MODELS.keys())}")

    sport_class = SPORT_MODELS[sport_lower]

    # Add _model suffix if not present
    if not model_type.endswith('_model'):
        model_type = model_type + '_model'

    if not hasattr(sport_class, model_type):
        available = [m for m in dir(sport_class) if m.endswith('_model') and not m.startswith('_')]
        raise ValueError(f"Unknown model type: {model_type}. Available for {sport}: {available}")

    model_method = getattr(sport_class, model_type)
    return model_method()
