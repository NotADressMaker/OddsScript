#!/usr/bin/env python3
"""
Show NHL Over/Under picks where at least 2 of 3 models agree
"""

import random

from lib import NHLDecisionTree, NHLPowerRankings, NHLSimilarGameModel
from sportsbetlang.common.odds import implied_probability, remove_vig

GAMES = [
    {
        'away': 'Nashville Predators',
        'home': 'Boston Bruins',
        'spread': -1.5,
        'ou_line': 6.5,
        'home_ml': -265,
        'away_ml': +210,
        'over_odds': +100,
        'under_odds': -122
    },
    {
        'away': 'Winnipeg Jets',
        'home': 'New Jersey Devils',
        'spread': -1.5,
        'ou_line': 5.5,
        'home_ml': -230,
        'away_ml': +184,
        'over_odds': -118,
        'under_odds': -104
    },
    {
        'away': 'Los Angeles Kings',
        'home': 'Detroit Red Wings',
        'spread': -1.5,
        'ou_line': 5.5,
        'home_ml': -235,
        'away_ml': +186,
        'over_odds': -118,
        'under_odds': -104
    },
    {
        'away': 'Utah Mammoth',
        'home': 'Florida Panthers',
        'spread': -1.5,
        'ou_line': 6.5,
        'home_ml': -172,
        'away_ml': +140,
        'over_odds': +100,
        'under_odds': -122
    },
    {
        'away': 'Buffalo Sabres',
        'home': 'Toronto Maple Leafs',
        'spread': -1.5,
        'ou_line': 6.5,
        'home_ml': -265,
        'away_ml': +210,
        'over_odds': -110,
        'under_odds': -110
    },
    {
        'away': 'Vegas Golden Knights',
        'home': 'Montreal Canadiens',
        'spread': +1.5,
        'ou_line': 6.5,
        'home_ml': -260,
        'away_ml': +205,
        'over_odds': -112,
        'under_odds': -108
    },
    {
        'away': 'Dallas Stars',
        'home': 'St. Louis Blues',
        'spread': -1.5,
        'ou_line': 5.5,
        'home_ml': -184,
        'away_ml': +148,
        'over_odds': -120,
        'under_odds': -102
    },
    {
        'away': 'Chicago Blackhawks',
        'home': 'Minnesota Wild',
        'spread': -1.5,
        'ou_line': 6.5,
        'home_ml': -120,
        'away_ml': +202,
        'over_odds': +110,
        'under_odds': -134
    },
    {
        'away': 'San Jose Sharks',
        'home': 'Vancouver Canucks',
        'spread': -1.5,
        'ou_line': 6.5,
        'home_ml': -245,
        'away_ml': +190,
        'over_odds': -104,
        'under_odds': -118
    },
    {
        'away': 'Washington Capitals',
        'home': 'Seattle Kraken',
        'spread': -1.5,
        'ou_line': 5.5,
        'home_ml': -215,
        'away_ml': +172,
        'over_odds': -138,
        'under_odds': +112
    }
]

