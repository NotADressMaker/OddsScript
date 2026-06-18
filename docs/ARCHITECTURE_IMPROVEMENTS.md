# SportsBetLang Architecture Improvement Plan

## Executive Summary

This document outlines concrete architectural improvements for SportsBetLang to enhance:
- **Maintainability**: Easier to update and extend
- **Scalability**: Handle larger datasets and more complex operations
- **Reusability**: Reduce code duplication across 36 Python files
- **Testability**: Comprehensive testing at all levels
- **Performance**: Optimize critical calculation paths
- **Usability**: Better APIs for both CLI and programmatic use

---

## Current Architecture Analysis

### Strengths ✅
- Clear separation between language core and utilities
- Pure Python implementation (no dependencies)
- Comprehensive tool suite (18 tools, 10 libraries)
- Consistent CLI interfaces using argparse
- Good documentation coverage

### Issues Identified ⚠️

1. **Code Duplication**
   - Odds conversion functions repeated in 15+ files
   - CSV handling logic duplicated across tools
   - Similar argparse patterns in every tool
   - Probability/EV calculations reimplemented

2. **No Shared Configuration**
   - Hard-coded values (K-factor, home advantage, vig rates)
   - No centralized settings management
   - Tool-specific defaults scattered

3. **Flat Module Structure**
   - All core files in root directory
   - No package hierarchy
   - Import paths unclear

4. **Limited Data Persistence**
   - CSV-only storage
   - No database option for large datasets
   - No caching layer

5. **Minimal Error Handling**
   - Basic try/except in some tools
   - No custom exception hierarchy
   - Limited input validation

6. **Testing Gaps**
   - Only core language tested
   - No tests for 18 tools
   - No integration tests
   - No performance benchmarks

7. **No Plugin Architecture**
   - Tools are standalone scripts
   - Can't dynamically load strategies
   - No extension points

8. **Performance Not Optimized**
   - Monte Carlo simulations could use multiprocessing
   - Large CSV parsing could be optimized
   - No memoization of expensive calculations

---

## Proposed Architecture

### 1. Project Structure Reorganization

**Current:**
```
programminglangauage/
├── lexer.py
├── parser.py
├── interpreter.py
├── oddsscript.py
├── lib/
├── tools/
├── strategies/
├── tests/
├── examples/
└── docs/
```

**Proposed:**
```
oddsscript/
├── setup.py                    # Package installation
├── pyproject.toml             # Modern Python packaging
├── README.md
├── .env.example               # Configuration template
│
├── oddsscript/                # Main package
│   ├── __init__.py
│   ├── __version__.py
│   │
│   ├── core/                  # Language core
│   │   ├── __init__.py
│   │   ├── lexer.py
│   │   ├── parser.py
│   │   ├── interpreter.py
│   │   ├── ast_nodes.py       # AST definitions
│   │   └── builtins.py        # Built-in functions
│   │
│   ├── common/                # Shared utilities
│   │   ├── __init__.py
│   │   ├── odds.py            # Odds conversions (DRY)
│   │   ├── probability.py     # Probability calculations
│   │   ├── kelly.py           # Kelly criterion
│   │   ├── ev.py              # Expected value
│   │   ├── math_utils.py      # Math helpers
│   │   └── validators.py      # Input validation
│   │
│   ├── data/                  # Data layer
│   │   ├── __init__.py
│   │   ├── storage.py         # Storage abstraction
│   │   ├── csv_adapter.py     # CSV implementation
│   │   ├── sqlite_adapter.py  # SQLite implementation
│   │   ├── cache.py           # Caching layer
│   │   └── models.py          # Data models
│   │
│   ├── config/                # Configuration
│   │   ├── __init__.py
│   │   ├── settings.py        # Settings management
│   │   └── defaults.py        # Default values
│   │
│   ├── analytics/             # Analytical libraries
│   │   ├── __init__.py
│   │   ├── statistics.py
│   │   ├── backtesting.py
│   │   ├── clv.py
│   │   ├── variance.py
│   │   ├── poisson.py
│   │   ├── elo.py
│   │   ├── expected_goals.py
│   │   ├── correlation.py
│   │   ├── regression.py
│   │   └── multi_outcome_kelly.py
│   │
│   ├── strategies/            # Betting strategies
│   │   ├── __init__.py
│   │   ├── base.py            # Strategy interface
│   │   ├── flat.py
│   │   ├── kelly.py
│   │   ├── martingale.py
│   │   └── fibonacci.py
│   │
│   ├── tools/                 # CLI tools
│   │   ├── __init__.py
│   │   ├── base_tool.py       # Base tool class
│   │   ├── odds_calc.py
│   │   ├── bet_tracker.py
│   │   ├── sharp_tracker.py
│   │   ├── public_fade.py
│   │   ├── parlay_optimizer.py
│   │   ├── arbitrage.py
│   │   ├── hedge.py
│   │   ├── portfolio.py
│   │   ├── teaser.py
│   │   ├── round_robin.py
│   │   ├── dutch.py
│   │   ├── market_maker.py
│   │   ├── line_tracker.py
│   │   ├── bankroll_sim.py
│   │   ├── bonus_calc.py
│   │   ├── tax_calc.py
│   │   └── performance.py
│   │
│   ├── api/                   # Programmatic API
│   │   ├── __init__.py
│   │   ├── client.py          # Main API client
│   │   └── endpoints.py       # API methods
│   │
│   └── cli/                   # CLI entry points
│       ├── __init__.py
│       ├── main.py            # Main CLI
│       └── helpers.py         # CLI utilities
│
├── tests/                     # Comprehensive tests
│   ├── __init__.py
│   ├── conftest.py           # Pytest configuration
│   ├── unit/                 # Unit tests
│   │   ├── test_core/
│   │   ├── test_common/
│   │   ├── test_analytics/
│   │   └── test_tools/
│   ├── integration/          # Integration tests
│   ├── performance/          # Performance tests
│   └── fixtures/             # Test data
│
├── examples/                  # Example code
│   ├── scripts/              # .sportsodds files
│   ├── notebooks/            # Jupyter notebooks
│   └── workflows/            # Common workflows
│
├── docs/                      # Documentation
│   ├── api/                  # API reference
│   ├── guides/               # User guides
│   ├── architecture/         # Architecture docs
│   └── contributing/         # Contribution guide
│
└── benchmarks/               # Performance benchmarks
    ├── odds_conversion.py
    ├── monte_carlo.py
    └── results/
```

