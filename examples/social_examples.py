#!/usr/bin/env python3
"""
Examples of using SportsBetLang Social Features

Demonstrates user-generated predictions, leaderboards, discussions, and following.
"""

import requests
import json
from typing import Optional

# API base URL
BASE_URL = "http://localhost:8000/social"


class SocialClient:
    """Client for interacting with SportsBetLang social features."""

    def __init__(self, base_url: str = BASE_URL):
        """Initialize client."""
        self.base_url = base_url
        self.token: Optional[str] = None

    def register(self, username: str, email: str, password: str, display_name: Optional[str] = None):
        """Register a new user."""
        response = requests.post(
            f"{self.base_url}/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password,
                "display_name": display_name or username
            }
        )
        data = response.json()
        if response.status_code == 200:
            self.token = data['token']
            print(f"✓ Registered as @{username}")
            return data['user']
        else:
            print(f"✗ Registration failed: {data}")
            return None

    def login(self, username: str, password: str):
        """Login and get token."""
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        )
        data = response.json()
        if response.status_code == 200:
            self.token = data['token']
            print(f"✓ Logged in as @{username}")
            return data['user']
        else:
            print(f"✗ Login failed: {data}")
            return None

    def _headers(self):
        """Get request headers with auth token."""
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def create_prediction(self, sport: str, prediction_type: str, description: str,
                         pick: str, odds: float, stake: float, confidence: int,
                         reasoning: str = ""):
        """Create a prediction."""
        response = requests.post(
            f"{self.base_url}/predictions",
            json={
                "sport": sport,
                "prediction_type": prediction_type,
                "description": description,
                "pick": pick,
                "odds": odds,
                "stake": stake,
                "confidence": confidence,
                "reasoning": reasoning
            },
            headers=self._headers()
        )
        return response.json()

    def get_predictions_feed(self, sport: Optional[str] = None):
        """Get recent predictions."""
        params = {"sport": sport} if sport else {}
        response = requests.get(
            f"{self.base_url}/predictions/feed",
            params=params
        )
        return response.json()

    def settle_prediction(self, prediction_id: int, status: str, result: float):
        """Settle a prediction."""
        response = requests.put(
            f"{self.base_url}/predictions/{prediction_id}/settle",
            json={"status": status, "result": result},
            headers=self._headers()
        )
        return response.json()

    def create_discussion(self, title: str, content: str, category: str = "general",
                         sport: Optional[str] = None, tags: Optional[list] = None):
        """Create a discussion thread."""
        response = requests.post(
            f"{self.base_url}/discussions",
            json={
                "title": title,
                "content": content,
                "category": category,
                "sport": sport,
                "tags": tags or []
            },
            headers=self._headers()
        )
        return response.json()

    def get_discussions(self, category: Optional[str] = None, sport: Optional[str] = None):
        """Get discussions."""
        params = {}
        if category:
            params['category'] = category
        if sport:
            params['sport'] = sport

        response = requests.get(
            f"{self.base_url}/discussions",
            params=params
        )
        return response.json()

    def add_comment(self, target_type: str, target_id: int, content: str):
        """Add a comment."""
        if target_type == 'prediction':
            url = f"{self.base_url}/predictions/{target_id}/comments"
        else:
            url = f"{self.base_url}/discussions/{target_id}/comments"

        response = requests.post(
            url,
            json={"content": content},
            headers=self._headers()
        )
        return response.json()

    def follow_user(self, username: str):
        """Follow a user."""
        response = requests.post(
            f"{self.base_url}/users/{username}/follow",
            headers=self._headers()
        )
        return response.json()

    def get_leaderboard(self, metric: str = 'roi', sport: Optional[str] = None):
        """Get leaderboard."""
        params = {"metric": metric}
        if sport:
            params['sport'] = sport

        response = requests.get(
            f"{self.base_url}/leaderboard",
            params=params
        )
        return response.json()

    def like_prediction(self, prediction_id: int):
        """Like a prediction."""
        response = requests.post(
            f"{self.base_url}/prediction/{prediction_id}/like",
            headers=self._headers()
        )
        return response.json()


def example_user_registration():
    """Example: Register users and create profiles."""
    print("\n" + "="*70)
    print("EXAMPLE 1: User Registration and Authentication")
    print("="*70 + "\n")

    # Create two users
    client1 = SocialClient()
    client2 = SocialClient()

    # Register users
    user1 = client1.register(
        username="sharpbettor",
        email="sharp@example.com",
        password="password123",
        display_name="Sharp Bettor"
    )

    user2 = client2.register(
        username="analyticsexpert",
        email="analytics@example.com",
        password="password123",
        display_name="Analytics Expert"
    )

    if user1:
        print(f"   User ID: {user1['id']}")
        print(f"   Display Name: {user1['display_name']}")
        print(f"   Created: {user1['created_at']}")

    return client1, client2


def example_create_predictions(client: SocialClient):
    """Example: Create predictions."""
    print("\n" + "="*70)
    print("EXAMPLE 2: User-Generated Predictions")
    print("="*70 + "\n")

    # Create NBA prediction
    pred1 = client.create_prediction(
        sport="nba",
        prediction_type="player_prop",
        description="LeBron James Over 27.5 Points",
        pick="Over 27.5",
        odds=-110,
        stake=100,
        confidence=4,
        reasoning="LeBron averaging 29.2 PPG over last 5 games. Playing against weak defense."
    )
    print(f"✓ Created NBA prediction: {pred1['description']}")
    print(f"   ID: {pred1['id']} | Confidence: {'⭐' * pred1['confidence']}")

    # Create NFL prediction
    pred2 = client.create_prediction(
        sport="nfl",
        prediction_type="spread",
        description="Chiefs -3.5 vs Bills",
        pick="Chiefs -3.5",
        odds=-110,
        stake=150,
        confidence=5,
        reasoning="Chiefs at home, Mahomes 8-2 ATS in division games"
    )
    print(f"✓ Created NFL prediction: {pred2['description']}")
    print(f"   ID: {pred2['id']} | Stake: ${pred2['stake']}")

    return [pred1, pred2]


