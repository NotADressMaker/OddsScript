"""
SportsBetLang Social Features Module

User-generated predictions, community leaderboards, discussions, and social interactions.
"""

from .database import get_database, SocialDatabase
from .auth import AuthService
from .services import (
    PredictionService,
    DiscussionService,
    FollowService,
    LeaderboardService,
    LikeService
)

__all__ = [
    'get_database',
    'SocialDatabase',
    'AuthService',
    'PredictionService',
    'DiscussionService',
    'FollowService',
    'LeaderboardService',
    'LikeService'
]
