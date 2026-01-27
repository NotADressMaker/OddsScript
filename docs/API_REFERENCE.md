# API Reference

Quick reference for all SportsBetLang API endpoints.

**Base URL:** `http://localhost:8000`

**Interactive Documentation:** http://localhost:8000/docs

## Core Calculations

### Calculate Kelly Criterion

```http
POST /calculate/kelly
Content-Type: application/json

{
    "win_probability": 0.55,
    "odds": 2.0
}
```

**Response:**
```json
{
    "kelly_size": 0.1,
    "recommended_percentage": "10.00%"
}
```

### Calculate Expected Value

```http
POST /calculate/ev
Content-Type: application/json

{
    "win_probability": 0.55,
    "odds": 2.0,
    "bet_amount": 100
}
```

**Response:**
```json
{
    "expected_value": 10.0,
    "ev_formatted": "$10.00"
}
```

### Calculate Edge

```http
POST /calculate/edge
Content-Type: application/json

{
    "win_probability": 0.55,
    "odds": 2.0
}
```

**Response:**
```json
{
    "edge": 0.1,
    "edge_percentage": "10.00%"
}
```

### Analyze Bet (Complete Analysis)

```http
POST /analyze/bet
Content-Type: application/json

{
    "amount": 100,
    "odds": 2.1,
    "win_probability": 0.58,
    "bankroll": 1000
}
```

**Response:**
```json
{
    "kelly_size": 0.15,
    "kelly_percentage": "15.00%",
    "expected_value": 21.8,
    "ev_formatted": "$21.80",
    "edge": 0.218,
    "edge_percentage": "21.80%",
    "roi": 0.218,
    "roi_percentage": "21.80%",
    "recommended_bet": 150.0,
    "bet_too_large": false,
    "recommendation": "STRONG BET - Positive EV",
    "metrics": {
        "kelly_percentage": "15.00%",
        "ev_formatted": "$21.80",
        "edge_percentage": "21.80%",
        "roi_percentage": "21.80%"
    }
}
```

## Sport Predictions

### Quick NBA Prediction

```http
POST /predict/nba/quick
Content-Type: application/json

{
    "team_off_rtg": 115.0,
    "team_def_rtg": 108.0,
    "opp_off_rtg": 110.0,
    "opp_def_rtg": 109.0,
    "home": true
}
```

**Response:**
```json
{
    "win_probability": 0.62,
    "win_percentage": "62.0%"
}
```

### Quick NFL Prediction

```http
POST /predict/nfl/quick
Content-Type: application/json

{
    "team_off_dvoa": 0.15,
    "team_def_dvoa": -0.10,
    "opp_off_dvoa": 0.08,
    "opp_def_dvoa": -0.05,
    "home": true
}
```

**Response:**
```json
{
    "win_probability": 0.58,
    "win_percentage": "58.0%"
}
```

### Quick Soccer BTTS Prediction

```http
POST /predict/soccer/btts
Content-Type: application/json

{
    "team_goals_per_game": 1.8,
    "team_conceded_per_game": 1.2,
    "opp_goals_per_game": 1.5,
    "opp_conceded_per_game": 1.1
}
```

**Response:**
```json
{
    "btts_probability": 0.65,
    "btts_percentage": "65.0%"
}
```

### Quick College Basketball Prediction

```http
POST /predict/cbb/quick
Content-Type: application/json

{
    "team_kenpom_rating": 25.5,
    "opp_kenpom_rating": 18.2,
    "team_adj_em": 20.5,
    "opp_adj_em": 15.2,
    "home": true,
    "conference_game": false,
    "tournament": false
}
```

**Response:**
```json
{
    "win_probability": 0.68,
    "win_percentage": "68.0%",
    "metric": "KenPom Adjusted Efficiency Margin",
    "home_advantage": "6.5%",
    "conference_game": false,
    "tournament": false
}
```

