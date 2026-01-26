#!/usr/bin/env python3
"""
Horse Racing Analytics Library

Comprehensive analytics toolkit for horse racing betting, including:
- Speed rating models with track surface adjustments
- Jockey and trainer statistical analysis
- Post position bias analysis
- Distance and surface specialization models
- Exotic bet probability calculators (exacta, trifecta, superfecta)
- Track condition and weather impact models
- Class rating and form analysis
"""

import argparse
import json
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class TrackSurface(Enum):
    """Track surface types"""
    DIRT = "dirt"
    TURF = "turf"
    SYNTHETIC = "synthetic"


class TrackCondition(Enum):
    """Track condition ratings"""
    FAST = "fast"
    GOOD = "good"
    MUDDY = "muddy"
    SLOPPY = "sloppy"
    YIELDING = "yielding"
    SOFT = "soft"
    HEAVY = "heavy"
    FIRM = "firm"


@dataclass
class Horse:
    """Represents a horse in a race"""
    name: str
    odds: float  # American odds
    post_position: int
    jockey: str
    trainer: str
    recent_speed_figures: List[int]
    best_speed_figure: int
    days_since_last_race: int
    career_starts: int
    career_wins: int
    career_places: int
    career_shows: int
    distance_starts: int = 0  # Starts at this distance
    distance_wins: int = 0    # Wins at this distance
    surface_starts: int = 0   # Starts on this surface
    surface_wins: int = 0     # Wins on this surface

    def win_percentage(self) -> float:
        """Calculate career win percentage"""
        if self.career_starts == 0:
            return 0.0
        return (self.career_wins / self.career_starts) * 100

    def distance_win_percentage(self) -> float:
        """Calculate win percentage at this distance"""
        if self.distance_starts == 0:
            return 0.0
        return (self.distance_wins / self.distance_starts) * 100

    def surface_win_percentage(self) -> float:
        """Calculate win percentage on this surface"""
        if self.surface_starts == 0:
            return 0.0
        return (self.surface_wins / self.surface_starts) * 100


@dataclass
class JockeyStats:
    """Statistics for a jockey"""
    name: str
    starts: int
    wins: int
    places: int
    shows: int
    earnings: float = 0.0

    def win_percentage(self) -> float:
        if self.starts == 0:
            return 0.0
        return (self.wins / self.starts) * 100

    def roi(self, total_bet: float = None) -> Optional[float]:
        """Return on investment if total_bet is provided"""
        if total_bet is None or total_bet == 0:
            return None
        return ((self.earnings - total_bet) / total_bet) * 100


@dataclass
class TrainerStats:
    """Statistics for a trainer"""
    name: str
    starts: int
    wins: int
    places: int
    shows: int
    earnings: float = 0.0

    def win_percentage(self) -> float:
        if self.starts == 0:
            return 0.0
        return (self.wins / self.starts) * 100

    def roi(self, total_bet: float = None) -> Optional[float]:
        """Return on investment if total_bet is provided"""
        if total_bet is None or total_bet == 0:
            return None
        return ((self.earnings - total_bet) / total_bet) * 100


