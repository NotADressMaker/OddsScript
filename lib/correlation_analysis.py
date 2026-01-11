"""
Correlation Analysis for Parlays

Analyze correlations between bets to avoid correlated parlay legs
and calculate adjusted parlay odds.
"""

import math
from typing import List, Dict, Tuple, Optional
from enum import Enum


class CorrelationType(Enum):
    """Types of correlation between bets"""
    NONE = "none"           # No correlation
    WEAK = "weak"           # Weak correlation (0.1-0.3)
    MODERATE = "moderate"   # Moderate correlation (0.3-0.6)
    STRONG = "strong"       # Strong correlation (0.6-0.9)
    PERFECT = "perfect"     # Perfect correlation (>0.9)
    INVERSE = "inverse"     # Inverse correlation


class BetType(Enum):
    """Common bet types"""
    MONEYLINE = "moneyline"
    SPREAD = "spread"
    TOTAL_OVER = "total_over"
    TOTAL_UNDER = "total_under"
    TEAM_TOTAL_OVER = "team_total_over"
    TEAM_TOTAL_UNDER = "team_total_under"
    FIRST_HALF = "first_half"
    SECOND_HALF = "second_half"
    PROP = "prop"


class CorrelationAnalyzer:
    """Analyze correlations between parlay legs"""

    # Known correlation coefficients for common bet combinations
    # These are empirical estimates based on historical data
    CORRELATION_MATRIX = {
        # Same game correlations
        ("moneyline", "spread", "same_game"): 0.85,          # Strong positive
        ("moneyline", "total_over", "same_game"): 0.15,      # Weak positive (favorite + over)
        ("moneyline", "total_under", "same_game"): -0.05,    # Negligible
        ("spread", "total_over", "same_game"): 0.25,         # Weak positive
        ("spread", "total_under", "same_game"): 0.05,        # Negligible
        ("total_over", "team_total_over", "same_game"): 0.70, # Strong positive
        ("total_under", "team_total_under", "same_game"): 0.70, # Strong positive
        ("first_half", "moneyline", "same_game"): 0.65,      # Strong positive
        ("first_half", "second_half", "same_game"): 0.10,    # Weak positive

        # Same game team totals
        ("team_total_over", "team_total_over", "same_game_both_teams"): -0.20,  # Weak negative
        ("moneyline", "team_total_over", "same_game_same_team"): 0.40,  # Moderate positive

        # Different games
        ("moneyline", "moneyline", "different_games"): 0.0,  # No correlation
        ("spread", "spread", "different_games"): 0.0,        # No correlation

        # Same day correlations (weather, etc.)
        ("total_under", "total_under", "same_day_same_sport"): 0.05,  # Negligible
    }

    @staticmethod
    def get_correlation(
        bet1_type: str,
        bet2_type: str,
        same_game: bool = False,
        same_team: bool = False,
        same_day: bool = False
    ) -> float:
        """
        Get correlation coefficient between two bet types

        Args:
            bet1_type: First bet type
            bet2_type: Second bet type
            same_game: Whether bets are on the same game
            same_team: Whether bets are on the same team
            same_day: Whether bets are on the same day

        Returns:
            Correlation coefficient (-1 to 1)
        """
        # Determine context
        if same_game and same_team:
            context = "same_game_same_team"
        elif same_game:
            # Check if both are team totals on different teams
            if "team_total" in bet1_type and "team_total" in bet2_type:
                context = "same_game_both_teams"
            else:
                context = "same_game"
        elif same_day:
            context = "same_day_same_sport"
        else:
            context = "different_games"

        # Look up correlation
        key = (bet1_type, bet2_type, context)

        if key in CorrelationAnalyzer.CORRELATION_MATRIX:
            return CorrelationAnalyzer.CORRELATION_MATRIX[key]

        # Try reverse order
        key_reverse = (bet2_type, bet1_type, context)
        if key_reverse in CorrelationAnalyzer.CORRELATION_MATRIX:
            return CorrelationAnalyzer.CORRELATION_MATRIX[key_reverse]

        # Default: assume no correlation for different games, 0.2 for same game
        if same_game:
            return 0.2  # Conservative estimate
        return 0.0

    @staticmethod
    def classify_correlation(coefficient: float) -> CorrelationType:
        """Classify correlation strength"""
        abs_coef = abs(coefficient)

        if abs_coef > 0.9:
            return CorrelationType.PERFECT
        elif abs_coef > 0.6:
            return CorrelationType.STRONG
        elif abs_coef > 0.3:
            return CorrelationType.MODERATE
        elif abs_coef > 0.1:
            return CorrelationType.WEAK
        elif coefficient < -0.1:
            return CorrelationType.INVERSE
        else:
            return CorrelationType.NONE

    @staticmethod
    def adjust_parlay_odds(
        individual_odds: List[float],
        correlations: List[float]
    ) -> float:
        """
        Adjust parlay odds based on correlations

        Standard parlay assumes independence. With correlation, actual odds are worse.

        Args:
            individual_odds: List of American odds for each leg
            correlations: List of correlation coefficients between legs

        Returns:
            Adjusted parlay odds (American)
        """
        # Convert to decimal odds
        decimal_odds = []
        for odds in individual_odds:
            if odds > 0:
                decimal_odds.append((odds / 100) + 1)
            else:
                decimal_odds.append((100 / abs(odds)) + 1)

        # Calculate implied probabilities
        implied_probs = [1 / dec_odds for dec_odds in decimal_odds]

        # Adjust for correlation
        # With positive correlation, the joint probability is higher than independent
        # This means worse odds for the bettor

        if len(implied_probs) < 2:
            # Single bet, no adjustment needed
            combined_prob = implied_probs[0]
        else:
            # For simplicity, use average correlation
            avg_correlation = sum(correlations) / len(correlations) if correlations else 0

            # Adjusted joint probability (simplified formula)
            # P(A and B) = P(A) * P(B) for independent events
            # With correlation, we adjust: P(A and B) ≈ P(A) * P(B) / (1 - ρ * min(P(A), P(B)))
            # For multiple legs, we apply iteratively

            combined_prob = implied_probs[0]
            for i in range(1, len(implied_probs)):
                correlation = correlations[i-1] if i-1 < len(correlations) else 0

                # Adjustment factor
                if correlation > 0:
                    # Positive correlation makes parlay less likely to hit
                    adjustment = 1 + (correlation * 0.5)  # Conservative adjustment
                    combined_prob = combined_prob * implied_probs[i] * adjustment
                elif correlation < 0:
                    # Negative correlation makes parlay more likely (rare)
                    adjustment = 1 + (abs(correlation) * 0.3)
                    combined_prob = combined_prob * implied_probs[i] / adjustment
                else:
                    # No correlation
                    combined_prob = combined_prob * implied_probs[i]

        # Convert back to odds
        if combined_prob >= 1:
            return -10000  # Essentially impossible

        adjusted_decimal = 1 / combined_prob

        # Convert to American odds
        if adjusted_decimal >= 2.0:
            return (adjusted_decimal - 1) * 100
        else:
            return -100 / (adjusted_decimal - 1)

    @staticmethod
    def analyze_parlay(legs: List[Dict]) -> Dict:
        """
        Analyze a parlay for correlations

        Args:
            legs: List of bet legs, each with:
                - 'type': Bet type
                - 'odds': American odds
                - 'game_id': Game identifier
                - 'team': Team identifier (optional)
                - 'description': Human-readable description

        Returns:
            Analysis with warnings and adjusted odds
        """
        if len(legs) < 2:
            return {
                'num_legs': len(legs),
                'warnings': [],
                'correlations': [],
                'standard_odds': legs[0]['odds'] if legs else 0,
                'adjusted_odds': legs[0]['odds'] if legs else 0,
                'edge_reduction': 0,
                'recommendation': 'Single bet, no correlation issues'
            }

        warnings = []
        correlations = []

        # Analyze each pair of legs
        for i in range(len(legs)):
            for j in range(i + 1, len(legs)):
                leg1 = legs[i]
                leg2 = legs[j]

                same_game = leg1.get('game_id') == leg2.get('game_id')
                same_team = leg1.get('team') == leg2.get('team') if 'team' in leg1 and 'team' in leg2 else False

                correlation = CorrelationAnalyzer.get_correlation(
                    leg1['type'],
                    leg2['type'],
                    same_game=same_game,
                    same_team=same_team
                )

                corr_type = CorrelationAnalyzer.classify_correlation(correlation)

                correlations.append({
                    'leg1': leg1['description'],
                    'leg2': leg2['description'],
                    'coefficient': correlation,
                    'type': corr_type.value
                })

                # Generate warnings
                if corr_type == CorrelationType.PERFECT:
                    warnings.append(
                        f"⛔ PERFECT CORRELATION: {leg1['description']} and {leg2['description']} "
                        f"(ρ={correlation:.2f}) - DO NOT PARLAY"
                    )
                elif corr_type == CorrelationType.STRONG:
                    warnings.append(
                        f"⚠️  STRONG CORRELATION: {leg1['description']} and {leg2['description']} "
                        f"(ρ={correlation:.2f}) - Not recommended for parlays"
                    )
                elif corr_type == CorrelationType.MODERATE:
                    warnings.append(
                        f"⚡ MODERATE CORRELATION: {leg1['description']} and {leg2['description']} "
                        f"(ρ={correlation:.2f}) - Reduces expected value"
                    )

        # Calculate standard parlay odds (assuming independence)
        standard_decimal = 1.0
        for leg in legs:
            odds = leg['odds']
            if odds > 0:
                standard_decimal *= ((odds / 100) + 1)
            else:
                standard_decimal *= ((100 / abs(odds)) + 1)

        if standard_decimal >= 2.0:
            standard_odds = (standard_decimal - 1) * 100
        else:
            standard_odds = -100 / (standard_decimal - 1)

        # Calculate adjusted odds
        individual_odds = [leg['odds'] for leg in legs]
        correlation_coeffs = [c['coefficient'] for c in correlations]
        adjusted_odds = CorrelationAnalyzer.adjust_parlay_odds(individual_odds, correlation_coeffs)

        # Calculate edge reduction
        # Convert to implied probabilities
        if standard_odds > 0:
            standard_prob = 100 / (standard_odds + 100)
        else:
            standard_prob = abs(standard_odds) / (abs(standard_odds) + 100)

        if adjusted_odds > 0:
            adjusted_prob = 100 / (adjusted_odds + 100)
        else:
            adjusted_prob = abs(adjusted_odds) / (abs(adjusted_odds) + 100)

        edge_reduction = ((adjusted_prob - standard_prob) / standard_prob) * 100

        # Generate recommendation
        if not warnings:
            recommendation = "✓ No significant correlations detected"
        elif any("PERFECT" in w for w in warnings):
            recommendation = "❌ DO NOT PLACE - Contains perfectly correlated legs"
        elif any("STRONG" in w for w in warnings):
            recommendation = "❌ NOT RECOMMENDED - Strong correlations present"
        elif any("MODERATE" in w for w in warnings):
            recommendation = "⚠️  CAUTION - Moderate correlations reduce value"
        else:
            recommendation = "~ ACCEPTABLE - Weak correlations present"

        return {
            'num_legs': len(legs),
            'warnings': warnings,
            'correlations': correlations,
            'standard_odds': standard_odds,
            'adjusted_odds': adjusted_odds,
            'edge_reduction': edge_reduction,
            'recommendation': recommendation
        }