**Notes:**
- Uses KenPom ratings and Adjusted Efficiency Margin
- `tournament`: Set to `true` for March Madness (increases upset potential)
- `conference_game`: Set to `true` for conference matchups (reduces favorite's edge)
- Home court advantage: 6.5% (stronger than NBA)

### Quick College Football Prediction

```http
POST /predict/cfb/quick
Content-Type: application/json

{
    "team_sp_rating": 18.5,
    "opp_sp_rating": 12.3,
    "team_recruiting_rank": 25,
    "opp_recruiting_rank": 50,
    "home": true,
    "rivalry_game": false,
    "conference_game": false
}
```

**Response:**
```json
{
    "win_probability": 0.72,
    "win_percentage": "72.0%",
    "metric": "SP+ Rating",
    "home_advantage": "8%",
    "rivalry_game": false,
    "conference_game": false
}
```

**Notes:**
- Uses SP+ (Success Rate Plus) ratings from Bill Connelly
- `rivalry_game`: Set to `true` for rivalry games (favorites perform worse)
- `conference_game`: Set to `true` for conference matchups
- `team_recruiting_rank`: 247Sports composite rank (1-130)
- Home field advantage: 8% (strongest in major sports)

### Quick WNBA Prediction

```http
POST /predict/wnba/quick
Content-Type: application/json

{
    "team_off_rtg": 105.0,
    "team_def_rtg": 100.0,
    "opp_off_rtg": 102.0,
    "opp_def_rtg": 101.0,
    "home": true,
    "rest_days_team": 2,
    "rest_days_opp": 2
}
```

**Response:**
```json
{
    "win_probability": 0.61,
    "win_percentage": "61.0%",
    "metric": "Net Rating (Off - Def)",
    "home_advantage": "6%",
    "rest_advantage": "0 days"
}
```

**Notes:**
- Uses offensive and defensive ratings (similar to NBA)
- Rest days are important due to compressed WNBA schedule
- Rest advantage kicks in at 2+ day difference
- Home court advantage: 6% (similar to NBA)

## Database Operations

### Save Bet

```http
POST /bets/save
Content-Type: application/json

{
    "matchup": "Lakers vs Celtics",
    "amount": 100,
    "odds": 2.1,
    "predicted_prob": 0.58,
    "sport": "nba",
    "bet_type": "moneyline",
    "notes": "Lakers at home"
}
```

**Response:**
```json
{
    "bet_id": 1,
    "message": "Bet saved successfully"
}
```

### Save Bet Result

```http
POST /bets/{bet_id}/result
Content-Type: application/json

{
    "won": true,
    "actual_odds": 2.1
}
```

**Response:**
```json
{
    "success": true,
    "profit": 110.0
}
```

### Get Performance Stats

```http
GET /performance?sport=nba&days=30
```

**Query Parameters:**
- `sport` (optional): Filter by sport (nba, nfl, mlb, etc.)
- `days` (optional): Filter by last N days

**Response:**
```json
{
    "total_bets": 47,
    "wins": 26,
    "losses": 21,
    "pending": 0,
    "win_rate": 0.553,
    "total_wagered": 4750.0,
    "total_profit": 342.5,
    "roi": 0.0721,
    "biggest_win": 185.0,
    "biggest_loss": -150.0,
    "avg_winning_odds": 2.15
}
```

### Save Prediction

```http
POST /predictions/save
Content-Type: application/json

{
    "matchup": "Warriors vs Nets",
    "predicted_value": 1,
    "predicted_prob": 0.65,
    "sport": "nba",
    "prediction_type": "game_winner",
    "model_used": "NBA ML Model v1"
}
```

**Response:**
```json
{
    "prediction_id": 1,
    "message": "Prediction saved successfully"
}
```

### Get Prediction Accuracy

```http
GET /predictions/accuracy?model=NBA ML Model v1
```

**Response:**
```json
{
    "total_predictions": 50,
    "correct_predictions": 32,
    "accuracy": 0.64,
    "avg_confidence": 0.68
}
```

## Utility Endpoints

### Compare Bets

```http
POST /compare/bets
Content-Type: application/json

{
    "bets": [
        {
            "name": "Lakers ML",
            "amount": 100,
            "odds": 2.1,
            "win_probability": 0.58,
            "bankroll": 1000
        },
        {
            "name": "Celtics ML",
            "amount": 100,
            "odds": 1.85,
            "win_probability": 0.60,
            "bankroll": 1000
        }
    ]
}
```

**Response:**
```json
{
    "comparisons": [
        {
            "name": "Lakers ML",
            "kelly_size": 0.15,
            "ev": 21.8,
            "edge": 0.218,
            "roi": 0.218,
            "recommendation": "STRONG BET"
        },
        {
            "name": "Celtics ML",
            "kelly_size": 0.18,
            "ev": 11.0,
            "edge": 0.11,
            "roi": 0.11,
            "recommendation": "VALUE BET"
        }
    ],
    "best_bet": "Lakers ML"
}
```

### Batch Kelly Calculation

```http
POST /batch/kelly
Content-Type: application/json

{
    "bets": [
        {"win_probability": 0.55, "odds": 2.0},
        {"win_probability": 0.60, "odds": 1.85},
        {"win_probability": 0.52, "odds": 2.2}
    ]
}
```

**Response:**
```json
{
    "results": [
        {"kelly_size": 0.1, "recommended_percentage": "10.00%"},
        {"kelly_size": 0.18, "recommended_percentage": "18.15%"},
        {"kelly_size": 0.08, "recommended_percentage": "7.73%"}
    ]
}
```

## WebSocket

### Real-time Updates

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
    console.log('Connected to SportsBetLang WebSocket');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === 'bet_placed') {
        console.log('New bet:', data);
    } else if (data.type === 'bet_result') {
        console.log('Bet result:', data);
    } else if (data.type === 'bankroll_update') {
        console.log('Bankroll updated:', data);
    }
};
```

**Message Types:**
- `bet_placed` - When a new bet is saved
- `bet_result` - When a bet result is recorded
- `bankroll_update` - When bankroll changes
- `prediction` - When a prediction is made

## Status Codes

- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (bet/prediction doesn't exist)
- `422` - Validation Error (Pydantic validation failed)
- `500` - Internal Server Error

## Error Response Format

```json
{
    "detail": "Error message here"
}
```

## Examples

### cURL

```bash
# Calculate Kelly
curl -X POST http://localhost:8000/calculate/kelly \
  -H "Content-Type: application/json" \
  -d '{"win_probability": 0.55, "odds": 2.0}'

