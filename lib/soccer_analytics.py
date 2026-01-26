#!/usr/bin/env python3
"""
Soccer Analytics Library

Statistical models and betting tools specifically designed for soccer (football).
Includes 3-way moneyline, Asian handicap, over/under goals, both teams to score,
and league-specific adjustments for major competitions.
"""

import math
import random
from typing import Dict, List, Tuple, Optional
from enum import Enum
from lib.poisson_calculator import PoissonCalculator


class League(Enum):
    """Major soccer leagues and competitions"""
    # Top 5 European leagues
    PREMIER_LEAGUE = "English Premier League"
    LA_LIGA = "La Liga"
    BUNDESLIGA = "Bundesliga"
    SERIE_A = "Serie A"
    LIGUE_1 = "Ligue 1"

    # Other major leagues
    MLS = "Major League Soccer"
    EREDIVISIE = "Eredivisie"
    LIGA_MX = "Liga MX"
    PRIMEIRA_LIGA = "Primeira Liga"
    SCOTTISH_PREM = "Scottish Premiership"

    # International competitions
    CHAMPIONS_LEAGUE = "UEFA Champions League"
    EUROPA_LEAGUE = "UEFA Europa League"
    WORLD_CUP = "FIFA World Cup"
    EUROS = "UEFA European Championship"

    # Other
    OTHER = "Other League"


