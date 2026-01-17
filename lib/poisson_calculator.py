"""
Poisson Distribution Calculator for Sports Betting

Use Poisson distribution to model goal/point scoring and calculate totals probabilities.
Particularly useful for soccer, hockey, and lower-scoring sports.
"""

import math
import random
from typing import Dict, List, Tuple, Optional


class PoissonCalculator:
    """Calculate probabilities using Poisson distribution"""

    @staticmethod
    def poisson_probability(k: int, lambda_param: float) -> float:
        """
        Calculate Poisson probability

        P(X = k) = (λ^k * e^(-λ)) / k!

        Args:
            k: Number of events (goals/points)
            lambda_param: Expected number of events

        Returns:
            Probability
        """
        return (lambda_param ** k) * math.exp(-lambda_param) / math.factorial(k)

    @staticmethod
    def poisson_cumulative(k: int, lambda_param: float) -> float:
        """
        Calculate cumulative Poisson probability P(X <= k)

        Args:
            k: Number of events
            lambda_param: Expected number of events

        Returns:
            Cumulative probability
        """
        return sum(
            PoissonCalculator.poisson_probability(i, lambda_param)
            for i in range(k + 1)
        )

    @staticmethod
    def calculate_match_probabilities(
        home_lambda: float,
        away_lambda: float,
        max_goals: int = 10
    ) -> Dict:
        """
        Calculate match outcome probabilities

        Args:
            home_lambda: Expected home team goals
            away_lambda: Expected away team goals
            max_goals: Maximum goals to consider

        Returns:
            Dictionary with probabilities
        """
        # Calculate probability matrix
        prob_matrix = []
        for home_goals in range(max_goals + 1):
            row = []
            for away_goals in range(max_goals + 1):
                prob_home = PoissonCalculator.poisson_probability(home_goals, home_lambda)
                prob_away = PoissonCalculator.poisson_probability(away_goals, away_lambda)
                prob_combined = prob_home * prob_away
                row.append(prob_combined)
            prob_matrix.append(row)

        # Calculate outcome probabilities
        home_win = sum(
            prob_matrix[h][a]
            for h in range(max_goals + 1)
            for a in range(h)
        )

        away_win = sum(
            prob_matrix[h][a]
            for h in range(max_goals + 1)
            for a in range(h + 1, max_goals + 1)
        )

        draw = sum(prob_matrix[i][i] for i in range(max_goals + 1))

        return {
            'home_win': home_win,
            'away_win': away_win,
            'draw': draw,
            'prob_matrix': prob_matrix
        }

    @staticmethod
    def calculate_total_probabilities(
        home_lambda: float,
        away_lambda: float,
        total_line: float,
        max_goals: int = 15
    ) -> Dict:
        """
        Calculate over/under probabilities for a total

        Args:
            home_lambda: Expected home team goals
            away_lambda: Expected away team goals
            total_line: Total line (e.g., 2.5, 3.5)
            max_goals: Maximum goals to consider

        Returns:
            Dictionary with over/under probabilities
        """
        # Calculate total goals distribution
        total_lambda = home_lambda + away_lambda

        # For independent Poisson processes, sum is also Poisson
        over_prob = 0
        under_prob = 0

        for total_goals in range(max_goals + 1):
            prob = PoissonCalculator.poisson_probability(total_goals, total_lambda)

            if total_goals > total_line:
                over_prob += prob
            elif total_goals < total_line:
                under_prob += prob
            # If total_goals == total_line (only possible if line is integer), it's a push

        return {
            'over_probability': over_prob,
            'under_probability': under_prob,
            'expected_total': total_lambda,
            'line': total_line
        }

    @staticmethod
    def calculate_correct_score_probabilities(
        home_lambda: float,
        away_lambda: float,
        max_score: int = 5
    ) -> List[Tuple[int, int, float]]:
        """
        Calculate probabilities for each correct score

        Args:
            home_lambda: Expected home goals
            away_lambda: Expected away goals
            max_score: Maximum score to consider

        Returns:
            List of (home_score, away_score, probability) tuples
        """
        scores = []

        for home_score in range(max_score + 1):
            for away_score in range(max_score + 1):
                prob_home = PoissonCalculator.poisson_probability(home_score, home_lambda)
                prob_away = PoissonCalculator.poisson_probability(away_score, away_lambda)
                prob_combined = prob_home * prob_away
                scores.append((home_score, away_score, prob_combined))

        # Sort by probability
        scores.sort(key=lambda x: x[2], reverse=True)

        return scores

    @staticmethod
    def calculate_btts_probability(
        home_lambda: float,
        away_lambda: float
    ) -> Dict:
        """
        Calculate Both Teams To Score (BTTS) probability

        Args:
            home_lambda: Expected home goals
            away_lambda: Expected away goals

        Returns:
            Dictionary with BTTS probabilities
        """
        # P(home scores >= 1)
        home_scores = 1 - PoissonCalculator.poisson_probability(0, home_lambda)

        # P(away scores >= 1)
        away_scores = 1 - PoissonCalculator.poisson_probability(0, away_lambda)

        # P(both score) = P(home >= 1) * P(away >= 1) (assuming independence)
        btts_yes = home_scores * away_scores

        # P(at least one doesn't score)
        btts_no = 1 - btts_yes

        return {
            'btts_yes': btts_yes,
            'btts_no': btts_no,
            'home_scores_prob': home_scores,
            'away_scores_prob': away_scores
        }

    @staticmethod
    def calculate_asian_handicap(
        home_lambda: float,
        away_lambda: float,
        handicap: float,
        max_goals: int = 10
    ) -> Dict:
        """
        Calculate Asian Handicap probabilities

        Args:
            home_lambda: Expected home goals
            away_lambda: Expected away goals
            handicap: Handicap for home team (e.g., -0.5, -1.0, -1.5)
            max_goals: Maximum goals

        Returns:
            Dictionary with win/lose/push probabilities
        """
        win_prob = 0
        lose_prob = 0
        push_prob = 0

        for home_goals in range(max_goals + 1):
            for away_goals in range(max_goals + 1):
                prob_home = PoissonCalculator.poisson_probability(home_goals, home_lambda)
                prob_away = PoissonCalculator.poisson_probability(away_goals, away_lambda)
                prob_combined = prob_home * prob_away

                # Home goals with handicap
                home_adjusted = home_goals + handicap

                if home_adjusted > away_goals:
                    win_prob += prob_combined
                elif home_adjusted < away_goals:
                    lose_prob += prob_combined
                else:
                    push_prob += prob_combined

        return {
            'win': win_prob,
            'lose': lose_prob,
            'push': push_prob,
            'handicap': handicap
        }

    @staticmethod
    def simulate_poisson_event(lambda_param: float, seed: Optional[int] = None) -> int:
        """
        Simulate a single Poisson-distributed random variable

        Uses inverse transform sampling with cumulative probabilities.

        Args:
            lambda_param: Expected number of events
            seed: Optional random seed for reproducibility

        Returns:
            Number of events (goals/points) simulated
        """
        if seed is not None:
            random.seed(seed)

        # For small lambda, use direct simulation
        if lambda_param < 30:
            # Knuth's algorithm for Poisson sampling
            L = math.exp(-lambda_param)
            k = 0
            p = 1.0

            while p > L:
                k += 1
                p *= random.random()

            return k - 1
        else:
            # For large lambda, use normal approximation
            # Poisson(lambda) ≈ Normal(lambda, lambda)
            return max(0, int(random.gauss(lambda_param, math.sqrt(lambda_param)) + 0.5))

    @staticmethod
    def simulate_match(
        home_lambda: float,
        away_lambda: float,
        seed: Optional[int] = None
    ) -> Dict:
        """
        Simulate a single match outcome using Poisson distribution

        Args:
            home_lambda: Expected home team goals/points
            away_lambda: Expected away team goals/points
            seed: Optional random seed for reproducibility

        Returns:
            Dictionary with match result
        """
        if seed is not None:
            random.seed(seed)

        home_score = PoissonCalculator.simulate_poisson_event(home_lambda)
        away_score = PoissonCalculator.simulate_poisson_event(away_lambda)

        if home_score > away_score:
            result = 'home_win'
        elif away_score > home_score:
            result = 'away_win'
        else:
            result = 'draw'

        return {
            'home_score': home_score,
            'away_score': away_score,
            'total_score': home_score + away_score,
            'result': result
        }

    @staticmethod
    def simulate_matches(
        home_lambda: float,
        away_lambda: float,
        num_simulations: int = 1000,
        seed: Optional[int] = None
    ) -> Dict:
        """
        Run Monte Carlo simulation of multiple matches

        Args:
            home_lambda: Expected home team goals/points
            away_lambda: Expected away team goals/points
            num_simulations: Number of matches to simulate
            seed: Optional random seed for reproducibility

        Returns:
            Dictionary with simulation statistics
        """
        if seed is not None:
            random.seed(seed)

        results = {
            'home_wins': 0,
            'away_wins': 0,
            'draws': 0,
            'scores': [],
            'total_scores': []
        }

        for _ in range(num_simulations):
            match = PoissonCalculator.simulate_match(home_lambda, away_lambda)

            if match['result'] == 'home_win':
                results['home_wins'] += 1
            elif match['result'] == 'away_win':
                results['away_wins'] += 1
            else:
                results['draws'] += 1

            results['scores'].append((match['home_score'], match['away_score']))
            results['total_scores'].append(match['total_score'])

        # Calculate statistics
        results['home_win_pct'] = results['home_wins'] / num_simulations
        results['away_win_pct'] = results['away_wins'] / num_simulations
        results['draw_pct'] = results['draws'] / num_simulations
        results['avg_total'] = sum(results['total_scores']) / num_simulations
        results['num_simulations'] = num_simulations

        return results

    @staticmethod
    def simulate_betting_strategy(
        home_lambda: float,
        away_lambda: float,
        bet_type: str,
        bet_target: any,
        odds: float,
        stake: float,
        num_simulations: int = 1000,
        seed: Optional[int] = None
    ) -> Dict:
        """
        Simulate a betting strategy over multiple matches

        Args:
            home_lambda: Expected home team goals/points
            away_lambda: Expected away team goals/points
            bet_type: Type of bet ('home_win', 'away_win', 'draw', 'over', 'under', 'btts')
            bet_target: Target value (e.g., total for over/under)
            odds: Decimal odds
            stake: Bet stake amount
            num_simulations: Number of matches to simulate
            seed: Optional random seed for reproducibility

        Returns:
            Dictionary with betting results and statistics
        """
        if seed is not None:
            random.seed(seed)

        wins = 0
        losses = 0
        total_profit = 0
        results_list = []

        for _ in range(num_simulations):
            match = PoissonCalculator.simulate_match(home_lambda, away_lambda)

            # Determine if bet wins
            bet_wins = False

            if bet_type == 'home_win':
                bet_wins = match['result'] == 'home_win'
            elif bet_type == 'away_win':
                bet_wins = match['result'] == 'away_win'
            elif bet_type == 'draw':
                bet_wins = match['result'] == 'draw'
            elif bet_type == 'over':
                bet_wins = match['total_score'] > bet_target
            elif bet_type == 'under':
                bet_wins = match['total_score'] < bet_target
            elif bet_type == 'btts':
                bet_wins = match['home_score'] > 0 and match['away_score'] > 0

            # Calculate profit/loss
            if bet_wins:
                profit = stake * (odds - 1)
                wins += 1
            else:
                profit = -stake
                losses += 1

            total_profit += profit
            results_list.append(profit)

        # Calculate statistics
        win_rate = wins / num_simulations
        avg_profit_per_bet = total_profit / num_simulations
        roi = (total_profit / (stake * num_simulations)) * 100

        # Calculate variance and standard deviation
        variance = sum((r - avg_profit_per_bet) ** 2 for r in results_list) / num_simulations
        std_dev = math.sqrt(variance)

        return {
            'num_simulations': num_simulations,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'avg_profit_per_bet': avg_profit_per_bet,
            'roi': roi,
            'std_dev': std_dev,
            'bet_type': bet_type,
            'odds': odds,
            'stake': stake
        }

    @staticmethod
    def simulate_season(
        teams: Dict[str, float],
        num_matches: int,
        home_advantage: float = 0.3,
        seed: Optional[int] = None
    ) -> Dict:
        """
        Simulate a season of matches between teams

        Args:
            teams: Dictionary of team names to their base lambda (scoring rate)
            num_matches: Number of matches to simulate
            home_advantage: Additional goals added to home team lambda
            seed: Optional random seed for reproducibility

        Returns:
            Dictionary with season results
        """
        if seed is not None:
            random.seed(seed)

        team_names = list(teams.keys())
        standings = {team: {'wins': 0, 'draws': 0, 'losses': 0, 'gf': 0, 'ga': 0, 'pts': 0}
                    for team in team_names}

        matches_played = []

        for _ in range(num_matches):
            # Randomly select two different teams
            home_team = random.choice(team_names)
            away_team = random.choice([t for t in team_names if t != home_team])

            # Get lambdas with home advantage
            home_lambda = teams[home_team] + home_advantage
            away_lambda = teams[away_team]

            # Simulate match
            match = PoissonCalculator.simulate_match(home_lambda, away_lambda)

            # Update standings
            standings[home_team]['gf'] += match['home_score']
            standings[home_team]['ga'] += match['away_score']
            standings[away_team]['gf'] += match['away_score']
            standings[away_team]['ga'] += match['home_score']

            if match['result'] == 'home_win':
                standings[home_team]['wins'] += 1
                standings[home_team]['pts'] += 3
                standings[away_team]['losses'] += 1
            elif match['result'] == 'away_win':
                standings[away_team]['wins'] += 1
                standings[away_team]['pts'] += 3
                standings[home_team]['losses'] += 1
            else:
                standings[home_team]['draws'] += 1
                standings[home_team]['pts'] += 1
                standings[away_team]['draws'] += 1
                standings[away_team]['pts'] += 1

            matches_played.append({
                'home': home_team,
                'away': away_team,
                'home_score': match['home_score'],
                'away_score': match['away_score'],
                'result': match['result']
            })

        # Sort standings by points
        sorted_standings = sorted(
            standings.items(),
            key=lambda x: (x[1]['pts'], x[1]['gf'] - x[1]['ga']),
            reverse=True
        )

        return {
            'standings': dict(sorted_standings),
            'matches': matches_played,
            'num_matches': num_matches
        }


