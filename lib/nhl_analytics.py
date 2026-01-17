#!/usr/bin/env python3
"""
NHL Analytics Library

Statistical models for NHL (Hockey) betting, including puck line analysis,
regulation time betting, and NHL-specific markets.
"""

import math
import random
from typing import Dict, List, Optional
from lib.poisson_calculator import PoissonCalculator


class NHLAnalytics:
    """NHL-specific betting analytics"""

    # NHL averages
    AVG_GOALS_PER_GAME = 3.0
    AVG_HOME_ADVANTAGE = 0.25  # Goals
    AVG_TOTAL_GOALS = 6.0
    REGULATION_TIME_PCT = 0.75  # ~75% of games end in regulation

    @staticmethod
    def calculate_moneyline_probability(
        team_goals_avg: float,
        opponent_goals_avg: float,
        is_home: bool = True,
        include_overtime: bool = True
    ) -> Dict:
        """
        Calculate NHL moneyline probability

        Args:
            team_goals_avg: Team average goals per game
            opponent_goals_avg: Opponent average goals
            is_home: Home ice advantage
            include_overtime: Include OT/SO in calculation

        Returns:
            Win probabilities
        """
        # Adjust for home advantage
        home_adj = NHLAnalytics.AVG_HOME_ADVANTAGE if is_home else 0
        team_lambda = team_goals_avg + home_adj
        opp_lambda = opponent_goals_avg

        # Use Poisson for probabilities
        results = PoissonCalculator.calculate_match_probabilities(
            team_lambda,
            opp_lambda,
            max_goals=10
        )

        if include_overtime:
            # In NHL, ties go to OT/SO - split draws
            overtime_win_boost = results['draw'] * 0.5
            return {
                'win_probability': results['home_win'] + overtime_win_boost if is_home else results['away_win'] + overtime_win_boost,
                'regulation_win_probability': results['home_win'] if is_home else results['away_win'],
                'overtime_probability': results['draw'],
                'loss_probability': results['away_win'] if is_home else results['home_win']
            }
        else:
            return {
                'win_probability': results['home_win'] if is_home else results['away_win'],
                'tie_probability': results['draw'],
                'loss_probability': results['away_win'] if is_home else results['home_win']
            }

    @staticmethod
    def calculate_puckline_probability(
        team_goals_avg: float,
        opponent_goals_avg: float,
        puckline: float = -1.5,
        is_home: bool = True
    ) -> Dict:
        """
        Calculate puck line cover probability

        Standard NHL puck line is -1.5/+1.5

        Args:
            team_goals_avg: Team average goals
            opponent_goals_avg: Opponent average goals
            puckline: Puck line (typically -1.5 for favorite)
            is_home: Home ice advantage

        Returns:
            Puck line probabilities
        """
        home_adj = NHLAnalytics.AVG_HOME_ADVANTAGE if is_home else 0
        team_lambda = team_goals_avg + home_adj
        opp_lambda = opponent_goals_avg

        # Calculate using Poisson
        results = PoissonCalculator.calculate_match_probabilities(
            team_lambda,
            opp_lambda,
            max_goals=10
        )

        # For puck line, need to win by 2+ goals
        cover_prob = 0.0
        prob_matrix = results['prob_matrix']

        for team_goals in range(len(prob_matrix)):
            for opp_goals in range(len(prob_matrix[0])):
                margin = team_goals - opp_goals
                if puckline < 0:  # Favorite
                    if margin > abs(puckline):
                        cover_prob += prob_matrix[team_goals][opp_goals]
                else:  # Underdog
                    if margin + puckline > 0:
                        cover_prob += prob_matrix[team_goals][opp_goals]

        return {
            'cover_probability': cover_prob,
            'puckline': puckline,
            'expected_margin': team_lambda - opp_lambda
        }

    @staticmethod
    def calculate_total_probability(
        team1_goals_avg: float,
        team2_goals_avg: float,
        total_line: float,
        goalie_adjustment: float = 1.0
    ) -> Dict:
        """
        Calculate over/under probability for total goals

        Args:
            team1_goals_avg: Team 1 average goals
            team2_goals_avg: Team 2 average goals
            total_line: Over/under line
            goalie_adjustment: Adjustment for goalie quality (0.8-1.2)

        Returns:
            Over/under probabilities
        """
        # Adjust for goalies
        total_lambda = (team1_goals_avg + team2_goals_avg) * goalie_adjustment

        # Use Poisson for totals
        results = PoissonCalculator.calculate_total_probabilities(
            total_lambda / 2,
            total_lambda / 2,
            total_line,
            max_goals=12
        )

        return {
            'over_probability': results['over_probability'],
            'under_probability': results['under_probability'],
            'expected_total': total_lambda,
            'line': total_line,
            'goalie_adjustment': goalie_adjustment
        }

    @staticmethod
    def calculate_regulation_time_probability(
        team_goals_avg: float,
        opponent_goals_avg: float,
        is_home: bool = True
    ) -> Dict:
        """
        Calculate probability of winning in regulation time (60 minutes)

        Args:
            team_goals_avg: Team average goals
            opponent_goals_avg: Opponent average goals
            is_home: Home ice advantage

        Returns:
            Regulation time probabilities
        """
        home_adj = NHLAnalytics.AVG_HOME_ADVANTAGE if is_home else 0
        team_lambda = team_goals_avg + home_adj
        opp_lambda = opponent_goals_avg

        results = PoissonCalculator.calculate_match_probabilities(
            team_lambda,
            opp_lambda,
            max_goals=10
        )

        return {
            'regulation_win_probability': results['home_win'] if is_home else results['away_win'],
            'regulation_loss_probability': results['away_win'] if is_home else results['home_win'],
            'overtime_probability': results['draw']
        }

    @staticmethod
    def simulate_game(
        home_goals_avg: float,
        away_goals_avg: float,
        seed: Optional[int] = None
    ) -> Dict:
        """
        Simulate NHL game using Poisson distribution

        Args:
            home_goals_avg: Home team average goals
            away_goals_avg: Away team average goals
            seed: Random seed

        Returns:
            Game result including OT/SO
        """
        # Adjust for home ice
        home_lambda = home_goals_avg + NHLAnalytics.AVG_HOME_ADVANTAGE
        away_lambda = away_goals_avg

        # Simulate regulation time
        result = PoissonCalculator.simulate_match(home_lambda, away_lambda, seed)

        game_result = {
            'home_score': result['home_score'],
            'away_score': result['away_score'],
            'total_goals': result['total_score'],
            'regulation_result': result['result'],
            'margin': result['home_score'] - result['away_score']
        }

        # If tied, simulate OT/SO (simplified - 50/50 in OT)
        if result['result'] == 'draw':
            if seed is not None:
                random.seed(seed + 1)
            ot_winner = random.choice(['home_win', 'away_win'])
            game_result['final_result'] = ot_winner
            game_result['overtime'] = True
            if ot_winner == 'home_win':
                game_result['home_score'] += 1
            else:
                game_result['away_score'] += 1
        else:
            game_result['final_result'] = result['result']
            game_result['overtime'] = False

        return game_result


if __name__ == '__main__':
    print("NHL Analytics Library")
    print("=" * 70)

    # Example: Moneyline
    print("\nMoneyline Probability:")
    ml_result = NHLAnalytics.calculate_moneyline_probability(
        team_goals_avg=3.2,
        opponent_goals_avg=2.7,
        is_home=True
    )
    print(f"Win Probability: {ml_result['win_probability']*100:.1f}%")
    print(f"Regulation Win: {ml_result['regulation_win_probability']*100:.1f}%")

    # Example: Puck line
    print("\nPuck Line (-1.5):")
    pl_result = NHLAnalytics.calculate_puckline_probability(
        team_goals_avg=3.2,
        opponent_goals_avg=2.7,
        puckline=-1.5
    )
    print(f"Cover Probability: {pl_result['cover_probability']*100:.1f}%")

    # Example: Total
    print("\nTotal (O/U 6.5):")
    total_result = NHLAnalytics.calculate_total_probability(
        team1_goals_avg=3.2,
        team2_goals_avg=2.7,
        total_line=6.5
    )
    print(f"Over Probability: {total_result['over_probability']*100:.1f}%")
    print(f"Expected Total: {total_result['expected_total']:.1f}")
