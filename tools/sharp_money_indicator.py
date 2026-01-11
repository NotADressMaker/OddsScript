#!/usr/bin/env python3
"""
Sharp Money Indicator

Detect sharp money movement by analyzing betting percentages vs line movement.

Sharp bettors (professionals, syndicates) move lines with large bets even if
they represent a small percentage of total bets. This creates Reverse Line
Movement (RLM) - a powerful indicator.
"""

import argparse
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class SharpIndicator(Enum):
    """Types of sharp money indicators"""
    STRONG_SHARP = "strong_sharp"      # Clear sharp action
    MODERATE_SHARP = "moderate_sharp"  # Likely sharp action
    WEAK_SHARP = "weak_sharp"          # Possible sharp action
    NEUTRAL = "neutral"                # No clear signal
    PUBLIC = "public"                  # Public money driving line


@dataclass
class BettingData:
    """Betting data for one side"""
    side: str  # "team1", "team2", "over", "under", etc.
    bet_percentage: float  # % of total bets
    money_percentage: float  # % of total money
    opening_line: float
    current_line: float


class SharpMoneyAnalyzer:
    """Analyze sharp vs public money"""

    @staticmethod
    def detect_reverse_line_movement(data: BettingData) -> Dict:
        """
        Detect Reverse Line Movement (RLM)

        RLM occurs when the line moves opposite to betting percentage.
        This indicates sharp money on the less popular side.

        Args:
            data: Betting data for one side

        Returns:
            Analysis dictionary
        """
        # Calculate line movement
        line_movement = data.current_line - data.opening_line

        # Determine if this side is getting majority of bets
        majority_bets = data.bet_percentage > 50

        # RLM detection
        has_rlm = False
        rlm_strength = 0

        if majority_bets and line_movement < 0:
            # Getting majority of bets but line moving against
            has_rlm = True
            rlm_strength = abs(line_movement) * (data.bet_percentage - 50) / 50
        elif not majority_bets and line_movement > 0:
            # Getting minority of bets but line moving toward
            has_rlm = True
            rlm_strength = abs(line_movement) * (50 - data.bet_percentage) / 50

        return {
            'has_rlm': has_rlm,
            'rlm_strength': rlm_strength,
            'line_movement': line_movement,
            'bet_percentage': data.bet_percentage,
            'side_getting_bets': data.side if majority_bets else 'other'
        }

    @staticmethod
    def analyze_sharp_indicators(
        data: BettingData,
        threshold_bet_money_diff: float = 10.0
    ) -> Dict:
        """
        Analyze multiple sharp money indicators

        Args:
            data: Betting data
            threshold_bet_money_diff: Minimum difference between bet% and money%

        Returns:
            Comprehensive analysis
        """
        # Indicator 1: Bet% vs Money% discrepancy
        bet_money_diff = data.money_percentage - data.bet_percentage

        # Large bets (sharp) vs small bets (public)
        has_large_bet_signal = abs(bet_money_diff) >= threshold_bet_money_diff

        # Indicator 2: RLM
        rlm_analysis = SharpMoneyAnalyzer.detect_reverse_line_movement(data)

        # Indicator 3: Line movement magnitude
        line_movement = data.current_line - data.opening_line
        significant_line_move = abs(line_movement) >= 0.5

        # Determine sharp side
        sharp_side = None
        confidence = 0

        if has_large_bet_signal:
            if bet_money_diff > 0:
                # Getting more money than bets = sharp action on this side
                sharp_side = data.side
                confidence += abs(bet_money_diff)
            else:
                # Getting more bets than money = public on this side, sharp on other
                sharp_side = 'other'
                confidence += abs(bet_money_diff)

        if rlm_analysis['has_rlm']:
            confidence += rlm_analysis['rlm_strength'] * 10

        # Classify indicator strength
        if confidence >= 20:
            indicator = SharpIndicator.STRONG_SHARP
        elif confidence >= 10:
            indicator = SharpIndicator.MODERATE_SHARP
        elif confidence >= 5:
            indicator = SharpIndicator.WEAK_SHARP
        elif bet_money_diff < -threshold_bet_money_diff:
            indicator = SharpIndicator.PUBLIC
        else:
            indicator = SharpIndicator.NEUTRAL

        return {
            'indicator': indicator,
            'sharp_side': sharp_side,
            'confidence': confidence,
            'bet_money_diff': bet_money_diff,
            'has_rlm': rlm_analysis['has_rlm'],
            'rlm_strength': rlm_analysis['rlm_strength'],
            'line_movement': line_movement,
            'significant_move': significant_line_move,
            'bet_percentage': data.bet_percentage,
            'money_percentage': data.money_percentage
        }

    @staticmethod
    def compare_two_sides(
        side1_data: BettingData,
        side2_data: BettingData
    ) -> Dict:
        """
        Compare both sides of a market to find sharp action

        Args:
            side1_data: Data for side 1
            side2_data: Data for side 2

        Returns:
            Comparative analysis
        """
        analysis1 = SharpMoneyAnalyzer.analyze_sharp_indicators(side1_data)
        analysis2 = SharpMoneyAnalyzer.analyze_sharp_indicators(side2_data)

        # Determine which side has sharp action
        if analysis1['confidence'] > analysis2['confidence']:
            sharp_side = side1_data.side
            sharp_analysis = analysis1
            public_side = side2_data.side
        else:
            sharp_side = side2_data.side
            sharp_analysis = analysis2
            public_side = side1_data.side

        # Calculate steam move score
        steam_score = 0
        if sharp_analysis['has_rlm']:
            steam_score += 30
        if abs(sharp_analysis['bet_money_diff']) > 15:
            steam_score += 25
        if sharp_analysis['significant_move']:
            steam_score += 20
        if abs(sharp_analysis['line_movement']) > 1.0:
            steam_score += 25

        return {
            'sharp_side': sharp_side,
            'public_side': public_side,
            'sharp_indicator': sharp_analysis['indicator'].value,
            'confidence': sharp_analysis['confidence'],
            'steam_score': steam_score,
            'side1_analysis': analysis1,
            'side2_analysis': analysis2,
            'recommendation': SharpMoneyAnalyzer._generate_recommendation(
                sharp_side, sharp_analysis, steam_score
            )
        }

    @staticmethod
    def _generate_recommendation(
        sharp_side: str,
        analysis: Dict,
        steam_score: float
    ) -> str:
        """Generate betting recommendation"""
        if steam_score >= 75:
            return f"🔥 STRONG SHARP PLAY on {sharp_side} - Follow the smart money"
        elif steam_score >= 50:
            return f"⚡ SHARP ACTION detected on {sharp_side} - Consider following"
        elif steam_score >= 30:
            return f"💡 Possible sharp lean toward {sharp_side} - Monitor closely"
        else:
            return "😐 No clear sharp signals - Avoid or wait for more data"