class SpeedRatingModel:
    """
    Speed rating model with track surface and condition adjustments

    Beyer Speed Figures-inspired model that adjusts raw times for:
    - Track surface (dirt, turf, synthetic)
    - Track condition (fast, muddy, etc.)
    - Distance
    - Track variant (daily track speed)
    """

    # Base adjustments for different surfaces (points)
    SURFACE_ADJUSTMENTS = {
        TrackSurface.DIRT: 0,
        TrackSurface.TURF: -2,
        TrackSurface.SYNTHETIC: -1
    }

    # Track condition adjustments (points)
    CONDITION_ADJUSTMENTS = {
        TrackCondition.FAST: 0,
        TrackCondition.FIRM: 0,
        TrackCondition.GOOD: -2,
        TrackCondition.YIELDING: -3,
        TrackCondition.MUDDY: -4,
        TrackCondition.SLOPPY: -5,
        TrackCondition.SOFT: -4,
        TrackCondition.HEAVY: -6
    }

    @staticmethod
    def calculate_speed_figure(
        final_time: float,
        distance_furlongs: float,
        track_surface: TrackSurface,
        track_condition: TrackCondition,
        track_variant: int = 0,
        par_time: Optional[float] = None
    ) -> int:
        """
        Calculate speed figure for a race performance

        Args:
            final_time: Final time in seconds
            distance_furlongs: Race distance in furlongs (1 furlong = 1/8 mile)
            track_surface: Type of track surface
            track_condition: Track condition
            track_variant: Daily track speed variant (positive = slower track)
            par_time: Expected par time for this distance/class (optional)

        Returns:
            Speed figure (higher is better, typically 0-120+)
        """
        # Use par time if provided, otherwise estimate based on distance
        if par_time is None:
            # Rough estimate: 12 seconds per furlong for average horse
            par_time = distance_furlongs * 12.0

        # Calculate lengths beaten/ahead (1 length ≈ 0.2 seconds)
        time_diff = par_time - final_time
        lengths_diff = time_diff / 0.2

        # Base figure (100 = par)
        base_figure = 100 + (lengths_diff * 2)  # 2 points per length

        # Apply surface adjustment
        surface_adj = SpeedRatingModel.SURFACE_ADJUSTMENTS.get(track_surface, 0)

        # Apply condition adjustment
        condition_adj = SpeedRatingModel.CONDITION_ADJUSTMENTS.get(track_condition, 0)

        # Apply track variant
        variant_adj = -track_variant

        # Final speed figure
        speed_figure = int(base_figure + surface_adj + condition_adj + variant_adj)

        return max(0, speed_figure)  # Don't allow negative figures

    @staticmethod
    def calculate_average_speed_figure(recent_figures: List[int], num_races: int = 3) -> float:
        """
        Calculate average of recent speed figures

        Args:
            recent_figures: List of recent speed figures (most recent first)
            num_races: Number of recent races to average

        Returns:
            Average speed figure
        """
        if not recent_figures:
            return 0.0

        relevant_figures = recent_figures[:num_races]
        return sum(relevant_figures) / len(relevant_figures)

    @staticmethod
    def calculate_form_trend(recent_figures: List[int]) -> str:
        """
        Analyze form trend from recent speed figures

        Args:
            recent_figures: List of recent speed figures (most recent first)

        Returns:
            "improving", "declining", "consistent", or "unknown"
        """
        if len(recent_figures) < 2:
            return "unknown"

        if len(recent_figures) >= 3:
            # Check last 3 races
            if recent_figures[0] > recent_figures[1] > recent_figures[2]:
                return "improving"
            elif recent_figures[0] < recent_figures[1] < recent_figures[2]:
                return "declining"

        # Check last 2 races
        diff = recent_figures[0] - recent_figures[1]
        if diff > 5:
            return "improving"
        elif diff < -5:
            return "declining"

        return "consistent"


class PostPositionAnalysis:
    """
    Post position bias analysis

    Analyzes the impact of post position on win probability based on:
    - Track configuration (oval vs. straight)
    - Distance (shorter races favor inside posts)
    - Number of horses in race
    """

    @staticmethod
    def calculate_post_bias(
        post_position: int,
        num_horses: int,
        distance_furlongs: float,
        track_type: str = "oval"
    ) -> float:
        """
        Calculate post position bias adjustment

        Args:
            post_position: Post position (1 = rail)
            num_horses: Total number of horses in race
            distance_furlongs: Race distance
            track_type: "oval" or "straight"

        Returns:
            Bias multiplier (1.0 = neutral, >1.0 = advantage, <1.0 = disadvantage)
        """
        if track_type == "straight":
            # Straight courses have minimal post bias
            return 1.0

        # For oval tracks, post position matters more in sprint races
        if distance_furlongs <= 7:  # Sprint races
            # Inside posts (1-3) have advantage in sprints
            if post_position <= 3:
                return 1.15
            elif post_position >= num_horses - 2:
                # Outside posts struggle
                return 0.85
            else:
                return 1.0
        else:  # Route races (longer distances)
            # Post position matters less in routes
            if post_position <= 2:
                return 1.05
            elif post_position >= num_horses - 1:
                return 0.95
            else:
                return 1.0

    @staticmethod
    def get_optimal_post_range(
        distance_furlongs: float,
        num_horses: int
    ) -> Tuple[int, int]:
        """
        Get the optimal post position range for given conditions

        Returns:
            Tuple of (min_post, max_post) for optimal range
        """
        if distance_furlongs <= 7:  # Sprints
            return (1, min(4, num_horses))
        else:  # Routes
            return (1, min(6, num_horses))


