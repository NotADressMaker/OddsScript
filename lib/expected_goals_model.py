#!/usr/bin/env python3
"""
Expected Goals (xG) Model

Advanced soccer analytics using expected goals to predict match outcomes.
xG measures the quality of scoring chances based on shot characteristics.
"""

import math
import argparse
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Shot:
    """Represents a single shot"""
    distance: float  # meters from goal
    angle: float  # degrees, 0 = dead center
    shot_type: str  # "open_play", "set_piece", "penalty", "header", "counter"
    body_part: str  # "foot", "header"
    assist_type: str  # "through_ball", "cross", "cutback", "individual", "none"


class ExpectedGoalsModel:
    """Calculate xG for shots and matches"""

    # Base conversion rates by shot type
    BASE_CONVERSION = {
        'penalty': 0.76,
        'open_play': 0.10,
        'set_piece': 0.08,
        'counter': 0.15,
        'header': 0.06
    }

    @staticmethod
    def calculate_shot_xg(shot: Shot) -> float:
        """
        Calculate xG for a single shot

        Simplified model based on:
        - Distance from goal
        - Angle to goal
        - Shot type
        - Body part used
        - Assist type

        Args:
            shot: Shot object

        Returns:
            xG value (0-1, probability of goal)
        """
        # Start with base conversion for shot type
        base_xg = ExpectedGoalsModel.BASE_CONVERSION.get(
            shot.shot_type,
            ExpectedGoalsModel.BASE_CONVERSION['open_play']
        )

        # Distance multiplier (closer = higher xG)
        # Using exponential decay: xG decreases as distance increases
        # Optimal distance: ~11 meters (penalty spot)
        distance_factor = math.exp(-0.1 * (shot.distance - 11) ** 2 / 100)

        # Angle multiplier (central = higher xG)
        # Normalize angle to 0-1, where 0 degrees (center) = 1.0
        angle_factor = 1 - (abs(shot.angle) / 90)  # 0-90 degrees max

        # Body part multiplier
        body_part_mult = {
            'foot': 1.0,
            'header': 0.7  # Headers generally less accurate
        }.get(shot.body_part, 0.8)

        # Assist type multiplier
        assist_mult = {
            'through_ball': 1.3,  # High quality chance
            'cutback': 1.2,       # Good angle
            'cross': 0.9,         # Often headers, harder
            'individual': 1.0,    # Normal
            'none': 0.8           # Long shot or rebound
        }.get(shot.assist_type, 1.0)

        # Combine factors
        xg = base_xg * distance_factor * angle_factor * body_part_mult * assist_mult

        # Cap at reasonable maximum (not counting penalties)
        if shot.shot_type != 'penalty':
            xg = min(xg, 0.5)  # Even best chances ~50% max

        return xg

    @staticmethod
    def calculate_team_xg(shots: List[Shot]) -> float:
        """
        Calculate total xG for a team from list of shots

        Args:
            shots: List of Shot objects

        Returns:
            Total xG
        """
        return sum(ExpectedGoalsModel.calculate_shot_xg(shot) for shot in shots)

    @staticmethod
    def predict_match_outcome(
        home_xg: float,
        away_xg: float,
        home_advantage: float = 0.15
    ) -> Dict:
        """
        Predict match outcome using Poisson distribution with xG

        Args:
            home_xg: Home team expected goals
            away_xg: Away team expected goals
            home_advantage: Home advantage multiplier (default 0.15 = 15%)

        Returns:
            Dictionary with outcome probabilities
        """
        # Adjust for home advantage
        adj_home_xg = home_xg * (1 + home_advantage)
        adj_away_xg = away_xg

        # Use Poisson distribution to calculate probabilities
        max_goals = 8  # Calculate up to 8 goals per team

        # Calculate probability matrix
        prob_matrix = [[0 for _ in range(max_goals + 1)] for _ in range(max_goals + 1)]

        for home_goals in range(max_goals + 1):
            for away_goals in range(max_goals + 1):
                # Poisson probability
                prob_home = (adj_home_xg ** home_goals * math.exp(-adj_home_xg)) / math.factorial(home_goals)
                prob_away = (adj_away_xg ** away_goals * math.exp(-adj_away_xg)) / math.factorial(away_goals)

                prob_matrix[home_goals][away_goals] = prob_home * prob_away

        # Calculate outcome probabilities
        home_win = sum(prob_matrix[h][a] for h in range(max_goals + 1) for a in range(max_goals + 1) if h > a)
        draw = sum(prob_matrix[h][a] for h in range(max_goals + 1) for a in range(max_goals + 1) if h == a)
        away_win = sum(prob_matrix[h][a] for h in range(max_goals + 1) for a in range(max_goals + 1) if h < a)

        # Over/under probabilities
        over_25 = sum(prob_matrix[h][a] for h in range(max_goals + 1) for a in range(max_goals + 1) if h + a > 2.5)
        under_25 = 1 - over_25

        over_35 = sum(prob_matrix[h][a] for h in range(max_goals + 1) for a in range(max_goals + 1) if h + a > 3.5)
        under_35 = 1 - over_35

        # Both teams to score
        btts_yes = sum(prob_matrix[h][a] for h in range(1, max_goals + 1) for a in range(1, max_goals + 1))
        btts_no = 1 - btts_yes

        # Most likely correct scores
        correct_scores = []
        for h in range(max_goals + 1):
            for a in range(max_goals + 1):
                correct_scores.append({
                    'score': f"{h}-{a}",
                    'probability': prob_matrix[h][a]
                })

        correct_scores.sort(key=lambda x: x['probability'], reverse=True)

        return {
            'home_xg': adj_home_xg,
            'away_xg': adj_away_xg,
            'home_win': home_win,
            'draw': draw,
            'away_win': away_win,
            'over_25': over_25,
            'under_25': under_25,
            'over_35': over_35,
            'under_35': under_35,
            'btts_yes': btts_yes,
            'btts_no': btts_no,
            'top_scores': correct_scores[:5]
        }

    @staticmethod
    def probability_to_odds(prob: float) -> float:
        """Convert probability to American odds"""
        if prob >= 0.5:
            return -100 * prob / (1 - prob)
        else:
            return 100 * (1 - prob) / prob