def example_settle_predictions(client: SocialClient, predictions: list):
    """Example: Settle predictions and update stats."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Settling Predictions")
    print("="*70 + "\n")

    # Win first prediction
    settled1 = client.settle_prediction(
        prediction_id=predictions[0]['id'],
        status='won',
        result=90.91  # Profit from $100 at -110
    )
    print(f"✓ Settled prediction {settled1['id']} as WON")
    print(f"   Profit: ${settled1['result']}")

    # Lose second prediction
    settled2 = client.settle_prediction(
        prediction_id=predictions[1]['id'],
        status='lost',
        result=-150  # Lost stake
    )
    print(f"✓ Settled prediction {settled2['id']} as LOST")
    print(f"   Loss: ${settled2['result']}")


def example_discussions(client: SocialClient):
    """Example: Create discussion threads."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Discussion Threads")
    print("="*70 + "\n")

    # Create strategy discussion
    discussion = client.create_discussion(
        title="Best strategies for NBA player props?",
        content="""I've been crushing it with NBA player props lately. My approach:

1. Focus on pace-adjusted matchups
2. Look for injuries that increase usage
3. Fade players on back-to-backs
4. Target over-performing benches

What strategies work for you?""",
        category="strategy",
        sport="nba",
        tags=["strategy", "nba", "props"]
    )

    print(f"✓ Created discussion: '{discussion['title']}'")
    print(f"   ID: {discussion['id']}")
    print(f"   Category: {discussion['category']}")
    print(f"   Tags: {', '.join(discussion['tags'])}")

    return discussion


def example_comments(client: SocialClient, discussion_id: int):
    """Example: Add comments to discussions."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Comments and Engagement")
    print("="*70 + "\n")

    # Add comment
    comment = client.add_comment(
        target_type='discussion',
        target_id=discussion_id,
        content="Great points! I also like targeting blowouts where starters sit early."
    )

    print(f"✓ Added comment to discussion {discussion_id}")
    print(f"   Comment ID: {comment['id']}")
    print(f"   Content: {comment['content']}")


def example_following(client1: SocialClient, client2: SocialClient):
    """Example: Follow analysts."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Following Analysts")
    print("="*70 + "\n")

    # User 1 follows User 2
    result = client1.follow_user("analyticsexpert")
    print(f"✓ @sharpbettor followed @analyticsexpert")
    print(f"   Status: {result['status']}")


def example_leaderboard():
    """Example: View leaderboards."""
    print("\n" + "="*70)
    print("EXAMPLE 7: Community Leaderboards")
    print("="*70 + "\n")

    client = SocialClient()

    # Get ROI leaderboard
    roi_leaders = client.get_leaderboard(metric='roi')
    print("📊 Top Users by ROI:\n")

    for user in roi_leaders[:5]:
        print(f"{user['rank']}. @{user['username']} - ROI: {user['roi']*100:.1f}%")
        print(f"   Predictions: {user['total_predictions']} | Win Rate: {user['win_rate']*100:.1f}%")

    # Get sport-specific leaderboard
    print("\n📊 Top NBA Predictors:\n")
    nba_leaders = client.get_leaderboard(metric='roi', sport='nba')

    for user in nba_leaders[:3]:
        print(f"{user['rank']}. @{user['username']}")
        print(f"   ROI: {user.get('roi', 0)*100:.1f}% | Predictions: {user.get('predictions_count', 0)}")


def example_predictions_feed():
    """Example: View predictions feed."""
    print("\n" + "="*70)
    print("EXAMPLE 8: Predictions Feed")
    print("="*70 + "\n")

    client = SocialClient()

    # Get recent predictions
    predictions = client.get_predictions_feed()
    print("📰 Recent Predictions:\n")

    for pred in predictions[:5]:
        confidence_stars = '⭐' * (pred['confidence'] or 3)
        analyst_badge = " 👑" if pred['is_analyst'] else ""

        print(f"@{pred['username']}{analyst_badge}: {pred['description']}")
        print(f"   Pick: {pred['pick']} | Confidence: {confidence_stars}")
        print(f"   {pred['likes_count']} ❤ | {pred['comments_count']} 💬\n")


def main():
    """Run all examples."""
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║      SportsBetLang Social Features - Usage Examples         ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    print("\n⚠️  Make sure the API server is running:")
    print("   python -m sportsbetlang.api.routes\n")

    try:
        # Register users
        client1, client2 = example_user_registration()

        # Create predictions
        predictions = example_create_predictions(client1)

        # Settle predictions
        example_settle_predictions(client1, predictions)

        # Create discussions
        discussion = example_discussions(client2)

        # Add comments
        example_comments(client1, discussion['id'])

        # Following
        example_following(client1, client2)

        # Leaderboards
        example_leaderboard()

        # Predictions feed
        example_predictions_feed()

        print("\n╔══════════════════════════════════════════════════════════════╗")
        print("║                    Examples Complete!                        ║")
        print("╚══════════════════════════════════════════════════════════════╝")

        print("\nNext steps:")
        print("  1. View API docs: http://localhost:8000/docs")
        print("  2. Check leaderboards: GET /social/leaderboard")
        print("  3. Browse discussions: GET /social/discussions")

    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Cannot connect to API server")
        print("   Make sure the server is running:")
        print("   python -m sportsbetlang.api.routes")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
