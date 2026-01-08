"""
TrackScript Race Simulation Package
Monte Carlo simulation and probability modeling for horse racing
"""

import random
import math
from typing import Dict, List, Tuple, Any


class RaceSimulator:
    """Monte Carlo simulation of horse races"""

    @staticmethod
    def simulate_race(horses: List[Dict[str, Any]], num_simulations: int = 10000) -> Dict[str, Any]:
        """Simulate a race many times to determine win probabilities
        horses: list of dicts with 'name' and 'true_prob' keys
        """
        results = {horse['name']: 0 for horse in horses}
        place_results = {horse['name']: 0 for horse in horses}
        show_results = {horse['name']: 0 for horse in horses}

        for _ in range(num_simulations):
            # Normalize probabilities
            total_prob = sum(h['true_prob'] for h in horses)
            normalized_probs = [h['true_prob'] / total_prob for h in horses]

            # Simulate race finish
            finish_order = []
            remaining_horses = horses.copy()
            remaining_probs = normalized_probs.copy()

            # Determine finish order
            for position in range(min(3, len(horses))):
                if not remaining_horses:
                    break

                # Re-normalize remaining probabilities
                total = sum(remaining_probs)
                if total <= 0:
                    break

                adjusted_probs = [p / total for p in remaining_probs]

                # Select winner based on probabilities
                winner_idx = random.choices(range(len(remaining_horses)),
                                           weights=adjusted_probs,
                                           k=1)[0]

                winner = remaining_horses[winner_idx]
                finish_order.append(winner['name'])

                # Remove winner from remaining
                remaining_horses.pop(winner_idx)
                remaining_probs.pop(winner_idx)

            # Record results
            if len(finish_order) > 0:
                results[finish_order[0]] += 1
            if len(finish_order) > 1:
                place_results[finish_order[0]] += 1
                place_results[finish_order[1]] += 1
            if len(finish_order) > 2:
                show_results[finish_order[0]] += 1
                show_results[finish_order[1]] += 1
                show_results[finish_order[2]] += 1

        # Calculate percentages
        win_pct = {name: (count / num_simulations) * 100
                   for name, count in results.items()}
        place_pct = {name: (count / num_simulations) * 100
                     for name, count in place_results.items()}
        show_pct = {name: (count / num_simulations) * 100
                    for name, count in show_results.items()}

        return {
            "win_probabilities": win_pct,
            "place_probabilities": place_pct,
            "show_probabilities": show_pct,
            "simulations_run": num_simulations
        }

    @staticmethod
    def simulate_exotic(exotic_type: str, horses: List[Dict[str, Any]],
                       num_simulations: int = 10000) -> Dict[str, float]:
        """Simulate exotic bet outcomes
        exotic_type: 'exacta', 'trifecta', or 'superfecta'
        """
        if exotic_type == "exacta":
            positions = 2
        elif exotic_type == "trifecta":
            positions = 3
        elif exotic_type == "superfecta":
            positions = 4
        else:
            return {}

        combinations = {}

        for _ in range(num_simulations):
            # Normalize probabilities
            total_prob = sum(h['true_prob'] for h in horses)
            normalized_probs = [h['true_prob'] / total_prob for h in horses]

            # Simulate finish order
            finish = []
            remaining_horses = horses.copy()
            remaining_probs = normalized_probs.copy()

            for _ in range(positions):
                if not remaining_horses:
                    break

                total = sum(remaining_probs)
                if total <= 0:
                    break

                adjusted_probs = [p / total for p in remaining_probs]
                winner_idx = random.choices(range(len(remaining_horses)),
                                           weights=adjusted_probs,
                                           k=1)[0]

                finish.append(remaining_horses[winner_idx]['name'])
                remaining_horses.pop(winner_idx)
                remaining_probs.pop(winner_idx)

            # Record combination
            if len(finish) == positions:
                combo = tuple(finish)
                combinations[combo] = combinations.get(combo, 0) + 1

        # Calculate probabilities
        probabilities = {combo: (count / num_simulations) * 100
                        for combo, count in combinations.items()}

        # Sort by probability
        sorted_combos = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)

        return {
            "top_combinations": dict(sorted_combos[:20]),  # Top 20 most likely
            "total_combinations": len(combinations),
            "simulations_run": num_simulations
        }

    @staticmethod
    def variance_calculation(win_prob: float, odds: float,
                            stake: float, num_bets: int) -> Dict[str, float]:
        """Calculate variance and bankroll requirements"""
        # Expected value per bet
        ev_per_bet = (win_prob * (odds * stake)) - ((1 - win_prob) * stake)

        # Variance per bet
        win_outcome = odds * stake - stake
        loss_outcome = -stake
        variance = (win_prob * (win_outcome - ev_per_bet) ** 2 +
                   (1 - win_prob) * (loss_outcome - ev_per_bet) ** 2)

        # Standard deviation
        std_dev = math.sqrt(variance)

        # Over multiple bets
        total_ev = ev_per_bet * num_bets
        total_std_dev = std_dev * math.sqrt(num_bets)

        # Risk of ruin (simplified approximation)
        if ev_per_bet <= 0:
            ror = 100.0
        else:
            ror = max(0, min(100, 50 - (ev_per_bet / std_dev) * 10))

        return {
            "ev_per_bet": ev_per_bet,
            "std_dev_per_bet": std_dev,
            "total_expected_profit": total_ev,
            "total_std_dev": total_std_dev,
            "risk_of_ruin_pct": ror,
            "recommended_bankroll": stake * num_bets * 3  # 3x Kelly for safety
        }