class ExoticBetCalculator:
    """
    Calculator for exotic bet probabilities and payouts

    Handles:
    - Exacta (pick first two in order)
    - Trifecta (pick first three in order)
    - Superfecta (pick first four in order)
    - Quinella (pick first two in any order)
    """

    @staticmethod
    def american_to_decimal(american_odds: float) -> float:
        """Convert American odds to decimal odds"""
        if american_odds > 0:
            return (american_odds / 100) + 1
        else:
            return (100 / abs(american_odds)) + 1

    @staticmethod
    def american_to_probability(american_odds: float) -> float:
        """Convert American odds to implied probability"""
        decimal_odds = ExoticBetCalculator.american_to_decimal(american_odds)
        return 1 / decimal_odds

    @staticmethod
    def calculate_exacta_probability(
        horse1_prob: float,
        horse2_prob: float,
        correlation: float = 0.0
    ) -> float:
        """
        Calculate probability of exacta (horse1 first, horse2 second)

        Args:
            horse1_prob: Probability of horse1 winning
            horse2_prob: Probability of horse2 finishing second
            correlation: Correlation coefficient (-1 to 1)

        Returns:
            Exacta probability
        """
        # Basic probability (assumes independence)
        base_prob = horse1_prob * horse2_prob

        # Adjust for correlation
        # Positive correlation: if one does well, other likely does too
        adjustment = 1 + (correlation * 0.2)

        return base_prob * adjustment

    @staticmethod
    def calculate_trifecta_probability(
        horse1_prob: float,
        horse2_prob: float,
        horse3_prob: float
    ) -> float:
        """
        Calculate probability of trifecta (horses finishing 1-2-3 in order)

        Args:
            horse1_prob: Probability of horse1 winning
            horse2_prob: Probability of horse2 finishing second
            horse3_prob: Probability of horse3 finishing third

        Returns:
            Trifecta probability
        """
        return horse1_prob * horse2_prob * horse3_prob

    @staticmethod
    def calculate_superfecta_probability(
        horse1_prob: float,
        horse2_prob: float,
        horse3_prob: float,
        horse4_prob: float
    ) -> float:
        """
        Calculate probability of superfecta (horses finishing 1-2-3-4 in order)

        Returns:
            Superfecta probability
        """
        return horse1_prob * horse2_prob * horse3_prob * horse4_prob

    @staticmethod
    def calculate_exacta_payout(
        horse1_odds: float,
        horse2_odds: float,
        base_bet: float = 2.0
    ) -> float:
        """
        Estimate exacta payout

        Args:
            horse1_odds: American odds for horse1
            horse2_odds: American odds for horse2
            base_bet: Base bet amount (typically $2)

        Returns:
            Estimated payout for base bet
        """
        decimal1 = ExoticBetCalculator.american_to_decimal(horse1_odds)
        decimal2 = ExoticBetCalculator.american_to_decimal(horse2_odds)

        # Rough estimate: multiply decimal odds and scale
        combined_odds = (decimal1 - 1) * (decimal2 - 1) + 1

        return base_bet * combined_odds * 0.7  # 0.7 for track take

    @staticmethod
    def calculate_exacta_expected_value(
        horse1_odds: float,
        horse2_odds: float,
        horse1_true_prob: float,
        horse2_true_prob: float,
        bet_amount: float = 2.0
    ) -> Dict:
        """
        Calculate expected value for an exacta bet

        Returns:
            Dictionary with probability, payout, expected value, and ROI
        """
        prob = ExoticBetCalculator.calculate_exacta_probability(
            horse1_true_prob,
            horse2_true_prob
        )
        payout = ExoticBetCalculator.calculate_exacta_payout(
            horse1_odds,
            horse2_odds,
            bet_amount
        )

        expected_value = (prob * payout) - bet_amount
        roi = (expected_value / bet_amount) * 100

        return {
            'probability': prob,
            'payout': payout,
            'expected_value': expected_value,
            'roi': roi,
            'bet_amount': bet_amount
        }


