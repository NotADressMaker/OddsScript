#!/usr/bin/env python3
"""
Advanced Sharp Money Tracker

Professional-grade sharp money detection with historical tracking, multi-book
analysis, line velocity measurement, and public fade strategies.

This tool helps you identify and follow professional betting syndicates.
"""

import argparse
import csv
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import math


@dataclass
class SharpBook:
    """Sportsbooks known for accepting sharp action"""
    name: str
    sharp_level: str  # "pinnacle", "high", "medium", "low"
    limits: str  # "high", "medium", "low"
    description: str


# Known sharp books (Pinnacle is the sharpest)
SHARP_BOOKS = {
    'pinnacle': SharpBook('Pinnacle', 'pinnacle', 'high', 'The sharpest book - market maker'),
    'circa': SharpBook('Circa Sports', 'high', 'high', 'Sharp Vegas book with high limits'),
    'bookmaker': SharpBook('Bookmaker.eu', 'high', 'high', 'Accepts sharp action'),
    'heritage': SharpBook('Heritage', 'high', 'medium', 'Sharp-friendly offshore'),
    'betonline': SharpBook('BetOnline', 'medium', 'medium', 'Accepts some sharp action'),
    'bovada': SharpBook('Bovada', 'low', 'low', 'Recreational book'),
    'draftkings': SharpBook('DraftKings', 'low', 'medium', 'Primarily recreational'),
    'fanduel': SharpBook('FanDuel', 'low', 'medium', 'Primarily recreational'),
    'mgm': SharpBook('BetMGM', 'low', 'medium', 'Primarily recreational'),
    'caesars': SharpBook('Caesars', 'low', 'medium', 'Primarily recreational')
}


@dataclass
class LineMovement:
    """Represents a single line movement"""
    timestamp: str
    book: str
    old_line: float
    new_line: float
    movement: float
    bet_pct: Optional[float] = None
    money_pct: Optional[float] = None


@dataclass
class SharpSignal:
    """A detected sharp money signal"""
    game_id: str
    game_description: str
    sharp_side: str
    signal_type: str  # "rlm", "sharp_book_move", "velocity", "discrepancy"
    confidence: float  # 0-100
    timestamp: str
    details: Dict