class SoccerAnalytics:
    """Soccer-specific betting analytics and simulations"""

    # League characteristics (average goals per game)
    LEAGUE_GOALS = {
        League.PREMIER_LEAGUE: 2.82,
        League.LA_LIGA: 2.65,
        League.BUNDESLIGA: 3.15,  # Highest scoring top league
        League.SERIE_A: 2.70,
        League.LIGUE_1: 2.75,
        League.MLS: 2.95,
        League.EREDIVISIE: 3.20,
        League.LIGA_MX: 2.80,
        League.PRIMEIRA_LIGA: 2.60,
        League.SCOTTISH_PREM: 2.90,
        League.CHAMPIONS_LEAGUE: 2.75,
        League.EUROPA_LEAGUE: 2.85,
        League.WORLD_CUP: 2.50,  # Typically lower scoring
        League.EUROS: 2.40,
        League.OTHER: 2.70
    }

    # Home advantage by league (goals advantage)
    HOME_ADVANTAGE = {
        League.PREMIER_LEAGUE: 0.35,
        League.LA_LIGA: 0.40,
        League.BUNDESLIGA: 0.38,
        League.SERIE_A: 0.35,
        League.LIGUE_1: 0.37,
        League.MLS: 0.30,  # Travel is huge factor
        League.EREDIVISIE: 0.35,
        League.LIGA_MX: 0.42,  # Strong home advantage
        League.PRIMEIRA_LIGA: 0.38,
        League.SCOTTISH_PREM: 0.40,
        League.CHAMPIONS_LEAGUE: 0.30,  # Elite teams, less advantage
        League.EUROPA_LEAGUE: 0.32,
        League.WORLD_CUP: 0.15,  # Neutral sites mostly
        League.EUROS: 0.20,
        League.OTHER: 0.35
    }

    # Draw probability by league (historical)
    DRAW_RATE = {
        League.PREMIER_LEAGUE: 0.26,
        League.LA_LIGA: 0.28,
        League.BUNDESLIGA: 0.24,
        League.SERIE_A: 0.27,
        League.LIGUE_1: 0.26,
        League.MLS: 0.23,
        League.EREDIVISIE: 0.25,
        League.LIGA_MX: 0.27,
        League.PRIMEIRA_LIGA: 0.28,
        League.SCOTTISH_PREM: 0.25,
        League.CHAMPIONS_LEAGUE: 0.24,
        League.EUROPA_LEAGUE: 0.26,
        League.WORLD_CUP: 0.30,
        League.EUROS: 0.32,
        League.OTHER: 0.27
    }

    @staticmethod
    def calculate_3way_moneyline(
        home_goals_avg: float,
        away_goals_avg: float,
        league: League = League.PREMIER_LEAGUE,
        home_advantage: Optional[float] = None
    ) -> Dict:
        """
        Calculate 3-way moneyline probability (home win, draw, away win)

        Args:
            home_goals_avg: Home team average goals per game
            away_goals_avg: Away team average goals per game
            league: League/competition
            home_advantage: Custom home advantage (overrides league default)

        Returns:
            Dictionary with home/draw/away probabilities
        """
        # Apply home advantage
        if home_advantage is None:
            home_advantage = SoccerAnalytics.HOME_ADVANTAGE.get(league, 0.35)

        home_lambda = home_goals_avg + home_advantage
        away_lambda = away_goals_avg

        # Use Poisson distribution
        results = PoissonCalculator.calculate_match_probabilities(
            home_lambda,
            away_lambda,
            max_goals=10
        )

        return {
            'home_win_probability': results['home_win'],
            'draw_probability': results['draw'],
            'away_win_probability': results['away_win'],
            'home_expected_goals': home_lambda,
            'away_expected_goals': away_lambda,
            'league': league.value
        }

    @staticmethod
    def calculate_double_chance(
        home_goals_avg: float,
        away_goals_avg: float,
        league: League = League.PREMIER_LEAGUE
    ) -> Dict:
        """
        Calculate double chance probabilities

        Double chance covers two of three outcomes:
        - Home or Draw (1X)
        - Away or Draw (X2)
        - Home or Away (12)

        Args:
            home_goals_avg: Home team average goals
            away_goals_avg: Away team average goals
            league: League/competition

        Returns:
            Double chance probabilities
        """
        three_way = SoccerAnalytics.calculate_3way_moneyline(
            home_goals_avg,
            away_goals_avg,
            league
        )

        return {
            'home_or_draw': three_way['home_win_probability'] + three_way['draw_probability'],
            'away_or_draw': three_way['away_win_probability'] + three_way['draw_probability'],
            'home_or_away': three_way['home_win_probability'] + three_way['away_win_probability'],
            'league': league.value
        }

    @staticmethod
    def calculate_asian_handicap(
        home_goals_avg: float,
        away_goals_avg: float,
        handicap: float,
        league: League = League.PREMIER_LEAGUE
    ) -> Dict:
        """
        Calculate Asian handicap probability

        Asian handicap eliminates the draw by giving one team a head start
        Example: -0.5, -1.0, -1.5, +0.5, +1.0, etc.

        Args:
            home_goals_avg: Home team average goals
            away_goals_avg: Away team average goals
            handicap: Handicap (negative = home favored, positive = away favored)
            league: League/competition

        Returns:
            Asian handicap probabilities
        """
        home_advantage = SoccerAnalytics.HOME_ADVANTAGE.get(league, 0.35)
        home_lambda = home_goals_avg + home_advantage
        away_lambda = away_goals_avg

        results = PoissonCalculator.calculate_match_probabilities(
            home_lambda,
            away_lambda,
            max_goals=10
        )

        prob_matrix = results['prob_matrix']

        # Calculate handicap probabilities
        home_cover = 0.0
        away_cover = 0.0
        push = 0.0

        for home_score in range(len(prob_matrix)):
            for away_score in range(len(prob_matrix[0])):
                prob = prob_matrix[home_score][away_score]

                # Apply handicap
                adjusted_home = home_score + handicap

                if adjusted_home > away_score:
                    home_cover += prob
                elif adjusted_home < away_score:
                    away_cover += prob
                else:
                    # Push - stake returned
                    push += prob

        return {
            'home_cover_probability': home_cover,
            'away_cover_probability': away_cover,
            'push_probability': push,
            'handicap': handicap,
            'expected_margin': home_lambda - away_lambda,
            'league': league.value
        }

    @staticmethod
    def calculate_total_goals(
        home_goals_avg: float,
        away_goals_avg: float,
        total_line: float,
        league: League = League.PREMIER_LEAGUE
    ) -> Dict:
        """
        Calculate over/under probability for total goals

        Args:
            home_goals_avg: Home team average goals
            away_goals_avg: Away team average goals
            total_line: Over/under line (e.g., 2.5, 3.5)
            league: League/competition

        Returns:
            Over/under probabilities
        """
        home_advantage = SoccerAnalytics.HOME_ADVANTAGE.get(league, 0.35)
        home_lambda = home_goals_avg + home_advantage
        away_lambda = away_goals_avg

        # Calculate total goals probabilities
        results = PoissonCalculator.calculate_total_probabilities(
            home_lambda,
            away_lambda,
            total_line,
            max_goals=10
        )

        return {
            'over_probability': results['over_probability'],
            'under_probability': results['under_probability'],
            'expected_total': home_lambda + away_lambda,
            'line': total_line,
            'league': league.value
        }

    @staticmethod
    def calculate_both_teams_to_score(
        home_goals_avg: float,
        away_goals_avg: float,
        home_goals_against_avg: float,
        away_goals_against_avg: float,
        league: League = League.PREMIER_LEAGUE
    ) -> Dict:
        """
        Calculate both teams to score (BTTS) probability

        Args:
            home_goals_avg: Home team average goals scored
            away_goals_avg: Away team average goals scored
            home_goals_against_avg: Home team average goals conceded
            away_goals_against_avg: Away team average goals conceded
            league: League/competition

        Returns:
            BTTS probabilities
        """
        home_advantage = SoccerAnalytics.HOME_ADVANTAGE.get(league, 0.35)

        # Home team scoring
        home_attack = home_goals_avg + home_advantage
        # Away team scoring (against home defense)
        away_attack = away_goals_avg

        # Probability home scores at least 1
        home_scores = 1 - PoissonCalculator.poisson_probability(0, home_attack)

        # Probability away scores at least 1
        away_scores = 1 - PoissonCalculator.poisson_probability(0, away_attack)

        # Both teams score (independent events)
        btts_yes = home_scores * away_scores
        btts_no = 1 - btts_yes

        return {
            'btts_yes_probability': btts_yes,
            'btts_no_probability': btts_no,
            'home_clean_sheet_probability': 1 - away_scores,
            'away_clean_sheet_probability': 1 - home_scores,
            'league': league.value
        }

    @staticmethod
    def calculate_correct_score_probabilities(
        home_goals_avg: float,
        away_goals_avg: float,
        league: League = League.PREMIER_LEAGUE,
        top_n: int = 10
    ) -> List[Dict]:
        """
        Calculate probabilities for most likely correct scores

        Args:
            home_goals_avg: Home team average goals
            away_goals_avg: Away team average goals
            league: League/competition
            top_n: Number of most likely scores to return

        Returns:
            List of most likely scores with probabilities
        """
        home_advantage = SoccerAnalytics.HOME_ADVANTAGE.get(league, 0.35)
        home_lambda = home_goals_avg + home_advantage
        away_lambda = away_goals_avg

        results = PoissonCalculator.calculate_match_probabilities(
            home_lambda,
            away_lambda,
            max_goals=8
        )

        prob_matrix = results['prob_matrix']

        # Collect all scores with probabilities
        scores = []
        for home_score in range(len(prob_matrix)):
            for away_score in range(len(prob_matrix[0])):
                prob = prob_matrix[home_score][away_score]

                # Determine result type
                if home_score > away_score:
                    result = "Home Win"
                elif home_score < away_score:
                    result = "Away Win"
                else:
                    result = "Draw"

                scores.append({
                    'home_score': home_score,
                    'away_score': away_score,
                    'score': f"{home_score}-{away_score}",
                    'probability': prob,
                    'result': result
                })

        # Sort by probability
        scores.sort(key=lambda x: x['probability'], reverse=True)

        return scores[:top_n]

    @staticmethod
    def calculate_expected_goals_probability(
        home_xg: float,
        away_xg: float,
        league: League = League.PREMIER_LEAGUE
    ) -> Dict:
        """
        Calculate match probabilities using Expected Goals (xG) data

        xG is a more sophisticated metric than average goals

        Args:
            home_xg: Home team expected goals (xG)
            away_xg: Away team expected goals (xG)
            league: League/competition

        Returns:
            Match outcome probabilities based on xG
        """
        # xG already incorporates quality of chances
        # Apply smaller home advantage since xG is match-specific
        home_advantage = SoccerAnalytics.HOME_ADVANTAGE.get(league, 0.35) * 0.5

        home_lambda = home_xg + home_advantage
        away_lambda = away_xg

        results = PoissonCalculator.calculate_match_probabilities(
            home_lambda,
            away_lambda,
            max_goals=10
        )

        return {
            'home_win_probability': results['home_win'],
            'draw_probability': results['draw'],
            'away_win_probability': results['away_win'],
            'home_xg': home_xg,
            'away_xg': away_xg,
            'league': league.value
        }

    @staticmethod
    def calculate_first_half_probability(
        home_goals_avg: float,
        away_goals_avg: float,
        league: League = League.PREMIER_LEAGUE
    ) -> Dict:
        """
        Calculate first half betting probabilities

        First half tends to be lower scoring (roughly 42% of goals)

        Args:
            home_goals_avg: Home team average goals per game
            away_goals_avg: Away team average goals per game
            league: League/competition

        Returns:
            First half probabilities
        """
        # First half scoring rate (typically 42% of goals)
        first_half_rate = 0.42

        home_advantage = SoccerAnalytics.HOME_ADVANTAGE.get(league, 0.35)
        home_lambda = (home_goals_avg + home_advantage) * first_half_rate
        away_lambda = away_goals_avg * first_half_rate

        results = PoissonCalculator.calculate_match_probabilities(
            home_lambda,
            away_lambda,
            max_goals=6  # Lower max for first half
        )

        return {
            'home_win_probability': results['home_win'],
            'draw_probability': results['draw'],
            'away_win_probability': results['away_win'],
            'expected_total_goals': home_lambda + away_lambda,
            'league': league.value
        }

    @staticmethod
    def analyze_league_characteristics(league: League) -> Dict:
        """
        Get statistical characteristics of a league

        Args:
            league: League to analyze

        Returns:
            League statistics and betting characteristics
        """
        avg_goals = SoccerAnalytics.LEAGUE_GOALS.get(league, 2.70)
        home_adv = SoccerAnalytics.HOME_ADVANTAGE.get(league, 0.35)
        draw_rate = SoccerAnalytics.DRAW_RATE.get(league, 0.27)

        # Infer characteristics
        if avg_goals > 3.0:
            scoring_style = "High scoring"
        elif avg_goals > 2.6:
            scoring_style = "Average scoring"
        else:
            scoring_style = "Low scoring"

        if home_adv > 0.38:
            home_strength = "Strong home advantage"
        elif home_adv > 0.30:
            home_strength = "Moderate home advantage"
        else:
            home_strength = "Weak home advantage"

        return {
            'league': league.value,
            'avg_goals_per_game': avg_goals,
            'home_advantage': home_adv,
            'draw_rate': draw_rate,
            'scoring_style': scoring_style,
            'home_field_strength': home_strength,
            'betting_advice': SoccerAnalytics._get_league_betting_advice(league)
        }

    @staticmethod
    def _get_league_betting_advice(league: League) -> str:
        """Get betting advice based on league characteristics"""
        avg_goals = SoccerAnalytics.LEAGUE_GOALS.get(league, 2.70)
        draw_rate = SoccerAnalytics.DRAW_RATE.get(league, 0.27)

        if league == League.BUNDESLIGA:
            return "High scoring - favor overs, fewer draws"
        elif league == League.SERIE_A:
            return "Tactical, defensive - consider unders, respect draw"
        elif league == League.WORLD_CUP or league == League.EUROS:
            return "Cagey, high draw rate - avoid heavy favorites, value draws"
        elif league == League.MLS:
            return "Moderate scoring, travel impacts away teams significantly"
        elif avg_goals > 3.0:
            return "High scoring league - overs and BTTS have value"
        elif draw_rate > 0.28:
            return "High draw rate - double chance and draw bets have value"
        else:
            return "Balanced league - standard betting approaches work"

    @staticmethod
    def simulate_match(
        home_goals_avg: float,
        away_goals_avg: float,
        league: League = League.PREMIER_LEAGUE,
        seed: Optional[int] = None
    ) -> Dict:
        """
        Simulate a soccer match

        Args:
            home_goals_avg: Home team average goals
            away_goals_avg: Away team average goals
            league: League/competition
            seed: Random seed for reproducibility

        Returns:
            Match result
        """
        if seed is not None:
            random.seed(seed)

        home_advantage = SoccerAnalytics.HOME_ADVANTAGE.get(league, 0.35)
        home_lambda = home_goals_avg + home_advantage
        away_lambda = away_goals_avg

        # Simulate goals using Poisson distribution
        home_goals = PoissonCalculator.simulate_poisson(home_lambda)
        away_goals = PoissonCalculator.simulate_poisson(away_lambda)

        # Determine result
        if home_goals > away_goals:
            result = 'home_win'
        elif away_goals > home_goals:
            result = 'away_win'
        else:
            result = 'draw'

        total_goals = home_goals + away_goals

        return {
            'home_goals': home_goals,
            'away_goals': away_goals,
            'score': f"{home_goals}-{away_goals}",
            'result': result,
            'total_goals': total_goals,
            'league': league.value
        }

    @staticmethod
    def simulate_season(
        teams: Dict[str, float],
        league: League = League.PREMIER_LEAGUE,
        home_away_split: bool = True,
        seed: Optional[int] = None
    ) -> Dict:
        """
        Simulate a soccer season

        Args:
            teams: Dictionary of team names to attacking strength ratings
            league: League/competition
            home_away_split: Whether to play home and away matches
            seed: Random seed

        Returns:
            Season results with standings
        """
        if seed is not None:
            random.seed(seed)

        team_names = list(teams.keys())
        standings = {team: {'wins': 0, 'draws': 0, 'losses': 0,
                           'gf': 0, 'ga': 0, 'points': 0}
                    for team in team_names}

        matches = []

        # Generate fixtures
        for i, home_team in enumerate(team_names):
            for j, away_team in enumerate(team_names):
                if i == j:
                    continue

                # Simulate match
                match = SoccerAnalytics.simulate_match(
                    teams[home_team],
                    teams[away_team],
                    league
                )

                # Update standings
                standings[home_team]['gf'] += match['home_goals']
                standings[home_team]['ga'] += match['away_goals']
                standings[away_team]['gf'] += match['away_goals']
                standings[away_team]['ga'] += match['home_goals']

                if match['result'] == 'home_win':
                    standings[home_team]['wins'] += 1
                    standings[home_team]['points'] += 3
                    standings[away_team]['losses'] += 1
                elif match['result'] == 'away_win':
                    standings[away_team]['wins'] += 1
                    standings[away_team]['points'] += 3
                    standings[home_team]['losses'] += 1
                else:  # Draw
                    standings[home_team]['draws'] += 1
                    standings[home_team]['points'] += 1
                    standings[away_team]['draws'] += 1
                    standings[away_team]['points'] += 1

                matches.append({
                    'home': home_team,
                    'away': away_team,
                    'home_goals': match['home_goals'],
                    'away_goals': match['away_goals'],
                    'result': match['result']
                })

        # Sort by points (then goal difference)
        for team in standings:
            standings[team]['goal_diff'] = standings[team]['gf'] - standings[team]['ga']

        sorted_standings = sorted(
            standings.items(),
            key=lambda x: (x[1]['points'], x[1]['goal_diff'], x[1]['gf']),
            reverse=True
        )

        return {
            'standings': dict(sorted_standings),
            'matches': matches,
            'league': league.value
        }