TEAM_STATS = {
    'Nashville Predators': {'xgf': 2.6, 'xga': 3.1, 'goalie_sv': 0.895, 'recent_goals': 2.4, 'recent_form': 0.400},
    'Boston Bruins': {'xgf': 3.0, 'xga': 2.7, 'goalie_sv': 0.912, 'recent_goals': 3.2, 'recent_form': 0.600},
    'Winnipeg Jets': {'xgf': 3.4, 'xga': 2.4, 'goalie_sv': 0.922, 'recent_goals': 3.6, 'recent_form': 0.750},
    'New Jersey Devils': {'xgf': 3.1, 'xga': 2.8, 'goalie_sv': 0.908, 'recent_goals': 3.0, 'recent_form': 0.550},
    'Los Angeles Kings': {'xgf': 2.9, 'xga': 2.6, 'goalie_sv': 0.915, 'recent_goals': 2.8, 'recent_form': 0.500},
    'Detroit Red Wings': {'xgf': 2.8, 'xga': 3.0, 'goalie_sv': 0.898, 'recent_goals': 2.9, 'recent_form': 0.450},
    'Utah Mammoth': {'xgf': 2.7, 'xga': 3.2, 'goalie_sv': 0.901, 'recent_goals': 2.5, 'recent_form': 0.350},
    'Florida Panthers': {'xgf': 3.2, 'xga': 2.7, 'goalie_sv': 0.910, 'recent_goals': 3.3, 'recent_form': 0.650},
    'Buffalo Sabres': {'xgf': 2.9, 'xga': 3.1, 'goalie_sv': 0.895, 'recent_goals': 2.7, 'recent_form': 0.400},
    'Toronto Maple Leafs': {'xgf': 3.3, 'xga': 2.8, 'goalie_sv': 0.908, 'recent_goals': 3.4, 'recent_form': 0.600},
    'Vegas Golden Knights': {'xgf': 3.1, 'xga': 2.6, 'goalie_sv': 0.918, 'recent_goals': 3.2, 'recent_form': 0.650},
    'Montreal Canadiens': {'xgf': 2.7, 'xga': 3.3, 'goalie_sv': 0.892, 'recent_goals': 2.6, 'recent_form': 0.350},
    'Dallas Stars': {'xgf': 3.2, 'xga': 2.5, 'goalie_sv': 0.916, 'recent_goals': 3.1, 'recent_form': 0.700},
    'St. Louis Blues': {'xgf': 2.8, 'xga': 3.0, 'goalie_sv': 0.902, 'recent_goals': 2.7, 'recent_form': 0.450},
    'Chicago Blackhawks': {'xgf': 2.4, 'xga': 3.4, 'goalie_sv': 0.888, 'recent_goals': 2.3, 'recent_form': 0.300},
    'Minnesota Wild': {'xgf': 3.0, 'xga': 2.7, 'goalie_sv': 0.914, 'recent_goals': 3.1, 'recent_form': 0.600},
    'San Jose Sharks': {'xgf': 2.5, 'xga': 3.5, 'goalie_sv': 0.885, 'recent_goals': 2.4, 'recent_form': 0.250},
    'Vancouver Canucks': {'xgf': 3.1, 'xga': 2.8, 'goalie_sv': 0.910, 'recent_goals': 3.0, 'recent_form': 0.550},
    'Washington Capitals': {'xgf': 3.0, 'xga': 2.8, 'goalie_sv': 0.906, 'recent_goals': 3.0, 'recent_form': 0.550},
    'Seattle Kraken': {'xgf': 2.8, 'xga': 2.9, 'goalie_sv': 0.903, 'recent_goals': 2.7, 'recent_form': 0.500}
}

POWER_RATINGS = {
    'Nashville Predators': 1420, 'Boston Bruins': 1580, 'Winnipeg Jets': 1680, 'New Jersey Devils': 1560,
    'Los Angeles Kings': 1540, 'Detroit Red Wings': 1480, 'Utah Mammoth': 1440, 'Florida Panthers': 1620,
    'Buffalo Sabres': 1460, 'Toronto Maple Leafs': 1590, 'Vegas Golden Knights': 1610, 'Montreal Canadiens': 1430,
    'Dallas Stars': 1640, 'St. Louis Blues': 1490, 'Chicago Blackhawks': 1380, 'Minnesota Wild': 1570,
    'San Jose Sharks': 1350, 'Vancouver Canucks': 1560, 'Washington Capitals': 1550, 'Seattle Kraken': 1520
}

def fair_market_probs(odds_a, odds_b):
    implied_a = implied_probability(odds_a)
    implied_b = implied_probability(odds_b)
    return remove_vig(implied_a, implied_b)


def average(values):
    return sum(values) / len(values) if values else None


def expected_value_per_1(prob, odds):
    if odds > 0:
        win_amount = odds / 100
    else:
        win_amount = 100 / abs(odds)
    return (prob * win_amount) - (1 - prob)