---

## 2. Shared Utilities Module

Create `oddsscript/common/` to eliminate code duplication.

### oddsscript/common/odds.py
```python
"""
Centralized odds conversion utilities.

Used by all tools and libraries - single source of truth.
"""

from typing import Union
from decimal import Decimal
from enum import Enum


class OddsFormat(Enum):
    """Supported odds formats"""
    AMERICAN = "american"
    DECIMAL = "decimal"
    FRACTIONAL = "fractional"
    IMPLIED = "implied"


class OddsConverter:
    """High-precision odds conversion"""

    @staticmethod
    def american_to_decimal(odds: float, precision: int = 4) -> Decimal:
        """Convert American to decimal with configurable precision"""
        if odds > 0:
            result = (odds / 100) + 1
        else:
            result = (100 / abs(odds)) + 1
        return Decimal(str(result)).quantize(Decimal(f'0.{"0" * precision}'))

    @staticmethod
    def decimal_to_american(odds: float) -> float:
        """Convert decimal to American odds"""
        if odds >= 2.0:
            return (odds - 1) * 100
        else:
            return -100 / (odds - 1)

    @staticmethod
    def american_to_fractional(odds: float) -> str:
        """Convert American to fractional (e.g., '5/2')"""
        decimal = float(OddsConverter.american_to_decimal(odds))
        # Implementation using continued fractions
        # ... (full implementation)
        pass

    @staticmethod
    def to_implied_probability(odds: float, format: OddsFormat = OddsFormat.AMERICAN) -> Decimal:
        """Convert any format to implied probability"""
        if format == OddsFormat.AMERICAN:
            decimal = OddsConverter.american_to_decimal(odds)
        elif format == OddsFormat.DECIMAL:
            decimal = Decimal(str(odds))
        else:
            raise ValueError(f"Unsupported format: {format}")

        return (Decimal('1') / decimal).quantize(Decimal('0.0001'))

    @staticmethod
    def remove_vig(prob1: float, prob2: float, method: str = 'proportional') -> tuple:
        """
        Remove vig from probabilities

        Args:
            prob1, prob2: Implied probabilities
            method: 'proportional', 'power', or 'additive'

        Returns:
            Tuple of (fair_prob1, fair_prob2)
        """
        total = prob1 + prob2

        if method == 'proportional':
            return prob1 / total, prob2 / total
        elif method == 'power':
            # Shin method
            c = 0.025  # Estimated insider trading proportion
            # ... (implementation)
            pass
        elif method == 'additive':
            vig = total - 1
            return prob1 - vig/2, prob2 - vig/2
        else:
            raise ValueError(f"Unknown method: {method}")


# Convenience functions
american_to_decimal = OddsConverter.american_to_decimal
decimal_to_american = OddsConverter.decimal_to_american
implied_probability = OddsConverter.to_implied_probability
remove_vig = OddsConverter.remove_vig
```

### oddsscript/common/kelly.py
```python
"""Kelly Criterion calculations - single implementation"""

from typing import Optional
from decimal import Decimal


class KellyCriterion:
    """Kelly criterion for optimal bet sizing"""

    @staticmethod
    def calculate(
        odds: float,
        true_prob: float,
        kelly_fraction: float = 1.0,
        bankroll: Optional[float] = None
    ) -> dict:
        """
        Calculate Kelly stake

        Args:
            odds: American odds
            true_prob: True probability (0-1)
            kelly_fraction: Fraction of full Kelly (default 1.0)
            bankroll: Optional bankroll for absolute stake

        Returns:
            Dict with kelly_pct, kelly_fraction, stake, ev, etc.
        """
        from oddsscript.common.odds import american_to_decimal

        decimal_odds = float(american_to_decimal(odds))
        b = decimal_odds - 1  # Net odds
        p = true_prob
        q = 1 - p

        # Kelly formula: (bp - q) / b
        kelly_pct = (b * p - q) / b

        # Apply fractional Kelly
        fractional_kelly = kelly_pct * kelly_fraction

        # Ensure non-negative
        fractional_kelly = max(0, fractional_kelly)

        # Calculate expected value
        ev = p * b - q

        result = {
            'kelly_pct': kelly_pct,
            'fractional_kelly': fractional_kelly,
            'kelly_fraction': kelly_fraction,
            'ev': ev,
            'edge': p - (1 / decimal_odds),
            'recommended': 'BET' if fractional_kelly > 0 else 'NO BET'
        }

        if bankroll:
            result['stake'] = fractional_kelly * bankroll

        return result

    @staticmethod
    def multi_outcome(
        outcomes: list,
        bankroll: float = 1000,
        kelly_fraction: float = 0.25
    ) -> dict:
        """
        Multi-outcome Kelly (horse racing, golf, etc.)

        Args:
            outcomes: List of {'odds': float, 'prob': float}
            bankroll: Total bankroll
            kelly_fraction: Fraction of full Kelly

        Returns:
            Optimal stakes for each outcome
        """
        # Implementation from multi_outcome_kelly.py
        # ... (full implementation)
        pass
```

### oddsscript/common/validators.py
```python
"""Input validation for all tools"""

from typing import Any, Union


class ValidationError(Exception):
    """Custom validation error"""
    pass


class Validators:
    """Common input validators"""

    @staticmethod
    def validate_odds(odds: float, format: str = 'american') -> float:
        """Validate odds are in valid range"""
        if format == 'american':
            if -10000 < odds < -100 or 100 < odds < 10000:
                return odds
            raise ValidationError(f"Invalid American odds: {odds} (must be <-100 or >100)")
        elif format == 'decimal':
            if odds >= 1.01:
                return odds
            raise ValidationError(f"Invalid decimal odds: {odds} (must be >= 1.01)")
        else:
            raise ValidationError(f"Unknown format: {format}")

    @staticmethod
    def validate_probability(prob: float) -> float:
        """Validate probability is between 0 and 1"""
        if 0 <= prob <= 1:
            return prob
        raise ValidationError(f"Invalid probability: {prob} (must be 0-1)")

    @staticmethod
    def validate_stake(stake: float) -> float:
        """Validate stake is positive"""
        if stake > 0:
            return stake
        raise ValidationError(f"Invalid stake: {stake} (must be positive)")

    @staticmethod
    def validate_bankroll(bankroll: float) -> float:
        """Validate bankroll is positive"""
        if bankroll > 0:
            return bankroll
        raise ValidationError(f"Invalid bankroll: {bankroll} (must be positive)")

    @staticmethod
    def validate_kelly_fraction(fraction: float) -> float:
        """Validate Kelly fraction"""
        if 0 < fraction <= 1:
            return fraction
        raise ValidationError(f"Invalid Kelly fraction: {fraction} (must be 0-1)")
```

