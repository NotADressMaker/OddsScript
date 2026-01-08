"""
TrackScript Arbitrage & Value Finding Package
Find guaranteed profit opportunities and value plays across multiple tracks/books
"""

import math
from typing import Dict, List, Tuple, Any, Optional


class ArbitrageDetector:
    """Detect arbitrage opportunities in horse racing markets"""

    @staticmethod
    def dutching_arbitrage(horses: List[Dict[str, float]],
                          track_takeout: float = 0.17) -> Dict[str, Any]:
        """Calculate if dutching multiple horses can guarantee profit
        Returns arbitrage opportunity details
        """
        total_implied_prob = 0.0

        for horse in horses:
            odds = horse.get('odds', 0)
            if odds <= 1.0:
                continue
            implied_prob = 1 / odds
            total_implied_prob += implied_prob

        # After takeout, is there an arb?
        effective_prob = total_implied_prob * (1 + track_takeout)

        is_arb = effective_prob < 1.0
        profit_margin = (1.0 - effective_prob) * 100 if is_arb else 0

        return {
            "is_arbitrage": is_arb,
            "profit_margin_pct": profit_margin,
            "total_implied_prob": total_implied_prob,
            "effective_prob": effective_prob,
            "playable": is_arb
        }

    @staticmethod
    def cross_track_arbitrage(track1_odds: Dict[str, float],
                             track2_odds: Dict[str, float],
                             track1_takeout: float,
                             track2_takeout: float) -> Optional[Dict[str, Any]]:
        """Find arbitrage between same race at different tracks"""
        opportunities = []

        # Compare odds for each horse
        all_horses = set(track1_odds.keys()) | set(track2_odds.keys())

        for horse in all_horses:
            odds1 = track1_odds.get(horse, 0)
            odds2 = track2_odds.get(horse, 0)

            if odds1 > 0 and odds2 > 0:
                # Take best odds for each horse
                best_odds = max(odds1, odds2)
                best_track = "track1" if odds1 > odds2 else "track2"

                opportunities.append({
                    "horse": horse,
                    "best_odds": best_odds,
                    "track": best_track,
                    "advantage": abs(odds1 - odds2) / min(odds1, odds2) * 100
                })

        if not opportunities:
            return None

        # Calculate if overall arbitrage exists
        total_prob = sum(1 / opp["best_odds"] for opp in opportunities)
        avg_takeout = (track1_takeout + track2_takeout) / 2

        is_arb = total_prob < (1.0 - avg_takeout)

        return {
            "opportunities": opportunities,
            "is_arbitrage": is_arb,
            "edge_pct": (1.0 - total_prob) * 100 if is_arb else 0
        }

    @staticmethod
    def place_show_arbitrage(win_odds: float, place_odds: float, show_odds: float,
                            num_runners: int) -> Dict[str, Any]:
        """Detect value in place/show pools vs win pool"""
        # Theoretical place probability (roughly 2/num_runners)
        theoretical_place_prob = min(2.0 / num_runners, 0.4)
        # Theoretical show probability (roughly 3/num_runners)
        theoretical_show_prob = min(3.0 / num_runners, 0.6)

        win_implied_prob = 1 / win_odds if win_odds > 0 else 0

        # Calculate expected place/show odds based on win odds
        expected_place_odds = 1 / (win_implied_prob * 2) if win_implied_prob > 0 else 0
        expected_show_odds = 1 / (win_implied_prob * 3) if win_implied_prob > 0 else 0

        place_value = (place_odds - expected_place_odds) / expected_place_odds * 100 if expected_place_odds > 0 else 0
        show_value = (show_odds - expected_show_odds) / expected_show_odds * 100 if expected_show_odds > 0 else 0

        return {
            "place_overlay": place_value > 20,
            "show_overlay": show_value > 20,
            "place_value_pct": place_value,
            "show_value_pct": show_value,
            "best_play": "place" if place_value > show_value else "show"
        }


