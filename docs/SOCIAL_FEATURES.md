## SportsBetLang Social Features

Community-driven predictions, leaderboards, discussions, and analyst following.

## Overview

The Social Features module turns SportsBetLang into a complete social betting platform where users can:
- Share predictions and track performance
- Compete on leaderboards
- Discuss strategies in forums
- Follow top analysts and experts
- Build reputation and credibility

## Features

### 👤 User Accounts & Profiles
- User registration and authentication
- JWT token-based security
- Public profiles with stats
- Analyst tier system (Amateur, Pro, Expert)
- Verified badges

### 📊 User-Generated Predictions
- Post betting predictions for any sport
- Track prediction history and performance
- Confidence ratings (1-5 stars)
- Detailed reasoning and analysis
- Automatic stats tracking (win rate, ROI, streak)

### 🏆 Community Leaderboards
- Global and sport-specific rankings
- Multiple metrics (ROI, win rate, profit, streak)
- Minimum prediction thresholds
- Time-based periods (daily, weekly, monthly, all-time)
- Top analysts showcase

### 💬 Discussion Threads
- Create discussion topics
- Categorized forums (strategy, analysis, picks, general)
- Tag system for organization
- View counts and engagement metrics
- Pinned and locked threads

### 👥 Social Following
- Follow top analysts and experts
- Activity feeds from followed users
- Follower/following counts
- Social proof and credibility

### ❤️ Engagement
- Like predictions and discussions
- Comment on posts
- Threaded conversations
- Engagement metrics

## Architecture

```
sportsbetlang/
├── social/
│   ├── __init__.py
│   ├── database.py       # SQLite schema and ORM
│   ├── auth.py          # Authentication & user management
│   └── services.py      # Business logic services
└── api/
    └── social_routes.py # FastAPI endpoints

Database: SQLite (sportsbetlang_social.db)
```

### Database Schema

**Tables:**
- `users` - User accounts and profiles
- `user_stats` - Performance statistics
- `predictions` - User predictions
- `discussions` - Discussion threads
- `comments` - Comments on predictions/discussions
- `follows` - User following relationships
- `likes` - Likes on content
- `activities` - Activity feed
- `leaderboard_snapshots` - Historical rankings

## Installation

### Dependencies

```bash
pip install -r requirements-api.txt
```

**Required:**
- `pyjwt>=2.8.0` - JWT authentication
- `fastapi>=0.104.0` - API framework
- `pydantic>=2.5.0` - Data validation
- `email-validator>=2.1.0` - Email validation

### Database Setup

The database is automatically created on first use. To manually initialize:

```python
from sportsbetlang.social.database import get_database

db = get_database()  # Creates sportsbetlang_social.db
```

## Quick Start

### 1. Start API Server

```bash
python -m sportsbetlang.api.routes
```

API will be available at `http://localhost:8000`

### 2. Register an Account

```bash
curl -X POST http://localhost:8000/social/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "sharpbettor",
    "email": "sharp@example.com",
    "password": "securepass123",
    "display_name": "Sharp Bettor"
  }'
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "username": "sharpbettor",
    "email": "sharp@example.com",
    "display_name": "Sharp Bettor",
    "is_analyst": false,
    "created_at": "2024-01-17T10:30:00"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "message": "Registration successful"
}
```

### 3. Create a Prediction

```bash
curl -X POST http://localhost:8000/social/predictions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "sport": "nba",
    "prediction_type": "player_prop",
    "description": "LeBron James Over 27.5 Points",
    "pick": "Over 27.5",
    "odds": -110,
    "stake": 100,
    "confidence": 4,
    "reasoning": "LeBron averaging 29.2 PPG over last 5 games"
  }'
```

### 4. View Leaderboard

```bash
curl http://localhost:8000/social/leaderboard?metric=roi&limit=10
```

## API Reference

### Authentication

#### POST /social/auth/register
Register a new user account.

**Request:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "display_name": "string (optional)",
  "bio": "string (optional)"
}
```

**Response:**
```json
{
  "user": {User object},
  "token": "JWT token",
  "message": "Registration successful"
}
```

#### POST /social/auth/login
Login and get JWT token.

**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "user": {User object},
  "token": "JWT token",
  "message": "Login successful"
}
```

