"""
SportsBetLang - Domain-specific language and analytics suite for sports betting.

A comprehensive platform for:
- Sports betting calculations (odds, Kelly, EV)
- Sharp money detection and analysis
- Bet tracking and performance analysis
- Arbitrage and hedge calculations
- Portfolio optimization
- And much more!

Example usage:
    >>> from sportsbetlang import SportsBetLangAPI
    >>> api = SportsBetLangAPI()
    >>> api.convert_odds(-110, 'american', 'decimal')
    1.9091
    >>> api.calculate_kelly(odds=-110, true_prob=0.55, bankroll=1000)
    {'stake': 11.9, 'ev': 0.047, ...}
"""

from sportsbetlang.__version__ import __version__, __author__, __description__

# Core language
from sportsbetlang.lang import (
    Lexer,
    Parser,
    Interpreter,
    CodeGenerator,
    GeneratedCode,
    generate_code,
    JITCompiler,
    JITCompilationError,
    JITCompilationResult,
)

# Language boundary alias
from sportsbetlang import language

# Common utilities
from sportsbetlang.common import (
    american_to_decimal,
    decimal_to_american,
    implied_probability,
    calculate_kelly,
    ValidationError
)

# Betting math boundary
from sportsbetlang import betting

# Configuration
from sportsbetlang.config import get_config, set_config

# Data storage
from sportsbetlang.data import create_storage

# Models boundary
from sportsbetlang import models

__all__ = [
    # Version info
    '__version__',
    '__author__',
    '__description__',

    # Core language
    'Lexer',
    'Parser',
    'Interpreter',
    'CodeGenerator',
    'GeneratedCode',
    'generate_code',
    'JITCompiler',
    'JITCompilationError',
    'JITCompilationResult',
    'language',

    # Common utilities
    'american_to_decimal',
    'decimal_to_american',
    'implied_probability',
    'calculate_kelly',
    'ValidationError',
    'betting',

    # Configuration
    'get_config',
    'set_config',

    # Storage
    'create_storage',

    # Models
    'models',
]