class ValueFinder:
    """Advanced value finding algorithms"""

    @staticmethod
    def true_odds_calculator(speed_rating: float, class_rating: float,
                            pace_rating: float, form_rating: float,
                            jockey_rating: float, trainer_rating: float) -> float:
        """Calculate true odds from multiple handicapping factors
        Returns estimated fair odds
        """
        # Weighted composite rating
        composite = (
            speed_rating * 0.30 +
            class_rating * 0.20 +
            pace_rating * 0.15 +
            form_rating * 0.15 +
            jockey_rating * 0.10 +
            trainer_rating * 0.10
        )

        # Normalize to 0-100 scale
        normalized = max(0, min(100, composite))

        # Convert to probability (higher rating = higher probability)
        probability = normalized / 100

        # Adjust probability curve (emphasize top horses)
        probability = probability ** 0.8

        # Convert to odds
        if probability <= 0:
            return 99.0
        if probability >= 1.0:
            return 1.1

        fair_odds = 1 / probability
        return fair_odds

    @staticmethod
    def value_bet_calculator(estimated_odds: float, actual_odds: float,
                            min_edge: float = 0.10) -> Dict[str, Any]:
        """Calculate value bet metrics"""
        if estimated_odds <= 0 or actual_odds <= 0:
            return {"is_value": False, "edge": 0, "roi": 0}

        estimated_prob = 1 / estimated_odds
        actual_prob = 1 / actual_odds

        edge = actual_prob - estimated_prob
        edge_pct = (edge / estimated_prob) * 100 if estimated_prob > 0 else 0

        # Calculate expected ROI
        expected_roi = (estimated_prob * actual_odds - 1) * 100

        is_value = edge >= min_edge

        return {
            "is_value": is_value,
            "edge": edge,
            "edge_pct": edge_pct,
            "expected_roi": expected_roi,
            "kelly_fraction": edge / (actual_odds - 1) if actual_odds > 1 else 0
        }

    @staticmethod
    def multi_race_parlay_value(races: List[Dict[str, float]],
                                min_roi: float = 0.15) -> Dict[str, Any]:
        """Analyze if multi-race wager offers value"""
        combined_prob = 1.0
        combined_odds = 1.0

        for race in races:
            est_prob = race.get('estimated_prob', 0)
            actual_odds = race.get('actual_odds', 0)

            if est_prob <= 0 or actual_odds <= 0:
                return {"is_value": False, "roi": -100}

            combined_prob *= est_prob
            combined_odds *= actual_odds

        if combined_prob <= 0:
            return {"is_value": False, "roi": -100}

        # Calculate expected return
        expected_return = combined_prob * combined_odds
        roi = (expected_return - 1) * 100

        is_value = roi >= (min_roi * 100)

        return {
            "is_value": is_value,
            "combined_prob": combined_prob,
            "combined_odds": combined_odds,
            "roi": roi,
            "playable": is_value
        }

    @staticmethod
    def exotic_value_score(exotic_type: str, key_horses_prob: List[float],
                          exotic_odds: float) -> Dict[str, Any]:
        """Evaluate value in exotic wagers"""
        if exotic_type == "exacta":
            # Probability of exacta = prob(1st) * prob(2nd|1st not selected)
            if len(key_horses_prob) < 2:
                return {"value_score": 0, "is_value": False}

            estimated_prob = key_horses_prob[0] * key_horses_prob[1]

        elif exotic_type == "trifecta":
            if len(key_horses_prob) < 3:
                return {"value_score": 0, "is_value": False}

            estimated_prob = (key_horses_prob[0] *
                            key_horses_prob[1] *
                            key_horses_prob[2])

        elif exotic_type == "superfecta":
            if len(key_horses_prob) < 4:
                return {"value_score": 0, "is_value": False}

            estimated_prob = (key_horses_prob[0] *
                            key_horses_prob[1] *
                            key_horses_prob[2] *
                            key_horses_prob[3])
        else:
            return {"value_score": 0, "is_value": False}

        if estimated_prob <= 0:
            return {"value_score": 0, "is_value": False}

        fair_odds = 1 / estimated_prob
        value_score = (exotic_odds - fair_odds) / fair_odds * 100

        return {
            "value_score": value_score,
            "is_value": value_score > 20,
            "estimated_prob": estimated_prob,
            "fair_odds": fair_odds,
            "overlay_pct": value_score
        }


class MarketEfficiency:
    """Analyze market efficiency and find inefficiencies"""

    @staticmethod
    def favorite_longshot_bias(favorites_roi: float, longshots_roi: float) -> Dict[str, str]:
        """Detect favorite-longshot bias in market"""
        bias_strength = favorites_roi - longshots_roi

        if bias_strength > 20:
            market_type = "strong_favorite_bias"
            strategy = "bet_favorites_avoid_longshots"
        elif bias_strength > 10:
            market_type = "moderate_favorite_bias"
            strategy = "favor_favorites"
        elif bias_strength < -20:
            market_type = "longshot_friendly"
            strategy = "seek_overlays_in_longshots"
        else:
            market_type = "efficient"
            strategy = "seek_individual_value"

        return {
            "market_type": market_type,
            "recommended_strategy": strategy,
            "bias_strength": bias_strength
        }

    @staticmethod
    def pool_size_inefficiency(pool_size: float, avg_pool: float,
                              typical_edge: float = -0.17) -> Dict[str, Any]:
        """Smaller pools tend to have more inefficiencies"""
        size_ratio = pool_size / avg_pool if avg_pool > 0 else 1.0

        # Smaller pools = more opportunity
        if size_ratio < 0.3:
            inefficiency_multiplier = 1.5
            opportunity = "high"
        elif size_ratio < 0.6:
            inefficiency_multiplier = 1.2
            opportunity = "moderate"
        else:
            inefficiency_multiplier = 1.0
            opportunity = "low"

        adjusted_edge = typical_edge * inefficiency_multiplier

        return {
            "pool_size_ratio": size_ratio,
            "inefficiency_multiplier": inefficiency_multiplier,
            "opportunity_level": opportunity,
            "adjusted_edge": adjusted_edge
        }

    @staticmethod
    def late_scratch_value(original_odds: List[float],
                          scratched_favorite: bool) -> Dict[str, Any]:
        """Calculate value creation from late scratches"""
        if scratched_favorite:
            # Favorite scratch creates massive value opportunities
            value_multiplier = 1.8
            opportunity = "major"
        else:
            value_multiplier = 1.2
            opportunity = "moderate"

        return {
            "value_multiplier": value_multiplier,
            "opportunity": opportunity,
            "action": "recalculate_all_probabilities"
        }


def get_arbitrage_functions():
    """Return dictionary of arbitrage functions for interpreter"""
    arb = ArbitrageDetector()
    value = ValueFinder()
    market = MarketEfficiency()

    return {
        # Arbitrage
        'dutching_arbitrage': arb.dutching_arbitrage,
        'cross_track_arbitrage': arb.cross_track_arbitrage,
        'place_show_arbitrage': arb.place_show_arbitrage,

        # Value finding
        'true_odds_calculator': value.true_odds_calculator,
        'value_bet_calculator': value.value_bet_calculator,
        'multi_race_parlay_value': value.multi_race_parlay_value,
        'exotic_value_score': value.exotic_value_score,

        # Market efficiency
        'favorite_longshot_bias': market.favorite_longshot_bias,
        'pool_size_inefficiency': market.pool_size_inefficiency,
        'late_scratch_value': market.late_scratch_value,
    }