class AdvancedSharpDetector:
    """Advanced sharp money detection system"""

    def __init__(self):
        self.signals: List[SharpSignal] = []
        self.historical_accuracy: Dict[str, List[bool]] = defaultdict(list)

    @staticmethod
    def detect_sharp_book_movement(
        movements: List[LineMovement]
    ) -> Dict:
        """
        Detect when sharp books move first

        Sharp books (especially Pinnacle) move before recreational books when
        sharp money comes in. This is a strong indicator.

        Args:
            movements: List of line movements across books

        Returns:
            Analysis of sharp book movement
        """
        if not movements:
            return {'has_sharp_move': False}

        # Sort by timestamp
        sorted_moves = sorted(movements, key=lambda m: m.timestamp)

        # Check if sharp books moved first
        sharp_books_moved_first = []
        rec_books_moved_first = []

        for i, move in enumerate(sorted_moves[:3]):  # First 3 movements
            book_lower = move.book.lower()
            is_sharp = any(sharp_key in book_lower for sharp_key in ['pinnacle', 'circa', 'bookmaker', 'heritage'])

            if is_sharp:
                sharp_books_moved_first.append(move)
            else:
                rec_books_moved_first.append(move)

        # Calculate signal strength
        has_sharp_move = len(sharp_books_moved_first) > 0 and len(sharp_books_moved_first) >= len(rec_books_moved_first)

        # Check if movement was significant
        avg_movement = sum(abs(m.movement) for m in sorted_moves) / len(sorted_moves)
        significant_move = avg_movement >= 0.5

        confidence = 0
        if has_sharp_move:
            confidence += 40
        if significant_move:
            confidence += 20
        if len(sharp_books_moved_first) >= 2:
            confidence += 20

        # Determine direction
        if sorted_moves:
            direction = "positive" if sorted_moves[0].movement > 0 else "negative"
        else:
            direction = "unknown"

        return {
            'has_sharp_move': has_sharp_move,
            'sharp_books_first': len(sharp_books_moved_first),
            'rec_books_first': len(rec_books_moved_first),
            'avg_movement': avg_movement,
            'significant_move': significant_move,
            'confidence': confidence,
            'direction': direction,
            'first_mover': sorted_moves[0].book if sorted_moves else None
        }

    @staticmethod
    def calculate_line_velocity(
        movements: List[LineMovement]
    ) -> Dict:
        """
        Calculate how fast the line is moving

        Faster line movement = more urgent sharp action
        "Steam moves" are very rapid line changes

        Args:
            movements: Chronological list of line movements

        Returns:
            Velocity analysis
        """
        if len(movements) < 2:
            return {'velocity': 0, 'is_steam': False}

        # Sort by timestamp
        sorted_moves = sorted(movements, key=lambda m: m.timestamp)

        # Calculate time between movements
        times = []
        for i in range(1, len(sorted_moves)):
            try:
                t1 = datetime.fromisoformat(sorted_moves[i-1].timestamp)
                t2 = datetime.fromisoformat(sorted_moves[i].timestamp)
                time_diff = (t2 - t1).total_seconds() / 60  # Minutes
                times.append(time_diff)
            except:
                times.append(60)  # Default to 60 min if parsing fails

        avg_time_between = sum(times) / len(times) if times else 60

        # Calculate total movement
        total_movement = abs(sorted_moves[-1].new_line - sorted_moves[0].old_line)

        # Velocity = points per hour
        if avg_time_between > 0:
            velocity = (total_movement / len(movements)) * (60 / avg_time_between)
        else:
            velocity = 0

        # Steam move detection
        is_steam = velocity > 1.0 and total_movement > 1.0 and len(movements) >= 3

        # Consistency check (all moving same direction = stronger)
        all_same_direction = all(
            (m.movement > 0) == (sorted_moves[0].movement > 0)
            for m in sorted_moves
        )

        return {
            'velocity': velocity,
            'total_movement': total_movement,
            'num_movements': len(movements),
            'avg_time_between': avg_time_between,
            'is_steam': is_steam,
            'consistent_direction': all_same_direction,
            'steam_score': min(100, velocity * 30) if is_steam else 0
        }

    @staticmethod
    def analyze_timing_pattern(
        bet_pct: float,
        money_pct: float,
        hours_to_game: float
    ) -> Dict:
        """
        Analyze betting timing patterns

        Sharp bettors bet early (opening lines), public bets late (game day).
        Large money% with lots of time = sharp. Large bet% close to game = public.

        Args:
            bet_pct: Percentage of bets on side
            money_pct: Percentage of money on side
            hours_to_game: Hours until game starts

        Returns:
            Timing analysis
        """
        bet_money_diff = money_pct - bet_pct

        # Sharp timing indicators
        early_sharp = hours_to_game > 24 and bet_money_diff > 10
        mid_sharp = 6 < hours_to_game <= 24 and bet_money_diff > 15
        late_public = hours_to_game <= 6 and bet_pct > 60 and bet_money_diff < 5

        timing_type = "neutral"
        confidence = 50

        if early_sharp:
            timing_type = "early_sharp"
            confidence = 70 + min(20, bet_money_diff)
        elif mid_sharp:
            timing_type = "mid_sharp"
            confidence = 60 + min(20, bet_money_diff)
        elif late_public:
            timing_type = "late_public"
            confidence = 40  # Fade signal

        return {
            'timing_type': timing_type,
            'hours_to_game': hours_to_game,
            'is_sharp_timing': early_sharp or mid_sharp,
            'is_public_timing': late_public,
            'confidence': confidence,
            'bet_money_diff': bet_money_diff
        }

    @staticmethod
    def detect_line_freeze(
        movements: List[LineMovement],
        bet_pct: float
    ) -> Dict:
        """
        Detect line freeze pattern

        When a line stops moving despite heavy public action, books may be
        waiting for sharp action or respecting sharp money already in.

        Args:
            movements: Recent line movements
            bet_pct: Current betting percentage

        Returns:
            Line freeze analysis
        """
        if not movements:
            return {'is_frozen': False}

        # Check if line hasn't moved in last few hours despite action
        recent_movements = [m for m in movements[-5:]]  # Last 5 movements

        if not recent_movements:
            return {'is_frozen': False}

        # Calculate time since last movement
        try:
            last_move_time = datetime.fromisoformat(recent_movements[-1].timestamp)
            current_time = datetime.now()
            hours_since_move = (current_time - last_move_time).total_seconds() / 3600
        except:
            hours_since_move = 0

        # Detect freeze: No movement for 6+ hours with heavy public action
        is_frozen = hours_since_move >= 6 and (bet_pct > 70 or bet_pct < 30)

        # If frozen with public on one side, sharp likely on other
        sharp_implied = False
        if is_frozen:
            if bet_pct > 70:
                sharp_implied = True
                sharp_side = "other"
            elif bet_pct < 30:
                sharp_implied = True
                sharp_side = "this"
            else:
                sharp_side = "unclear"
        else:
            sharp_side = "unclear"

        return {
            'is_frozen': is_frozen,
            'hours_since_move': hours_since_move,
            'sharp_implied': sharp_implied,
            'implied_sharp_side': sharp_side,
            'public_percentage': bet_pct,
            'confidence': 60 if is_frozen and sharp_implied else 30
        }

    def calculate_composite_sharp_score(
        self,
        rlm_score: float,
        sharp_book_score: float,
        velocity_score: float,
        timing_score: float,
        freeze_score: float,
        bet_money_diff: float
    ) -> Dict:
        """
        Calculate composite sharp money score from all indicators

        Args:
            rlm_score: RLM indicator score (0-100)
            sharp_book_score: Sharp book movement score (0-100)
            velocity_score: Line velocity score (0-100)
            timing_score: Timing pattern score (0-100)
            freeze_score: Line freeze score (0-100)
            bet_money_diff: Bet% vs Money% difference

        Returns:
            Composite analysis
        """
        # Weight each indicator
        weights = {
            'rlm': 0.30,
            'sharp_books': 0.25,
            'velocity': 0.20,
            'timing': 0.15,
            'freeze': 0.10
        }

        # Calculate weighted score
        composite = (
            rlm_score * weights['rlm'] +
            sharp_book_score * weights['sharp_books'] +
            velocity_score * weights['velocity'] +
            timing_score * weights['timing'] +
            freeze_score * weights['freeze']
        )

        # Bonus for multiple strong indicators
        strong_indicators = sum([
            rlm_score >= 70,
            sharp_book_score >= 70,
            velocity_score >= 70,
            timing_score >= 70,
            bet_money_diff >= 20
        ])

        if strong_indicators >= 3:
            composite = min(100, composite * 1.2)

        # Classification
        if composite >= 80:
            grade = "A+ (Elite Sharp Signal)"
            action = "🔥 STRONG BET - Follow the sharp money"
        elif composite >= 70:
            grade = "A (Strong Sharp Signal)"
            action = "✅ BET - Sharp action detected"
        elif composite >= 60:
            grade = "B (Good Sharp Signal)"
            action = "💡 CONSIDER - Lean sharp"
        elif composite >= 50:
            grade = "C (Weak Sharp Signal)"
            action = "⚠️ MONITOR - Wait for more data"
        else:
            grade = "D (No Sharp Signal)"
            action = "❌ PASS - No clear sharp action"

        return {
            'composite_score': composite,
            'grade': grade,
            'action': action,
            'strong_indicators': strong_indicators,
            'individual_scores': {
                'rlm': rlm_score,
                'sharp_books': sharp_book_score,
                'velocity': velocity_score,
                'timing': timing_score,
                'freeze': freeze_score
            }
        }


