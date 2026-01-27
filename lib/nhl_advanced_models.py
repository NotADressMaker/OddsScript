#!/usr/bin/env python3
"""
NHL Advanced Prediction Models

Specialized models for NHL betting including:
- Decision Tree Model for O/U and ATS predictions
- Power Ranking Model with Elo-style ratings
- Similar Game Model for historical pattern matching
"""

import math
import random
from typing import Dict, List, Tuple, Optional
from collections import defaultdict


class NHLDecisionTree:
    """
    Decision Tree model for NHL game predictions

    Uses key factors to make O/U and ATS predictions:
    - Expected Goals (xG) differential
    - Recent form (last 10 games)
    - Home/Away performance
    - Goalie matchup
    - Rest advantage
    - Head-to-head history
    """

    def __init__(self):
        self.tree_nodes = {}
        self.trained = False

    def predict_over_under(
        self,
        team1_xgf: float,
        team1_xga: float,
        team2_xgf: float,
        team2_xga: float,
        line: float,
        team1_goalie_sv_pct: float = 0.910,
        team2_goalie_sv_pct: float = 0.910,
        team1_recent_goals: float = 3.0,
        team2_recent_goals: float = 3.0,
        team1_rest_days: int = 1,
        team2_rest_days: int = 1
    ) -> Dict:
        """
        Predict Over/Under using decision tree logic

        Args:
            team1_xgf: Team 1 expected goals for per game
            team1_xga: Team 1 expected goals against per game
            team2_xgf: Team 2 expected goals for per game
            team2_xga: Team 2 expected goals against per game
            line: O/U line
            team1_goalie_sv_pct: Team 1 goalie save percentage
            team2_goalie_sv_pct: Team 2 goalie save percentage
            team1_recent_goals: Team 1 goals in last 10 games (avg)
            team2_recent_goals: Team 2 goals in last 10 games (avg)
            team1_rest_days: Team 1 rest days
            team2_rest_days: Team 2 rest days

        Returns:
            Dictionary with prediction and confidence
        """
        # Calculate expected total using xG
        team1_expected = team1_xgf * (team2_goalie_sv_pct / 0.910)
        team2_expected = team2_xgf * (team1_goalie_sv_pct / 0.910)
        xg_total = team1_expected + team2_expected

        # Recent form adjustment
        recent_avg = (team1_recent_goals + team2_recent_goals) / 2
        form_weight = 0.3
        adjusted_total = (xg_total * (1 - form_weight)) + (recent_avg * 2 * form_weight)

        # Rest adjustment (tired teams score less, allow more)
        if team1_rest_days == 0 or team2_rest_days == 0:
            adjusted_total *= 0.95  # Back-to-back reduces scoring
        elif team1_rest_days >= 3 and team2_rest_days >= 3:
            adjusted_total *= 1.05  # Well-rested increases scoring

        # Decision tree logic
        confidence = 0.0
        prediction = "PUSH"

        # Node 1: Is predicted total significantly different from line?
        diff = abs(adjusted_total - line)

        if diff < 0.3:
            # Too close to call
            prediction = "PUSH"
            confidence = 0.50
        elif adjusted_total > line:
            # Node 2: Check goalie quality
            avg_sv_pct = (team1_goalie_sv_pct + team2_goalie_sv_pct) / 2

            if avg_sv_pct < 0.900:
                # Weak goalies = more goals
                prediction = "OVER"
                confidence = 0.70
            elif avg_sv_pct > 0.920:
                # Elite goalies might suppress scoring
                if diff > 0.5:
                    prediction = "OVER"
                    confidence = 0.60
                else:
                    prediction = "PUSH"
                    confidence = 0.52
            else:
                # Average goalies
                prediction = "OVER"
                confidence = 0.65

            # Node 3: Boost confidence if recent form supports it
            if recent_avg * 2 > line:
                confidence = min(0.75, confidence + 0.05)
        else:
            # Predicted under
            avg_sv_pct = (team1_goalie_sv_pct + team2_goalie_sv_pct) / 2

            if avg_sv_pct > 0.920:
                # Elite goalies = fewer goals
                prediction = "UNDER"
                confidence = 0.70
            elif avg_sv_pct < 0.900:
                # Weak goalies make under risky
                if diff > 0.5:
                    prediction = "UNDER"
                    confidence = 0.60
                else:
                    prediction = "PUSH"
                    confidence = 0.52
            else:
                prediction = "UNDER"
                confidence = 0.65

            if recent_avg * 2 < line:
                confidence = min(0.75, confidence + 0.05)

        return {
            'prediction': prediction,
            'confidence': confidence,
            'expected_total': round(adjusted_total, 2),
            'line': line,
            'difference': round(adjusted_total - line, 2),
            'factors': {
                'xg_based_total': round(xg_total, 2),
                'recent_form_total': round(recent_avg * 2, 2),
                'goalie_quality': 'Elite' if avg_sv_pct > 0.920 else 'Weak' if avg_sv_pct < 0.900 else 'Average',
                'rest_impact': 'Negative' if team1_rest_days == 0 or team2_rest_days == 0 else 'Positive' if team1_rest_days >= 3 and team2_rest_days >= 3 else 'Neutral'
            }
        }

    def predict_ats(
        self,
        team_xgf: float,
        team_xga: float,
        opp_xgf: float,
        opp_xga: float,
        spread: float,
        is_home: bool = True,
        team_ats_record: Tuple[int, int] = (0, 0),
        team_recent_form: float = 0.500,
        opp_recent_form: float = 0.500,
        team_rest_days: int = 1,
        opp_rest_days: int = 1,
        h2h_advantage: float = 0.0
    ) -> Dict:
        """
        Predict Against The Spread using decision tree

        Args:
            team_xgf: Team expected goals for per game
            team_xga: Team expected goals against per game
            opp_xgf: Opponent expected goals for per game
            opp_xga: Opponent expected goals against per game
            spread: Puck line (usually -1.5 or +1.5)
            is_home: Whether team is home
            team_ats_record: Team's ATS record (wins, losses)
            team_recent_form: Win % in last 10 games
            opp_recent_form: Opponent win % in last 10 games
            team_rest_days: Team rest days
            opp_rest_days: Opponent rest days
            h2h_advantage: Head to head goal differential

        Returns:
            Dictionary with ATS prediction and confidence
        """
        # Calculate expected goal differential
        team_goal_diff = team_xgf - team_xga
        opp_goal_diff = opp_xgf - opp_xga
        xg_differential = team_goal_diff - opp_goal_diff

        # Home ice advantage (about 0.2 goals)
        if is_home:
            xg_differential += 0.2

        # Recent form adjustment
        form_diff = team_recent_form - opp_recent_form
        xg_differential += form_diff * 0.5

        # Rest advantage
        rest_diff = team_rest_days - opp_rest_days
        if abs(rest_diff) >= 2:
            xg_differential += rest_diff * 0.15

        # Head-to-head
        xg_differential += h2h_advantage * 0.3

        # Decision tree for ATS
        confidence = 0.50
        prediction = "PUSH"

        # Node 1: Compare expected differential to spread
        cover_margin = xg_differential + spread  # Positive = covers spread

        if abs(cover_margin) < 0.3:
            prediction = "PUSH"
            confidence = 0.50
        elif cover_margin > 0:
            # Team should cover
            prediction = "COVER"

            # Node 2: Check recent ATS performance
            if team_ats_record[0] + team_ats_record[1] > 0:
                ats_pct = team_ats_record[0] / (team_ats_record[0] + team_ats_record[1])
                if ats_pct > 0.55:
                    confidence = 0.70
                elif ats_pct < 0.45:
                    confidence = 0.55
                else:
                    confidence = 0.60
            else:
                confidence = 0.60

            # Node 3: Boost for strong recent form
            if team_recent_form > 0.65:
                confidence = min(0.75, confidence + 0.05)

            # Node 4: Check cover margin strength
            if abs(cover_margin) > 0.8:
                confidence = min(0.78, confidence + 0.05)
        else:
            # Team won't cover
            prediction = "NO COVER"

            if team_ats_record[0] + team_ats_record[1] > 0:
                ats_pct = team_ats_record[0] / (team_ats_record[0] + team_ats_record[1])
                if ats_pct < 0.45:
                    confidence = 0.70
                elif ats_pct > 0.55:
                    confidence = 0.55
                else:
                    confidence = 0.60
            else:
                confidence = 0.60

            if team_recent_form < 0.35:
                confidence = min(0.75, confidence + 0.05)

            if abs(cover_margin) > 0.8:
                confidence = min(0.78, confidence + 0.05)

        return {
            'prediction': prediction,
            'confidence': confidence,
            'expected_differential': round(xg_differential, 2),
            'spread': spread,
            'cover_margin': round(cover_margin, 2),
            'factors': {
                'xg_differential': round(team_goal_diff - opp_goal_diff, 2),
                'home_advantage': 0.2 if is_home else 0.0,
                'form_differential': round(form_diff, 3),
                'rest_advantage': rest_diff,
                'h2h_factor': round(h2h_advantage * 0.3, 2)
            }
        }