def print_xg_analysis(result: Dict, home_team: str, away_team: str):
    """Print xG match analysis"""
    print(f"\n{'='*80}")
    print(f"EXPECTED GOALS (xG) MATCH PREDICTION")
    print(f"{'='*80}")

    print(f"\n⚽ Match: {home_team} vs {away_team}")

    print(f"\nExpected Goals:")
    print(f"  {home_team}: {result['home_xg']:.2f} xG")
    print(f"  {away_team}: {result['away_xg']:.2f} xG")

    print(f"\n📊 Match Outcome Probabilities:")
    print(f"  {home_team} Win:  {result['home_win']*100:>6.2f}%  (Odds: {ExpectedGoalsModel.probability_to_odds(result['home_win']):>+7.0f})")
    print(f"  Draw:            {result['draw']*100:>6.2f}%  (Odds: {ExpectedGoalsModel.probability_to_odds(result['draw']):>+7.0f})")
    print(f"  {away_team} Win:  {result['away_win']*100:>6.2f}%  (Odds: {ExpectedGoalsModel.probability_to_odds(result['away_win']):>+7.0f})")

    print(f"\n🎯 Totals Probabilities:")
    print(f"  Over 2.5:   {result['over_25']*100:>6.2f}%  (Odds: {ExpectedGoalsModel.probability_to_odds(result['over_25']):>+7.0f})")
    print(f"  Under 2.5:  {result['under_25']*100:>6.2f}%  (Odds: {ExpectedGoalsModel.probability_to_odds(result['under_25']):>+7.0f})")
    print(f"  Over 3.5:   {result['over_35']*100:>6.2f}%  (Odds: {ExpectedGoalsModel.probability_to_odds(result['over_35']):>+7.0f})")
    print(f"  Under 3.5:  {result['under_35']*100:>6.2f}%  (Odds: {ExpectedGoalsModel.probability_to_odds(result['under_35']):>+7.0f})")

    print(f"\n🥅 Both Teams to Score:")
    print(f"  Yes: {result['btts_yes']*100:>6.2f}%  (Odds: {ExpectedGoalsModel.probability_to_odds(result['btts_yes']):>+7.0f})")
    print(f"  No:  {result['btts_no']*100:>6.2f}%  (Odds: {ExpectedGoalsModel.probability_to_odds(result['btts_no']):>+7.0f})")

    print(f"\n📋 Most Likely Correct Scores:")
    for i, score in enumerate(result['top_scores'], 1):
        print(f"  {i}. {score['score']:<6} {score['probability']*100:>6.2f}%")

    print(f"\n{'='*80}")