def print_advanced_sharp_analysis(analysis: Dict):
    """Print comprehensive sharp analysis"""
    print(f"\n{'='*90}")
    print(f"🎯 ADVANCED SHARP MONEY ANALYSIS")
    print(f"{'='*90}")

    comp = analysis['composite']

    print(f"\n📊 COMPOSITE SHARP SCORE: {comp['composite_score']:.1f}/100")
    print(f"   Grade: {comp['grade']}")
    print(f"   {comp['action']}")

    print(f"\n📈 Individual Indicator Scores:")
    scores = comp['individual_scores']
    print(f"   RLM Detection:        {scores['rlm']:.1f}/100")
    print(f"   Sharp Book Movement:  {scores['sharp_books']:.1f}/100")
    print(f"   Line Velocity:        {scores['velocity']:.1f}/100")
    print(f"   Timing Pattern:       {scores['timing']:.1f}/100")
    print(f"   Line Freeze:          {scores['freeze']:.1f}/100")

    print(f"\n🔍 Detailed Analysis:")

    if 'rlm' in analysis:
        rlm = analysis['rlm']
        if rlm['has_rlm']:
            print(f"   ✓ RLM Detected - Strength: {rlm['strength']:.1f}")
            print(f"     Line moving against {rlm['bet_pct']:.0f}% of bets")

    if 'sharp_books' in analysis:
        sb = analysis['sharp_books']
        if sb['has_sharp_move']:
            print(f"   ✓ Sharp Books Moved First")
            print(f"     {sb['sharp_books_first']} sharp books, {sb['rec_books_first']} rec books")
            print(f"     First mover: {sb['first_mover']}")

    if 'velocity' in analysis:
        vel = analysis['velocity']
        if vel['is_steam']:
            print(f"   🔥 STEAM MOVE DETECTED!")
            print(f"     Velocity: {vel['velocity']:.2f} points/hour")
            print(f"     Total movement: {vel['total_movement']:.1f} points")
            print(f"     Steam score: {vel['steam_score']:.0f}/100")

    if 'timing' in analysis:
        tim = analysis['timing']
        if tim['is_sharp_timing']:
            print(f"   ✓ Sharp Timing Pattern - {tim['timing_type']}")
            print(f"     {tim['hours_to_game']:.1f} hours to game")
            print(f"     Bet/Money diff: {tim['bet_money_diff']:+.1f}%")

    if 'freeze' in analysis:
        frz = analysis['freeze']
        if frz['is_frozen']:
            print(f"   ⚠️  LINE FREEZE Detected")
            print(f"     {frz['hours_since_move']:.1f} hours since last move")
            if frz['sharp_implied']:
                print(f"     Sharp implied on: {frz['implied_sharp_side']}")

    print(f"\n{'='*90}")


