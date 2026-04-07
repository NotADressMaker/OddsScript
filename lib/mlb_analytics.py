#!/usr/bin/env python3
"""
MLB Analytics Library

Statistical models for MLB (Baseball) betting, including run line analysis,
totals modeling, and pitcher-specific adjustments.
"""

import math
import random
from typing import Dict, List, Optional, Tuple
from lib.poisson_calculator import PoissonCalculator


class MLBAnalytics:
    """MLB-specific betting analytics"""

    # MLB averages
    AVG_RUNS_PER_GAME = 4.5
    AVG_HOME_ADVANTAGE = 0.25  # Runs
    AVG_TOTAL_RUNS = 9.0
    AVG_ERA = 4.20
    RECENT_FORM_WEIGHT = 0.30
    STARTER_WEIGHT = 0.65
    BULLPEN_WEIGHT = 0.35

    @staticmethod
    def _clamp(value: float, min_value: float, max_value: float) -> float:
        """Clamp value into [min_value, max_value]."""
        return max(min_value, min(max_value, value))

    @staticmethod
    def _blend_offense(season_runs: float, recent_runs: Optional[float]) -> float:
        """
        Blend season-long and recent scoring production.

        Recent form receives a modest weight to avoid overreacting to small samples.
        """
        if recent_runs is None:
            return season_runs
        recent_weight = MLBAnalytics.RECENT_FORM_WEIGHT
        return season_runs * (1 - recent_weight) + recent_runs * recent_weight

    @staticmethod
    def _pitching_factor(starter_era: Optional[float], bullpen_era: Optional[float]) -> float:
        """
        Convert pitcher quality into a run multiplier.

        Factor is centered at 1.0 when ERA equals league average.
        Lower ERA -> lower run environment, higher ERA -> higher run environment.
        """
        starter = starter_era if starter_era is not None else MLBAnalytics.AVG_ERA
        bullpen = bullpen_era if bullpen_era is not None else MLBAnalytics.AVG_ERA
        weighted_era = (
            starter * MLBAnalytics.STARTER_WEIGHT
            + bullpen * MLBAnalytics.BULLPEN_WEIGHT
        )
        factor = weighted_era / MLBAnalytics.AVG_ERA
        return MLBAnalytics._clamp(factor, 0.75, 1.30)

    @staticmethod
    def _calculate_adjusted_lambdas(
        team_runs_avg: float,
        opponent_runs_avg: float,
        is_home: bool,
        team_recent_runs: Optional[float] = None,
        opponent_recent_runs: Optional[float] = None,
        team_pitcher_era: Optional[float] = None,
        opponent_pitcher_era: Optional[float] = None,
        team_bullpen_era: Optional[float] = None,
        opponent_bullpen_era: Optional[float] = None,
        weather_run_factor: float = 1.0
    ) -> Tuple[float, float]:
        """Build adjusted expected-runs inputs used by MLB side markets."""
        home_adj = MLBAnalytics.AVG_HOME_ADVANTAGE if is_home else 0

        team_offense = MLBAnalytics._blend_offense(team_runs_avg, team_recent_runs)
        opp_offense = MLBAnalytics._blend_offense(opponent_runs_avg, opponent_recent_runs)

        opp_pitching_factor = MLBAnalytics._pitching_factor(
            starter_era=opponent_pitcher_era,
            bullpen_era=opponent_bullpen_era
        )
        team_pitching_factor = MLBAnalytics._pitching_factor(
            starter_era=team_pitcher_era,
            bullpen_era=team_bullpen_era
        )

        weather = MLBAnalytics._clamp(weather_run_factor, 0.85, 1.15)

        team_lambda = (team_offense + home_adj) * opp_pitching_factor * weather
        opp_lambda = opp_offense * team_pitching_factor * weather
        return team_lambda, opp_lambda

    @staticmethod
    def calculate_moneyline_probability(
        team_runs_avg: float,
        opponent_runs_avg: float,
        is_home: bool = True,
        team_recent_runs: Optional[float] = None,
        opponent_recent_runs: Optional[float] = None,
        team_pitcher_era: Optional[float] = None,
        opponent_pitcher_era: Optional[float] = None,
        team_bullpen_era: Optional[float] = None,
        opponent_bullpen_era: Optional[float] = None,
        weather_run_factor: float = 1.0
    ) -> Dict:
        """
        Calculate MLB moneyline probability using Poisson

        Args:
            team_runs_avg: Team average runs per game
            opponent_runs_avg: Opponent average runs
            is_home: Home team advantage
            team_recent_runs: Team recent runs per game (optional)
            opponent_recent_runs: Opponent recent runs per game (optional)
            team_pitcher_era: Team starting pitcher ERA (optional)
            opponent_pitcher_era: Opponent starting pitcher ERA (optional)
            team_bullpen_era: Team bullpen ERA (optional)
            opponent_bullpen_era: Opponent bullpen ERA (optional)
            weather_run_factor: Weather run environment multiplier (0.85-1.15 typical)

        Returns:
            Win probabilities
        """
        team_lambda, opp_lambda = MLBAnalytics._calculate_adjusted_lambdas(
            team_runs_avg=team_runs_avg,
            opponent_runs_avg=opponent_runs_avg,
            is_home=is_home,
            team_recent_runs=team_recent_runs,
            opponent_recent_runs=opponent_recent_runs,
            team_pitcher_era=team_pitcher_era,
            opponent_pitcher_era=opponent_pitcher_era,
            team_bullpen_era=team_bullpen_era,
            opponent_bullpen_era=opponent_bullpen_era,
            weather_run_factor=weather_run_factor
        )

        # Use Poisson to calculate probabilities
        results = PoissonCalculator.calculate_match_probabilities(
            team_lambda,
            opp_lambda,
            max_goals=15  # Max runs to consider
        )

        return {
            'win_probability': results['home_win'] if is_home else results['away_win'],
            'tie_probability': results['draw'],  # Extra innings
            'loss_probability': results['away_win'] if is_home else results['home_win'],
            'expected_runs': team_lambda,
            'opponent_expected_runs': opp_lambda,
            'weather_run_factor': MLBAnalytics._clamp(weather_run_factor, 0.85, 1.15)
        }

    @staticmethod
    def calculate_runline_probability(
        team_runs_avg: float,
        opponent_runs_avg: float,
        runline: float = -1.5,
        is_home: bool = True,
        team_recent_runs: Optional[float] = None,
        opponent_recent_runs: Optional[float] = None,
        team_pitcher_era: Optional[float] = None,
        opponent_pitcher_era: Optional[float] = None,
        team_bullpen_era: Optional[float] = None,
        opponent_bullpen_era: Optional[float] = None,
        weather_run_factor: float = 1.0
    ) -> Dict:
        """
        Calculate run line cover probability

        Standard MLB run line is -1.5/+1.5

        Args:
            team_runs_avg: Team average runs
            opponent_runs_avg: Opponent average runs
            runline: Run line (typically -1.5 for favorite)
            is_home: Home team advantage
            team_recent_runs: Team recent runs per game (optional)
            opponent_recent_runs: Opponent recent runs per game (optional)
            team_pitcher_era: Team starting pitcher ERA (optional)
            opponent_pitcher_era: Opponent starting pitcher ERA (optional)
            team_bullpen_era: Team bullpen ERA (optional)
            opponent_bullpen_era: Opponent bullpen ERA (optional)
            weather_run_factor: Weather run environment multiplier (0.85-1.15 typical)

        Returns:
            Run line probabilities
        """
        team_lambda, opp_lambda = MLBAnalytics._calculate_adjusted_lambdas(
            team_runs_avg=team_runs_avg,
            opponent_runs_avg=opponent_runs_avg,
            is_home=is_home,
            team_recent_runs=team_recent_runs,
            opponent_recent_runs=opponent_recent_runs,
            team_pitcher_era=team_pitcher_era,
            opponent_pitcher_era=opponent_pitcher_era,
            team_bullpen_era=team_bullpen_era,
            opponent_bullpen_era=opponent_bullpen_era,
            weather_run_factor=weather_run_factor
        )

        # Calculate using Poisson distribution
        results = PoissonCalculator.calculate_match_probabilities(
            team_lambda,
            opp_lambda,
            max_goals=15
        )

        # For run line, need to win by more than 1.5 (i.e., 2+ runs)
        cover_prob = 0.0
        prob_matrix = results['prob_matrix']

        for team_runs in range(len(prob_matrix)):
            for opp_runs in range(len(prob_matrix[0])):
                margin = team_runs - opp_runs
                if runline < 0:  # Favorite
                    if margin > abs(runline):
                        cover_prob += prob_matrix[team_runs][opp_runs]
                else:  # Underdog
                    if margin + runline > 0:
                        cover_prob += prob_matrix[team_runs][opp_runs]

        return {
            'cover_probability': cover_prob,
            'runline': runline,
            'expected_margin': team_lambda - opp_lambda,
            'weather_run_factor': MLBAnalytics._clamp(weather_run_factor, 0.85, 1.15)
        }

    @staticmethod
    def calculate_total_probability(
        team1_runs_avg: float,
        team2_runs_avg: float,
        total_line: float,
        pitcher_adjustment: float = 1.0,
        park_factor: float = 1.0
    ) -> Dict:
        """
        Calculate over/under probability for total runs

        Args:
            team1_runs_avg: Team 1 average runs
            team2_runs_avg: Team 2 average runs
            total_line: Over/under line
            pitcher_adjustment: Adjustment for pitcher quality (0.8-1.2)
            park_factor: Park factor (1.0 = neutral, >1.0 = hitter friendly)

        Returns:
            Over/under probabilities
        """
        # Adjust for pitcher and park
        adjusted_total = (team1_runs_avg + team2_runs_avg) * pitcher_adjustment * park_factor

        # Use Poisson for total runs
        total_lambda = adjusted_total

        # Calculate over/under using Poisson
        results = PoissonCalculator.calculate_total_probabilities(
            total_lambda / 2,  # Split equally for calculation
            total_lambda / 2,
            total_line,
            max_goals=20
        )

        return {
            'over_probability': results['over_probability'],
            'under_probability': results['under_probability'],
            'expected_total': adjusted_total,
            'line': total_line,
            'pitcher_adjustment': pitcher_adjustment,
            'park_factor': park_factor
        }

    @staticmethod
    def simulate_game(
        home_runs_avg: float,
        away_runs_avg: float,
        seed: Optional[int] = None
    ) -> Dict:
        """
        Simulate MLB game using Poisson distribution

        Args:
            home_runs_avg: Home team average runs
            away_runs_avg: Away team average runs
            seed: Random seed

        Returns:
            Game result
        """
        # Adjust for home advantage
        home_lambda = home_runs_avg + MLBAnalytics.AVG_HOME_ADVANTAGE
        away_lambda = away_runs_avg

        # Use Poisson simulation
        result = PoissonCalculator.simulate_match(home_lambda, away_lambda, seed)

        return {
            'home_score': result['home_score'],
            'away_score': result['away_score'],
            'total_runs': result['total_score'],
            'result': result['result'],
            'margin': result['home_score'] - result['away_score']
        }


if __name__ == '__main__':
    print("MLB Analytics Library")
    print("=" * 70)

    # Example: Calculate moneyline probability
    print("\nMoneyline Probability:")
    ml_result = MLBAnalytics.calculate_moneyline_probability(
        team_runs_avg=5.2,
        opponent_runs_avg=4.1,
        is_home=True
    )
    print(f"Win Probability: {ml_result['win_probability']*100:.1f}%")

    # Example: Run line
    print("\nRun Line (-1.5):")
    rl_result = MLBAnalytics.calculate_runline_probability(
        team_runs_avg=5.2,
        opponent_runs_avg=4.1,
        runline=-1.5,
        is_home=True
    )
    print(f"Cover Probability: {rl_result['cover_probability']*100:.1f}%")

    # Example: Total
    print("\nTotal (O/U 8.5):")
    total_result = MLBAnalytics.calculate_total_probability(
        team1_runs_avg=5.2,
        team2_runs_avg=4.1,
        total_line=8.5,
        park_factor=1.1  # Hitter-friendly park
    )
    print(f"Over Probability: {total_result['over_probability']*100:.1f}%")
    print(f"Expected Total: {total_result['expected_total']:.1f}")