#### GET /social/auth/me
Get current user profile (requires authentication).

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
{
  "id": 1,
  "username": "sharpbettor",
  "display_name": "Sharp Bettor",
  "total_predictions": 50,
  "correct_predictions": 32,
  "win_rate": 0.64,
  "roi": 0.12,
  "current_streak": 5,
  "followers_count": 25,
  "following_count": 10
}
```

### Predictions

#### POST /social/predictions
Create a new prediction (requires authentication).

**Request:**
```json
{
  "sport": "nba|nfl|mlb|nhl",
  "prediction_type": "player_prop|game_outcome|spread|total",
  "description": "string",
  "pick": "string",
  "odds": -110,
  "stake": 100,
  "confidence": 4,
  "reasoning": "string",
  "game_id": "string (optional)",
  "game_date": "2024-01-17 (optional)"
}
```

#### GET /social/predictions/feed
Get recent predictions from all users.

**Query Params:**
- `sport` (optional): Filter by sport
- `limit` (default: 50): Number of predictions
- `offset` (default: 0): Pagination offset

#### GET /social/predictions/user/{username}
Get predictions for a specific user.

**Query Params:**
- `status` (optional): Filter by status (pending, won, lost)
- `limit` (default: 50)
- `offset` (default: 0)

#### PUT /social/predictions/{id}/settle
Settle a prediction (requires authentication, owner only).

**Request:**
```json
{
  "status": "won|lost|void",
  "result": 90.91
}
```

### Discussions

#### POST /social/discussions
Create a discussion thread (requires authentication).

**Request:**
```json
{
  "title": "string",
  "content": "string",
  "category": "general|strategy|picks|analysis",
  "sport": "nba|nfl|mlb|nhl (optional)",
  "tags": ["string"] (optional)
}
```

#### GET /social/discussions
Get discussion threads.

**Query Params:**
- `category` (optional): Filter by category
- `sport` (optional): Filter by sport
- `limit` (default: 50)
- `offset` (default: 0)

#### GET /social/discussions/{id}
Get a specific discussion.

#### POST /social/discussions/{id}/comments
Add a comment to a discussion (requires authentication).

**Request:**
```json
{
  "content": "string"
}
```

#### GET /social/discussions/{id}/comments
Get comments for a discussion.

### Predictions Comments

#### POST /social/predictions/{id}/comments
Add a comment to a prediction (requires authentication).

#### GET /social/predictions/{id}/comments
Get comments for a prediction.

### Following

#### POST /social/users/{username}/follow
Follow a user (requires authentication).

**Response:**
```json
{
  "status": "success",
  "follower_id": 1,
  "following_id": 2
}
```

#### DELETE /social/users/{username}/follow
Unfollow a user (requires authentication).

#### GET /social/users/{username}/followers
Get a user's followers.

#### GET /social/users/{username}/following
Get users that a user follows.

#### GET /social/feed
Get activity feed from followed users (requires authentication).

**Query Params:**
- `limit` (default: 50)

### Leaderboards

#### GET /social/leaderboard
Get community leaderboard.

**Query Params:**
- `metric` (default: roi): Ranking metric
  - `roi` - Return on investment
  - `win_rate` - Win percentage
  - `total_profit` - Total profit/loss
  - `streak` - Current winning streak
- `sport` (optional): Filter by sport
- `period` (default: all_time): Time period
  - `daily`, `weekly`, `monthly`, `all_time`
- `min_predictions` (default: 10): Minimum predictions to qualify
- `limit` (default: 100): Number of users

**Response:**
```json
[
  {
    "rank": 1,
    "id": 5,
    "username": "sharpbettor",
    "display_name": "Sharp Bettor",
    "is_analyst": true,
    "total_predictions": 150,
    "win_rate": 0.64,
    "roi": 0.18,
    "total_profit_loss": 2700,
    "current_streak": 8,
    "reputation_score": 1250
  }
]
```

#### GET /social/leaderboard/analysts
Get top performing analysts.

**Query Params:**
- `limit` (default: 10)

### Likes

#### POST /social/{type}/{id}/like
Like a prediction, discussion, or comment (requires authentication).

**Path Params:**
- `type`: `prediction`, `discussion`, or `comment`
- `id`: Target ID

#### DELETE /social/{type}/{id}/like
Unlike content (requires authentication).

### Users

#### GET /social/users/{username}
Get user profile by username.

**Response:**
```json
{
  "id": 1,
  "username": "sharpbettor",
  "display_name": "Sharp Bettor",
  "bio": "Professional sports bettor | NBA specialist",
  "is_analyst": true,
  "analyst_tier": "expert",
  "verified": true,
  "total_predictions": 150,
  "win_rate": 0.64,
  "roi": 0.18,
  "followers_count": 1250,
  "following_count": 45
}
```

## Python Client Usage

### Registration and Authentication

```python
from sportsbetlang.social import AuthService

auth = AuthService()

# Register
user = auth.create_user(
    username="sharpbettor",
    email="sharp@example.com",
    password="securepass123",
    display_name="Sharp Bettor"
)

# Login
user = auth.authenticate("sharpbettor", "securepass123")

# Generate token
token = auth.create_token(user['id'])

# Verify token
user_id = auth.verify_token(token)
```

### Creating Predictions

```python
from sportsbetlang.social import PredictionService

predictions = PredictionService()

# Create prediction
prediction = predictions.create_prediction(
    user_id=1,
    sport="nba",
    prediction_type="player_prop",
    description="LeBron James Over 27.5 Points",
    pick="Over 27.5",
    odds=-110,
    stake=100,
    confidence=4,
    reasoning="Strong recent form, favorable matchup"
)

# Settle prediction
settled = predictions.settle_prediction(
    prediction_id=prediction['id'],
    status='won',
    result=90.91  # Profit
)

# Get user predictions
user_preds = predictions.get_user_predictions(
    user_id=1,
    status='pending'
)
```

### Discussions and Comments

```python
from sportsbetlang.social import DiscussionService

discussions = DiscussionService()

