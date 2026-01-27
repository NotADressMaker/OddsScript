#!/usr/bin/env python3
"""
WNBA Analytics Library

Statistical models and betting tools specifically designed for the WNBA.
Includes rest advantage modeling, compressed schedule analysis, pace adjustments,
and WNBA-specific betting calculations.
"""

import math
import random
from typing import Dict, List, Tuple, Optional
from enum import Enum


class WNBATeam(Enum):
    """WNBA Teams"""
    # Eastern Conference
    NEW_YORK_LIBERTY = "New York Liberty"
    CHICAGO_SKY = "Chicago Sky"
    CONNECTICUT_SUN = "Connecticut Sun"
    INDIANA_FEVER = "Indiana Fever"
    ATLANTA_DREAM = "Atlanta Dream"
    WASHINGTON_MYSTICS = "Washington Mystics"

    # Western Conference
    LAS_VEGAS_ACES = "Las Vegas Aces"
    SEATTLE_STORM = "Seattle Storm"
    LOS_ANGELES_SPARKS = "Los Angeles Sparks"
    PHOENIX_MERCURY = "Phoenix Mercury"
    MINNESOTA_LYNX = "Minnesota Lynx"
    DALLAS_WINGS = "Dallas Wings"


class WNBAAnalytics:
    """WNBA-specific betting analytics and simulations"""

    # Average WNBA statistics
    AVG_POINTS_PER_GAME = 82.5      # Similar to NBA but slightly lower
    AVG_TOTAL_POINTS = 165.0         # Lower scoring than NBA
    AVG_HOME_ADVANTAGE = 2.5         # Similar to NBA
    AVG_PACE = 82.0                  # Possessions per game (slightly slower than NBA)
    AVG_OFFENSIVE_RATING = 105.0     # Points per 100 possessions
    AVG_DEFENSIVE_RATING = 105.0     # Points allowed per 100 possessions

    # Rest advantage is crucial in WNBA due to compressed schedule
    REST_ADVANTAGE_MULTIPLIER = 1.5  # More important than NBA

    @staticmethod
    def calculate_rest_advantage(
        team_rest_days: int,
        opponent_rest_days: int
    ) -> float:
        """
        Calculate rest advantage impact on game outcome

        WNBA schedules are compressed (40 games in ~120 days)
        making rest a significant factor

        Args:
            team_rest_days: Days of rest for the team
            opponent_rest_days: Days of rest for opponent

        Returns:
            Rest advantage in points (positive = team advantage)
        """
        rest_diff = team_rest_days - opponent_rest_days

        # Rest advantage is more pronounced in WNBA
        if abs(rest_diff) >= 3:
            # 3+ day difference = significant advantage
            return rest_diff * 1.5
        elif abs(rest_diff) == 2:
            # 2 day difference = moderate advantage
            return rest_diff * 1.0
        elif abs(rest_diff) == 1:
            # 1 day difference = small advantage
            return rest_diff * 0.5
        else:
            return 0.0

    @staticmethod
    def calculate_back_to_back_penalty(
        is_back_to_back: bool,
        traveled: bool = False
    ) -> float:
        """
        Calculate penalty for back-to-back games

        Args:
            is_back_to_back: Whether team is on back-to-back
            traveled: Whether team traveled between games

        Returns:
            Penalty in points (negative)
        """
        if not is_back_to_back:
            return 0.0

        base_penalty = -3.0  # Larger penalty than NBA

        if traveled:
            # Travel makes it worse
            return base_penalty - 1.5

        return base_penalty

    @staticmethod
    def calculate_game_total(
        team1_off_rating: float,
        team1_def_rating: float,
        team2_off_rating: float,
        team2_def_rating: float,
        pace: float = None
    ) -> Dict:
        """
        Calculate expected game total using Four Factors

        Args:
            team1_off_rating: Team 1 offensive rating (pts per 100 poss)
            team1_def_rating: Team 1 defensive rating
            team2_off_rating: Team 2 offensive rating
            team2_def_rating: Team 2 defensive rating
            pace: Expected pace (possessions per game)

        Returns:
            Dictionary with total prediction and breakdown
        """
        if pace is None:
            pace = WNBAAnalytics.AVG_PACE

        # Predict team scores based on matchup
        team1_expected_off = team1_off_rating * (team2_def_rating / WNBAAnalytics.AVG_DEFENSIVE_RATING)
        team2_expected_off = team2_off_rating * (team1_def_rating / WNBAAnalytics.AVG_DEFENSIVE_RATING)

        # Adjust for pace
        team1_score = (team1_expected_off / 100) * pace
        team2_score = (team2_expected_off / 100) * pace

        total = team1_score + team2_score

        return {
            'total': round(total, 1),
            'team1_score': round(team1_score, 1),
            'team2_score': round(team2_score, 1),
            'pace': pace,
            'typical_over': total > WNBAAnalytics.AVG_TOTAL_POINTS,
            'scoring_environment': 'high' if total > 170 else 'low' if total < 160 else 'average'
        }

    @staticmethod
    def calculate_spread_probability(
        team_rating: float,
        opponent_rating: float,
        spread: float,
        is_home: bool = True,
        team_rest_days: int = 2,
        opponent_rest_days: int = 2
    ) -> float:
        """
        Calculate probability of covering spread with WNBA-specific adjustments

        Args:
            team_rating: Team's net rating (off - def)
            opponent_rating: Opponent's net rating
            spread: Point spread (negative means team is favorite)
            is_home: Whether team is playing at home
            team_rest_days: Days of rest for team
            opponent_rest_days: Days of rest for opponent

        Returns:
            Probability of covering spread (0-1)
        """
        # Base rating differential
        rating_diff = team_rating - opponent_rating

        # Home court advantage
        if is_home:
            rating_diff += WNBAAnalytics.AVG_HOME_ADVANTAGE

        # Rest advantage
        rest_advantage = WNBAAnalytics.calculate_rest_advantage(
            team_rest_days, opponent_rest_days
        )
        rating_diff += rest_advantage

        # Expected margin
        expected_margin = rating_diff

        # Probability calculation using normal distribution
        # Standard deviation for WNBA is about 11 points
        std_dev = 11.0

        # Z-score calculation
        z = (expected_margin + spread) / std_dev

        # Convert to probability using cumulative normal distribution
        probability = 0.5 * (1 + math.erf(z / math.sqrt(2)))

        return max(0.01, min(0.99, probability))

    @staticmethod
    def calculate_moneyline_probability(
        team_off_rating: float,
        team_def_rating: float,
        opp_off_rating: float,
        opp_def_rating: float,
        is_home: bool = True,
        team_rest_days: int = 2,
        opp_rest_days: int = 2
    ) -> float:
        """
        Calculate win probability for moneyline betting

        Args:
            team_off_rating: Team offensive rating
            team_def_rating: Team defensive rating
            opp_off_rating: Opponent offensive rating
            opp_def_rating: Opponent defensive rating
            is_home: Whether team is home
            team_rest_days: Team rest days
            opp_rest_days: Opponent rest days

        Returns:
            Win probability (0-1)
        """
        # Calculate net ratings
        team_net_rating = team_off_rating - team_def_rating
        opp_net_rating = opp_off_rating - opp_def_rating

        # Rating differential
        rating_diff = team_net_rating - opp_net_rating

        # Home court advantage
        if is_home:
            rating_diff += WNBAAnalytics.AVG_HOME_ADVANTAGE

        # Rest advantage (important in WNBA!)
        rest_advantage = WNBAAnalytics.calculate_rest_advantage(
            team_rest_days, opp_rest_days
        )
        rating_diff += rest_advantage

        # Convert rating difference to probability
        # Using Pythagorean expectation adapted for WNBA
        exponent = 14.0  # WNBA-specific exponent

        win_pct = (rating_diff + 100) ** exponent / (
            ((rating_diff + 100) ** exponent) + (100 ** exponent)
        )

        return max(0.05, min(0.95, win_pct))

    @staticmethod
    def calculate_playoff_adjustments(
        regular_season_rating: float,
        playoff_experience: int,
        star_player_present: bool = True
    ) -> float:
        """
        Adjust team ratings for playoff performance

        WNBA playoffs are single-elimination or best-of-3/5,
        making star players and experience more important

        Args:
            regular_season_rating: Team's regular season net rating
            playoff_experience: Number of playoff games in last 3 years
            star_player_present: Whether team has All-WNBA caliber player

        Returns:
            Adjusted playoff rating
        """
        adjusted_rating = regular_season_rating

        # Experience matters in playoffs
        if playoff_experience > 20:
            adjusted_rating += 2.0  # Veteran playoff team
        elif playoff_experience > 10:
            adjusted_rating += 1.0  # Some experience
        else:
            adjusted_rating -= 1.0  # Inexperienced in playoffs

        # Star power is crucial
        if star_player_present:
            adjusted_rating += 2.5  # Stars elevate in playoffs
        else:
            adjusted_rating -= 1.5  # Harder without a star

        return adjusted_rating

    @staticmethod
    def calculate_pace_adjustment(
        team1_pace: float,
        team2_pace: float
    ) -> float:
        """
        Calculate expected game pace

        Args:
            team1_pace: Team 1's average pace
            team2_pace: Team 2's average pace

        Returns:
            Expected game pace
        """
        # Weighted average favoring faster team slightly
        faster_pace = max(team1_pace, team2_pace)
        slower_pace = min(team1_pace, team2_pace)

        # 60% weight to faster, 40% to slower
        expected_pace = (faster_pace * 0.6) + (slower_pace * 0.4)

        return expected_pace

    @staticmethod
    def calculate_travel_fatigue(
        miles_traveled: float,
        time_zones_crossed: int,
        hours_since_arrival: int
    ) -> float:
        """
        Calculate travel fatigue penalty

        Args:
            miles_traveled: Distance traveled in miles
            time_zones_crossed: Number of time zones crossed
            hours_since_arrival: Hours between arrival and game

        Returns:
            Fatigue penalty in points (negative)
        """
        penalty = 0.0

        # Distance penalty
        if miles_traveled > 2000:
            penalty -= 1.5  # Cross-country travel
        elif miles_traveled > 1000:
            penalty -= 0.8  # Long flight
        elif miles_traveled > 500:
            penalty -= 0.3  # Medium flight

        # Time zone penalty
        penalty -= time_zones_crossed * 0.7

        # Recovery time adjustment
        if hours_since_arrival < 24:
            penalty -= 1.0  # Arrived same day
        elif hours_since_arrival < 48:
            penalty -= 0.3  # Arrived day before
        # else: No additional penalty if 48+ hours

        return penalty

    @staticmethod
    def simulate_season(
        team_ratings: Dict[str, float],
        num_simulations: int = 10000
    ) -> Dict:
        """
        Simulate WNBA season to predict playoff teams

        Args:
            team_ratings: Dictionary of team names to net ratings
            num_simulations: Number of seasons to simulate

        Returns:
            Dictionary with playoff probabilities for each team
        """
        playoff_counts = {team: 0 for team in team_ratings.keys()}

        for _ in range(num_simulations):
            # Simulate wins for each team (40 game season)
            team_wins = {}
            for team, rating in team_ratings.items():
                # Convert rating to expected win probability
                base_win_prob = 0.5 + (rating / 50)  # Normalize
                base_win_prob = max(0.1, min(0.9, base_win_prob))

                # Simulate 40 games
                wins = sum(1 for _ in range(40) if random.random() < base_win_prob)
                team_wins[team] = wins

            # Top 8 teams make playoffs
            sorted_teams = sorted(team_wins.items(), key=lambda x: x[1], reverse=True)
            playoff_teams = [team for team, _ in sorted_teams[:8]]

            for team in playoff_teams:
                playoff_counts[team] += 1

        # Calculate probabilities
        playoff_probs = {
            team: (count / num_simulations)
            for team, count in playoff_counts.items()
        }

        return {
            'playoff_probabilities': playoff_probs,
            'simulations_run': num_simulations,
            'top_teams': sorted(playoff_probs.items(), key=lambda x: x[1], reverse=True)[:8]
        }

    @staticmethod
    def calculate_championship_odds(
        team_rating: float,
        playoff_seed: int,
        star_player_rating: float = 8.0
    ) -> float:
        """
        Calculate championship probability

        Args:
            team_rating: Team's net rating
            playoff_seed: Playoff seed (1-8)
            star_player_rating: Star player rating (1-10 scale)

        Returns:
            Championship probability
        """
        # Base probability from rating
        base_prob = 1 / (1 + math.exp(-team_rating / 8))

        # Seed adjustment (home court matters)
        seed_multiplier = {
            1: 1.5,
            2: 1.3,
            3: 1.1,
            4: 1.0,
            5: 0.85,
            6: 0.7,
            7: 0.6,
            8: 0.5
        }.get(playoff_seed, 1.0)

        # Star power adjustment (crucial in WNBA playoffs)
        star_multiplier = 0.8 + (star_player_rating / 10) * 0.4

        championship_prob = base_prob * seed_multiplier * star_multiplier

        return max(0.01, min(0.99, championship_prob))

    @staticmethod
    def analyze_player_prop(
        player_avg: float,
        opponent_def_rating: float,
        line: float,
        is_home: bool = True,
        rest_days: int = 2
    ) -> Dict:
        """
        Analyze player prop bet

        Args:
            player_avg: Player's season average
            opponent_def_rating: Opponent's defensive rating
            line: Prop bet line (over/under)
            is_home: Whether playing at home
            rest_days: Days of rest

        Returns:
            Dictionary with analysis
        """
        # Adjust for opponent defense
        league_avg_def = WNBAAnalytics.AVG_DEFENSIVE_RATING
        def_adjustment = (opponent_def_rating - league_avg_def) / league_avg_def
        adjusted_avg = player_avg * (1 - def_adjustment * 0.3)

        # Home advantage (slight boost)
        if is_home:
            adjusted_avg *= 1.03

        # Rest advantage
        if rest_days >= 3:
            adjusted_avg *= 1.05  # Well-rested
        elif rest_days == 0:
            adjusted_avg *= 0.93  # Back-to-back

        # Calculate probability
        # Standard deviation is about 25% of average
        std_dev = player_avg * 0.25
        z = (adjusted_avg - line) / std_dev
        over_prob = 0.5 * (1 + math.erf(z / math.sqrt(2)))

        return {
            'adjusted_projection': round(adjusted_avg, 1),
            'line': line,
            'over_probability': round(over_prob, 3),
            'under_probability': round(1 - over_prob, 3),
            'recommendation': 'OVER' if over_prob > 0.55 else 'UNDER' if over_prob < 0.45 else 'PASS',
            'edge': round(abs(over_prob - 0.5), 3)
        }


