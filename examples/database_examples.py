#!/usr/bin/env python3
"""
Betting Database Examples

Shows how to use the SportsBetLang database to track bets, predictions,
and performance.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.database import BettingDatabase, create_database
from lib import SBL, EasySportModel
from datetime import datetime, timedelta
import random

print("SportsBetLang - Database Examples")
print("=" * 60)
print()

# Create database (or connect to existing one)
db = create_database("example_betting.db")

# ========================================
# Example 1: Track Bets
# ========================================
print("EXAMPLE 1: Tracking Bets")
print("-" * 60)

# Save a bet
bet_id = db.save_bet(
    matchup="Lakers vs Celtics",
    amount=100,
    odds=2.1,
    predicted_prob=0.58,
    sport='nba',
    bet_type='moneyline',
    notes="Lakers at home, Celtics on back-to-back"
)
print(f"✓ Saved bet #{bet_id}")

# Save result (Lakers won!)
db.save_result(bet_id, won=True)
print(f"✓ Bet #{bet_id} marked as won")

# Save another bet (this one lost)
bet_id2 = db.save_bet(
    matchup="Chiefs vs Bills",
    amount=150,
    odds=1.95,
    predicted_prob=0.54,
    sport='nfl',
    bet_type='moneyline'
)
db.save_result(bet_id2, won=False)
print(f"✓ Saved bet #{bet_id2} (lost)")
print()

# ========================================
# Example 2: View Bet History
# ========================================
print("EXAMPLE 2: View Bet History")
print("-" * 60)

bets = db.get_bets(limit=10)
print(f"Last {len(bets)} bets:")
for bet in bets[:5]:
    result = bet['result'] or 'pending'
    profit = bet['profit'] or 0
    print(f"  {bet['matchup']}: {result.upper()} (${profit:+.2f})")
print()

# ========================================
# Example 3: Track Predictions
# ========================================
print("EXAMPLE 3: Tracking Predictions")
print("-" * 60)

# Save predictions for upcoming games
pred_id1 = db.save_prediction(
    matchup="Warriors vs Nets",
    predicted_value=1,  # Warriors win
    predicted_prob=0.65,
    sport='nba',
    prediction_type='game_winner',
    model_used='NBA ML Model v1',
    confidence=0.70
)
print(f"✓ Saved prediction #{pred_id1}: Warriors to win (65% prob)")

pred_id2 = db.save_prediction(
    matchup="Packers vs Vikings",
    predicted_value=0,  # Packers lose
    predicted_prob=0.45,
    sport='nfl',
    prediction_type='game_winner',
    model_used='NFL ML Model v1'
)
print(f"✓ Saved prediction #{pred_id2}: Packers to lose (45% prob)")

# After games finish, save actual results
db.save_prediction_result(pred_id1, actual_value=1)  # Warriors won!
print(f"✓ Prediction #{pred_id1} was CORRECT")

db.save_prediction_result(pred_id2, actual_value=1)  # Packers actually won
print(f"✓ Prediction #{pred_id2} was WRONG")
print()

# ========================================
# Example 4: Track Historical Games
# ========================================
print("EXAMPLE 4: Storing Historical Game Data")
print("-" * 60)

# Save game with features for future ML training
game_id = db.save_game(
    date="2024-01-15",
    sport="nba",
    matchup="Lakers vs Celtics",
    home_team="Lakers",
    away_team="Celtics",
    home_score=118,
    away_score=112,
    features={
        'team_offensive_rating': 115.0,
        'team_defensive_rating': 107.5,
        'opponent_offensive_rating': 112.2,
        'opponent_defensive_rating': 108.3,
        'home_court': 1,
        'rest_days_team': 2,
        'rest_days_opponent': 1,
        'pace': 101.5
    },
    notes="Lakers strong defensive performance"
)
print(f"✓ Saved game #{game_id} with features for ML training")
print()

# ========================================
# Example 5: Bankroll Tracking
# ========================================
print("EXAMPLE 5: Bankroll Tracking")
print("-" * 60)

# Initialize bankroll
db.update_bankroll(1000, reason="Initial deposit")
print(f"✓ Starting bankroll: ${db.get_bankroll():.2f}")

# After bet wins
db.update_bankroll(1110, change=110, reason="Lakers ML win")
print(f"✓ After Lakers win: ${db.get_bankroll():.2f}")

# After bet loses
db.update_bankroll(960, change=-150, reason="Chiefs ML loss")
print(f"✓ After Chiefs loss: ${db.get_bankroll():.2f}")

# View history
print("\nBankroll history:")
history = db.get_bankroll_history(limit=5)
for entry in history:
    change = entry['change'] or 0
    print(f"  {entry['timestamp'][:10]}: ${entry['amount']:.2f} ({change:+.2f}) - {entry['reason']}")
print()

# ========================================
# Example 6: Performance Analytics
# ========================================
print("EXAMPLE 6: Performance Analytics")
print("-" * 60)

# Add more bets for better stats
random.seed(42)
for i in range(20):
    matchup = f"Team A vs Team B (Game {i+1})"
    amount = random.uniform(50, 200)
    odds = random.uniform(1.8, 2.5)
    prob = random.uniform(0.45, 0.65)

    bet_id = db.save_bet(matchup, amount, odds, prob, sport='nba')

    # Simulate results
    won = random.random() < prob
    db.save_result(bet_id, won=won)

# Get performance stats
db.print_performance(sport='nba')

# Get specific stats
stats = db.get_performance(sport='nba')
print(f"\nQuick Stats:")
print(f"  {stats['wins']} wins, {stats['losses']} losses")
print(f"  Win rate: {stats['win_rate']:.1%}")
print(f"  Total profit: ${stats['total_profit']:.2f}")
print(f"  ROI: {stats['roi']:.2%}")
print()

# ========================================
# Example 7: Prediction Accuracy
# ========================================
print("EXAMPLE 7: Model Prediction Accuracy")
print("-" * 60)

# Add more predictions
for i in range(10):
    pred = random.choice([0, 1])
    prob = random.uniform(0.5, 0.8)
    pred_id = db.save_prediction(
        matchup=f"Game {i+1}",
        predicted_value=pred,
        predicted_prob=prob,
        sport='nba',
        model_used='NBA ML Model v1'
    )

    # Simulate actual result
    actual = random.choice([0, 1])
    db.save_prediction_result(pred_id, actual)

# Check accuracy
accuracy = db.get_prediction_accuracy(model='NBA ML Model v1')
print(f"Model: NBA ML Model v1")
print(f"  Total predictions: {accuracy['total_predictions']}")
print(f"  Correct: {accuracy['correct_predictions']}")
print(f"  Accuracy: {accuracy['accuracy']:.1%}")
print(f"  Avg confidence: {accuracy['avg_confidence']:.1%}")
print()

# ========================================
# Example 8: Filter and Query
# ========================================
print("EXAMPLE 8: Filtering Bets")
print("-" * 60)

# Get only NBA bets
nba_bets = db.get_bets(sport='nba', limit=5)
print(f"NBA bets: {len(nba_bets)}")

# Get only winning bets
winning_bets = db.get_bets(result='won', limit=5)
print(f"Winning bets: {len(winning_bets)}")

# Get pending bets
pending_bets = db.get_bets(result='pending')
print(f"Pending bets: {len(pending_bets)}")
print()

# ========================================
# Example 9: Integration with Easy Sport Models
# ========================================
print("EXAMPLE 9: Integration with ML Models")
print("-" * 60)

# Generate training data from database
print("Loading historical games from database...")
games = db.get_games(sport='nba', limit=100)

# If we have games with features, we can train a model
if games and games[0].get('features'):
    print(f"✓ Found {len(games)} games with features")

    # Convert to format for EasySportModel
    training_data = []
    for game in games:
        if game['features'] and game['result']:
            features = game['features']
            features['result'] = 1 if game['result'] == 'home_win' else 0
            training_data.append(features)

    if len(training_data) >= 20:
        # Train model
        print("Training model on historical data...")
        model = EasySportModel('nba', 'game_winner')
        model.fit(training_data)

        # Make prediction
        new_game = {
            'team_offensive_rating': 116.0,
            'team_defensive_rating': 108.0,
            'opponent_offensive_rating': 111.0,
            'opponent_defensive_rating': 110.0,
            'home_court': 1,
            'rest_days_team': 2,
            'rest_days_opponent': 2,
            'pace': 101.0
        }

        prob = model.predict_proba(new_game)

        # Save prediction to database
        pred_id = db.save_prediction(
            matchup="Future Game",
            predicted_value=1,
            predicted_prob=prob,
            sport='nba',
            prediction_type='game_winner',
            model_used='EasySportModel NBA',
            confidence=prob,
            features=new_game
        )

        print(f"✓ Made prediction (ID {pred_id}): Win probability {prob:.1%}")
else:
    print("  (Not enough historical data yet)")
print()

# ========================================
# Example 10: Complete Betting Workflow
# ========================================
print("EXAMPLE 10: Complete Betting Workflow")
print("-" * 60)

# 1. Get current bankroll
bankroll = db.get_bankroll()
print(f"1. Current bankroll: ${bankroll:.2f}")

# 2. Calculate Kelly for a bet
matchup = "Bucks vs Heat"
win_prob = 0.57
odds = 2.0

kelly = SBL.kelly(win_prob, odds)
recommended_bet = bankroll * kelly

print(f"\n2. Analyzing bet: {matchup}")
print(f"   Win probability: {win_prob:.1%}")
print(f"   Odds: {odds}")
print(f"   Kelly size: {kelly:.2%}")
print(f"   Recommended bet: ${recommended_bet:.2f}")

# 3. Place bet (using 1/2 Kelly for safety)
actual_bet = recommended_bet * 0.5
bet_id = db.save_bet(
    matchup=matchup,
    amount=actual_bet,
    odds=odds,
    predicted_prob=win_prob,
    sport='nba',
    bet_type='moneyline',
    notes="1/2 Kelly sizing"
)
print(f"\n3. Placed bet: ${actual_bet:.2f} (bet ID {bet_id})")

# 4. Simulate game result (won!)
db.save_result(bet_id, won=True)
profit = actual_bet * (odds - 1)
new_bankroll = bankroll + profit

print(f"\n4. Bet WON!")
print(f"   Profit: ${profit:.2f}")
print(f"   New bankroll: ${new_bankroll:.2f}")

# 5. Update bankroll
db.update_bankroll(new_bankroll, change=profit, reason=f"{matchup} win")

# 6. View updated performance
print(f"\n5. Updated performance:")
stats = db.get_performance(sport='nba')
print(f"   Total profit: ${stats['total_profit']:.2f}")
print(f"   ROI: {stats['roi']:.2%}")
print(f"   Win rate: {stats['win_rate']:.1%}")

print()
print("=" * 60)
print("All database examples complete!")
print()
print("Database features:")
print("  ✓ Track bets with automatic Kelly/EV calculation")
print("  ✓ Save predictions and track accuracy")
print("  ✓ Store historical games for ML training")
print("  ✓ Monitor bankroll over time")
print("  ✓ Performance analytics (ROI, win rate, etc.)")
print("  ✓ Filter and query by sport, date, result")
print("  ✓ Integration with Easy Sport Models")
print()
print(f"Database file: example_betting.db")
print("You can open it with any SQLite viewer or continue using it!")

# Clean up
db.close()