---

## 3. Configuration Management

Create `oddsscript/config/` for centralized settings.

### oddsscript/config/settings.py
```python
"""
Centralized configuration management.

Loads from environment variables and .env files.
"""

import os
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field


@dataclass
class SportsBetLangConfig:
    """Main configuration class"""

    # Kelly settings
    kelly_fraction: float = 0.25
    max_kelly_pct: float = 0.10  # Never bet more than 10% of bankroll

    # Elo settings
    elo_k_factor: float = 32
    elo_home_advantage: float = 100

    # Sharp money thresholds
    sharp_rlm_threshold: float = 0.5
    sharp_velocity_threshold: float = 2.0

    # Public fade thresholds
    public_fade_min_pct: float = 70

    # Arbitrage settings
    arb_min_profit: float = 0.5  # Minimum 0.5% profit

    # Data storage
    storage_backend: str = 'csv'  # 'csv' or 'sqlite'
    data_directory: Path = field(default_factory=lambda: Path.home() / '.oddsscript' / 'data')

    # Caching
    enable_cache: bool = True
    cache_ttl: int = 300  # 5 minutes

    # Display
    default_odds_format: str = 'american'
    decimal_places: int = 2

    # Performance
    enable_multiprocessing: bool = True
    max_workers: int = 4

    def __post_init__(self):
        """Create data directory if it doesn't exist"""
        self.data_directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> 'SportsBetLangConfig':
        """Load configuration from environment variables"""
        config = cls()

        # Override with environment variables if present
        if val := os.getenv('ODDSSCRIPT_KELLY_FRACTION'):
            config.kelly_fraction = float(val)

        if val := os.getenv('ODDSSCRIPT_STORAGE_BACKEND'):
            config.storage_backend = val

        if val := os.getenv('ODDSSCRIPT_DATA_DIR'):
            config.data_directory = Path(val)

        # ... (load all settings)

        return config

    def save_to_file(self, path: Path):
        """Save configuration to file"""
        import json
        with open(path, 'w') as f:
            json.dump(self.__dict__, f, indent=2, default=str)

    @classmethod
    def load_from_file(cls, path: Path) -> 'SportsBetLangConfig':
        """Load configuration from file"""
        import json
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(**data)


# Global config instance
_config: Optional[SportsBetLangConfig] = None


def get_config() -> SportsBetLangConfig:
    """Get global configuration (singleton)"""
    global _config
    if _config is None:
        _config = SportsBetLangConfig.from_env()
    return _config


def set_config(config: SportsBetLangConfig):
    """Set global configuration"""
    global _config
    _config = config
```

### .env.example
```bash
# SportsBetLang Configuration

# Kelly Criterion Settings
ODDSSCRIPT_KELLY_FRACTION=0.25
ODDSSCRIPT_MAX_KELLY_PCT=0.10

# Elo Rating Settings
ODDSSCRIPT_ELO_K_FACTOR=32
ODDSSCRIPT_ELO_HOME_ADVANTAGE=100

# Sharp Money Detection
ODDSSCRIPT_SHARP_RLM_THRESHOLD=0.5
ODDSSCRIPT_SHARP_VELOCITY_THRESHOLD=2.0

# Public Fade Settings
ODDSSCRIPT_PUBLIC_FADE_MIN_PCT=70

# Data Storage
ODDSSCRIPT_STORAGE_BACKEND=csv  # csv or sqlite
ODDSSCRIPT_DATA_DIR=~/.oddsscript/data

# Performance
ODDSSCRIPT_ENABLE_MULTIPROCESSING=true
ODDSSCRIPT_MAX_WORKERS=4

# Display
ODDSSCRIPT_DEFAULT_ODDS_FORMAT=american
ODDSSCRIPT_DECIMAL_PLACES=2
```

---

## 4. Data Layer Abstraction

Create `oddsscript/data/` for storage abstraction.

### oddsscript/data/storage.py
```python
"""
Storage abstraction layer.

Supports CSV and SQLite backends with same interface.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path


class StorageBackend(ABC):
    """Abstract storage interface"""

    @abstractmethod
    def save_bet(self, bet: Dict[str, Any]) -> str:
        """Save bet and return ID"""
        pass

    @abstractmethod
    def get_bet(self, bet_id: str) -> Optional[Dict[str, Any]]:
        """Get bet by ID"""
        pass

    @abstractmethod
    def update_bet(self, bet_id: str, updates: Dict[str, Any]) -> bool:
        """Update bet"""
        pass

    @abstractmethod
    def list_bets(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """List bets with optional filters"""
        pass

    @abstractmethod
    def delete_bet(self, bet_id: str) -> bool:
        """Delete bet"""
        pass

    @abstractmethod
    def save_line_movement(self, line: Dict[str, Any]) -> str:
        """Save line movement data"""
        pass

    @abstractmethod
    def get_line_history(
        self,
        game_id: str,
        sportsbook: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get line movement history"""
        pass


class CSVStorage(StorageBackend):
    """CSV-based storage (existing implementation)"""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.bets_file = data_dir / 'bets.csv'
        self.lines_file = data_dir / 'lines.csv'

    def save_bet(self, bet: Dict[str, Any]) -> str:
        """Save to CSV"""
        # Implementation
        pass

    # ... (implement all methods)


class SQLiteStorage(StorageBackend):
    """SQLite-based storage for better performance"""

    def __init__(self, db_path: Path):
        import sqlite3
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self):
        """Create database schema"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS bets (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                sport TEXT,
                description TEXT,
                odds REAL,
                stake REAL,
                result TEXT,
                profit REAL,
                clv REAL,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS line_movements (
                id TEXT PRIMARY KEY,
                game_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                sportsbook TEXT,
                bet_type TEXT,
                line REAL,
                odds REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_bets_date ON bets(date);
            CREATE INDEX IF NOT EXISTS idx_bets_sport ON bets(sport);
            CREATE INDEX IF NOT EXISTS idx_lines_game ON line_movements(game_id);
        """)

        self.conn.commit()

    def save_bet(self, bet: Dict[str, Any]) -> str:
        """Save to SQLite"""
        import uuid
        import json

        bet_id = str(uuid.uuid4())

        self.conn.execute("""
            INSERT INTO bets
            (id, date, sport, description, odds, stake, result, profit, clv, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bet_id,
            bet.get('date'),
            bet.get('sport'),
            bet.get('description'),
            bet.get('odds'),
            bet.get('stake'),
            bet.get('result'),
            bet.get('profit'),
            bet.get('clv'),
            json.dumps(bet.get('metadata', {}))
        ))

        self.conn.commit()
        return bet_id

    # ... (implement all methods with proper SQL)


def create_storage(backend: str = 'csv', **kwargs) -> StorageBackend:
    """Factory function to create storage backend"""
    if backend == 'csv':
        from oddsscript.config import get_config
        return CSVStorage(get_config().data_directory)
    elif backend == 'sqlite':
        from oddsscript.config import get_config
        db_path = get_config().data_directory / 'oddsscript.db'
        return SQLiteStorage(db_path)
    else:
        raise ValueError(f"Unknown backend: {backend}")
```

