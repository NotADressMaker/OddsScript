# Full-Stack Application Guide

Complete guide for using VigScript in full-stack web and mobile applications.

## Overview

VigScript provides a complete REST API that exposes all betting calculations, ML predictions, and database operations. This allows you to build web apps, mobile apps, and integrate with any platform that can make HTTP requests.

**What's Included:**
- REST API with FastAPI
- WebSocket support for real-time updates
- Docker deployment
- Frontend examples (Vanilla JS, React)
- Database persistence
- Production-ready configuration

## Quick Start

### 1. Start the API Server

```bash
# Install API dependencies
pip install -r requirements-api.txt

# Start the server
uvicorn api:app --reload

# API runs at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### 2. Use the API

```javascript
// Calculate Kelly criterion
const response = await fetch('http://localhost:8000/calculate/kelly', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        win_probability: 0.55,
        odds: 2.0
    })
});

const data = await response.json();
console.log(data.kelly_size); // 0.1 (bet 10% of bankroll)
```

## API Reference

### Base URL

```
http://localhost:8000
```

### Interactive Documentation

FastAPI provides automatic interactive documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Core Endpoints

#### 1. Calculate Kelly Criterion

**POST** `/calculate/kelly`

Calculate optimal bet size using Kelly Criterion.

**Request:**
```json
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

#### 2. Calculate Expected Value

**POST** `/calculate/ev`

Calculate expected value of a bet.

**Request:**
```json
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

#### 3. Calculate Edge

**POST** `/calculate/edge`

Calculate betting edge (advantage over bookmaker).

**Request:**
```json
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

#### 4. Analyze Bet (Complete)

**POST** `/analyze/bet`

Complete bet analysis with Kelly, EV, edge, ROI, and recommendation.

**Request:**
```json
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

### Sport Predictions

#### 5. Quick NBA Prediction

**POST** `/predict/nba/quick`

Fast NBA game prediction without training data.

**Request:**
```json
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

#### 6. Quick NFL Prediction

**POST** `/predict/nfl/quick`

Fast NFL game prediction.

**Request:**
```json
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

#### 7. Quick Soccer BTTS Prediction

**POST** `/predict/soccer/btts`

Predict Both Teams To Score.

**Request:**
```json
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

### Database Operations

#### 8. Save Bet

**POST** `/bets/save`

Save a bet to the database.

**Request:**
```json
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

#### 9. Save Bet Result

**POST** `/bets/{bet_id}/result`

Save the outcome of a bet.

**Request:**
```json
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

#### 10. Get Performance Stats

**GET** `/performance?sport=nba&days=30`

Get betting performance statistics.

**Query Parameters:**
- `sport` (optional): Filter by sport
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

#### 11. Save Prediction

**POST** `/predictions/save`

Save a model prediction.

**Request:**
```json
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

#### 12. Get Prediction Accuracy

**GET** `/predictions/accuracy?model=NBA ML Model v1`

Get model accuracy statistics.

**Response:**
```json
{
    "total_predictions": 50,
    "correct_predictions": 32,
    "accuracy": 0.64,
    "avg_confidence": 0.68
}
```

### Utility Endpoints

#### 13. Compare Bets

**POST** `/compare/bets`

Compare multiple betting opportunities.

**Request:**
```json
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

#### 14. Batch Kelly Calculation

**POST** `/batch/kelly`

Calculate Kelly for multiple bets at once.

**Request:**
```json
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

### WebSocket

#### 15. Real-time Updates

**WebSocket** `/ws`

Connect to receive real-time updates.

**JavaScript Example:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Update:', data);
};

// Messages are sent automatically when:
// - New bets are placed
// - Bet results are saved
// - Bankroll changes
```

## Frontend Integration

### Vanilla JavaScript

