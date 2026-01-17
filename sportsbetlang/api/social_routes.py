"""
FastAPI Routes for Social Features

Authentication, predictions, discussions, follows, and leaderboards.
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

from sportsbetlang.social import (
    AuthService,
    PredictionService,
    DiscussionService,
    FollowService,
    LeaderboardService,
    LikeService
)

# Initialize services
auth_service = AuthService()
prediction_service = PredictionService()
discussion_service = DiscussionService()
follow_service = FollowService()
leaderboard_service = LeaderboardService()
like_service = LikeService()

# Create router
social_router = APIRouter(prefix="/social", tags=["social"])


# Pydantic models

class UserRegister(BaseModel):
    """User registration request."""
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(..., min_length=6)
    display_name: Optional[str] = None
    bio: Optional[str] = None


class UserLogin(BaseModel):
    """User login request."""
    username: str
    password: str


class ProfileUpdate(BaseModel):
    """Profile update request."""
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class PredictionCreate(BaseModel):
    """Create prediction request."""
    sport: str = Field(..., description="Sport (nba, nfl, mlb, nhl)")
    prediction_type: str = Field(..., description="Type (player_prop, game_outcome, spread, total)")
    description: str = Field(..., description="Prediction description")
    pick: str = Field(..., description="The actual pick")
    odds: Optional[float] = None
    stake: Optional[float] = None
    confidence: Optional[int] = Field(None, ge=1, le=5, description="Confidence 1-5 stars")
    reasoning: Optional[str] = None
    game_id: Optional[str] = None
    game_date: Optional[str] = None


class PredictionSettle(BaseModel):
    """Settle prediction request."""
    status: str = Field(..., description="won, lost, or void")
    result: float = Field(..., description="Profit/loss amount")


class DiscussionCreate(BaseModel):
    """Create discussion request."""
    title: str = Field(..., min_length=5, max_length=200)
    content: str = Field(..., min_length=10)
    category: Optional[str] = Field(None, description="general, strategy, picks, analysis")
    sport: Optional[str] = None
    tags: Optional[List[str]] = None


class CommentCreate(BaseModel):
    """Create comment request."""
    content: str = Field(..., min_length=1, max_length=1000)


# Authentication dependency
def get_current_user(authorization: Optional[str] = Header(None)) -> int:
    """Get current user from JWT token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.replace("Bearer ", "")
    user_id = auth_service.verify_token(token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user_id


# Authentication routes

@social_router.post("/auth/register")
async def register(user_data: UserRegister):
    """Register a new user account."""
    try:
        user = auth_service.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            display_name=user_data.display_name,
            bio=user_data.bio
        )

        token = auth_service.create_token(user['id'])

        return {
            "user": user,
            "token": token,
            "message": "Registration successful"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@social_router.post("/auth/login")
async def login(credentials: UserLogin):
    """Login and get JWT token."""
    user = auth_service.authenticate(credentials.username, credentials.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = auth_service.create_token(user['id'])

    return {
        "user": user,
        "token": token,
        "message": "Login successful"
    }


@social_router.get("/auth/me")
async def get_current_user_profile(user_id: int = Depends(get_current_user)):
    """Get current user's profile with stats."""
    user = auth_service.get_user_with_stats(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@social_router.put("/auth/profile")
async def update_profile(
    profile: ProfileUpdate,
    user_id: int = Depends(get_current_user)
):
    """Update user profile."""
    user = auth_service.update_user_profile(
        user_id=user_id,
        display_name=profile.display_name,
        bio=profile.bio,
        avatar_url=profile.avatar_url
    )
    return user


# User routes

@social_router.get("/users/{username}")
async def get_user_profile(username: str):
    """Get user profile by username."""
    users = auth_service.db.execute_query(
        """SELECT u.*, s.*
           FROM users u
           LEFT JOIN user_stats s ON u.id = s.user_id
           WHERE u.username = ?""",
        (username,)
    )

    if not users:
        raise HTTPException(status_code=404, detail="User not found")

    user = dict(users[0])
    del user['password_hash']
    return user


# Prediction routes

@social_router.post("/predictions")
async def create_prediction(
    prediction: PredictionCreate,
    user_id: int = Depends(get_current_user)
):
    """Create a new prediction."""
    result = prediction_service.create_prediction(
        user_id=user_id,
        sport=prediction.sport,
        prediction_type=prediction.prediction_type,
        description=prediction.description,
        pick=prediction.pick,
        odds=prediction.odds,
        stake=prediction.stake,
        confidence=prediction.confidence,
        reasoning=prediction.reasoning,
        game_id=prediction.game_id,
        game_date=prediction.game_date
    )
    return result


@social_router.get("/predictions/{prediction_id}")
async def get_prediction(prediction_id: int):
    """Get a prediction by ID."""
    prediction = prediction_service.get_prediction(prediction_id)
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction


@social_router.get("/predictions/user/{username}")
async def get_user_predictions(
    username: str,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get predictions for a user."""
    # Get user ID
    users = auth_service.db.execute_query(
        "SELECT id FROM users WHERE username = ?",
        (username,)
    )
    if not users:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = users[0]['id']
    predictions = prediction_service.get_user_predictions(user_id, status, limit, offset)
    return predictions


@social_router.get("/predictions/feed")
async def get_predictions_feed(
    sport: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get recent predictions feed."""
    predictions = prediction_service.get_feed_predictions(sport, limit, offset)
    return predictions


@social_router.put("/predictions/{prediction_id}/settle")
async def settle_prediction(
    prediction_id: int,
    settle_data: PredictionSettle,
    user_id: int = Depends(get_current_user)
):
    """Settle a prediction (mark as won/lost)."""
    # Verify ownership
    prediction = prediction_service.get_prediction(prediction_id)
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")

    if prediction['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = prediction_service.settle_prediction(
        prediction_id=prediction_id,
        status=settle_data.status,
        result=settle_data.result
    )
    return result


# Discussion routes

@social_router.post("/discussions")
async def create_discussion(
    discussion: DiscussionCreate,
    user_id: int = Depends(get_current_user)
):
    """Create a new discussion thread."""
    result = discussion_service.create_discussion(
        user_id=user_id,
        title=discussion.title,
        content=discussion.content,
        category=discussion.category,
        sport=discussion.sport,
        tags=discussion.tags
    )
    return result


@social_router.get("/discussions")
async def get_discussions(
    category: Optional[str] = None,
    sport: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get discussion threads."""
    discussions = discussion_service.get_discussions(category, sport, limit, offset)
    return discussions


@social_router.get("/discussions/{discussion_id}")
async def get_discussion(discussion_id: int):
    """Get a discussion thread."""
    discussion = discussion_service.get_discussion(discussion_id)
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")
    return discussion


@social_router.get("/discussions/{discussion_id}/comments")
async def get_discussion_comments(discussion_id: int, limit: int = 100):
    """Get comments for a discussion."""
    comments = discussion_service.get_comments('discussion', discussion_id, limit)
    return comments


@social_router.post("/discussions/{discussion_id}/comments")
async def add_discussion_comment(
    discussion_id: int,
    comment: CommentCreate,
    user_id: int = Depends(get_current_user)
):
    """Add a comment to a discussion."""
    result = discussion_service.add_comment(
        user_id=user_id,
        parent_type='discussion',
        parent_id=discussion_id,
        content=comment.content
    )
    return result


# Prediction comments

@social_router.get("/predictions/{prediction_id}/comments")
async def get_prediction_comments(prediction_id: int, limit: int = 100):
    """Get comments for a prediction."""
    comments = discussion_service.get_comments('prediction', prediction_id, limit)
    return comments


@social_router.post("/predictions/{prediction_id}/comments")
async def add_prediction_comment(
    prediction_id: int,
    comment: CommentCreate,
    user_id: int = Depends(get_current_user)
):
    """Add a comment to a prediction."""
    result = discussion_service.add_comment(
        user_id=user_id,
        parent_type='prediction',
        parent_id=prediction_id,
        content=comment.content
    )
    return result


# Follow routes

@social_router.post("/users/{username}/follow")
async def follow_user(username: str, user_id: int = Depends(get_current_user)):
    """Follow a user."""
    # Get target user ID
    users = auth_service.db.execute_query(
        "SELECT id FROM users WHERE username = ?",
        (username,)
    )
    if not users:
        raise HTTPException(status_code=404, detail="User not found")

    following_id = users[0]['id']

    try:
        result = follow_service.follow_user(user_id, following_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@social_router.delete("/users/{username}/follow")
async def unfollow_user(username: str, user_id: int = Depends(get_current_user)):
    """Unfollow a user."""
    # Get target user ID
    users = auth_service.db.execute_query(
        "SELECT id FROM users WHERE username = ?",
        (username,)
    )
    if not users:
        raise HTTPException(status_code=404, detail="User not found")

    following_id = users[0]['id']
    result = follow_service.unfollow_user(user_id, following_id)
    return result


@social_router.get("/users/{username}/followers")
async def get_followers(username: str, limit: int = 100):
    """Get user's followers."""
    # Get user ID
    users = auth_service.db.execute_query(
        "SELECT id FROM users WHERE username = ?",
        (username,)
    )
    if not users:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = users[0]['id']
    followers = follow_service.get_followers(user_id, limit)
    return followers


@social_router.get("/users/{username}/following")
async def get_following(username: str, limit: int = 100):
    """Get users that this user follows."""
    # Get user ID
    users = auth_service.db.execute_query(
        "SELECT id FROM users WHERE username = ?",
        (username,)
    )
    if not users:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = users[0]['id']
    following = follow_service.get_following(user_id, limit)
    return following


@social_router.get("/feed")
async def get_activity_feed(
    user_id: int = Depends(get_current_user),
    limit: int = 50
):
    """Get activity feed from followed users."""
    feed = follow_service.get_feed(user_id, limit)
    return feed


# Leaderboard routes

@social_router.get("/leaderboard")
async def get_leaderboard(
    metric: str = 'roi',
    sport: Optional[str] = None,
    period: str = 'all_time',
    min_predictions: int = 10,
    limit: int = 100
):
    """
    Get community leaderboard.

    Metrics: roi, win_rate, total_profit, streak
    Period: daily, weekly, monthly, all_time
    """
    rankings = leaderboard_service.get_leaderboard(
        metric=metric,
        sport=sport,
        period=period,
        min_predictions=min_predictions,
        limit=limit
    )
    return rankings


@social_router.get("/leaderboard/analysts")
async def get_top_analysts(limit: int = 10):
    """Get top performing analysts."""
    analysts = leaderboard_service.get_top_analysts(limit)
    return analysts


# Like routes

@social_router.post("/{target_type}/{target_id}/like")
async def like_content(
    target_type: str,
    target_id: int,
    user_id: int = Depends(get_current_user)
):
    """Like a prediction, discussion, or comment."""
    if target_type not in ['prediction', 'discussion', 'comment']:
        raise HTTPException(status_code=400, detail="Invalid target type")

    try:
        result = like_service.like(user_id, target_type, target_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@social_router.delete("/{target_type}/{target_id}/like")
async def unlike_content(
    target_type: str,
    target_id: int,
    user_id: int = Depends(get_current_user)
):
    """Unlike a prediction, discussion, or comment."""
    if target_type not in ['prediction', 'discussion', 'comment']:
        raise HTTPException(status_code=400, detail="Invalid target type")

    result = like_service.unlike(user_id, target_type, target_id)
    return result