class NHLPowerRankings:
    """
    Elo-style power ranking system for NHL teams

    Maintains dynamic ratings that update after each game
    Used for predicting future matchups
    """

    def __init__(self, k_factor: float = 20.0, home_advantage: float = 55.0):
        """
        Initialize power rankings

        Args:
            k_factor: How much ratings change per game (higher = more volatile)
            home_advantage: Home ice advantage in rating points
        """
        self.ratings = {}
        self.k_factor = k_factor
        self.home_advantage = home_advantage
        self.default_rating = 1500.0

    def get_rating(self, team: str) -> float:
        """Get team's current rating"""
        return self.ratings.get(team, self.default_rating)

    def set_rating(self, team: str, rating: float):
        """Set team's rating"""
        self.ratings[team] = rating

    def expected_score(self, team_rating: float, opp_rating: float) -> float:
        """
        Calculate expected score (0-1) for a team

        Uses Elo formula: 1 / (1 + 10^((opponent - team)/400))
        """
        return 1.0 / (1.0 + 10 ** ((opp_rating - team_rating) / 400.0))

    def update_ratings(
        self,
        team1: str,
        team2: str,
        team1_score: int,
        team2_score: int,
        team1_home: bool = True,
        overtime: bool = False
    ):
        """
        Update ratings based on game result

        Args:
            team1: Team 1 name
            team2: Team 2 name
            team1_score: Team 1 goals
            team2_score: Team 2 goals
            team1_home: Whether team1 was home
            overtime: Whether game went to OT/SO
        """
        # Get current ratings
        team1_rating = self.get_rating(team1)
        team2_rating = self.get_rating(team2)

        # Apply home advantage
        if team1_home:
            team1_rating += self.home_advantage
        else:
            team2_rating += self.home_advantage

        # Calculate expected scores
        team1_expected = self.expected_score(team1_rating, team2_rating)
        team2_expected = 1.0 - team1_expected

        # Determine actual scores (1 for win, 0.5 for OT loss, 0 for regulation loss)
        if team1_score > team2_score:
            team1_actual = 1.0
            team2_actual = 0.0 if not overtime else 0.5
        else:
            team1_actual = 0.0 if not overtime else 0.5
            team2_actual = 1.0

        # Update ratings
        team1_new = self.get_rating(team1) + self.k_factor * (team1_actual - team1_expected)
        team2_new = self.get_rating(team2) + self.k_factor * (team2_actual - team2_expected)

        self.set_rating(team1, team1_new)
        self.set_rating(team2, team2_new)

    def predict_game(
        self,
        team1: str,
        team2: str,
        team1_home: bool = True
    ) -> Dict:
        """
        Predict game outcome using power rankings

        Returns win probability, expected spread, and total prediction
        """
        # Get ratings
        team1_rating = self.get_rating(team1)
        team2_rating = self.get_rating(team2)

        # Apply home advantage
        if team1_home:
            team1_adj = team1_rating + self.home_advantage
            team2_adj = team2_rating
        else:
            team1_adj = team1_rating
            team2_adj = team2_rating + self.home_advantage

        # Win probability
        team1_win_prob = self.expected_score(team1_adj, team2_adj)

        # Expected goal differential (rating diff / 100 ≈ goal diff)
        rating_diff = team1_adj - team2_adj
        expected_diff = rating_diff / 100.0

        # Expected total (average NHL game is ~6 goals)
        # Higher rated teams tend to be in higher scoring games
        avg_rating = (team1_rating + team2_rating) / 2
        rating_factor = (avg_rating - self.default_rating) / 200.0
        expected_total = 6.0 + rating_factor

        return {
            'team1_win_probability': round(team1_win_prob, 3),
            'team2_win_probability': round(1 - team1_win_prob, 3),
            'expected_goal_differential': round(expected_diff, 2),
            'expected_total': round(expected_total, 1),
            'team1_rating': round(team1_rating, 1),
            'team2_rating': round(team2_rating, 1),
            'rating_advantage': round(rating_diff, 1)
        }

    def get_top_teams(self, n: int = 10) -> List[Tuple[str, float]]:
        """Get top N teams by rating"""
        sorted_teams = sorted(self.ratings.items(), key=lambda x: x[1], reverse=True)
        return sorted_teams[:n]