Complete example in `frontend/index.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>VigScript</title>
</head>
<body>
    <h1>Kelly Calculator</h1>
    <form id="kelly-form">
        <input type="number" id="win-prob" placeholder="Win Probability %" />
        <input type="number" id="odds" placeholder="Decimal Odds" />
        <button type="submit">Calculate</button>
    </form>
    <div id="result"></div>

    <script>
        const API_URL = 'http://localhost:8000';

        document.getElementById('kelly-form').addEventListener('submit', async (e) => {
            e.preventDefault();

            const winProb = document.getElementById('win-prob').value / 100;
            const odds = document.getElementById('odds').value;

            const response = await fetch(`${API_URL}/calculate/kelly`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    win_probability: winProb,
                    odds: parseFloat(odds)
                })
            });

            const data = await response.json();
            document.getElementById('result').innerHTML =
                `Bet ${data.recommended_percentage} of your bankroll`;
        });
    </script>
</body>
</html>
```

### React

Complete components in `frontend/react-example.jsx`:

```jsx
import React, { useState } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

export function BettingCalculator() {
    const [winProb, setWinProb] = useState(55);
    const [odds, setOdds] = useState(2.0);
    const [amount, setAmount] = useState(100);
    const [bankroll, setBankroll] = useState(1000);
    const [results, setResults] = useState(null);

    const analyzeBet = async (e) => {
        e.preventDefault();

        const response = await axios.post(`${API_URL}/analyze/bet`, {
            amount,
            odds,
            win_probability: winProb / 100,
            bankroll
        });

        setResults(response.data);
    };

    return (
        <div>
            <h1>Betting Calculator</h1>
            <form onSubmit={analyzeBet}>
                <input
                    type="number"
                    value={winProb}
                    onChange={(e) => setWinProb(e.target.value)}
                />
                <input
                    type="number"
                    value={odds}
                    onChange={(e) => setOdds(e.target.value)}
                />
                <button type="submit">Analyze Bet</button>
            </form>

            {results && (
                <div>
                    <h2>Results</h2>
                    <p>Kelly: {results.metrics.kelly_percentage}</p>
                    <p>EV: {results.metrics.ev_formatted}</p>
                    <p>Edge: {results.metrics.edge_percentage}</p>
                    <p>Recommendation: {results.recommendation}</p>
                </div>
            )}
        </div>
    );
}
```

### WebSocket Hook

```jsx
import React, { useState, useEffect } from 'react';

export function useWebSocket() {
    const [data, setData] = useState(null);
    const [connected, setConnected] = useState(false);

    useEffect(() => {
        const ws = new WebSocket('ws://localhost:8000/ws');

        ws.onopen = () => {
            console.log('WebSocket connected');
            setConnected(true);
        };

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            setData(message);
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected');
            setConnected(false);
        };

        return () => ws.close();
    }, []);

    return { data, connected };
}

// Usage:
function App() {
    const { data, connected } = useWebSocket();

    return (
        <div>
            <p>Status: {connected ? 'Connected' : 'Disconnected'}</p>
            {data && <p>Latest update: {JSON.stringify(data)}</p>}
        </div>
    );
}
```

## Docker Deployment

### Development

```bash
# Build image
docker build -t sportsbetlang-api .

# Run container
docker run -p 8000:8000 sportsbetlang-api
```

### Production with Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_PATH=/app/data/betting.db
    restart: unless-stopped
```

### Production Configuration

For production, use gunicorn:

```bash
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Add to Dockerfile:**
```dockerfile
CMD ["gunicorn", "api:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

## Environment Variables

Configure the API with environment variables:

```bash
# Database path
DATABASE_PATH=/path/to/betting.db

# API configuration
API_HOST=0.0.0.0
API_PORT=8000

# CORS origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,https://myapp.com
```

**In Python:**
```python
import os

DATABASE_PATH = os.getenv('DATABASE_PATH', 'betting.db')
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', 8000))
```

## Security Considerations

### 1. Authentication

Add authentication to protect endpoints:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != "your-secret-token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return credentials.credentials

@app.post("/analyze/bet", dependencies=[Depends(verify_token)])
async def analyze_bet(request: BetAnalysisRequest):
    # Protected endpoint
    pass
```

### 2. Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