class WNBATeamStats:
    """Helper class for tracking and analyzing WNBA team statistics"""

    def __init__(self):
        self.team_data = {}

    def add_team(
        self,
        team_name: str,
        off_rating: float,
        def_rating: float,
        pace: float,
        home_record: Tuple[int, int],
        away_record: Tuple[int, int]
    ):
        """
        Add team statistics

        Args:
            team_name: Team name
            off_rating: Offensive rating
            def_rating: Defensive rating
            pace: Average pace
            home_record: (wins, losses) at home
            away_record: (wins, losses) away
        """
        self.team_data[team_name] = {
            'off_rating': off_rating,
            'def_rating': def_rating,
            'net_rating': off_rating - def_rating,
            'pace': pace,
            'home_record': home_record,
            'away_record': away_record,
            'home_win_pct': home_record[0] / (home_record[0] + home_record[1]),
            'away_win_pct': away_record[0] / (away_record[0] + away_record[1])
        }

    def get_matchup_prediction(
        self,
        team1: str,
        team2: str,
        team1_home: bool = True,
        team1_rest: int = 2,
        team2_rest: int = 2
    ) -> Dict:
        """
        Get prediction for matchup

        Args:
            team1: Team 1 name
            team2: Team 2 name
            team1_home: Whether team1 is home
            team1_rest: Team 1 rest days
            team2_rest: Team 2 rest days

        Returns:
            Dictionary with prediction
        """
        if team1 not in self.team_data or team2 not in self.team_data:
            raise ValueError("Team not found in database")

        t1 = self.team_data[team1]
        t2 = self.team_data[team2]

        # Calculate win probability
        win_prob = WNBAAnalytics.calculate_moneyline_probability(
            t1['off_rating'], t1['def_rating'],
            t2['off_rating'], t2['def_rating'],
            team1_home, team1_rest, team2_rest
        )

        # Calculate total
        total_data = WNBAAnalytics.calculate_game_total(
            t1['off_rating'], t1['def_rating'],
            t2['off_rating'], t2['def_rating'],
            WNBAAnalytics.calculate_pace_adjustment(t1['pace'], t2['pace'])
        )

        return {
            'team1': team1,
            'team2': team2,
            'team1_win_prob': round(win_prob, 3),
            'team2_win_prob': round(1 - win_prob, 3),
            'predicted_total': total_data['total'],
            'predicted_score': f"{total_data['team1_score']:.1f} - {total_data['team2_score']:.1f}",
            'rest_advantage': WNBAAnalytics.calculate_rest_advantage(team1_rest, team2_rest)
        }