class DistanceSurfaceModel:
    """
    Model for analyzing horse performance by distance and surface

    Evaluates:
    - Distance suitability (sprinter vs router)
    - Surface preferences (dirt, turf, synthetic)
    - Distance/surface combination patterns
    """

    @staticmethod
    def classify_distance(distance_furlongs: float) -> str:
        """Classify race distance"""
        if distance_furlongs <= 7:
            return "sprint"
        elif distance_furlongs <= 9:
            return "middle"
        else:
            return "route"

    @staticmethod
    def calculate_distance_suitability(
        horse: Horse,
        race_distance_furlongs: float
    ) -> float:
        """
        Calculate how suitable this distance is for the horse

        Args:
            horse: Horse object with distance statistics
            race_distance_furlongs: Distance of upcoming race

        Returns:
            Suitability score (0-1, higher is better)
        """
        if horse.distance_starts == 0:
            # No data at this distance, use career win rate
            return horse.win_percentage() / 100

        # Use distance-specific win percentage
        distance_win_rate = horse.distance_win_percentage() / 100

        # Weight by sample size
        confidence = min(horse.distance_starts / 10, 1.0)
        career_win_rate = horse.win_percentage() / 100

        # Blend distance-specific and career rates based on confidence
        suitability = (confidence * distance_win_rate) + ((1 - confidence) * career_win_rate)

        return suitability

    @staticmethod
    def calculate_surface_suitability(
        horse: Horse,
        race_surface: TrackSurface
    ) -> float:
        """
        Calculate how suitable this surface is for the horse

        Returns:
            Suitability score (0-1, higher is better)
        """
        if horse.surface_starts == 0:
            # No data on this surface, use career win rate
            return horse.win_percentage() / 100

        # Use surface-specific win percentage
        surface_win_rate = horse.surface_win_percentage() / 100

        # Weight by sample size
        confidence = min(horse.surface_starts / 10, 1.0)
        career_win_rate = horse.win_percentage() / 100

        # Blend surface-specific and career rates
        suitability = (confidence * surface_win_rate) + ((1 - confidence) * career_win_rate)

        return suitability

    @staticmethod
    def identify_specialist_type(horse: Horse) -> str:
        """
        Identify if horse is a specialist

        Returns:
            "sprinter", "router", "turf_specialist", "dirt_specialist", or "versatile"
        """
        # Check distance specialization
        if horse.distance_starts >= 5:
            distance_rate = horse.distance_win_percentage()
            overall_rate = horse.win_percentage()

            if distance_rate > overall_rate * 1.5:
                # Strong at this distance
                return "distance_specialist"

        # Check surface specialization
        if horse.surface_starts >= 5:
            surface_rate = horse.surface_win_percentage()
            overall_rate = horse.win_percentage()

            if surface_rate > overall_rate * 1.5:
                return "surface_specialist"

        return "versatile"