@app.post("/analyze/bet")
@limiter.limit("10/minute")
async def analyze_bet(request: Request, bet_request: BetAnalysisRequest):
    # Limited to 10 requests per minute
    pass
```

### 3. HTTPS

Always use HTTPS in production:

```bash
# Use a reverse proxy like nginx
server {
    listen 443 ssl;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Mobile Apps

### React Native

```javascript
import React, { useState } from 'react';
import { View, TextInput, Button, Text } from 'react-native';

const API_URL = 'https://api.yourdomain.com';

export default function KellyCalculator() {
    const [winProb, setWinProb] = useState('55');
    const [odds, setOdds] = useState('2.0');
    const [result, setResult] = useState(null);

    const calculate = async () => {
        const response = await fetch(`${API_URL}/calculate/kelly`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                win_probability: parseFloat(winProb) / 100,
                odds: parseFloat(odds)
            })
        });

        const data = await response.json();
        setResult(data);
    };

    return (
        <View>
            <TextInput
                value={winProb}
                onChangeText={setWinProb}
                placeholder="Win Probability %"
                keyboardType="numeric"
            />
            <TextInput
                value={odds}
                onChangeText={setOdds}
                placeholder="Decimal Odds"
                keyboardType="numeric"
            />
            <Button title="Calculate" onPress={calculate} />
            {result && (
                <Text>Bet {result.recommended_percentage} of bankroll</Text>
            )}
        </View>
    );
}
```

### Flutter

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

Future<Map<String, dynamic>> calculateKelly(double winProb, double odds) async {
  final response = await http.post(
    Uri.parse('https://api.yourdomain.com/calculate/kelly'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'win_probability': winProb,
      'odds': odds,
    }),
  );

  return jsonDecode(response.body);
}
```

## Complete Workflows

### Workflow 1: Daily Betting Analysis

```javascript
const API_URL = 'http://localhost:8000';

// Today's games
const games = [
    {
        matchup: 'Lakers vs Celtics',
        odds: 2.1,
        team_off_rtg: 115,
        team_def_rtg: 108,
        opp_off_rtg: 112,
        opp_def_rtg: 107
    },
    // ... more games
];

async function analyzeDailyGames() {
    const bankroll = 1000;

    for (const game of games) {
        // Get prediction
        const predResp = await fetch(`${API_URL}/predict/nba/quick`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                team_off_rtg: game.team_off_rtg,
                team_def_rtg: game.team_def_rtg,
                opp_off_rtg: game.opp_off_rtg,
                opp_def_rtg: game.opp_def_rtg,
                home: true
            })
        });
        const prediction = await predResp.json();

        // Analyze bet
        const betResp = await fetch(`${API_URL}/analyze/bet`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                amount: 100,
                odds: game.odds,
                win_probability: prediction.win_probability,
                bankroll: bankroll
            })
        });
        const analysis = await betResp.json();

        // If positive EV, save bet
        if (analysis.expected_value > 0) {
            await fetch(`${API_URL}/bets/save`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    matchup: game.matchup,
                    amount: analysis.recommended_bet,
                    odds: game.odds,
                    predicted_prob: prediction.win_probability,
                    sport: 'nba',
                    notes: `EV: $${analysis.expected_value.toFixed(2)}`
                })
            });

            console.log(`✓ Placed bet on ${game.matchup}`);
        }
    }
}
```

### Workflow 2: Performance Dashboard

```javascript
async function loadPerformanceDashboard() {
    // Get overall performance
    const overallResp = await fetch(`${API_URL}/performance`);
    const overall = await overallResp.json();

    // Get sport-specific performance
    const nbaResp = await fetch(`${API_URL}/performance?sport=nba`);
    const nba = await nbaResp.json();

    // Get model accuracy
    const accuracyResp = await fetch(
        `${API_URL}/predictions/accuracy?model=NBA ML Model v1`
    );
    const accuracy = await accuracyResp.json();

    return {
        overall,
        nba,
        accuracy
    };
}
```

### Workflow 3: Real-time Betting

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
let bankroll = 1000;

ws.onmessage = (event) => {
    const update = JSON.parse(event.data);

    if (update.type === 'bet_result') {
        if (update.won) {
            bankroll += update.profit;
            console.log(`✓ Bet won! +$${update.profit}`);
        } else {
            bankroll -= update.amount;
            console.log(`✗ Bet lost! -$${update.amount}`);
        }

        console.log(`New bankroll: $${bankroll}`);
    }
};

// Place bet
async function placeBet(matchup, odds, winProb) {
    const response = await fetch(`${API_URL}/analyze/bet`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            amount: bankroll * 0.05, // 5% of bankroll
            odds: odds,
            win_probability: winProb,
            bankroll: bankroll
        })
    });

    const analysis = await response.json();

    if (analysis.recommendation.includes('BET')) {
        await fetch(`${API_URL}/bets/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                matchup,
                amount: analysis.recommended_bet,
                odds,
                predicted_prob: winProb,
                sport: 'nba'
            })
        });

        console.log('Bet placed, waiting for result...');
    }
}
```

## Testing the API

### Manual Testing with curl

```bash
# Calculate Kelly
curl -X POST http://localhost:8000/calculate/kelly \
  -H "Content-Type: application/json" \
  -d '{"win_probability": 0.55, "odds": 2.0}'

