#!/usr/bin/env python3
"""
Examples of using SportsBetLang Developer Features

Demonstrates API keys, webhooks, custom data feeds, and white-label solutions.
"""

import requests
import hmac
import hashlib
import json
from typing import Optional


# API base URL
BASE_URL = "http://localhost:8000"


class DeveloperClient:
    """Client for SportsBetLang Developer API."""

    def __init__(self, base_url: str = BASE_URL):
        """Initialize client."""
        self.base_url = base_url
        self.token: Optional[str] = None
        self.api_key: Optional[str] = None

    def login(self, username: str, password: str):
        """Login and get JWT token."""
        response = requests.post(
            f"{self.base_url}/social/auth/login",
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

    def _headers(self, use_api_key: bool = False):
        """Get request headers."""
        if use_api_key and self.api_key:
            return {"X-API-Key": self.api_key}
        elif self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def create_api_key(self, name: str, tier: str = 'free', expires_days: Optional[int] = None):
        """Create an API key."""
        response = requests.post(
            f"{self.base_url}/developer/keys",
            json={
                "name": name,
                "tier": tier,
                "expires_days": expires_days
            },
            headers=self._headers()
        )

        if response.status_code == 200:
            data = response.json()
            self.api_key = data['key']  # Save for later use
            print(f"\n✓ Created {tier.upper()} API key: {name}")
            print(f"  Key: {data['key'][:20]}... (save this!)")
            print(f"  Rate Limit: {data['rate_limit']} requests/day")
            return data
        else:
            print(f"✗ Failed to create API key: {response.json()}")
            return None

    def list_api_keys(self):
        """List all API keys."""
        response = requests.get(
            f"{self.base_url}/developer/keys",
            headers=self._headers()
        )
        return response.json()

    def get_usage_stats(self, days: int = 30):
        """Get API usage statistics."""
        response = requests.get(
            f"{self.base_url}/developer/keys/usage",
            params={"days": days},
            headers=self._headers()
        )
        return response.json()

    def create_webhook(self, url: str, events: list):
        """Create a webhook."""
        response = requests.post(
            f"{self.base_url}/developer/webhooks",
            json={
                "url": url,
                "events": events
            },
            headers=self._headers()
        )

        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Created webhook: {url}")
            print(f"  Events: {', '.join(events)}")
            print(f"  Secret: {data['secret'][:20]}... (use for signature verification)")
            return data
        else:
            print(f"✗ Failed to create webhook: {response.json()}")
            return None

    def list_webhooks(self):
        """List all webhooks."""
        response = requests.get(
            f"{self.base_url}/developer/webhooks",
            headers=self._headers()
        )
        return response.json()

    def get_predictions_data(self, sport: Optional[str] = None, limit: int = 10):
        """Get predictions using API key."""
        params = {"limit": limit}
        if sport:
            params['sport'] = sport

        response = requests.get(
            f"{self.base_url}/developer/data/predictions",
            params=params,
            headers=self._headers(use_api_key=True)
        )
        return response.json()

    def get_leaderboard_data(self, metric: str = 'roi', limit: int = 10):
        """Get leaderboard data using API key."""
        response = requests.get(
            f"{self.base_url}/developer/data/leaderboard",
            params={"metric": metric, "limit": limit},
            headers=self._headers(use_api_key=True)
        )
        return response.json()

    def export_custom_data(self, sport: Optional[str] = None, format: str = 'json'):
        """Export custom data."""
        response = requests.post(
            f"{self.base_url}/developer/data/export",
            json={
                "sport": sport,
                "format": format
            },
            headers=self._headers()
        )
        return response.json()

    def create_whitelabel(self, domain: str, brand_name: str, **kwargs):
        """Create white-label configuration (Enterprise only)."""
        response = requests.post(
            f"{self.base_url}/developer/whitelabel",
            json={
                "domain": domain,
                "brand_name": brand_name,
                **kwargs
            },
            headers=self._headers()
        )
        return response.json()


def example_api_key_management():
    """Example: Create and manage API keys."""
    print("\n" + "="*70)
    print("EXAMPLE 1: API Key Management")
    print("="*70)

    client = DeveloperClient()

    # Login (assuming user exists from social examples)
    user = client.login("sharpbettor", "password123")
    if not user:
        print("User not found. Run social_examples.py first.")
        return None

    # Create Free API key
    free_key = client.create_api_key(
        name="My Free App",
        tier="free"
    )

    # Create Pro API key (would require subscription in production)
    pro_key = client.create_api_key(
        name="My Pro Integration",
        tier="pro",
        expires_days=365
    )

    # List all keys
    print("\n📋 Your API Keys:")
    keys = client.list_api_keys()
    for key in keys['keys']:
        status = "✓ Active" if key['active'] else "✗ Revoked"
        print(f"  {status} | {key['name']} ({key['tier']})")
        print(f"      {key['key_prefix']}... | {key['requests_today']}/{key['rate_limit']} today")

    return client


def example_data_feeds(client: DeveloperClient):
    """Example: Access custom data feeds."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Custom Data Feeds")
    print("="*70)

    # Get predictions data
    print("\n📊 Recent NBA Predictions:")
    predictions = client.get_predictions_data(sport="nba", limit=5)

    for pred in predictions['predictions'][:5]:
        print(f"  @{pred['username']}: {pred['description']}")
        print(f"    Pick: {pred['pick']} | Confidence: {'⭐' * (pred['confidence'] or 3)}")

    # Get leaderboard data
    print("\n🏆 Top ROI Leaders:")
    leaderboard = client.get_leaderboard_data(metric="roi", limit=3)

    for user in leaderboard['rankings']:
        print(f"  #{user['rank']} @{user['username']} - ROI: {user['roi']*100:.1f}%")


def example_webhooks(client: DeveloperClient):
    """Example: Create webhooks for events."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Webhooks")
    print("="*70)

    # Create webhook
    webhook = client.create_webhook(
        url="https://example.com/webhooks/sportsbetlang",
        events=[
            "prediction.created",
            "prediction.settled",
            "leaderboard.updated"
        ]
    )

    if webhook:
        print("\n📝 Webhook created!")
        print(f"  ID: {webhook['id']}")
        print(f"  Events: {', '.join(webhook['events'])}")
        print("\n💡 Use the secret to verify webhook signatures:")
        print(f"  Secret: {webhook['secret']}")

        # Example verification code
        print("\n📚 Signature Verification Example:")
        print("""
def verify_webhook(request_body, signature, secret):
    computed = hmac.new(
        secret.encode(),
        request_body.encode(),
        'sha256'
    ).hexdigest()
    return computed == signature
        """)

    # List webhooks
    print("\n📋 Your Webhooks:")
    webhooks = client.list_webhooks()
    for wh in webhooks['webhooks']:
        status = "✓ Active" if wh['active'] else "✗ Inactive"
        print(f"  {status} | {wh['url']}")
        print(f"      Events: {', '.join(wh['events'])}")
        print(f"      Failures: {wh['failures']} | Last success: {wh['last_success_at'] or 'Never'}")