---

## 5. Base Tool Class

Create `oddsscript/tools/base_tool.py` to reduce CLI duplication.

```python
"""
Base class for all CLI tools.

Provides common functionality:
- Argument parsing patterns
- Configuration access
- Storage access
- Error handling
- Output formatting
"""

import argparse
import sys
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from oddsscript.config import get_config
from oddsscript.data.storage import create_storage
from oddsscript.common.validators import ValidationError


class BaseTool(ABC):
    """Base class for CLI tools"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.config = get_config()
        self.storage = create_storage(self.config.storage_backend)
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser with common arguments"""
        parser = argparse.ArgumentParser(
            prog=self.name,
            description=self.description,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        # Common arguments for all tools
        parser.add_argument(
            '--config',
            type=str,
            help='Path to configuration file'
        )

        parser.add_argument(
            '--output-format',
            choices=['text', 'json', 'csv'],
            default='text',
            help='Output format (default: text)'
        )

        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Verbose output'
        )

        return parser

    @abstractmethod
    def add_arguments(self, parser: argparse.ArgumentParser):
        """Add tool-specific arguments (implement in subclass)"""
        pass

    @abstractmethod
    def run(self, args: argparse.Namespace) -> int:
        """Run tool logic (implement in subclass)"""
        pass

    def main(self, argv: Optional[List[str]] = None) -> int:
        """Main entry point"""
        # Add tool-specific arguments
        self.add_arguments(self.parser)

        # Parse arguments
        args = self.parser.parse_args(argv)

        # Load custom config if specified
        if args.config:
            from pathlib import Path
            from oddsscript.config import SportsBetLangConfig, set_config
            config = SportsBetLangConfig.load_from_file(Path(args.config))
            set_config(config)
            self.config = config

        try:
            # Run tool
            return self.run(args)

        except ValidationError as e:
            self.print_error(f"Validation Error: {e}")
            return 1

        except KeyboardInterrupt:
            self.print_error("\nInterrupted by user")
            return 130

        except Exception as e:
            if args.verbose:
                import traceback
                traceback.print_exc()
            else:
                self.print_error(f"Error: {e}")
            return 1

    def print_output(self, data: Any, format: str = 'text'):
        """Print output in specified format"""
        if format == 'json':
            import json
            print(json.dumps(data, indent=2, default=str))
        elif format == 'csv':
            import csv
            import sys
            if isinstance(data, list) and len(data) > 0:
                writer = csv.DictWriter(sys.stdout, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
        else:
            # Text format (default)
            print(data)

    def print_error(self, message: str):
        """Print error message to stderr"""
        print(f"❌ {message}", file=sys.stderr)

    def print_success(self, message: str):
        """Print success message"""
        print(f"✅ {message}")

    def print_warning(self, message: str):
        """Print warning message"""
        print(f"⚠️  {message}")
```

### Example: Refactored Sharp Tracker

```python
"""Sharp Money Tracker using base tool class"""

from oddsscript.tools.base_tool import BaseTool
from oddsscript.analytics.sharp import SharpMoneyAnalyzer
import argparse


class SharpTrackerTool(BaseTool):
    """CLI tool for sharp money detection"""

    def __init__(self):
        super().__init__(
            name='sharp-tracker',
            description='Advanced sharp money detection'
        )

    def add_arguments(self, parser: argparse.ArgumentParser):
        """Add sharp tracker specific arguments"""
        subparsers = parser.add_subparsers(dest='command')

        # Analyze command
        analyze = subparsers.add_parser('analyze', help='Analyze sharp signals')
        analyze.add_argument('--game', required=True)
        analyze.add_argument('--open-line', type=float, required=True)
        analyze.add_argument('--current-line', type=float, required=True)
        # ... more arguments

    def run(self, args: argparse.Namespace) -> int:
        """Run sharp tracker"""
        if args.command == 'analyze':
            analyzer = SharpMoneyAnalyzer(self.config)
            result = analyzer.analyze(
                game=args.game,
                open_line=args.open_line,
                current_line=args.current_line
            )

            self.print_output(result, args.output_format)
            return 0

        else:
            self.parser.print_help()
            return 1


def main():
    tool = SharpTrackerTool()
    return tool.main()


if __name__ == '__main__':
    sys.exit(main())
```

---

## 6. Plugin Architecture for Strategies

Create extensible strategy system.

