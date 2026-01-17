"""
FastAPI Routes for SportsBetLang AI Chat Assistant

Provides REST API endpoints for conversational sports analytics.
"""

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from .chat import ChatService, SportsAnalyticsService
from .social_routes import social_router

# Initialize FastAPI app
app = FastAPI(
    title="SportsBetLang API",
    description="Natural language sports analytics and social betting community",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
chat_service = None
analytics_service = SportsAnalyticsService()


# Pydantic models for request/response
class ChatRequest(BaseModel):
    """Chat query request."""
    query: str = Field(..., description="Natural language sports query")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context data")


class ChatResponse(BaseModel):
    """Chat query response."""
    answer: str
    session_id: str
    timestamp: str
    query: str
    prediction: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class PlayerPredictionRequest(BaseModel):
    """Player performance prediction request."""
    sport: str = Field(..., description="Sport league (nba, nfl, mlb, nhl)")
    player_name: str = Field(..., description="Player's full name")
    metric: str = Field(..., description="Statistic to predict")
    historical_data: Optional[List[float]] = Field(None, description="Recent performance data")


class PlayerComparisonRequest(BaseModel):
    """Player comparison request."""
    sport: str
    player1: str
    player2: str
    metrics: Optional[List[str]] = None


class TrendAnalysisRequest(BaseModel):
    """Historical trend analysis request."""
    sport: str
    player_name: str
    metric: str
    games: int = Field(10, description="Number of recent games to analyze")


class SessionResponse(BaseModel):
    """Session creation response."""
    session_id: str
    created_at: str


# Helper function to initialize chat service
def get_chat_service() -> ChatService:
    """Get or initialize chat service."""
    global chat_service
    if chat_service is None:
        try:
            chat_service = ChatService()
        except ValueError as e:
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )
    return chat_service


# API Routes

@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "SportsBetLang AI Chat API",
        "version": "1.0.0",
        "endpoints": [
            "/chat",
            "/predict",
            "/compare",
            "/trend",
            "/session/new",
            "/session/{session_id}/history"
        ]
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a natural language sports query.

    Example queries:
    - "Predict LeBron's points tonight"
    - "Compare Mahomes and Allen this season"
    - "What's the best bet for tonight's Lakers game?"
    - "Show me Ohtani's hitting trend"
    """
    service = get_chat_service()

    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())

    # Process query
    result = await service.process_query(
        query=request.query,
        session_id=session_id,
        context=request.context
    )

    return ChatResponse(**result)


@app.post("/predict")
async def predict_player_stat(request: PlayerPredictionRequest):
    """
    Predict a player's statistical performance.

    Example:
    ```json
    {
        "sport": "nba",
        "player_name": "LeBron James",
        "metric": "points"
    }
    ```
    """
    result = analytics_service.predict_player_stat(
        sport=request.sport,
        player_name=request.player_name,
        metric=request.metric,
        historical_data=request.historical_data
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@app.post("/compare")
async def compare_players(request: PlayerComparisonRequest):
    """
    Compare two players across multiple metrics.

    Example:
    ```json
    {
        "sport": "nba",
        "player1": "LeBron James",
        "player2": "Kevin Durant",
        "metrics": ["points", "assists", "rebounds"]
    }
    ```
    """
    result = analytics_service.compare_players(
        sport=request.sport,
        player1=request.player1,
        player2=request.player2,
        metrics=request.metrics
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@app.post("/trend")
async def analyze_trend(request: TrendAnalysisRequest):
    """
    Analyze historical trends for a player.

    Example:
    ```json
    {
        "sport": "nba",
        "player_name": "Stephen Curry",
        "metric": "three_pointers",
        "games": 10
    }
    ```
    """
    result = analytics_service.analyze_historical_trend(
        sport=request.sport,
        player_name=request.player_name,
        metric=request.metric,
        games=request.games
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@app.post("/session/new", response_model=SessionResponse)
async def create_session():
    """Create a new conversation session."""
    service = get_chat_service()
    session_id = str(uuid.uuid4())
    service.create_session(session_id)

    return SessionResponse(
        session_id=session_id,
        created_at=datetime.now().isoformat()
    )


@app.get("/session/{session_id}/history")
async def get_session_history(session_id: str):
    """Get conversation history for a session."""
    service = get_chat_service()
    history = service.get_session_history(session_id)

    return {
        "session_id": session_id,
        "message_count": len(history),
        "history": history
    }


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear conversation history for a session."""
    service = get_chat_service()
    service.clear_session(session_id)

    return {
        "session_id": session_id,
        "status": "cleared"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "chat": chat_service is not None,
            "analytics": True,
            "social": True
        }
    }


# Include social features router
app.include_router(social_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
