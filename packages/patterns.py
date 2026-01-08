"""
TrackScript Pattern Recognition Package
Identify profitable patterns in trainer/jockey behavior, track biases, and betting trends
"""

import math
from typing import Dict, List, Tuple, Any
from collections import defaultdict


class TrainerPatterns:
    """Analyze trainer patterns and specialties"""

    @staticmethod
    def layoff_pattern(trainer: str, layoff_days: int, wins: int, starts: int) -> float:
        """Analyze trainer's success rate after specific layoff periods
        Returns win percentage for this trainer after similar layoffs
        """
        if starts == 0:
            return 0.0
        return (wins / starts) * 100

    @staticmethod
    def first_time_starter_angle(ftse_wins: int, ftse_starts: int) -> Dict[str, Any]:
        """Evaluate trainer's first-time starter effectiveness"""
        if ftse_starts == 0:
            return {"rating": "insufficient_data", "pct": 0.0, "roi": 0.0}

        win_pct = (ftse_wins / ftse_starts) * 100

        # Rating system
        if win_pct > 30:
            rating = "elite"
        elif win_pct > 20:
            rating = "strong"
        elif win_pct > 12:
            rating = "average"
        else:
            rating = "weak"

        return {
            "rating": rating,
            "pct": win_pct,
            "profitable": win_pct > 15
        }

    @staticmethod
    def class_drop_specialist(drop_wins: int, drop_starts: int,
                             raise_wins: int, raise_starts: int) -> float:
        """Identify trainers who excel when dropping horses in class"""
        if drop_starts == 0:
            return 0.0

        drop_pct = (drop_wins / drop_starts) * 100

        # Compare to class raise performance
        raise_pct = (raise_wins / raise_starts) * 100 if raise_starts > 0 else 0

        # Calculate specialization score
        specialization = drop_pct - raise_pct
        return max(0, specialization)

    @staticmethod
    def distance_switch_pattern(route_to_sprint_wins: int,
                               route_to_sprint_starts: int,
                               sprint_to_route_wins: int,
                               sprint_to_route_starts: int) -> Dict[str, float]:
        """Analyze trainer's ability to stretch out or cut back horses"""
        return {
            "stretch_out_pct": (sprint_to_route_wins / sprint_to_route_starts * 100)
                               if sprint_to_route_starts > 0 else 0.0,
            "cut_back_pct": (route_to_sprint_wins / route_to_sprint_starts * 100)
                            if route_to_sprint_starts > 0 else 0.0
        }

    @staticmethod
    def surface_switch_specialist(turf_to_dirt_wins: int,
                                  turf_to_dirt_starts: int) -> float:
        """Identify trainers skilled at moving horses from turf to dirt"""
        if turf_to_dirt_starts == 0:
            return 0.0

        success_rate = (turf_to_dirt_wins / turf_to_dirt_starts) * 100

        # 20%+ is exceptional for surface switches
        return success_rate

    @staticmethod
    def claiming_pattern(claims_won: int, claims_started: int,
                        next_race_wins: int) -> Dict[str, Any]:
        """Analyze trainer's first race after claim performance"""
        if claims_started == 0:
            return {"roi": 0.0, "strike_rate": 0.0, "pattern": "none"}

        strike_rate = (next_race_wins / claims_started) * 100

        # Estimated ROI (assuming average odds)
        estimated_roi = (strike_rate / 20) * 100 - 100  # Rough estimate

        pattern = "strong" if strike_rate > 25 else "weak"

        return {
            "strike_rate": strike_rate,
            "roi": estimated_roi,
            "pattern": pattern
        }


class JockeyPatterns:
    """Analyze jockey riding patterns and specialties"""

    @staticmethod
    def running_style_affinity(jockey_early_wins: int, jockey_early_starts: int,
                               jockey_late_wins: int, jockey_late_starts: int) -> str:
        """Determine if jockey is better on early speed or closers"""
        early_pct = (jockey_early_wins / jockey_early_starts * 100) if jockey_early_starts > 0 else 0
        late_pct = (jockey_late_wins / jockey_late_starts * 100) if jockey_late_starts > 0 else 0

        if early_pct > late_pct + 5:
            return "speed_rider"
        elif late_pct > early_pct + 5:
            return "closer_specialist"
        else:
            return "versatile"

    @staticmethod
    def track_specialist_rating(track_wins: int, track_starts: int,
                               overall_wins: int, overall_starts: int) -> float:
        """Measure how much better jockey performs at specific track"""
        if track_starts == 0 or overall_starts == 0:
            return 0.0

        track_pct = (track_wins / track_starts) * 100
        overall_pct = (overall_wins / overall_starts) * 100

        # Positive difference = track specialist
        return track_pct - overall_pct

    @staticmethod
    def post_position_skill(rail_wins: int, rail_starts: int,
                           outside_wins: int, outside_starts: int) -> Dict[str, float]:
        """Analyze jockey's skill from different post positions"""
        return {
            "rail_pct": (rail_wins / rail_starts * 100) if rail_starts > 0 else 0.0,
            "outside_pct": (outside_wins / outside_starts * 100) if outside_starts > 0 else 0.0
        }

    @staticmethod
    def favorite_performance(fav_wins: int, fav_starts: int) -> Dict[str, Any]:
        """Evaluate jockey's ability to deliver on favorites"""
        if fav_starts == 0:
            return {"roi": -100, "reliable": False}

        win_pct = (fav_wins / fav_starts) * 100

        # Favorites need 33%+ to break even at typical odds
        roi = ((win_pct / 33) - 1) * 100
        reliable = win_pct > 33

        return {
            "win_pct": win_pct,
            "roi": roi,
            "reliable": reliable
        }