def example_usage_stats(client: DeveloperClient):
    """Example: View API usage statistics."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Usage Statistics")
    print("="*70)

    stats = client.get_usage_stats(days=30)

    print(f"\n📈 Last 30 Days:")
    print(f"  Total Requests: {stats['total_requests']:,}")
    print(f"  Avg Response Time: {stats['avg_response_time_ms']:.1f}ms")
    print(f"  Unique Endpoints: {stats['unique_endpoints']}")
    print(f"  Active Days: {stats['active_days']}")

    if stats['top_endpoints']:
        print("\n🔥 Top Endpoints:")
        for endpoint in stats['top_endpoints'][:5]:
            print(f"  {endpoint['endpoint']}: {endpoint['count']} requests")

    if stats['status_codes']:
        print("\n📊 Status Codes:")
        for code in stats['status_codes']:
            print(f"  {code['status_code']}: {code['count']} responses")


def example_data_export(client: DeveloperClient):
    """Example: Export custom data."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Custom Data Export")
    print("="*70)

    # Export NBA predictions as JSON
    print("\n📁 Exporting NBA predictions (JSON)...")
    json_export = client.export_custom_data(sport="nba", format="json")
    print(f"  Exported {json_export['count']} predictions")

    # Export as CSV
    print("\n📁 Exporting all predictions (CSV)...")
    csv_export = client.export_custom_data(format="csv")
    print(f"  Exported {csv_export['count']} predictions")
    print(f"  First 200 chars of CSV:\n{csv_export['data'][:200]}...")