def analyze_match(
    home_team: str,
    away_team: str,
    home_avg: float,
    away_avg: float,
    total_line: float = None,
    handicap: float = None
):
    """Comprehensive match analysis using Poisson"""
    calc = PoissonCalculator()

    print(f"\n{'='*70}")
    print(f"Poisson Distribution Analysis")
    print(f"{home_team} vs {away_team}")
    print(f"{'='*70}")

    print(f"\nExpected Goals:")
    print(f"  {home_team}: {home_avg:.2f}")
    print(f"  {away_team}: {away_avg:.2f}")
    print(f"  Total: {home_avg + away_avg:.2f}")

    # Match outcome probabilities
    outcomes = calc.calculate_match_probabilities(home_avg, away_avg)

    print(f"\nMatch Outcome Probabilities:")
    print(f"  {home_team} Win: {outcomes['home_win']*100:.2f}%")
    print(f"  Draw:           {outcomes['draw']*100:.2f}%")
    print(f"  {away_team} Win: {outcomes['away_win']*100:.2f}%")

    # Convert to odds
    if outcomes['home_win'] > 0:
        home_odds = (1 / outcomes['home_win']) - 1
        print(f"\nFair Odds (Decimal):")
        print(f"  {home_team}: {1/outcomes['home_win']:.2f}")
        print(f"  Draw:       {1/outcomes['draw']:.2f}")
        print(f"  {away_team}: {1/outcomes['away_win']:.2f}")

    # Total analysis
    if total_line:
        total_probs = calc.calculate_total_probabilities(home_avg, away_avg, total_line)

        print(f"\nTotal {total_line} Analysis:")
        print(f"  Over {total_line}:  {total_probs['over_probability']*100:.2f}%")
        print(f"  Under {total_line}: {total_probs['under_probability']*100:.2f}%")
        print(f"  Expected Total: {total_probs['expected_total']:.2f}")

        # Fair odds for total
        if total_probs['over_probability'] > 0:
            over_fair = 1 / total_probs['over_probability']
            under_fair = 1 / total_probs['under_probability']
            print(f"\n  Fair Odds - Over: {over_fair:.2f} | Under: {under_fair:.2f}")

    # BTTS
    btts = calc.calculate_btts_probability(home_avg, away_avg)

    print(f"\nBoth Teams To Score:")
    print(f"  Yes: {btts['btts_yes']*100:.2f}%")
    print(f"  No:  {btts['btts_no']*100:.2f}%")

    # Asian Handicap
    if handicap is not None:
        ah_probs = calc.calculate_asian_handicap(home_avg, away_avg, handicap)

        print(f"\nAsian Handicap {handicap:+.1f} ({home_team}):")
        print(f"  Win:  {ah_probs['win']*100:.2f}%")
        print(f"  Push: {ah_probs['push']*100:.2f}%")
        print(f"  Lose: {ah_probs['lose']*100:.2f}%")

    # Most likely scores
    scores = calc.calculate_correct_score_probabilities(home_avg, away_avg)

    print(f"\nMost Likely Correct Scores:")
    for i, (h, a, prob) in enumerate(scores[:10], 1):
        print(f"  {i:2d}. {h}-{a}: {prob*100:.2f}%")


