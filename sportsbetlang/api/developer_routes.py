"""
FastAPI Routes for Developer Features

API key management, webhooks, data feeds, and white-label configurations.
"""

from fastapi import APIRouter, HTTPException, Depends, Header, Request
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
import time

from sportsbetlang.developer import (
    APIKeyService,
    APIKeyTier,
    WebhookService,
    WhiteLabelService
)
from sportsbetlang.social import AuthService

# Initialize services
api_key_service = APIKeyService()
webhook_service = WebhookService()
whitelabel_service = WhiteLabelService()
auth_service = AuthService()

# Create router
developer_router = APIRouter(prefix="/developer", tags=["developer"])


# Pydantic models

class APIKeyCreate(BaseModel):
    """Create API key request."""
    name: str = Field(..., description="Descriptive name for the API key")
    tier: str = Field("free", description="API tier (free, pro, enterprise)")
    expires_days: Optional[int] = Field(None, description="Days until expiration")


class WebhookCreate(BaseModel):
    """Create webhook request."""
    url: HttpUrl = Field(..., description="Webhook URL")
    events: List[str] = Field(..., description="Event types to subscribe to")


class WhiteLabelConfig(BaseModel):
    """White-label configuration."""
    domain: str = Field(..., description="Custom domain")
    brand_name: str = Field(..., description="Brand name")
    logo_url: Optional[str] = None
    primary_color: Optional[str] = Field(None, description="Primary brand color (hex)")
    secondary_color: Optional[str] = Field(None, description="Secondary color (hex)")
    custom_css: Optional[str] = None
    features: Optional[List[str]] = Field(default_factory=list)


class DataFeedRequest(BaseModel):
    """Custom data feed request."""
    sport: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    format: str = Field("json", description="Output format (json, csv)")
    include_fields: Optional[List[str]] = None


# Authentication dependency (user JWT)
def get_current_user(authorization: Optional[str] = Header(None)) -> int:
    """Get current user from JWT token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.replace("Bearer ", "")
    user_id = auth_service.verify_token(token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user_id


# API key authentication dependency
def verify_api_key(x_api_key: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Verify API key from header."""
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Include X-API-Key header."
        )

    key_data = api_key_service.verify_api_key(x_api_key)

    if not key_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired API key"
        )

    # Increment usage
    api_key_service.increment_usage(key_data['id'])

    return key_data


# Middleware for logging API requests
async def log_api_request(
    request: Request,
    api_key: Dict[str, Any],
    response_status: int,
    response_time_ms: int
):
    """Log API request for analytics."""
    api_key_service.log_request(
        api_key_id=api_key['id'],
        endpoint=str(request.url.path),
        method=request.method,
        status_code=response_status,
        response_time_ms=response_time_ms,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get('user-agent')
    )


# API Key Management Routes

@developer_router.post("/keys")
async def create_api_key(
    key_data: APIKeyCreate,
    user_id: int = Depends(get_current_user)
):
    """
    Create a new API key.

    Requires user authentication. The API key is only shown once.

    **Tiers:**
    - `free`: 1,000 requests/day
    - `pro`: 100,000 requests/day
    - `enterprise`: Unlimited requests
    """
    # Validate tier
    valid_tiers = [t.value for t in APIKeyTier]
    if key_data.tier not in valid_tiers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tier. Must be one of: {', '.join(valid_tiers)}"
        )

    # Check user's subscription level (simplified - add real check in production)
    # For now, anyone can create free keys, pro+ for paid users
    if key_data.tier != APIKeyTier.FREE.value:
        # TODO: Check user subscription
        pass

    result = api_key_service.generate_api_key(
        user_id=user_id,
        name=key_data.name,
        tier=key_data.tier,
        expires_days=key_data.expires_days
    )

    return result


@developer_router.get("/keys")
async def list_api_keys(user_id: int = Depends(get_current_user)):
    """List all API keys for the authenticated user."""
    keys = api_key_service.get_user_api_keys(user_id)
    return {"keys": keys}


@developer_router.delete("/keys/{key_id}")
async def revoke_api_key(
    key_id: int,
    user_id: int = Depends(get_current_user)
):
    """Revoke an API key."""
    api_key_service.revoke_api_key(key_id, user_id)
    return {"status": "revoked", "key_id": key_id}


@developer_router.post("/keys/{key_id}/rotate")
async def rotate_api_key(
    key_id: int,
    user_id: int = Depends(get_current_user)
):
    """
    Rotate an API key.

    Revokes the old key and creates a new one with the same settings.
    """
    new_key = api_key_service.rotate_api_key(key_id, user_id)
    return new_key


