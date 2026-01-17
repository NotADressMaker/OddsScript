# SportsBetLang AI Chat Assistant

Natural language interface for sports analytics, predictions, and betting insights powered by Claude AI.

## Features

### 🗣️ Natural Language Queries
Ask questions in plain English and get intelligent, data-driven answers:

```
"Predict LeBron's points tonight"
"Compare Mahomes and Allen this season"
"What's the best bet for tonight's Lakers game?"
"Show me Ohtani's hitting trend over last 10 games"
```

### 📊 Conversational Sports Insights
- Player performance predictions
- Team analytics and comparisons
- Betting strategy recommendations
- Statistical trend analysis
- Historical data exploration

### 🏀 Supported Sports
- **NBA** - Basketball analytics
- **NFL** - Football predictions
- **MLB** - Baseball statistics
- **NHL** - Hockey insights

### 🎯 Core Capabilities

#### 1. Player Predictions
Predict player statistics using advanced models:
- Moving average predictions
- Confidence intervals
- Recent form analysis
- Historical trend weighting

**Example:**
```python
analytics.predict_player_stat(
    sport="nba",
    player_name="LeBron James",
    metric="points"
)
```

**Response:**
```json
{
  "player": "LeBron James",
  "sport": "NBA",
  "metric": "points",
  "prediction": 27.3,
  "confidence_interval": [23.1, 31.5],
  "methodology": "7-game weighted moving average",
  "recent_form": [29.0, 25.5, 31.0, 26.0, 28.5]
}
```

#### 2. Player Comparisons
Compare two players across multiple metrics:

**Example:**
```python
analytics.compare_players(
    sport="nba",
    player1="LeBron James",
    player2="Kevin Durant",
    metrics=["points", "assists", "rebounds"]
)
```

**Response:**
```json
{
  "sport": "NBA",
  "player1": "LeBron James",
  "player2": "Kevin Durant",
  "metrics": {
    "points": {
      "LeBron James": 27.3,
      "Kevin Durant": 29.1,
      "difference": -1.8,
      "advantage": "Kevin Durant"
    },
    "assists": {
      "LeBron James": 8.2,
      "Kevin Durant": 5.1,
      "difference": 3.1,
      "advantage": "LeBron James"
    }
  }
}
```

#### 3. Historical Trend Analysis
Analyze performance trends over recent games:

**Example:**
```python
analytics.analyze_historical_trend(
    sport="nba",
    player_name="Stephen Curry",
    metric="three_pointers",
    games=10
)
```

**Response:**
```json
{
  "player": "Stephen Curry",
  "sport": "NBA",
  "metric": "three_pointers",
  "trend": "improving",
  "trend_strength": "15.3%",
  "recent_average": 5.2,
  "peak": 8,
  "lowest": 2,
  "data": [3, 4, 2, 5, 6, 4, 7, 8, 5, 6]
}
```

## Installation

### 1. Install Dependencies

```bash
# Install API dependencies
pip install -r requirements-api.txt
```

**Required packages:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `anthropic` - Claude AI SDK
- `pydantic` - Data validation

### 2. Set API Key

