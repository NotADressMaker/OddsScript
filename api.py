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

class TrainModelRequest(BaseModel):
    sport: str
    model_type: str
    training_data: List[Dict]
    test_data: List[Dict]

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
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