### oddsscript/strategies/base.py
```python
"""Base strategy interface for plugins"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class BetRecommendation:
    """Recommendation from strategy"""
    should_bet: bool
    stake: float
    confidence: float  # 0-1
    reasoning: str
    metadata: Dict[str, Any]


class BettingStrategy(ABC):
    """Abstract base class for betting strategies"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Strategy description"""
        pass

    @abstractmethod
    def calculate_stake(
        self,
        bankroll: float,
        odds: float,
        edge: float,
        **kwargs
    ) -> BetRecommendation:
        """
        Calculate recommended stake

        Args:
            bankroll: Current bankroll
            odds: American odds
            edge: Estimated edge (0-1)
            **kwargs: Strategy-specific parameters

        Returns:
            BetRecommendation
        """
        pass

    def validate_parameters(self, **kwargs):
        """Validate strategy parameters"""
        pass


class StrategyRegistry:
    """Registry for dynamically loaded strategies"""

    _strategies: Dict[str, type[BettingStrategy]] = {}

    @classmethod
    def register(cls, strategy_class: type[BettingStrategy]):
        """Register a strategy"""
        instance = strategy_class()
        cls._strategies[instance.name] = strategy_class
        return strategy_class

    @classmethod
    def get(cls, name: str) -> BettingStrategy:
        """Get strategy by name"""
        if name not in cls._strategies:
            raise ValueError(f"Unknown strategy: {name}")
        return cls._strategies[name]()

    @classmethod
    def list_strategies(cls) -> List[str]:
        """List available strategies"""
        return list(cls._strategies.keys())


# Decorator for easy registration
def register_strategy(cls):
    """Decorator to register strategy"""
    return StrategyRegistry.register(cls)
```

### Refactored Kelly Strategy

```python
"""Kelly Criterion strategy"""

from oddsscript.strategies.base import BettingStrategy, BetRecommendation, register_strategy
from oddsscript.common.kelly import KellyCriterion
from oddsscript.common.validators import Validators


@register_strategy
class KellyStrategy(BettingStrategy):
    """Kelly Criterion betting strategy"""

    @property
    def name(self) -> str:
        return "kelly"

    @property
    def description(self) -> str:
        return "Kelly Criterion optimal bet sizing"

    def calculate_stake(
        self,
        bankroll: float,
        odds: float,
        edge: float,
        kelly_fraction: float = 0.25,
        **kwargs
    ) -> BetRecommendation:
        """Calculate Kelly stake"""

        # Validate inputs
        Validators.validate_bankroll(bankroll)
        Validators.validate_odds(odds)
        Validators.validate_kelly_fraction(kelly_fraction)

        # Calculate Kelly
        true_prob = edge + (1 / (abs(odds)/100 + 1))  # Approximate
        result = KellyCriterion.calculate(
            odds=odds,
            true_prob=true_prob,
            kelly_fraction=kelly_fraction,
            bankroll=bankroll
        )

        should_bet = result['fractional_kelly'] > 0.01  # Minimum 1% of bankroll

        return BetRecommendation(
            should_bet=should_bet,
            stake=result.get('stake', 0),
            confidence=min(1.0, edge * 10),  # Scale edge to confidence
            reasoning=f"Kelly: {result['fractional_kelly']*100:.2f}% of bankroll (Edge: {edge*100:+.2f}%)",
            metadata=result
        )
```

---

## 7. Comprehensive Testing

Expand test suite to cover all components.

### tests/conftest.py
```python
"""Pytest configuration and fixtures"""

import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_data_dir():
    """Create temporary data directory"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_config(temp_data_dir):
    """Create sample configuration"""
    from oddsscript.config import SportsBetLangConfig
    return SportsBetLangConfig(
        data_directory=temp_data_dir,
        storage_backend='csv'
    )


@pytest.fixture
def sample_bets():
    """Sample bet data for testing"""
    return [
        {
            'date': '2024-01-15',
            'sport': 'nfl',
            'description': 'Chiefs -3',
            'odds': -110,
            'stake': 110,
            'result': 'win',
            'profit': 100
        },
        {
            'date': '2024-01-16',
            'sport': 'nba',
            'description': 'Lakers ML',
            'odds': -150,
            'stake': 150,
            'result': 'loss',
            'profit': -150
        }
    ]


@pytest.fixture
def storage(sample_config):
    """Create storage backend"""
    from oddsscript.data.storage import create_storage
    return create_storage('csv', data_dir=sample_config.data_directory)
```

### tests/unit/test_common/test_odds.py
```python
"""Test odds conversion utilities"""

import pytest
from decimal import Decimal
from oddsscript.common.odds import OddsConverter, ValidationError


class TestOddsConverter:
    """Test OddsConverter class"""

    def test_american_to_decimal_positive(self):
        """Test positive American odds"""
        result = OddsConverter.american_to_decimal(150)
        assert result == Decimal('2.5')

    def test_american_to_decimal_negative(self):
        """Test negative American odds"""
        result = OddsConverter.american_to_decimal(-150)
        assert result == Decimal('1.6667')

    def test_decimal_to_american_favorite(self):
        """Test decimal to American for favorite"""
        result = OddsConverter.decimal_to_american(1.6667)
        assert abs(result - (-150)) < 1  # Allow small rounding error

    def test_decimal_to_american_underdog(self):
        """Test decimal to American for underdog"""
        result = OddsConverter.decimal_to_american(2.5)
        assert result == 150

    def test_implied_probability(self):
        """Test implied probability calculation"""
        prob = OddsConverter.to_implied_probability(-110)
        assert abs(float(prob) - 0.5238) < 0.0001

    def test_remove_vig_proportional(self):
        """Test vig removal"""
        fair1, fair2 = OddsConverter.remove_vig(0.5238, 0.5238, method='proportional')
        assert abs(fair1 - 0.5) < 0.0001
        assert abs(fair2 - 0.5) < 0.0001


class TestValidators:
    """Test input validators"""

    def test_valid_american_odds(self):
        """Test valid odds pass"""
        from oddsscript.common.validators import Validators
        assert Validators.validate_odds(-110) == -110
        assert Validators.validate_odds(150) == 150

    def test_invalid_american_odds(self):
        """Test invalid odds raise error"""
        from oddsscript.common.validators import Validators, ValidationError

        with pytest.raises(ValidationError):
            Validators.validate_odds(-50)  # Too close to even

        with pytest.raises(ValidationError):
            Validators.validate_odds(50)  # Too close to even

    def test_valid_probability(self):
        """Test valid probability"""
        from oddsscript.common.validators import Validators
        assert Validators.validate_probability(0.5) == 0.5
        assert Validators.validate_probability(0.0) == 0.0
        assert Validators.validate_probability(1.0) == 1.0

    def test_invalid_probability(self):
        """Test invalid probability"""
        from oddsscript.common.validators import Validators, ValidationError

        with pytest.raises(ValidationError):
            Validators.validate_probability(1.5)

        with pytest.raises(ValidationError):
            Validators.validate_probability(-0.1)
```