class HorseRacingAnalyzer:
    """
    Comprehensive horse racing analyzer

    Combines all models to produce a complete race analysis with:
    - Win probability adjustments
    - Recommended bets
    - Risk assessment
    """

    def __init__(self):
        self.speed_model = SpeedRatingModel()
        self.post_model = PostPositionAnalysis()
        self.exotic_calc = ExoticBetCalculator()
        self.distance_model = DistanceSurfaceModel()

    def analyze_horse(
        self,
        horse: Horse,
        race_distance_furlongs: float,
        race_surface: TrackSurface,
        num_horses: int,
        jockey_stats: Optional[JockeyStats] = None,
        trainer_stats: Optional[TrainerStats] = None
    ) -> Dict:
        """
        Comprehensive analysis of a single horse

        Returns:
            Dictionary with analysis results
        """
        # Base probability from odds
        market_prob = self.exotic_calc.american_to_probability(horse.odds)

        # Speed rating analysis
        avg_speed = self.speed_model.calculate_average_speed_figure(
            horse.recent_speed_figures
        )
        form_trend = self.speed_model.calculate_form_trend(horse.recent_speed_figures)

        # Post position bias
        post_bias = self.post_model.calculate_post_bias(
            horse.post_position,
            num_horses,
            race_distance_furlongs
        )

        # Distance suitability
        distance_suit = self.distance_model.calculate_distance_suitability(
            horse,
            race_distance_furlongs
        )

        # Surface suitability
        surface_suit = self.distance_model.calculate_surface_suitability(
            horse,
            race_surface
        )

        # Specialist type
        specialist = self.distance_model.identify_specialist_type(horse)

        # Adjusted probability (simple multiplicative model)
        adjusted_prob = market_prob * post_bias * (1 + (distance_suit - 0.5)) * (1 + (surface_suit - 0.5))

        # Normalize to reasonable range
        adjusted_prob = max(0.01, min(0.95, adjusted_prob))

        analysis = {
            'horse_name': horse.name,
            'market_odds': horse.odds,
            'market_probability': market_prob,
            'adjusted_probability': adjusted_prob,
            'average_speed_figure': avg_speed,
            'best_speed_figure': horse.best_speed_figure,
            'form_trend': form_trend,
            'post_position': horse.post_position,
            'post_bias_multiplier': post_bias,
            'distance_suitability': distance_suit,
            'surface_suitability': surface_suit,
            'specialist_type': specialist,
            'days_since_last_race': horse.days_since_last_race,
            'career_record': f"{horse.career_wins}-{horse.career_places}-{horse.career_shows} from {horse.career_starts}",
            'win_percentage': horse.win_percentage()
        }

        # Add jockey stats if provided
        if jockey_stats:
            analysis['jockey'] = horse.jockey
            analysis['jockey_win_pct'] = jockey_stats.win_percentage()

        # Add trainer stats if provided
        if trainer_stats:
            analysis['trainer'] = horse.trainer
            analysis['trainer_win_pct'] = trainer_stats.win_percentage()

        return analysis

    def analyze_race(
        self,
        horses: List[Horse],
        race_distance_furlongs: float,
        race_surface: TrackSurface,
        jockey_stats_map: Optional[Dict[str, JockeyStats]] = None,
        trainer_stats_map: Optional[Dict[str, TrainerStats]] = None
    ) -> List[Dict]:
        """
        Analyze entire race and rank horses

        Returns:
            List of horse analyses sorted by adjusted probability (descending)
        """
        analyses = []

        for horse in horses:
            jockey_stats = None
            trainer_stats = None

            if jockey_stats_map and horse.jockey in jockey_stats_map:
                jockey_stats = jockey_stats_map[horse.jockey]

            if trainer_stats_map and horse.trainer in trainer_stats_map:
                trainer_stats = trainer_stats_map[horse.trainer]

            analysis = self.analyze_horse(
                horse,
                race_distance_furlongs,
                race_surface,
                len(horses),
                jockey_stats,
                trainer_stats
            )

            analyses.append(analysis)

        # Sort by adjusted probability (descending)
        analyses.sort(key=lambda x: x['adjusted_probability'], reverse=True)

        return analyses

    def find_betting_opportunities(
        self,
        race_analyses: List[Dict],
        min_edge: float = 0.05
    ) -> List[Dict]:
        """
        Find horses with positive expected value

        Args:
            race_analyses: List of horse analyses from analyze_race()
            min_edge: Minimum edge required (default 5%)

        Returns:
            List of betting opportunities
        """
        opportunities = []

        for analysis in race_analyses:
            market_prob = analysis['market_probability']
            adjusted_prob = analysis['adjusted_probability']

            # Calculate edge
            edge = adjusted_prob - market_prob

            if edge >= min_edge:
                opportunity = {
                    'horse_name': analysis['horse_name'],
                    'odds': analysis['market_odds'],
                    'market_probability': market_prob,
                    'true_probability': adjusted_prob,
                    'edge': edge,
                    'edge_percentage': (edge / market_prob) * 100,
                    'recommendation': 'STRONG BET' if edge >= 0.10 else 'BET'
                }

                opportunities.append(opportunity)

        return opportunities