def example_rate_limits():
    """Example: Check rate limit information."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Rate Limits & Tiers")
    print("="*70)

    response = requests.get(f"{BASE_URL}/developer/docs/rate-limits")
    tiers = response.json()

    print("\n💎 API Tiers:")
    for tier in tiers['tiers']:
        print(f"\n  {tier['name'].upper()}")
        print(f"  Rate Limit: {tier['rate_limit']}")
        print(f"  Features:")
        for feature in tier['features']:
            print(f"    • {feature}")


def example_webhook_events():
    """Example: List available webhook events."""
    print("\n" + "="*70)
    print("EXAMPLE 7: Webhook Events")
    print("="*70)

    response = requests.get(f"{BASE_URL}/developer/docs/events")
    events = response.json()

    print("\n📡 Available Webhook Events:")
    for event in events['events']:
        print(f"\n  {event['name']}")
        print(f"  {event['description']}")
        print(f"  Payload: {json.dumps(event['payload'], indent=4)}")


def example_python_sdk():
    """Example: Using the Python SDK directly."""
    print("\n" + "="*70)
    print("EXAMPLE 8: Python SDK Usage")
    print("="*70)

    print("\n💻 Direct Python SDK Example:")
    print("""
from sportsbetlang.developer import APIKeyService, WebhookService

# Initialize services
api_keys = APIKeyService()
webhooks = WebhookService()

# Generate API key
key = api_keys.generate_api_key(
    user_id=1,
    name="My App",
    tier="pro"
)

print(f"API Key: {key['key']}")
print(f"Rate Limit: {key['rate_limit']}")

# Create webhook
webhook = webhooks.create_webhook(
    user_id=1,
    api_key_id=key['id'],
    url="https://example.com/webhook",
    events=["prediction.created", "prediction.settled"]
)

print(f"Webhook ID: {webhook['id']}")
print(f"Secret: {webhook['secret']}")

# Trigger webhook (from your app)
webhooks.trigger_webhook(
    event_type="prediction.created",
    payload={
        "prediction_id": 123,
        "user_id": 1,
        "sport": "nba",
        "description": "LeBron Over 27.5 Points"
    }
)
    """)


def main():
    """Run all examples."""
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║     SportsBetLang Developer Features - Usage Examples       ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    print("\n⚠️  Make sure the API server is running:")
    print("   python -m sportsbetlang.api.routes\n")

    try:
        # Create API keys
        client = example_api_key_management()

        if client:
            # Data feeds
            example_data_feeds(client)

            # Webhooks
            example_webhooks(client)

            # Usage stats
            example_usage_stats(client)

            # Data export
            example_data_export(client)

        # Documentation examples
        example_rate_limits()
        example_webhook_events()
        example_python_sdk()

        print("\n╔══════════════════════════════════════════════════════════════╗")
        print("║                    Examples Complete!                        ║")
        print("╚══════════════════════════════════════════════════════════════╝")

        print("\nNext steps:")
        print("  1. View API docs: http://localhost:8000/docs")
        print("  2. Create API keys: POST /developer/keys")
        print("  3. Set up webhooks: POST /developer/webhooks")
        print("  4. Access data feeds: GET /developer/data/*")

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
