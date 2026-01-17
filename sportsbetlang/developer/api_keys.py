"""
Developer API Key Management System

API keys for third-party developers to access SportsBetLang services.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from enum import Enum

from sportsbetlang.social.database import get_database


class APIKeyTier(Enum):
    """API key tier levels."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class APIKeyService:
    """Service for managing developer API keys."""

    def __init__(self):
        """Initialize API key service."""
        self.db = get_database()
        self._init_tables()

    def _init_tables(self):
        """Initialize API key tables."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # API keys table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    key_hash TEXT UNIQUE NOT NULL,
                    key_prefix TEXT NOT NULL,
                    name TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    active BOOLEAN DEFAULT 1,
                    rate_limit INTEGER NOT NULL,
                    requests_today INTEGER DEFAULT 0,
                    requests_total INTEGER DEFAULT 0,
                    last_used_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # API usage logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_key_id INTEGER NOT NULL,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    status_code INTEGER,
                    response_time_ms INTEGER,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (api_key_id) REFERENCES api_keys(id)
                )
            """)

            # Webhooks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS webhooks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    api_key_id INTEGER NOT NULL,
                    url TEXT NOT NULL,
                    events TEXT NOT NULL,
                    secret TEXT NOT NULL,
                    active BOOLEAN DEFAULT 1,
                    failures INTEGER DEFAULT 0,
                    last_success_at TIMESTAMP,
                    last_failure_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (api_key_id) REFERENCES api_keys(id)
                )
            """)

            # Webhook delivery logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS webhook_deliveries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    webhook_id INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status_code INTEGER,
                    success BOOLEAN,
                    response TEXT,
                    attempts INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (webhook_id) REFERENCES webhooks(id)
                )
            """)

            # White-label configurations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS whitelabel_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    api_key_id INTEGER NOT NULL,
                    domain TEXT UNIQUE,
                    brand_name TEXT,
                    logo_url TEXT,
                    primary_color TEXT,
                    secondary_color TEXT,
                    custom_css TEXT,
                    features TEXT,
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (api_key_id) REFERENCES api_keys(id)
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(active)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_usage_key ON api_usage_logs(api_key_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_webhooks_user ON webhooks(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_webhook ON webhook_deliveries(webhook_id)")

            conn.commit()

    def generate_api_key(
        self,
        user_id: int,
        name: str,
        tier: str = APIKeyTier.FREE.value,
        expires_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a new API key for a user.

        Args:
            user_id: User ID
            name: Descriptive name for the key
            tier: API tier (free, pro, enterprise)
            expires_days: Days until expiration (None = never)

        Returns:
            API key data including the raw key (only shown once)
        """
        # Generate secure random key
        raw_key = f"sbl_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:12]  # For identification

        # Set rate limits based on tier
        rate_limits = {
            APIKeyTier.FREE.value: 1000,      # 1k requests/day
            APIKeyTier.PRO.value: 100000,     # 100k requests/day
            APIKeyTier.ENTERPRISE.value: -1   # Unlimited
        }
        rate_limit = rate_limits.get(tier, 1000)

        # Calculate expiration
        expires_at = None
        if expires_days:
            expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()

        # Insert key
        key_id = self.db.execute_update(
            """INSERT INTO api_keys
               (user_id, key_hash, key_prefix, name, tier, rate_limit, expires_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, key_hash, key_prefix, name, tier, rate_limit, expires_at)
        )

        return {
            "id": key_id,
            "key": raw_key,  # Only returned once!
            "key_prefix": key_prefix,
            "name": name,
            "tier": tier,
            "rate_limit": rate_limit,
            "expires_at": expires_at,
            "created_at": datetime.now().isoformat(),
            "warning": "Save this key securely. It won't be shown again."
        }

    def verify_api_key(self, raw_key: str) -> Optional[Dict[str, Any]]:
        """
        Verify an API key and return key info.

        Args:
            raw_key: The raw API key

        Returns:
            API key data if valid, None otherwise
        """
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        keys = self.db.execute_query(
            """SELECT * FROM api_keys
               WHERE key_hash = ? AND active = 1""",
            (key_hash,)
        )

        if not keys:
            return None

        key = dict(keys[0])

        # Check expiration
        if key['expires_at']:
            expires = datetime.fromisoformat(key['expires_at'])
            if datetime.now() > expires:
                return None

        # Check rate limit
        if key['rate_limit'] > 0 and key['requests_today'] >= key['rate_limit']:
            return None

        return key

    def increment_usage(self, key_id: int):
        """Increment API key usage counters."""
        self.db.execute_update(
            """UPDATE api_keys
               SET requests_today = requests_today + 1,
                   requests_total = requests_total + 1,
                   last_used_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (key_id,)
        )

    def log_request(
        self,
        api_key_id: int,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log API request for analytics."""
        self.db.execute_update(
            """INSERT INTO api_usage_logs
               (api_key_id, endpoint, method, status_code, response_time_ms, ip_address, user_agent)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (api_key_id, endpoint, method, status_code, response_time_ms, ip_address, user_agent)
        )

    def get_user_api_keys(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all API keys for a user."""
        return self.db.execute_query(
            """SELECT id, key_prefix, name, tier, rate_limit, requests_today,
                      requests_total, active, last_used_at, expires_at, created_at
               FROM api_keys
               WHERE user_id = ?
               ORDER BY created_at DESC""",
            (user_id,)
        )

    def revoke_api_key(self, key_id: int, user_id: int) -> bool:
        """Revoke an API key."""
        self.db.execute_update(
            """UPDATE api_keys
               SET active = 0
               WHERE id = ? AND user_id = ?""",
            (key_id, user_id)
        )
        return True

    def rotate_api_key(self, key_id: int, user_id: int) -> Dict[str, Any]:
        """
        Rotate an API key (revoke old, create new).

        Args:
            key_id: Old key ID
            user_id: User ID

        Returns:
            New API key data
        """
        # Get old key info
        old_keys = self.db.execute_query(
            "SELECT * FROM api_keys WHERE id = ? AND user_id = ?",
            (key_id, user_id)
        )

        if not old_keys:
            raise ValueError("API key not found")

        old_key = dict(old_keys[0])

        # Revoke old key
        self.revoke_api_key(key_id, user_id)

        # Generate new key with same settings
        new_key = self.generate_api_key(
            user_id=user_id,
            name=old_key['name'],
            tier=old_key['tier'],
            expires_days=None
        )

        return new_key

    def get_usage_stats(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Get API usage statistics for a user.

        Args:
            user_id: User ID
            days: Number of days to analyze

        Returns:
            Usage statistics
        """
        # Get total requests
        stats = self.db.execute_query(
            """SELECT
                   COUNT(*) as total_requests,
                   AVG(response_time_ms) as avg_response_time,
                   COUNT(DISTINCT endpoint) as unique_endpoints,
                   COUNT(DISTINCT DATE(created_at)) as active_days
               FROM api_usage_logs l
               JOIN api_keys k ON l.api_key_id = k.id
               WHERE k.user_id = ?
                 AND l.created_at >= datetime('now', '-' || ? || ' days')""",
            (user_id, days)
        )[0]

        # Get requests by endpoint
        top_endpoints = self.db.execute_query(
            """SELECT endpoint, COUNT(*) as count
               FROM api_usage_logs l
               JOIN api_keys k ON l.api_key_id = k.id
               WHERE k.user_id = ?
                 AND l.created_at >= datetime('now', '-' || ? || ' days')
               GROUP BY endpoint
               ORDER BY count DESC
               LIMIT 10""",
            (user_id, days)
        )

        # Get requests by status code
        status_codes = self.db.execute_query(
            """SELECT status_code, COUNT(*) as count
               FROM api_usage_logs l
               JOIN api_keys k ON l.api_key_id = k.id
               WHERE k.user_id = ?
                 AND l.created_at >= datetime('now', '-' || ? || ' days')
               GROUP BY status_code
               ORDER BY count DESC""",
            (user_id, days)
        )

        return {
            "period_days": days,
            "total_requests": stats['total_requests'] or 0,
            "avg_response_time_ms": stats['avg_response_time'] or 0,
            "unique_endpoints": stats['unique_endpoints'] or 0,
            "active_days": stats['active_days'] or 0,
            "top_endpoints": top_endpoints,
            "status_codes": status_codes
        }

    def reset_daily_limits(self):
        """Reset daily request counters (run via cron)."""
        self.db.execute_update("UPDATE api_keys SET requests_today = 0")


class WebhookService:
    """Service for managing webhooks."""

    def __init__(self):
        """Initialize webhook service."""
        self.db = get_database()

    def create_webhook(
        self,
        user_id: int,
        api_key_id: int,
        url: str,
        events: List[str]
    ) -> Dict[str, Any]:
        """
        Create a webhook subscription.

        Args:
            user_id: User ID
            api_key_id: API key ID
            url: Webhook URL
            events: List of event types to subscribe to

        Returns:
            Webhook data including secret
        """
        import json

        # Generate webhook secret
        secret = secrets.token_urlsafe(32)

        # Insert webhook
        webhook_id = self.db.execute_update(
            """INSERT INTO webhooks (user_id, api_key_id, url, events, secret)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, api_key_id, url, json.dumps(events), secret)
        )

        return {
            "id": webhook_id,
            "url": url,
            "events": events,
            "secret": secret,
            "active": True,
            "created_at": datetime.now().isoformat()
        }

    def get_user_webhooks(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all webhooks for a user."""
        import json

        webhooks = self.db.execute_query(
            """SELECT * FROM webhooks
               WHERE user_id = ?
               ORDER BY created_at DESC""",
            (user_id,)
        )

        for webhook in webhooks:
            webhook['events'] = json.loads(webhook['events'])

        return webhooks

    def delete_webhook(self, webhook_id: int, user_id: int):
        """Delete a webhook."""
        self.db.execute_update(
            "DELETE FROM webhooks WHERE id = ? AND user_id = ?",
            (webhook_id, user_id)
        )

    def trigger_webhook(
        self,
        event_type: str,
        payload: Dict[str, Any]
    ):
        """
        Trigger webhooks for an event type.

        Args:
            event_type: Type of event
            payload: Event data
        """
        import json
        import httpx
        import hmac

        # Get all webhooks subscribed to this event
        webhooks = self.db.execute_query(
            """SELECT * FROM webhooks
               WHERE active = 1
               AND json_extract(events, '$') LIKE ?""",
            (f'%{event_type}%',)
        )

        for webhook in webhooks:
            webhook_id = webhook['id']
            url = webhook['url']
            secret = webhook['secret']

            # Create payload with signature
            payload_json = json.dumps(payload)
            signature = hmac.new(
                secret.encode(),
                payload_json.encode(),
                'sha256'
            ).hexdigest()

            headers = {
                'Content-Type': 'application/json',
                'X-SportsBetLang-Event': event_type,
                'X-SportsBetLang-Signature': signature
            }

            # Deliver webhook (async in production)
            try:
                response = httpx.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=5.0
                )

                # Log delivery
                self.db.execute_update(
                    """INSERT INTO webhook_deliveries
                       (webhook_id, event_type, payload, status_code, success, response)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (webhook_id, event_type, payload_json, response.status_code,
                     response.status_code < 400, response.text[:1000])
                )

                # Update webhook stats
                if response.status_code < 400:
                    self.db.execute_update(
                        """UPDATE webhooks
                           SET failures = 0, last_success_at = CURRENT_TIMESTAMP
                           WHERE id = ?""",
                        (webhook_id,)
                    )
                else:
                    self.db.execute_update(
                        """UPDATE webhooks
                           SET failures = failures + 1, last_failure_at = CURRENT_TIMESTAMP
                           WHERE id = ?""",
                        (webhook_id,)
                    )

            except Exception as e:
                # Log failed delivery
                self.db.execute_update(
                    """INSERT INTO webhook_deliveries
                       (webhook_id, event_type, payload, success, response)
                       VALUES (?, ?, ?, ?, ?)""",
                    (webhook_id, event_type, payload_json, False, str(e)[:1000])
                )

                # Increment failures
                self.db.execute_update(
                    """UPDATE webhooks
                       SET failures = failures + 1, last_failure_at = CURRENT_TIMESTAMP
                       WHERE id = ?""",
                    (webhook_id,)
                )


class WhiteLabelService:
    """Service for white-label configurations."""

    def __init__(self):
        """Initialize white-label service."""
        self.db = get_database()

    def create_config(
        self,
        user_id: int,
        api_key_id: int,
        domain: str,
        brand_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Create white-label configuration."""
        import json

        config_id = self.db.execute_update(
            """INSERT INTO whitelabel_configs
               (user_id, api_key_id, domain, brand_name, logo_url, primary_color,
                secondary_color, custom_css, features)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, api_key_id, domain, brand_name,
             kwargs.get('logo_url'), kwargs.get('primary_color'),
             kwargs.get('secondary_color'), kwargs.get('custom_css'),
             json.dumps(kwargs.get('features', [])))
        )

        return self.get_config(config_id)

    def get_config(self, config_id: int) -> Optional[Dict[str, Any]]:
        """Get white-label configuration."""
        import json

        configs = self.db.execute_query(
            "SELECT * FROM whitelabel_configs WHERE id = ?",
            (config_id,)
        )

        if configs:
            config = dict(configs[0])
            config['features'] = json.loads(config['features'] or '[]')
            return config

        return None

    def get_config_by_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get white-label configuration by domain."""
        import json

        configs = self.db.execute_query(
            "SELECT * FROM whitelabel_configs WHERE domain = ? AND active = 1",
            (domain,)
        )

        if configs:
            config = dict(configs[0])
            config['features'] = json.loads(config['features'] or '[]')
            return config

        return None