### tests/integration/test_bet_tracking.py
```python
"""Integration tests for bet tracking workflow"""

import pytest
from oddsscript.tools.bet_tracker import BetTrackerTool


def test_full_bet_lifecycle(temp_data_dir, sample_config):
    """Test adding, settling, and querying bets"""

    # Create tool
    tool = BetTrackerTool()

    # Add bet
    result = tool.main(['add', '--sport', 'nfl', '--desc', 'Chiefs -3',
                        '--odds', '-110', '--stake', '110'])
    assert result == 0

    # Settle bet
    result = tool.main(['settle', '--id', '1', '--result', 'win'])
    assert result == 0

    # Get stats
    result = tool.main(['stats'])
    assert result == 0
```

### Run tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=oddsscript --cov-report=html

# Run specific test file
pytest tests/unit/test_common/test_odds.py

# Run performance tests
pytest tests/performance/ --benchmark-only
```

---

## 8. Performance Optimizations

### Multiprocessing for Monte Carlo

```python
"""Optimized Monte Carlo simulations using multiprocessing"""

from multiprocessing import Pool, cpu_count
from typing import List, Callable
import numpy as np


class MonteCarloEngine:
    """Parallelized Monte Carlo engine"""

    @staticmethod
    def run_parallel(
        simulation_func: Callable,
        n_simulations: int,
        **kwargs
    ) -> List:
        """
        Run simulations in parallel

        Args:
            simulation_func: Function to run (must be picklable)
            n_simulations: Total simulations
            **kwargs: Arguments to simulation_func

        Returns:
            Combined results from all workers
        """
        from oddsscript.config import get_config

        config = get_config()

        if not config.enable_multiprocessing or n_simulations < 1000:
            # Run serially for small jobs
            return [simulation_func(**kwargs) for _ in range(n_simulations)]

        # Split work across workers
        n_workers = min(config.max_workers, cpu_count())
        sims_per_worker = n_simulations // n_workers

        # Prepare worker arguments
        worker_args = [
            (simulation_func, sims_per_worker, kwargs)
            for _ in range(n_workers)
        ]

        # Run in parallel
        with Pool(n_workers) as pool:
            results = pool.starmap(_worker_func, worker_args)

        # Flatten results
        return [item for sublist in results for item in sublist]


def _worker_func(func, n, kwargs):
    """Worker function for multiprocessing"""
    return [func(**kwargs) for _ in range(n)]
```

### Caching Layer

```python
"""Caching for expensive calculations"""

import functools
import time
from typing import Any, Callable


class Cache:
    """Simple TTL cache"""

    def __init__(self, ttl: int = 300):
        self.ttl = ttl
        self.cache = {}

    def get(self, key: str) -> Any:
        """Get from cache if not expired"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: Any):
        """Set cache value"""
        self.cache[key] = (value, time.time())

    def clear(self):
        """Clear cache"""
        self.cache.clear()


# Global cache instance
_cache = None


def get_cache():
    """Get global cache"""
    global _cache
    if _cache is None:
        from oddsscript.config import get_config
        _cache = Cache(ttl=get_config().cache_ttl)
    return _cache


def cached(key_func: Callable = None):
    """Decorator for caching function results"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from oddsscript.config import get_config

            if not get_config().enable_cache:
                return func(*args, **kwargs)

            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{args}:{kwargs}"

            # Check cache
            cache = get_cache()
            result = cache.get(cache_key)

            if result is not None:
                return result

            # Compute and cache
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            return result

        return wrapper
    return decorator


# Example usage
@cached(lambda odds: f"american_to_decimal:{odds}")
def american_to_decimal_cached(odds: float):
    """Cached odds conversion"""
    # Expensive calculation (mocked)
    time.sleep(0.001)
    return (odds / 100) + 1 if odds > 0 else (100 / abs(odds)) + 1
```

---

## 9. Programmatic API

Create Python API for non-CLI usage.

### oddsscript/api/client.py
```python
"""
Programmatic API for SportsBetLang.

Use SportsBetLang as a library in your own applications.
"""

from typing import List, Dict, Any, Optional
from oddsscript.config import SportsBetLangConfig, get_config, set_config
from oddsscript.data.storage import create_storage, StorageBackend
from oddsscript.strategies.base import StrategyRegistry


