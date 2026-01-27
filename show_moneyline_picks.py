#!/usr/bin/env python3
"""
Show NHL Money Line picks where ALL 3 models agree on the winner
"""

from lib import NHLDecisionTree, NHLPowerRankings, NHLSimilarGameModel
import random

GAMES = [
    {'away': 'Nashville Predators', 'home': 'Boston Bruins', 'spread': -1.5, 'ou_line': 6.5, 'home_ml': -265, 'away_ml': +210},
    {'away': 'Winnipeg Jets', 'home': 'New Jersey Devils', 'spread': -1.5, 'ou_line': 5.5, 'home_ml': -230, 'away_ml': +184},
    {'away': 'Los Angeles Kings', 'home': 'Detroit Red Wings', 'spread': -1.5, 'ou_line': 5.5, 'home_ml': -235, 'away_ml': +186},
    {'away': 'Utah Mammoth', 'home': 'Florida Panthers', 'spread': -1.5, 'ou_line': 6.5, 'home_ml': -172, 'away_ml': +140},
    {'away': 'Buffalo Sabres', 'home': 'Toronto Maple Leafs', 'spread': -1.5, 'ou_line': 6.5, 'home_ml': -265, 'away_ml': +210},
    {'away': 'Vegas Golden Knights', 'home': 'Montreal Canadiens', 'spread': +1.5, 'ou_line': 6.5, 'home_ml': -260, 'away_ml': +205},
    {'away': 'Dallas Stars', 'home': 'St. Louis Blues', 'spread': -1.5, 'ou_line': 5.5, 'home_ml': -184, 'away_ml': +148},
    {'away': 'Chicago Blackhawks', 'home': 'Minnesota Wild', 'spread': -1.5, 'ou_line': 6.5, 'home_ml': -120, 'away_ml': +202},
    {'away': 'San Jose Sharks', 'home': 'Vancouver Canucks', 'spread': -1.5, 'ou_line': 6.5, 'home_ml': -245, 'away_ml': +190},
    {'away': 'Washington Capitals', 'home': 'Seattle Kraken', 'spread': -1.5, 'ou_line': 5.5, 'home_ml': -215, 'away_ml': +172}
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

def american_to_implied_prob(odds):
    """Convert American odds to implied probability"""
    if odds < 0:
        return abs(odds) / (abs(odds) + 100)
    else:
        return 100 / (odds + 100)

def main():
    print("=" * 80)
    print("💰 NHL MONEY LINE PICKS - ALL 3 MODELS AGREE")
    print("=" * 80)
    print("Showing ML picks where Decision Tree, Power Rankings, AND Similar Game")
    print("models all agree on the winner\n")

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

    ml_picks = []

    for game in GAMES:
        away_team = game['away']
        home_team = game['home']
        away_stats = TEAM_STATS[away_team]
        home_stats = TEAM_STATS[home_team]

        # Decision Tree - use ATS expected differential
        dt_ats = tree.predict_ats(
            team_xgf=home_stats['xgf'], team_xga=home_stats['xga'],
            opp_xgf=away_stats['xgf'], opp_xga=away_stats['xga'],
            spread=game['spread'], is_home=True,
            team_recent_form=home_stats['recent_form'],
            opp_recent_form=away_stats['recent_form']
        )

        # Decision Tree winner (based on expected differential)
        dt_winner = home_team if dt_ats['expected_differential'] > 0 else away_team
        dt_confidence = abs(dt_ats['expected_differential']) * 0.2 + 0.50  # Scale to 50-70%
        dt_confidence = min(0.70, max(0.50, dt_confidence))

        # Power Rankings
        rankings.set_rating(home_team, POWER_RATINGS[home_team])
        rankings.set_rating(away_team, POWER_RATINGS[away_team])
        pr = rankings.predict_game(home_team, away_team, team1_home=True)

        pr_winner = home_team if pr['team1_win_probability'] > 0.50 else away_team
        pr_confidence = max(pr['team1_win_probability'], pr['team2_win_probability'])

        # Similar Game
        sim_pred = sim_model.predict_from_similar(
            team1_xgf=home_stats['xgf'], team1_xga=home_stats['xga'],
            team2_xgf=away_stats['xgf'], team2_xga=away_stats['xga'],
            line_total=game['ou_line'], line_spread=game['spread'], team1_home=True
        )

        sg_winner = None
        sg_confidence = 0.50
        if 'against_spread' in sim_pred:
            avg_diff = sim_pred['against_spread']['average_goal_diff']
            sg_winner = home_team if avg_diff > 0 else away_team
            sg_confidence = min(0.70, 0.50 + abs(avg_diff) * 0.15)

        # Check if all 3 agree (with confidence threshold)
        votes = []
        if dt_confidence >= 0.52:  # Slight edge required
            votes.append((dt_winner, dt_confidence, 'Decision Tree', dt_ats['expected_differential']))
        if pr_confidence >= 0.52:
            votes.append((pr_winner, pr_confidence, 'Power Rankings', pr['expected_goal_differential']))
        if sg_winner and sg_confidence >= 0.52:
            votes.append((sg_winner, sg_confidence, 'Similar Games', sim_pred['against_spread']['average_goal_diff']))

        # Check if all 3 agree on the same winner
        if len(votes) == 3:
            winners = [v[0] for v in votes]
            if len(set(winners)) == 1:  # All agree on same winner
                winner = winners[0]
                avg_conf = sum(v[1] for v in votes) / 3
                avg_diff = sum(v[3] for v in votes) / 3

                # Get odds
                if winner == home_team:
                    odds = game['home_ml']
                    loser = away_team
                else:
                    odds = game['away_ml']
                    loser = home_team

                implied_prob = american_to_implied_prob(odds)
                edge = avg_conf - implied_prob

                ml_picks.append({
                    'game': f"{away_team} @ {home_team}",
                    'winner': winner,
                    'odds': odds,
                    'confidence': avg_conf,
                    'expected_diff': avg_diff,
                    'implied_prob': implied_prob,
                    'edge': edge,
                    'models': [v[2] for v in votes]
                })

    # Display results
    if ml_picks:
        print(f"Found {len(ml_picks)} unanimous Money Line picks:\n")

        for i, pick in enumerate(ml_picks, 1):
            odds_str = f"{pick['odds']:+d}"
            print(f"{i}. {pick['game']}")
            print(f"   💰 BET: {pick['winner']} ML {odds_str}")
            print(f"   ✅ All 3 models agree!")
            print(f"   💪 Win Probability: {pick['confidence']:.1%}")
            print(f"   📊 Expected Goal Diff: {pick['expected_diff']:+.2f}")
            print(f"   🎯 Market: {pick['implied_prob']:.1%} | Model: {pick['confidence']:.1%} | Edge: {pick['edge']:+.1%}")
            print(f"   🤖 {', '.join(pick['models'])}")
            print()

        print("=" * 80)
        print("💎 SORTED BY EDGE (Model Probability - Market Probability):")
        print("=" * 80)
        sorted_picks = sorted(ml_picks, key=lambda x: x['edge'], reverse=True)
        for i, pick in enumerate(sorted_picks, 1):
            odds_str = f"{pick['odds']:+d}"
            print(f"{i}. {pick['winner']:30s} {odds_str:>5s} | {pick['confidence']:.0%} win prob | {pick['edge']:+.1%} edge | {pick['game']}")

        print("\n" + "=" * 80)
        print("📋 BETTING STRATEGY:")
        print("=" * 80)

        positive_edge = [p for p in ml_picks if p['edge'] > 0]
        if positive_edge:
            print(f"✅ {len(positive_edge)} pick(s) with POSITIVE EDGE (model sees more value than market):\n")
            for pick in positive_edge:
                odds_str = f"{pick['odds']:+d}"
                print(f"   🔥 {pick['winner']} ML {odds_str} - {pick['edge']:+.1%} edge")
        else:
            print("⚠️  No picks with positive edge (all favorites are fairly priced)")

    else:
        print("⚠️  No unanimous Money Line picks found")
        print("(All 3 models must agree on the same winner with 52%+ confidence each)")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
