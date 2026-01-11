#!/usr/bin/env python3
"""
Line Movement Tracker and Steam Detector

Track line movements and detect sharp/steam moves in betting markets.
"""

import csv
import json
from datetime import datetime
from typing import List, Dict, Optional


class LineMovement:
    """Represents a single line movement"""

    def __init__(
        self,
        timestamp: datetime,
        odds: float,
        book: str = "unknown"
    ):
        self.timestamp = timestamp
        self.odds = odds
        self.book = book


class LineTracker:
    """Track and analyze line movements"""

    def __init__(self, game_id: str, initial_line: float):
        """
        Initialize line tracker

        Args:
            game_id: Identifier for the game
            initial_line: Opening line
        """
        self.game_id = game_id
        self.movements: List[LineMovement] = []
        self.opening_line = initial_line
        self.current_line = initial_line

    def add_movement(self, odds: float, book: str = "unknown", timestamp: Optional[datetime] = None):
        """
        Add a line movement

        Args:
            odds: New odds
            book: Sportsbook name
            timestamp: Time of movement (default: now)
        """
        if timestamp is None:
            timestamp = datetime.now()

        movement = LineMovement(timestamp, odds, book)
        self.movements.append(movement)
        self.current_line = odds

    def get_line_delta(self) -> float:
        """Calculate total line movement from opening"""
        return self.current_line - self.opening_line

    def detect_steam(self, threshold: float = 10, time_window: int = 60) -> List[Dict]:
        """
        Detect steam moves (sharp money movements)

        Steam indicators:
        1. Large sudden movement
        2. Movement across multiple books
        3. Line moves against public betting percentage

        Args:
            threshold: Minimum point/odds movement to consider (cents)
            time_window: Time window in seconds to check

        Returns:
            List of detected steam moves
        """
        steam_moves = []

        for i in range(1, len(self.movements)):
            current = self.movements[i]
            previous = self.movements[i - 1]

            # Calculate movement
            delta = current.odds - previous.odds

            # Time difference
            time_diff = (current.timestamp - previous.timestamp).total_seconds()

            # Check for steam criteria
            if abs(delta) >= threshold and time_diff <= time_window:
                steam_moves.append({
                    'timestamp': current.timestamp,
                    'from': previous.odds,
                    'to': current.odds,
                    'delta': delta,
                    'time_seconds': time_diff,
                    'book': current.book,
                    'type': 'sharp' if abs(delta) >= threshold else 'public'
                })

        return steam_moves

    def analyze_movement_pattern(self) -> Dict:
        """
        Analyze the pattern of line movement

        Returns:
            Dictionary with movement analysis
        """
        if len(self.movements) < 2:
            return {
                'pattern': 'insufficient_data',
                'movements': 0
            }

        total_delta = self.get_line_delta()
        num_movements = len(self.movements)

        # Calculate volatility (standard deviation of movements)
        deltas = []
        for i in range(1, len(self.movements)):
            delta = self.movements[i].odds - self.movements[i-1].odds
            deltas.append(delta)

        avg_delta = sum(deltas) / len(deltas) if deltas else 0
        variance = sum((d - avg_delta) ** 2 for d in deltas) / len(deltas) if deltas else 0
        volatility = variance ** 0.5

        # Determine pattern
        if total_delta > 0:
            direction = 'upward'
        elif total_delta < 0:
            direction = 'downward'
        else:
            direction = 'stable'

        # Check for reverse line movement (RLM)
        # RLM = line moves opposite to public betting
        # Simplified: check for consistent direction
        consistent_direction = all(d > 0 for d in deltas) or all(d < 0 for d in deltas)

        return {
            'pattern': direction,
            'total_movement': total_delta,
            'num_movements': num_movements,
            'avg_movement': avg_delta,
            'volatility': volatility,
            'consistent': consistent_direction,
            'potential_rlm': consistent_direction and abs(total_delta) > 5
        }

    def calculate_clv_opportunity(self, opening_line: Optional[float] = None) -> float:
        """
        Calculate potential CLV if betting now vs opening

        Args:
            opening_line: Opening line (default: use stored opening line)

        Returns:
            CLV in percentage
        """
        if opening_line is None:
            opening_line = self.opening_line

        # Convert to implied probability
        if opening_line > 0:
            opening_prob = 100 / (opening_line + 100)
        else:
            opening_prob = abs(opening_line) / (abs(opening_line) + 100)

        if self.current_line > 0:
            current_prob = 100 / (self.current_line + 100)
        else:
            current_prob = abs(self.current_line) / (abs(self.current_line) + 100)

        # CLV = improvement in implied probability
        clv = ((opening_prob - current_prob) / current_prob) * 100

        return clv

    def print_summary(self):
        """Print line movement summary"""
        print(f"\n{'='*70}")
        print(f"Line Movement Analysis: {self.game_id}")
        print(f"{'='*70}")

        print(f"\nLine History:")
        print(f"  Opening Line: {self.opening_line:+.0f}")
        print(f"  Current Line: {self.current_line:+.0f}")
        print(f"  Total Movement: {self.get_line_delta():+.0f}")
        print(f"  Number of Movements: {len(self.movements)}")

        # Pattern analysis
        pattern = self.analyze_movement_pattern()

        print(f"\nMovement Pattern:")
        print(f"  Direction: {pattern['pattern'].title()}")
        print(f"  Average Movement: {pattern.get('avg_movement', 0):+.2f}")
        print(f"  Volatility: {pattern.get('volatility', 0):.2f}")

        if pattern.get('potential_rlm'):
            print(f"\n  ⚠️  Potential Reverse Line Movement (RLM) detected!")
            print(f"      Line moving against public - possible sharp action")

        # Steam detection
        steam_moves = self.detect_steam()

        if steam_moves:
            print(f"\n🔥 Steam Moves Detected: {len(steam_moves)}")
            for i, move in enumerate(steam_moves[:5], 1):
                print(f"\n  {i}. {move['timestamp'].strftime('%H:%M:%S')}")
                print(f"     {move['from']:+.0f} → {move['to']:+.0f} ({move['delta']:+.0f})")
                print(f"     Book: {move['book']}")
                print(f"     Type: {move['type'].upper()}")

        # CLV opportunity
        clv = self.calculate_clv_opportunity()

        print(f"\nCLV Analysis:")
        print(f"  Betting now vs opening: {clv:+.2f}%")

        if clv > 2:
            print(f"  ✓ GOOD - Improved value from opening")
        elif clv < -2:
            print(f"  ✗ WORSE - Lost value from opening")
        else:
            print(f"  ~ NEUTRAL - Similar to opening")

    def export_to_csv(self, filename: str):
        """Export movements to CSV"""
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'Odds', 'Book', 'Delta'])

            for i, movement in enumerate(self.movements):
                if i == 0:
                    delta = 0
                else:
                    delta = movement.odds - self.movements[i-1].odds

                writer.writerow([
                    movement.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    movement.odds,
                    movement.book,
                    delta
                ])

        print(f"✓ Exported to {filename}")