class BiasDetector:
    """Detect track biases and advantageous racing conditions"""

    @staticmethod
    def speed_bias_score(frontrunner_wins: int, frontrunner_starters: int,
                        closer_wins: int, closer_starters: int) -> float:
        """Detect if track favors front-runners
        Positive score = speed bias, Negative = closing bias
        """
        if frontrunner_starters == 0 or closer_starters == 0:
            return 0.0

        fr_pct = (frontrunner_wins / frontrunner_starters) * 100
        closer_pct = (closer_wins / closer_starters) * 100

        return fr_pct - closer_pct

    @staticmethod
    def rail_bias(rail_wins: int, rail_runners: int,
                  middle_wins: int, middle_runners: int,
                  outside_wins: int, outside_runners: int) -> str:
        """Detect post position bias"""
        rail_pct = (rail_wins / rail_runners * 100) if rail_runners > 0 else 0
        middle_pct = (middle_wins / middle_runners * 100) if middle_runners > 0 else 0
        outside_pct = (outside_wins / outside_runners * 100) if outside_runners > 0 else 0

        if rail_pct > middle_pct + 5 and rail_pct > outside_pct + 5:
            return "inside"
        elif outside_pct > middle_pct + 5 and outside_pct > rail_pct + 5:
            return "outside"
        elif middle_pct > rail_pct + 3 and middle_pct > outside_pct + 3:
            return "middle"
        else:
            return "neutral"

    @staticmethod
    def wet_track_specialists(wet_wins: int, wet_starts: int,
                             fast_wins: int, fast_starts: int) -> float:
        """Identify horses/connections that excel on off tracks"""
        if wet_starts == 0 or fast_starts == 0:
            return 0.0

        wet_pct = (wet_wins / wet_starts) * 100
        fast_pct = (fast_wins / fast_starts) * 100

        # Positive = wet track specialist
        return wet_pct - fast_pct

    @staticmethod
    def pace_scenario_advantage(contested_pace_wins: int, contested_starts: int,
                                uncontested_pace_wins: int, uncontested_starts: int) -> str:
        """Determine advantage based on pace scenario"""
        contested_pct = (contested_pace_wins / contested_starts * 100) if contested_starts > 0 else 0
        uncontested_pct = (uncontested_pace_wins / uncontested_starts * 100) if uncontested_starts > 0 else 0

        if uncontested_pct > contested_pct + 10:
            return "needs_easy_lead"
        elif contested_pct > uncontested_pct + 10:
            return "pace_presser"
        else:
            return "adaptable"


class BettingPatterns:
    """Analyze betting market patterns and public tendencies"""

    @staticmethod
    def overlay_finder(true_prob: float, morning_line_odds: float,
                      current_odds: float) -> Dict[str, Any]:
        """Identify overlay/underlay situations"""
        ml_prob = 1 / morning_line_odds
        current_prob = 1 / current_odds

        overlay_from_ml = ((ml_prob - true_prob) / true_prob) * 100
        overlay_from_current = ((current_prob - true_prob) / true_prob) * 100

        is_overlay = current_odds > (1 / true_prob)

        return {
            "is_overlay": is_overlay,
            "ml_overlay_pct": overlay_from_ml,
            "current_overlay_pct": overlay_from_current,
            "value": current_odds - (1 / true_prob)
        }

    @staticmethod
    def chalk_eat_pattern(favorites_won: int, favorites_ran: int,
                         avg_favorite_odds: float) -> Dict[str, float]:
        """Analyze favorite performance at track/distance"""
        if favorites_ran == 0:
            return {"win_pct": 0.0, "roi": -100}

        win_pct = (favorites_won / favorites_ran) * 100

        # Calculate ROI
        expected_return_per_dollar = (favorites_won * avg_favorite_odds) / favorites_ran
        roi = (expected_return_per_dollar - 1) * 100

        return {
            "win_pct": win_pct,
            "roi": roi,
            "playable": roi > -10  # Within acceptable loss range
        }

    @staticmethod
    def late_money_indicator(opening_odds: float, current_odds: float,
                            threshold: float = 0.20) -> Dict[str, Any]:
        """Detect significant late money (smart money)"""
        odds_change = ((opening_odds - current_odds) / opening_odds)

        significant = abs(odds_change) > threshold
        direction = "supporting" if odds_change > 0 else "against"

        return {
            "significant_move": significant,
            "direction": direction,
            "change_pct": odds_change * 100,
            "follow": significant and direction == "supporting"
        }


def get_pattern_functions():
    """Return dictionary of pattern recognition functions for interpreter"""
    trainer = TrainerPatterns()
    jockey = JockeyPatterns()
    bias = BiasDetector()
    betting = BettingPatterns()

    return {
        # Trainer patterns
        'layoff_pattern': trainer.layoff_pattern,
        'first_time_starter_angle': trainer.first_time_starter_angle,
        'class_drop_specialist': trainer.class_drop_specialist,
        'distance_switch_pattern': trainer.distance_switch_pattern,
        'surface_switch_specialist': trainer.surface_switch_specialist,
        'claiming_pattern': trainer.claiming_pattern,

        # Jockey patterns
        'running_style_affinity': jockey.running_style_affinity,
        'track_specialist_rating': jockey.track_specialist_rating,
        'post_position_skill': jockey.post_position_skill,
        'favorite_performance': jockey.favorite_performance,

        # Bias detection
        'speed_bias_score': bias.speed_bias_score,
        'rail_bias': bias.rail_bias,
        'wet_track_specialists': bias.wet_track_specialists,
        'pace_scenario_advantage': bias.pace_scenario_advantage,

        # Betting patterns
        'overlay_finder': betting.overlay_finder,
        'chalk_eat_pattern': betting.chalk_eat_pattern,
        'late_money_indicator': betting.late_money_indicator,
    }