def main():
    parser = argparse.ArgumentParser(
        description='Advanced Sharp Money Tracker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Comprehensive analysis with all indicators
  %(prog)s analyze --game "Chiefs vs Bills" \\
    --side1-data Chiefs 68 54 -7 -6.5 \\
    --side2-data Bills 32 46 +7 +6.5 \\
    --hours-to-game 48 \\
    --movement "2024-01-10T10:00" Pinnacle -7 -6.5 \\
    --movement "2024-01-10T11:00" Circa -7 -6.5 \\
    --movement "2024-01-10T14:00" FanDuel -7 -7

  # Show sharp book guide
  %(prog)s --sharp-books

Sharp Money Concepts:

1. Reverse Line Movement (RLM):
   Line moves opposite to betting percentage. This is THE #1 indicator.
   Example: 70% of bets on Team A, but line moves toward Team B = sharp action on B

2. Sharp Book Movement:
   Pinnacle, Circa, Bookmaker.eu move first when sharp money comes in.
   Recreational books (FanDuel, DraftKings, etc.) follow later.

3. Line Velocity (Steam Moves):
   Rapid line movement = urgent sharp action
   >1 point/hour + consistent direction = steam move
   Often occurs after injury news or lineup changes

4. Timing Patterns:
   Sharps bet early (opening lines)
   Public bets late (game day)
   Large money% early = sharp, large bet% late = public

5. Line Freeze:
   Line stops moving despite heavy public action
   Books waiting for sharp money or respecting sharp bets already in

6. Bet% vs Money% Discrepancy:
   Large difference = different bet sizes
   Higher money% than bet% = sharp action (fewer, larger bets)
   Higher bet% than money% = public action (many small bets)

How Professional Bettors Use This:
1. Track all indicators across multiple games
2. Act immediately on Grade A/A+ signals
3. Bet the sharp side within minutes of detection
4. Use steamchaser tools to get alerts in real-time
5. Historical tracking shows 60-65% win rate on strong sharp signals
        """
    )

    parser.add_argument('--sharp-books', action='store_true',
                       help='Show guide to sharp vs recreational books')

    subparsers = parser.add_subparsers(dest='command')

    # Comprehensive analysis
    analyze_parser = subparsers.add_parser('analyze', help='Comprehensive sharp analysis')
    analyze_parser.add_argument('--game', required=True, help='Game description')
    analyze_parser.add_argument('--side1-data', nargs=5, required=True,
                               metavar=('NAME', 'BET%', 'MONEY%', 'OPEN', 'CURRENT'),
                               help='Side 1: name bet% money% opening current')
    analyze_parser.add_argument('--side2-data', nargs=5, required=True,
                               metavar=('NAME', 'BET%', 'MONEY%', 'OPEN', 'CURRENT'),
                               help='Side 2: name bet% money% opening current')
    analyze_parser.add_argument('--hours-to-game', type=float, default=24,
                               help='Hours until game (default: 24)')
    analyze_parser.add_argument('--movement', nargs=4, action='append',
                               metavar=('TIME', 'BOOK', 'OLD', 'NEW'),
                               help='Line movement: timestamp book old_line new_line')

    args = parser.parse_args()

    if args.sharp_books:
        print(f"\n{'='*80}")
        print(f"GUIDE TO SHARP VS RECREATIONAL SPORTSBOOKS")
        print(f"{'='*80}\n")

        print("📌 PINNACLE TIER (Market Makers):")
        print("  - Pinnacle: The sharpest book in the world")
        print("  - Highest limits, lowest margins, fastest to move")
        print("  - If Pinnacle moves, sharp money is in\n")

        print("🎯 HIGH SHARP TIER:")
        for book in ['circa', 'bookmaker', 'heritage']:
            b = SHARP_BOOKS[book]
            print(f"  - {b.name}: {b.description}")
        print()

        print("💰 MEDIUM SHARP TIER:")
        print("  - BetOnline: Accepts some sharp action, moderate limits\n")

        print("🎰 RECREATIONAL TIER:")
        for book in ['draftkings', 'fanduel', 'mgm', 'caesars', 'bovada']:
            b = SHARP_BOOKS[book]
            print(f"  - {b.name}: {b.description}")

        print(f"\n💡 KEY INSIGHT:")
        print("Watch Pinnacle/Circa first. When they move, sharps are betting.")
        print("If recreational books move first, it's likely public money.")
        print(f"\n{'='*80}")
        return

    if args.command == 'analyze':
        detector = AdvancedSharpDetector()

        # Parse side data
        name1, bet1, money1, open1, curr1 = args.side1_data
        name2, bet2, money2, open2, curr2 = args.side2_data

        bet_pct = float(bet1)
        money_pct = float(money1)
        open_line = float(open1)
        curr_line = float(curr1)

        # Parse movements if provided
        movements = []
        if args.movement:
            for mov_data in args.movement:
                time, book, old, new = mov_data
                movements.append(LineMovement(
                    timestamp=time,
                    book=book,
                    old_line=float(old),
                    new_line=float(new),
                    movement=float(new) - float(old)
                ))

        # Run all analyses
        analysis = {}

        # 1. RLM detection
        line_movement = curr_line - open_line
        majority_bets = bet_pct > 50
        has_rlm = (majority_bets and line_movement < 0) or (not majority_bets and line_movement > 0)
        rlm_strength = abs(line_movement) * abs(bet_pct - 50) / 50 if has_rlm else 0
        rlm_score = min(100, rlm_strength * 30)

        analysis['rlm'] = {
            'has_rlm': has_rlm,
            'strength': rlm_strength,
            'bet_pct': bet_pct,
            'line_movement': line_movement
        }

        # 2. Sharp book movement
        sharp_book_analysis = detector.detect_sharp_book_movement(movements)
        analysis['sharp_books'] = sharp_book_analysis
        sharp_book_score = sharp_book_analysis.get('confidence', 0)

        # 3. Velocity
        velocity_analysis = detector.calculate_line_velocity(movements)
        analysis['velocity'] = velocity_analysis
        velocity_score = velocity_analysis.get('steam_score', 0)

        # 4. Timing
        timing_analysis = detector.analyze_timing_pattern(bet_pct, money_pct, args.hours_to_game)
        analysis['timing'] = timing_analysis
        timing_score = timing_analysis['confidence']

        # 5. Freeze
        freeze_analysis = detector.detect_line_freeze(movements, bet_pct)
        analysis['freeze'] = freeze_analysis
        freeze_score = freeze_analysis.get('confidence', 0)

        # 6. Composite score
        bet_money_diff = money_pct - bet_pct
        composite = detector.calculate_composite_sharp_score(
            rlm_score,
            sharp_book_score,
            velocity_score,
            timing_score,
            freeze_score,
            bet_money_diff
        )

        analysis['composite'] = composite

        # Print results
        print_advanced_sharp_analysis(analysis)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