def main():
    parser = argparse.ArgumentParser(
        description='Expected Goals (xG) Model',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Predict match from xG values
  %(prog)s predict --home-xg 1.8 --away-xg 1.2

  # With custom home advantage
  %(prog)s predict --home-xg 2.1 --away-xg 0.9 --home-adv 0.20

  # Calculate xG for a specific shot
  %(prog)s shot --distance 12 --angle 10 --type open_play \
    --body foot --assist through_ball

  # Multiple shots for a team
  %(prog)s team-xg \
    --shot 11 5 penalty foot none \
    --shot 18 20 open_play foot through_ball \
    --shot 25 30 open_play header cross

What is xG?
  Expected Goals (xG) measures the quality of scoring chances. Each shot is
  assigned an xG value between 0-1 representing the probability it results in
  a goal, based on historical data of similar shots.

  A shot from the penalty spot might have 0.76 xG (76% chance of scoring)
  while a 30-yard shot might have 0.03 xG (3% chance).

How to Use for Betting:
  1. Track team xG over multiple matches
  2. Compare to actual goals scored (over/underperformance)
  3. Use xG to predict future matches
  4. Find value when bookmaker odds differ from xG probabilities
        """
    )

    subparsers = parser.add_subparsers(dest='command')

    # Predict match
    predict_parser = subparsers.add_parser('predict', help='Predict match from xG')
    predict_parser.add_argument('--home-xg', type=float, required=True,
                               help='Home team expected goals')
    predict_parser.add_argument('--away-xg', type=float, required=True,
                               help='Away team expected goals')
    predict_parser.add_argument('--home-adv', type=float, default=0.15,
                               help='Home advantage (default: 0.15)')
    predict_parser.add_argument('--home-team', type=str, default='Home',
                               help='Home team name')
    predict_parser.add_argument('--away-team', type=str, default='Away',
                               help='Away team name')

    # Calculate single shot xG
    shot_parser = subparsers.add_parser('shot', help='Calculate xG for a shot')
    shot_parser.add_argument('--distance', type=float, required=True,
                            help='Distance from goal (meters)')
    shot_parser.add_argument('--angle', type=float, required=True,
                            help='Angle from center (degrees, 0=center)')
    shot_parser.add_argument('--type', choices=['open_play', 'set_piece', 'penalty', 'counter', 'header'],
                            required=True, help='Shot type')
    shot_parser.add_argument('--body', choices=['foot', 'header'], required=True,
                            help='Body part used')
    shot_parser.add_argument('--assist', choices=['through_ball', 'cross', 'cutback', 'individual', 'none'],
                            required=True, help='Assist type')

    # Calculate team xG from multiple shots
    team_parser = subparsers.add_parser('team-xg', help='Calculate team xG from shots')
    team_parser.add_argument('--shot', nargs=5, action='append',
                            metavar=('DIST', 'ANGLE', 'TYPE', 'BODY', 'ASSIST'),
                            help='Add shot: distance angle type body assist')

    args = parser.parse_args()

    if args.command == 'predict':
        result = ExpectedGoalsModel.predict_match_outcome(
            args.home_xg,
            args.away_xg,
            args.home_adv
        )

        print_xg_analysis(result, args.home_team, args.away_team)

    elif args.command == 'shot':
        shot = Shot(
            distance=args.distance,
            angle=args.angle,
            shot_type=args.type,
            body_part=args.body,
            assist_type=args.assist
        )

        xg = ExpectedGoalsModel.calculate_shot_xg(shot)

        print(f"\n{'='*60}")
        print(f"SHOT xG CALCULATION")
        print(f"{'='*60}")
        print(f"\nShot Details:")
        print(f"  Distance: {shot.distance}m from goal")
        print(f"  Angle: {shot.angle}° from center")
        print(f"  Type: {shot.shot_type}")
        print(f"  Body Part: {shot.body_part}")
        print(f"  Assist: {shot.assist_type}")
        print(f"\nExpected Goals (xG): {xg:.3f}")
        print(f"Conversion Probability: {xg*100:.1f}%")
        print(f"\n{'='*60}")

    elif args.command == 'team-xg':
        if not args.shot:
            print("Error: Provide at least one --shot")
            return

        shots = []
        for shot_data in args.shot:
            dist, angle, shot_type, body, assist = shot_data
            shots.append(Shot(
                distance=float(dist),
                angle=float(angle),
                shot_type=shot_type,
                body_part=body,
                assist_type=assist
            ))

        total_xg = ExpectedGoalsModel.calculate_team_xg(shots)

        print(f"\n{'='*60}")
        print(f"TEAM xG CALCULATION")
        print(f"{'='*60}")
        print(f"\n{len(shots)} shots analyzed:")
        for i, shot in enumerate(shots, 1):
            xg = ExpectedGoalsModel.calculate_shot_xg(shot)
            print(f"  Shot {i}: {shot.shot_type:12s} {shot.distance:4.1f}m  xG: {xg:.3f}")

        print(f"\nTotal Team xG: {total_xg:.2f}")
        print(f"{'='*60}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
