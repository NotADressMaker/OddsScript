"""
Centralized configuration management for OddsScript.

Loads configuration from environment variables and .env files.
Provides defaults for all settings.
"""

import os
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field, asdict
import json


@dataclass
class OddsScriptConfig:
    """Main configuration class for OddsScript"""

    # ===== Kelly Criterion Settings =====
    kelly_fraction: float = 0.25  # Quarter Kelly (recommended for safety)
    max_kelly_pct: float = 0.10   # Never bet more than 10% of bankroll

    # ===== Elo Rating Settings =====
    elo_k_factor: float = 32
    elo_home_advantage: float = 100
    elo_mov_multiplier: bool = True  # Apply margin of victory adjustments

    # ===== Sharp Money Detection =====
    sharp_rlm_threshold: float = 0.5  # Reverse line movement threshold
    sharp_velocity_threshold: float = 2.0  # Line velocity (points/hour)
    sharp_bet_money_diff: float = 10.0  # Bet% vs Money% difference

    # ===== Public Fade Settings =====
    public_fade_min_pct: float = 70.0  # Minimum public % to consider fading
    public_fade_primetime_bonus: float = 0.02  # Bonus edge for primetime games

    # ===== Arbitrage Settings =====
    arb_min_profit: float = 0.5  # Minimum 0.5% profit to flag arb
    arb_max_hold: float = 110.0  # Maximum hold % for valid market

    # ===== Parlay Settings =====
    parlay_max_legs: int = 4
    parlay_max_correlation: float = 0.3  # Maximum allowed correlation

    # ===== Odds Display =====
    default_odds_format: str = 'american'  # 'american', 'decimal', or 'fractional'
    decimal_places: int = 2

    # ===== Data Storage =====
    storage_backend: str = 'csv'  # 'csv' or 'sqlite'
    data_directory: Path = field(default_factory=lambda: Path.home() / '.oddsscript' / 'data')
    db_filename: str = 'oddsscript.db'

    # ===== Caching =====
    enable_cache: bool = True
    cache_ttl: int = 300  # Time-to-live in seconds (5 minutes)
    cache_max_size: int = 1000  # Maximum cached items

    # ===== Performance =====
    enable_multiprocessing: bool = True
    max_workers: int = 4  # CPU cores to use
    monte_carlo_threshold: int = 1000  # Min simulations for parallel processing

    # ===== Backtesting =====
    backtest_starting_bankroll: float = 1000.0
    backtest_default_strategy: str = 'kelly'

    # ===== Risk Management =====
    max_daily_risk: float = 0.05  # Max 5% of bankroll per day
    stop_loss_pct: float = 0.20   # Stop betting if down 20%
    min_edge_threshold: float = 0.02  # Minimum 2% edge to bet

    # ===== API Settings =====
    api_timeout: int = 30  # Seconds
    api_retry_attempts: int = 3

    def __post_init__(self):
        """Initialize configuration"""
        # Ensure data directory exists
        self.data_directory.mkdir(parents=True, exist_ok=True)

        # Convert string path to Path if needed
        if isinstance(self.data_directory, str):
            self.data_directory = Path(self.data_directory)

    @classmethod
    def from_env(cls, env_file: Optional[Path] = None) -> 'OddsScriptConfig':
        """
        Load configuration from environment variables

        Args:
            env_file: Optional path to .env file

        Returns:
            Configured OddsScriptConfig instance

        Environment variables:
            ODDSSCRIPT_KELLY_FRACTION: Kelly fraction (default: 0.25)
            ODDSSCRIPT_STORAGE_BACKEND: Storage backend (default: csv)
            ODDSSCRIPT_DATA_DIR: Data directory path
            ... (see .env.example for full list)
        """
        # Load .env file if provided
        if env_file and env_file.exists():
            cls._load_env_file(env_file)

        # Create config with defaults
        config = cls()

        # Override with environment variables
        def get_env_float(key: str, default: float) -> float:
            val = os.getenv(key)
            return float(val) if val else default

        def get_env_int(key: str, default: int) -> int:
            val = os.getenv(key)
            return int(val) if val else default

        def get_env_bool(key: str, default: bool) -> bool:
            val = os.getenv(key)
            if val is None:
                return default
            return val.lower() in ('true', '1', 'yes', 'on')

        # Kelly settings
        config.kelly_fraction = get_env_float('ODDSSCRIPT_KELLY_FRACTION', config.kelly_fraction)
        config.max_kelly_pct = get_env_float('ODDSSCRIPT_MAX_KELLY_PCT', config.max_kelly_pct)

        # Elo settings
        config.elo_k_factor = get_env_float('ODDSSCRIPT_ELO_K_FACTOR', config.elo_k_factor)
        config.elo_home_advantage = get_env_float('ODDSSCRIPT_ELO_HOME_ADVANTAGE', config.elo_home_advantage)

        # Sharp money settings
        config.sharp_rlm_threshold = get_env_float('ODDSSCRIPT_SHARP_RLM_THRESHOLD', config.sharp_rlm_threshold)
        config.sharp_velocity_threshold = get_env_float('ODDSSCRIPT_SHARP_VELOCITY_THRESHOLD', config.sharp_velocity_threshold)

        # Public fade settings
        config.public_fade_min_pct = get_env_float('ODDSSCRIPT_PUBLIC_FADE_MIN_PCT', config.public_fade_min_pct)

        # Storage settings
        config.storage_backend = os.getenv('ODDSSCRIPT_STORAGE_BACKEND', config.storage_backend)
        if data_dir := os.getenv('ODDSSCRIPT_DATA_DIR'):
            config.data_directory = Path(data_dir).expanduser()

        # Performance settings
        config.enable_multiprocessing = get_env_bool('ODDSSCRIPT_ENABLE_MULTIPROCESSING', config.enable_multiprocessing)
        config.max_workers = get_env_int('ODDSSCRIPT_MAX_WORKERS', config.max_workers)

        # Cache settings
        config.enable_cache = get_env_bool('ODDSSCRIPT_ENABLE_CACHE', config.enable_cache)
        config.cache_ttl = get_env_int('ODDSSCRIPT_CACHE_TTL', config.cache_ttl)

        # Display settings
        config.default_odds_format = os.getenv('ODDSSCRIPT_DEFAULT_ODDS_FORMAT', config.default_odds_format)
        config.decimal_places = get_env_int('ODDSSCRIPT_DECIMAL_PLACES', config.decimal_places)

        # Ensure data directory exists
        config.data_directory.mkdir(parents=True, exist_ok=True)

        return config

    @staticmethod
    def _load_env_file(env_file: Path):
        """Load environment variables from .env file"""
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # Parse KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    # Set environment variable
                    os.environ[key] = value

    def save_to_file(self, path: Path):
        """
        Save configuration to JSON file

        Args:
            path: Path to save config file
        """
        with open(path, 'w') as f:
            data = asdict(self)
            # Convert Path to string for JSON serialization
            data['data_directory'] = str(data['data_directory'])
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_file(cls, path: Path) -> 'OddsScriptConfig':
        """
        Load configuration from JSON file

        Args:
            path: Path to config file

        Returns:
            OddsScriptConfig instance
        """
        with open(path, 'r') as f:
            data = json.load(f)

        # Convert data_directory string to Path
        if 'data_directory' in data:
            data['data_directory'] = Path(data['data_directory'])

        return cls(**data)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        return getattr(self, key, default)

    def set(self, key: str, value: Any):
        """
        Set configuration value

        Args:
            key: Configuration key
            value: New value
        """
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            raise KeyError(f"Unknown configuration key: {key}")

    def to_dict(self) -> dict:
        """Convert configuration to dictionary"""
        data = asdict(self)
        data['data_directory'] = str(data['data_directory'])
        return data


# ===== Global Configuration Singleton =====

_config: Optional[OddsScriptConfig] = None


def get_config() -> OddsScriptConfig:
    """
    Get global configuration instance (singleton)

    Returns:
        OddsScriptConfig instance

    Examples:
        >>> from oddsscript.config import get_config
        >>> config = get_config()
        >>> config.kelly_fraction
        0.25
    """
    global _config
    if _config is None:
        _config = OddsScriptConfig.from_env()
    return _config


def set_config(config: OddsScriptConfig):
    """
    Set global configuration instance

    Args:
        config: New configuration instance
    """
    global _config
    _config = config


def reset_config():
    """Reset configuration to defaults"""
    global _config
    _config = None


def load_config_from_env(env_file: Optional[Path] = None) -> OddsScriptConfig:
    """
    Load and set global configuration from environment

    Args:
        env_file: Optional path to .env file

    Returns:
        Configured instance
    """
    config = OddsScriptConfig.from_env(env_file)
    set_config(config)
    return config