def print_sharp_analysis(result: Dict, side1_name: str, side2_name: str):
    """Print sharp money analysis"""
    print(f"\n{'='*80}")
    print(f"SHARP MONEY INDICATOR ANALYSIS")
    print(f"{'='*80}")

    print(f"\n📊 Market Overview:")
    print(f"  {side1_name} vs {side2_name}")

    analysis1 = result['side1_analysis']
    analysis2 = result['side2_analysis']

    print(f"\n{side1_name}:")
    print(f"  Bet %:   {analysis1['bet_percentage']:.1f}%")
    print(f"  Money %: {analysis1['money_percentage']:.1f}%")
    print(f"  Diff:    {analysis1['bet_money_diff']:+.1f}%")
    print(f"  Line Movement: {analysis1['line_movement']:+.1f}")
    if analysis1['has_rlm']:
        print(f"  ⚠️  RLM Detected (strength: {analysis1['rlm_strength']:.1f})")

    print(f"\n{side2_name}:")
    print(f"  Bet %:   {analysis2['bet_percentage']:.1f}%")
    print(f"  Money %: {analysis2['money_percentage']:.1f}%")
    print(f"  Diff:    {analysis2['bet_money_diff']:+.1f}%")
    print(f"  Line Movement: {analysis2['line_movement']:+.1f}")
    if analysis2['has_rlm']:
        print(f"  ⚠️  RLM Detected (strength: {analysis2['rlm_strength']:.1f})")

    print(f"\n🎯 Sharp Money Detection:")
    print(f"  Sharp Side: {result['sharp_side']}")
    print(f"  Public Side: {result['public_side']}")
    print(f"  Indicator: {result['sharp_indicator'].upper()}")
    print(f"  Confidence: {result['confidence']:.1f}/100")
    print(f"  Steam Score: {result['steam_score']}/100")

    print(f"\n💡 Recommendation:")
    print(f"  {result['recommendation']}")

    print(f"\n{'='*80}")