class MultiBookTracker:
    """Track lines across multiple sportsbooks"""

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.books: Dict[str, LineTracker] = {}

    def add_book(self, book_name: str, opening_line: float):
        """Add a sportsbook to track"""
        self.books[book_name] = LineTracker(f"{self.game_id}_{book_name}", opening_line)

    def update_line(self, book_name: str, new_line: float):
        """Update line for a specific book"""
        if book_name in self.books:
            self.books[book_name].add_movement(new_line, book_name)
        else:
            # Auto-add if not exists
            self.add_book(book_name, new_line)

    def find_best_line(self, side: str = 'favorite') -> Dict:
        """
        Find best current line across all books

        Args:
            side: 'favorite' or 'underdog'

        Returns:
            Dictionary with best line info
        """
        if not self.books:
            return {}

        best_book = None
        best_line = None

        for book_name, tracker in self.books.items():
            current = tracker.current_line

            if best_line is None:
                best_line = current
                best_book = book_name
            else:
                if side == 'favorite':
                    # For favorite, less negative is better
                    if current > best_line:
                        best_line = current
                        best_book = book_name
                else:
                    # For underdog, more positive is better
                    if current > best_line:
                        best_line = current
                        best_book = book_name

        return {
            'book': best_book,
            'line': best_line,
            'value': abs(best_line - min(t.current_line for t in self.books.values()))
        }

    def detect_line_disparity(self, threshold: float = 5) -> List[Dict]:
        """
        Detect significant line disparities between books

        Args:
            threshold: Minimum disparity to flag

        Returns:
            List of disparities
        """
        if len(self.books) < 2:
            return []

        disparities = []
        book_lines = [(name, tracker.current_line) for name, tracker in self.books.items()]

        # Compare all pairs
        for i in range(len(book_lines)):
            for j in range(i + 1, len(book_lines)):
                book1, line1 = book_lines[i]
                book2, line2 = book_lines[j]

                diff = abs(line1 - line2)

                if diff >= threshold:
                    disparities.append({
                        'book1': book1,
                        'line1': line1,
                        'book2': book2,
                        'line2': line2,
                        'disparity': diff
                    })

        return disparities

    def print_comparison(self):
        """Print comparison across all books"""
        print(f"\n{'='*70}")
        print(f"Multi-Book Line Comparison: {self.game_id}")
        print(f"{'='*70}")

        print(f"\n{'Book':<20} {'Current Line':<15} {'Movement':<15}")
        print(f"{'-'*70}")

        for book_name, tracker in sorted(self.books.items()):
            movement = tracker.get_line_delta()
            print(f"{book_name:<20} {tracker.current_line:>+14.0f} {movement:>+14.0f}")

        # Best line
        best_fav = self.find_best_line('favorite')
        best_dog = self.find_best_line('underdog')

        print(f"\nBest Lines:")
        print(f"  Favorite: {best_fav['book']} @ {best_fav['line']:+.0f}")
        print(f"  Underdog: {best_dog['book']} @ {best_dog['line']:+.0f}")

        # Line disparities
        disparities = self.detect_line_disparity()

        if disparities:
            print(f"\n⚠️  Line Disparities Detected:")
            for disp in disparities:
                print(f"  {disp['book1']}: {disp['line1']:+.0f} vs "
                      f"{disp['book2']}: {disp['line2']:+.0f} "
                      f"(Diff: {disp['disparity']:.0f})")


def main():
    """Demo line tracker"""
    import argparse

    parser = argparse.ArgumentParser(description='Line Movement Tracker')
    parser.add_argument('game', help='Game identifier')
    parser.add_argument('opening', type=float, help='Opening line')
    parser.add_argument('-m', '--movement', action='append', nargs=2,
                       metavar=('ODDS', 'BOOK'),
                       help='Add line movement: odds book')

    args = parser.parse_args()

    # Create tracker
    tracker = LineTracker(args.game, args.opening)

    # Add movements
    if args.movement:
        for odds, book in args.movement:
            tracker.add_movement(float(odds), book)

    # Print summary
    tracker.print_summary()


if __name__ == '__main__':
    main()
