# Quick Start: Social Features

Get started with SportsBetLang's social betting community in 5 minutes.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements-api.txt
```

### 2. Start API Server

```bash
python -m sportsbetlang.api.routes
```

Server runs at `http://localhost:8000`

**API Documentation:** http://localhost:8000/docs

## Your First Prediction

### Step 1: Register

```bash
curl -X POST http://localhost:8000/social/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "mybettor",
    "email": "me@example.com",
    "password": "mypassword123",
    "display_name": "My Bettor Name"
  }'
```

**Save your token from the response!**

### Step 2: Create a Prediction

```bash
curl -X POST http://localhost:8000/social/predictions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "sport": "nba",
    "prediction_type": "player_prop",
    "description": "LeBron James Over 27.5 Points",
    "pick": "Over 27.5",
    "odds": -110,
    "stake": 100,
    "confidence": 4,
    "reasoning": "LeBron averaging 29 PPG in last 5 games"
  }'
```

### Step 3: Settle Your Prediction

After the game, mark it as won or lost:

```bash
# If you won
curl -X PUT http://localhost:8000/social/predictions/1/settle \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "status": "won",
    "result": 90.91
  }'
```

### Step 4: Check the Leaderboard

```bash
curl http://localhost:8000/social/leaderboard?metric=roi&limit=10
```

## Common Tasks

### View Recent Predictions

```bash
# All sports
curl http://localhost:8000/social/predictions/feed

# NBA only
curl http://localhost:8000/social/predictions/feed?sport=nba
```

### Follow a Top Analyst

```bash
curl -X POST http://localhost:8000/social/users/sharpbettor/follow \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Start a Discussion

```bash
curl -X POST http://localhost:8000/social/discussions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "title": "Best strategies for NBA player props?",
    "content": "What strategies work best for you?",
    "category": "strategy",
    "sport": "nba",
    "tags": ["strategy", "nba", "props"]
  }'
```

### Add a Comment

```bash
curl -X POST http://localhost:8000/social/predictions/1/comments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "content": "Great pick! I was thinking the same thing."
  }'
```

### Like a Prediction

```bash
curl -X POST http://localhost:8000/social/prediction/1/like \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Python Examples

### Using the Python API

```python
from sportsbetlang.social import (
    AuthService,
    PredictionService,
    LeaderboardService
)

# Register
auth = AuthService()
user = auth.create_user(
    username="mybettor",
    email="me@example.com",
    password="password123"
)

token = auth.create_token(user['id'])

# Create prediction
predictions = PredictionService()
pred = predictions.create_prediction(
    user_id=user['id'],
    sport="nba",
    prediction_type="player_prop",
    description="LeBron Over 27.5 Points",
    pick="Over 27.5",
    odds=-110,
    stake=100,
    confidence=4
)

# View leaderboard
leaderboard = LeaderboardService()
top_users = leaderboard.get_leaderboard(metric='roi')

print(f"Top user: {top_users[0]['username']}")
print(f"ROI: {top_users[0]['roi'] * 100:.1f}%")
```

### Run Complete Examples

```bash
python examples/social_examples.py
```

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/social/auth/register` | POST | Register new user |
| `/social/auth/login` | POST | Login and get token |
| `/social/predictions` | POST | Create prediction |
| `/social/predictions/feed` | GET | View recent predictions |
| `/social/leaderboard` | GET | View leaderboard |
| `/social/discussions` | POST | Create discussion |
| `/social/users/{user}/follow` | POST | Follow user |

## Interactive API Docs

Visit http://localhost:8000/docs for interactive API documentation where you can:
- Test all endpoints
- See request/response schemas
- Try authentication
- Explore all features

## Key Concepts

### Predictions
- **Status**: `pending`, `won`, `lost`, `void`
- **Confidence**: 1-5 stars
- **Types**: player_prop, game_outcome, spread, total

### Leaderboard Metrics
- **ROI**: Return on investment (profit / wagered)
- **Win Rate**: Percentage of winning predictions
- **Streak**: Current consecutive wins
- **Total Profit**: Net profit/loss

### Analyst Tiers
- **Amateur**: Building reputation
- **Pro**: Proven track record
- **Expert**: Elite performance

## Tips for Success

1. **Be Consistent**: Post predictions regularly
2. **Add Reasoning**: Explain your picks to build credibility
3. **Engage**: Comment on others' predictions
4. **Track Everything**: Always settle your predictions
5. **Follow Top Analysts**: Learn from the best
6. **Join Discussions**: Share and learn strategies

## Troubleshooting

**"401 Unauthorized"**
- Your token expired or is invalid
- Login again to get a new token

**"Cannot connect"**
- Make sure API server is running
- Check that you're using http://localhost:8000

**"Already exists"**
- Username or email already taken
- Try a different username

## Next Steps

1. **Read Full Documentation**: [SOCIAL_FEATURES.md](docs/SOCIAL_FEATURES.md)
2. **Try Examples**: `python examples/social_examples.py`
3. **Explore API**: http://localhost:8000/docs
4. **Join Community**: Start posting predictions!

## Support

Questions? Check out:
- [Full Documentation](docs/SOCIAL_FEATURES.md)
- [API Reference](http://localhost:8000/docs)
- [Example Code](examples/social_examples.py)

---

**Ready to climb the leaderboard? Start posting predictions!** 🚀
