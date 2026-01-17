#!/usr/bin/env python3
"""
Examples of using the SportsBetLang AI Chat Assistant

Demonstrates various natural language queries and API usage.
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sportsbetlang.api.chat import ChatService, SportsAnalyticsService


async def example_natural_language_queries():
    """Example: Natural language chat queries."""
    print("=" * 70)
    print("EXAMPLE 1: Natural Language Queries")
    print("=" * 70)

    # Initialize chat service
    chat = ChatService()
    session_id = "demo-session-1"
    chat.create_session(session_id)

    queries = [
        "Predict LeBron's points tonight",
        "Compare Patrick Mahomes and Josh Allen this season",
        "What's the best strategy for betting on NBA games?",
        "Analyze Stephen Curry's three-point shooting trend"
    ]

    for query in queries:
        print(f"\n🏀 Query: {query}")
        print("-" * 70)

        result = await chat.process_query(query, session_id)

        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"🤖 Response:\n{result['answer']}\n")

            if result.get('prediction'):
                print("📊 Prediction:")
                for key, value in result['prediction'].items():
                    print(f"  {key}: {value}")


def example_player_predictions():
    """Example: Player performance predictions."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Player Performance Predictions")
    print("=" * 70)

    analytics = SportsAnalyticsService()

    # Predict NBA player stats
    predictions = [
        ("nba", "LeBron James", "points"),
        ("nba", "Stephen Curry", "three_pointers"),
        ("nfl", "Patrick Mahomes", "passing_yards"),
        ("mlb", "Shohei Ohtani", "home_runs"),
    ]

    for sport, player, metric in predictions:
        print(f"\n🎯 Predicting {player} - {metric} ({sport.upper()})")
        print("-" * 70)

        result = analytics.predict_player_stat(sport, player, metric)

        print(f"Prediction: {result['prediction']}")
        print(f"Confidence Interval: {result['confidence_interval']}")
        print(f"Methodology: {result['methodology']}")
        print(f"Recent Form: {result['recent_form']}")


def example_player_comparisons():
    """Example: Player comparisons."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Player Comparisons")
    print("=" * 70)

    analytics = SportsAnalyticsService()

    comparisons = [
        ("nba", "LeBron James", "Kevin Durant", ["points", "assists", "rebounds"]),
        ("nfl", "Patrick Mahomes", "Josh Allen", ["passing_yards", "touchdowns"]),
        ("mlb", "Aaron Judge", "Shohei Ohtani", ["home_runs", "rbis"]),
    ]

    for sport, player1, player2, metrics in comparisons:
        print(f"\n⚖️  Comparing {player1} vs {player2} ({sport.upper()})")
        print("-" * 70)

        result = analytics.compare_players(sport, player1, player2, metrics)

        for metric, data in result['metrics'].items():
            print(f"\n{metric.upper()}:")
            print(f"  {player1}: {data[player1]}")
            print(f"  {player2}: {data[player2]}")
            print(f"  Difference: {data['difference']} (advantage: {data['advantage']})")


def example_historical_trends():
    """Example: Historical trend analysis."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Historical Trend Analysis")
    print("=" * 70)

    analytics = SportsAnalyticsService()

    trends = [
        ("nba", "Stephen Curry", "three_pointers", 10),
        ("nfl", "Patrick Mahomes", "passing_yards", 5),
        ("mlb", "Shohei Ohtani", "home_runs", 10),
    ]

    for sport, player, metric, games in trends:
        print(f"\n📈 Trend Analysis: {player} - {metric} (last {games} games)")
        print("-" * 70)

        result = analytics.analyze_historical_trend(sport, player, metric, games)

        print(f"Trend: {result['trend']} ({result['trend_strength']})")
        print(f"Recent Average: {result['recent_average']}")
        print(f"Peak: {result['peak']} | Lowest: {result['lowest']}")
        print(f"Data: {result['data']}")


async def example_conversational_context():
    """Example: Conversational context and follow-up questions."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Conversational Context")
    print("=" * 70)

    chat = ChatService()
    session_id = "context-demo"
    chat.create_session(session_id)

    conversation = [
        "Tell me about LeBron James' scoring this season",
        "How does that compare to last season?",
        "What's his prediction for tonight?",
        "Should I bet on him to score over 25 points?"
    ]

    for i, query in enumerate(conversation, 1):
        print(f"\n[Turn {i}] You: {query}")
        print("-" * 70)

        result = await chat.process_query(query, session_id)

        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Assistant: {result['answer'][:200]}...")


def example_api_usage():
    """Example: Direct API usage (non-chat)."""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Direct API Usage")
    print("=" * 70)

    analytics = SportsAnalyticsService()

    print("\n1. Quick prediction:")
    pred = analytics.predict_player_stat("nba", "LeBron James", "points")
    print(f"   LeBron points prediction: {pred['prediction']}")

    print("\n2. Quick comparison:")
    comp = analytics.compare_players("nba", "LeBron James", "Kevin Durant", ["points"])
    print(f"   LeBron vs KD points: {comp['metrics']['points']}")

    print("\n3. Supported sports and metrics:")
    print(f"   Sports: {analytics.supported_sports}")
    print(f"   NBA metrics: {analytics.supported_metrics['nba']}")


async def main():
    """Run all examples."""
    print("\n")
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║      SportsBetLang AI Chat Assistant - Usage Examples       ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    try:
        # Check for API key
        if not os.getenv('ANTHROPIC_API_KEY'):
            print("\n⚠️  Warning: ANTHROPIC_API_KEY not set.")
            print("Natural language chat examples will be skipped.")
            print("Set your API key: export ANTHROPIC_API_KEY='your-key'\n")
            skip_chat = True
        else:
            skip_chat = False

        # Run examples that don't require API key
        example_player_predictions()
        example_player_comparisons()
        example_historical_trends()
        example_api_usage()

        # Run chat examples if API key is available
        if not skip_chat:
            await example_natural_language_queries()
            await example_conversational_context()
        else:
            print("\n" + "=" * 70)
            print("Skipping chat examples (API key not set)")
            print("=" * 70)

        print("\n")
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║                    Examples Complete!                        ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print("\nNext steps:")
        print("  1. Try the interactive CLI: python sportsbetlang/cli/chat_assistant.py")
        print("  2. Start the API server: python -m sportsbetlang.api.routes")
        print("  3. Explore the API docs: http://localhost:8000/docs")

    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
