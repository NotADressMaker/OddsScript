"""
Market + odds normalization utilities.

Provides:
- First-class Market objects with consistent fields
- Odds normalization (American/decimal/implied probability)
- Vig-aware comparisons + optional devigging
- Correlation/exposure rules
- Backtesting hooks (time splits, CLV, slippage assumptions)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, Iterable, List, Optional, Tuple


class OddsFormat(str, Enum):
    AMERICAN = "american"
    DECIMAL = "decimal"
    IMPLIED_PROB = "implied_prob"


@dataclass(frozen=True)
class Odds:
    """Normalized odds container."""

    american: float
    decimal: float
    implied_prob: float

    @staticmethod
    def _validate_implied(prob: float) -> float:
        if prob <= 0.0 or prob >= 1.0:
            raise ValueError("Implied probability must be between 0 and 1 (exclusive).")
        return float(prob)

    @classmethod
    def from_american(cls, odds: float) -> "Odds":
        o = float(odds)
        decimal = (o / 100.0) + 1.0 if o > 0 else (100.0 / abs(o)) + 1.0
        implied = 1.0 / decimal
        return cls(american=o, decimal=decimal, implied_prob=implied)

    @classmethod
    def from_decimal(cls, odds: float) -> "Odds":
        dec = float(odds)
        if dec <= 1.0:
            raise ValueError("Decimal odds must be greater than 1.0.")
        if dec >= 2.0:
            american = (dec - 1.0) * 100.0
        else:
            american = -100.0 / (dec - 1.0)
        implied = 1.0 / dec
        return cls(american=american, decimal=dec, implied_prob=implied)

    @classmethod
    def from_implied_prob(cls, prob: float) -> "Odds":
        implied = cls._validate_implied(prob)
        decimal = 1.0 / implied
        if decimal >= 2.0:
            american = (decimal - 1.0) * 100.0
        else:
            american = -100.0 / (decimal - 1.0)
        return cls(american=american, decimal=decimal, implied_prob=implied)


def normalize_odds(odds: float, format: OddsFormat) -> Odds:
    if format == OddsFormat.AMERICAN:
        return Odds.from_american(odds)
    if format == OddsFormat.DECIMAL:
        return Odds.from_decimal(odds)
    if format == OddsFormat.IMPLIED_PROB:
        return Odds.from_implied_prob(odds)
    raise ValueError(f"Unsupported odds format: {format}")


class MarketType(str, Enum):
    MONEYLINE = "moneyline"
    SPREAD = "spread"
    TOTAL = "total"
    PROP = "prop"


@dataclass
class Market:
    """First-class market definition."""

    market_id: str
    sport: str
    event_id: str
    market_type: MarketType
    selection: str
    odds: Odds
    line: Optional[float] = None
    book: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Dict[str, object] = field(default_factory=dict)

    @classmethod
    def moneyline(
        cls,
        *,
        market_id: str,
        sport: str,
        event_id: str,
        selection: str,
        odds: float,
        odds_format: OddsFormat = OddsFormat.AMERICAN,
        book: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, object]] = None,
    ) -> "Market":
        return cls(
            market_id=market_id,
            sport=sport,
            event_id=event_id,
            market_type=MarketType.MONEYLINE,
            selection=selection,
            odds=normalize_odds(odds, odds_format),
            line=None,
            book=book,
            timestamp=timestamp,
            metadata=metadata or {},
        )

    @classmethod
    def spread(
        cls,
        *,
        market_id: str,
        sport: str,
        event_id: str,
        selection: str,
        line: float,
        odds: float,
        odds_format: OddsFormat = OddsFormat.AMERICAN,
        book: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, object]] = None,
    ) -> "Market":
        return cls(
            market_id=market_id,
            sport=sport,
            event_id=event_id,
            market_type=MarketType.SPREAD,
            selection=selection,
            odds=normalize_odds(odds, odds_format),
            line=float(line),
            book=book,
            timestamp=timestamp,
            metadata=metadata or {},
        )

    @classmethod
    def total(
        cls,
        *,
        market_id: str,
        sport: str,
        event_id: str,
        selection: str,
        line: float,
        odds: float,
        odds_format: OddsFormat = OddsFormat.AMERICAN,
        book: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, object]] = None,
    ) -> "Market":
        return cls(
            market_id=market_id,
            sport=sport,
            event_id=event_id,
            market_type=MarketType.TOTAL,
            selection=selection,
            odds=normalize_odds(odds, odds_format),
            line=float(line),
            book=book,
            timestamp=timestamp,
            metadata=metadata or {},
        )

    @classmethod
    def prop(
        cls,
        *,
        market_id: str,
        sport: str,
        event_id: str,
        selection: str,
        line: float,
        odds: float,
        odds_format: OddsFormat = OddsFormat.AMERICAN,
        book: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, object]] = None,
    ) -> "Market":
        return cls(
            market_id=market_id,
            sport=sport,
            event_id=event_id,
            market_type=MarketType.PROP,
            selection=selection,
            odds=normalize_odds(odds, odds_format),
            line=float(line),
            book=book,
            timestamp=timestamp,
            metadata=metadata or {},
        )


def vig_from_two_way(
    odds_a: float,
    odds_b: float,
    *,
    odds_format: OddsFormat = OddsFormat.DECIMAL,
) -> float:
    """Return vig as total implied prob minus 1."""
    if odds_format == OddsFormat.DECIMAL:
        implied_a = 1.0 / float(odds_a)
        implied_b = 1.0 / float(odds_b)
    elif odds_format == OddsFormat.AMERICAN:
        implied_a = normalize_odds(odds_a, OddsFormat.AMERICAN).implied_prob
        implied_b = normalize_odds(odds_b, OddsFormat.AMERICAN).implied_prob
    else:
        implied_a = float(odds_a)
        implied_b = float(odds_b)
    return (implied_a + implied_b) - 1.0


def devig_two_way(
    prob_a: float,
    prob_b: float,
    *,
    method: str = "proportional",
) -> Tuple[float, float]:
    """Remove vig from two probabilities."""
    total = float(prob_a) + float(prob_b)
    if total <= 0.0:
        raise ValueError("Probabilities must sum to a positive number.")

    if method == "proportional":
        return float(prob_a) / total, float(prob_b) / total
    if method == "equal":
        vig = total - 1.0
        return float(prob_a) - vig / 2.0, float(prob_b) - vig / 2.0
    raise ValueError(f"Unsupported devig method: {method}")


def devig_from_odds(
    odds_a: float,
    odds_b: float,
    *,
    odds_format: OddsFormat = OddsFormat.DECIMAL,
    method: str = "proportional",
) -> Dict[str, Odds]:
    """Return devigged odds for a two-way market."""
    if odds_format == OddsFormat.IMPLIED_PROB:
        prob_a, prob_b = float(odds_a), float(odds_b)
    else:
        prob_a = normalize_odds(odds_a, odds_format).implied_prob
        prob_b = normalize_odds(odds_b, odds_format).implied_prob
    fair_a, fair_b = devig_two_way(prob_a, prob_b, method=method)
    return {
        "a": Odds.from_implied_prob(fair_a),
        "b": Odds.from_implied_prob(fair_b),
    }


@dataclass
class MarketComparison:
    market: Market
    implied_prob: float
    devigged_prob: Optional[float]


def compare_markets(
    markets: Iterable[Market],
    *,
    devig: bool = False,
    devig_method: str = "proportional",
) -> List[MarketComparison]:
    """Compare markets with optional devigging (two-way markets)."""
    items = list(markets)
    comparisons: List[MarketComparison] = []
    if devig and len(items) == 2:
        fair = devig_from_odds(
            items[0].odds.decimal,
            items[1].odds.decimal,
            odds_format=OddsFormat.DECIMAL,
            method=devig_method,
        )
        comparisons.append(
            MarketComparison(
                market=items[0],
                implied_prob=items[0].odds.implied_prob,
                devigged_prob=fair["a"].implied_prob,
            )
        )
        comparisons.append(
            MarketComparison(
                market=items[1],
                implied_prob=items[1].odds.implied_prob,
                devigged_prob=fair["b"].implied_prob,
            )
        )
        return comparisons

    for item in items:
        comparisons.append(
            MarketComparison(
                market=item,
                implied_prob=item.odds.implied_prob,
                devigged_prob=None,
            )
        )
    return comparisons


@dataclass(frozen=True)
class ExposureRule:
    name: str
    key_func: Callable[[Market], str]
    max_exposure: int


def default_exposure_rules(
    *,
    max_same_game: int = 1,
    max_same_team: int = 1,
    max_same_market: int = 1,
) -> List[ExposureRule]:
    return [
        ExposureRule(
            name="same_game",
            key_func=lambda m: f"{m.event_id}",
            max_exposure=max_same_game,
        ),
        ExposureRule(
            name="same_team",
            key_func=lambda m: f"{m.event_id}:{m.metadata.get('team', m.selection)}",
            max_exposure=max_same_team,
        ),
        ExposureRule(
            name="same_market",
            key_func=lambda m: f"{m.event_id}:{m.market_type.value}:{m.selection}",
            max_exposure=max_same_market,
        ),
    ]


def check_exposure(markets: Iterable[Market], rules: Iterable[ExposureRule]) -> List[Dict[str, object]]:
    violations: List[Dict[str, object]] = []
    market_list = list(markets)
    for rule in rules:
        counts: Dict[str, List[Market]] = {}
        for market in market_list:
            key = rule.key_func(market)
            counts.setdefault(key, []).append(market)
        for key, group in counts.items():
            if len(group) > rule.max_exposure:
                violations.append(
                    {
                        "rule": rule.name,
                        "key": key,
                        "count": len(group),
                        "max_exposure": rule.max_exposure,
                        "markets": group,
                    }
                )
    return violations


@dataclass
class BacktestBet:
    market: Market
    stake: float
    placed_odds: Odds
    placed_at: datetime
    closing_odds: Optional[Odds] = None
    result: Optional[bool] = None


def clv_decimal(placed_odds: float, closing_odds: float) -> float:
    """Closing line value using decimal odds."""
    return (float(closing_odds) - float(placed_odds)) / float(placed_odds)


def apply_slippage(decimal_odds: float, slippage_bps: float) -> float:
    """
    Apply slippage in basis points to decimal odds.
    Positive slippage_bps worsens the price for the bettor.
    """
    return float(decimal_odds) * (1.0 - (float(slippage_bps) / 10000.0))


def time_split_bets(
    bets: Iterable[BacktestBet],
    *,
    n_splits: int,
    by: str = "placed_at",
) -> List[List[BacktestBet]]:
    items = sorted(bets, key=lambda b: getattr(b, by))
    if n_splits <= 0:
        raise ValueError("n_splits must be >= 1")
    if not items:
        return []
    size = max(1, len(items) // n_splits)
    return [items[i:i + size] for i in range(0, len(items), size)]