def print_indicators_explanation():
    """Print explanation of sharp money indicators"""
    print(f"\n{'='*80}")
    print(f"SHARP MONEY INDICATORS EXPLAINED")
    print(f"{'='*80}")

    print("""
1. Reverse Line Movement (RLM)
   - Line moves opposite to betting percentage
   - Example: 70% of bets on Team A, but line moves toward Team B
   - Indicates sharp money on Team B despite fewer bets

2. Bet % vs Money % Discrepancy
   - Large difference suggests different bet sizes
   - Higher money% than bet% = larger average bet size (sharp)
   - Example: 40% of bets but 60% of money = sharp action

3. Line Movement Magnitude
   - Sharp bets cause significant line moves
   - Moves of 1+ point are notable
   - Multiple moves in same direction = steam move

4. Steam Moves
   - Rapid line movement across multiple sportsbooks
   - Often occurs when sharp syndicates place bets
   - Creates RLM with high money percentage

Sharp Betting Traits:
- Large bet sizes relative to public
- Bet earlier (opening lines)
- Cause line movement despite being minority
- Often create RLM patterns

Public Betting Traits:
- Many small bets
- Bet closer to game time
- Follow favorites and overs
- Usually don't move lines much

How to Use:
1. Check betting percentages from Action Network, Vegas Insider, etc.
2. Compare to line movement
3. Look for discrepancies (RLM, bet%/money% gaps)
4. Follow sharp side when indicators align
    """)

    print(f"{'='*80}")


def main():
    parser = argparse.ArgumentParser(
        description='Sharp Money Indicator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze NFL game
  %(prog)s analyze \
    --side1 "Chiefs" 65 55 -7 -6.5 \
    --side2 "Bills" 35 45 +7 +6.5

  # College basketball with RLM
  %(prog)s analyze \
    --side1 "Duke" 72 58 -8.5 -7.5 \
    --side2 "UNC" 28 42 +8.5 +7.5

  # Totals market
  %(prog)s analyze \
    --side1 "Over" 55 48 48.5 47.5 \
    --side2 "Under" 45 52 -48.5 -47.5

  # Show explanation of indicators
  %(prog)s --explain

Format for --sideX: NAME BET% MONEY% OPENING CURRENT
  - BET%: Percentage of total bets on this side
  - MONEY%: Percentage of total money on this side
  - OPENING: Opening line
  - CURRENT: Current line
        """
    )

    parser.add_argument('--explain', action='store_true',
                       help='Show explanation of sharp money indicators')

    subparsers = parser.add_subparsers(dest='command')

    analyze_parser = subparsers.add_parser('analyze', help='Analyze sharp money')
    analyze_parser.add_argument('--side1', nargs=5, required=True,
                               metavar=('NAME', 'BET%', 'MONEY%', 'OPEN', 'CURRENT'),
                               help='Side 1 data')
    analyze_parser.add_argument('--side2', nargs=5, required=True,
                               metavar=('NAME', 'BET%', 'MONEY%', 'OPEN', 'CURRENT'),
                               help='Side 2 data')

    args = parser.parse_args()

    if args.explain:
        print_indicators_explanation()
        return

    if args.command == 'analyze':
        # Parse side 1
        name1, bet_pct1, money_pct1, open1, curr1 = args.side1
        side1 = BettingData(
            side=name1,
            bet_percentage=float(bet_pct1),
            money_percentage=float(money_pct1),
            opening_line=float(open1),
            current_line=float(curr1)
        )

        # Parse side 2
        name2, bet_pct2, money_pct2, open2, curr2 = args.side2
        side2 = BettingData(
            side=name2,
            bet_percentage=float(bet_pct2),
            money_percentage=float(money_pct2),
            opening_line=float(open2),
            current_line=float(curr2)
        )

        # Analyze
        result = SharpMoneyAnalyzer.compare_two_sides(side1, side2)

        # Print
        print_sharp_analysis(result, name1, name2)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