def print_parlay_analysis(analysis: Dict):
    """Print formatted parlay analysis"""
    print(f"\n{'='*70}")
    print(f"Parlay Correlation Analysis ({analysis['num_legs']} legs)")
    print(f"{'='*70}")

    print(f"\nOdds Comparison:")
    print(f"  Standard Parlay Odds:  {analysis['standard_odds']:+.0f}")
    print(f"  Adjusted Odds:         {analysis['adjusted_odds']:+.0f}")
    print(f"  Edge Reduction:        {analysis['edge_reduction']:+.2f}%")

    if analysis['correlations']:
        print(f"\nCorrelation Matrix:")
        print(f"  {'Leg 1':<30} {'Leg 2':<30} {'ρ':<8} {'Type':<12}")
        print(f"  {'-'*80}")
        for corr in analysis['correlations']:
            print(f"  {corr['leg1'][:28]:<30} {corr['leg2'][:28]:<30} "
                  f"{corr['coefficient']:>6.2f}  {corr['type']:<12}")

    if analysis['warnings']:
        print(f"\n⚠️  Warnings:")
        for warning in analysis['warnings']:
            print(f"  {warning}")

    print(f"\nRecommendation:")
    print(f"  {analysis['recommendation']}")

    print(f"\n{'='*70}")


