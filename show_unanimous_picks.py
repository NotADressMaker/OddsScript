#!/usr/bin/env python3
"""
Show only NHL picks where ALL 3 models agree
"""

from lib import NHLDecisionTree, NHLPowerRankings, NHLSimilarGameModel
import random

# Tomorrow's NHL Games (Tuesday)
GAMES = [
    {
        'away': 'Nashville Predators',
        'home': 'Boston Bruins',
        'spread': -1.5,
        'ou_line': 6.5,
        'home_ml': -265,
        'away_ml': +210
    },
    {
        'away': 'Winnipeg Jets',
        'home': 'New Jersey Devils',
        'spread': -1.5,
        'ou_line': 5.5,
        'home_ml': -230,
        'away_ml': +184
    },
    {
        'away': 'Los Angeles Kings',
        'home': 'Detroit Red Wings',
        'spread': -1.5,
        'ou_line': 5.5,
        'home_ml': -235,
        'away_ml': +186
    },
    {
        'away': 'Utah Mammoth',
        'home': 'Florida Panthers',
        'spread': -1.5,
        'ou_line': 6.5,
        'home_ml': -172,
        'away_ml': +140
    },
    {
        'away': 'Buffalo Sabres',
        'home': 'Toronto Maple Leafs',
        'spread': -1.5,
        'ou_line': 6.5,
        'home_ml': -265,
        'away_ml': +210
    },
    {
        'away': 'Vegas Golden Knights',
        'home': 'Montreal Canadiens',
        'spread': +1.5,
        'ou_line': 6.5,
        'home_ml': -260,
        'away_ml': +205
    },
    {
        'away': 'Dallas Stars',
        'home': 'St. Louis Blues',
        'spread': -1.5,
        'ou_line': 5.5,
        'home_ml': -184,
        'away_ml': +148
    },
    {
        'away': 'Chicago Blackhawks',
        'home': 'Minnesota Wild',
        'spread': -1.5,
        'ou_line': 6.5,
        'home_ml': -120,
        'away_ml': +202
    },
    {
        'away': 'San Jose Sharks',
        'home': 'Vancouver Canucks',
        'spread': -1.5,
        'ou_line': 6.5,
        'home_ml': -245,
        'away_ml': +190
    },
    {
        'away': 'Washington Capitals',
        'home': 'Seattle Kraken',
        'spread': -1.5,
        'ou_line': 5.5,
        'home_ml': -215,
        'away_ml': +172
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
    'Nashville Predators': 1420,
    'Boston Bruins': 1580,
    'Winnipeg Jets': 1680,
    'New Jersey Devils': 1560,
    'Los Angeles Kings': 1540,
    'Detroit Red Wings': 1480,
    'Utah Mammoth': 1440,
    'Florida Panthers': 1620,
    'Buffalo Sabres': 1460,
    'Toronto Maple Leafs': 1590,
    'Vegas Golden Knights': 1610,
    'Montreal Canadiens': 1430,
    'Dallas Stars': 1640,
    'St. Louis Blues': 1490,
    'Chicago Blackhawks': 1380,
    'Minnesota Wild': 1570,
    'San Jose Sharks': 1350,
    'Vancouver Canucks': 1560,
    'Washington Capitals': 1550,
    'Seattle Kraken': 1520
}


def main():
    print("=" * 80)
    print("🏒 NHL UNANIMOUS PICKS - ALL 3 MODELS AGREE")
    print("=" * 80)
    print("Showing only picks where Decision Tree, Power Rankings, AND Similar Game")
    print("models all agree on the same prediction\n")

    # Initialize models
    tree = NHLDecisionTree()
    rankings = NHLPowerRankings(k_factor=20.0, home_advantage=55.0)
    sim_model = NHLSimilarGameModel()

    # Populate similar game model
    for _ in range(100):
        sim_model.add_game(
            team1=f"Team{random.randint(1,32)}",
            team2=f"Team{random.randint(1,32)}",
            team1_xgf=random.uniform(2.4, 3.6),
            team1_xga=random.uniform(2.4, 3.6),
            team2_xgf=random.uniform(2.4, 3.6),
            team2_xga=random.uniform(2.4, 3.6),
            team1_goals=random.randint(1, 6),
            team2_goals=random.randint(1, 6),
            total_goals=random.randint(4, 8),
            spread_result=random.choice(['cover', 'no_cover', 'push']),
            over_under_result=random.choice(['over', 'under', 'push']),
            team1_home=True
        )

    unanimous_picks = []

    for game in GAMES:
        away_team = game['away']
        home_team = game['home']
        spread = game['spread']
        ou_line = game['ou_line']

        away_stats = TEAM_STATS[away_team]
        home_stats = TEAM_STATS[home_team]

        # Decision Tree predictions
        dt_ou = tree.predict_over_under(
            team1_xgf=home_stats['xgf'], team1_xga=home_stats['xga'],
            team2_xgf=away_stats['xgf'], team2_xga=away_stats['xga'],
            line=ou_line,
            team1_goalie_sv_pct=home_stats['goalie_sv'],
            team2_goalie_sv_pct=away_stats['goalie_sv'],
            team1_recent_goals=home_stats['recent_goals'],
            team2_recent_goals=away_stats['recent_goals']
        )

        dt_ats = tree.predict_ats(
            team_xgf=home_stats['xgf'], team_xga=home_stats['xga'],
            opp_xgf=away_stats['xgf'], opp_xga=away_stats['xga'],
            spread=spread, is_home=True,
            team_recent_form=home_stats['recent_form'],
            opp_recent_form=away_stats['recent_form']
        )

        # Power Rankings predictions
        rankings.set_rating(home_team, POWER_RATINGS[home_team])
        rankings.set_rating(away_team, POWER_RATINGS[away_team])
        pr = rankings.predict_game(home_team, away_team, team1_home=True)

        # Similar Game predictions
        sim_pred = sim_model.predict_from_similar(
            team1_xgf=home_stats['xgf'], team1_xga=home_stats['xga'],
            team2_xgf=away_stats['xgf'], team2_xga=away_stats['xga'],
            line_total=ou_line, line_spread=spread, team1_home=True
        )

        # Determine Power Rankings votes
        pr_ou_vote = None
        if abs(pr['expected_total'] - ou_line) > 0.3:
            pr_ou_vote = 'OVER' if pr['expected_total'] > ou_line else 'UNDER'

        pr_ats_vote = None
        if abs(pr['expected_goal_differential'] - spread) > 0.5:
            pr_ats_vote = 'COVER' if pr['expected_goal_differential'] > abs(spread) else 'NO COVER'

        # Check for unanimous O/U
        ou_votes = []
        if dt_ou['confidence'] >= 0.60 and dt_ou['prediction'] != 'PUSH':
            ou_votes.append(('DT', dt_ou['prediction'], dt_ou['confidence']))
        if pr_ou_vote:
            conf = min(0.70, 0.50 + abs(pr['expected_total'] - ou_line) * 0.1)
            ou_votes.append(('PR', pr_ou_vote, conf))
        if 'over_under' in sim_pred and sim_pred['over_under']['confidence'] >= 0.60 and sim_pred['over_under']['prediction'] != 'PUSH':
            ou_votes.append(('SG', sim_pred['over_under']['prediction'], sim_pred['over_under']['confidence']))

        # Check if all 3 agree on O/U
        if len(ou_votes) == 3:
            predictions = [v[1] for v in ou_votes]
            if len(set(predictions)) == 1:  # All same prediction
                avg_conf = sum(v[2] for v in ou_votes) / 3
                unanimous_picks.append({
                    'type': 'O/U',
                    'game': f"{away_team} @ {home_team}",
                    'pick': f"{predictions[0]} {ou_line}",
                    'confidence': avg_conf,
                    'details': f"Expected: {dt_ou['expected_total']:.1f}, Line: {ou_line}"
                })

        # Check for unanimous ATS
        ats_votes = []
        if dt_ats['confidence'] >= 0.60 and dt_ats['prediction'] != 'PUSH':
            ats_votes.append(('DT', dt_ats['prediction'], dt_ats['confidence']))
        if pr_ats_vote:
            conf = min(0.70, 0.50 + abs(pr['expected_goal_differential'] - abs(spread)) * 0.1)
            ats_votes.append(('PR', pr_ats_vote, conf))
        if 'against_spread' in sim_pred and sim_pred['against_spread']['confidence'] >= 0.60 and sim_pred['against_spread']['prediction'] != 'PUSH':
            ats_votes.append(('SG', sim_pred['against_spread']['prediction'], sim_pred['against_spread']['confidence']))

        # Check if all 3 agree on ATS
        if len(ats_votes) == 3:
            predictions = [v[1] for v in ats_votes]
            if len(set(predictions)) == 1:  # All same prediction
                avg_conf = sum(v[2] for v in ats_votes) / 3
                team_to_bet = home_team if predictions[0] == 'COVER' else away_team
                spread_to_bet = spread if predictions[0] == 'COVER' else -spread
                unanimous_picks.append({
                    'type': 'ATS',
                    'game': f"{away_team} @ {home_team}",
                    'pick': f"{team_to_bet} {spread_to_bet:+.1f}",
                    'confidence': avg_conf,
                    'details': f"Expected diff: {dt_ats['expected_differential']:+.1f}"
                })

    # Display unanimous picks
    if unanimous_picks:
        print(f"Found {len(unanimous_picks)} unanimous picks:\n")

        for i, pick in enumerate(unanimous_picks, 1):
            print(f"{i}. {pick['game']}")
            print(f"   🎯 BET: {pick['pick']}")
            print(f"   ✅ All 3 models agree ({pick['type']})")
            print(f"   💪 Confidence: {pick['confidence']:.1%}")
            print(f"   📊 {pick['details']}")
            print()

        print("=" * 80)
        print(f"💎 STRONGEST UNANIMOUS PICKS (sorted by confidence):")
        print("=" * 80)

        sorted_picks = sorted(unanimous_picks, key=lambda x: x['confidence'], reverse=True)
        for i, pick in enumerate(sorted_picks[:5], 1):
            print(f"{i}. {pick['pick']:30s} | {pick['confidence']:.0%} | {pick['game']}")

    else:
        print("⚠️  No unanimous picks found (all 3 models must agree with 60%+ confidence)")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