def main():
    """Command-line interface for horse racing analytics"""
    parser = argparse.ArgumentParser(
        description="Horse Racing Analytics - Comprehensive betting analysis"
    )

    parser.add_argument(
        'command',
        choices=['speed-rating', 'post-bias', 'exacta', 'analyze-race'],
        help='Analysis command to run'
    )

    # Speed rating arguments
    parser.add_argument('--final-time', type=float, help='Final time in seconds')
    parser.add_argument('--distance', type=float, help='Distance in furlongs')
    parser.add_argument('--surface', choices=['dirt', 'turf', 'synthetic'], help='Track surface')
    parser.add_argument('--condition', help='Track condition')
    parser.add_argument('--par-time', type=float, help='Par time for this class/distance')

    # Post position arguments
    parser.add_argument('--post', type=int, help='Post position')
    parser.add_argument('--horses', type=int, help='Number of horses in race')

    # Exacta arguments
    parser.add_argument('--horse1-odds', type=float, help='Horse 1 American odds')
    parser.add_argument('--horse2-odds', type=float, help='Horse 2 American odds')
    parser.add_argument('--horse1-prob', type=float, help='Horse 1 true win probability')
    parser.add_argument('--horse2-prob', type=float, help='Horse 2 true place probability')
    parser.add_argument('--bet', type=float, default=2.0, help='Bet amount')

    # Race analysis arguments
    parser.add_argument('--race-file', help='JSON file with race data')

    args = parser.parse_args()

    if args.command == 'speed-rating':
        if not all([args.final_time, args.distance, args.surface, args.condition]):
            print("Error: speed-rating requires --final-time, --distance, --surface, and --condition")
            return

        surface = TrackSurface(args.surface)
        condition = TrackCondition(args.condition)

        speed_fig = SpeedRatingModel.calculate_speed_figure(
            args.final_time,
            args.distance,
            surface,
            condition,
            par_time=args.par_time
        )

        print(f"\nSpeed Rating Analysis")
        print(f"{'=' * 50}")
        print(f"Final Time: {args.final_time:.2f} seconds")
        print(f"Distance: {args.distance} furlongs")
        print(f"Surface: {surface.value}")
        print(f"Condition: {condition.value}")
        print(f"\nSpeed Figure: {speed_fig}")
        print(f"\nInterpretation:")
        if speed_fig >= 100:
            print("  Above par performance")
        elif speed_fig >= 90:
            print("  Near par performance")
        else:
            print("  Below par performance")

    elif args.command == 'post-bias':
        if not all([args.post, args.horses, args.distance]):
            print("Error: post-bias requires --post, --horses, and --distance")
            return

        bias = PostPositionAnalysis.calculate_post_bias(
            args.post,
            args.horses,
            args.distance
        )

        optimal_range = PostPositionAnalysis.get_optimal_post_range(
            args.distance,
            args.horses
        )

        print(f"\nPost Position Bias Analysis")
        print(f"{'=' * 50}")
        print(f"Post Position: {args.post}")
        print(f"Field Size: {args.horses} horses")
        print(f"Distance: {args.distance} furlongs")
        print(f"\nBias Multiplier: {bias:.2f}")
        print(f"Optimal Post Range: {optimal_range[0]}-{optimal_range[1]}")

        if bias > 1.0:
            print(f"\nAdvantage: +{((bias - 1) * 100):.1f}%")
        elif bias < 1.0:
            print(f"\nDisadvantage: {((bias - 1) * 100):.1f}%")
        else:
            print("\nNeutral position")

    elif args.command == 'exacta':
        if not all([args.horse1_odds, args.horse2_odds, args.horse1_prob, args.horse2_prob]):
            print("Error: exacta requires --horse1-odds, --horse2-odds, --horse1-prob, --horse2-prob")
            return

        result = ExoticBetCalculator.calculate_exacta_expected_value(
            args.horse1_odds,
            args.horse2_odds,
            args.horse1_prob,
            args.horse2_prob,
            args.bet
        )

        print(f"\nExacta Bet Analysis")
        print(f"{'=' * 50}")
        print(f"Horse 1 Odds: {args.horse1_odds:+.0f}")
        print(f"Horse 2 Odds: {args.horse2_odds:+.0f}")
        print(f"Bet Amount: ${args.bet:.2f}")
        print(f"\nProbability: {result['probability'] * 100:.2f}%")
        print(f"Estimated Payout: ${result['payout']:.2f}")
        print(f"Expected Value: ${result['expected_value']:.2f}")
        print(f"ROI: {result['roi']:.1f}%")

        if result['expected_value'] > 0:
            print(f"\n✓ POSITIVE EXPECTED VALUE - Consider betting")
        else:
            print(f"\n✗ NEGATIVE EXPECTED VALUE - Avoid")

    elif args.command == 'analyze-race':
        if not args.race_file:
            print("Error: analyze-race requires --race-file")
            return

        try:
            with open(args.race_file, 'r') as f:
                race_data = json.load(f)
        except FileNotFoundError:
            print(f"Error: File '{args.race_file}' not found")
            return
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in '{args.race_file}'")
            return

        # Parse race data
        horses = []
        for h_data in race_data.get('horses', []):
            horse = Horse(
                name=h_data['name'],
                odds=h_data['odds'],
                post_position=h_data['post_position'],
                jockey=h_data.get('jockey', 'Unknown'),
                trainer=h_data.get('trainer', 'Unknown'),
                recent_speed_figures=h_data.get('recent_speed_figures', []),
                best_speed_figure=h_data.get('best_speed_figure', 0),
                days_since_last_race=h_data.get('days_since_last_race', 0),
                career_starts=h_data.get('career_starts', 0),
                career_wins=h_data.get('career_wins', 0),
                career_places=h_data.get('career_places', 0),
                career_shows=h_data.get('career_shows', 0),
                distance_starts=h_data.get('distance_starts', 0),
                distance_wins=h_data.get('distance_wins', 0),
                surface_starts=h_data.get('surface_starts', 0),
                surface_wins=h_data.get('surface_wins', 0)
            )
            horses.append(horse)

        distance = race_data.get('distance_furlongs', 8.0)
        surface = TrackSurface(race_data.get('surface', 'dirt'))

        # Analyze race
        analyzer = HorseRacingAnalyzer()
        analyses = analyzer.analyze_race(horses, distance, surface)

        print(f"\nRace Analysis")
        print(f"{'=' * 80}")
        print(f"Distance: {distance} furlongs ({DistanceSurfaceModel.classify_distance(distance)})")
        print(f"Surface: {surface.value}")
        print(f"Field Size: {len(horses)} horses")
        print(f"\nHorse Rankings:")
        print(f"{'-' * 80}")

        for i, analysis in enumerate(analyses, 1):
            print(f"\n{i}. {analysis['horse_name']}")
            print(f"   Odds: {analysis['market_odds']:+.0f} (Market: {analysis['market_probability']*100:.1f}%)")
            print(f"   Adjusted Probability: {analysis['adjusted_probability']*100:.1f}%")
            print(f"   Speed: Avg {analysis['average_speed_figure']:.0f}, Best {analysis['best_speed_figure']}")
            print(f"   Form: {analysis['form_trend'].capitalize()}")
            print(f"   Post: {analysis['post_position']} (bias: {analysis['post_bias_multiplier']:.2f})")
            print(f"   Distance Suit: {analysis['distance_suitability']*100:.0f}%")
            print(f"   Surface Suit: {analysis['surface_suitability']*100:.0f}%")

        # Find betting opportunities
        opportunities = analyzer.find_betting_opportunities(analyses)

        if opportunities:
            print(f"\n\nBetting Opportunities")
            print(f"{'=' * 80}")
            for opp in opportunities:
                print(f"\n{opp['recommendation']}: {opp['horse_name']}")
                print(f"   Odds: {opp['odds']:+.0f}")
                print(f"   Market Prob: {opp['market_probability']*100:.1f}%")
                print(f"   True Prob: {opp['true_probability']*100:.1f}%")
                print(f"   Edge: {opp['edge']*100:.1f}% ({opp['edge_percentage']:.1f}% of market)")
        else:
            print(f"\n\nNo betting opportunities found with positive expected value")


if __name__ == '__main__':
    main()