# Create discussion
discussion = discussions.create_discussion(
    user_id=1,
    title="Best NBA betting strategies",
    content="What strategies work best for you?",
    category="strategy",
    sport="nba",
    tags=["strategy", "nba"]
)

# Add comment
comment = discussions.add_comment(
    user_id=2,
    parent_type='discussion',
    parent_id=discussion['id'],
    content="Great topic! I focus on pace-adjusted stats."
)

# Get comments
comments = discussions.get_comments('discussion', discussion['id'])
```

### Following and Feeds

```python
from sportsbetlang.social import FollowService

follows = FollowService()

# Follow user
follows.follow_user(follower_id=1, following_id=2)

# Get followers
followers = follows.get_followers(user_id=2)

# Get following
following = follows.get_following(user_id=1)

# Get activity feed
feed = follows.get_feed(user_id=1, limit=50)
```

### Leaderboards

```python
from sportsbetlang.social import LeaderboardService

leaderboard = LeaderboardService()

# Get ROI leaderboard
top_roi = leaderboard.get_leaderboard(
    metric='roi',
    min_predictions=20,
    limit=100
)

# Get sport-specific leaderboard
nba_leaders = leaderboard.get_leaderboard(
    metric='roi',
    sport='nba',
    min_predictions=10
)

# Get top analysts
analysts = leaderboard.get_top_analysts(limit=10)
```

## Advanced Features

### Analyst Tier System

Users can be promoted to analyst status with different tiers:

```python
auth = AuthService()

# Promote to analyst
user = auth.promote_to_analyst(
    user_id=1,
    tier='expert'  # 'amateur', 'pro', 'expert'
)
```

**Tiers:**
- **Amateur**: New analysts, building reputation
- **Pro**: Proven track record (50+ predictions, 55%+ win rate)
- **Expert**: Elite analysts (100+ predictions, 60%+ win rate, high ROI)

### Reputation System

Users earn reputation through:
- Winning predictions (+10 per win)
- High confidence wins (+20 bonus)
- Followers (+5 per follower)
- Engagement (likes, comments)
- Streak bonuses (+50 at 10 streak, +100 at 20 streak)

### Performance Metrics

Tracked automatically for each user:
- **Total Predictions**: Count of all predictions
- **Correct Predictions**: Number of wins
- **Win Rate**: Percentage of winning predictions
- **ROI**: Return on investment (profit / wagered)
- **Total Profit/Loss**: Net profit or loss
- **Current Streak**: Consecutive wins (resets on loss)
- **Best Streak**: Highest win streak achieved
- **Units Wagered**: Total amount staked

## Security

### Authentication Flow

1. User registers → receives JWT token
2. Token included in `Authorization` header for protected endpoints
3. Token expires after 7 days
4. Passwords hashed with SHA-256 + salt

### Best Practices

- **Never** commit database files to git
- Use strong passwords (min 6 characters)
- Validate all user input
- Rate limit API endpoints in production
- Use HTTPS in production
- Implement email verification for registration
- Add 2FA for analyst accounts

## Examples

See `examples/social_examples.py` for complete usage examples:

```bash
# Run examples (requires API server running)
python examples/social_examples.py
```

**Examples include:**
1. User registration and authentication
2. Creating and settling predictions
3. Discussion threads and comments
4. Following analysts
5. Viewing leaderboards
6. Predictions feed
7. Engagement (likes, comments)
8. Activity feeds

## Testing

### Clear Test Data

```python
from sportsbetlang.social.database import get_database

db = get_database()
db.clear_all_data()  # WARNING: Deletes all data
```

### Seed Sample Data

```python
from sportsbetlang.social import AuthService, PredictionService

auth = AuthService()
predictions = PredictionService()

# Create test user
user = auth.create_user("testuser", "test@example.com", "password")

# Create test predictions
for i in range(10):
    predictions.create_prediction(
        user_id=user['id'],
        sport="nba",
        prediction_type="player_prop",
        description=f"Test prediction {i}",
        pick="Over",
        stake=100,
        confidence=3
    )
```

## Future Enhancements

- [ ] Real-time notifications (WebSockets)
- [ ] Private messaging between users
- [ ] Badges and achievements system
- [ ] Contest/challenge creation
- [ ] Analytics dashboard
- [ ] Export data (CSV, JSON)
- [ ] Advanced search and filtering
- [ ] User blocking/reporting
- [ ] Moderator roles
- [ ] API rate limiting
- [ ] Email notifications
- [ ] Mobile app integration

## Troubleshooting

### "sqlite3.OperationalError: database is locked"
Multiple processes accessing database. Use connection pooling or queue writes.

### "401 Unauthorized"
Token expired or invalid. Login again to get new token.

### "Already following this user"
Duplicate follow attempt. Check if already following before calling API.

### Performance with large datasets
Add indexes, implement pagination, consider PostgreSQL for production.

## Support

For issues, questions, or feature requests:
1. Check the [examples](../examples/social_examples.py)
2. Review the [API docs](http://localhost:8000/docs)
3. Open an issue on GitHub

---

**Built with ❤️ for the SportsBetLang betting community**
