"""
TrackScript Breeding & Pedigree Analysis Package
Advanced bloodline and breeding pattern analysis for handicapping
"""

import math
from typing import Dict, List, Any


class PedigreeAnalyzer:
    """Analyzes horse pedigrees for racing potential"""

    # Dosage system - chef de race classifications
    BRILLIANT = ["Northern Dancer", "Mr. Prospector", "Raise a Native", "Bold Ruler"]
    INTERMEDIATE = ["Seattle Slew", "Nijinsky II", "Secretariat", "Damascus"]
    CLASSIC = ["Princequillo", "Round Table", "Buckpasser", "Arts and Letters"]
    SOLID = ["Equipoise", "Count Fleet", "War Admiral", "Citation"]
    PROFESSIONAL = ["Nasrullah", "Turn-to", "Royal Charger", "Tom Fool"]

    @staticmethod
    def dosage_index(brilliant: int, intermediate: int, classic: int,
                     solid: int, professional: int) -> float:
        """Calculate Dosage Index (DI)
        DI < 4.0 suggests potential for classic distances (1.25 miles+)
        DI > 4.0 suggests sprinter/miler
        """
        speed_points = brilliant + intermediate
        stamina_points = classic + solid + professional

        if stamina_points == 0:
            return 999.0  # Pure sprinter

        return speed_points / stamina_points

    @staticmethod
    def center_of_distribution(brilliant: int, intermediate: int, classic: int,
                               solid: int, professional: int) -> float:
        """Calculate Center of Distribution (CD)
        Measures balance between speed and stamina
        CD closer to 0.0 = more stamina, closer to 1.0 = more speed
        """
        total = brilliant + intermediate + classic + solid + professional
        if total == 0:
            return 0.5

        weighted = (brilliant * 1.0) + (intermediate * 0.5) - (solid * 0.5) - (professional * 1.0)
        cd = 0.5 + (weighted / (2 * total))
        return cd

    @staticmethod
    def optimal_distance(dosage_index: float) -> str:
        """Predict optimal racing distance based on DI"""
        if dosage_index < 1.5:
            return "12+ furlongs (marathon)"
        elif dosage_index < 2.5:
            return "10-12 furlongs (classic)"
        elif dosage_index < 3.5:
            return "8-10 furlongs (route)"
        elif dosage_index < 5.0:
            return "6-8 furlongs (mile)"
        else:
            return "5-7 furlongs (sprint)"

    @staticmethod
    def inbreeding_coefficient(duplications: int, generations_back: int) -> float:
        """Calculate inbreeding coefficient
        Higher values indicate more inbreeding (can be good or bad)
        """
        return duplications * (1 / (2 ** generations_back))

    @staticmethod
    def surface_affinity(turf_wins: int, turf_starts: int,
                        dirt_wins: int, dirt_starts: int) -> str:
        """Determine surface preference from pedigree performance"""
        if turf_starts == 0 and dirt_starts == 0:
            return "unknown"

        turf_pct = (turf_wins / turf_starts * 100) if turf_starts > 0 else 0
        dirt_pct = (dirt_wins / dirt_starts * 100) if dirt_starts > 0 else 0

        if turf_pct > dirt_pct + 10:
            return "turf"
        elif dirt_pct > turf_pct + 10:
            return "dirt"
        else:
            return "versatile"

    @staticmethod
    def maiden_breaker_score(sire_first_crop_wins: int,
                            sire_first_crop_starters: int) -> float:
        """Predict likelihood of winning maiden race based on sire's record
        Score > 0.25 = strong maiden sire
        """
        if sire_first_crop_starters == 0:
            return 0.15  # Average

        return sire_first_crop_wins / sire_first_crop_starters

    @staticmethod
    def distance_pedigree_rating(sire_avg_distance: float,
                                 dam_avg_distance: float,
                                 race_distance: float) -> float:
        """Rate horse's pedigree for specific distance
        Returns score 0-100, higher is better
        """
        avg_optimal = (sire_avg_distance + dam_avg_distance) / 2
        distance_diff = abs(race_distance - avg_optimal)

        # Perfect match = 100, each furlong difference reduces score
        score = 100 - (distance_diff * 10)
        return max(0, min(100, score))


class BreedingPatterns:
    """Identify successful breeding patterns and nick crosses"""

    # Famous successful sire/broodmare sire combinations
    NICK_CROSSES = {
        ("Mr. Prospector", "Buckpasser"): 1.25,
        ("Northern Dancer", "Princequillo"): 1.30,
        ("Storm Cat", "Forty Niner"): 1.20,
        ("A.P. Indy", "Seattle Slew"): 1.15,
        ("Tapit", "Smart Strike"): 1.35,
        ("Into Mischief", "Unbridled"): 1.40,
    }

    @staticmethod
    def nick_multiplier(sire: str, broodmare_sire: str) -> float:
        """Get multiplier for known successful nick crosses"""
        return BreedingPatterns.NICK_CROSSES.get((sire, broodmare_sire), 1.0)

    @staticmethod
    def female_family_strength(stakes_winners: int, graded_winners: int,
                              total_foals: int) -> float:
        """Evaluate strength of female family
        Returns 0-100 score
        """
        if total_foals == 0:
            return 50  # Unknown

        sw_rate = (stakes_winners / total_foals) * 100
        gr_rate = (graded_winners / total_foals) * 100

        # Weighted score favoring graded stakes winners
        score = (sw_rate * 1.0) + (gr_rate * 2.0)
        return min(100, score * 10)

    @staticmethod
    def chef_de_race_count(pedigree_sires: List[str]) -> Dict[str, int]:
        """Count chef de race classifications in pedigree"""
        counts = {
            "brilliant": 0,
            "intermediate": 0,
            "classic": 0,
            "solid": 0,
            "professional": 0
        }

        for sire in pedigree_sires:
            if sire in PedigreeAnalyzer.BRILLIANT:
                counts["brilliant"] += 1
            elif sire in PedigreeAnalyzer.INTERMEDIATE:
                counts["intermediate"] += 1
            elif sire in PedigreeAnalyzer.CLASSIC:
                counts["classic"] += 1
            elif sire in PedigreeAnalyzer.SOLID:
                counts["solid"] += 1
            elif sire in PedigreeAnalyzer.PROFESSIONAL:
                counts["professional"] += 1

        return counts

    @staticmethod
    def workout_indicator(sire_2yo_starts: int, total_2yo_foals: int) -> str:
        """Predict early maturity based on sire's 2YO record"""
        if total_2yo_foals == 0:
            return "unknown"

        early_rate = sire_2yo_starts / total_2yo_foals

        if early_rate > 0.65:
            return "precocious"
        elif early_rate > 0.40:
            return "average"
        else:
            return "late_developer"


# Export functions for TrackScript interpreter
def get_breeding_functions():
    """Return dictionary of breeding functions for interpreter"""
    pedigree = PedigreeAnalyzer()
    patterns = BreedingPatterns()

    return {
        'dosage_index': pedigree.dosage_index,
        'center_of_distribution': pedigree.center_of_distribution,
        'optimal_distance': pedigree.optimal_distance,
        'inbreeding_coefficient': pedigree.inbreeding_coefficient,
        'surface_affinity': pedigree.surface_affinity,
        'maiden_breaker_score': pedigree.maiden_breaker_score,
        'distance_pedigree_rating': pedigree.distance_pedigree_rating,
        'nick_multiplier': patterns.nick_multiplier,
        'female_family_strength': patterns.female_family_strength,
        'chef_de_race_count': patterns.chef_de_race_count,
        'workout_indicator': patterns.workout_indicator,
    }
