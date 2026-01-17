# Quick Start: AI Chat Assistant

Get started with SportsBetLang's AI-powered chat assistant in 5 minutes!

## 1. Install Dependencies

```bash
pip install -r requirements-api.txt
```

This installs:
- FastAPI (web framework)
- Anthropic SDK (Claude AI)
- Uvicorn (server)
- Pydantic (data validation)

## 2. Get Your API Key

1. Go to [https://console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in
3. Create an API key
4. Copy your key

## 3. Set Environment Variable

**Linux/Mac:**
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

**Windows (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY='your-api-key-here'
```

**Permanent (add to ~/.bashrc or ~/.zshrc):**
```bash
echo 'export ANTHROPIC_API_KEY="your-key"' >> ~/.bashrc
source ~/.bashrc
```

## 4. Choose Your Interface

### Option A: Interactive CLI (Recommended for First-Time Users)

```bash
python sportsbetlang/cli/chat_assistant.py
```

**Try these queries:**
```
Predict LeBron's points tonight
Compare Mahomes and Allen this season
What's the best bet for tonight's Lakers game?
Show me Ohtani's hitting trend
```

**CLI Commands:**
- `/help` - Show help
- `/history` - View chat history
- `/clear` - Clear conversation
- `/exit` - Quit

### Option B: Single Query Mode

```bash
python sportsbetlang/cli/chat_assistant.py -q "Predict LeBron's points tonight"
```

### Option C: REST API Server

```bash
# Start server
python -m sportsbetlang.api.routes

# Visit interactive docs
open http://localhost:8000/docs
```

**Test with curl:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Predict LeBron points tonight",
    "session_id": "test-session"
  }'
```

### Option D: Python Script

```python
import asyncio
from sportsbetlang.api.chat import ChatService, SportsAnalyticsService

async def main():
    # Initialize
    chat = ChatService()
    analytics = SportsAnalyticsService()

    # Create session
    session_id = "demo"
    chat.create_session(session_id)

    # Natural language query
    result = await chat.process_query(
        "Predict LeBron's points tonight",
        session_id
    )
    print(result['answer'])

    # Direct analytics
    pred = analytics.predict_player_stat("nba", "LeBron James", "points")
    print(f"Prediction: {pred['prediction']}")

asyncio.run(main())
```

## 5. Run Examples

```bash
python examples/chat_examples.py
```

This demonstrates:
- Natural language queries
- Player predictions
- Player comparisons
- Historical trend analysis
- Conversational context
- API usage patterns

## Example Interactions

### 🏀 Basketball (NBA)

**You:** Predict LeBron's points tonight

**Assistant:** Based on LeBron James' recent performance over his last 7 games, I predict he will score approximately **27.3 points** tonight.

**Analysis:**
- Recent 5-game average: 28.0 points
- Confidence interval: 23.1 - 31.5 points
- Trend: Consistent scoring with slight upward trajectory
- Recent form: [29.0, 25.5, 31.0, 26.0, 28.5]

**Methodology:** 7-game weighted moving average with higher weight on recent games

---

**You:** Compare LeBron and Durant

**Assistant:** Here's a comprehensive comparison of LeBron James and Kevin Durant:

**Points per game:**
- LeBron James: 27.3
- Kevin Durant: 29.1
- Advantage: Kevin Durant (+1.8)

**Assists per game:**
- LeBron James: 8.2
- Kevin Durant: 5.1
- Advantage: LeBron James (+3.1)

**Rebounds per game:**
- LeBron James: 9.1
- Kevin Durant: 7.3
- Advantage: LeBron James (+1.8)

**Overall:** LeBron excels in playmaking and rebounding, while Durant has a slight edge in scoring.

### 🏈 Football (NFL)

**You:** Predict Mahomes passing yards this week

**Assistant:** Patrick Mahomes is projected to throw for **298.5 yards** this week.

**Analysis:**
- Recent 5-game average: 287.2 yards
- Confidence interval: 265.0 - 332.0 yards
- Trend: Improving (+8.5% last 5 games)
- Peak: 358 yards | Lowest: 241 yards

### ⚾ Baseball (MLB)

**You:** Show me Ohtani's home run trend

**Assistant:** Shohei Ohtani's home run trend over his last 10 games:

**Trend Analysis:**
- Trend: Improving (+12.3%)
- Recent average: 0.8 HR per game
- Peak: 2 | Lowest: 0
- Data: [0, 1, 0, 1, 2, 1, 0, 1, 1, 1]

Ohtani is showing an upward trend in power hitting, with increased frequency of home runs in recent games.

## API Endpoints Quick Reference

### Chat
```bash
POST /chat
Body: {"query": "your question", "session_id": "optional"}
```

### Predict
```bash
POST /predict
Body: {"sport": "nba", "player_name": "LeBron James", "metric": "points"}
```

### Compare
```bash
POST /compare
Body: {"sport": "nba", "player1": "LeBron", "player2": "Durant", "metrics": ["points"]}
```

### Trend
```bash
POST /trend
Body: {"sport": "nba", "player_name": "Curry", "metric": "three_pointers", "games": 10}
```

### Session Management
```bash
POST /session/new                    # Create session
GET /session/{id}/history           # Get history
DELETE /session/{id}                # Clear session
```

### Health Check
```bash
GET /health
```

## Supported Features

### Sports
- ✅ NBA (Basketball)
- ✅ NFL (Football)
- ✅ MLB (Baseball)
- ✅ NHL (Hockey)

### Metrics

**NBA:** points, assists, rebounds, steals, blocks, three_pointers

**NFL:** passing_yards, rushing_yards, touchdowns, receptions, completions

**MLB:** hits, runs, rbis, home_runs, strikeouts, walks

**NHL:** goals, assists, points, shots, saves, plus_minus

### Capabilities
- ✅ Player performance predictions
- ✅ Statistical comparisons
- ✅ Historical trend analysis
- ✅ Conversational context
- ✅ Natural language queries
- ✅ Betting insights
- ✅ Confidence intervals
- ✅ Recent form analysis

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
```bash
# Check if set
echo $ANTHROPIC_API_KEY

# Set it
export ANTHROPIC_API_KEY='your-key'
```

### "ModuleNotFoundError: No module named 'fastapi'"
```bash
pip install -r requirements-api.txt
```

### "Permission denied" when running CLI
```bash
chmod +x sportsbetlang/cli/chat_assistant.py
python sportsbetlang/cli/chat_assistant.py
```

### API server won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Use different port
uvicorn sportsbetlang.api.routes:app --port 8080
```

## Next Steps

1. **Explore the full documentation:** `docs/AI_CHAT_ASSISTANT.md`
2. **Try different sports:** NBA, NFL, MLB, NHL
3. **Integrate with your app:** Use the Python API or REST endpoints
4. **Customize predictions:** Provide your own historical data
5. **Build betting strategies:** Combine with SportsBetLang's Kelly criterion and analytics

## Need Help?

- **Documentation:** `docs/AI_CHAT_ASSISTANT.md`
- **Examples:** `examples/chat_examples.py`
- **API Docs:** `http://localhost:8000/docs` (when server running)
- **Issues:** Open a GitHub issue

---

**Ready to get started?**

```bash
export ANTHROPIC_API_KEY='your-key'
python sportsbetlang/cli/chat_assistant.py
```

Type: `Predict LeBron's points tonight` and press Enter!

🎉 **Enjoy SportsBetLang AI Chat!**