# Analyze bet
curl -X POST http://localhost:8000/analyze/bet \
  -H "Content-Type: application/json" \
  -d '{"amount": 100, "odds": 2.1, "win_probability": 0.58, "bankroll": 1000}'

# NBA prediction
curl -X POST http://localhost:8000/predict/nba/quick \
  -H "Content-Type: application/json" \
  -d '{"team_off_rtg": 115, "team_def_rtg": 108, "opp_off_rtg": 110, "opp_def_rtg": 109, "home": true}'
```

### Python Tests

```python
import requests

API_URL = 'http://localhost:8000'

# Test Kelly calculation
response = requests.post(f'{API_URL}/calculate/kelly', json={
    'win_probability': 0.55,
    'odds': 2.0
})
print(response.json())

# Test bet analysis
response = requests.post(f'{API_URL}/analyze/bet', json={
    'amount': 100,
    'odds': 2.1,
    'win_probability': 0.58,
    'bankroll': 1000
})
print(response.json())
```

## Troubleshooting

### CORS Issues

If you get CORS errors from the browser:

```python
# In api.py, update CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Database Locked

If you get "database is locked" errors:

```python
# Use connection with longer timeout
import sqlite3
conn = sqlite3.connect('betting.db', timeout=30.0)
```

### Port Already in Use

```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn api:app --port 8001
```

## Best Practices

1. **Use environment variables** for configuration
2. **Enable HTTPS** in production
3. **Add authentication** for sensitive endpoints
4. **Implement rate limiting** to prevent abuse
5. **Log all API requests** for debugging
6. **Monitor performance** with tools like Prometheus
7. **Use connection pooling** for database
8. **Cache frequently accessed data**
9. **Handle errors gracefully** with proper status codes
10. **Document your API** with OpenAPI/Swagger

## Next Steps

1. **Deploy to production** - Use AWS, DigitalOcean, or Heroku
2. **Add authentication** - JWT tokens, OAuth2
3. **Implement caching** - Redis for performance
4. **Add monitoring** - Prometheus, Grafana
5. **Create admin dashboard** - Manage users, view stats
6. **Build mobile apps** - React Native or Flutter
7. **Add notifications** - Email, SMS, push notifications
8. **Integrate with sportsbooks** - Automated bet placement (where legal)

## See Also

- [API Code](../api.py) - Complete API implementation
- [Frontend Examples](../frontend/) - Vanilla JS and React examples
- [Docker Files](../Dockerfile) - Deployment configuration
- [Database Guide](database_guide.md) - Database documentation
- [Simple API Guide](simple_api_guide.md) - Python library usage

---

For more information, see the main [README](../README.md).