def calculate_implied_totals(
    home_ml_odds: float,
    away_ml_odds: float,
    total_line: float,
    over_odds: float,
    under_odds: float
) -> Dict:
    """
    Derive implied team totals from market odds

    Args:
        home_ml_odds: Home moneyline odds (decimal)
        away_ml_odds: Away moneyline odds (decimal)
        total_line: Total line
        over_odds: Over odds (decimal)
        under_odds: Under odds (decimal)

    Returns:
        Dictionary with implied totals
    """
    # This is a simplified version
    # In reality, would need more sophisticated calculation

    # Rough estimate: split total based on win probabilities
    home_prob = 1 / home_ml_odds
    away_prob = 1 / away_ml_odds

    # Normalize
    total_prob = home_prob + away_prob
    home_weight = home_prob / total_prob
    away_weight = away_prob / total_prob

    # Implied total from over/under
    over_prob = 1 / over_odds
    under_prob = 1 / under_odds

    # Weight the total line
    implied_total = total_line

    # Split based on team strength
    home_implied = implied_total * home_weight
    away_implied = implied_total * away_weight

    return {
        'home_implied_total': home_implied,
        'away_implied_total': away_implied,
        'game_implied_total': home_implied + away_implied
    }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Poisson Calculator for Sports')
    parser.add_argument('home_team', help='Home team name')
    parser.add_argument('away_team', help='Away team name')
    parser.add_argument('home_avg', type=float, help='Home team avg goals/points')
    parser.add_argument('away_avg', type=float, help='Away team avg goals/points')
    parser.add_argument('-t', '--total', type=float, help='Total line to analyze')
    parser.add_argument('--handicap', type=float, help='Asian handicap to analyze')

    args = parser.parse_args()

    analyze_match(
        args.home_team,
        args.away_team,
        args.home_avg,
        args.away_avg,
        args.total,
        args.handicap
    )
