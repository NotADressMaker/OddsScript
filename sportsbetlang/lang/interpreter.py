"""
SportsBetLang Interpreter - Executes the AST with built-in betting functions
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.request import urlopen


from sportsbetlang.lang.diagnostics import format_snippet
from sportsbetlang.lang.lexer import TokenType
from sportsbetlang.lang.limits import DEFAULT_LIMITS, RuntimeLimits
from sportsbetlang.lang.parser import *
from sportsbetlang.lang.sandbox import HostCapabilities, SandboxViolation


class ReturnValue(Exception):
    """Exception used to handle return statements"""
    def __init__(self, value: Any) -> None:
        self.value = value


@dataclass(frozen=True)
class TaggedNumber:
    """Tiny units system for safety-critical betting semantics."""

    value: float
    tag: str

    def __float__(self) -> float:
        return float(self.value)

    @staticmethod
    def money(value: float) -> "TaggedNumber":
        return TaggedNumber(float(value), "money")

    @staticmethod
    def probability(value: float, clamp: bool = False) -> "TaggedNumber":
        numeric = float(value)
        if clamp:
            numeric = min(1.0, max(0.0, numeric))
        elif numeric < 0 or numeric > 1:
            raise ValueError("Probability must be between 0 and 1")
        return TaggedNumber(numeric, "probability")

    @staticmethod
    def american_odds(value: float) -> "TaggedNumber":
        if value == 0:
            raise ValueError("American odds cannot be 0")
        return TaggedNumber(float(value), "american_odds")

    @staticmethod
    def decimal_odds(value: float) -> "TaggedNumber":
        if value <= 1.0:
            raise ValueError("Decimal odds must be greater than 1.0")
        return TaggedNumber(float(value), "decimal_odds")

    def _number(self, other: Any) -> float:
        return other.value if isinstance(other, TaggedNumber) else float(other)

    def _expect_same_tag(self, other: Any, op: str) -> "TaggedNumber":
        if not isinstance(other, TaggedNumber):
            raise TypeError(f"Cannot {op} tagged value '{self.tag}' with untagged number")
        if other.tag != self.tag:
            raise TypeError(f"Cannot {op} '{self.tag}' and '{other.tag}'")
        return other

    def __add__(self, other: Any) -> "TaggedNumber":
        if self.tag in {"american_odds"}:
            raise TypeError(f"Cannot add values with unit '{self.tag}'")
        rhs = self._expect_same_tag(other, "add")
        return TaggedNumber(self.value + rhs.value, self.tag)

    def __sub__(self, other: Any) -> "TaggedNumber | float":
        if not isinstance(other, TaggedNumber):
            return float(self.value - float(other))
        if self.tag in {"american_odds"}:
            raise TypeError(f"Cannot subtract values with unit '{self.tag}'")
        rhs = self._expect_same_tag(other, "subtract")
        return TaggedNumber(self.value - rhs.value, self.tag)

    def __rsub__(self, other: Any) -> float:
        return float(float(other) - self.value)

    def __abs__(self) -> float:
        return abs(self.value)

    def __mul__(self, other: Any) -> "TaggedNumber":
        if isinstance(other, TaggedNumber):
            raise TypeError(f"Cannot multiply '{self.tag}' by '{other.tag}'")
        return TaggedNumber(self.value * float(other), self.tag)

    def __rmul__(self, other: Any) -> "TaggedNumber":
        return self.__mul__(other)

    def __truediv__(self, other: Any) -> "TaggedNumber":
        if isinstance(other, TaggedNumber):
            raise TypeError(f"Cannot divide '{self.tag}' by '{other.tag}'")
        return TaggedNumber(self.value / float(other), self.tag)

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, TaggedNumber):
            self._expect_same_tag(other, "compare")
            return self.value < other.value
        return self.value < float(other)

    def __le__(self, other: Any) -> bool:
        return self == other or self < other

    def __gt__(self, other: Any) -> bool:
        return not self <= other

    def __ge__(self, other: Any) -> bool:
        return not self < other

    def __eq__(self, other: Any) -> bool:  # type: ignore[override]
        if isinstance(other, TaggedNumber):
            return self.tag == other.tag and self.value == other.value
        return self.value == float(other)


@dataclass
class LanguageRuntimeError(RuntimeError):
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    source: Optional[str] = None
    hint: Optional[str] = None

    def __post_init__(self) -> None:
        super().__init__(self.message)

    def format(self) -> str:
        details = self.message
        if self.line is not None and self.column is not None:
            details = f"{details} (line {self.line}, column {self.column})"
        snippet = format_snippet(self.source or "", self.line, self.column)
        if snippet:
            details = f"{details}\n{snippet}"
        if self.hint:
            details = f"{details}\nHint: {self.hint}"
        return details

    def __str__(self) -> str:
        return self.format()


class Environment:
    """Manages variable scopes"""
    def __init__(self, parent: Optional["Environment"] = None) -> None:
        self.variables: Dict[str, Any] = {}
        self.constants: set = set()
        self.parent = parent

    def define(self, name: str, value: Any, is_const: bool = False) -> None:
        if name in self.variables:
            raise RuntimeError(f"Variable '{name}' already defined")
        self.variables[name] = value
        if is_const:
            self.constants.add(name)

    def get(self, name: str) -> Any:
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.get(name)
        raise RuntimeError(f"Undefined variable '{name}'")

    def set(self, name: str, value: Any) -> None:
        if name in self.variables:
            if name in self.constants:
                raise RuntimeError(f"Cannot reassign constant '{name}'")
            self.variables[name] = value
        elif self.parent:
            self.parent.set(name, value)
        else:
            raise RuntimeError(f"Undefined variable '{name}'")

    def exists(self, name: str) -> bool:
        return name in self.variables or (self.parent and self.parent.exists(name))


class Bet:
    """Represents a sports bet"""
    def __init__(
        self,
        bet_type: str,
        team: str,
        odds: float,
        stake: float,
        **kwargs: Any,
    ) -> None:
        self.bet_type = bet_type
        self.team = team
        self.odds = odds
        self.stake = stake
        self.spread = kwargs.get('spread', None)
        self.result = None  # 'win', 'loss', 'push'

    def calculate_payout(self) -> float:
        """Calculate potential payout"""
        if self.odds == 0:
            raise ValueError("American odds cannot be 0")
        if self.odds > 0:  # American odds (positive)
            return self.stake * (self.odds / 100)
        else:  # American odds (negative)
            return self.stake * (100 / abs(self.odds))

    def calculate_total_return(self) -> float:
        """Calculate total return including stake"""
        return self.stake + self.calculate_payout()

    def to_decimal_odds(self) -> float:
        """Convert American odds to decimal"""
        if self.odds == 0:
            raise ValueError("American odds cannot be 0")
        if self.odds > 0:
            return (self.odds / 100) + 1
        else:
            return (100 / abs(self.odds)) + 1

    def __repr__(self) -> str:
        spread_info = f" ({self.spread:+.1f})" if self.spread else ""
        return f"Bet({self.bet_type}: {self.team}{spread_info} @ {self.odds:+.0f}, ${self.stake:.2f})"


class Interpreter:
    def __init__(
        self,
        max_steps: Optional[int] = None,
        limits: RuntimeLimits = DEFAULT_LIMITS,
        source: str = "",
        capabilities: Optional[HostCapabilities] = None,
    ) -> None:
        self.limits = limits
        self.source = source
        self.max_steps = max_steps or limits.max_steps
        self.steps_remaining = self.max_steps
        self.recursion_depth = 0
        self.global_env = Environment()
        self.capabilities = capabilities or HostCapabilities(no_io=True)
        self.setup_builtins()

    def _enter_eval(self) -> None:
        self.steps_remaining -= 1
        if self.steps_remaining < 0:
            raise LanguageRuntimeError(
                "Execution step limit exceeded",
                source=self.source,
                hint="Increase --max-steps, use --mode expert, or add #limits max_steps=<n>.",
            )
        self.recursion_depth += 1
        if self.recursion_depth > self.limits.max_recursion_depth:
            raise LanguageRuntimeError(
                "Maximum recursion depth exceeded",
                source=self.source,
                hint="Increase --max-recursion, use --mode expert, or refactor recursive functions.",
            )

    def _exit_eval(self) -> None:
        self.recursion_depth = max(self.recursion_depth - 1, 0)

    def _check_string_length(self, value: str) -> None:
        if len(value) > self.limits.max_string_length:
            raise LanguageRuntimeError("Maximum string length exceeded", source=self.source)

    def _check_list_length(self, value: List[Any]) -> None:
        if len(value) > self.limits.max_list_length:
            raise LanguageRuntimeError("Maximum list length exceeded", source=self.source)

    def _node_location(self, node: ASTNode) -> tuple[Optional[int], Optional[int]]:
        return getattr(node, "line", None), getattr(node, "column", None)

    def _runtime_error(self, message: str, node: ASTNode, hint: Optional[str] = None) -> LanguageRuntimeError:
        line, column = self._node_location(node)
        return LanguageRuntimeError(message, line=line, column=column, source=self.source, hint=hint)

    def setup_builtins(self) -> None:
        """Setup built-in functions for betting operations"""
        from sportsbetlang.analytics.poisson import (
            poisson_cumulative,
            poisson_probability,
            set_seed as set_poisson_seed,
            simulate_match,
            simulate_poisson_event,
        )
        from sportsbetlang.analytics.repro import set_global_seed

        def american_to_decimal(odds: float | TaggedNumber) -> TaggedNumber:
            """Convert American odds to decimal odds"""
            american = TaggedNumber.american_odds(float(odds))
            if american.value > 0:
                decimal = (american.value / 100) + 1
            else:
                decimal = (100 / abs(american.value)) + 1
            return TaggedNumber.decimal_odds(decimal)

        def decimal_to_american(odds: float | TaggedNumber) -> TaggedNumber:
            """Convert decimal odds to American odds"""
            decimal = TaggedNumber.decimal_odds(float(odds))
            if decimal.value >= 2.0:
                american = (decimal.value - 1) * 100
            else:
                american = -100 / (decimal.value - 1)
            return TaggedNumber.american_odds(american)

        def implied_probability(odds: float) -> TaggedNumber:
            """Calculate implied probability from American odds"""
            if odds > 0:
                probability = 100 / (odds + 100)
            else:
                probability = abs(odds) / (abs(odds) + 100)
            return TaggedNumber.probability(probability)

        def calculate_ev(true_prob: float | TaggedNumber, odds: float | TaggedNumber, stake: float | TaggedNumber = 100) -> TaggedNumber:
            """Calculate expected value of a bet."""
            prob_value = float(true_prob)
            if prob_value < 0 or prob_value > 1:
                raise ValueError("Probability must be between 0 and 1")
            american_value = float(TaggedNumber.american_odds(float(odds)))
            stake_value = float(TaggedNumber.money(float(stake)))
            decimal_odds = float(american_to_decimal(american_value))
            win_amount = stake_value * (decimal_odds - 1)
            loss_amount = stake_value
            ev = (prob_value * win_amount) - ((1 - prob_value) * loss_amount)
            return TaggedNumber.money(ev)

        def kelly_criterion(true_prob: float | TaggedNumber, odds: float | TaggedNumber) -> float:
            """Calculate optimal bet size using Kelly Criterion"""
            p = float(TaggedNumber.probability(float(true_prob)))
            decimal_odds = float(american_to_decimal(odds))
            b = decimal_odds - 1  # net odds received on the wager
            q = 1 - p
            kelly = (b * p - q) / b
            return max(0, kelly)  # Don't bet if kelly is negative

        def parlay_odds(*odds_list: float | TaggedNumber) -> TaggedNumber:
            """Calculate parlay odds from multiple bets"""
            decimal_odds = [float(american_to_decimal(o)) for o in odds_list]
            combined = 1.0
            for odd in decimal_odds:
                combined *= odd
            return decimal_to_american(combined)

        def parlay_probability(*probs: float | TaggedNumber) -> TaggedNumber:
            """Calculate probability of winning a parlay"""
            result = 1.0
            for p in probs:
                result *= float(TaggedNumber.probability(float(p)))
            return TaggedNumber.probability(result, clamp=True)

        def break_even_percentage(odds: float | TaggedNumber) -> TaggedNumber:
            """Calculate break-even win percentage"""
            return TaggedNumber.probability(float(implied_probability(float(odds))))

        def vig_calculator(odds1: float, odds2: float) -> float:
            """Calculate bookmaker's vig (juice) from two-way market"""
            prob1 = float(implied_probability(odds1))
            prob2 = float(implied_probability(odds2))
            total = prob1 + prob2
            vig = total - 1
            return vig * 100  # Return as percentage

        def true_odds_from_vig(odds: float | TaggedNumber, total_vig: float) -> TaggedNumber:
            """Remove vig to get true odds"""
            implied_prob = float(implied_probability(float(odds)))
            true_prob = implied_prob / (1 + total_vig)
            if true_prob >= 0.5:
                true_american = -100 * true_prob / (1 - true_prob)
            else:
                true_american = 100 * (1 - true_prob) / true_prob
            return TaggedNumber.american_odds(true_american)

        def units_to_risk(odds: float, units_to_win: float = 1) -> float:
            """Calculate units to risk to win specified units"""
            if odds > 0:
                return units_to_win * (100 / odds)
            else:
                return units_to_win * (abs(odds) / 100)

        def roi_calculator(wins: int, losses: int, avg_odds: float) -> float:
            """Calculate ROI from betting record"""
            if wins + losses == 0:
                return 0
            win_rate = wins / (wins + losses)
            avg_payout = float(calculate_ev(win_rate, avg_odds, 100))
            total_staked = (wins + losses) * 100
            total_return = wins * (100 + abs(avg_payout))
            roi = ((total_return - total_staked) / total_staked) * 100
            return roi

        def round_robin(bets_count: int, parlay_size: int) -> int:
            """Calculate number of parlays in a round robin"""
            from math import comb
            return comb(bets_count, parlay_size)

        def to_json(value: Any) -> str:
            """Serialize a value to pretty JSON."""
            return json.dumps(value, indent=2, default=str)

        def host_read_text(path: str) -> str:
            self.capabilities.check_read_path(path)
            return Path(path).read_text(encoding="utf-8")

        def host_http_get(url: str, timeout: float = 5.0) -> str:
            self.capabilities.check_domain(url)
            with urlopen(url, timeout=timeout) as response:
                payload = response.read()
            return payload.decode("utf-8", errors="replace")

        def host_audit_log() -> list[str]:
            return self.capabilities.snapshot_audit_log()

        def to_csv(rows: Any) -> str:
            """Serialize rows to CSV."""
            output = StringIO()
            if isinstance(rows, list) and rows:
                first = rows[0]
                if isinstance(first, dict):
                    writer = csv.DictWriter(output, fieldnames=list(first.keys()), lineterminator="\n")
                    writer.writeheader()
                    writer.writerows(rows)
                else:
                    writer = csv.writer(output, lineterminator="\n")
                    writer.writerows(rows)
            elif isinstance(rows, dict):
                writer = csv.DictWriter(output, fieldnames=list(rows.keys()), lineterminator="\n")
                writer.writeheader()
                writer.writerow(rows)
            else:
                writer = csv.writer(output, lineterminator="\n")
                writer.writerow([rows])
            return output.getvalue().rstrip("\n")

        def arbitrage_stakes(
            odds1: float,
            odds2: float,
            total_stake: float = 100,
        ) -> Dict[str, float]:
            """Calculate two-way arbitrage stakes and expected profit"""
            decimal1 = float(american_to_decimal(odds1))
            decimal2 = float(american_to_decimal(odds2))

            implied1 = 1 / decimal1
            implied2 = 1 / decimal2
            total_implied = implied1 + implied2

            stake1 = total_stake * (implied1 / total_implied)
            stake2 = total_stake * (implied2 / total_implied)

            payout1 = stake1 * decimal1
            payout2 = stake2 * decimal2
            profit = min(payout1, payout2) - total_stake

            return {
                'odds1': odds1,
                'odds2': odds2,
                'stake_total': total_stake,
                'stake1': stake1,
                'stake2': stake2,
                'total_implied': total_implied,
                'arb_margin_pct': (1 - total_implied) * 100,
                'profit': profit,
                'roi_pct': (profit / total_stake) * 100
            }

        def hedge_stake(
            odds: float,
            stake: float,
            hedge_odds: float,
        ) -> Dict[str, float]:
            """Calculate hedge stake to lock in profit on a two-way bet"""
            decimal_main = float(american_to_decimal(odds))
            decimal_hedge = float(american_to_decimal(hedge_odds))

            hedge_amount = stake * (decimal_main - 1) / (decimal_hedge - 1)
            total_stake = stake + hedge_amount

            profit_main = (stake * decimal_main) - total_stake
            profit_hedge = (hedge_amount * decimal_hedge) - total_stake

            return {
                'original_odds': odds,
                'original_stake': stake,
                'hedge_odds': hedge_odds,
                'hedge_stake': hedge_amount,
                'total_stake': total_stake,
                'profit_if_original_wins': profit_main,
                'profit_if_hedge_wins': profit_hedge,
                'locked_profit': min(profit_main, profit_hedge)
            }


        def set_seed(seed: int) -> int:
            """Set deterministic global seed for language runtime helpers."""
            normalized = int(seed)
            set_global_seed(normalized)
            set_poisson_seed(normalized)
            return normalized

        def poisson_simulate_event(lambda_param: float) -> int:
            """Simulate a single Poisson event."""
            return simulate_poisson_event(lambda_param)

        def poisson_simulate_match(home_lambda: float, away_lambda: float) -> Dict[str, object]:
            """Simulate a single Poisson-based match outcome."""
            return simulate_match(home_lambda, away_lambda)

        def poisson_simulate_matches(
            home_lambda: float,
            away_lambda: float,
            count: int,
        ) -> List[Dict[str, object]]:
            """Simulate multiple Poisson-based match outcomes."""
            return [simulate_match(home_lambda, away_lambda) for _ in range(count)]

        # Register built-in functions
        self.global_env.define('american_to_decimal', american_to_decimal)
        self.global_env.define('decimal_to_american', decimal_to_american)
        self.global_env.define('implied_probability', implied_probability)
        self.global_env.define('calculate_ev', calculate_ev)
        self.global_env.define('kelly_criterion', kelly_criterion)
        self.global_env.define('parlay_odds', parlay_odds)
        self.global_env.define('parlay_probability', parlay_probability)
        self.global_env.define('break_even_percentage', break_even_percentage)
        self.global_env.define('vig_calculator', vig_calculator)
        self.global_env.define('true_odds_from_vig', true_odds_from_vig)
        self.global_env.define('units_to_risk', units_to_risk)
        self.global_env.define('roi_calculator', roi_calculator)
        self.global_env.define('round_robin', round_robin)
        self.global_env.define('to_json', to_json)
        self.global_env.define('to_csv', to_csv)
        self.global_env.define('host_read_text', host_read_text)
        self.global_env.define('host_http_get', host_http_get)
        self.global_env.define('host_audit_log', host_audit_log)
        self.global_env.define('arbitrage_stakes', arbitrage_stakes)
        self.global_env.define('hedge_stake', hedge_stake)
        self.global_env.define('poisson_probability', poisson_probability)
        self.global_env.define('poisson_cumulative', poisson_cumulative)
        self.global_env.define('poisson_simulate_event', poisson_simulate_event)
        self.global_env.define('poisson_simulate_match', poisson_simulate_match)
        self.global_env.define('poisson_simulate_matches', poisson_simulate_matches)
        self.global_env.define('set_seed', set_seed)
        self.global_env.define('abs', abs)
        self.global_env.define('min', min)
        self.global_env.define('max', max)
        self.global_env.define('sqrt', math.sqrt)
        self.global_env.define('pow', pow)
        self.global_env.define('len', len)
        self.global_env.define('range', range)
        self.global_env.define('sum', sum)

    def _betting_module(self) -> Dict[str, Any]:
        return {
            "american_to_decimal": self.global_env.get("american_to_decimal"),
            "decimal_to_american": self.global_env.get("decimal_to_american"),
            "implied_probability": self.global_env.get("implied_probability"),
            "calculate_ev": self.global_env.get("calculate_ev"),
            "kelly_criterion": self.global_env.get("kelly_criterion"),
            "parlay_odds": self.global_env.get("parlay_odds"),
            "parlay_probability": self.global_env.get("parlay_probability"),
        }

    def _elo_totals_module(self) -> Dict[str, Any]:
        from lib.elo_totals import EloTotalsModel

        def init(
            league: str = "NBA",
            k_factor: float = 20.0,
            base_total: Optional[float] = None,
            base_total_std: Optional[float] = None,
            points_per_elo: float = 0.025,
        ) -> EloTotalsModel:
            return EloTotalsModel(
                league=league,
                k_factor=k_factor,
                base_total=base_total,
                base_total_std=base_total_std,
                points_per_elo=points_per_elo,
            )

        def update(model: EloTotalsModel, game: Dict[str, Any]) -> None:
            model.update(game)

        def predict_total(
            model: EloTotalsModel,
            home_team: str,
            away_team: str,
            neutral_site: bool = False,
            home_field_adv: Optional[float] = None,
            league_avg_total: Optional[float] = None,
        ) -> float:
            return model.predict_total(
                home_team,
                away_team,
                neutral_site=neutral_site,
                home_field_adv=home_field_adv,
                league_avg_total=league_avg_total,
            )

        def prob_over(
            model: EloTotalsModel,
            home_team: str,
            away_team: str,
            line: float,
            neutral_site: bool = False,
            home_field_adv: Optional[float] = None,
            league_avg_total: Optional[float] = None,
        ) -> float:
            return model.prob_over(
                home_team,
                away_team,
                line,
                neutral_site=neutral_site,
                home_field_adv=home_field_adv,
                league_avg_total=league_avg_total,
            )

        return {
            "init": init,
            "update": update,
            "predict_total": predict_total,
            "prob_over": prob_over,
        }

    def _multi_market_ratings_module(self) -> Dict[str, Any]:
        from lib.multi_market_ratings import MultiMarketRatingsModel

        def init(
            sport: str,
            window: Optional[int] = None,
            k_off: Optional[float] = None,
            k_def: Optional[float] = None,
            home_adv: Optional[float] = None,
            base_total: Optional[float] = None,
            base_spread: float = 0.0,
            spread_stdev: Optional[float] = None,
            total_stdev: Optional[float] = None,
            scoring_scale: Optional[float] = None,
            k_pace: Optional[float] = None,
        ) -> MultiMarketRatingsModel:
            return MultiMarketRatingsModel(
                sport=sport,
                window=window,
                k_off=k_off,
                k_def=k_def,
                home_adv=home_adv,
                base_total=base_total,
                base_spread=base_spread,
                spread_stdev=spread_stdev,
                total_stdev=total_stdev,
                scoring_scale=scoring_scale,
                k_pace=k_pace,
            )

        def update(model: MultiMarketRatingsModel, game: Dict[str, Any]) -> None:
            model.update(game)

        def predict(
            model: MultiMarketRatingsModel,
            home_team: str,
            away_team: str,
            neutral_site: bool = False,
        ) -> Dict[str, float]:
            return model.predict(home_team, away_team, neutral_site=neutral_site)

        def predict_spread(
            model: MultiMarketRatingsModel,
            home_team: str,
            away_team: str,
            neutral_site: bool = False,
        ) -> float:
            return model.predict_spread(home_team, away_team, neutral_site=neutral_site)

        def predict_total(
            model: MultiMarketRatingsModel,
            home_team: str,
            away_team: str,
            neutral_site: bool = False,
        ) -> float:
            return model.predict_total(home_team, away_team, neutral_site=neutral_site)

        def prob_cover(
            model: MultiMarketRatingsModel,
            home_team: str,
            away_team: str,
            spread_line: float,
            stdev: Optional[float] = None,
            neutral_site: bool = False,
        ) -> float:
            return model.prob_cover(
                home_team,
                away_team,
                spread_line,
                stdev=stdev,
                neutral_site=neutral_site,
            )

        def prob_away_cover(
            model: MultiMarketRatingsModel,
            home_team: str,
            away_team: str,
            spread_line: float,
            stdev: Optional[float] = None,
            neutral_site: bool = False,
        ) -> float:
            return model.prob_away_cover(
                home_team,
                away_team,
                spread_line,
                stdev=stdev,
                neutral_site=neutral_site,
            )

        def prob_over(
            model: MultiMarketRatingsModel,
            home_team: str,
            away_team: str,
            total_line: float,
            stdev: Optional[float] = None,
            neutral_site: bool = False,
        ) -> float:
            return model.prob_over(
                home_team,
                away_team,
                total_line,
                stdev=stdev,
                neutral_site=neutral_site,
            )

        def prob_under(
            model: MultiMarketRatingsModel,
            home_team: str,
            away_team: str,
            total_line: float,
            stdev: Optional[float] = None,
            neutral_site: bool = False,
        ) -> float:
            return model.prob_under(
                home_team,
                away_team,
                total_line,
                stdev=stdev,
                neutral_site=neutral_site,
            )

        return {
            "init": init,
            "update": update,
            "predict": predict,
            "predict_spread": predict_spread,
            "predict_total": predict_total,
            "prob_cover": prob_cover,
            "prob_away_cover": prob_away_cover,
            "prob_over": prob_over,
            "prob_under": prob_under,
        }

    def load_module(self, module: str) -> Dict[str, Any]:
        """Load a module for import statements."""

        if module == "betting":
            return self._betting_module()
        if module == "elo_totals":
            return self._elo_totals_module()
        if module == "multi_market_ratings":
            return self._multi_market_ratings_module()
        raise RuntimeError(f"Unknown module '{module}'")

    def interpret(self, program: Program) -> Any:
        """Execute the program"""
        self.steps_remaining = self.max_steps
        self.recursion_depth = 0
        result = None
        for statement in program.statements:
            result = self.eval_node(statement, self.global_env)
        return result

    def eval_node(self, node: ASTNode, env: Environment) -> Any:
        """Evaluate an AST node"""
        self._enter_eval()
        try:

            if isinstance(node, Program):
                result = None
                for statement in node.statements:
                    result = self.eval_node(statement, env)
                return result

            elif isinstance(node, NumberLiteral):
                return node.value

            elif isinstance(node, StringLiteral):
                self._check_string_length(node.value)
                return node.value

            elif isinstance(node, BooleanLiteral):
                return node.value

            elif isinstance(node, Identifier):
                return env.get(node.name)

            elif isinstance(node, ImportStatement):
                module = self.load_module(node.module)
                alias = node.alias or node.module.split(".")[-1]
                env.define(alias, module)
                return module

            elif isinstance(node, FromImportStatement):
                module = self.load_module(node.module)
                for name, alias in node.imports:
                    if isinstance(module, dict):
                        value = module.get(name)
                    else:
                        value = getattr(module, name, None)
                    if value is None:
                        raise RuntimeError(f"Module '{node.module}' has no member '{name}'")
                    env.define(alias or name, value)
                return None

            elif isinstance(node, ArrayLiteral):
                values = [self.eval_node(elem, env) for elem in node.elements]
                self._check_list_length(values)
                return values

            elif isinstance(node, DictLiteral):
                result = {}
                for key_node, value_node in node.pairs:
                    key = self.eval_node(key_node, env)
                    value = self.eval_node(value_node, env)
                    result[key] = value
                return result

            elif isinstance(node, BinaryOp):
                return self.eval_binary_op(node, env)

            elif isinstance(node, UnaryOp):
                return self.eval_unary_op(node, env)

            elif isinstance(node, Assignment):
                value = self.eval_node(node.value, env)
                if env.exists(node.name):
                    env.set(node.name, value)
                else:
                    env.define(node.name, value, node.is_const)
                return value

            elif isinstance(node, FunctionCall):
                return self.eval_function_call(node, env)

            elif isinstance(node, CallExpression):
                return self.eval_call_expression(node, env)

            elif isinstance(node, IfStatement):
                condition = self.eval_node(node.condition, env)
                if self.is_truthy(condition):
                    result = None
                    for stmt in node.then_block:
                        result = self.eval_node(stmt, env)
                    return result
                elif node.else_block:
                    result = None
                    for stmt in node.else_block:
                        result = self.eval_node(stmt, env)
                    return result
                return None

            elif isinstance(node, WhileLoop):
                result = None
                iterations = 0
                while self.is_truthy(self.eval_node(node.condition, env)):
                    iterations += 1
                    if iterations > self.limits.max_loop_iterations:
                        raise self._runtime_error("Maximum loop iteration count exceeded", node, hint="Increase --max-loop, use --mode expert, or add #limits max_loop=<n>.")
                    for stmt in node.body:
                        result = self.eval_node(stmt, env)
                return result

            elif isinstance(node, ForLoop):
                iterable = self.eval_node(node.iterable, env)
                result = None
                iterations = 0
                for item in iterable:
                    iterations += 1
                    if iterations > self.limits.max_loop_iterations:
                        raise self._runtime_error("Maximum loop iteration count exceeded", node, hint="Increase --max-loop, use --mode expert, or add #limits max_loop=<n>.")
                    loop_env = Environment(env)
                    loop_env.define(node.variable, item)
                    for stmt in node.body:
                        result = self.eval_node(stmt, loop_env)
                return result

            elif isinstance(node, FunctionDef):
                env.define(node.name, node)
                return None

            elif isinstance(node, ReturnStatement):
                value = self.eval_node(node.value, env) if node.value else None
                raise ReturnValue(value)

            elif isinstance(node, IndexAccess):
                obj = self.eval_node(node.object, env)
                index = self.eval_node(node.index, env)
                return obj[index]

            elif isinstance(node, MemberAccess):
                obj = self.eval_node(node.object, env)
                if isinstance(obj, Bet):
                    return getattr(obj, node.member)
                elif isinstance(obj, dict):
                    return obj.get(node.member)
                else:
                    raise RuntimeError(f"Cannot access member '{node.member}' on {type(obj)}")

            elif isinstance(node, BetStatement):
                return self.eval_bet_statement(node, env)

            elif isinstance(node, ParlayStatement):
                return self.eval_parlay_statement(node, env)

            else:
                raise RuntimeError(f"Unknown node type: {type(node)}")
        except LanguageRuntimeError:
            raise
        except SandboxViolation as exc:
            raise self._runtime_error(str(exc), node, hint="Adjust --allow-read-dir/--allow-domain or disable --no-io.") from exc
        except (RuntimeError, TypeError, ValueError, ZeroDivisionError) as exc:
            hint = None
            msg = str(exc)
            if "Undefined variable" in msg:
                hint = "Declare it first with 'let name = ...' before using it."
            elif "not a function" in msg:
                hint = "Check the callee name and ensure you're calling a function value."
            elif "Cannot reassign constant" in msg:
                hint = "Use 'let' for mutable values, or avoid reassigning a 'const'."
            elif "expects" in msg and "arguments" in msg:
                hint = "Verify the function signature and the number of arguments passed."
            raise self._runtime_error(msg, node, hint=hint) from exc
        finally:
            self._exit_eval()

    def eval_binary_op(self, node: BinaryOp, env: Environment) -> Any:
        left = self.eval_node(node.left, env)
        right = self.eval_node(node.right, env)

        if node.operator == TokenType.PLUS:
            if isinstance(left, str) and isinstance(right, str):
                result = left + right
                self._check_string_length(result)
                return result
            if isinstance(left, list) and isinstance(right, list):
                result = left + right
                self._check_list_length(result)
                return result
            return left + right
        elif node.operator == TokenType.MINUS:
            return left - right
        elif node.operator == TokenType.MULTIPLY:
            return left * right
        elif node.operator == TokenType.DIVIDE:
            return left / right
        elif node.operator == TokenType.MODULO:
            return left % right
        elif node.operator == TokenType.EQUAL:
            return left == right
        elif node.operator == TokenType.NOT_EQUAL:
            return left != right
        elif node.operator == TokenType.LESS_THAN:
            return left < right
        elif node.operator == TokenType.GREATER_THAN:
            return left > right
        elif node.operator == TokenType.LESS_EQUAL:
            return left <= right
        elif node.operator == TokenType.GREATER_EQUAL:
            return left >= right
        elif node.operator == TokenType.AND:
            return self.is_truthy(left) and self.is_truthy(right)
        elif node.operator == TokenType.OR:
            return self.is_truthy(left) or self.is_truthy(right)
        else:
            raise RuntimeError(f"Unknown binary operator: {node.operator}")

    def eval_unary_op(self, node: UnaryOp, env: Environment) -> Any:
        operand = self.eval_node(node.operand, env)

        if node.operator == TokenType.MINUS:
            return -operand
        elif node.operator == TokenType.NOT:
            return not self.is_truthy(operand)
        else:
            raise RuntimeError(f"Unknown unary operator: {node.operator}")

    def eval_function_call(self, node: FunctionCall, env: Environment) -> Any:
        if node.name == 'print':
            args = [self.eval_node(arg, env) for arg in node.arguments]
            print(*args)
            return None

        func = env.get(node.name)

        # Built-in Python function
        if callable(func) and not isinstance(func, FunctionDef):
            args = [self.eval_node(arg, env) for arg in node.arguments]
            return func(*args)

        # User-defined function
        if isinstance(func, FunctionDef):
            if len(node.arguments) != len(func.parameters):
                raise RuntimeError(f"Function '{node.name}' expects {len(func.parameters)} arguments, got {len(node.arguments)}")

            func_env = Environment(env)
            for param, arg in zip(func.parameters, node.arguments):
                arg_value = self.eval_node(arg, env)
                func_env.define(param, arg_value)

            try:
                result = None
                for stmt in func.body:
                    result = self.eval_node(stmt, func_env)
                return result
            except ReturnValue as ret:
                return ret.value

        raise RuntimeError(f"'{node.name}' is not a function")

    def eval_call_expression(self, node: CallExpression, env: Environment) -> Any:
        callee = self.eval_node(node.callee, env)
        args = [self.eval_node(arg, env) for arg in node.arguments]

        if isinstance(callee, FunctionDef):
            if len(args) != len(callee.parameters):
                raise RuntimeError(
                    f"Function expects {len(callee.parameters)} arguments, got {len(args)}"
                )

            func_env = Environment(env)
            for param, arg_value in zip(callee.parameters, args):
                func_env.define(param, arg_value)

            try:
                result = None
                for stmt in callee.body:
                    result = self.eval_node(stmt, func_env)
                return result
            except ReturnValue as ret:
                return ret.value

        if callable(callee):
            return callee(*args)

        raise RuntimeError("Target is not callable")

    def eval_bet_statement(self, node: BetStatement, env: Environment) -> Bet:
        team = self.eval_node(node.team, env)
        odds = self.eval_node(node.odds, env) if node.odds else -110
        stake = self.eval_node(node.stake, env) if node.stake else 100

        kwargs = {}
        for key, value_node in node.additional_params.items():
            kwargs[key] = self.eval_node(value_node, env)

        bet = Bet(node.bet_type, team, odds, stake, **kwargs)
        print(f"Created: {bet}")
        return bet

    def eval_parlay_statement(self, node: ParlayStatement, env: Environment) -> Dict[str, Any]:
        bets = [self.eval_node(bet_node, env) for bet_node in node.bets]
        stake = self.eval_node(node.stake, env) if node.stake else 100

        # Calculate combined odds
        combined_decimal = 1
        for bet in bets:
            if isinstance(bet, Bet):
                combined_decimal *= bet.to_decimal_odds()

        # Convert back to American odds
        if combined_decimal >= 2.0:
            combined_american = (combined_decimal - 1) * 100
        else:
            combined_american = -100 / (combined_decimal - 1)

        potential_payout = stake * (combined_decimal - 1)

        parlay = {
            'bets': bets,
            'stake': stake,
            'combined_odds': combined_american,
            'decimal_odds': combined_decimal,
            'potential_payout': potential_payout,
            'total_return': stake + potential_payout
        }

        print(f"Parlay created: {len(bets)} legs, ${stake:.2f} to win ${potential_payout:.2f}")
        return parlay

    def is_truthy(self, value: Any) -> bool:
        """Determine if a value is truthy"""
        if value is None or value is False:
            return False
        if value == 0 or value == "":
            return False
        return True
