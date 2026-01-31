#!/usr/bin/env python3
"""
College Football (CFB) Analytics Library

Statistical models and betting tools specifically designed for College Football.
Includes spread analysis, totals modeling, conference strength adjustments,
and college football-specific betting calculations.
"""

import math
import random
from typing import Dict, List, Tuple, Optional
from enum import Enum


class Conference(Enum):
    """Major college football conferences"""
    SEC = "SEC"
    BIG_TEN = "Big Ten"
    BIG_12 = "Big 12"
    ACC = "ACC"
    PAC_12 = "Pac-12"
    AAC = "AAC"
    MOUNTAIN_WEST = "Mountain West"
    MAC = "MAC"
    SUN_BELT = "Sun Belt"
    CUSA = "C-USA"
    INDEPENDENT = "Independent"
    FCS = "FCS"


class CFBAnalytics:
    """College Football-specific betting analytics and simulations"""

    # College football key numbers (different from NFL due to bigger spreads)
    KEY_NUMBERS = {
        3: 0.118,   # Field goal - common but less than NFL
        7: 0.092,   # Touchdown
        10: 0.055,  # FG + TD
        14: 0.048,  # 2 TDs
        17: 0.035,  # FG + 2 TDs
        21: 0.032,  # 3 TDs
        24: 0.028,  # FG + 3 TDs
        28: 0.025,  # 4 TDs
        4: 0.038,   # TD + missed XP or safety
        6: 0.036,   # 2 FGs
        13: 0.032,  # TD + 2FG
        20: 0.028   # TD + FG + TD
    }

    # Conference strength ratings (relative to average FBS team)
    # Higher = stronger conference
    CONFERENCE_RATINGS = {
        Conference.SEC: 3.5,
        Conference.BIG_TEN: 3.0,
        Conference.BIG_12: 2.5,
        Conference.ACC: 2.0,
        Conference.PAC_12: 2.0,
        Conference.AAC: 0.0,
        Conference.MOUNTAIN_WEST: -1.0,
        Conference.MAC: -2.5,
        Conference.SUN_BELT: -2.0,
        Conference.CUSA: -3.0,
        Conference.FCS: -12.0,
        Conference.INDEPENDENT: 0.0
    }

    # Average CFB statistics
    AVG_POINTS_PER_GAME = 29.5
    AVG_HOME_ADVANTAGE = 3.5  # Larger than NFL
    AVG_TOTAL_POINTS = 59.0   # Higher scoring than NFL
    MAX_HOME_ADVANTAGE = 7.0  # Some venues (Death Valley, Camp Randall) have huge advantages
    MIN_HOME_ADVANTAGE = 1.5  # Neutral-site-like venues

    @staticmethod
    def calculate_spread_probability(
        team_rating: float,
        opponent_rating: float,
        spread: float,
        is_home: bool = True,
        home_advantage: Optional[float] = None,
        rivalry_game: bool = False,
        team_conference: Optional[Conference] = None,
        opponent_conference: Optional[Conference] = None,
        talent_composite_diff: Optional[float] = None
    ) -> Dict:
        """
        Calculate probability of covering the spread in college football

        Args:
            team_rating: Team power rating (e.g., SP+, FPI)
            opponent_rating: Opponent power rating
            spread: Point spread (negative means team is favorite)
            is_home: Whether team is playing at home
            home_advantage: Custom home field advantage (overrides default)
            rivalry_game: Whether this is a rivalry game (reduces home advantage)
            team_conference: Team's conference
            opponent_conference: Opponent's conference
            talent_composite_diff: Difference in recruiting rankings/talent (optional)

        Returns:
            Dictionary with cover probability and analysis
        """
        # Adjust for home field advantage
        if home_advantage is None:
            home_advantage = CFBAnalytics.AVG_HOME_ADVANTAGE

        # Rivalry games reduce home field advantage
        if rivalry_game:
            home_advantage *= 0.6

        home_adj = home_advantage if is_home else -home_advantage

        # Conference strength adjustment
        conf_adj = 0.0
        if team_conference and opponent_conference:
            team_conf_rating = CFBAnalytics.CONFERENCE_RATINGS.get(team_conference, 0.0)
            opp_conf_rating = CFBAnalytics.CONFERENCE_RATINGS.get(opponent_conference, 0.0)
            conf_adj = (team_conf_rating - opp_conf_rating) * 0.5

        # Talent composite adjustment (if recruiting rankings available)
        talent_adj = 0.0
        if talent_composite_diff is not None:
            # Each point of talent difference = ~0.15 points on field
            talent_adj = talent_composite_diff * 0.15

        # Expected point differential
        expected_diff = (team_rating - opponent_rating) + home_adj + conf_adj + talent_adj

        # Adjusted differential accounting for spread
        adjusted_diff = expected_diff - spread

        # Use normal distribution with higher variance than NFL
        # CFB has more volatility due to talent disparities
        # Standard deviation for CFB games ~16-18 points (vs 13.5 for NFL)
        std_dev = 17.0

        # For mismatches (large spread), increase variance
        if abs(spread) > 21:
            std_dev = 20.0
        elif abs(spread) > 14:
            std_dev = 18.5

        # Calculate z-score
        z_score = adjusted_diff / std_dev

        # Convert to probability using cumulative normal distribution
        cover_prob = CFBAnalytics._normal_cdf(z_score)

        # Push probability (for key numbers)
        push_prob = 0.0
        if abs(spread) in CFBAnalytics.KEY_NUMBERS:
            push_prob = CFBAnalytics.KEY_NUMBERS[abs(spread)] * 0.5

        return {
            'cover_probability': cover_prob * (1 - push_prob),
            'push_probability': push_prob,
            'lose_probability': (1 - cover_prob) * (1 - push_prob),
            'expected_margin': expected_diff,
            'spread': spread,
            'is_key_number': abs(spread) in CFBAnalytics.KEY_NUMBERS,
            'home_advantage_used': home_adj,
            'conference_adjustment': conf_adj,
            'talent_adjustment': talent_adj
        }

    @staticmethod
    def calculate_total_probability(
        team1_avg: float,
        team2_avg: float,
        total_line: float,
        pace_factor: float = 1.0,
        is_conference_game: bool = False,
        weather_impact: Optional[str] = None
    ) -> Dict:
        """
        Calculate over/under probability for game total

        Args:
            team1_avg: Team 1 average points per game
            team2_avg: Team 2 average points per game
            total_line: Over/under line
            pace_factor: Game pace adjustment (1.0 = normal)
            is_conference_game: Conference games tend to be lower scoring
            weather_impact: "heavy_wind", "rain", "snow", or None

        Returns:
            Dictionary with over/under probabilities
        """
        # Expected total
        expected_total = (team1_avg + team2_avg) * pace_factor

        # Conference game adjustment (familiarity reduces scoring)
        if is_conference_game:
            expected_total *= 0.95

        # Weather adjustments
        if weather_impact == "heavy_wind":
            expected_total *= 0.90  # Significant impact on passing
        elif weather_impact == "rain":
            expected_total *= 0.93
        elif weather_impact == "snow":
            expected_total *= 0.88

        # Standard deviation for total points ~15 points
        std_dev = 15.0

        # Calculate z-score for over
        z_score = (total_line - expected_total) / std_dev

        # Under probability = CDF(z)
        under_prob = CFBAnalytics._normal_cdf(z_score)
        over_prob = 1 - under_prob

        return {
            'over_probability': over_prob,
            'under_probability': under_prob,
            'expected_total': expected_total,
            'line': total_line,
            'difference': expected_total - total_line,
            'weather_impact': weather_impact,
            'is_conference_game': is_conference_game
        }

    @staticmethod
    def calculate_first_half_probability(
        team_rating: float,
        opponent_rating: float,
        first_half_spread: float,
        is_home: bool = True
    ) -> Dict:
        """
        Calculate first half spread probability

        College football first halves are often closer than full games
        as underdogs stay competitive early

        Args:
            team_rating: Team power rating
            opponent_rating: Opponent power rating
            first_half_spread: First half point spread
            is_home: Whether team is playing at home

        Returns:
            Dictionary with first half cover probability
        """
        # First half home advantage is slightly less
        home_adj = (CFBAnalytics.AVG_HOME_ADVANTAGE * 0.8) if is_home else -(CFBAnalytics.AVG_HOME_ADVANTAGE * 0.8)

        # Expected point differential (scale to first half)
        full_game_diff = (team_rating - opponent_rating) + home_adj
        first_half_diff = full_game_diff * 0.45  # First halves are closer

        # Adjusted differential accounting for spread
        adjusted_diff = first_half_diff - first_half_spread

        # Lower variance in first half
        std_dev = 12.0

        # Calculate z-score
        z_score = adjusted_diff / std_dev

        # Convert to probability
        cover_prob = CFBAnalytics._normal_cdf(z_score)

        return {
            'cover_probability': cover_prob,
            'expected_margin': first_half_diff,
            'spread': first_half_spread
        }

    @staticmethod
    def analyze_rivalry_game(
        team1_rating: float,
        team2_rating: float,
        spread: float,
        historical_record: Optional[Dict[str, int]] = None
    ) -> Dict:
        """
        Analyze betting factors for rivalry games

        Rivalry games tend to be closer and more unpredictable

        Args:
            team1_rating: Team 1 power rating
            team2_rating: Team 2 power rating
            spread: Point spread
            historical_record: {"team1_wins": X, "team2_wins": Y} (optional)

        Returns:
            Analysis with rivalry adjustments
        """
        # Expected differential without rivalry factor
        normal_diff = team1_rating - team2_rating

        # Rivalry games compress the spread
        # Favorites cover less often in rivalries
        rivalry_compression = 0.75  # Multiply expected diff by this

        adjusted_diff = normal_diff * rivalry_compression

        # Historical momentum factor
        momentum_adj = 0.0
        if historical_record:
            team1_wins = historical_record.get('team1_wins', 0)
            team2_wins = historical_record.get('team2_wins', 0)
            total_games = team1_wins + team2_wins

            if total_games > 0:
                # Slight adjustment based on recent dominance
                win_rate = team1_wins / total_games
                if win_rate > 0.7 or win_rate < 0.3:
                    # One team has dominated recently
                    momentum_adj = (win_rate - 0.5) * 2  # -1 to +1

        return {
            'normal_expected_margin': normal_diff,
            'rivalry_adjusted_margin': adjusted_diff + momentum_adj,
            'spread': spread,
            'compression_factor': rivalry_compression,
            'momentum_adjustment': momentum_adj,
            'advice': "Rivalry games favor underdogs - spreads often too high"
        }

    @staticmethod
    def calculate_conference_championship_probability(
        team_rating: float,
        opponent_rating: float,
        spread: float,
        neutral_site: bool = True
    ) -> Dict:
        """
        Calculate probability for conference championship games

        These are typically at neutral sites with better teams

        Args:
            team_rating: Team power rating
            opponent_rating: Opponent power rating
            spread: Point spread
            neutral_site: Whether game is at neutral site

        Returns:
            Championship game analysis
        """
        # Neutral site = no home advantage
        home_adj = 0.0 if neutral_site else CFBAnalytics.AVG_HOME_ADVANTAGE

        # Expected differential
        expected_diff = (team_rating - opponent_rating) + home_adj
        adjusted_diff = expected_diff - spread

        # Championship games have slightly lower variance
        # Both teams are good, reducing blowout potential
        std_dev = 14.0

        z_score = adjusted_diff / std_dev
        cover_prob = CFBAnalytics._normal_cdf(z_score)

        return {
            'cover_probability': cover_prob,
            'expected_margin': expected_diff,
            'spread': spread,
            'neutral_site': neutral_site,
            'variance': 'lower',
            'advice': "Better teams, lower variance - more predictable"
        }

    @staticmethod
    def simulate_game(
        home_rating: float,
        away_rating: float,
        home_advantage: Optional[float] = None,
        seed: Optional[int] = None
    ) -> Dict:
        """
        Simulate a single college football game

        Args:
            home_rating: Home team rating (average points)
            away_rating: Away team rating (average points)
            home_advantage: Custom home field advantage
            seed: Random seed for reproducibility

        Returns:
            Dictionary with game result
        """
        if seed is not None:
            random.seed(seed)

        # Add home field advantage
        if home_advantage is None:
            home_advantage = CFBAnalytics.AVG_HOME_ADVANTAGE

        home_adj = home_rating + home_advantage
        away_adj = away_rating

        # Simulate scores using normal distribution with CFB variance
        home_score = max(0, int(random.gauss(home_adj, 12) + 0.5))
        away_score = max(0, int(random.gauss(away_adj, 12) + 0.5))

        margin = home_score - away_score
        total = home_score + away_score

        if margin > 0:
            result = 'home_win'
        elif margin < 0:
            result = 'away_win'
        else:
            # Overtime
            # Simplified: 50/50 chance in OT
            if random.random() < 0.5:
                home_score += 7
                result = 'home_win_ot'
            else:
                away_score += 7
                result = 'away_win_ot'

        return {
            'home_score': home_score,
            'away_score': away_score,
            'margin': abs(margin),
            'total': total,
            'result': result,
            'is_key_number': abs(margin) in CFBAnalytics.KEY_NUMBERS,
            'is_blowout': abs(margin) > 28
        }

    @staticmethod
    def simulate_season(
        teams: Dict[str, float],
        games_per_team: int = 12,
        conference_teams: Optional[Dict[str, Conference]] = None,
        seed: Optional[int] = None
    ) -> Dict:
        """
        Simulate a college football season

        Args:
            teams: Dictionary of team names to ratings
            games_per_team: Games per team (CFB regular season = 12)
            conference_teams: Dictionary mapping teams to conferences
            seed: Random seed

        Returns:
            Season results with standings
        """
        if seed is not None:
            random.seed(seed)

        team_names = list(teams.keys())
        standings = {team: {'wins': 0, 'losses': 0, 'pf': 0, 'pa': 0, 'conf_wins': 0, 'conf_losses': 0}
                    for team in team_names}

        matches = []
        total_games = (len(team_names) * games_per_team) // 2

        for _ in range(total_games):
            # Random matchup
            home_team = random.choice(team_names)
            away_team = random.choice([t for t in team_names if t != home_team])

            # Determine if conference game
            is_conf_game = False
            if conference_teams:
                is_conf_game = (home_team in conference_teams and
                              away_team in conference_teams and
                              conference_teams[home_team] == conference_teams[away_team])

            # Simulate game
            game = CFBAnalytics.simulate_game(teams[home_team], teams[away_team])

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
    def analyze_key_numbers(spread: float) -> Dict:
        """
        Analyze the importance of key numbers for a given spread

        Args:
            spread: Point spread to analyze

        Returns:
            Analysis of key number proximity and impact
        """
        spread_val = abs(spread)

        # Find nearest key numbers
        key_nums = sorted(CFBAnalytics.KEY_NUMBERS.keys())
        nearest_below = max([k for k in key_nums if k <= spread_val], default=0)
        nearest_above = min([k for k in key_nums if k >= spread_val], default=max(key_nums))

        is_key = spread_val in CFBAnalytics.KEY_NUMBERS
        frequency = CFBAnalytics.KEY_NUMBERS.get(spread_val, 0.0)

        return {
            'is_key_number': is_key,
            'spread': spread,
            'frequency': frequency,
            'nearest_key_below': nearest_below,
            'nearest_key_above': nearest_above,
            'advice': CFBAnalytics._get_key_number_advice(spread_val)
        }

    @staticmethod
    def calculate_playoff_probability(
        team_rating: float,
        current_record: Tuple[int, int],
        games_remaining: int,
        conference_rank: int,
        strength_of_schedule: float
    ) -> Dict:
        """
        Estimate College Football Playoff probability

        Args:
            team_rating: Team power rating
            current_record: (wins, losses)
            games_remaining: Number of games left
            conference_rank: Rank within conference (1-14 typically)
            strength_of_schedule: SOS rating (0-100, higher = harder)

        Returns:
            Playoff probability analysis
        """
        wins, losses = current_record

        # Base probability from record
        if losses >= 2:
            base_prob = 0.05  # Very unlikely with 2+ losses
        elif losses == 1:
            base_prob = 0.25  # Possible with 1 loss
        else:
            base_prob = 0.70  # Good chance if undefeated

        # Adjust for conference rank
        conf_adj = (5 - conference_rank) * 0.05  # Top teams get boost

        # Adjust for strength of schedule
        sos_adj = (strength_of_schedule - 50) * 0.003

        # Adjust for team rating
        rating_adj = (team_rating - 30) * 0.01

        # Games remaining factor
        # More games = more risk
        games_risk = games_remaining * 0.05

        playoff_prob = max(0.0, min(1.0, base_prob + conf_adj + sos_adj + rating_adj - games_risk))

        return {
            'playoff_probability': playoff_prob,
            'current_record': f"{wins}-{losses}",
            'games_remaining': games_remaining,
            'conference_rank': conference_rank,
            'rating': team_rating,
            'factors': {
                'base': base_prob,
                'conference_rank_adj': conf_adj,
                'sos_adj': sos_adj,
                'rating_adj': rating_adj,
                'games_risk': -games_risk
            }
        }

    @staticmethod
    def _get_key_number_advice(spread: float) -> str:
        """Get betting advice based on key numbers"""
        if spread in [3, 7]:
            return "IMPORTANT KEY NUMBER - Line shopping matters"
        elif spread in [10, 14, 17, 21]:
            return "Key number - Consider 0.5 point moves"
        elif spread in [24, 28]:
            return "Blowout territory - Higher variance"
        elif spread > 35:
            return "Large spread - Backdoor cover risk high"
        else:
            return "Not a key number - Standard spread"

    @staticmethod
    def _normal_cdf(z: float) -> float:
        """
        Cumulative distribution function for standard normal distribution
        Using error function approximation
        """
        return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def calculate_cfb_sp_plus_probability(
    sp_plus_1: float,
    sp_plus_2: float,
    home_advantage: float = 3.5
) -> float:
    """
    Calculate win probability based on SP+ ratings

    SP+ is Bill Connelly's advanced college football rating system

    Args:
        sp_plus_1: Team 1 SP+ rating
        sp_plus_2: Team 2 SP+ rating
        home_advantage: Home field advantage in points

    Returns:
        Probability of team 1 winning
    """
    expected_margin = sp_plus_1 - sp_plus_2 - home_advantage
    std_dev = 17.0

    z_score = expected_margin / std_dev
    return CFBAnalytics._normal_cdf(z_score)


