#!/usr/bin/env python3
"""
College Basketball (CBB) Analytics Library

Statistical models and betting tools specifically designed for College Basketball.
Includes pace-adjusted metrics, March Madness modeling, conference tournament analysis,
and college basketball-specific betting calculations.
"""

import math
import random
from typing import Dict, List, Tuple, Optional
from enum import Enum


class CBBConference(Enum):
    """Major college basketball conferences"""
    BIG_EAST = "Big East"
    BIG_TEN = "Big Ten"
    BIG_12 = "Big 12"
    ACC = "ACC"
    SEC = "SEC"
    PAC_12 = "Pac-12"
    AAC = "AAC"
    MOUNTAIN_WEST = "Mountain West"
    WEST_COAST = "West Coast"
    ATLANTIC_10 = "Atlantic 10"
    CONFERENCE_USA = "C-USA"
    MAC = "MAC"
    SUN_BELT = "Sun Belt"
    MID_AMERICAN = "Mid-American"
    OTHER = "Other"


class CBBAnalytics:
    """College Basketball-specific betting analytics and simulations"""

    # Conference strength ratings (KenPom-style, relative to average)
    CONFERENCE_RATINGS = {
        CBBConference.BIG_EAST: 2.5,
        CBBConference.BIG_TEN: 2.3,
        CBBConference.BIG_12: 2.0,
        CBBConference.ACC: 1.8,
        CBBConference.SEC: 1.5,
        CBBConference.PAC_12: 1.0,
        CBBConference.MOUNTAIN_WEST: 0.5,
        CBBConference.WEST_COAST: 0.3,
        CBBConference.ATLANTIC_10: 0.2,
        CBBConference.AAC: 0.0,
        CBBConference.CONFERENCE_USA: -1.5,
        CBBConference.MAC: -2.0,
        CBBConference.SUN_BELT: -2.5,
        CBBConference.MID_AMERICAN: -2.0,
        CBBConference.OTHER: -3.0
    }

    # Average CBB statistics
    AVG_POINTS_PER_GAME = 72.0  # Lower than NBA
    AVG_TOTAL_POINTS = 144.0     # Lower scoring
    AVG_HOME_ADVANTAGE = 4.0     # Larger than NBA (student sections!)
    MAX_HOME_ADVANTAGE = 8.0     # Duke Cameron Indoor, Kansas Allen Fieldhouse
    AVG_PACE = 70.0              # Possessions per 40 minutes (slower than NBA)
    AVG_OFFENSIVE_RATING = 103.0  # Points per 100 possessions

    @staticmethod
    def calculate_pace_adjusted_total(
        team1_pace: float,
        team2_pace: float,
        team1_off_rating: float,
        team2_off_rating: float,
        team1_def_rating: float,
        team2_def_rating: float,
        is_conference_game: bool = False
    ) -> Dict:
        """
        Calculate expected total using pace and efficiency metrics

        Args:
            team1_pace: Team 1 pace (possessions per 40 min)
            team2_pace: Team 2 pace
            team1_off_rating: Team 1 offensive rating (pts per 100 poss)
            team2_off_rating: Team 2 offensive rating
            team1_def_rating: Team 1 defensive rating (pts allowed per 100 poss)
            team2_def_rating: Team 2 defensive rating
            is_conference_game: Conference games tend to be slower

        Returns:
            Expected scoring for both teams
        """
        # Combined pace
        game_pace = (team1_pace + team2_pace) / 2

        # Conference games are typically slower and grindier
        if is_conference_game:
            game_pace *= 0.96

        # Team 1 expected points
        # Based on their offense vs opponent's defense
        team1_efficiency = (team1_off_rating + team2_def_rating) / 2
        team1_expected = (team1_efficiency / 100) * game_pace

        # Team 2 expected points
        team2_efficiency = (team2_off_rating + team1_def_rating) / 2
        team2_expected = (team2_efficiency / 100) * game_pace

        return {
            'team1_expected': team1_expected,
            'team2_expected': team2_expected,
            'total_expected': team1_expected + team2_expected,
            'game_pace': game_pace,
            'is_conference_game': is_conference_game
        }

    @staticmethod
    def calculate_spread_probability(
        team_rating: float,
        opponent_rating: float,
        spread: float,
        is_home: bool = True,
        home_advantage: Optional[float] = None,
        neutral_site: bool = False,
        team_conference: Optional[CBBConference] = None,
        opponent_conference: Optional[CBBConference] = None,
        is_conference_game: bool = False
    ) -> Dict:
        """
        Calculate probability of covering the spread

        Args:
            team_rating: Team power rating (e.g., KenPom, NET)
            opponent_rating: Opponent power rating
            spread: Point spread (negative means favorite)
            is_home: Whether team is playing at home
            home_advantage: Custom home court advantage (overrides default)
            neutral_site: Neutral site game (no home court advantage)
            team_conference: Team's conference
            opponent_conference: Opponent's conference
            is_conference_game: Whether this is a conference game

        Returns:
            Cover probability and analysis
        """
        # Adjust for home court advantage
        if home_advantage is None:
            home_advantage = CBBAnalytics.AVG_HOME_ADVANTAGE

        home_advantage = max(0.0, min(home_advantage, CBBAnalytics.MAX_HOME_ADVANTAGE))
        if neutral_site:
            home_adj = 0.0
        else:
            home_adj = home_advantage if is_home else -home_advantage

        # Conference strength adjustment
        conf_adj = 0.0
        if team_conference and opponent_conference and not is_conference_game:
            team_conf_rating = CBBAnalytics.CONFERENCE_RATINGS.get(team_conference, 0.0)
            opp_conf_rating = CBBAnalytics.CONFERENCE_RATINGS.get(opponent_conference, 0.0)
            conf_adj = (team_conf_rating - opp_conf_rating) * 0.4

        # Expected point differential
        expected_diff = (team_rating - opponent_rating) + home_adj + conf_adj

        # Adjusted for spread
        adjusted_diff = expected_diff - spread

        # College basketball has higher variance than NBA due to:
        # - Shorter games (40 min vs 48 min)
        # - Less consistent shooting
        # - Greater talent disparities
        std_dev = 12.5  # vs 11.0 for NBA

        # For mismatches, increase variance
        if abs(spread) > 15:
            std_dev = 14.0

        # Z-score
        z_score = adjusted_diff / std_dev

        # Probability
        cover_prob = CBBAnalytics._normal_cdf(z_score)

        return {
            'cover_probability': cover_prob,
            'expected_margin': expected_diff,
            'spread': spread,
            'home_advantage_used': home_adj,
            'conference_adjustment': conf_adj,
            'is_conference_game': is_conference_game,
            'neutral_site': neutral_site
        }

    @staticmethod
    def calculate_total_probability(
        team1_avg: float,
        team2_avg: float,
        total_line: float,
        pace_factor: float = 1.0,
        is_conference_game: bool = False
    ) -> Dict:
        """
        Calculate over/under probability for game total

        Args:
            team1_avg: Team 1 average points per game
            team2_avg: Team 2 average points per game
            total_line: Over/under line
            pace_factor: Game pace adjustment (1.0 = normal)
            is_conference_game: Conference games tend to be lower scoring

        Returns:
            Over/under probabilities
        """
        # Expected total
        expected_total = (team1_avg + team2_avg) * pace_factor

        # Conference game adjustment (familiarity reduces scoring)
        if is_conference_game:
            expected_total *= 0.95

        # Standard deviation for total points ~12 points
        std_dev = 12.0

        # Calculate z-score for over
        z_score = (total_line - expected_total) / std_dev

        # Under probability = CDF(z)
        under_prob = CBBAnalytics._normal_cdf(z_score)
        over_prob = 1 - under_prob

        return {
            'over_probability': over_prob,
            'under_probability': under_prob,
            'expected_total': expected_total,
            'line': total_line,
            'difference': expected_total - total_line,
            'is_conference_game': is_conference_game
        }

    @staticmethod
    def calculate_first_half_probability(
        team_rating: float,
        opponent_rating: float,
        first_half_spread: float,
        is_home: bool = True,
        home_advantage: Optional[float] = None,
        neutral_site: bool = False
    ) -> Dict:
        """
        Calculate first half spread probability

        College basketball first halves tend to be closer

        Args:
            team_rating: Team power rating
            opponent_rating: Opponent power rating
            first_half_spread: First half point spread
            is_home: Whether team is playing at home
            home_advantage: Custom home court advantage (overrides default)
            neutral_site: Neutral site game (no home court advantage)

        Returns:
            First half cover probability
        """
        # First half home advantage is slightly less
        if home_advantage is None:
            home_advantage = CBBAnalytics.AVG_HOME_ADVANTAGE

        home_advantage = max(0.0, min(home_advantage, CBBAnalytics.MAX_HOME_ADVANTAGE)) * 0.75
        if neutral_site:
            home_adj = 0.0
        else:
            home_adj = home_advantage if is_home else -home_advantage

        # Expected point differential (scale to first half ~48% of scoring)
        full_game_diff = (team_rating - opponent_rating) + home_adj
        first_half_diff = full_game_diff * 0.48

        # Adjusted differential accounting for spread
        adjusted_diff = first_half_diff - first_half_spread

        # Higher variance in first half
        std_dev = 9.0

        # Calculate z-score
        z_score = adjusted_diff / std_dev

        # Convert to probability
        cover_prob = CBBAnalytics._normal_cdf(z_score)

        return {
            'cover_probability': cover_prob,
            'expected_margin': first_half_diff,
            'spread': first_half_spread,
            'neutral_site': neutral_site
        }

    @staticmethod
    def calculate_march_madness_upset_probability(
        higher_seed: int,
        lower_seed: int,
        rating_diff: float
    ) -> Dict:
        """
        Calculate upset probability in NCAA Tournament

        Args:
            higher_seed: Better seed (1-16, lower number = better)
            lower_seed: Worse seed (1-16, higher number = worse)
            rating_diff: Point difference in power ratings

        Returns:
            Upset probability and analysis
        """
        # Seed difference
        seed_diff = lower_seed - higher_seed

        # Historical upset rates by seed difference (higher seed loses)
        # Approximate NCAA tournament averages; larger gaps mean fewer upsets.
        historical_upset_rates = {
            1: 0.50,   # 8 vs 9 (essentially 50/50)
            2: 0.42,   # 7 vs 9 / 8 vs 10
            3: 0.40,   # 7 vs 10
            4: 0.33,   # 6 vs 10 / 6 vs 11
            5: 0.30,   # 6 vs 11
            6: 0.28,   # 5 vs 11 / 6 vs 12
            7: 0.35,   # 5 vs 12 (most common upset)
            8: 0.24,   # 4 vs 12 / 5 vs 13
            9: 0.20,   # 4 vs 13
            10: 0.18,  # 3 vs 13 / 4 vs 14
            11: 0.16,  # 3 vs 14
            12: 0.12,  # 2 vs 14 / 3 vs 15
            13: 0.08,  # 2 vs 15
            14: 0.04,  # 2 vs 16
            15: 0.01   # 1 vs 16 (extremely rare)
        }

        base_upset_prob = historical_upset_rates.get(seed_diff, 0.50)

        # Adjust based on actual rating difference
        # If rating difference is less than expected, upset more likely
        expected_rating_diff = seed_diff * 3.5  # Rough estimate
        adjustment_scale = 0.02 * (base_upset_prob / 0.5)
        rating_adjustment = (expected_rating_diff - rating_diff) * adjustment_scale

        adjusted_upset_prob = max(0.01, min(0.99, base_upset_prob + rating_adjustment))

        # Determine upset category
        if seed_diff >= 5:
            category = "Major upset"
        elif seed_diff >= 3:
            category = "Moderate upset"
        elif seed_diff >= 1:
            category = "Minor upset"
        else:
            category = "Favorite wins"

        return {
            'higher_seed': higher_seed,
            'lower_seed': lower_seed,
            'seed_difference': seed_diff,
            'base_upset_probability': base_upset_prob,
            'adjusted_upset_probability': adjusted_upset_prob,
            'favorite_probability': 1 - adjusted_upset_prob,
            'rating_difference': rating_diff,
            'category': category
        }

    @staticmethod
    def calculate_tournament_probability(
        team_seed: int,
        team_rating: float,
        bracket_region: str = "Midwest"
    ) -> Dict:
        """
        Calculate probability of reaching different tournament rounds

        Args:
            team_seed: Tournament seed (1-16)
            team_rating: Power rating (KenPom, NET, etc.)
            bracket_region: Tournament region

        Returns:
            Probabilities for each round
        """
        # Base probabilities by seed (historical averages)
        round_32_probs = {
            1: 0.995, 2: 0.938, 3: 0.848, 4: 0.792,
            5: 0.643, 6: 0.621, 7: 0.602, 8: 0.517,
            9: 0.483, 10: 0.398, 11: 0.379, 12: 0.357,
            13: 0.208, 14: 0.152, 15: 0.062, 16: 0.005
        }

        sweet_16_probs = {
            1: 0.837, 2: 0.612, 3: 0.465, 4: 0.393,
            5: 0.271, 6: 0.253, 7: 0.239, 8: 0.187,
            9: 0.165, 10: 0.112, 11: 0.097, 12: 0.085,
            13: 0.032, 14: 0.017, 15: 0.005, 16: 0.000
        }

        elite_8_probs = {
            1: 0.517, 2: 0.296, 3: 0.185, 4: 0.142,
            5: 0.089, 6: 0.077, 7: 0.069, 8: 0.045,
            9: 0.037, 10: 0.021, 11: 0.017, 12: 0.013,
            13: 0.004, 14: 0.001, 15: 0.000, 16: 0.000
        }

        final_4_probs = {
            1: 0.244, 2: 0.115, 3: 0.062, 4: 0.041,
            5: 0.022, 6: 0.017, 7: 0.014, 8: 0.008,
            9: 0.006, 10: 0.003, 11: 0.002, 12: 0.001,
            13: 0.000, 14: 0.000, 15: 0.000, 16: 0.000
        }

        championship_probs = {
            1: 0.098, 2: 0.041, 3: 0.019, 4: 0.011,
            5: 0.005, 6: 0.004, 7: 0.003, 8: 0.001,
            9: 0.001, 10: 0.000, 11: 0.000, 12: 0.000,
            13: 0.000, 14: 0.000, 15: 0.000, 16: 0.000
        }

        # Adjust based on team rating
        rating_factor = (team_rating - 15) / 100  # Normalize around average

        return {
            'seed': team_seed,
            'rating': team_rating,
            'region': bracket_region,
            'round_of_32': CBBAnalytics._clamp_probability(
                round_32_probs.get(team_seed, 0.5) * (1 + rating_factor)
            ),
            'sweet_16': CBBAnalytics._clamp_probability(
                sweet_16_probs.get(team_seed, 0.2) * (1 + rating_factor * 1.5)
            ),
            'elite_8': CBBAnalytics._clamp_probability(
                elite_8_probs.get(team_seed, 0.1) * (1 + rating_factor * 2)
            ),
            'final_4': CBBAnalytics._clamp_probability(
                final_4_probs.get(team_seed, 0.05) * (1 + rating_factor * 2.5)
            ),
            'championship': CBBAnalytics._clamp_probability(
                championship_probs.get(team_seed, 0.01) * (1 + rating_factor * 3)
            )
        }

    @staticmethod
    def simulate_game(
        home_rating: float,
        away_rating: float,
        home_advantage: Optional[float] = None,
        seed: Optional[int] = None,
        neutral_site: bool = False,
        rng: Optional[random.Random] = None
    ) -> Dict:
        """
        Simulate a single college basketball game

        Args:
            home_rating: Home team rating (average points)
            away_rating: Away team rating (average points)
            home_advantage: Custom home court advantage
            seed: Random seed for reproducibility (ignored if rng provided)
            neutral_site: Neutral site game (no home court advantage)
            rng: Optional random generator for reproducible simulations

        Returns:
            Game result
        """
        if rng is None:
            rng = random.Random(seed) if seed is not None else random

        # Add home court advantage
        if home_advantage is None:
            home_advantage = CBBAnalytics.AVG_HOME_ADVANTAGE

        home_advantage = max(0.0, min(home_advantage, CBBAnalytics.MAX_HOME_ADVANTAGE))
        home_adj = home_rating if neutral_site else home_rating + home_advantage
        away_adj = away_rating

        # Simulate scores using normal distribution
        home_score = max(0, int(rng.gauss(home_adj, 10) + 0.5))
        away_score = max(0, int(rng.gauss(away_adj, 10) + 0.5))

        margin = home_score - away_score
        total = home_score + away_score

        # Handle overtime (roughly 6% of games)
        if margin == 0:
            # Overtime scoring (typically 5-10 points per team)
            home_ot = rng.randint(5, 10)
            away_ot = rng.randint(5, 10)

            if home_ot > away_ot:
                home_score += home_ot
                away_score += away_ot - 1
                result = 'home_win_ot'
            else:
                away_score += away_ot
                home_score += home_ot - 1
                result = 'away_win_ot'

            margin = home_score - away_score
            total = home_score + away_score
        elif margin > 0:
            result = 'home_win'
        else:
            result = 'away_win'

        return {
            'home_score': home_score,
            'away_score': away_score,
            'margin': abs(margin),
            'total': total,
            'result': result,
            'is_blowout': abs(margin) > 20,
            'neutral_site': neutral_site
        }

    @staticmethod
    def simulate_season(
        teams: Dict[str, float],
        games_per_team: int = 30,
        conference_teams: Optional[Dict[str, CBBConference]] = None,
        seed: Optional[int] = None
    ) -> Dict:
        """
        Simulate a college basketball season

        Args:
            teams: Dictionary of team names to ratings
            games_per_team: Games per team (CBB regular season ~30)
            conference_teams: Dictionary mapping teams to conferences
            seed: Random seed

        Returns:
            Season results with standings
        """
        rng = random.Random(seed) if seed is not None else random

        team_names = list(teams.keys())
        standings = {team: {'wins': 0, 'losses': 0, 'pf': 0, 'pa': 0, 'conf_wins': 0, 'conf_losses': 0}
                    for team in team_names}

        matches = []
        total_games = (len(team_names) * games_per_team) // 2

        for _ in range(total_games):
            # Random matchup
            home_team = rng.choice(team_names)
            away_team = rng.choice([t for t in team_names if t != home_team])

            # Determine if conference game
            is_conf_game = False
            if conference_teams:
                is_conf_game = (home_team in conference_teams and
                              away_team in conference_teams and
                              conference_teams[home_team] == conference_teams[away_team])

            # Simulate game
            game = CBBAnalytics.simulate_game(
                teams[home_team],
                teams[away_team],
                rng=rng
            )

            # Update standings
            standings[home_team]['pf'] += game['home_score']
            standings[home_team]['pa'] += game['away_score']
            standings[away_team]['pf'] += game['away_score']
            standings[away_team]['pa'] += game['home_score']

            if 'home_win' in game['result']:
                standings[home_team]['wins'] += 1
                standings[away_team]['losses'] += 1
                if is_conf_game:
                    standings[home_team]['conf_wins'] += 1
                    standings[away_team]['conf_losses'] += 1
            elif 'away_win' in game['result']:
                standings[away_team]['wins'] += 1
                standings[home_team]['losses'] += 1
                if is_conf_game:
                    standings[away_team]['conf_wins'] += 1
                    standings[home_team]['conf_losses'] += 1

            matches.append({
                'home': home_team,
                'away': away_team,
                'home_score': game['home_score'],
                'away_score': game['away_score'],
                'margin': game['margin'],
                'is_conference_game': is_conf_game
            })

        # Calculate winning percentage
        for team in standings:
            games = standings[team]['wins'] + standings[team]['losses']
            if games > 0:
                standings[team]['win_pct'] = standings[team]['wins'] / games
            else:
                standings[team]['win_pct'] = 0.0

        # Sort by win percentage
        sorted_standings = sorted(
            standings.items(),
            key=lambda x: (x[1]['win_pct'], x[1]['pf'] - x[1]['pa']),
            reverse=True
        )

        return {
            'standings': dict(sorted_standings),
            'matches': matches
        }

    @staticmethod
    def _normal_cdf(z: float) -> float:
        """
        Cumulative distribution function for standard normal distribution
        """
        return 0.5 * (1 + math.erf(z / math.sqrt(2)))

    @staticmethod
    def _clamp_probability(value: float) -> float:
        """
        Clamp probability to [0.0, 0.999] to avoid invalid outputs.
        """
        return max(0.0, min(0.999, value))