class NHLSimilarGameModel:
    """
    Historical pattern matching model

    Finds similar games from history and uses their outcomes
    to predict current matchup
    """

    def __init__(self):
        self.game_database = []

    def add_game(
        self,
        team1: str,
        team2: str,
        team1_xgf: float,
        team1_xga: float,
        team2_xgf: float,
        team2_xga: float,
        team1_goals: int,
        team2_goals: int,
        total_goals: int,
        spread_result: str,  # 'cover', 'no_cover', or 'push'
        over_under_result: str,  # 'over', 'under', or 'push'
        team1_home: bool = True,
        team1_rest: int = 1,
        team2_rest: int = 1,
        metadata: Dict = None
    ):
        """
        Add historical game to database

        Args:
            team1: Team 1 name
            team2: Team 2 name
            team1_xgf: Team 1 xG for
            team1_xga: Team 1 xG against
            team2_xgf: Team 2 xG for
            team2_xga: Team 2 xG against
            team1_goals: Team 1 actual goals
            team2_goals: Team 2 actual goals
            total_goals: Total goals in game
            spread_result: ATS result
            over_under_result: O/U result
            team1_home: Team 1 home
            team1_rest: Team 1 rest days
            team2_rest: Team 2 rest days
            metadata: Additional info
        """
        game = {
            'team1': team1,
            'team2': team2,
            'team1_xgf': team1_xgf,
            'team1_xga': team1_xga,
            'team2_xgf': team2_xgf,
            'team2_xga': team2_xga,
            'team1_xg_diff': team1_xgf - team1_xga,
            'team2_xg_diff': team2_xgf - team2_xga,
            'xg_matchup_diff': (team1_xgf - team1_xga) - (team2_xgf - team2_xga),
            'expected_total': team1_xgf + team2_xgf,
            'team1_goals': team1_goals,
            'team2_goals': team2_goals,
            'total_goals': total_goals,
            'spread_result': spread_result,
            'over_under_result': over_under_result,
            'team1_home': team1_home,
            'team1_rest': team1_rest,
            'team2_rest': team2_rest,
            'rest_diff': team1_rest - team2_rest,
            'metadata': metadata or {}
        }

        self.game_database.append(game)

    def find_similar_games(
        self,
        team1_xgf: float,
        team1_xga: float,
        team2_xgf: float,
        team2_xga: float,
        team1_home: bool = True,
        team1_rest: int = 1,
        team2_rest: int = 1,
        max_results: int = 20,
        similarity_threshold: float = 0.8
    ) -> List[Dict]:
        """
        Find similar games from historical database

        Similarity based on:
        - xG differential matchup
        - Expected total
        - Home/away
        - Rest situation

        Args:
            team1_xgf: Team 1 xG for
            team1_xga: Team 1 xG against
            team2_xgf: Team 2 xG for
            team2_xga: Team 2 xG against
            team1_home: Team 1 home
            team1_rest: Team 1 rest days
            team2_rest: Team 2 rest days
            max_results: Maximum number of similar games
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of similar games sorted by similarity
        """
        if not self.game_database:
            return []

        # Calculate current game characteristics
        current_xg_diff = (team1_xgf - team1_xga) - (team2_xgf - team2_xga)
        current_expected_total = team1_xgf + team2_xgf
        current_rest_diff = team1_rest - team2_rest

        similar_games = []

        for game in self.game_database:
            # Calculate similarity score (0-1)
            similarity = 0.0

            # xG differential similarity (40% weight)
            xg_diff_error = abs(game['xg_matchup_diff'] - current_xg_diff)
            xg_sim = max(0, 1 - (xg_diff_error / 2.0))  # Within 2.0 xG = perfect
            similarity += xg_sim * 0.40

            # Expected total similarity (30% weight)
            total_error = abs(game['expected_total'] - current_expected_total)
            total_sim = max(0, 1 - (total_error / 3.0))  # Within 3.0 goals = perfect
            similarity += total_sim * 0.30

            # Home/away match (15% weight)
            if game['team1_home'] == team1_home:
                similarity += 0.15

            # Rest situation similarity (15% weight)
            rest_error = abs(game['rest_diff'] - current_rest_diff)
            rest_sim = max(0, 1 - (rest_error / 3.0))
            similarity += rest_sim * 0.15

            if similarity >= similarity_threshold:
                game_copy = game.copy()
                game_copy['similarity'] = similarity
                similar_games.append(game_copy)

        # Sort by similarity
        similar_games.sort(key=lambda x: x['similarity'], reverse=True)

        return similar_games[:max_results]

    def predict_from_similar(
        self,
        team1_xgf: float,
        team1_xga: float,
        team2_xgf: float,
        team2_xga: float,
        line_total: float,
        line_spread: float,
        team1_home: bool = True,
        team1_rest: int = 1,
        team2_rest: int = 1,
        min_similar_games: int = 5
    ) -> Dict:
        """
        Predict O/U and ATS based on similar historical games

        Args:
            team1_xgf: Team 1 xG for
            team1_xga: Team 1 xG against
            team2_xgf: Team 2 xG for
            team2_xga: Team 2 xG against
            line_total: O/U line
            line_spread: ATS spread
            team1_home: Team 1 home
            team1_rest: Team 1 rest days
            team2_rest: Team 2 rest days
            min_similar_games: Minimum similar games needed

        Returns:
            Predictions with confidence based on historical patterns
        """
        similar_games = self.find_similar_games(
            team1_xgf, team1_xga, team2_xgf, team2_xga,
            team1_home, team1_rest, team2_rest
        )

        if len(similar_games) < min_similar_games:
            return {
                'prediction': 'INSUFFICIENT DATA',
                'confidence': 0.0,
                'similar_games_found': len(similar_games),
                'minimum_required': min_similar_games
            }

        # Analyze O/U results
        over_count = sum(1 for g in similar_games if g['over_under_result'] == 'over')
        under_count = sum(1 for g in similar_games if g['over_under_result'] == 'under')
        push_count = sum(1 for g in similar_games if g['over_under_result'] == 'push')

        over_pct = over_count / len(similar_games)
        under_pct = under_count / len(similar_games)

        # Analyze ATS results
        cover_count = sum(1 for g in similar_games if g['spread_result'] == 'cover')
        no_cover_count = sum(1 for g in similar_games if g['spread_result'] == 'no_cover')
        ats_push_count = sum(1 for g in similar_games if g['spread_result'] == 'push')

        cover_pct = cover_count / len(similar_games)

        # Calculate average outcomes
        avg_total = sum(g['total_goals'] for g in similar_games) / len(similar_games)
        avg_team1_goals = sum(g['team1_goals'] for g in similar_games) / len(similar_games)
        avg_team2_goals = sum(g['team2_goals'] for g in similar_games) / len(similar_games)
        avg_goal_diff = avg_team1_goals - avg_team2_goals

        # Average similarity (for confidence)
        avg_similarity = sum(g['similarity'] for g in similar_games) / len(similar_games)

        # O/U Prediction
        if over_pct > 0.60:
            ou_prediction = "OVER"
            ou_confidence = min(0.75, 0.50 + (over_pct - 0.50) * avg_similarity)
        elif under_pct > 0.60:
            ou_prediction = "UNDER"
            ou_confidence = min(0.75, 0.50 + (under_pct - 0.50) * avg_similarity)
        else:
            ou_prediction = "PUSH"
            ou_confidence = 0.50

        # ATS Prediction
        if cover_pct > 0.60:
            ats_prediction = "COVER"
            ats_confidence = min(0.75, 0.50 + (cover_pct - 0.50) * avg_similarity)
        elif cover_pct < 0.40:
            ats_prediction = "NO COVER"
            ats_confidence = min(0.75, 0.50 + ((1 - cover_pct) - 0.50) * avg_similarity)
        else:
            ats_prediction = "PUSH"
            ats_confidence = 0.50

        return {
            'over_under': {
                'prediction': ou_prediction,
                'confidence': round(ou_confidence, 3),
                'over_percentage': round(over_pct, 3),
                'under_percentage': round(under_pct, 3),
                'average_total': round(avg_total, 1),
                'line': line_total
            },
            'against_spread': {
                'prediction': ats_prediction,
                'confidence': round(ats_confidence, 3),
                'cover_percentage': round(cover_pct, 3),
                'average_goal_diff': round(avg_goal_diff, 2),
                'spread': line_spread
            },
            'analysis': {
                'similar_games_found': len(similar_games),
                'average_similarity': round(avg_similarity, 3),
                'sample_quality': 'Excellent' if len(similar_games) >= 15 and avg_similarity > 0.85 else 'Good' if len(similar_games) >= 10 else 'Fair',
                'historical_patterns': {
                    'avg_team1_goals': round(avg_team1_goals, 1),
                    'avg_team2_goals': round(avg_team2_goals, 1),
                    'avg_total': round(avg_total, 1)
                }
            }
        }


