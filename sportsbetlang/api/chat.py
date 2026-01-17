"""
AI Chat Service for Natural Language Sports Queries

Handles conversational sports analytics, player predictions, and historical analysis.
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import anthropic

from sportsbetlang.common.odds_converter import american_to_decimal, decimal_to_probability
from sportsbetlang.common.kelly import kelly_criterion
from sportsbetlang.analytics.statistics import calculate_roi, calculate_sharpe_ratio


class ChatService:
    """AI-powered chat service for sports analytics queries."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize chat service with Anthropic API."""
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable must be set")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.conversation_history: Dict[str, List[Dict]] = {}

        # System prompt for sports analytics assistant
        self.system_prompt = """You are an expert sports analytics AI assistant for SportsBetLang,
a platform that provides betting insights, player predictions, and statistical analysis.

You have access to these analytical capabilities:
- Player performance predictions using statistical models
- Historical data analysis across NFL, NBA, MLB, and NHL
- Betting odds calculations and expected value analysis
- Player comparisons based on advanced metrics
- Real-time insights on games and players

When users ask questions like "Predict LeBron's points tonight", you should:
1. Identify the sport (NBA), player (LeBron James), and metric (points)
2. Request historical data analysis
3. Apply relevant statistical models (moving averages, trend analysis)
4. Provide a prediction with confidence intervals
5. Explain your reasoning clearly

Be conversational, insightful, and always back up predictions with data and methodology.
Format numbers clearly and provide actionable insights."""

    def create_session(self, session_id: str) -> None:
        """Create a new conversation session."""
        self.conversation_history[session_id] = []

    def get_session_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session."""
        return self.conversation_history.get(session_id, [])

    async def process_query(
        self,
        query: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a natural language sports query.

        Args:
            query: User's natural language question
            session_id: Conversation session identifier
            context: Optional context (player stats, game data, etc.)

        Returns:
            Response dictionary with answer and metadata
        """
        # Ensure session exists
        if session_id not in self.conversation_history:
            self.create_session(session_id)

        # Add context if available
        enhanced_query = query
        if context:
            enhanced_query = f"{query}\n\nContext: {json.dumps(context, indent=2)}"

        # Build messages for Claude
        messages = self.conversation_history[session_id].copy()
        messages.append({
            "role": "user",
            "content": enhanced_query
        })

        # Call Claude API
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2048,
                system=self.system_prompt,
                messages=messages
            )

            # Extract response text
            assistant_message = response.content[0].text

            # Update conversation history
            self.conversation_history[session_id].append({
                "role": "user",
                "content": query
            })
            self.conversation_history[session_id].append({
                "role": "assistant",
                "content": assistant_message
            })

            # Parse response for structured data
            result = {
                "answer": assistant_message,
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "query": query,
                "model": "claude-sonnet-4-5-20250929"
            }

            # Attempt to extract predictions or structured insights
            if self._is_prediction_query(query):
                result["prediction"] = self._extract_prediction(assistant_message)

            return result

        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "query": query
            }

    def _is_prediction_query(self, query: str) -> bool:
        """Check if query is asking for a prediction."""
        prediction_keywords = ['predict', 'forecast', 'expect', 'tonight', 'tomorrow', 'will']
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in prediction_keywords)

    def _extract_prediction(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract structured prediction from response text."""
        # This is a simple implementation - could be enhanced with more sophisticated parsing
        lines = response.split('\n')
        prediction = {}

        for line in lines:
            # Look for numeric predictions
            if 'points' in line.lower() and any(char.isdigit() for char in line):
                prediction['metric'] = 'points'
                # Extract numbers from line
                numbers = [word for word in line.split() if any(char.isdigit() for char in word)]
                if numbers:
                    prediction['value'] = numbers[0]

            if 'confidence' in line.lower():
                prediction['confidence'] = line

        return prediction if prediction else None

    def clear_session(self, session_id: str) -> None:
        """Clear conversation history for a session."""
        if session_id in self.conversation_history:
            self.conversation_history[session_id] = []


class SportsAnalyticsService:
    """Service for sports-specific analytics and predictions."""

    def __init__(self):
        """Initialize analytics service."""
        self.supported_sports = ['nfl', 'nba', 'mlb', 'nhl']
        self.supported_metrics = {
            'nba': ['points', 'assists', 'rebounds', 'steals', 'blocks', 'three_pointers'],
            'nfl': ['passing_yards', 'rushing_yards', 'touchdowns', 'receptions', 'completions'],
            'mlb': ['hits', 'runs', 'rbis', 'home_runs', 'strikeouts', 'walks'],
            'nhl': ['goals', 'assists', 'points', 'shots', 'saves', 'plus_minus']
        }

    def predict_player_stat(
        self,
        sport: str,
        player_name: str,
        metric: str,
        historical_data: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Predict a player's statistical performance.

        Args:
            sport: Sport league (nba, nfl, mlb, nhl)
            player_name: Player's name
            metric: Statistic to predict (points, yards, etc.)
            historical_data: Optional list of recent performances

        Returns:
            Prediction with confidence intervals
        """
        if sport.lower() not in self.supported_sports:
            return {"error": f"Sport {sport} not supported"}

        # Use historical data or mock data for demonstration
        if historical_data is None:
            historical_data = self._get_mock_player_data(sport, player_name, metric)

        # Calculate prediction using moving average
        prediction = self._calculate_moving_average_prediction(historical_data)

        return {
            "player": player_name,
            "sport": sport.upper(),
            "metric": metric,
            "prediction": prediction['value'],
            "confidence_interval": prediction['interval'],
            "methodology": "7-game weighted moving average",
            "sample_size": len(historical_data),
            "recent_form": historical_data[-5:] if len(historical_data) >= 5 else historical_data
        }

    def compare_players(
        self,
        sport: str,
        player1: str,
        player2: str,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare two players across multiple metrics.

        Args:
            sport: Sport league
            player1: First player name
            player2: Second player name
            metrics: List of metrics to compare

        Returns:
            Comparison results
        """
        if sport.lower() not in self.supported_sports:
            return {"error": f"Sport {sport} not supported"}

        if metrics is None:
            metrics = self.supported_metrics.get(sport.lower(), ['points'])

        comparison = {
            "sport": sport.upper(),
            "player1": player1,
            "player2": player2,
            "metrics": {}
        }

        for metric in metrics:
            # Get mock data for both players
            p1_data = self._get_mock_player_data(sport, player1, metric)
            p2_data = self._get_mock_player_data(sport, player2, metric)

            # Calculate averages
            p1_avg = sum(p1_data) / len(p1_data) if p1_data else 0
            p2_avg = sum(p2_data) / len(p2_data) if p2_data else 0

            comparison["metrics"][metric] = {
                player1: round(p1_avg, 2),
                player2: round(p2_avg, 2),
                "difference": round(p1_avg - p2_avg, 2),
                "advantage": player1 if p1_avg > p2_avg else player2
            }

        return comparison

    def analyze_historical_trend(
        self,
        sport: str,
        player_name: str,
        metric: str,
        games: int = 10
    ) -> Dict[str, Any]:
        """
        Analyze historical trends for a player.

        Args:
            sport: Sport league
            player_name: Player name
            metric: Metric to analyze
            games: Number of recent games to analyze

        Returns:
            Trend analysis results
        """
        data = self._get_mock_player_data(sport, player_name, metric)
        recent_data = data[-games:] if len(data) >= games else data

        # Calculate trend
        if len(recent_data) < 2:
            return {"error": "Insufficient data for trend analysis"}

        # Simple linear trend
        avg_first_half = sum(recent_data[:len(recent_data)//2]) / (len(recent_data)//2)
        avg_second_half = sum(recent_data[len(recent_data)//2:]) / (len(recent_data) - len(recent_data)//2)

        trend = "improving" if avg_second_half > avg_first_half else "declining"
        trend_strength = abs(avg_second_half - avg_first_half) / avg_first_half * 100

        return {
            "player": player_name,
            "sport": sport.upper(),
            "metric": metric,
            "games_analyzed": len(recent_data),
            "trend": trend,
            "trend_strength": f"{round(trend_strength, 1)}%",
            "recent_average": round(sum(recent_data) / len(recent_data), 2),
            "peak": max(recent_data),
            "lowest": min(recent_data),
            "data": recent_data
        }

    def _calculate_moving_average_prediction(
        self,
        data: List[float],
        window: int = 7
    ) -> Dict[str, Any]:
        """Calculate weighted moving average prediction."""
        if len(data) < window:
            window = len(data)

        recent_data = data[-window:]

        # Weighted moving average (more recent games weighted higher)
        weights = list(range(1, window + 1))
        weighted_sum = sum(val * weight for val, weight in zip(recent_data, weights))
        total_weight = sum(weights)
        prediction = weighted_sum / total_weight

        # Calculate standard deviation for confidence interval
        mean = sum(recent_data) / len(recent_data)
        variance = sum((x - mean) ** 2 for x in recent_data) / len(recent_data)
        std_dev = variance ** 0.5

        return {
            "value": round(prediction, 2),
            "interval": [
                round(prediction - std_dev, 2),
                round(prediction + std_dev, 2)
            ]
        }

    def _get_mock_player_data(
        self,
        sport: str,
        player_name: str,
        metric: str
    ) -> List[float]:
        """Get mock historical data for demonstration."""
        # This would be replaced with real database queries
        import random
        random.seed(hash(player_name + metric))

        # Generate realistic mock data based on sport and metric
        base_values = {
            'nba': {
                'points': (20, 35),
                'assists': (5, 12),
                'rebounds': (6, 14)
            },
            'nfl': {
                'passing_yards': (200, 350),
                'rushing_yards': (50, 150),
                'touchdowns': (1, 4)
            },
            'mlb': {
                'hits': (0, 4),
                'home_runs': (0, 2),
                'rbis': (0, 4)
            },
            'nhl': {
                'goals': (0, 3),
                'assists': (0, 3),
                'points': (0, 5)
            }
        }

        sport_lower = sport.lower()
        if sport_lower in base_values and metric in base_values[sport_lower]:
            min_val, max_val = base_values[sport_lower][metric]
            return [round(random.uniform(min_val, max_val), 1) for _ in range(15)]

        # Default fallback
        return [round(random.uniform(10, 30), 1) for _ in range(15)]
