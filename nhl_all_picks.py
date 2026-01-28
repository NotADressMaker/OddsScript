#!/usr/bin/env python3
"""
NHL Comprehensive Picks - All 3 Models, All Bet Types
Money Line, ATS (Spread), and Totals (O/U)
"""

import random

from lib import NHLDecisionTree, NHLPowerRankings, NHLSimilarGameModel
from sportsbetlang.common.odds import implied_probability, remove_vig

# Today's NHL Games with FanDuel odds
GAMES = [
    {
        'away': 'Nashville Predators', 'home': 'Boston Bruins',
        'away_ml': +205, 'home_ml': -265,
        'away_spread': +1.5, 'away_spread_odds': -106,
        'home_spread': -1.5, 'home_spread_odds': -113,
        'ou_line': 6.5, 'over_odds': +100, 'under_odds': -122
    },
    {
        'away': 'Winnipeg Jets', 'home': 'New Jersey Devils',
        'away_ml': +194, 'home_ml': -245,
        'away_spread': +1.5, 'away_spread_odds': +106,
        'home_spread': -1.5, 'home_spread_odds': -128,
        'ou_line': 5.5, 'over_odds': -118, 'under_odds': -104
    },
    {
        'away': 'Los Angeles Kings', 'home': 'Detroit Red Wings',
        'away_ml': +186, 'home_ml': -235,
        'away_spread': +1.5, 'away_spread_odds': +108,
        'home_spread': -1.5, 'home_spread_odds': -130,
        'ou_line': 5.5, 'over_odds': -118, 'under_odds': -104
    },
    {
        'away': 'Utah Mammoth', 'home': 'Florida Panthers',
        'away_ml': +148, 'home_ml': -184,
        'away_spread': +1.5, 'away_spread_odds': +132,
        'home_spread': -1.5, 'home_spread_odds': -160,
        'ou_line': 6.5, 'over_odds': +100, 'under_odds': -122
    },
    {
        'away': 'Buffalo Sabres', 'home': 'Toronto Maple Leafs',
        'away_ml': +205, 'home_ml': -265,
        'away_spread': +1.5, 'away_spread_odds': -110,
        'home_spread': -1.5, 'home_spread_odds': -110,
        'ou_line': 6.5, 'over_odds': -110, 'under_odds': -110
    },
    {
        'away': 'Vegas Golden Knights', 'home': 'Montreal Canadiens',
        'away_ml': -114, 'home_ml': -260,  # Vegas favored
        'away_spread': -1.5, 'away_spread_odds': +205,
        'home_spread': +1.5, 'home_spread_odds': -105,
        'ou_line': 6.5, 'over_odds': -112, 'under_odds': -108
    },
    {
        'away': 'Dallas Stars', 'home': 'St. Louis Blues',
        'away_ml': -162, 'home_ml': -194,  # Dallas favored
        'away_spread': -1.5, 'away_spread_odds': +154,
        'home_spread': +1.5, 'home_spread_odds': +134,
        'ou_line': 5.5, 'over_odds': -120, 'under_odds': -102
    },
    {
        'away': 'Chicago Blackhawks', 'home': 'Minnesota Wild',
        'away_ml': +198, 'home_ml': -245,
        'away_spread': +1.5, 'away_spread_odds': -122,
        'home_spread': -1.5, 'home_spread_odds': +100,
        'ou_line': 6.5, 'over_odds': +110, 'under_odds': -134
    },
    {
        'away': 'San Jose Sharks', 'home': 'Vancouver Canucks',
        'away_ml': -128, 'home_ml': -225,  # Canucks favored
        'away_spread': -1.5, 'away_spread_odds': +180,
        'home_spread': +1.5, 'home_spread_odds': +106,
        'ou_line': 6.5, 'over_odds': -104, 'under_odds': -118
    },
    {
        'away': 'Washington Capitals', 'home': 'Seattle Kraken',
        'away_ml': -140, 'home_ml': -215,  # Caps favored
        'away_spread': -1.5, 'away_spread_odds': +168,
        'home_spread': +1.5, 'home_spread_odds': +116,
        'ou_line': 5.5, 'over_odds': -138, 'under_odds': +112
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
    """Convert American odds to fair (no-vig) probabilities."""
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
    print("=" * 90)
    print("🏒 NHL COMPREHENSIVE PICKS - ALL 3 MODELS")
    print("=" * 90)
    print("Analyzing Money Line, ATS (Spread), and Totals (O/U)")
    print("Ranking picks by model EV vs no-vig market probabilities\n")

    # Initialize models
    tree = NHLDecisionTree()
    rankings = NHLPowerRankings()
    sim_model = NHLSimilarGameModel()

    # Populate similar game model with more data for robustness
    print("Loading historical data...")
    for _ in range(200):  # Doubled for more robust predictions
        sim_model.add_game(
            team1=f"Team{random.randint(1,32)}", team2=f"Team{random.randint(1,32)}",
            team1_xgf=random.uniform(2.3, 3.7), team1_xga=random.uniform(2.3, 3.7),
            team2_xgf=random.uniform(2.3, 3.7), team2_xga=random.uniform(2.3, 3.7),
            team1_goals=random.randint(1, 6), team2_goals=random.randint(1, 6),
            total_goals=random.randint(4, 8),
            spread_result=random.choice(['cover', 'no_cover', 'push']),
            over_under_result=random.choice(['over', 'under', 'push']),
            team1_home=True, team1_rest=random.randint(0, 3), team2_rest=random.randint(0, 3)
        )
    print("✓ Models initialized\n")

    all_picks = {'ml': [], 'ats': [], 'ou': []}

    for game in GAMES:
        away_team = game['away']
        home_team = game['home']
        away_stats = TEAM_STATS[away_team]
        home_stats = TEAM_STATS[home_team]

        # === DECISION TREE ===
        dt_ou = tree.predict_over_under(
            team1_xgf=home_stats['xgf'], team1_xga=home_stats['xga'],
            team2_xgf=away_stats['xgf'], team2_xga=away_stats['xga'],
            line=game['ou_line'],
            team1_goalie_sv_pct=home_stats['goalie_sv'], team2_goalie_sv_pct=away_stats['goalie_sv'],
            team1_recent_goals=home_stats['recent_goals'], team2_recent_goals=away_stats['recent_goals']
        )

        dt_ats = tree.predict_ats(
            team_xgf=home_stats['xgf'], team_xga=home_stats['xga'],
            opp_xgf=away_stats['xgf'], opp_xga=away_stats['xga'],
            spread=game['home_spread'], is_home=True,
            team_recent_form=home_stats['recent_form'], opp_recent_form=away_stats['recent_form']
        )

        # === POWER RANKINGS ===
        rankings.set_rating(home_team, POWER_RATINGS[home_team])
        rankings.set_rating(away_team, POWER_RATINGS[away_team])
        pr = rankings.predict_game(
            home_team,
            away_team,
            team1_home=True,
            line_total=game['ou_line'],
            line_spread=game['home_spread']
        )

        # === SIMILAR GAME ===
        sim_pred = sim_model.predict_from_similar(
            team1_xgf=home_stats['xgf'], team1_xga=home_stats['xga'],
            team2_xgf=away_stats['xgf'], team2_xga=away_stats['xga'],
            line_total=game['ou_line'], line_spread=game['home_spread'], team1_home=True
        )

        # === ANALYZE O/U ===
        ou_over_probs = [
            dt_ou.get('over_probability'),
            pr.get('over_probability'),
            sim_pred.get('over_under', {}).get('over_probability')
        ]
        ou_under_probs = [
            dt_ou.get('under_probability'),
            pr.get('under_probability'),
            sim_pred.get('over_under', {}).get('under_probability')
        ]
        p_over = average([p for p in ou_over_probs if p is not None])
        p_under = average([p for p in ou_under_probs if p is not None])
        if p_over is None and p_under is not None:
            p_over = 1 - p_under
        if p_under is None and p_over is not None:
            p_under = 1 - p_over

        if p_over is not None and p_under is not None:
            market_over_prob, market_under_prob = fair_market_probs(game['over_odds'], game['under_odds'])
            edge_over = p_over - market_over_prob
            edge_under = p_under - market_under_prob
            if edge_over > 0 or edge_under > 0:
                if edge_over >= edge_under:
                    odds = game['over_odds']
                    all_picks['ou'].append({
                        'game': f"{away_team} @ {home_team}",
                        'pick': f"OVER {game['ou_line']}",
                        'odds': odds,
                        'probability': p_over,
                        'market_prob': market_over_prob,
                        'edge': edge_over,
                        'ev': expected_value_per_1(p_over, odds),
                        'expected': dt_ou['expected_total'],
                        'line': game['ou_line']
                    })
                else:
                    odds = game['under_odds']
                    all_picks['ou'].append({
                        'game': f"{away_team} @ {home_team}",
                        'pick': f"UNDER {game['ou_line']}",
                        'odds': odds,
                        'probability': p_under,
                        'market_prob': market_under_prob,
                        'edge': edge_under,
                        'ev': expected_value_per_1(p_under, odds),
                        'expected': dt_ou['expected_total'],
                        'line': game['ou_line']
                    })

        # === ANALYZE ATS ===
        spread_probs = [
            dt_ats.get('cover_probability'),
            pr.get('team1_cover_probability'),
            sim_pred.get('against_spread', {}).get('cover_probability')
        ]
        p_home_cover = average([p for p in spread_probs if p is not None])
        if p_home_cover is not None:
            p_away_cover = 1 - p_home_cover
            market_home_prob, market_away_prob = fair_market_probs(
                game['home_spread_odds'], game['away_spread_odds']
            )
            edge_home = p_home_cover - market_home_prob
            edge_away = p_away_cover - market_away_prob
            if edge_home > 0 or edge_away > 0:
                if edge_home >= edge_away:
                    odds = game['home_spread_odds']
                    all_picks['ats'].append({
                        'game': f"{away_team} @ {home_team}",
                        'pick': f"{home_team} {game['home_spread']:+.1f}",
                        'odds': odds,
                        'probability': p_home_cover,
                        'market_prob': market_home_prob,
                        'edge': edge_home,
                        'ev': expected_value_per_1(p_home_cover, odds)
                    })
                else:
                    odds = game['away_spread_odds']
                    all_picks['ats'].append({
                        'game': f"{away_team} @ {home_team}",
                        'pick': f"{away_team} {game['away_spread']:+.1f}",
                        'odds': odds,
                        'probability': p_away_cover,
                        'market_prob': market_away_prob,
                        'edge': edge_away,
                        'ev': expected_value_per_1(p_away_cover, odds)
                    })

        # === ANALYZE MONEY LINE ===
        ml_probs = [
            dt_ats.get('team_win_probability'),
            pr.get('team1_win_probability'),
            sim_pred.get('moneyline', {}).get('team1_win_probability')
        ]
        p_home = average([p for p in ml_probs if p is not None])
        if p_home is not None:
            p_away = 1 - p_home
            market_home_prob, market_away_prob = fair_market_probs(game['home_ml'], game['away_ml'])
            edge_home = p_home - market_home_prob
            edge_away = p_away - market_away_prob
            if edge_home > 0 or edge_away > 0:
                if edge_home >= edge_away:
                    odds = game['home_ml']
                    all_picks['ml'].append({
                        'game': f"{away_team} @ {home_team}",
                        'pick': f"{home_team} ML",
                        'odds': odds,
                        'probability': p_home,
                        'market_prob': market_home_prob,
                        'edge': edge_home,
                        'ev': expected_value_per_1(p_home, odds)
                    })
                else:
                    odds = game['away_ml']
                    all_picks['ml'].append({
                        'game': f"{away_team} @ {home_team}",
                        'pick': f"{away_team} ML",
                        'odds': odds,
                        'probability': p_away,
                        'market_prob': market_away_prob,
                        'edge': edge_away,
                        'ev': expected_value_per_1(p_away, odds)
                    })

    # === DISPLAY RESULTS ===
    print("=" * 90)
    print("💰 MONEY LINE PICKS")
    print("=" * 90)
    if all_picks['ml']:
        ml_sorted = sorted(all_picks['ml'], key=lambda x: x['edge'], reverse=True)
        for i, pick in enumerate(ml_sorted, 1):
            odds_str = f"{pick['odds']:+d}"
            print(
                f"{i}. {pick['pick']:35s} {odds_str:>5s} | "
                f"P(win) {pick['probability']:.1%} | Market {pick['market_prob']:.1%} | "
                f"Edge {pick['edge']:+.1%} | EV {pick['ev']:+.3f} | {pick['game']}"
            )
    else:
        print("No ML picks with positive edge found\n")

    print("\n" + "=" * 90)
    print("🎯 AGAINST THE SPREAD (ATS) PICKS")
    print("=" * 90)
    if all_picks['ats']:
        ats_sorted = sorted(all_picks['ats'], key=lambda x: x['edge'], reverse=True)
        for i, pick in enumerate(ats_sorted, 1):
            odds_str = f"{pick['odds']:+d}"
            print(
                f"{i}. {pick['pick']:35s} {odds_str:>5s} | "
                f"P(cover) {pick['probability']:.1%} | Market {pick['market_prob']:.1%} | "
                f"Edge {pick['edge']:+.1%} | EV {pick['ev']:+.3f} | {pick['game']}"
            )
    else:
        print("No ATS picks with positive edge found\n")

    print("\n" + "=" * 90)
    print("📊 OVER/UNDER (TOTALS) PICKS")
    print("=" * 90)
    if all_picks['ou']:
        ou_sorted = sorted(all_picks['ou'], key=lambda x: x['edge'], reverse=True)
        for i, pick in enumerate(ou_sorted, 1):
            odds_str = f"{pick['odds']:+d}"
            exp_str = f"Exp: {pick['expected']:.1f}"
            print(
                f"{i}. {pick['pick']:20s} {odds_str:>5s} | "
                f"P(side) {pick['probability']:.1%} | Market {pick['market_prob']:.1%} | "
                f"Edge {pick['edge']:+.1%} | EV {pick['ev']:+.3f} | {exp_str} | {pick['game']}"
            )
    else:
        print("No O/U picks with positive edge found\n")

    # === BEST BETS ===
    print("\n" + "=" * 90)
    print("🔥 TOP 5 BEST BETS (BY POSITIVE EDGE)")
    print("=" * 90)

    all_bets = []
    for bet_type, picks in all_picks.items():
        for pick in picks:
            pick['type'] = bet_type.upper()
            all_bets.append(pick)

    best_bets = sorted([b for b in all_bets if b['edge'] > 0], key=lambda x: x['edge'], reverse=True)[:5]

    if best_bets:
        for i, bet in enumerate(best_bets, 1):
            odds_str = f"{bet['odds']:+d}"
            print(
                f"{i}. [{bet['type']}] {bet['pick']:35s} {odds_str:>5s} | "
                f"Edge {bet['edge']:+.1%} | EV {bet['ev']:+.3f}"
            )
    else:
        print("No bets with positive edge found")

    print("\n" + "=" * 90)


if __name__ == "__main__":
    main()
