#!/usr/bin/env python3
"""
SportsBetLang REST API

Full-stack ready API for betting analytics, ML predictions, and database tracking.
Built with FastAPI for modern web/mobile app integration.

Features:
- REST API endpoints for all SportsBetLang features
- WebSocket support for real-time updates
- CORS enabled for frontend integration
- JSON responses
- API documentation (Swagger/OpenAPI)
- Authentication ready
- Works with React, Vue, Angular, mobile apps

Usage:
    # Start server
    uvicorn api:app --reload

    # Or with Docker
    docker build -t sportsbetlang-api .
    docker run -p 8000:8000 sportsbetlang-api

    # Access API docs
    http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

# Import SportsBetLang
from lib import (
    SBL, Bet, Compare,
    EasySportModel, quick_nba_prediction, quick_nfl_prediction, quick_soccer_btts,
    BettingDatabase, create_database,
    train_and_predict
)

# Create FastAPI app
app = FastAPI(
    title="SportsBetLang API",
    description="REST API for sports betting analytics, ML predictions, and tracking",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
db = create_database("api_betting.db")

# WebSocket manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# ============================================================================
# Pydantic Models (Request/Response schemas)
# ============================================================================

class KellyRequest(BaseModel):
    win_probability: float = Field(..., ge=0, le=1, description="Win probability (0-1)")
    odds: float = Field(..., gt=1, description="Decimal odds")

class EVRequest(BaseModel):
    win_probability: float = Field(..., ge=0, le=1)
    odds: float = Field(..., gt=1)
    bet_amount: float = Field(..., gt=0)

class BetAnalysisRequest(BaseModel):
    amount: float = Field(..., gt=0)
    odds: float = Field(..., gt=1)
    win_probability: float = Field(..., ge=0, le=1)
    bankroll: Optional[float] = Field(None, gt=0)

class SaveBetRequest(BaseModel):
    matchup: str
    amount: float = Field(..., gt=0)
    odds: float = Field(..., gt=1)
    predicted_prob: Optional[float] = Field(None, ge=0, le=1)
    sport: Optional[str] = None
    bet_type: Optional[str] = None
    notes: Optional[str] = None

class BetResultRequest(BaseModel):
    bet_id: int
    won: bool
    actual_odds: Optional[float] = None

class PredictionRequest(BaseModel):
    matchup: str
    predicted_value: float
    predicted_prob: Optional[float] = None
    sport: Optional[str] = None
    prediction_type: Optional[str] = None
    model_used: Optional[str] = None
    confidence: Optional[float] = None
    features: Optional[Dict] = None

class QuickNBAPredictionRequest(BaseModel):
    team_off_rtg: float
    team_def_rtg: float
    opp_off_rtg: float
    opp_def_rtg: float
    home: bool = True
    rest_team: int = 2
    rest_opp: int = 2
    pace: float = 100.0

class QuickNFLPredictionRequest(BaseModel):
    team_dvoa: float
    opp_dvoa: float
    home: bool = True
    temperature: float = 70
    wind_speed: float = 5

class QuickNHLPredictionRequest(BaseModel):
    team_xg_for: float
    team_xg_against: float
    opp_xg_for: float
    opp_xg_against: float
    home: bool = True

class QuickMLBPredictionRequest(BaseModel):
    team_rating: float
    opp_rating: float
    home: bool = True
    park_factor: float = 1.0

class QuickHorseRacingRequest(BaseModel):
    speed_rating: float
    post_position: int
    distance: float
    surface: str = 'dirt'

class TrainModelRequest(BaseModel):
    sport: str
    model_type: str
    training_data: List[Dict]
    test_data: List[Dict]

class BetRecommendationRequest(BaseModel):
    bankroll: float = Field(..., gt=0)
    risk_tolerance: str = Field('medium', description='low, medium, high')
    min_edge: float = Field(0.02, ge=0, le=1)
    games: List[Dict] = Field(..., description='List of games with predictions')

# ============================================================================
# Health & Info Endpoints
# ============================================================================

@app.get("/")
async def root():
    """API root - basic info"""
    return {
        "name": "SportsBetLang API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ============================================================================
# Betting Calculations
# ============================================================================

@app.post("/calculate/kelly")
async def calculate_kelly(request: KellyRequest):
    """
    Calculate Kelly Criterion bet size

    Returns optimal bet size as percentage of bankroll
    """
    kelly = SBL.kelly(request.win_probability, request.odds)
    return {
        "kelly_size": kelly,
        "recommended_percentage": f"{kelly:.2%}",
        "input": {
            "win_probability": request.win_probability,
            "odds": request.odds
        }
    }

@app.post("/calculate/ev")
async def calculate_ev(request: EVRequest):
    """Calculate Expected Value"""
    ev = SBL.ev(request.win_probability, request.odds, request.bet_amount)
    roi = SBL.roi(request.win_probability, request.odds)

    return {
        "expected_value": ev,
        "roi": roi,
        "roi_percentage": f"{roi:.2%}",
        "input": request.dict()
    }

@app.post("/calculate/edge")
async def calculate_edge(request: KellyRequest):
    """Calculate betting edge"""
    edge = SBL.edge(request.win_probability, request.odds)

    return {
        "edge": edge,
        "edge_percentage": f"{edge:.2%}",
        "positive_edge": edge > 0
    }

@app.post("/analyze/bet")
async def analyze_bet(request: BetAnalysisRequest):
    """
    Complete bet analysis

    Returns Kelly, EV, edge, ROI, and recommendation
    """
    kelly = SBL.kelly(request.win_probability, request.odds)
    ev = SBL.ev(request.win_probability, request.odds, request.amount)
    edge = SBL.edge(request.win_probability, request.odds)
    roi = SBL.roi(request.win_probability, request.odds)

    recommendation = "PASS"
    if edge > 0.05:  # 5% edge
        recommendation = "STRONG BET"
    elif edge > 0.02:  # 2% edge
        recommendation = "VALUE BET"
    elif edge > 0:
        recommendation = "SLIGHT VALUE"

    result = {
        "kelly_size": kelly,
        "expected_value": ev,
        "edge": edge,
        "roi": roi,
        "recommendation": recommendation,
        "metrics": {
            "kelly_percentage": f"{kelly:.2%}",
            "ev_formatted": f"${ev:+.2f}",
            "edge_percentage": f"{edge:.2%}",
            "roi_percentage": f"{roi:.2%}"
        }
    }

    if request.bankroll:
        result["recommended_bet"] = request.bankroll * kelly * 0.5  # 1/2 Kelly

    return result

# ============================================================================
# Quick Predictions
# ============================================================================

@app.post("/predict/nba/quick")
async def predict_nba_quick(request: QuickNBAPredictionRequest):
    """Quick NBA game prediction (no training needed)"""
    prob = quick_nba_prediction(
        request.team_off_rtg, request.team_def_rtg,
        request.opp_off_rtg, request.opp_def_rtg,
        request.home, request.rest_team, request.rest_opp, request.pace
    )

    return {
        "win_probability": prob,
        "win_percentage": f"{prob:.1%}",
        "confidence": "medium",
        "input": request.dict()
    }

@app.post("/predict/nfl/quick")
async def predict_nfl_quick(request: QuickNFLPredictionRequest):
    """Quick NFL game prediction with weather"""
    prob = quick_nfl_prediction(
        request.team_dvoa, request.opp_dvoa,
        request.home, request.temperature, request.wind_speed
    )

    return {
        "win_probability": prob,
        "win_percentage": f"{prob:.1%}",
        "weather_considered": True,
        "input": request.dict()
    }

@app.post("/predict/soccer/btts")
async def predict_soccer_btts(
    team_goals_avg: float,
    opp_goals_avg: float,
    team_clean_sheets: float = 0.35,
    opp_clean_sheets: float = 0.35
):
    """Soccer Both Teams To Score prediction"""
    prob = quick_soccer_btts(
        team_goals_avg, opp_goals_avg,
        team_clean_sheets, opp_clean_sheets
    )

    return {
        "btts_probability": prob,
        "btts_percentage": f"{prob:.1%}",
        "recommended": prob > 0.5
    }

@app.post("/predict/nhl/quick")
async def predict_nhl_quick(request: QuickNHLPredictionRequest):
    """Quick NHL game prediction using Expected Goals (xG)"""
    try:
        from lib.easy_sport_models import quick_nhl_prediction
        prob = quick_nhl_prediction(
            request.team_xg_for, request.team_xg_against,
            request.opp_xg_for, request.opp_xg_against,
            request.home
        )
    except ImportError:
        # Fallback calculation
        team_goal_diff = request.team_xg_for - request.team_xg_against
        opp_goal_diff = request.opp_xg_for - request.opp_xg_against
        diff = team_goal_diff - opp_goal_diff
        home_advantage = 0.1 if request.home else -0.1
        prob = 0.5 + (diff / 10) + home_advantage
        prob = max(0.1, min(0.9, prob))

    return {
        "win_probability": prob,
        "win_percentage": f"{prob:.1%}",
        "metric": "Expected Goals (xG)",
        "input": request.dict()
    }

@app.post("/predict/mlb/quick")
async def predict_mlb_quick(request: QuickMLBPredictionRequest):
    """Quick MLB game prediction with park factors"""
    try:
        from lib.easy_sport_models import quick_mlb_prediction
        prob = quick_mlb_prediction(
            request.team_rating, request.opp_rating,
            request.home, request.park_factor
        )
    except ImportError:
        # Fallback calculation
        rating_diff = request.team_rating - request.opp_rating
        home_advantage = 0.05 if request.home else -0.05
        park_effect = (request.park_factor - 1.0) * 0.03
        prob = 0.5 + (rating_diff / 100) + home_advantage + park_effect
        prob = max(0.1, min(0.9, prob))

    return {
        "win_probability": prob,
        "win_percentage": f"{prob:.1%}",
        "park_factor": request.park_factor,
        "input": request.dict()
    }

@app.post("/predict/horse-racing/quick")
async def predict_horse_racing_quick(request: QuickHorseRacingRequest):
    """Quick horse racing win probability prediction"""
    # Simple speed rating + post position model
    base_prob = 1.0 / 12  # Assume 12 horse field
    speed_factor = request.speed_rating / 100

    # Post position penalty (worse for outside posts)
    post_penalty = 0
    if request.post_position > 8:
        post_penalty = (request.post_position - 8) * 0.02
    elif request.post_position == 1:
        post_penalty = 0.01  # Rail bias

    # Distance factor
    distance_factor = 0
    if request.distance > 1.25:  # Long distance
        distance_factor = -0.01

    # Surface bonus (dirt is standard)
    surface_bonus = 0.01 if request.surface == 'turf' else 0

    prob = base_prob + speed_factor + surface_bonus - post_penalty + distance_factor
    prob = max(0.01, min(0.95, prob))

    return {
        "win_probability": prob,
        "win_percentage": f"{prob:.1%}",
        "speed_rating": request.speed_rating,
        "post_position": request.post_position,
        "input": request.dict()
    }

# ============================================================================
# Database - Bets
# ============================================================================

@app.post("/bets")
async def save_bet(request: SaveBetRequest):
    """Save a bet to database"""
    bet_id = db.save_bet(
        matchup=request.matchup,
        amount=request.amount,
        odds=request.odds,
        predicted_prob=request.predicted_prob,
        sport=request.sport,
        bet_type=request.bet_type,
        notes=request.notes
    )

    # Broadcast to WebSocket clients
    await manager.broadcast({
        "type": "bet_placed",
        "bet_id": bet_id,
        "matchup": request.matchup,
        "amount": request.amount
    })

    return {"bet_id": bet_id, "status": "saved"}

@app.put("/bets/{bet_id}/result")
async def update_bet_result(bet_id: int, request: BetResultRequest):
    """Update bet result"""
    db.save_result(request.bet_id, request.won, request.actual_odds)

    # Broadcast result
    await manager.broadcast({
        "type": "bet_result",
        "bet_id": bet_id,
        "won": request.won
    })

    return {"status": "updated"}

@app.get("/bets")
async def get_bets(
    sport: Optional[str] = None,
    result: Optional[str] = None,
    limit: Optional[int] = 100
):
    """Get bets from database"""
    bets = db.get_bets(sport=sport, result=result, limit=limit)
    return {"bets": bets, "count": len(bets)}

@app.get("/bets/{bet_id}")
async def get_bet(bet_id: int):
    """Get specific bet"""
    bets = db.get_bets(limit=1000)  # Get all and filter
    bet = next((b for b in bets if b['id'] == bet_id), None)

    if not bet:
        raise HTTPException(status_code=404, detail="Bet not found")

    return bet

# ============================================================================
# Database - Predictions
# ============================================================================

@app.post("/predictions")
async def save_prediction(request: PredictionRequest):
    """Save a prediction"""
    pred_id = db.save_prediction(
        matchup=request.matchup,
        predicted_value=request.predicted_value,
        predicted_prob=request.predicted_prob,
        sport=request.sport,
        prediction_type=request.prediction_type,
        model_used=request.model_used,
        confidence=request.confidence,
        features=request.features
    )

    return {"prediction_id": pred_id, "status": "saved"}

@app.get("/predictions")
async def get_predictions(
    sport: Optional[str] = None,
    model: Optional[str] = None,
    limit: Optional[int] = 100
):
    """Get predictions"""
    predictions = db.get_predictions(sport=sport, model=model, limit=limit)
    return {"predictions": predictions, "count": len(predictions)}

@app.get("/predictions/accuracy")
async def get_prediction_accuracy(
    sport: Optional[str] = None,
    model: Optional[str] = None
):
    """Get prediction accuracy stats"""
    accuracy = db.get_prediction_accuracy(sport=sport, model=model)
    return accuracy

# ============================================================================
# Performance Analytics
# ============================================================================

@app.get("/performance")
async def get_performance(sport: Optional[str] = None, days: Optional[int] = None):
    """Get betting performance statistics"""
    stats = db.get_performance(sport=sport, days=days)
    return stats

@app.get("/bankroll")
async def get_bankroll():
    """Get current bankroll"""
    bankroll = db.get_bankroll()
    if bankroll is None:
        return {"bankroll": None, "message": "No bankroll data"}
    return {"bankroll": bankroll}

@app.post("/bankroll")
async def update_bankroll(amount: float, change: Optional[float] = None, reason: Optional[str] = None):
    """Update bankroll"""
    db.update_bankroll(amount, change, reason)

    # Broadcast update
    await manager.broadcast({
        "type": "bankroll_update",
        "amount": amount,
        "change": change
    })

    return {"status": "updated", "bankroll": amount}

@app.get("/bankroll/history")
async def get_bankroll_history(limit: Optional[int] = 50):
    """Get bankroll history"""
    history = db.get_bankroll_history(limit=limit)
    return {"history": history, "count": len(history)}

# ============================================================================
# WebSocket for Real-time Updates
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates

    Clients receive updates for:
    - New bets placed
    - Bet results
    - Bankroll changes
    - Performance updates
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # Echo back or handle commands
            await websocket.send_json({"status": "received", "message": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ============================================================================
# Batch Operations
# ============================================================================

@app.post("/batch/analyze")
async def batch_analyze(bets: List[BetAnalysisRequest]):
    """Analyze multiple bets at once"""
    results = []

    for bet in bets:
        kelly = SBL.kelly(bet.win_probability, bet.odds)
        ev = SBL.ev(bet.win_probability, bet.odds, bet.amount)
        edge = SBL.edge(bet.win_probability, bet.odds)

        results.append({
            "amount": bet.amount,
            "odds": bet.odds,
            "kelly": kelly,
            "ev": ev,
            "edge": edge
        })

    return {"results": results, "count": len(results)}

# ============================================================================
# Comparison
# ============================================================================

@app.post("/compare")
async def compare_bets(
    bets: List[Dict[str, Any]],
    bankroll: float = 1000
):
    """
    Compare multiple bets

    bets format: [{"name": "Bet A", "prob": 0.58, "odds": 2.1}, ...]
    """
    comp = Compare(bankroll=bankroll)

    for bet in bets:
        comp.add(bet['name'], prob=bet['prob'], odds=bet['odds'])

    # Get best bet by edge
    best = comp.best('edge')

    # Calculate metrics for all
    results = []
    for bet in bets:
        kelly = SBL.kelly(bet['prob'], bet['odds'])
        ev = SBL.ev(bet['prob'], bet['odds'], 100)
        edge = SBL.edge(bet['prob'], bet['odds'])

        results.append({
            "name": bet['name'],
            "probability": bet['prob'],
            "odds": bet['odds'],
            "kelly": kelly,
            "ev": ev,
            "edge": edge,
            "is_best": bet['name'] == best
        })

    return {
        "bets": results,
        "best_bet": best,
        "bankroll": bankroll
    }

# ============================================================================
# Advanced Features
# ============================================================================

@app.post("/recommendations")
async def get_bet_recommendations(request: BetRecommendationRequest):
    """
    Get bet recommendations based on bankroll and risk tolerance

    Analyzes all games and returns recommended bets with sizing
    """
    recommendations = []

    # Kelly multiplier based on risk tolerance
    kelly_multiplier = {
        'low': 0.25,      # Quarter Kelly (conservative)
        'medium': 0.5,    # Half Kelly (balanced)
        'high': 0.75      # Three-quarter Kelly (aggressive)
    }.get(request.risk_tolerance, 0.5)

    for game in request.games:
        # Extract game data
        matchup = game.get('matchup', 'Unknown')
        win_prob = game.get('win_probability', game.get('prob'))
        odds = game.get('odds')

        if not win_prob or not odds:
            continue

        # Calculate metrics
        edge = SBL.edge(win_prob, odds)

        # Only recommend if edge meets minimum
        if edge >= request.min_edge:
            kelly = SBL.kelly(win_prob, odds)
            adjusted_kelly = kelly * kelly_multiplier
            bet_amount = request.bankroll * adjusted_kelly
            ev = SBL.ev(win_prob, odds, bet_amount)

            # Determine strength
            if edge >= 0.10:
                strength = "EXCELLENT"
            elif edge >= 0.05:
                strength = "STRONG"
            elif edge >= 0.03:
                strength = "GOOD"
            else:
                strength = "FAIR"

            recommendations.append({
                "matchup": matchup,
                "win_probability": win_prob,
                "odds": odds,
                "edge": edge,
                "edge_percentage": f"{edge:.2%}",
                "kelly": kelly,
                "adjusted_kelly": adjusted_kelly,
                "bet_amount": round(bet_amount, 2),
                "expected_value": round(ev, 2),
                "strength": strength,
                "confidence": game.get('confidence', 'medium')
            })

    # Sort by edge (best first)
    recommendations.sort(key=lambda x: x['edge'], reverse=True)

    # Calculate total recommended risk
    total_risk = sum(r['bet_amount'] for r in recommendations)
    risk_percentage = (total_risk / request.bankroll) * 100

    return {
        "recommendations": recommendations,
        "count": len(recommendations),
        "total_risk": round(total_risk, 2),
        "risk_percentage": f"{risk_percentage:.1f}%",
        "bankroll": request.bankroll,
        "risk_tolerance": request.risk_tolerance,
        "kelly_multiplier": kelly_multiplier
    }

@app.post("/arbitrage/detect")
async def detect_arbitrage(
    odds_list: List[Dict[str, float]],
    stake: float = 100
):
    """
    Detect arbitrage opportunities across multiple bookmakers

    odds_list format: [{"book": "BookA", "team1": 2.1, "team2": 2.0}, ...]
    """
    if len(odds_list) < 2:
        return {"arbitrage": False, "message": "Need at least 2 books to compare"}

    # Find best odds for each outcome
    best_odds = {}
    for book_odds in odds_list:
        book = book_odds.get('book', 'Unknown')
        for outcome, odds in book_odds.items():
            if outcome == 'book':
                continue
            if outcome not in best_odds or odds > best_odds[outcome]['odds']:
                best_odds[outcome] = {'odds': odds, 'book': book}

    # Calculate implied probabilities
    total_implied_prob = sum(1/v['odds'] for v in best_odds.values())

    # Check for arbitrage
    is_arb = total_implied_prob < 1.0

    if is_arb:
        # Calculate optimal stakes
        profit_margin = (1 / total_implied_prob) - 1
        stakes = {}
        payouts = {}

        for outcome, data in best_odds.items():
            # Stake proportional to inverse odds
            stake_fraction = (1 / data['odds']) / total_implied_prob
            outcome_stake = stake * stake_fraction
            stakes[outcome] = round(outcome_stake, 2)
            payouts[outcome] = round(outcome_stake * data['odds'], 2)

        guaranteed_profit = min(payouts.values()) - stake

        return {
            "arbitrage": True,
            "profit_margin": f"{profit_margin:.2%}",
            "total_stake": stake,
            "guaranteed_profit": round(guaranteed_profit, 2),
            "roi": f"{(guaranteed_profit/stake)*100:.2f}%",
            "bets": [
                {
                    "outcome": outcome,
                    "book": data['book'],
                    "odds": data['odds'],
                    "stake": stakes[outcome],
                    "payout": payouts[outcome]
                }
                for outcome, data in best_odds.items()
            ]
        }
    else:
        return {
            "arbitrage": False,
            "total_implied_probability": f"{total_implied_prob:.2%}",
            "margin": f"{(total_implied_prob - 1)*100:.2f}%",
            "message": "No arbitrage opportunity found"
        }

@app.post("/export/bets")
async def export_bets(
    format: str = 'json',
    sport: Optional[str] = None,
    days: Optional[int] = None
):
    """
    Export betting data

    Supported formats: json, csv
    """
    bets = db.get_bets(sport=sport, limit=10000)

    # Filter by days if specified
    if days:
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(days=days)
        bets = [b for b in bets if datetime.fromisoformat(b['date']) >= cutoff]

    if format == 'csv':
        # Convert to CSV format
        if not bets:
            return {"data": "", "format": "csv", "count": 0}

        # Get headers from first bet
        headers = list(bets[0].keys())
        csv_lines = [','.join(headers)]

        for bet in bets:
            values = [str(bet.get(h, '')) for h in headers]
            csv_lines.append(','.join(values))

        csv_data = '\n'.join(csv_lines)

        return {
            "data": csv_data,
            "format": "csv",
            "count": len(bets),
            "filename": f"bets_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    else:
        # JSON format (default)
        return {
            "data": bets,
            "format": "json",
            "count": len(bets),
            "filename": f"bets_{datetime.now().strftime('%Y%m%d')}.json"
        }

@app.get("/statistics/summary")
async def get_statistics_summary():
    """Get comprehensive statistics summary"""
    overall_perf = db.get_performance()
    bankroll_current = db.get_bankroll()
    bankroll_history = db.get_bankroll_history(limit=100)

    # Calculate additional metrics
    total_bets = overall_perf.get('total_bets', 0)
    win_rate = overall_perf.get('win_rate', 0)
    roi = overall_perf.get('roi', 0)

    # Sport breakdown
    sports_stats = {}
    for sport in ['nba', 'nfl', 'nhl', 'mlb', 'soccer']:
        sport_perf = db.get_performance(sport=sport)
        if sport_perf.get('total_bets', 0) > 0:
            sports_stats[sport] = {
                "total_bets": sport_perf.get('total_bets', 0),
                "win_rate": sport_perf.get('win_rate', 0),
                "roi": sport_perf.get('roi', 0),
                "profit": sport_perf.get('total_profit', 0)
            }

    # Bankroll growth
    bankroll_growth = 0
    if len(bankroll_history) >= 2:
        start = bankroll_history[-1]['amount']
        current = bankroll_history[0]['amount']
        if start > 0:
            bankroll_growth = ((current - start) / start)

    return {
        "overall": {
            "total_bets": total_bets,
            "win_rate": win_rate,
            "win_rate_percentage": f"{win_rate:.1%}",
            "roi": roi,
            "roi_percentage": f"{roi:.1%}",
            "total_profit": overall_perf.get('total_profit', 0),
            "total_wagered": overall_perf.get('total_wagered', 0)
        },
        "bankroll": {
            "current": bankroll_current,
            "growth": bankroll_growth,
            "growth_percentage": f"{bankroll_growth:.1%}",
            "history_points": len(bankroll_history)
        },
        "by_sport": sports_stats,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/statistics/trends")
async def get_trends(days: int = 30):
    """Get betting trends over time"""
    from datetime import datetime, timedelta

    # Get recent bets
    all_bets = db.get_bets(limit=10000)
    cutoff = datetime.now() - timedelta(days=days)

    recent_bets = [
        b for b in all_bets
        if datetime.fromisoformat(b['date']) >= cutoff
    ]

    # Group by day
    daily_stats = {}
    for bet in recent_bets:
        date = bet['date'].split('T')[0]  # Get date part only

        if date not in daily_stats:
            daily_stats[date] = {
                'bets': 0,
                'wins': 0,
                'wagered': 0,
                'profit': 0
            }

        daily_stats[date]['bets'] += 1
        daily_stats[date]['wagered'] += bet['amount']

        if bet['result'] == 'won':
            daily_stats[date]['wins'] += 1
            profit = bet['amount'] * (bet['odds'] - 1)
            daily_stats[date]['profit'] += profit
        elif bet['result'] == 'lost':
            daily_stats[date]['profit'] -= bet['amount']

    # Calculate cumulative profit
    sorted_dates = sorted(daily_stats.keys())
    cumulative_profit = 0
    trends = []

    for date in sorted_dates:
        stats = daily_stats[date]
        cumulative_profit += stats['profit']
        win_rate = stats['wins'] / stats['bets'] if stats['bets'] > 0 else 0

        trends.append({
            'date': date,
            'bets': stats['bets'],
            'wins': stats['wins'],
            'win_rate': win_rate,
            'wagered': round(stats['wagered'], 2),
            'profit': round(stats['profit'], 2),
            'cumulative_profit': round(cumulative_profit, 2)
        })

    return {
        "trends": trends,
        "days": days,
        "total_bets": len(recent_bets),
        "overall_profit": round(cumulative_profit, 2)
    }

# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