@developer_router.get("/keys/usage")
async def get_api_usage(
    days: int = 30,
    user_id: int = Depends(get_current_user)
):
    """Get API usage statistics."""
    stats = api_key_service.get_usage_stats(user_id, days)
    return stats


# Webhook Routes

@developer_router.post("/webhooks")
async def create_webhook(
    webhook_data: WebhookCreate,
    user_id: int = Depends(get_current_user)
):
    """
    Create a webhook subscription.

    **Available Events:**
    - `prediction.created` - New prediction posted
    - `prediction.settled` - Prediction settled
    - `discussion.created` - New discussion thread
    - `comment.created` - New comment
    - `leaderboard.updated` - Leaderboard updated
    - `user.followed` - User followed

    Returns a webhook secret for verifying signatures.
    """
    # Get user's first active API key
    keys = api_key_service.get_user_api_keys(user_id)
    if not keys:
        raise HTTPException(
            status_code=400,
            detail="No API key found. Create an API key first."
        )

    api_key_id = keys[0]['id']

    webhook = webhook_service.create_webhook(
        user_id=user_id,
        api_key_id=api_key_id,
        url=str(webhook_data.url),
        events=webhook_data.events
    )

    return webhook


@developer_router.get("/webhooks")
async def list_webhooks(user_id: int = Depends(get_current_user)):
    """List all webhooks for the authenticated user."""
    webhooks = webhook_service.get_user_webhooks(user_id)
    return {"webhooks": webhooks}


@developer_router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    user_id: int = Depends(get_current_user)
):
    """Delete a webhook."""
    webhook_service.delete_webhook(webhook_id, user_id)
    return {"status": "deleted", "webhook_id": webhook_id}


# Data Feed Routes (require API key)

@developer_router.get("/data/predictions")
async def get_predictions_feed(
    sport: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    api_key: Dict = Depends(verify_api_key)
):
    """
    Get predictions data feed.

    Requires API key authentication.

    **Query Parameters:**
    - `sport`: Filter by sport (nba, nfl, mlb, nhl)
    - `start_date`: Start date (YYYY-MM-DD)
    - `end_date`: End date (YYYY-MM-DD)
    - `limit`: Number of records (max 1000)
    - `offset`: Pagination offset
    """
    from sportsbetlang.social import PredictionService

    # Limit max results based on tier
    max_limits = {
        'free': 100,
        'pro': 1000,
        'enterprise': 10000
    }
    max_limit = max_limits.get(api_key['tier'], 100)
    limit = min(limit, max_limit)

    prediction_service = PredictionService()
    predictions = prediction_service.get_feed_predictions(sport, limit, offset)

    # Filter by date if provided
    if start_date or end_date:
        filtered = []
        for pred in predictions:
            pred_date = pred.get('created_at', '')[:10]
            if start_date and pred_date < start_date:
                continue
            if end_date and pred_date > end_date:
                continue
            filtered.append(pred)
        predictions = filtered

    return {
        "predictions": predictions,
        "count": len(predictions),
        "limit": limit,
        "offset": offset,
        "api_key_tier": api_key['tier']
    }


@developer_router.get("/data/leaderboard")
async def get_leaderboard_data(
    metric: str = 'roi',
    sport: Optional[str] = None,
    limit: int = 100,
    api_key: Dict = Depends(verify_api_key)
):
    """
    Get leaderboard data.

    Requires API key authentication.
    """
    from sportsbetlang.social import LeaderboardService

    leaderboard_service = LeaderboardService()
    rankings = leaderboard_service.get_leaderboard(
        metric=metric,
        sport=sport,
        limit=limit
    )

    return {
        "rankings": rankings,
        "count": len(rankings),
        "metric": metric,
        "sport": sport
    }


@developer_router.get("/data/discussions")
async def get_discussions_data(
    category: Optional[str] = None,
    sport: Optional[str] = None,
    limit: int = 100,
    api_key: Dict = Depends(verify_api_key)
):
    """
    Get discussions data.

    Requires API key authentication.
    """
    from sportsbetlang.social import DiscussionService

    discussion_service = DiscussionService()
    discussions = discussion_service.get_discussions(category, sport, limit, 0)

    return {
        "discussions": discussions,
        "count": len(discussions)
    }