# Analyze bet
curl -X POST http://localhost:8000/analyze/bet \
  -H "Content-Type: application/json" \
  -d '{"amount": 100, "odds": 2.1, "win_probability": 0.58, "bankroll": 1000}'
```

### JavaScript (fetch)

```javascript
const response = await fetch('http://localhost:8000/calculate/kelly', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        win_probability: 0.55,
        odds: 2.0
    })
});

const data = await response.json();
console.log(data.kelly_size);
```

### Python (requests)

```python
import requests

response = requests.post('http://localhost:8000/calculate/kelly', json={
    'win_probability': 0.55,
    'odds': 2.0
})

print(response.json()['kelly_size'])
```

### React

```jsx
import axios from 'axios';

const analyzeBet = async () => {
    const response = await axios.post('http://localhost:8000/analyze/bet', {
        amount: 100,
        odds: 2.1,
        win_probability: 0.58,
        bankroll: 1000
    });

    console.log(response.data.recommendation);
};
```

## Rate Limits

Currently no rate limits are enforced. For production, implement rate limiting based on your needs.

## Authentication

Currently no authentication is required. For production, add authentication to protect endpoints.

## CORS

CORS is enabled for all origins in development. For production, configure specific origins in `api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## See Also

- [Full-Stack Guide](FULLSTACK_GUIDE.md) - Complete guide with examples and workflows
- [Frontend Examples](../frontend/) - Vanilla JS and React examples
- [Database Guide](database_guide.md) - Database operations
- [API Code](../api.py) - API implementation

---

For interactive documentation, visit http://localhost:8000/docs when the API is running.
