"""
Authentication System for Social Features

User registration, login, and JWT token management.
"""

import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from .database import get_database


class AuthService:
    """User authentication service."""

    def __init__(self, secret_key: Optional[str] = None):
        """Initialize auth service."""
        self.db = get_database()
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.algorithm = "HS256"
        self.token_expiry = timedelta(days=7)

    def hash_password(self, password: str) -> str:
        """Hash a password using SHA-256 with salt."""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}${pwd_hash}"

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        try:
            salt, pwd_hash = password_hash.split('$')
            test_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return test_hash == pwd_hash
        except:
            return False

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        display_name: Optional[str] = None,
        bio: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new user account.

        Args:
            username: Unique username
            email: User email
            password: Plain text password (will be hashed)
            display_name: Display name (optional)
            bio: User bio (optional)

        Returns:
            User data dict

        Raises:
            ValueError: If username or email already exists
        """
        # Check if user exists
        existing = self.db.execute_query(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (username, email)
        )
        if existing:
            raise ValueError("Username or email already exists")

        # Hash password
        password_hash = self.hash_password(password)

        # Insert user
        user_id = self.db.execute_update(
            """INSERT INTO users (username, email, password_hash, display_name, bio)
               VALUES (?, ?, ?, ?, ?)""",
            (username, email, password_hash, display_name or username, bio)
        )

        # Create user stats entry
        self.db.execute_update(
            "INSERT INTO user_stats (user_id) VALUES (?)",
            (user_id,)
        )

        # Get created user
        user = self.db.execute_query(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )[0]

        # Remove password hash from response
        user = dict(user)
        del user['password_hash']

        return user

    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user.

        Args:
            username: Username or email
            password: Plain text password

        Returns:
            User data dict if authenticated, None otherwise
        """
        # Get user by username or email
        users = self.db.execute_query(
            "SELECT * FROM users WHERE username = ? OR email = ?",
            (username, username)
        )

        if not users:
            return None

        user = users[0]

        # Verify password
        if not self.verify_password(password, user['password_hash']):
            return None

        # Remove password hash from response
        user = dict(user)
        del user['password_hash']

        return user

    def create_token(self, user_id: int) -> str:
        """
        Create a JWT token for a user.

        Args:
            user_id: User ID

        Returns:
            JWT token string
        """
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + self.token_expiry,
            'iat': datetime.utcnow()
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def verify_token(self, token: str) -> Optional[int]:
        """
        Verify a JWT token and return user ID.

        Args:
            token: JWT token string

        Returns:
            User ID if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload.get('user_id')
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User data dict without password hash
        """
        users = self.db.execute_query(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )

        if not users:
            return None

        user = dict(users[0])
        del user['password_hash']
        return user

    def get_user_with_stats(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user with stats.

        Args:
            user_id: User ID

        Returns:
            User data dict with stats
        """
        results = self.db.execute_query(
            """SELECT u.*, s.*
               FROM users u
               LEFT JOIN user_stats s ON u.id = s.user_id
               WHERE u.id = ?""",
            (user_id,)
        )

        if not results:
            return None

        user = dict(results[0])
        del user['password_hash']
        return user

    def update_user_profile(
        self,
        user_id: int,
        display_name: Optional[str] = None,
        bio: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update user profile.

        Args:
            user_id: User ID
            display_name: New display name
            bio: New bio
            avatar_url: New avatar URL

        Returns:
            Updated user data
        """
        updates = []
        params = []

        if display_name is not None:
            updates.append("display_name = ?")
            params.append(display_name)

        if bio is not None:
            updates.append("bio = ?")
            params.append(bio)

        if avatar_url is not None:
            updates.append("avatar_url = ?")
            params.append(avatar_url)

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(user_id)

        if updates:
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            self.db.execute_update(query, tuple(params))

        return self.get_user(user_id)

    def promote_to_analyst(
        self,
        user_id: int,
        tier: str = 'amateur'
    ) -> Dict[str, Any]:
        """
        Promote user to analyst status.

        Args:
            user_id: User ID
            tier: Analyst tier ('amateur', 'pro', 'expert')

        Returns:
            Updated user data
        """
        self.db.execute_update(
            """UPDATE users
               SET is_analyst = 1, analyst_tier = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (tier, user_id)
        )

        return self.get_user(user_id)
