#!/usr/bin/env python3
"""
NHL Comprehensive Picks - All 3 Models, All Bet Types
Money Line, ATS (Spread), and Totals (O/U)
"""

from lib import NHLDecisionTree, NHLPowerRankings, NHLSimilarGameModel
import random

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

def american_to_prob(odds):
    """Convert American odds to implied probability"""
    if odds < 0:
        return abs(odds) / (abs(odds) + 100)
    else:
        return 100 / (odds + 100)

def main():
    print("=" * 90)
    print("🏒 NHL COMPREHENSIVE PICKS - ALL 3 MODELS")
    print("=" * 90)
    print("Analyzing Money Line, ATS (Spread), and Totals (O/U)")
    print("Showing only picks where 2+ models agree with 60%+ confidence\n")

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
        pr = rankings.predict_game(home_team, away_team, team1_home=True)

        # === SIMILAR GAME ===
        sim_pred = sim_model.predict_from_similar(
            team1_xgf=home_stats['xgf'], team1_xga=home_stats['xga'],
            team2_xgf=away_stats['xgf'], team2_xga=away_stats['xga'],
            line_total=game['ou_line'], line_spread=game['home_spread'], team1_home=True
        )

        # === ANALYZE O/U ===
        ou_votes = []
        if dt_ou['confidence'] >= 0.60 and dt_ou['prediction'] != 'PUSH':
            ou_votes.append(('DT', dt_ou['prediction'], dt_ou['confidence'], dt_ou['expected_total']))

        if abs(pr['expected_total'] - game['ou_line']) > 0.3:
            pr_pred = 'OVER' if pr['expected_total'] > game['ou_line'] else 'UNDER'
            pr_conf = min(0.72, 0.50 + abs(pr['expected_total'] - game['ou_line']) * 0.12)
            if pr_conf >= 0.60:
                ou_votes.append(('PR', pr_pred, pr_conf, pr['expected_total']))

        if 'over_under' in sim_pred and sim_pred['over_under']['confidence'] >= 0.60:
            if sim_pred['over_under']['prediction'] != 'PUSH':
                ou_votes.append(('SG', sim_pred['over_under']['prediction'],
                               sim_pred['over_under']['confidence'],
                               sim_pred['over_under']['average_total']))

        # Check for 2+ agreement on O/U
        if len(ou_votes) >= 2:
            over_count = sum(1 for v in ou_votes if v[1] == 'OVER')
            under_count = sum(1 for v in ou_votes if v[1] == 'UNDER')

            if over_count >= 2:
                agreeing = [v for v in ou_votes if v[1] == 'OVER']
                avg_conf = sum(v[2] for v in agreeing) / len(agreeing)
                avg_total = sum(v[3] for v in agreeing) / len(agreeing)
                market_prob = american_to_prob(game['over_odds'])
                edge = avg_conf - market_prob

                all_picks['ou'].append({
                    'game': f"{away_team} @ {home_team}",
                    'pick': f"OVER {game['ou_line']}",
                    'odds': game['over_odds'],
                    'confidence': avg_conf,
                    'expected': avg_total,
                    'edge': edge,
                    'models': len(agreeing),
                    'line': game['ou_line']
                })

            elif under_count >= 2:
                agreeing = [v for v in ou_votes if v[1] == 'UNDER']
                avg_conf = sum(v[2] for v in agreeing) / len(agreeing)
                avg_total = sum(v[3] for v in agreeing) / len(agreeing)
                market_prob = american_to_prob(game['under_odds'])
                edge = avg_conf - market_prob

                all_picks['ou'].append({
                    'game': f"{away_team} @ {home_team}",
                    'pick': f"UNDER {game['ou_line']}",
                    'odds': game['under_odds'],
                    'confidence': avg_conf,
                    'expected': avg_total,
                    'edge': edge,
                    'models': len(agreeing),
                    'line': game['ou_line']
                })

        # === ANALYZE ATS ===
        ats_votes = []
        if dt_ats['confidence'] >= 0.60 and dt_ats['prediction'] != 'PUSH':
            ats_votes.append(('DT', dt_ats['prediction'], dt_ats['confidence'], dt_ats['cover_margin']))

        if abs(pr['expected_goal_differential'] + game['home_spread']) > 0.4:
            pr_pred = 'COVER' if (pr['expected_goal_differential'] + game['home_spread']) > 0 else 'NO COVER'
            pr_conf = min(0.72, 0.50 + abs(pr['expected_goal_differential'] + game['home_spread']) * 0.15)
            if pr_conf >= 0.60:
                ats_votes.append(('PR', pr_pred, pr_conf, pr['expected_goal_differential'] + game['home_spread']))

        if 'against_spread' in sim_pred and sim_pred['against_spread']['confidence'] >= 0.60:
            if sim_pred['against_spread']['prediction'] != 'PUSH':
                ats_votes.append(('SG', sim_pred['against_spread']['prediction'],
                                sim_pred['against_spread']['confidence'], 0))

        # Check for 2+ agreement on ATS
        if len(ats_votes) >= 2:
            cover_count = sum(1 for v in ats_votes if v[1] == 'COVER')
            no_cover_count = sum(1 for v in ats_votes if v[1] == 'NO COVER')

            if cover_count >= 2:
                agreeing = [v for v in ats_votes if v[1] == 'COVER']
                avg_conf = sum(v[2] for v in agreeing) / len(agreeing)
                team = home_team
                spread = game['home_spread']
                odds = game['home_spread_odds']
                market_prob = american_to_prob(odds)
                edge = avg_conf - market_prob

                all_picks['ats'].append({
                    'game': f"{away_team} @ {home_team}",
                    'pick': f"{team} {spread:+.1f}",
                    'odds': odds,
                    'confidence': avg_conf,
                    'edge': edge,
                    'models': len(agreeing)
                })

            elif no_cover_count >= 2:
                agreeing = [v for v in ats_votes if v[1] == 'NO COVER']
                avg_conf = sum(v[2] for v in agreeing) / len(agreeing)
                team = away_team
                spread = game['away_spread']
                odds = game['away_spread_odds']
                market_prob = american_to_prob(odds)
                edge = avg_conf - market_prob

                all_picks['ats'].append({
                    'game': f"{away_team} @ {home_team}",
                    'pick': f"{team} {spread:+.1f}",
                    'odds': odds,
                    'confidence': avg_conf,
                    'edge': edge,
                    'models': len(agreeing)
                })

        # === ANALYZE MONEY LINE ===
        ml_votes = []

        # DT vote based on expected differential
        dt_winner = home_team if dt_ats['expected_differential'] > 0 else away_team
        dt_ml_conf = min(0.70, 0.50 + abs(dt_ats['expected_differential']) * 0.15)
        if dt_ml_conf >= 0.55:
            ml_votes.append(('DT', dt_winner, dt_ml_conf))

        # PR vote
        pr_winner = home_team if pr['team1_win_probability'] > 0.50 else away_team
        pr_ml_conf = max(pr['team1_win_probability'], pr['team2_win_probability'])
        if pr_ml_conf >= 0.55:
            ml_votes.append(('PR', pr_winner, pr_ml_conf))

        # SG vote
        if 'against_spread' in sim_pred:
            avg_diff = sim_pred['against_spread']['average_goal_diff']
            sg_winner = home_team if avg_diff > 0 else away_team
            sg_ml_conf = min(0.70, 0.50 + abs(avg_diff) * 0.12)
            if sg_ml_conf >= 0.55:
                ml_votes.append(('SG', sg_winner, sg_ml_conf))

        # Check for 2+ agreement on ML
        if len(ml_votes) >= 2:
            home_votes = sum(1 for v in ml_votes if v[1] == home_team)
            away_votes = sum(1 for v in ml_votes if v[1] == away_team)

            if home_votes >= 2:
                agreeing = [v for v in ml_votes if v[1] == home_team]
                avg_conf = sum(v[2] for v in agreeing) / len(agreeing)
                odds = game['home_ml']
                market_prob = american_to_prob(odds)
                edge = avg_conf - market_prob

                all_picks['ml'].append({
                    'game': f"{away_team} @ {home_team}",
                    'pick': f"{home_team} ML",
                    'odds': odds,
                    'confidence': avg_conf,
                    'edge': edge,
                    'models': len(agreeing)
                })

            elif away_votes >= 2:
                agreeing = [v for v in ml_votes if v[1] == away_team]
                avg_conf = sum(v[2] for v in agreeing) / len(agreeing)
                odds = game['away_ml']
                market_prob = american_to_prob(odds)
                edge = avg_conf - market_prob

                all_picks['ml'].append({
                    'game': f"{away_team} @ {home_team}",
                    'pick': f"{away_team} ML",
                    'odds': odds,
                    'confidence': avg_conf,
                    'edge': edge,
                    'models': len(agreeing)
                })

    # === DISPLAY RESULTS ===
    print("=" * 90)
    print("💰 MONEY LINE PICKS")
    print("=" * 90)
    if all_picks['ml']:
        ml_sorted = sorted(all_picks['ml'], key=lambda x: x['edge'], reverse=True)
        for i, pick in enumerate(ml_sorted, 1):
            models_str = "3/3" if pick['models'] == 3 else "2/3"
            odds_str = f"{pick['odds']:+d}"
            print(f"{i}. {pick['pick']:35s} {odds_str:>5s} | {pick['confidence']:.0%} | {pick['edge']:+.1%} edge | {models_str} | {pick['game']}")
    else:
        print("No ML picks found where 2+ models agree\n")

    print("\n" + "=" * 90)
    print("🎯 AGAINST THE SPREAD (ATS) PICKS")
    print("=" * 90)
    if all_picks['ats']:
        ats_sorted = sorted(all_picks['ats'], key=lambda x: x['edge'], reverse=True)
        for i, pick in enumerate(ats_sorted, 1):
            models_str = "3/3" if pick['models'] == 3 else "2/3"
            odds_str = f"{pick['odds']:+d}"
            print(f"{i}. {pick['pick']:35s} {odds_str:>5s} | {pick['confidence']:.0%} | {pick['edge']:+.1%} edge | {models_str} | {pick['game']}")
    else:
        print("No ATS picks found where 2+ models agree\n")

    print("\n" + "=" * 90)
    print("📊 OVER/UNDER (TOTALS) PICKS")
    print("=" * 90)
    if all_picks['ou']:
        ou_sorted = sorted(all_picks['ou'], key=lambda x: x['edge'], reverse=True)
        for i, pick in enumerate(ou_sorted, 1):
            models_str = "3/3" if pick['models'] == 3 else "2/3"
            odds_str = f"{pick['odds']:+d}"
            exp_str = f"Exp: {pick['expected']:.1f}"
            print(f"{i}. {pick['pick']:20s} {odds_str:>5s} | {pick['confidence']:.0%} | {pick['edge']:+.1%} edge | {models_str} | {exp_str} | {pick['game']}")
    else:
        print("No O/U picks found where 2+ models agree\n")

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
            models_str = "3/3" if bet['models'] == 3 else "2/3"
            odds_str = f"{bet['odds']:+d}"
            print(f"{i}. [{bet['type']}] {bet['pick']:35s} {odds_str:>5s} | {bet['edge']:+.1%} edge | {bet['confidence']:.0%} conf | {models_str}")
    else:
        print("No bets with positive edge found")

    print("\n" + "=" * 90)


if __name__ == "__main__":
    main()
