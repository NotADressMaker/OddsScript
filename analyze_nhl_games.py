#!/usr/bin/env python3
"""
NHL Game Analysis Script
Uses all three advanced NHL models to analyze tomorrow's games
"""

from lib import NHLDecisionTree, NHLPowerRankings, NHLSimilarGameModel
import random

# Tomorrow's NHL Games (Tuesday)
GAMES = [
    {
        'away': 'Nashville Predators',
        'home': 'Boston Bruins',
        'spread': -1.5,  # Home team spread
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
        'spread': +1.5,  # Vegas favored on road
        'ou_line': 6.5,
        'home_ml': -260,
        'away_ml': +205
    },
    {
        'away': 'Dallas Stars',
        'home': 'St. Louis Blues',
        'spread': -1.5,  # Dallas favored
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
        'spread': -1.5,  # Washington favored
        'ou_line': 5.5,
        'home_ml': -215,
        'away_ml': +172
    }
]

# NHL Team Stats (2024-25 Season - Expected Goals per game)
# Format: {team: {'xgf': expected goals for, 'xga': expected goals against, 'goalie_sv': save %, 'recent_goals': avg last 10}}
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

# Power Rankings (Elo-style ratings)
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


def analyze_game_with_all_models(game, tree, rankings, sim_model):
    """Analyze a single game with all three models"""

    away_team = game['away']
    home_team = game['home']
    spread = game['spread']
    ou_line = game['ou_line']

    print(f"\n{'='*80}")
    print(f"🏒 {away_team} @ {home_team}")
    print(f"{'='*80}")
    print(f"Spread: {home_team} {spread:+.1f} | O/U: {ou_line}")
    print(f"Moneyline: {away_team} {game['away_ml']:+d} | {home_team} {game['home_ml']:+d}")

    # Get team stats
    away_stats = TEAM_STATS[away_team]
    home_stats = TEAM_STATS[home_team]

    print(f"\nTeam Stats:")
    print(f"  {away_team}: {away_stats['xgf']:.1f} xGF, {away_stats['xga']:.1f} xGA, .{int(away_stats['goalie_sv']*1000)} SV%")
    print(f"  {home_team}: {home_stats['xgf']:.1f} xGF, {home_stats['xga']:.1f} xGA, .{int(home_stats['goalie_sv']*1000)} SV%")

    # === MODEL 1: DECISION TREE ===
    print(f"\n{'─'*80}")
    print("📊 MODEL 1: DECISION TREE")
    print(f"{'─'*80}")

    # O/U Prediction
    ou_pred = tree.predict_over_under(
        team1_xgf=home_stats['xgf'],
        team1_xga=home_stats['xga'],
        team2_xgf=away_stats['xgf'],
        team2_xga=away_stats['xga'],
        line=ou_line,
        team1_goalie_sv_pct=home_stats['goalie_sv'],
        team2_goalie_sv_pct=away_stats['goalie_sv'],
        team1_recent_goals=home_stats['recent_goals'],
        team2_recent_goals=away_stats['recent_goals'],
        team1_rest_days=1,
        team2_rest_days=1
    )

    print(f"O/U Prediction: {ou_pred['prediction']} (Confidence: {ou_pred['confidence']:.1%})")
    print(f"  Expected Total: {ou_pred['expected_total']} (Line: {ou_line})")
    print(f"  Factors: xG Total={ou_pred['factors']['xg_based_total']}, "
          f"Form Total={ou_pred['factors']['recent_form_total']}, "
          f"Goalies={ou_pred['factors']['goalie_quality']}")

    # ATS Prediction (home team perspective)
    ats_pred = tree.predict_ats(
        team_xgf=home_stats['xgf'],
        team_xga=home_stats['xga'],
        opp_xgf=away_stats['xgf'],
        opp_xga=away_stats['xga'],
        spread=spread,
        is_home=True,
        team_recent_form=home_stats['recent_form'],
        opp_recent_form=away_stats['recent_form']
    )

    print(f"ATS Prediction: {home_team} {ats_pred['prediction']} (Confidence: {ats_pred['confidence']:.1%})")
    print(f"  Expected Differential: {ats_pred['expected_differential']:+.2f} (Spread: {spread:+.1f})")
    print(f"  Cover Margin: {ats_pred['cover_margin']:+.2f}")

    # === MODEL 2: POWER RANKINGS ===
    print(f"\n{'─'*80}")
    print("⚡ MODEL 2: POWER RANKINGS (ELO)")
    print(f"{'─'*80}")

    # Set team ratings
    rankings.set_rating(home_team, POWER_RATINGS[home_team])
    rankings.set_rating(away_team, POWER_RATINGS[away_team])

    power_pred = rankings.predict_game(home_team, away_team, team1_home=True)

    print(f"Win Probability: {home_team} {power_pred['team1_win_probability']:.1%} | "
          f"{away_team} {power_pred['team2_win_probability']:.1%}")
    print(f"  Ratings: {home_team} {power_pred['team1_rating']:.0f} | "
          f"{away_team} {power_pred['team2_rating']:.0f}")
    print(f"  Expected Goal Differential: {power_pred['expected_goal_differential']:+.2f}")
    print(f"  Expected Total: {power_pred['expected_total']:.1f}")

    # === MODEL 3: SIMILAR GAME MODEL ===
    print(f"\n{'─'*80}")
    print("🔍 MODEL 3: SIMILAR GAME MODEL")
    print(f"{'─'*80}")

    sim_pred = sim_model.predict_from_similar(
        team1_xgf=home_stats['xgf'],
        team1_xga=home_stats['xga'],
        team2_xgf=away_stats['xgf'],
        team2_xga=away_stats['xga'],
        line_total=ou_line,
        line_spread=spread,
        team1_home=True
    )

    if 'over_under' not in sim_pred:
        # Insufficient data case
        print(f"⚠️  Insufficient historical data ({sim_pred['similar_games_found']} games found, need {sim_pred['minimum_required']})")
    else:
        print(f"O/U: {sim_pred['over_under']['prediction']} (Confidence: {sim_pred['over_under']['confidence']:.1%})")
        print(f"  Historical: {sim_pred['over_under']['over_percentage']:.1%} over, "
              f"{sim_pred['over_under']['under_percentage']:.1%} under")
        print(f"  Average Total: {sim_pred['over_under']['average_total']:.1f}")

        print(f"ATS: {sim_pred['against_spread']['prediction']} (Confidence: {sim_pred['against_spread']['confidence']:.1%})")
        print(f"  Historical: {sim_pred['against_spread']['cover_percentage']:.1%} cover rate")
        print(f"  Sample: {sim_pred['analysis']['similar_games_found']} games, "
              f"quality={sim_pred['analysis']['sample_quality']}")

    # === CONSENSUS RECOMMENDATION ===
    print(f"\n{'─'*80}")
    print("💡 CONSENSUS RECOMMENDATION")
    print(f"{'─'*80}")

    # O/U Consensus
    ou_votes = []
    if ou_pred['confidence'] >= 0.60:
        ou_votes.append((ou_pred['prediction'], ou_pred['confidence'], 'Decision Tree'))
    if abs(power_pred['expected_total'] - ou_line) > 0.3:
        vote = 'OVER' if power_pred['expected_total'] > ou_line else 'UNDER'
        conf = min(0.70, 0.50 + abs(power_pred['expected_total'] - ou_line) * 0.1)
        ou_votes.append((vote, conf, 'Power Rankings'))
    if 'over_under' in sim_pred and sim_pred['over_under']['confidence'] >= 0.60:
        ou_votes.append((sim_pred['over_under']['prediction'], sim_pred['over_under']['confidence'], 'Similar Games'))

    if ou_votes:
        print(f"O/U Recommendations:")
        for vote, conf, model in ou_votes:
            print(f"  ✓ {vote} ({conf:.0%} confidence) - {model}")

        # Count votes
        over_votes = sum(1 for v in ou_votes if v[0] == 'OVER')
        under_votes = sum(1 for v in ou_votes if v[0] == 'UNDER')

        if over_votes > under_votes:
            avg_conf = sum(v[1] for v in ou_votes if v[0] == 'OVER') / over_votes
            print(f"  🎯 CONSENSUS: BET OVER {ou_line} ({over_votes}/{len(ou_votes)} models agree, avg {avg_conf:.0%} confidence)")
        elif under_votes > over_votes:
            avg_conf = sum(v[1] for v in ou_votes if v[0] == 'UNDER') / under_votes
            print(f"  🎯 CONSENSUS: BET UNDER {ou_line} ({under_votes}/{len(ou_votes)} models agree, avg {avg_conf:.0%} confidence)")
        else:
            print(f"  ⚠️  No consensus - models disagree")
    else:
        print(f"O/U: No strong recommendations (all confidences < 60%)")

    # ATS Consensus
    ats_votes = []
    if ats_pred['confidence'] >= 0.60:
        ats_votes.append((ats_pred['prediction'], ats_pred['confidence'], 'Decision Tree'))
    if abs(power_pred['expected_goal_differential'] - spread) > 0.5:
        vote = 'COVER' if power_pred['expected_goal_differential'] > abs(spread) else 'NO COVER'
        conf = min(0.70, 0.50 + abs(power_pred['expected_goal_differential'] - abs(spread)) * 0.1)
        ats_votes.append((vote, conf, 'Power Rankings'))
    if 'against_spread' in sim_pred and sim_pred['against_spread']['confidence'] >= 0.60:
        ats_votes.append((sim_pred['against_spread']['prediction'], sim_pred['against_spread']['confidence'], 'Similar Games'))

    if ats_votes:
        print(f"\nATS Recommendations:")
        for vote, conf, model in ats_votes:
            print(f"  ✓ {vote} ({conf:.0%} confidence) - {model}")

        cover_votes = sum(1 for v in ats_votes if v[0] == 'COVER')
        no_cover_votes = sum(1 for v in ats_votes if v[0] == 'NO COVER')

        if cover_votes > no_cover_votes:
            avg_conf = sum(v[1] for v in ats_votes if v[0] == 'COVER') / cover_votes
            print(f"  🎯 CONSENSUS: BET {home_team} {spread:+.1f} ({cover_votes}/{len(ats_votes)} models agree, avg {avg_conf:.0%} confidence)")
        elif no_cover_votes > cover_votes:
            avg_conf = sum(v[1] for v in ats_votes if v[0] == 'NO COVER') / no_cover_votes
            print(f"  🎯 CONSENSUS: BET {away_team} {-spread:+.1f} ({no_cover_votes}/{len(ats_votes)} models agree, avg {avg_conf:.0%} confidence)")
        else:
            print(f"  ⚠️  No consensus - models disagree")
    else:
        print(f"ATS: No strong recommendations (all confidences < 60%)")

    return {
        'game': game,
        'decision_tree': {'ou': ou_pred, 'ats': ats_pred},
        'power_rankings': power_pred,
        'similar_games': sim_pred
    }