if __name__ == '__main__':
    # Example usage
    print("Soccer Analytics Library")
    print("=" * 70)

    # Example 1: 3-way moneyline (Premier League)
    print("\nExample 1: 3-Way Moneyline (Man City vs Arsenal)")
    result = SoccerAnalytics.calculate_3way_moneyline(
        home_goals_avg=2.1,  # Man City at home
        away_goals_avg=1.8,  # Arsenal away
        league=League.PREMIER_LEAGUE
    )
    print(f"Home Win: {result['home_win_probability']*100:.1f}%")
    print(f"Draw: {result['draw_probability']*100:.1f}%")
    print(f"Away Win: {result['away_win_probability']*100:.1f}%")

    # Example 2: Asian handicap
    print("\nExample 2: Asian Handicap -1.0")
    handicap = SoccerAnalytics.calculate_asian_handicap(
        home_goals_avg=2.3,
        away_goals_avg=1.2,
        handicap=-1.0,
        league=League.PREMIER_LEAGUE
    )
    print(f"Home Cover (-1.0): {handicap['home_cover_probability']*100:.1f}%")
    print(f"Push: {handicap['push_probability']*100:.1f}%")
    print(f"Away Cover (+1.0): {handicap['away_cover_probability']*100:.1f}%")

    # Example 3: Total goals
    print("\nExample 3: Total Goals Over/Under 2.5")
    total = SoccerAnalytics.calculate_total_goals(
        home_goals_avg=2.1,
        away_goals_avg=1.8,
        total_line=2.5,
        league=League.PREMIER_LEAGUE
    )
    print(f"Over 2.5: {total['over_probability']*100:.1f}%")
    print(f"Under 2.5: {total['under_probability']*100:.1f}%")
    print(f"Expected Total: {total['expected_total']:.2f}")

    # Example 4: Both teams to score
    print("\nExample 4: Both Teams to Score")
    btts = SoccerAnalytics.calculate_both_teams_to_score(
        home_goals_avg=2.0,
        away_goals_avg=1.7,
        home_goals_against_avg=1.1,
        away_goals_against_avg=1.3,
        league=League.PREMIER_LEAGUE
    )
    print(f"BTTS Yes: {btts['btts_yes_probability']*100:.1f}%")
    print(f"BTTS No: {btts['btts_no_probability']*100:.1f}%")

    # Example 5: Most likely correct scores
    print("\nExample 5: Most Likely Correct Scores")
    scores = SoccerAnalytics.calculate_correct_score_probabilities(
        home_goals_avg=2.1,
        away_goals_avg=1.8,
        league=League.PREMIER_LEAGUE,
        top_n=5
    )
    for i, score in enumerate(scores, 1):
        print(f"{i}. {score['score']} ({score['result']}): {score['probability']*100:.1f}%")

    # Example 6: League characteristics
    print("\nExample 6: League Characteristics")
    leagues_to_compare = [League.PREMIER_LEAGUE, League.BUNDESLIGA, League.SERIE_A]
    for league in leagues_to_compare:
        analysis = SoccerAnalytics.analyze_league_characteristics(league)
        print(f"\n{analysis['league']}:")
        print(f"  Avg Goals: {analysis['avg_goals_per_game']:.2f}")
        print(f"  Draw Rate: {analysis['draw_rate']*100:.0f}%")
        print(f"  Style: {analysis['scoring_style']}")
        print(f"  Advice: {analysis['betting_advice']}")