class SportsBetLangAPI:
    """Main API client"""

    def __init__(self, config: Optional[SportsBetLangConfig] = None):
        """
        Initialize API

        Args:
            config: Optional custom configuration
        """
        if config:
            set_config(config)

        self.config = get_config()
        self.storage = create_storage(self.config.storage_backend)

    # Odds conversions
    def convert_odds(
        self,
        odds: float,
        from_format: str = 'american',
        to_format: str = 'decimal'
    ) -> float:
        """Convert between odds formats"""
        from oddsscript.common.odds import OddsConverter

        if from_format == 'american' and to_format == 'decimal':
            return float(OddsConverter.american_to_decimal(odds))
        elif from_format == 'decimal' and to_format == 'american':
            return OddsConverter.decimal_to_american(odds)
        else:
            raise ValueError(f"Unsupported conversion: {from_format} -> {to_format}")

    def implied_probability(self, odds: float, format: str = 'american') -> float:
        """Calculate implied probability"""
        from oddsscript.common.odds import OddsConverter, OddsFormat
        return float(OddsConverter.to_implied_probability(
            odds,
            OddsFormat.AMERICAN if format == 'american' else OddsFormat.DECIMAL
        ))

    # Kelly Criterion
    def calculate_kelly(
        self,
        odds: float,
        true_prob: float,
        bankroll: float,
        kelly_fraction: float = 0.25
    ) -> Dict[str, Any]:
        """Calculate Kelly stake"""
        from oddsscript.common.kelly import KellyCriterion
        return KellyCriterion.calculate(odds, true_prob, kelly_fraction, bankroll)

    # Bet tracking
    def add_bet(
        self,
        date: str,
        sport: str,
        description: str,
        odds: float,
        stake: float,
        **metadata
    ) -> str:
        """Add bet to tracker"""
        bet = {
            'date': date,
            'sport': sport,
            'description': description,
            'odds': odds,
            'stake': stake,
            'result': None,
            'profit': None,
            'metadata': metadata
        }
        return self.storage.save_bet(bet)

    def settle_bet(
        self,
        bet_id: str,
        result: str,
        profit: Optional[float] = None
    ) -> bool:
        """Settle bet"""
        updates = {'result': result}

        if profit is not None:
            updates['profit'] = profit
        elif result == 'win':
            bet = self.storage.get_bet(bet_id)
            updates['profit'] = self.calculate_payout(bet['odds'], bet['stake']) - bet['stake']
        elif result == 'loss':
            bet = self.storage.get_bet(bet_id)
            updates['profit'] = -bet['stake']
        else:  # push
            updates['profit'] = 0

        return self.storage.update_bet(bet_id, updates)

    def get_stats(
        self,
        sport: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get betting statistics"""
        filters = {}
        if sport:
            filters['sport'] = sport

        bets = self.storage.list_bets(filters=filters)

        # Calculate stats
        total_bets = len(bets)
        settled = [b for b in bets if b['result']]
        wins = len([b for b in settled if b['result'] == 'win'])
        losses = len([b for b in settled if b['result'] == 'loss'])
        pushes = len([b for b in settled if b['result'] == 'push'])

        total_profit = sum(b['profit'] or 0 for b in settled)
        total_staked = sum(b['stake'] for b in settled)
        roi = (total_profit / total_staked * 100) if total_staked > 0 else 0
        win_rate = (wins / len(settled) * 100) if settled else 0

        return {
            'total_bets': total_bets,
            'settled': len(settled),
            'wins': wins,
            'losses': losses,
            'pushes': pushes,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'total_staked': total_staked,
            'roi': roi
        }

    # Sharp money detection
    def detect_sharp_money(
        self,
        open_line: float,
        current_line: float,
        bet_pct: Optional[float] = None,
        money_pct: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Detect sharp money signals"""
        from oddsscript.analytics.sharp import SharpMoneyAnalyzer

        analyzer = SharpMoneyAnalyzer(self.config)
        return analyzer.analyze(
            open_line=open_line,
            current_line=current_line,
            bet_pct=bet_pct,
            money_pct=money_pct,
            **kwargs
        )

    # Arbitrage detection
    def find_arbitrage(
        self,
        odds1: float,
        odds2: float,
        min_profit: float = 0.5
    ) -> Dict[str, Any]:
        """Find arbitrage opportunity"""
        from oddsscript.analytics.arbitrage import ArbitrageCalculator

        arb = ArbitrageCalculator.calculate_two_way_arb(odds1, odds2)

        if arb['is_arb'] and arb['profit_margin'] >= min_profit:
            return arb
        else:
            return {'is_arb': False}

    # Parlay optimization
    def optimize_parlay(
        self,
        bets: List[Dict[str, Any]],
        min_legs: int = 2,
        max_legs: int = 4,
        max_correlation: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Find optimal parlay combinations"""
        from oddsscript.analytics.parlay import ParlayOptimizer
        from oddsscript.analytics.parlay import Bet as ParlayBet

        # Convert to Bet objects
        bet_objects = [
            ParlayBet(
                id=b['id'],
                description=b['description'],
                odds=b['odds'],
                true_prob=b['true_prob'],
                game_id=b['game_id'],
                bet_type=b['bet_type']
            )
            for b in bets
        ]

        return ParlayOptimizer.find_optimal_parlays(
            bet_objects,
            min_legs=min_legs,
            max_legs=max_legs,
            max_correlation=max_correlation
        )

    # Strategy execution
    def execute_strategy(
        self,
        strategy_name: str,
        bankroll: float,
        odds: float,
        edge: float,
        **strategy_params
    ) -> Dict[str, Any]:
        """Execute betting strategy"""
        strategy = StrategyRegistry.get(strategy_name)
        recommendation = strategy.calculate_stake(
            bankroll=bankroll,
            odds=odds,
            edge=edge,
            **strategy_params
        )

        return {
            'should_bet': recommendation.should_bet,
            'stake': recommendation.stake,
            'confidence': recommendation.confidence,
            'reasoning': recommendation.reasoning,
            'metadata': recommendation.metadata
        }

    # Utility methods
    def calculate_payout(self, odds: float, stake: float) -> float:
        """Calculate payout for bet"""
        decimal = float(self.convert_odds(odds, 'american', 'decimal'))
        return stake * decimal

    def calculate_ev(self, odds: float, true_prob: float, stake: float = 100) -> float:
        """Calculate expected value"""
        from oddsscript.common.odds import OddsConverter
        decimal = float(OddsConverter.american_to_decimal(odds))
        return (true_prob * (decimal - 1) * stake) - ((1 - true_prob) * stake)


# Example usage
if __name__ == '__main__':
    # Initialize API
    api = SportsBetLangAPI()

    # Convert odds
    decimal = api.convert_odds(-110, 'american', 'decimal')
    print(f"Decimal odds: {decimal}")

    # Calculate Kelly
    kelly = api.calculate_kelly(
        odds=-110,
        true_prob=0.55,
        bankroll=1000,
        kelly_fraction=0.25
    )
    print(f"Kelly stake: ${kelly['stake']:.2f}")

    # Add and settle bet
    bet_id = api.add_bet(
        date='2024-01-15',
        sport='nfl',
        description='Chiefs -3',
        odds=-110,
        stake=110
    )
    api.settle_bet(bet_id, 'win')

    # Get stats
    stats = api.get_stats(sport='nfl')
    print(f"ROI: {stats['roi']:.2f}%")
```

---

## 10. Installation and Packaging

### setup.py

```python
"""SportsBetLang package setup"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read version
version = {}
with open("oddsscript/__version__.py") as f:
    exec(f.read(), version)

setup(
    name="oddsscript",
    version=version['__version__'],
    description="Domain-specific language and analytics suite for sports betting",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="SportsBetLang Team",
    author_email="info@oddsscript.com",
    url="https://github.com/yourusername/oddsscript",
    packages=find_packages(exclude=["tests", "tests.*"]),
    include_package_data=True,
    python_requires=">=3.7",
    install_requires=[
        # Pure Python - no dependencies!
    ],
    extras_require={
        'dev': [
            'pytest>=7.0',
            'pytest-cov>=4.0',
            'black>=22.0',
            'mypy>=0.990',
            'flake8>=5.0',
        ],
        'performance': [
            'numpy>=1.21',  # For faster calculations
            'pandas>=1.3',  # For data analysis
        ],
        'jupyter': [
            'jupyter>=1.0',
            'matplotlib>=3.5',
            'seaborn>=0.12',
        ]
    },
    entry_points={
        'console_scripts': [
            'oddsscript=oddsscript.cli.main:main',
            'odds-calc=oddsscript.tools.odds_calc:main',
            'bet-tracker=oddsscript.tools.bet_tracker:main',
            'sharp-tracker=oddsscript.tools.sharp_tracker:main',
            'public-fade=oddsscript.tools.public_fade:main',
            'parlay-optimizer=oddsscript.tools.parlay_optimizer:main',
            'arbitrage-finder=oddsscript.tools.arbitrage:main',
            # ... (all tools as CLI commands)
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Office/Business :: Financial",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="sports betting analytics odds kelly arbitrage sharp money",
)
```

### pyproject.toml

```toml
[build-system]
requires = ["setuptools>=45", "wheel", "setuptools_scm>=6.2"]
build-backend = "setuptools.build_meta"

[project]
name = "oddsscript"
dynamic = ["version"]
description = "Domain-specific language and analytics suite for sports betting"
readme = "README.md"
requires-python = ">=3.7"
license = {text = "MIT"}
keywords = ["sports", "betting", "analytics", "odds", "kelly"]
authors = [
  {name = "SportsBetLang Team"}
]
classifiers = [
  "Development Status :: 4 - Beta",
  "Intended Audience :: End Users/Desktop",
  "Programming Language :: Python :: 3",
]

[tool.black]
line-length = 100
target-version = ['py37', 'py38', 'py39', 'py310', 'py311']

[tool.mypy]
python_version = "3.7"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --cov=oddsscript --cov-report=term-missing"

[tool.coverage.run]
source = ["oddsscript"]
omit = ["tests/*", "oddsscript/__version__.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Create new directory structure
- [ ] Implement `oddsscript/common/` utilities
- [ ] Implement `oddsscript/config/` system
- [ ] Implement `oddsscript/data/` storage layer
- [ ] Migrate core language to `oddsscript/core/`

### Phase 2: Refactoring (Week 3-4)
- [ ] Create `BaseTool` class
- [ ] Refactor all 18 tools to use `BaseTool`
- [ ] Migrate analytics libraries to `oddsscript/analytics/`
- [ ] Implement strategy plugin system
- [ ] Remove code duplication

### Phase 3: Testing (Week 5-6)
- [ ] Set up pytest framework
- [ ] Write unit tests for all modules
- [ ] Write integration tests
- [ ] Write performance tests
- [ ] Achieve 80%+ code coverage

### Phase 4: API & Packaging (Week 7-8)
- [ ] Implement programmatic API
- [ ] Create setup.py and pyproject.toml
- [ ] Add entry points for CLI tools
- [ ] Test package installation
- [ ] Prepare for PyPI publication

### Phase 5: Documentation (Week 9-10)
- [ ] Update README.md
- [ ] Generate API documentation
- [ ] Write user guides
- [ ] Create example notebooks
- [ ] Write contribution guide

### Phase 6: Performance (Week 11-12)
- [ ] Implement multiprocessing for Monte Carlo
- [ ] Add caching layer
- [ ] Profile and optimize bottlenecks
- [ ] Run performance benchmarks
- [ ] Document performance improvements

---

## Migration Strategy

To avoid breaking existing code, follow these steps:

### Step 1: Create new structure alongside old
```bash
# Create new package directory
mkdir -p oddsscript/core
mkdir -p oddsscript/common
mkdir -p oddsscript/config
mkdir -p oddsscript/data
mkdir -p oddsscript/analytics
```

### Step 2: Implement shared utilities
- Start with `oddsscript/common/odds.py`
- Add comprehensive tests
- Update one tool to use it
- Verify it works
- Gradually migrate other tools

### Step 3: Backwards compatibility
```python
# In old location (root/tools/odds_calc.py)
# Add deprecation warning
import warnings
from oddsscript.tools.odds_calc import main

warnings.warn(
    "Importing from tools.odds_calc is deprecated. "
    "Use 'from oddsscript.tools.odds_calc import main' instead.",
    DeprecationWarning,
    stacklevel=2
)
```

### Step 4: Gradual migration
- One module at a time
- Test after each migration
- Keep old imports working with deprecation warnings
- Remove old code only after 2-3 version releases

---

## Expected Benefits

### Code Quality
- **75% less code duplication** (odds conversion, CSV handling, etc.)
- **Consistent error handling** across all tools
- **Type safety** with proper type hints and validation
- **Easier maintenance** with clear module boundaries

### Performance
- **3-5x faster Monte Carlo** simulations with multiprocessing
- **Instant repeated calculations** with caching
- **Efficient data queries** with SQLite backend option

### Developer Experience
- **10-minute setup** with `pip install oddsscript`
- **Clear API** for programmatic usage
- **Extensible** plugin system for custom strategies
- **Well-tested** with 80%+ code coverage

### User Experience
- **Unified CLI** - `oddsscript <command>` instead of individual scripts
- **JSON/CSV output** for integration with other tools
- **Configurable** via environment variables or config file
- **Fast** - optimized critical paths

---

## Conclusion

These architectural improvements will transform SportsBetLang from a collection of useful scripts into a **professional-grade betting analytics platform**.

The key improvements are:

1. **DRY Principle** - Shared utilities eliminate duplication
2. **Configuration Management** - Centralized, flexible settings
3. **Storage Abstraction** - Support multiple backends
4. **Testing** - Comprehensive test coverage
5. **Plugin Architecture** - Extensible strategy system
6. **Performance** - Optimized for production use
7. **Packaging** - Professional distribution
8. **API** - Both CLI and programmatic interfaces

Implementation can be done gradually without breaking existing code, following the phased roadmap outlined above.