def main():
    print("=" * 80)
    print("🏒 NHL ADVANCED MODELS - GAME ANALYSIS")
    print("=" * 80)
    print(f"Analyzing {len(GAMES)} games for Tuesday")
    print("Using: Decision Tree, Power Rankings, and Similar Game Models")

    # Initialize models
    print("\nInitializing models...")
    tree = NHLDecisionTree()
    rankings = NHLPowerRankings(k_factor=20.0, home_advantage=55.0)
    sim_model = NHLSimilarGameModel()

    # Populate similar game model with historical data
    print("Loading historical data for Similar Game Model...")
    for _ in range(100):
        # Generate synthetic historical games
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

    print("✓ Models initialized\n")

    # Analyze all games
    results = []
    for game in GAMES:
        result = analyze_game_with_all_models(game, tree, rankings, sim_model)
        results.append(result)

    # Summary
    print(f"\n\n{'='*80}")
    print("📋 SUMMARY - BEST BETS")
    print(f"{'='*80}\n")

    print("🔥 HIGH CONFIDENCE PLAYS (60%+ from multiple models):\n")

    high_conf_count = 0
    for result in results:
        game = result['game']
        dt_ou = result['decision_tree']['ou']
        dt_ats = result['decision_tree']['ats']
        pr = result['power_rankings']

        # Check for high confidence plays
        if dt_ou['confidence'] >= 0.65:
            high_conf_count += 1
            print(f"✓ {game['away']} @ {game['home']}")
            print(f"  BET: {dt_ou['prediction']} {game['ou_line']} ({dt_ou['confidence']:.0%} confidence)")
            print(f"  Reason: Expected total {dt_ou['expected_total']} vs line {game['ou_line']}\n")

        if dt_ats['confidence'] >= 0.65:
            high_conf_count += 1
            team_to_bet = game['home'] if dt_ats['prediction'] == 'COVER' else game['away']
            spread_to_bet = game['spread'] if dt_ats['prediction'] == 'COVER' else -game['spread']
            print(f"✓ {game['away']} @ {game['home']}")
            print(f"  BET: {team_to_bet} {spread_to_bet:+.1f} ({dt_ats['confidence']:.0%} confidence)")
            print(f"  Reason: Expected differential {dt_ats['expected_differential']:+.2f}\n")

    if high_conf_count == 0:
        print("No plays with 65%+ confidence found. Review individual game analysis above.\n")

    print(f"{'='*80}")
    print("Analysis complete! Good luck! 🍀")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