@developer_router.post("/data/export")
async def export_custom_data(
    request: DataFeedRequest,
    user_id: int = Depends(get_current_user)
):
    """
    Export custom data in various formats.

    **Pro feature**: Requires Pro or Enterprise tier.
    """
    # Check if user has pro access
    # TODO: Implement subscription check

    from sportsbetlang.social import PredictionService
    import csv
    import io

    prediction_service = PredictionService()
    predictions = prediction_service.get_feed_predictions(
        sport=request.sport,
        limit=10000
    )

    # Filter by date
    if request.start_date or request.end_date:
        filtered = []
        for pred in predictions:
            pred_date = pred.get('created_at', '')[:10]
            if request.start_date and pred_date < request.start_date:
                continue
            if request.end_date and pred_date > request.end_date:
                continue
            filtered.append(pred)
        predictions = filtered

    # Format output
    if request.format == 'csv':
        output = io.StringIO()
        if predictions:
            writer = csv.DictWriter(output, fieldnames=predictions[0].keys())
            writer.writeheader()
            writer.writerows(predictions)

        return {
            "format": "csv",
            "data": output.getvalue(),
            "count": len(predictions)
        }
    else:
        return {
            "format": "json",
            "data": predictions,
            "count": len(predictions)
        }


# White-Label Routes

@developer_router.post("/whitelabel")
async def create_whitelabel_config(
    config: WhiteLabelConfig,
    user_id: int = Depends(get_current_user)
):
    """
    Create white-label configuration.

    **Enterprise feature**: Requires Enterprise tier.
    """
    # Get user's API key
    keys = api_key_service.get_user_api_keys(user_id)
    if not keys:
        raise HTTPException(
            status_code=400,
            detail="No API key found. Create an Enterprise API key first."
        )

    # Check for Enterprise tier
    enterprise_key = None
    for key in keys:
        if key['tier'] == APIKeyTier.ENTERPRISE.value and key['active']:
            enterprise_key = key
            break

    if not enterprise_key:
        raise HTTPException(
            status_code=403,
            detail="White-label requires Enterprise tier API key"
        )

    wl_config = whitelabel_service.create_config(
        user_id=user_id,
        api_key_id=enterprise_key['id'],
        domain=config.domain,
        brand_name=config.brand_name,
        logo_url=config.logo_url,
        primary_color=config.primary_color,
        secondary_color=config.secondary_color,
        custom_css=config.custom_css,
        features=config.features
    )

    return wl_config


@developer_router.get("/whitelabel/{domain}")
async def get_whitelabel_config(domain: str):
    """Get white-label configuration for a domain."""
    config = whitelabel_service.get_config_by_domain(domain)

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    return config


# Developer Portal Routes

@developer_router.get("/docs/events")
async def list_webhook_events():
    """List all available webhook events."""
    return {
        "events": [
            {
                "name": "prediction.created",
                "description": "Triggered when a new prediction is posted",
                "payload": {
                    "prediction_id": "int",
                    "user_id": "int",
                    "sport": "string",
                    "description": "string",
                    "pick": "string"
                }
            },
            {
                "name": "prediction.settled",
                "description": "Triggered when a prediction is settled",
                "payload": {
                    "prediction_id": "int",
                    "user_id": "int",
                    "status": "won|lost|void",
                    "result": "float"
                }
            },
            {
                "name": "discussion.created",
                "description": "Triggered when a new discussion is created",
                "payload": {
                    "discussion_id": "int",
                    "user_id": "int",
                    "title": "string",
                    "category": "string"
                }
            },
            {
                "name": "comment.created",
                "description": "Triggered when a comment is posted",
                "payload": {
                    "comment_id": "int",
                    "user_id": "int",
                    "parent_type": "prediction|discussion",
                    "parent_id": "int"
                }
            },
            {
                "name": "leaderboard.updated",
                "description": "Triggered when leaderboard rankings change",
                "payload": {
                    "sport": "string|null",
                    "metric": "string",
                    "top_10": "array"
                }
            },
            {
                "name": "user.followed",
                "description": "Triggered when a user is followed",
                "payload": {
                    "follower_id": "int",
                    "following_id": "int"
                }
            }
        ]
    }


@developer_router.get("/docs/rate-limits")
async def get_rate_limits():
    """Get rate limit information for all tiers."""
    return {
        "tiers": [
            {
                "name": "free",
                "rate_limit": "1,000 requests/day",
                "features": [
                    "Basic API access",
                    "Public endpoints",
                    "Limited webhooks (3 max)"
                ]
            },
            {
                "name": "pro",
                "rate_limit": "100,000 requests/day",
                "features": [
                    "Full API access",
                    "All endpoints",
                    "Unlimited webhooks",
                    "Custom data exports",
                    "Priority support"
                ]
            },
            {
                "name": "enterprise",
                "rate_limit": "Unlimited",
                "features": [
                    "Unlimited API access",
                    "White-label solutions",
                    "Custom integrations",
                    "Dedicated support",
                    "SLA guarantees"
                ]
            }
        ]
    }
