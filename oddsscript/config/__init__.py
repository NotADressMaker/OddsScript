"""
Configuration management for OddsScript.

Provides centralized settings loaded from environment variables and .env files.
"""

from oddsscript.config.settings import (
    OddsScriptConfig,
    get_config,
    set_config,
    reset_config,
    load_config_from_env
)

__all__ = [
    'OddsScriptConfig',
    'get_config',
    'set_config',
    'reset_config',
    'load_config_from_env',
]