Get your Anthropic API key from [https://console.anthropic.com](https://console.anthropic.com)

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

Or add to your `~/.bashrc` or `~/.zshrc`:
```bash
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

## Usage

### Option 1: Interactive CLI

```bash
# Start interactive chat
python sportsbetlang/cli/chat_assistant.py

# With custom API key
python sportsbetlang/cli/chat_assistant.py --api-key "your-key"

# Single query mode
python sportsbetlang/cli/chat_assistant.py -q "Predict LeBron's points tonight"
```

**CLI Commands:**
- `/help` - Show help message
- `/history` - View conversation history
- `/clear` - Clear conversation
- `/exit` - Exit chat

### Option 2: REST API Server

```bash
# Start API server
python -m sportsbetlang.api.routes

# Or with uvicorn
uvicorn sportsbetlang.api.routes:app --reload --host 0.0.0.0 --port 8000
```

**API will be available at:**
- Base URL: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- OpenAPI spec: `http://localhost:8000/openapi.json`

### Option 3: Python API

```python
import asyncio
from sportsbetlang.api.chat import ChatService, SportsAnalyticsService

async def main():
    # Initialize services
    chat = ChatService()
    analytics = SportsAnalyticsService()

    # Create session
    session_id = "my-session"
    chat.create_session(session_id)

    # Natural language query
    result = await chat.process_query(
        query="Predict LeBron's points tonight",
        session_id=session_id
    )
    print(result['answer'])

    # Direct prediction
    pred = analytics.predict_player_stat(
        sport="nba",
        player_name="LeBron James",
        metric="points"
    )
    print(f"Prediction: {pred['prediction']}")

asyncio.run(main())
```

## API Endpoints

### POST /chat
Process natural language sports queries

**Request:**
```json
{
  "query": "Predict LeBron's points tonight",
  "session_id": "optional-session-id",
  "context": {}
}
```

**Response:**
```json
{
  "answer": "Based on LeBron James' recent performance...",
  "session_id": "abc-123",
  "timestamp": "2024-01-17T10:30:00",
  "query": "Predict LeBron's points tonight",
  "prediction": {
    "metric": "points",
    "value": "27.3"
  }
}
```

### POST /predict
Get player performance predictions

**Request:**
```json
{
  "sport": "nba",
  "player_name": "LeBron James",
  "metric": "points",
  "historical_data": [29.0, 25.5, 31.0]
}
```

### POST /compare
Compare two players

**Request:**
```json
{
  "sport": "nba",
  "player1": "LeBron James",
  "player2": "Kevin Durant",
  "metrics": ["points", "assists", "rebounds"]
}
```

### POST /trend
Analyze historical trends

**Request:**
```json
{
  "sport": "nba",
  "player_name": "Stephen Curry",
  "metric": "three_pointers",
  "games": 10
}
```

### POST /session/new
Create new conversation session

**Response:**
```json
{
  "session_id": "abc-123",
  "created_at": "2024-01-17T10:30:00"
}
```

### GET /session/{session_id}/history
Get conversation history

### DELETE /session/{session_id}
Clear conversation history

### GET /health
Health check endpoint

## Example Queries

### Basketball (NBA)
```
"Predict LeBron's points tonight"
"Compare Curry and Lillard's three-point shooting"
"What's Giannis' recent scoring trend?"
"Should I bet on the Lakers to win tonight?"
```

### Football (NFL)
```
"Predict Mahomes' passing yards this week"
"Compare Mahomes vs Allen quarterback stats"
"What's the best bet for Chiefs vs Bills?"
"Analyze Derrick Henry's rushing trend"
```

### Baseball (MLB)
```
"Predict Ohtani's home runs tonight"
"Compare Judge vs Ohtani power hitting"
"What's the over/under value for Dodgers game?"
"Show me deGrom's strikeout trend"
```

### Hockey (NHL)
```
"Predict McDavid's points tonight"
"Compare Ovechkin and Matthews goal scoring"
"What's the best bet for tonight's Bruins game?"
"Analyze Matthews' recent scoring form"
```

## Architecture

```
sportsbetlang/
├── api/
│   ├── __init__.py
│   ├── chat.py           # ChatService & SportsAnalyticsService
│   └── routes.py         # FastAPI endpoints
├── cli/
│   └── chat_assistant.py # Interactive CLI
└── ...

examples/
└── chat_examples.py      # Usage examples

docs/
└── AI_CHAT_ASSISTANT.md  # This file
```

### Components

1. **ChatService** - Manages AI conversations with Claude
   - Session management
   - Conversation history
   - Natural language processing
   - Query routing

2. **SportsAnalyticsService** - Sports analytics engine
   - Player predictions
   - Statistical comparisons
   - Trend analysis
   - Historical data processing

3. **FastAPI Routes** - REST API endpoints
   - `/chat` - Natural language queries
   - `/predict` - Direct predictions
   - `/compare` - Player comparisons
   - `/trend` - Trend analysis

## Advanced Usage

### Custom Context
Provide additional context to improve responses:

```python
result = await chat.process_query(
    query="Should I bet on LeBron scoring over 25?",
    session_id=session_id,
    context={
        "game": "Lakers vs Celtics",
        "date": "2024-01-17",
        "odds": {"over_25": -110, "under_25": -110},
        "opponent_defense_rank": 5
    }
)
```

### Historical Data
Provide your own historical data:

```python
# Your actual player data
lebron_recent_points = [29.0, 25.5, 31.0, 26.0, 28.5, 24.0, 30.0]

prediction = analytics.predict_player_stat(
    sport="nba",
    player_name="LeBron James",
    metric="points",
    historical_data=lebron_recent_points
)
```

### Integration with Existing Tools
Combine with SportsBetLang's existing analytics:

```python
from sportsbetlang.common.kelly import kelly_criterion
from sportsbetlang.api.chat import SportsAnalyticsService

analytics = SportsAnalyticsService()

# Get prediction
pred = analytics.predict_player_stat("nba", "LeBron James", "points")
predicted_value = pred['prediction']

# Calculate betting edge
line = 27.5  # Sportsbook line
if predicted_value > line:
    # Calculate optimal bet size using Kelly
    edge = (predicted_value - line) / line
    implied_prob = 0.5  # -110 odds
    win_prob = 0.55  # Your model
    kelly_size = kelly_criterion(win_prob, 2.0, 0.01)
    print(f"Bet {kelly_size * 100}% of bankroll on Over")
```

## Production Deployment

### Environment Variables
```bash
# Required
export ANTHROPIC_API_KEY="your-api-key"

# Optional
export API_HOST="0.0.0.0"
export API_PORT="8000"
export LOG_LEVEL="info"
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install -r requirements-api.txt

ENV ANTHROPIC_API_KEY=""
EXPOSE 8000

CMD ["uvicorn", "sportsbetlang.api.routes:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Security Best Practices
1. Never commit API keys to version control
2. Use environment variables for secrets
3. Enable CORS only for trusted domains in production
4. Implement rate limiting (nginx, CloudFlare, etc.)
5. Use HTTPS in production
6. Implement API authentication for public deployments

## Troubleshooting

### "ANTHROPIC_API_KEY environment variable must be set"
**Solution:** Set your API key:
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

### Import errors
**Solution:** Install dependencies:
```bash
pip install -r requirements-api.txt
```

### "Module 'sportsbetlang' not found"
**Solution:** Run from project root directory:
```bash
cd /path/to/SportsBetLang
python sportsbetlang/cli/chat_assistant.py
```

### API connection errors
**Solution:** Check if server is running:
```bash
curl http://localhost:8000/health
```

## Future Enhancements

- [ ] Real-time game data integration
- [ ] Live odds from multiple sportsbooks
- [ ] Advanced statistical models (Poisson, Monte Carlo)
- [ ] User authentication and personalization
- [ ] Historical bet tracking and performance
- [ ] WebSocket support for live updates
- [ ] Mobile app integration
- [ ] Voice command interface
- [ ] Multi-language support
- [ ] Advanced visualization dashboards

## Contributing

Contributions are welcome! Areas for improvement:
- Enhanced statistical models
- Real-time data source integrations
- Additional sports support
- UI/UX improvements
- Performance optimizations

## License

See main SportsBetLang LICENSE file.

## Support

For issues, questions, or feature requests:
1. Check the [examples](../examples/chat_examples.py)
2. Review the [API docs](http://localhost:8000/docs)
3. Open an issue on GitHub

---

**Built with ❤️ using SportsBetLang and Claude AI**
