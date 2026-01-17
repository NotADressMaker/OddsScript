# SportsBetLang Developer API

Complete API access for third-party developers to build apps, integrations, and custom solutions.

## Quick Start

### 1. Create an Account

```bash
curl -X POST http://localhost:8000/social/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "developer",
    "email": "dev@example.com",
    "password": "securepass123"
  }'
```

Save your JWT token from the response.

### 2. Generate an API Key

```bash
curl -X POST http://localhost:8000/developer/keys \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My App",
    "tier": "free"
  }'
```

**Save the API key!** It's only shown once.

### 3. Make API Requests

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  http://localhost:8000/developer/data/predictions?sport=nba&limit=10
```

## API Tiers

| Tier | Rate Limit | Features | Price |
|------|-----------|----------|-------|
| **Free** | 1,000/day | Basic endpoints, 3 webhooks | Free |
| **Pro** | 100,000/day | All endpoints, unlimited webhooks, exports | $99/month |
| **Enterprise** | Unlimited | White-label, SLA, dedicated support | Custom |

## Authentication

Two methods:

### 1. User Authentication (JWT)
For managing your developer account:

```python
headers = {"Authorization": "Bearer YOUR_JWT_TOKEN"}
```

### 2. API Key Authentication
For production API access:

```python
headers = {"X-API-Key": "sbl_your_api_key_here"}
```

## Core Endpoints

### API Keys

```bash
# Create key
POST /developer/keys
{
  "name": "My App",
  "tier": "pro",
  "expires_days": 365
}

# List keys
GET /developer/keys

# Revoke key
DELETE /developer/keys/{key_id}

# Rotate key
POST /developer/keys/{key_id}/rotate

# Usage stats
GET /developer/keys/usage?days=30
```

### Webhooks

```bash
# Create webhook
POST /developer/webhooks
{
  "url": "https://example.com/webhook",
  "events": ["prediction.created", "prediction.settled"]
}

# List webhooks
GET /developer/webhooks

# Delete webhook
DELETE /developer/webhooks/{webhook_id}
```

**Webhook Events:**
- `prediction.created` - New prediction posted
- `prediction.settled` - Prediction result
- `discussion.created` - New discussion
- `comment.created` - New comment
- `leaderboard.updated` - Rankings changed
- `user.followed` - User followed

**Signature Verification:**
```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    computed = hmac.new(
        secret.encode(),
        payload.encode(),
        'sha256'
    ).hexdigest()
    return computed == signature
```

### Data Feeds

```bash
# Predictions feed
GET /developer/data/predictions?sport=nba&limit=100

# Leaderboard data
GET /developer/data/leaderboard?metric=roi&limit=100

# Discussions feed
GET /developer/data/discussions?category=strategy

# Custom export
POST /developer/data/export
{
  "sport": "nba",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "format": "csv"
}
```

## White-Label Solutions (Enterprise)

Build custom-branded sports betting platforms:

```bash
POST /developer/whitelabel
{
  "domain": "mybettingapp.com",
  "brand_name": "My Betting App",
  "logo_url": "https://example.com/logo.png",
  "primary_color": "#FF6B00",
  "features": ["predictions", "leaderboards", "chat"]
}
```

## Rate Limiting

Rate limits are enforced per API key, per day.

**Headers:**
```
X-RateLimit-Limit: 100000
X-RateLimit-Remaining: 99950
X-RateLimit-Reset: 1705536000
```

**Over Limit Response:**
```json
{
  "error": "Rate limit exceeded",
  "limit": 1000,
  "reset_at": "2024-01-18T00:00:00Z"
}
```

## Python SDK Example

```python
from sportsbetlang.developer import APIKeyService, WebhookService

# Initialize
api_keys = APIKeyService()

# Create key
key = api_keys.generate_api_key(
    user_id=1,
    name="Production App",
    tier="pro"
)

print(f"Key: {key['key']}")
print(f"Limit: {key['rate_limit']}/day")

# Webhooks
webhooks = WebhookService()

webhook = webhooks.create_webhook(
    user_id=1,
    api_key_id=key['id'],
    url="https://example.com/webhook",
    events=["prediction.created"]
)

# Trigger webhook (internal use)
webhooks.trigger_webhook(
    event_type="prediction.created",
    payload={"prediction_id": 123}
)
```

## Complete Example

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Login
response = requests.post(f"{BASE_URL}/social/auth/login", json={
    "username": "developer",
    "password": "password"
})
token = response.json()['token']

# 2. Create API key
response = requests.post(
    f"{BASE_URL}/developer/keys",
    headers={"Authorization": f"Bearer {token}"},
    json={"name": "My App", "tier": "free"}
)
api_key = response.json()['key']

# 3. Use API key
response = requests.get(
    f"{BASE_URL}/developer/data/predictions",
    headers={"X-API-Key": api_key},
    params={"sport": "nba", "limit": 10}
)
predictions = response.json()

for pred in predictions['predictions']:
    print(f"{pred['username']}: {pred['description']}")
```

## Security Best Practices

1. **Never expose API keys** in client-side code
2. **Use environment variables** for keys
3. **Rotate keys regularly** (quarterly recommended)
4. **Verify webhook signatures** always
5. **Use HTTPS** in production
6. **Rate limit your own apps** to avoid bans
7. **Monitor usage** via dashboard

## Error Handling

```python
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        print("Invalid API key")
    elif e.response.status_code == 429:
        print("Rate limit exceeded")
    else:
        print(f"Error: {e}")
```

## Support

- **Documentation**: http://localhost:8000/docs
- **Rate Limits**: GET /developer/docs/rate-limits
- **Webhook Events**: GET /developer/docs/events
- **Examples**: `examples/developer_examples.py`

---

**Ready to build? Get your API key at http://localhost:8000/docs**