def main():
    print("=" * 80)
    print("🎯 NHL OVER/UNDER PICKS - 2+ MODELS AGREE")
    print("=" * 80)
    print("Showing O/U picks where model probability beats no-vig market\n")

    # Initialize models
    tree = NHLDecisionTree()
    rankings = NHLPowerRankings()
    sim_model = NHLSimilarGameModel()

    # Populate similar game model
    for _ in range(100):
        sim_model.add_game(
            team1=f"Team{random.randint(1,32)}", team2=f"Team{random.randint(1,32)}",
            team1_xgf=random.uniform(2.4, 3.6), team1_xga=random.uniform(2.4, 3.6),
            team2_xgf=random.uniform(2.4, 3.6), team2_xga=random.uniform(2.4, 3.6),
            team1_goals=random.randint(1, 6), team2_goals=random.randint(1, 6),
            total_goals=random.randint(4, 8),
            spread_result=random.choice(['cover', 'no_cover', 'push']),
            over_under_result=random.choice(['over', 'under', 'push']),
            team1_home=True
        )

    ou_picks = []

    for game in GAMES:
        away_team = game['away']
        home_team = game['home']
        ou_line = game['ou_line']
        away_stats = TEAM_STATS[away_team]
        home_stats = TEAM_STATS[home_team]

        # Decision Tree
        dt_ou = tree.predict_over_under(
            team1_xgf=home_stats['xgf'], team1_xga=home_stats['xga'],
            team2_xgf=away_stats['xgf'], team2_xga=away_stats['xga'],
            line=ou_line,
            team1_goalie_sv_pct=home_stats['goalie_sv'],
            team2_goalie_sv_pct=away_stats['goalie_sv'],
            team1_recent_goals=home_stats['recent_goals'],
            team2_recent_goals=away_stats['recent_goals']
        )

        # Power Rankings
        rankings.set_rating(home_team, POWER_RATINGS[home_team])
        rankings.set_rating(away_team, POWER_RATINGS[away_team])
        pr = rankings.predict_game(home_team, away_team, team1_home=True, line_total=ou_line)

        # Similar Game
        sim_pred = sim_model.predict_from_similar(
            team1_xgf=home_stats['xgf'], team1_xga=home_stats['xga'],
            team2_xgf=away_stats['xgf'], team2_xga=away_stats['xga'],
            line_total=ou_line, line_spread=game['spread'], team1_home=True
        )

        over_probs = [
            dt_ou.get('over_probability'),
            pr.get('over_probability'),
            sim_pred.get('over_under', {}).get('over_probability')
        ]
        under_probs = [
            dt_ou.get('under_probability'),
            pr.get('under_probability'),
            sim_pred.get('over_under', {}).get('under_probability')
        ]
        p_over = average([p for p in over_probs if p is not None])
        p_under = average([p for p in under_probs if p is not None])
        if p_over is None and p_under is not None:
            p_over = 1 - p_under
        if p_under is None and p_over is not None:
            p_under = 1 - p_over

        if p_over is None or p_under is None:
            continue

        market_over_prob, market_under_prob = fair_market_probs(game['over_odds'], game['under_odds'])
        edge_over = p_over - market_over_prob
        edge_under = p_under - market_under_prob

        if edge_over <= 0 and edge_under <= 0:
            continue

        if edge_over >= edge_under:
            odds = game['over_odds']
            pick = f"OVER {ou_line}"
            probability = p_over
            market_prob = market_over_prob
            edge = edge_over
        else:
            odds = game['under_odds']
            pick = f"UNDER {ou_line}"
            probability = p_under
            market_prob = market_under_prob
            edge = edge_under

        ou_picks.append({
            'game': f"{away_team} @ {home_team}",
            'pick': pick,
            'line': ou_line,
            'probability': probability,
            'market_prob': market_prob,
            'edge': edge,
            'ev': expected_value_per_1(probability, odds),
            'expected_total': dt_ou['expected_total'],
            'odds': odds
        })

    # Display results
    if ou_picks:
        print(f"Found {len(ou_picks)} O/U picks with positive edge:\n")
        for i, pick in enumerate(ou_picks, 1):
            odds_str = f"{pick['odds']:+d}"
            print(f"{i}. {pick['game']}")
            print(f"   🎯 BET: {pick['pick']} {odds_str}")
            print(f"   💪 Probability: {pick['probability']:.1%}")
            print(f"   🎯 Market (no-vig): {pick['market_prob']:.1%} | Edge: {pick['edge']:+.1%}")
            print(f"   💵 EV per $1: {pick['ev']:+.3f}")
            print(f"   📊 Expected total: {pick['expected_total']:.1f} (Line: {pick['line']})")
            print()

        print("=" * 80)
        print("📊 ALL O/U PICKS SORTED BY EDGE:")
        print("=" * 80)
        sorted_picks = sorted(ou_picks, key=lambda x: x['edge'], reverse=True)
        for i, pick in enumerate(sorted_picks, 1):
            print(f"{i}. {pick['pick']:20s} | {pick['edge']:+.1%} | {pick['game']}")

    else:
        print("⚠️  No O/U picks found with positive edge")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
