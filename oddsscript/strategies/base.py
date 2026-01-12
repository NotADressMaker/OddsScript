"""
Base strategy interface for OddsScript.

Provides plugin architecture for extensible betting strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class BetAction(Enum):
    """Recommended betting action"""
    BET = "bet"
    NO_BET = "no_bet"
    WAIT = "wait"


@dataclass
class BetRecommendation:
    """Recommendation from a betting strategy"""
    should_bet: bool
    stake: float
    confidence: float  # 0-1 scale
    reasoning: str
    action: BetAction
    metadata: Dict[str, Any]

    def __str__(self) -> str:
        action_emoji = {
            BetAction.BET: "✅",
            BetAction.NO_BET: "❌",
            BetAction.WAIT: "⏸️"
        }
        emoji = action_emoji.get(self.action, "")

        if self.should_bet:
            return (f"{emoji} BET ${self.stake:.2f} "
                   f"(Confidence: {self.confidence*100:.1f}%) - {self.reasoning}")
        else:
            return f"{emoji} NO BET - {self.reasoning}"


class BettingStrategy(ABC):
    """Abstract base class for betting strategies"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name (must be unique)"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Strategy description for documentation"""
        pass

    @property
    def version(self) -> str:
        """Strategy version"""
        return "1.0.0"

    @property
    def parameters(self) -> Dict[str, Any]:
        """Strategy parameters with default values"""
        return {}

    @abstractmethod
    def calculate_stake(
        self,
        bankroll: float,
        odds: float,
        edge: float,
        **kwargs
    ) -> BetRecommendation:
        """
        Calculate recommended stake for a bet

        Args:
            bankroll: Current bankroll
            odds: American odds
            edge: Estimated edge (as decimal, e.g., 0.05 = 5%)
            **kwargs: Strategy-specific parameters

        Returns:
            BetRecommendation with stake, confidence, and reasoning
        """
        pass

    def validate_parameters(self, **kwargs):
        """
        Validate strategy parameters

        Args:
            **kwargs: Parameters to validate

        Raises:
            ValueError: If parameters are invalid
        """
        # Default implementation - override in subclass if needed
        pass

    def get_help(self) -> str:
        """
        Get help text for the strategy

        Returns:
            Help text describing strategy and parameters
        """
        help_text = f"{self.name} - {self.description}\n"
        help_text += f"Version: {self.version}\n\n"

        if self.parameters:
            help_text += "Parameters:\n"
            for param, default in self.parameters.items():
                help_text += f"  {param}: {default}\n"

        return help_text


class StrategyRegistry:
    """
    Registry for dynamically loaded betting strategies

    Allows plugins to register themselves for discovery.
    """

    _strategies: Dict[str, type[BettingStrategy]] = {}

    @classmethod
    def register(cls, strategy_class: type[BettingStrategy]):
        """
        Register a strategy class

        Args:
            strategy_class: Strategy class to register

        Returns:
            The strategy class (for use as decorator)

        Example:
            @StrategyRegistry.register
            class MyStrategy(BettingStrategy):
                ...
        """
        instance = strategy_class()
        name = instance.name

        if name in cls._strategies:
            raise ValueError(f"Strategy '{name}' is already registered")

        cls._strategies[name] = strategy_class
        return strategy_class

    @classmethod
    def get(cls, name: str) -> BettingStrategy:
        """
        Get strategy instance by name

        Args:
            name: Strategy name

        Returns:
            Strategy instance

        Raises:
            ValueError: If strategy not found
        """
        if name not in cls._strategies:
            available = ", ".join(cls._strategies.keys())
            raise ValueError(f"Unknown strategy: '{name}'. Available: {available}")

        return cls._strategies[name]()

    @classmethod
    def list_strategies(cls) -> List[str]:
        """
        List all registered strategy names

        Returns:
            List of strategy names
        """
        return list(cls._strategies.keys())

    @classmethod
    def get_all_strategies(cls) -> Dict[str, BettingStrategy]:
        """
        Get all registered strategies as instances

        Returns:
            Dictionary of strategy_name -> strategy_instance
        """
        return {name: cls_type() for name, cls_type in cls._strategies.items()}

    @classmethod
    def clear(cls):
        """Clear all registered strategies (mainly for testing)"""
        cls._strategies.clear()


# Decorator for easy strategy registration
def register_strategy(cls):
    """
    Decorator to register a strategy

    Usage:
        @register_strategy
        class MyStrategy(BettingStrategy):
            @property
            def name(self):
                return "my-strategy"

            def calculate_stake(self, bankroll, odds, edge, **kwargs):
                return BetRecommendation(...)
    """
    return StrategyRegistry.register(cls)


# Export public API
__all__ = [
    'BettingStrategy',
    'BetRecommendation',
    'BetAction',
    'StrategyRegistry',
    'register_strategy',
]
