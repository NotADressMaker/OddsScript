"""
Social Services for User-Generated Content

Predictions, discussions, follows, leaderboards, and activity feeds.
"""

import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from .database import get_database


class PredictionService:
    """Service for user-generated predictions."""

    def __init__(self):
        """Initialize prediction service."""
        self.db = get_database()

    def create_prediction(
        self,
        user_id: int,
        sport: str,
        prediction_type: str,
        description: str,
        pick: str,
        odds: Optional[float] = None,
        stake: Optional[float] = None,
        confidence: Optional[int] = None,
        reasoning: Optional[str] = None,
        game_id: Optional[str] = None,
        game_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new prediction."""
        prediction_id = self.db.execute_update(
            """INSERT INTO predictions
               (user_id, sport, game_id, prediction_type, description, pick,
                odds, stake, confidence, reasoning, game_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, sport, game_id, prediction_type, description, pick,
             odds, stake, confidence, reasoning, game_date)
        )

        # Update user stats
        self.db.execute_update(
            """UPDATE user_stats
               SET total_predictions = total_predictions + 1,
                   total_units_wagered = total_units_wagered + ?
               WHERE user_id = ?""",
            (stake or 0, user_id)
        )

        # Create activity
        self._create_activity(user_id, 'prediction', {'prediction_id': prediction_id})

        return self.get_prediction(prediction_id)

    def get_prediction(self, prediction_id: int) -> Optional[Dict[str, Any]]:
        """Get a prediction by ID."""
        predictions = self.db.execute_query(
            """SELECT p.*, u.username, u.display_name, u.is_analyst, u.analyst_tier
               FROM predictions p
               JOIN users u ON p.user_id = u.id
               WHERE p.id = ?""",
            (prediction_id,)
        )
        return dict(predictions[0]) if predictions else None

    def get_user_predictions(
        self,
        user_id: int,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get predictions for a user."""
        if status:
            query = """SELECT p.*, u.username, u.display_name
                      FROM predictions p
                      JOIN users u ON p.user_id = u.id
                      WHERE p.user_id = ? AND p.status = ?
                      ORDER BY p.created_at DESC
                      LIMIT ? OFFSET ?"""
            params = (user_id, status, limit, offset)
        else:
            query = """SELECT p.*, u.username, u.display_name
                      FROM predictions p
                      JOIN users u ON p.user_id = u.id
                      WHERE p.user_id = ?
                      ORDER BY p.created_at DESC
                      LIMIT ? OFFSET ?"""
            params = (user_id, limit, offset)

        return self.db.execute_query(query, params)

    def get_feed_predictions(
        self,
        sport: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get predictions feed (recent predictions from all users)."""
        if sport:
            query = """SELECT p.*, u.username, u.display_name, u.is_analyst, u.analyst_tier
                      FROM predictions p
                      JOIN users u ON p.user_id = u.id
                      WHERE p.sport = ?
                      ORDER BY p.created_at DESC
                      LIMIT ? OFFSET ?"""
            params = (sport, limit, offset)
        else:
            query = """SELECT p.*, u.username, u.display_name, u.is_analyst, u.analyst_tier
                      FROM predictions p
                      JOIN users u ON p.user_id = u.id
                      ORDER BY p.created_at DESC
                      LIMIT ? OFFSET ?"""
            params = (limit, offset)

        return self.db.execute_query(query, params)

    def settle_prediction(
        self,
        prediction_id: int,
        status: str,
        result: float
    ) -> Dict[str, Any]:
        """
        Settle a prediction (mark as won/lost).

        Args:
            prediction_id: Prediction ID
            status: 'won', 'lost', or 'void'
            result: Profit/loss amount

        Returns:
            Updated prediction
        """
        # Get prediction
        prediction = self.get_prediction(prediction_id)
        if not prediction:
            raise ValueError("Prediction not found")

        # Update prediction
        self.db.execute_update(
            """UPDATE predictions
               SET status = ?, result = ?, settled_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (status, result, prediction_id)
        )

        # Update user stats
        if status == 'won':
            self._update_stats_on_win(prediction['user_id'], result)
        elif status == 'lost':
            self._update_stats_on_loss(prediction['user_id'], result)

        return self.get_prediction(prediction_id)

    def _update_stats_on_win(self, user_id: int, profit: float):
        """Update user stats after a win."""
        self.db.execute_update(
            """UPDATE user_stats
               SET correct_predictions = correct_predictions + 1,
                   total_profit_loss = total_profit_loss + ?,
                   current_streak = current_streak + 1,
                   best_streak = MAX(best_streak, current_streak + 1)
               WHERE user_id = ?""",
            (profit, user_id)
        )
        self._recalculate_stats(user_id)

    def _update_stats_on_loss(self, user_id: int, loss: float):
        """Update user stats after a loss."""
        self.db.execute_update(
            """UPDATE user_stats
               SET total_profit_loss = total_profit_loss + ?,
                   current_streak = 0
               WHERE user_id = ?""",
            (loss, user_id)
        )
        self._recalculate_stats(user_id)

    def _recalculate_stats(self, user_id: int):
        """Recalculate win rate and ROI."""
        stats = self.db.execute_query(
            "SELECT * FROM user_stats WHERE user_id = ?",
            (user_id,)
        )[0]

        if stats['total_predictions'] > 0:
            win_rate = stats['correct_predictions'] / stats['total_predictions']
        else:
            win_rate = 0

        if stats['total_units_wagered'] > 0:
            roi = stats['total_profit_loss'] / stats['total_units_wagered']
        else:
            roi = 0

        self.db.execute_update(
            "UPDATE user_stats SET win_rate = ?, roi = ? WHERE user_id = ?",
            (win_rate, roi, user_id)
        )

    def _create_activity(self, user_id: int, activity_type: str, data: Dict):
        """Create activity feed entry."""
        self.db.execute_update(
            "INSERT INTO activities (user_id, activity_type, activity_data) VALUES (?, ?, ?)",
            (user_id, activity_type, json.dumps(data))
        )


class DiscussionService:
    """Service for discussion threads."""

    def __init__(self):
        """Initialize discussion service."""
        self.db = get_database()

    def create_discussion(
        self,
        user_id: int,
        title: str,
        content: str,
        category: Optional[str] = None,
        sport: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new discussion thread."""
        discussion_id = self.db.execute_update(
            """INSERT INTO discussions
               (user_id, title, content, category, sport, tags)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, title, content, category, sport, json.dumps(tags or []))
        )

        # Create activity
        self.db.execute_update(
            "INSERT INTO activities (user_id, activity_type, activity_data) VALUES (?, ?, ?)",
            (user_id, 'discussion', json.dumps({'discussion_id': discussion_id}))
        )

        return self.get_discussion(discussion_id)

    def get_discussion(self, discussion_id: int) -> Optional[Dict[str, Any]]:
        """Get a discussion by ID."""
        discussions = self.db.execute_query(
            """SELECT d.*, u.username, u.display_name, u.is_analyst
               FROM discussions d
               JOIN users u ON d.user_id = u.id
               WHERE d.id = ?""",
            (discussion_id,)
        )

        if not discussions:
            return None

        discussion = dict(discussions[0])
        discussion['tags'] = json.loads(discussion['tags'])

        # Increment view count
        self.db.execute_update(
            "UPDATE discussions SET views_count = views_count + 1 WHERE id = ?",
            (discussion_id,)
        )

        return discussion

    def get_discussions(
        self,
        category: Optional[str] = None,
        sport: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get discussion threads."""
        conditions = []
        params = []

        if category:
            conditions.append("d.category = ?")
            params.append(category)

        if sport:
            conditions.append("d.sport = ?")
            params.append(sport)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""SELECT d.*, u.username, u.display_name, u.is_analyst
                   FROM discussions d
                   JOIN users u ON d.user_id = u.id
                   WHERE {where_clause}
                   ORDER BY d.is_pinned DESC, d.updated_at DESC
                   LIMIT ? OFFSET ?"""

        params.extend([limit, offset])

        discussions = self.db.execute_query(query, tuple(params))

        for d in discussions:
            d['tags'] = json.loads(d['tags'])

        return discussions

    def add_comment(
        self,
        user_id: int,
        parent_type: str,
        parent_id: int,
        content: str
    ) -> Dict[str, Any]:
        """Add a comment to a prediction or discussion."""
        comment_id = self.db.execute_update(
            """INSERT INTO comments (user_id, parent_type, parent_id, content)
               VALUES (?, ?, ?, ?)""",
            (user_id, parent_type, parent_id, content)
        )

        # Update comment count on parent
        if parent_type == 'prediction':
            self.db.execute_update(
                "UPDATE predictions SET comments_count = comments_count + 1 WHERE id = ?",
                (parent_id,)
            )
        elif parent_type == 'discussion':
            self.db.execute_update(
                """UPDATE discussions
                   SET comments_count = comments_count + 1, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (parent_id,)
            )

        return self.get_comment(comment_id)

    def get_comment(self, comment_id: int) -> Optional[Dict[str, Any]]:
        """Get a comment by ID."""
        comments = self.db.execute_query(
            """SELECT c.*, u.username, u.display_name
               FROM comments c
               JOIN users u ON c.user_id = u.id
               WHERE c.id = ?""",
            (comment_id,)
        )
        return dict(comments[0]) if comments else None

    def get_comments(
        self,
        parent_type: str,
        parent_id: int,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get comments for a prediction or discussion."""
        return self.db.execute_query(
            """SELECT c.*, u.username, u.display_name, u.is_analyst
               FROM comments c
               JOIN users u ON c.user_id = u.id
               WHERE c.parent_type = ? AND c.parent_id = ?
               ORDER BY c.created_at ASC
               LIMIT ?""",
            (parent_type, parent_id, limit)
        )


class FollowService:
    """Service for following analysts and users."""

    def __init__(self):
        """Initialize follow service."""
        self.db = get_database()

    def follow_user(self, follower_id: int, following_id: int) -> Dict[str, Any]:
        """Follow a user."""
        if follower_id == following_id:
            raise ValueError("Cannot follow yourself")

        try:
            self.db.execute_update(
                "INSERT INTO follows (follower_id, following_id) VALUES (?, ?)",
                (follower_id, following_id)
            )

            # Update follower/following counts
            self.db.execute_update(
                "UPDATE user_stats SET following_count = following_count + 1 WHERE user_id = ?",
                (follower_id,)
            )
            self.db.execute_update(
                "UPDATE user_stats SET followers_count = followers_count + 1 WHERE user_id = ?",
                (following_id,)
            )

            # Create activity
            self.db.execute_update(
                "INSERT INTO activities (user_id, activity_type, activity_data) VALUES (?, ?, ?)",
                (follower_id, 'follow', json.dumps({'following_id': following_id}))
            )

            return {"status": "success", "follower_id": follower_id, "following_id": following_id}
        except:
            raise ValueError("Already following this user")

    def unfollow_user(self, follower_id: int, following_id: int) -> Dict[str, Any]:
        """Unfollow a user."""
        self.db.execute_update(
            "DELETE FROM follows WHERE follower_id = ? AND following_id = ?",
            (follower_id, following_id)
        )

        # Update counts
        self.db.execute_update(
            "UPDATE user_stats SET following_count = following_count - 1 WHERE user_id = ?",
            (follower_id,)
        )
        self.db.execute_update(
            "UPDATE user_stats SET followers_count = followers_count - 1 WHERE user_id = ?",
            (following_id,)
        )

        return {"status": "success", "follower_id": follower_id, "following_id": following_id}

    def get_followers(self, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Get users who follow this user."""
        return self.db.execute_query(
            """SELECT u.id, u.username, u.display_name, u.is_analyst, u.avatar_url,
                      s.total_predictions, s.win_rate, s.roi
               FROM follows f
               JOIN users u ON f.follower_id = u.id
               LEFT JOIN user_stats s ON u.id = s.user_id
               WHERE f.following_id = ?
               ORDER BY f.created_at DESC
               LIMIT ?""",
            (user_id, limit)
        )

    def get_following(self, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Get users that this user follows."""
        return self.db.execute_query(
            """SELECT u.id, u.username, u.display_name, u.is_analyst, u.avatar_url,
                      s.total_predictions, s.win_rate, s.roi
               FROM follows f
               JOIN users u ON f.following_id = u.id
               LEFT JOIN user_stats s ON u.id = s.user_id
               WHERE f.follower_id = ?
               ORDER BY f.created_at DESC
               LIMIT ?""",
            (user_id, limit)
        )

    def is_following(self, follower_id: int, following_id: int) -> bool:
        """Check if a user is following another user."""
        result = self.db.execute_query(
            "SELECT 1 FROM follows WHERE follower_id = ? AND following_id = ?",
            (follower_id, following_id)
        )
        return len(result) > 0

    def get_feed(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get activity feed from followed users."""
        return self.db.execute_query(
            """SELECT a.*, u.username, u.display_name
               FROM activities a
               JOIN follows f ON a.user_id = f.following_id
               JOIN users u ON a.user_id = u.id
               WHERE f.follower_id = ?
               ORDER BY a.created_at DESC
               LIMIT ?""",
            (user_id, limit)
        )


class LeaderboardService:
    """Service for community leaderboards."""

    def __init__(self):
        """Initialize leaderboard service."""
        self.db = get_database()

    def get_leaderboard(
        self,
        metric: str = 'roi',
        sport: Optional[str] = None,
        period: str = 'all_time',
        min_predictions: int = 10,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get leaderboard rankings.

        Args:
            metric: 'roi', 'win_rate', 'total_profit', 'streak'
            sport: Filter by sport (optional)
            period: 'daily', 'weekly', 'monthly', 'all_time'
            min_predictions: Minimum predictions to qualify
            limit: Number of users to return

        Returns:
            List of user rankings
        """
        # Map metric to column
        metric_map = {
            'roi': 's.roi',
            'win_rate': 's.win_rate',
            'total_profit': 's.total_profit_loss',
            'streak': 's.current_streak'
        }

        order_by = metric_map.get(metric, 's.roi')

        # Build query
        if sport:
            # Sport-specific leaderboard (requires joining predictions)
            query = f"""
                SELECT u.id, u.username, u.display_name, u.is_analyst, u.avatar_url,
                       COUNT(DISTINCT p.id) as predictions_count,
                       SUM(CASE WHEN p.status = 'won' THEN 1 ELSE 0 END) as wins,
                       SUM(CASE WHEN p.status = 'lost' THEN 1 ELSE 0 END) as losses,
                       SUM(COALESCE(p.result, 0)) as total_profit,
                       CASE WHEN COUNT(p.id) > 0
                            THEN CAST(SUM(CASE WHEN p.status = 'won' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(p.id)
                            ELSE 0 END as win_rate,
                       CASE WHEN SUM(COALESCE(p.stake, 0)) > 0
                            THEN SUM(COALESCE(p.result, 0)) / SUM(COALESCE(p.stake, 0))
                            ELSE 0 END as roi
                FROM users u
                JOIN predictions p ON u.id = p.user_id
                WHERE p.sport = ? AND p.status IN ('won', 'lost')
                GROUP BY u.id
                HAVING COUNT(p.id) >= ?
                ORDER BY roi DESC
                LIMIT ?
            """
            params = (sport, min_predictions, limit)
        else:
            # All-time leaderboard
            query = f"""
                SELECT u.id, u.username, u.display_name, u.is_analyst, u.avatar_url,
                       s.total_predictions, s.correct_predictions, s.win_rate,
                       s.roi, s.total_profit_loss, s.current_streak, s.best_streak,
                       s.reputation_score
                FROM users u
                JOIN user_stats s ON u.id = s.user_id
                WHERE s.total_predictions >= ?
                ORDER BY {order_by} DESC
                LIMIT ?
            """
            params = (min_predictions, limit)

        rankings = self.db.execute_query(query, params)

        # Add rank
        for i, user in enumerate(rankings, 1):
            user['rank'] = i

        return rankings

    def get_top_analysts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performing analysts."""
        return self.db.execute_query(
            """SELECT u.id, u.username, u.display_name, u.analyst_tier, u.avatar_url,
                      s.total_predictions, s.win_rate, s.roi, s.followers_count
               FROM users u
               JOIN user_stats s ON u.id = s.user_id
               WHERE u.is_analyst = 1 AND s.total_predictions >= 20
               ORDER BY s.roi DESC, s.followers_count DESC
               LIMIT ?""",
            (limit,)
        )


class LikeService:
    """Service for likes."""

    def __init__(self):
        """Initialize like service."""
        self.db = get_database()

    def like(self, user_id: int, target_type: str, target_id: int) -> Dict[str, Any]:
        """Like a prediction, discussion, or comment."""
        try:
            self.db.execute_update(
                "INSERT INTO likes (user_id, target_type, target_id) VALUES (?, ?, ?)",
                (user_id, target_type, target_id)
            )

            # Update like count
            table_map = {
                'prediction': 'predictions',
                'discussion': 'discussions',
                'comment': 'comments'
            }
            table = table_map.get(target_type)
            if table:
                self.db.execute_update(
                    f"UPDATE {table} SET likes_count = likes_count + 1 WHERE id = ?",
                    (target_id,)
                )

            return {"status": "liked"}
        except:
            raise ValueError("Already liked")

    def unlike(self, user_id: int, target_type: str, target_id: int) -> Dict[str, Any]:
        """Unlike a prediction, discussion, or comment."""
        self.db.execute_update(
            "DELETE FROM likes WHERE user_id = ? AND target_type = ? AND target_id = ?",
            (user_id, target_type, target_id)
        )

        # Update like count
        table_map = {
            'prediction': 'predictions',
            'discussion': 'discussions',
            'comment': 'comments'
        }
        table = table_map.get(target_type)
        if table:
            self.db.execute_update(
                f"UPDATE {table} SET likes_count = likes_count - 1 WHERE id = ?",
                (target_id,)
            )

        return {"status": "unliked"}

    def has_liked(self, user_id: int, target_type: str, target_id: int) -> bool:
        """Check if user has liked a target."""
        result = self.db.execute_query(
            "SELECT 1 FROM likes WHERE user_id = ? AND target_type = ? AND target_id = ?",
            (user_id, target_type, target_id)
        )
        return len(result) > 0