# Quick helper functions
def quick_nhl_decision_tree_ou(
    team1_xgf: float, team1_xga: float,
    team2_xgf: float, team2_xga: float,
    line: float
) -> Dict:
    """Quick O/U prediction using decision tree"""
    tree = NHLDecisionTree()
    return tree.predict_over_under(team1_xgf, team1_xga, team2_xgf, team2_xga, line)


def quick_nhl_decision_tree_ats(
    team_xgf: float, team_xga: float,
    opp_xgf: float, opp_xga: float,
    spread: float,
    is_home: bool = True
) -> Dict:
    """Quick ATS prediction using decision tree"""
    tree = NHLDecisionTree()
    return tree.predict_ats(team_xgf, team_xga, opp_xgf, opp_xga, spread, is_home)


if __name__ == "__main__":
    print("NHL Advanced Prediction Models")
    print("=" * 60)

    # Example 1: Decision Tree O/U
    print("\nExample 1: Decision Tree O/U Prediction")
    print("-" * 60)
    tree = NHLDecisionTree()
    ou_pred = tree.predict_over_under(
        team1_xgf=3.2, team1_xga=2.8,
        team2_xgf=2.9, team2_xga=3.0,
        line=6.5,
        team1_goalie_sv_pct=0.920,
        team2_goalie_sv_pct=0.905,
        team1_recent_goals=3.5,
        team2_recent_goals=2.8
    )
    print(f"Prediction: {ou_pred['prediction']}")
    print(f"Confidence: {ou_pred['confidence']:.1%}")
    print(f"Expected Total: {ou_pred['expected_total']}")
    print(f"Line: {ou_pred['line']}")

    # Example 2: Decision Tree ATS
    print("\nExample 2: Decision Tree ATS Prediction")
    print("-" * 60)
    ats_pred = tree.predict_ats(
        team_xgf=3.2, team_xga=2.8,
        opp_xgf=2.9, opp_xga=3.0,
        spread=-1.5,
        is_home=True,
        team_recent_form=0.700,
        opp_recent_form=0.450
    )
    print(f"Prediction: {ats_pred['prediction']}")
    print(f"Confidence: {ats_pred['confidence']:.1%}")
    print(f"Expected Differential: {ats_pred['expected_differential']}")

    # Example 3: Power Rankings
    print("\nExample 3: Power Rankings Model")
    print("-" * 60)
    rankings = NHLPowerRankings()

    # Seed some teams
    rankings.set_rating("Tampa Bay", 1650)
    rankings.set_rating("Toronto", 1580)
    rankings.set_rating("Boston", 1620)
    rankings.set_rating("Arizona", 1380)

    prediction = rankings.predict_game("Tampa Bay", "Arizona", team1_home=True)
    print(f"Tampa Bay vs Arizona:")
    print(f"  Tampa Win Probability: {prediction['team1_win_probability']:.1%}")
    print(f"  Expected Goal Differential: {prediction['expected_goal_differential']}")
    print(f"  Expected Total: {prediction['expected_total']}")

    # Example 4: Similar Game Model
    print("\nExample 4: Similar Game Model")
    print("-" * 60)
    sim_model = NHLSimilarGameModel()

    # Add some historical games
    for i in range(25):
        sim_model.add_game(
            team1="Team A", team2="Team B",
            team1_xgf=3.0 + random.uniform(-0.5, 0.5),
            team1_xga=2.8 + random.uniform(-0.5, 0.5),
            team2_xgf=2.9 + random.uniform(-0.5, 0.5),
            team2_xga=3.0 + random.uniform(-0.5, 0.5),
            team1_goals=random.randint(2, 5),
            team2_goals=random.randint(2, 5),
            total_goals=random.randint(5, 8),
            spread_result=random.choice(['cover', 'no_cover', 'push']),
            over_under_result=random.choice(['over', 'under', 'push'])
        )

    sim_pred = sim_model.predict_from_similar(
        team1_xgf=3.1, team1_xga=2.9,
        team2_xgf=2.8, team2_xga=3.1,
        line_total=6.5,
        line_spread=-1.5
    )

    print(f"Similar Games Found: {sim_pred['analysis']['similar_games_found']}")
    print(f"Sample Quality: {sim_pred['analysis']['sample_quality']}")
    print(f"\nO/U Prediction: {sim_pred['over_under']['prediction']}")
    print(f"O/U Confidence: {sim_pred['over_under']['confidence']:.1%}")
    print(f"\nATS Prediction: {sim_pred['against_spread']['prediction']}")
    print(f"ATS Confidence: {sim_pred['against_spread']['confidence']:.1%}")