def common_correlation_examples():
    """Print common correlation scenarios"""
    print(f"\n{'='*70}")
    print("Common Parlay Correlations to Avoid")
    print(f"{'='*70}")

    examples = [
        {
            'scenario': 'Same Game: Moneyline + Spread',
            'correlation': 0.85,
            'explanation': 'If team wins, they usually cover spread (strong correlation)',
            'recommendation': '❌ AVOID'
        },
        {
            'scenario': 'Same Game: Team Total Over + Game Total Over',
            'correlation': 0.70,
            'explanation': 'One team scoring more directly contributes to game total',
            'recommendation': '❌ AVOID'
        },
        {
            'scenario': 'Same Game: Moneyline + First Half ML',
            'correlation': 0.65,
            'explanation': 'Winning first half increases chance of winning game',
            'recommendation': '❌ AVOID'
        },
        {
            'scenario': 'Same Game: Favorite ML + Over',
            'correlation': 0.15,
            'explanation': 'Weak correlation - favorites in shootouts',
            'recommendation': '⚠️  CAUTION'
        },
        {
            'scenario': 'Different Games: Any combination',
            'correlation': 0.0,
            'explanation': 'No correlation between different games',
            'recommendation': '✓ ACCEPTABLE'
        },
        {
            'scenario': 'Same Game: Both Team Totals Over',
            'correlation': -0.20,
            'explanation': 'One team scoring might mean other scores less (pace)',
            'recommendation': '✓ ACCEPTABLE (inverse correlation)'
        },
    ]

    for example in examples:
        print(f"\n{example['scenario']}")
        print(f"  Correlation: {example['correlation']:+.2f}")
        print(f"  Explanation: {example['explanation']}")
        print(f"  {example['recommendation']}")

    print(f"\n{'='*70}")
    print("Key Takeaway: Only parlay bets from DIFFERENT games to avoid correlation")
    print(f"{'='*70}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Parlay Correlation Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show common correlation scenarios
  %(prog)s --examples

  # Analyze a same-game parlay (BAD)
  %(prog)s \\
    --leg "moneyline:-150:game1::Chiefs ML" \\
    --leg "spread:-110:game1::Chiefs -7" \\
    --leg "total_over:-110:game1::Over 48.5"

  # Analyze a multi-game parlay (GOOD)
  %(prog)s \\
    --leg "moneyline:-150:game1::Chiefs ML" \\
    --leg "moneyline:+120:game2::Lions ML" \\
    --leg "spread:-110:game3::Eagles -3"
        """
    )

    parser.add_argument('--leg', action='append', nargs=5,
                       metavar=('TYPE', 'ODDS', 'GAME_ID', 'TEAM', 'DESC'),
                       help='Add parlay leg: type odds game_id team description')
    parser.add_argument('--examples', action='store_true',
                       help='Show common correlation examples')

    args = parser.parse_args()

    if args.examples:
        common_correlation_examples()
    elif args.leg:
        legs = []
        for leg_data in args.leg:
            bet_type, odds, game_id, team, desc = leg_data
            legs.append({
                'type': bet_type,
                'odds': float(odds),
                'game_id': game_id,
                'team': team if team else None,
                'description': desc
            })

        analysis = CorrelationAnalyzer.analyze_parlay(legs)
        print_parlay_analysis(analysis)
    else:
        parser.print_help()