class ProbabilityModeler:
    """Advanced probability modeling"""

    @staticmethod
    def bayesian_update(prior_prob: float, likelihood: float,
                       evidence_strength: float = 1.0) -> float:
        """Update probability based on new information"""
        # Bayesian update with evidence strength weighting
        prior_odds = prior_prob / (1 - prior_prob) if prior_prob < 1 else 99

        # Likelihood ratio
        lr = likelihood ** evidence_strength

        # Posterior odds
        posterior_odds = prior_odds * lr

        # Convert back to probability
        posterior_prob = posterior_odds / (1 + posterior_odds)
        return min(0.99, max(0.01, posterior_prob))

    @staticmethod
    def confidence_interval(estimated_prob: float, sample_size: int,
                           confidence_level: float = 0.95) -> Tuple[float, float]:
        """Calculate confidence interval for probability estimate"""
        # Standard error
        se = math.sqrt((estimated_prob * (1 - estimated_prob)) / sample_size)

        # Z-score for confidence level (95% ≈ 1.96)
        z_score = 1.96 if confidence_level == 0.95 else 1.645

        # Margin of error
        margin = z_score * se

        lower = max(0.0, estimated_prob - margin)
        upper = min(1.0, estimated_prob + margin)

        return (lower, upper)

    @staticmethod
    def poisson_pace_model(early_pace_time: float, avg_early_pace: float,
                          std_dev: float) -> float:
        """Model probability distribution of pace scenarios"""
        # Z-score
        z = (early_pace_time - avg_early_pace) / std_dev if std_dev > 0 else 0

        # Probability (using normal approximation)
        # Fast pace = negative z, slow pace = positive z
        prob_faster = 0.5 - (0.5 * math.erf(z / math.sqrt(2)))

        return prob_faster

    @staticmethod
    def elo_rating_update(winner_rating: float, loser_rating: float,
                         k_factor: float = 32) -> Tuple[float, float]:
        """Update Elo ratings after race result"""
        # Expected scores
        winner_expected = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
        loser_expected = 1 - winner_expected

        # Actual scores (winner = 1, loser = 0)
        winner_actual = 1.0
        loser_actual = 0.0

        # New ratings
        new_winner_rating = winner_rating + k_factor * (winner_actual - winner_expected)
        new_loser_rating = loser_rating + k_factor * (loser_actual - loser_expected)

        return (new_winner_rating, new_loser_rating)

    @staticmethod
    def regression_to_mean(current_performance: float,
                          career_average: float,
                          races_back: int,
                          max_weight: float = 0.7) -> float:
        """Adjust for regression to the mean"""
        # Weight based on recency
        recency_weight = min(max_weight, races_back / 10)

        # Regressed estimate
        regressed = (current_performance * recency_weight +
                    career_average * (1 - recency_weight))

        return regressed


class MonteCarloStrategies:
    """Monte Carlo based betting strategies"""

    @staticmethod
    def optimal_bet_sizing(bankroll: float, win_prob: float, odds: float,
                          simulations: int = 10000, target_kelly: float = 0.25) -> Dict[str, Any]:
        """Simulate to find optimal bet size"""
        kelly = ((win_prob * odds - 1) / (odds - 1)) if odds > 1 else 0
        kelly_bet = bankroll * kelly * target_kelly

        # Simulate different bet sizes
        bet_sizes = [kelly_bet * mult for mult in [0.5, 0.75, 1.0, 1.25, 1.5]]
        results = {}

        for bet_size in bet_sizes:
            if bet_size <= 0 or bet_size > bankroll * 0.25:
                continue

            ending_bankrolls = []

            for _ in range(simulations):
                sim_bankroll = bankroll

                # Simulate 100 bets
                for _ in range(100):
                    if random.random() < win_prob:
                        sim_bankroll += bet_size * (odds - 1)
                    else:
                        sim_bankroll -= bet_size

                    if sim_bankroll <= 0:
                        sim_bankroll = 0
                        break

                ending_bankrolls.append(sim_bankroll)

            avg_ending = sum(ending_bankrolls) / len(ending_bankrolls)
            ruin_count = sum(1 for b in ending_bankrolls if b == 0)
            ruin_rate = (ruin_count / simulations) * 100

            results[bet_size] = {
                "avg_ending_bankroll": avg_ending,
                "ruin_rate": ruin_rate,
                "roi": ((avg_ending - bankroll) / bankroll) * 100
            }

        # Find optimal
        best_bet = max(results.items(), key=lambda x: x[1]['avg_ending_bankroll'])

        return {
            "optimal_bet_size": best_bet[0],
            "expected_ending_bankroll": best_bet[1]['avg_ending_bankroll'],
            "ruin_rate": best_bet[1]['ruin_rate'],
            "all_results": results
        }


def get_simulation_functions():
    """Return dictionary of simulation functions for interpreter"""
    sim = RaceSimulator()
    prob = ProbabilityModeler()
    mc = MonteCarloStrategies()

    return {
        # Race simulation
        'simulate_race': sim.simulate_race,
        'simulate_exotic': sim.simulate_exotic,
        'variance_calculation': sim.variance_calculation,

        # Probability modeling
        'bayesian_update': prob.bayesian_update,
        'confidence_interval': prob.confidence_interval,
        'poisson_pace_model': prob.poisson_pace_model,
        'elo_rating_update': prob.elo_rating_update,
        'regression_to_mean': prob.regression_to_mean,

        # Monte Carlo strategies
        'optimal_bet_sizing': mc.optimal_bet_sizing,
    }