if __name__ == '__main__':
    # Example usage
    print("College Football (CFB) Analytics Library")
    print("=" * 70)

    # Example 1: Spread analysis with conference adjustment
    print("\nExample 1: Spread Analysis (SEC vs FCS)")
    result = CFBAnalytics.calculate_spread_probability(
        team_rating=35.0,  # Strong SEC team
        opponent_rating=15.0,  # FCS opponent
        spread=-42.0,
        is_home=True,
        team_conference=Conference.SEC,
        opponent_conference=Conference.FCS
    )
    print(f"Cover Probability: {result['cover_probability']*100:.1f}%")
    print(f"Expected Margin: {result['expected_margin']:.1f}")
    print(f"Conference Adjustment: {result['conference_adjustment']:.1f}")

    # Example 2: Rivalry game analysis
    print("\nExample 2: Rivalry Game Analysis")
    rivalry = CFBAnalytics.analyze_rivalry_game(
        team1_rating=32.0,
        team2_rating=28.0,
        spread=-7.0,
        historical_record={'team1_wins': 8, 'team2_wins': 12}
    )
    print(f"Normal Expected Margin: {rivalry['normal_expected_margin']:.1f}")
    print(f"Rivalry Adjusted: {rivalry['rivalry_adjusted_margin']:.1f}")
    print(f"Advice: {rivalry['advice']}")

    # Example 3: Total with weather
    print("\nExample 3: Total Analysis with Weather")
    total = CFBAnalytics.calculate_total_probability(
        team1_avg=32.5,
        team2_avg=28.3,
        total_line=58.5,
        weather_impact="heavy_wind"
    )
    print(f"Over Probability: {total['over_probability']*100:.1f}%")
    print(f"Expected Total: {total['expected_total']:.1f}")
    print(f"Weather Impact: {total['weather_impact']}")

    # Example 4: Key numbers
    print("\nExample 4: Key Number Analysis")
    key_analysis = CFBAnalytics.analyze_key_numbers(-14.0)
    print(f"Spread: {key_analysis['spread']}")
    print(f"Is Key Number: {key_analysis['is_key_number']}")
    print(f"Advice: {key_analysis['advice']}")

    # Example 5: Playoff probability
    print("\nExample 5: College Football Playoff Probability")
    playoff = CFBAnalytics.calculate_playoff_probability(
        team_rating=38.0,
        current_record=(10, 0),
        games_remaining=2,
        conference_rank=1,
        strength_of_schedule=75.0
    )
    print(f"Current Record: {playoff['current_record']}")
    print(f"Playoff Probability: {playoff['playoff_probability']*100:.1f}%")