# Quick helper functions for easy integration
def quick_wnba_prediction(
    team_off_rtg: float,
    team_def_rtg: float,
    opp_off_rtg: float,
    opp_def_rtg: float,
    home: bool = True,
    rest_days_team: int = 2,
    rest_days_opp: int = 2
) -> float:
    """
    Quick WNBA game prediction

    Returns win probability for the team
    """
    return WNBAAnalytics.calculate_moneyline_probability(
        team_off_rtg, team_def_rtg,
        opp_off_rtg, opp_def_rtg,
        home, rest_days_team, rest_days_opp
    )


def quick_wnba_total(
    team1_off_rtg: float,
    team1_def_rtg: float,
    team2_off_rtg: float,
    team2_def_rtg: float,
    pace: float = None
) -> float:
    """
    Quick WNBA total prediction

    Returns predicted game total
    """
    result = WNBAAnalytics.calculate_game_total(
        team1_off_rtg, team1_def_rtg,
        team2_off_rtg, team2_def_rtg,
        pace
    )
    return result['total']


if __name__ == "__main__":
    # Example usage
    print("WNBA Analytics Library")
    print("=" * 50)

    # Example 1: Calculate win probability
    print("\nExample 1: Win Probability")
    win_prob = WNBAAnalytics.calculate_moneyline_probability(
        team_off_rating=108.0,
        team_def_rating=102.0,
        opp_off_rating=105.0,
        opp_def_rating=106.0,
        is_home=True,
        team_rest_days=3,
        opp_rest_days=1
    )
    print(f"Win Probability: {win_prob:.1%}")

    # Example 2: Rest advantage
    print("\nExample 2: Rest Advantage")
    rest_adv = WNBAAnalytics.calculate_rest_advantage(3, 1)
    print(f"Rest Advantage: {rest_adv:.1f} points")

    # Example 3: Game total
    print("\nExample 3: Game Total Prediction")
    total = WNBAAnalytics.calculate_game_total(
        108.0, 102.0, 105.0, 106.0
    )
    print(f"Predicted Total: {total['total']}")
    print(f"Team 1: {total['team1_score']:.1f}")
    print(f"Team 2: {total['team2_score']:.1f}")

    # Example 4: Player prop
    print("\nExample 4: Player Prop Analysis")
    prop = WNBAAnalytics.analyze_player_prop(
        player_avg=18.5,
        opponent_def_rating=108.0,
        line=17.5,
        is_home=True,
        rest_days=2
    )
    print(f"Projection: {prop['adjusted_projection']}")
    print(f"Line: {prop['line']}")
    print(f"Over Probability: {prop['over_probability']:.1%}")
    print(f"Recommendation: {prop['recommendation']}")