def calculate_cbb_kenpom_probability(
    kenpom_1: float,
    kenpom_2: float,
    home_advantage: float = 4.0
) -> float:
    """
    Calculate win probability based on KenPom ratings

    Args:
        kenpom_1: Team 1 KenPom rating
        kenpom_2: Team 2 KenPom rating
        home_advantage: Points to subtract to normalize to a neutral court

    Returns:
        Probability of team 1 winning
    """
    expected_margin = kenpom_1 - kenpom_2 - home_advantage
    std_dev = 12.0

    z_score = expected_margin / std_dev
    return CBBAnalytics._normal_cdf(z_score)


if __name__ == '__main__':
    # Example usage
    print("College Basketball (CBB) Analytics Library")
    print("=" * 70)

    # Example 1: Spread analysis
    print("\nExample 1: Spread Analysis")
    result = CBBAnalytics.calculate_spread_probability(
        team_rating=78.0,  # Strong team
        opponent_rating=68.0,
        spread=-6.5,
        is_home=True
    )
    print(f"Cover Probability: {result['cover_probability']*100:.1f}%")
    print(f"Expected Margin: {result['expected_margin']:.1f}")

    # Example 2: March Madness upset
    print("\nExample 2: March Madness Upset Probability")
    upset = CBBAnalytics.calculate_march_madness_upset_probability(
        higher_seed=5,
        lower_seed=12,
        rating_diff=8.0
    )
    print(f"Matchup: {upset['higher_seed']} seed vs {upset['lower_seed']} seed")
    print(f"Upset Probability: {upset['adjusted_upset_probability']*100:.1f}%")
    print(f"Category: {upset['category']}")

    # Example 3: Tournament probability
    print("\nExample 3: Tournament Run Probabilities")
    tournament = CBBAnalytics.calculate_tournament_probability(
        team_seed=3,
        team_rating=25.0,
        bracket_region="East"
    )
    print(f"Seed: {tournament['seed']}")
    print(f"Sweet 16: {tournament['sweet_16']*100:.1f}%")
    print(f"Elite 8: {tournament['elite_8']*100:.1f}%")
    print(f"Final 4: {tournament['final_4']*100:.1f}%")
    print(f"Championship: {tournament['championship']*100:.1f}%")

    # Example 4: Total analysis
    print("\nExample 4: Total Analysis")
    total = CBBAnalytics.calculate_total_probability(
        team1_avg=75.5,
        team2_avg=71.3,
        total_line=145.5,
        is_conference_game=True
    )
    print(f"Over Probability: {total['over_probability']*100:.1f}%")
    print(f"Expected Total: {total['expected_total']:.1f}")
    print(f"Conference Game: {total['is_conference_game']}")
