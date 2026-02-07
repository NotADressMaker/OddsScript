"""
SportsBetLang Interpreter - Executes the AST with built-in betting functions
"""

import csv
import json
import math
import urllib.error
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from io import StringIO
from typing import Any, Dict, List, Optional
from parser import *
from lexer import TokenType
from lib.poisson_calculator import PoissonCalculator
from lib.elo_totals import EloTotalsModel


@dataclass(frozen=True)
class TaggedNumber:
    value: float
    tag: str

    def __float__(self) -> float:
        return float(self.value)

    def _coerce(self, other: Any) -> float:
        return other.value if isinstance(other, TaggedNumber) else float(other)

    def __add__(self, other: Any) -> float:
        return float(self.value) + self._coerce(other)

    def __radd__(self, other: Any) -> float:
        return self._coerce(other) + float(self.value)

    def __sub__(self, other: Any) -> float:
        return float(self.value) - self._coerce(other)

    def __rsub__(self, other: Any) -> float:
        return self._coerce(other) - float(self.value)

    def __mul__(self, other: Any) -> float:
        return float(self.value) * self._coerce(other)

    def __rmul__(self, other: Any) -> float:
        return self._coerce(other) * float(self.value)

    def __truediv__(self, other: Any) -> float:
        return float(self.value) / self._coerce(other)

    def __rtruediv__(self, other: Any) -> float:
        return self._coerce(other) / float(self.value)


class ReturnValue(Exception):
    """Exception used to handle return statements"""
    def __init__(self, value):
        self.value = value


@dataclass
class LanguageRuntimeError(RuntimeError):
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    call_stack: Optional[List[str]] = None

    def __post_init__(self) -> None:
        super().__init__(self.message)

    def format(self) -> str:
        details = self.message
        if self.line is not None and self.column is not None:
            details = f"{details} (line {self.line}, column {self.column})"
        if self.call_stack:
            details = f"{details}\nCall stack:\n  " + "\n  ".join(self.call_stack)
        return details

    def __str__(self) -> str:
        return self.format()


class Environment:
    """Manages variable scopes"""
    def __init__(self, parent: Optional['Environment'] = None):
        self.variables: Dict[str, Any] = {}
        self.constants: set = set()
        self.parent = parent

    def define(self, name: str, value: Any, is_const: bool = False):
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

    def set(self, name: str, value: Any):
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
    def __init__(self, bet_type: str, team: str, odds: float, stake: float, **kwargs):
        self.bet_type = bet_type
        self.team = team
        self.odds = odds
        self.stake = stake
        self.spread = kwargs.get('spread', None)
        self.result = None  # 'win', 'loss', 'push'

    def calculate_payout(self) -> float:
        """Calculate potential payout"""
        if self.odds > 0:  # American odds (positive)
            return self.stake * (self.odds / 100)
        else:  # American odds (negative)
            return self.stake * (100 / abs(self.odds))

    def calculate_total_return(self) -> float:
        """Calculate total return including stake"""
        return self.stake + self.calculate_payout()

    def to_decimal_odds(self) -> float:
        """Convert American odds to decimal"""
        if self.odds > 0:
            return (self.odds / 100) + 1
        else:
            return (100 / abs(self.odds)) + 1

    def __repr__(self):
        spread_info = f" ({self.spread:+.1f})" if self.spread else ""
        return f"Bet({self.bet_type}: {self.team}{spread_info} @ {self.odds:+.2f}, ${self.stake:.2f})"


class Module:
    """Represents a module namespace"""
    def __init__(self, name: str, exports: Dict[str, Any]):
        self.name = name
        self.exports = exports

    def get(self, name: str) -> Any:
        if name in self.exports:
            return self.exports[name]
        raise RuntimeError(f"Module '{self.name}' has no member '{name}'")


class Interpreter:
    def __init__(self, max_steps: int = 1_000_000, max_call_depth: int = 1_000):
        self.global_env = Environment()
        self.modules: Dict[str, Module] = {}
        self.max_steps = max_steps
        self.max_call_depth = max_call_depth
        self.steps_remaining = max_steps
        self.call_stack: List[str] = []
        self.setup_builtins()

    def unwrap_number(self, value: Any, expected_tag: Optional[str] = None, label: str = "value") -> float:
        if isinstance(value, TaggedNumber):
            if expected_tag and value.tag != expected_tag:
                raise RuntimeError(f"Expected {label} to be '{expected_tag}', got '{value.tag}'")
            return value.value
        if isinstance(value, (int, float)):
            return value
        raise RuntimeError(f"Expected {label} to be a number")

    def unwrap_tagged(self, value: Any) -> Any:
        if isinstance(value, TaggedNumber):
            return value.value
        return value

    def setup_builtins(self):
        """Setup built-in functions for betting operations"""

        def register_builtin(name: str, func: Any, module: Optional[str] = None):
            self.global_env.define(name, func)
            if module:
                module_exports = modules.setdefault(module, {})
                module_exports[name] = func

        modules: Dict[str, Dict[str, Any]] = {}

        def ensure_probability(value: Any, label: str = "probability") -> float:
            if isinstance(value, TaggedNumber):
                if value.tag != "probability":
                    raise RuntimeError(f"Expected {label} to be 'probability', got '{value.tag}'")
                prob_value = value.value
            elif isinstance(value, (int, float)):
                prob_value = value
            else:
                raise RuntimeError(f"Expected {label} to be a probability")

            if not 0 <= prob_value <= 1:
                raise RuntimeError(f"Expected {label} to be between 0 and 1")
            return prob_value

        def ensure_string(value: Any, label: str = "value") -> str:
            value = self.unwrap_tagged(value)
            if not isinstance(value, str):
                raise RuntimeError(f"Expected {label} to be a string")
            return value

        def american_to_decimal(odds: float) -> float:
            """Convert American odds to decimal odds"""
            odds_value = self.unwrap_number(odds, expected_tag="odds", label="odds")
            if odds_value > 0:
                return (odds_value / 100) + 1
            else:
                return (100 / abs(odds_value)) + 1

        def decimal_to_american(odds: Any) -> float:
            """Convert decimal odds to American odds"""
            odds_value = self.unwrap_number(odds, expected_tag="odds", label="decimal_odds")
            if odds_value >= 2.0:
                return (odds_value - 1) * 100
            else:
                return -100 / (odds_value - 1)

        def implied_probability(odds: Any) -> TaggedNumber:
            """Calculate implied probability from American odds"""
            odds_value = self.unwrap_number(odds, expected_tag="odds", label="odds")
            if odds_value > 0:
                probability = 100 / (odds_value + 100)
            else:
                probability = abs(odds_value) / (abs(odds_value) + 100)
            return TaggedNumber(probability, "probability")

        def calculate_ev(true_prob: Any, odds: Any, stake: Any = 100) -> float:
            """Calculate expected value of a bet"""
            prob = ensure_probability(true_prob, label="true_prob")
            decimal_odds = american_to_decimal(odds)
            stake_value = self.unwrap_number(stake, expected_tag="stake", label="stake")
            win_amount = stake_value * (decimal_odds - 1)
            loss_amount = stake_value
            ev = (prob * win_amount) - ((1 - prob) * loss_amount)
            return ev

        def kelly_criterion(true_prob: Any, odds: Any) -> float:
            """Calculate optimal bet size using Kelly Criterion"""
            prob = ensure_probability(true_prob, label="true_prob")
            decimal_odds = american_to_decimal(odds)
            b = decimal_odds - 1  # net odds received on the wager
            p = prob
            q = 1 - p
            kelly = (b * p - q) / b
            return max(0, kelly)  # Don't bet if kelly is negative

        def parlay_odds(*odds_list) -> float:
            """Calculate parlay odds from multiple bets"""
            decimal_odds = [american_to_decimal(o) for o in odds_list]
            combined = 1
            for odd in decimal_odds:
                combined *= odd
            return decimal_to_american(combined)

        def parlay_probability(*probs) -> TaggedNumber:
            """Calculate probability of winning a parlay"""
            result = 1
            for p in probs:
                result *= ensure_probability(p, label="parlay_prob")
            return TaggedNumber(result, "probability")

        def break_even_percentage(odds: Any) -> TaggedNumber:
            """Calculate break-even win percentage"""
            return implied_probability(odds)

        def vig_calculator(odds1: Any, odds2: Any) -> float:
            """Calculate bookmaker's vig (juice) from two-way market"""
            prob1 = ensure_probability(implied_probability(odds1), label="odds1")
            prob2 = ensure_probability(implied_probability(odds2), label="odds2")
            total = prob1 + prob2
            vig = total - 1
            return vig * 100  # Return as percentage

        def true_odds_from_vig(odds: Any, total_vig: float) -> float:
            """Remove vig to get true odds"""
            implied_prob = ensure_probability(implied_probability(odds), label="odds")
            true_prob = implied_prob / (1 + total_vig)
            if true_prob >= 0.5:
                true_american = -100 * true_prob / (1 - true_prob)
            else:
                true_american = 100 * (1 - true_prob) / true_prob
            return true_american

        def units_to_risk(odds: Any, units_to_win: Any = 1) -> float:
            """Calculate units to risk to win specified units"""
            odds_value = self.unwrap_number(odds, expected_tag="odds", label="odds")
            units_value = self.unwrap_number(units_to_win, expected_tag="stake", label="units_to_win")
            if odds_value > 0:
                return units_value * (100 / odds_value)
            else:
                return units_value * (abs(odds_value) / 100)

        def roi_calculator(wins: int, losses: int, avg_odds: Any) -> float:
            """Calculate ROI from betting record"""
            if wins + losses == 0:
                return 0
            win_rate = wins / (wins + losses)
            avg_payout = calculate_ev(win_rate, avg_odds, 100)
            total_staked = (wins + losses) * 100
            total_return = wins * (100 + abs(avg_payout))
            roi = ((total_return - total_staked) / total_staked) * 100
            return roi

        def round_robin(bets_count: int, parlay_size: int) -> int:
            """Calculate number of parlays in a round robin"""
            from math import comb
            return comb(bets_count, parlay_size)

        def arbitrage_stakes(odds1: Any, odds2: Any, total_stake: Any = 100) -> Dict:
            """Calculate two-way arbitrage stakes and expected profit"""
            decimal1 = american_to_decimal(odds1)
            decimal2 = american_to_decimal(odds2)

            implied1 = 1 / decimal1
            implied2 = 1 / decimal2
            total_implied = implied1 + implied2

            total_value = self.unwrap_number(total_stake, expected_tag="stake", label="total_stake")
            stake1 = total_value * (implied1 / total_implied)
            stake2 = total_value * (implied2 / total_implied)

            payout1 = stake1 * decimal1
            payout2 = stake2 * decimal2
            profit = min(payout1, payout2) - total_value

            return {
                'odds1': odds1,
                'odds2': odds2,
                'stake_total': total_value,
                'stake1': stake1,
                'stake2': stake2,
                'total_implied': total_implied,
                'arb_margin_pct': (1 - total_implied) * 100,
                'profit': profit,
                'roi_pct': (profit / total_value) * 100
            }

        def hedge_stake(odds: Any, stake: Any, hedge_odds: Any) -> Dict:
            """Calculate hedge stake to lock in profit on a two-way bet"""
            decimal_main = american_to_decimal(odds)
            decimal_hedge = american_to_decimal(hedge_odds)

            stake_value = self.unwrap_number(stake, expected_tag="stake", label="stake")
            hedge_amount = stake_value * (decimal_main - 1) / (decimal_hedge - 1)
            total_stake = stake_value + hedge_amount

            profit_main = (stake_value * decimal_main) - total_stake
            profit_hedge = (hedge_amount * decimal_hedge) - total_stake

            return {
                'original_odds': odds,
                'original_stake': stake_value,
                'hedge_odds': hedge_odds,
                'hedge_stake': hedge_amount,
                'total_stake': total_stake,
                'profit_if_original_wins': profit_main,
                'profit_if_hedge_wins': profit_hedge,
                'locked_profit': min(profit_main, profit_hedge)
            }

        def elo_totals_init(
            league: str = "NBA",
            k: float = 20.0,
            base_total: Optional[float] = None,
            base_total_std: Optional[float] = None,
            points_per_elo: float = 0.025,
        ) -> EloTotalsModel:
            """Initialize an Elo totals model instance."""
            return EloTotalsModel(
                league=league,
                k_factor=k,
                base_total=base_total,
                base_total_std=base_total_std,
                points_per_elo=points_per_elo,
            )

        def elo_totals_update(model: Any, game: Any) -> None:
            """Update model ratings with a game dict/object."""
            if not isinstance(model, EloTotalsModel):
                raise RuntimeError("elo_totals.update expects a model handle")
            model.update(game)

        def elo_totals_predict_total(
            model: Any,
            home: str,
            away: str,
            neutral: bool = False,
            home_field_adv: Optional[float] = None,
            league_avg_total: Optional[float] = None,
        ) -> float:
            """Predict total points for a matchup."""
            if not isinstance(model, EloTotalsModel):
                raise RuntimeError("elo_totals.predict_total expects a model handle")
            return model.predict_total(
                home,
                away,
                neutral_site=neutral,
                home_field_adv=home_field_adv,
                league_avg_total=league_avg_total,
            )

        def elo_totals_prob_over(
            model: Any,
            home: str,
            away: str,
            line: Any,
            neutral: bool = False,
            home_field_adv: Optional[float] = None,
            league_avg_total: Optional[float] = None,
        ) -> TaggedNumber:
            """Probability that total points go over the line."""
            if not isinstance(model, EloTotalsModel):
                raise RuntimeError("elo_totals.prob_over expects a model handle")
            line_value = self.unwrap_number(line, label="line")
            probability = model.prob_over(
                home,
                away,
                line_value,
                neutral_site=neutral,
                home_field_adv=home_field_adv,
                league_avg_total=league_avg_total,
            )
            return TaggedNumber(probability, "probability")

        def elo_totals_predict_distribution(
            model: Any,
            home: str,
            away: str,
            neutral: bool = False,
            home_field_adv: Optional[float] = None,
            league_avg_total: Optional[float] = None,
        ) -> Dict[str, float]:
            """Return a dict with mean/std for total points."""
            if not isinstance(model, EloTotalsModel):
                raise RuntimeError("elo_totals.predict_distribution expects a model handle")
            mean, std = model.predict_distribution(
                home,
                away,
                neutral_site=neutral,
                home_field_adv=home_field_adv,
                league_avg_total=league_avg_total,
            )
            return {"mean": mean, "std": std}

        # Poisson Distribution Simulation Functions
        def poisson_probability(k: int, lambda_param: float) -> float:
            """Calculate Poisson probability P(X = k)"""
            return PoissonCalculator.poisson_probability(k, lambda_param)

        def poisson_cumulative(k: int, lambda_param: float) -> float:
            """Calculate cumulative Poisson probability P(X <= k)"""
            return PoissonCalculator.poisson_cumulative(k, lambda_param)

        def poisson_simulate_event(lambda_param: float) -> int:
            """Simulate a single Poisson-distributed event (returns number of goals/points)"""
            return PoissonCalculator.simulate_poisson_event(lambda_param)

        def poisson_simulate_match(home_lambda: float, away_lambda: float) -> Dict:
            """Simulate a single match outcome using Poisson distribution"""
            return PoissonCalculator.simulate_match(home_lambda, away_lambda)

        def poisson_simulate_matches(home_lambda: float, away_lambda: float, num_simulations: int) -> Dict:
            """Run Monte Carlo simulation of multiple matches"""
            return PoissonCalculator.simulate_matches(home_lambda, away_lambda, num_simulations)

        def web_get(url: Any, timeout: Any = 10, headers: Any = None) -> str:
            """Fetch a URL and return response text."""
            url_value = ensure_string(url, label="url")
            timeout_value = self.unwrap_number(timeout, label="timeout")
            header_map: Dict[str, str] = {}
            if headers is not None:
                headers_value = self.unwrap_tagged(headers)
                if not isinstance(headers_value, dict):
                    raise RuntimeError("Expected headers to be a dictionary")
                header_map = {str(key): str(value) for key, value in headers_value.items()}
            request = urllib.request.Request(url_value, headers=header_map)
            try:
                with urllib.request.urlopen(request, timeout=timeout_value) as response:
                    encoding = response.headers.get_content_charset() or "utf-8"
                    return response.read().decode(encoding, errors="replace")
            except urllib.error.HTTPError as err:
                raise RuntimeError(f"HTTP error {err.code} while fetching {url_value}")
            except urllib.error.URLError as err:
                raise RuntimeError(f"Failed to fetch {url_value}: {err.reason}")

        class HTMLTableParser(HTMLParser):
            def __init__(self) -> None:
                super().__init__()
                self.tables: List[List[List[str]]] = []
                self._current_table: List[List[str]] = []
                self._current_row: List[str] = []
                self._cell_chunks: List[str] = []
                self._in_table = False
                self._in_row = False
                self._in_cell = False

            def handle_starttag(self, tag: str, attrs: List[tuple]) -> None:
                if tag == "table":
                    self._in_table = True
                    self._current_table = []
                elif self._in_table and tag == "tr":
                    self._in_row = True
                    self._current_row = []
                elif self._in_row and tag in ("td", "th"):
                    self._in_cell = True
                    self._cell_chunks = []

            def handle_endtag(self, tag: str) -> None:
                if tag in ("td", "th") and self._in_cell:
                    cell_text = "".join(self._cell_chunks).strip()
                    self._current_row.append(cell_text)
                    self._in_cell = False
                elif tag == "tr" and self._in_row:
                    if self._current_row:
                        self._current_table.append(self._current_row)
                    self._in_row = False
                elif tag == "table" and self._in_table:
                    if self._current_table:
                        self.tables.append(self._current_table)
                    self._in_table = False

            def handle_data(self, data: str) -> None:
                if self._in_cell:
                    self._cell_chunks.append(data)

        def parse_html_tables(html_text: str) -> List[List[List[str]]]:
            parser = HTMLTableParser()
            parser.feed(html_text)
            return parser.tables

        def parse_csv_text(csv_text: str) -> List[Dict[str, str]]:
            reader = csv.DictReader(StringIO(csv_text))
            return [dict(row) for row in reader]

        def web_get_json(url: Any, timeout: Any = 10, headers: Any = None) -> Any:
            """Fetch a URL and parse the response as JSON."""
            text = web_get(url, timeout=timeout, headers=headers)
            try:
                return json.loads(text)
            except json.JSONDecodeError as err:
                raise RuntimeError(f"Failed to parse JSON from {url}: {err}")

        def web_get_table(url: Any, table_index: Any = 0, timeout: Any = 10, headers: Any = None) -> Any:
            """Fetch a URL and extract a table by index."""
            index_value = int(self.unwrap_number(table_index, label="table_index"))
            html_text = web_get(url, timeout=timeout, headers=headers)
            tables = parse_html_tables(html_text)
            if not tables:
                raise RuntimeError(f"No HTML tables found at {ensure_string(url, label='url')}")
            if index_value < 0 or index_value >= len(tables):
                raise RuntimeError(f"Table index {index_value} out of range (found {len(tables)} tables)")
            return tables[index_value]

        def web_get_tables(url: Any, timeout: Any = 10, headers: Any = None) -> Any:
            """Fetch a URL and extract all HTML tables."""
            html_text = web_get(url, timeout=timeout, headers=headers)
            return parse_html_tables(html_text)

        def web_get_csv(url: Any, timeout: Any = 10, headers: Any = None) -> Any:
            """Fetch a URL and parse CSV into a list of dictionaries."""
            csv_text = web_get(url, timeout=timeout, headers=headers)
            return parse_csv_text(csv_text)

        def to_json(value: Any) -> str:
            """Serialize a value to pretty JSON."""
            return json.dumps(value, indent=2, default=str)

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

        # Register built-in functions
        register_builtin('american_to_decimal', american_to_decimal, module='betting')
        register_builtin('decimal_to_american', decimal_to_american, module='betting')
        register_builtin('implied_probability', implied_probability, module='betting')
        register_builtin('calculate_ev', calculate_ev, module='betting')
        register_builtin('kelly_criterion', kelly_criterion, module='betting')
        register_builtin('parlay_odds', parlay_odds, module='betting')
        register_builtin('parlay_probability', parlay_probability, module='betting')
        register_builtin('break_even_percentage', break_even_percentage, module='betting')
        register_builtin('vig_calculator', vig_calculator, module='betting')
        register_builtin('true_odds_from_vig', true_odds_from_vig, module='betting')
        register_builtin('units_to_risk', units_to_risk, module='betting')
        register_builtin('roi_calculator', roi_calculator, module='betting')
        register_builtin('round_robin', round_robin, module='betting')
        register_builtin('arbitrage_stakes', arbitrage_stakes, module='betting')
        register_builtin('hedge_stake', hedge_stake, module='betting')
        register_builtin('init', elo_totals_init, module='elo_totals')
        register_builtin('update', elo_totals_update, module='elo_totals')
        register_builtin('predict_total', elo_totals_predict_total, module='elo_totals')
        register_builtin('prob_over', elo_totals_prob_over, module='elo_totals')
        register_builtin('predict_distribution', elo_totals_predict_distribution, module='elo_totals')
        register_builtin('abs', abs, module='core')
        register_builtin('min', min, module='core')
        register_builtin('max', max, module='core')
        register_builtin('sqrt', math.sqrt, module='core')
        register_builtin('pow', pow, module='core')
        register_builtin('len', len, module='core')
        register_builtin('range', range, module='core')
        register_builtin('sum', sum, module='core')
        register_builtin('to_json', to_json, module='core')
        register_builtin('to_csv', to_csv, module='core')

        # Poisson distribution functions
        register_builtin('poisson_probability', poisson_probability, module='stats')
        register_builtin('poisson_cumulative', poisson_cumulative, module='stats')
        register_builtin('poisson_simulate_event', poisson_simulate_event, module='stats')
        register_builtin('poisson_simulate_match', poisson_simulate_match, module='stats')
        register_builtin('poisson_simulate_matches', poisson_simulate_matches, module='stats')
        register_builtin('get', web_get, module='web')
        register_builtin('get_json', web_get_json, module='web')
        register_builtin('get_table', web_get_table, module='web')
        register_builtin('get_tables', web_get_tables, module='web')
        register_builtin('get_csv', web_get_csv, module='web')

        for name, exports in modules.items():
            self.modules[name] = Module(name, exports)

    def load_module(self, module_path: str) -> Module:
        if module_path in self.modules:
            return self.modules[module_path]
        raise RuntimeError(f"Unknown module '{module_path}'")

    def interpret(self, program: Program) -> Any:
        """Execute the program"""
        self.steps_remaining = self.max_steps
        program = self.optimize_program(program)
        result = None
        for statement in program.statements:
            result = self.eval_node(statement, self.global_env)
        return result

    def runtime_error(self, message: str, node: Optional[ASTNode] = None) -> None:
        line = getattr(node, "line", None) if node else None
        column = getattr(node, "column", None) if node else None
        raise LanguageRuntimeError(message, line=line, column=column, call_stack=list(self.call_stack))

    def tick(self, node: Optional[ASTNode] = None) -> None:
        self.steps_remaining -= 1
        if self.steps_remaining < 0:
            self.runtime_error("Execution step limit exceeded", node)

    def optimize_program(self, program: Program) -> Program:
        return Program(
            statements=self.optimize_statements(program.statements),
            line=program.line,
            column=program.column,
        )

    def optimize_statements(self, statements: List[ASTNode]) -> List[ASTNode]:
        optimized: List[ASTNode] = []
        for statement in statements:
            optimized.extend(self.optimize_statement(statement))
        return optimized

    def optimize_statement(self, statement: ASTNode) -> List[ASTNode]:
        if isinstance(statement, IfStatement):
            condition = self.optimize_node(statement.condition)
            if self.is_literal(condition):
                if self.is_truthy_literal(condition):
                    return self.optimize_statements(statement.then_block)
                return self.optimize_statements(statement.else_block or [])
            then_block = self.optimize_statements(statement.then_block)
            else_block = (
                self.optimize_statements(statement.else_block) if statement.else_block else None
            )
            return [
                IfStatement(
                    condition=condition,
                    then_block=then_block,
                    else_block=else_block,
                    line=statement.line,
                    column=statement.column,
                )
            ]

        if isinstance(statement, WhileLoop):
            condition = self.optimize_node(statement.condition)
            if self.is_literal(condition) and not self.is_truthy_literal(condition):
                return []
            body = self.optimize_statements(statement.body)
            return [
                WhileLoop(
                    condition=condition,
                    body=body,
                    line=statement.line,
                    column=statement.column,
                )
            ]

        if isinstance(statement, ForLoop):
            iterable = self.optimize_node(statement.iterable)
            body = self.optimize_statements(statement.body)
            return [
                ForLoop(
                    variable=statement.variable,
                    iterable=iterable,
                    body=body,
                    line=statement.line,
                    column=statement.column,
                )
            ]

        optimized = self.optimize_node(statement)
        return [optimized] if optimized is not None else []

    def optimize_node(self, node: ASTNode) -> ASTNode:
        if isinstance(node, Program):
            return self.optimize_program(node)

        if isinstance(node, BinaryOp):
            left = self.optimize_node(node.left)
            right = self.optimize_node(node.right)
            folded = self.try_fold_binary(node, left, right)
            if folded:
                return folded
            return BinaryOp(
                left=left,
                operator=node.operator,
                right=right,
                line=node.line,
                column=node.column,
            )

        if isinstance(node, UnaryOp):
            operand = self.optimize_node(node.operand)
            folded = self.try_fold_unary(node, operand)
            if folded:
                return folded
            return UnaryOp(
                operator=node.operator,
                operand=operand,
                line=node.line,
                column=node.column,
            )

        if isinstance(node, ArrayLiteral):
            elements = [self.optimize_node(elem) for elem in node.elements]
            return ArrayLiteral(elements=elements, line=node.line, column=node.column)

        if isinstance(node, DictLiteral):
            pairs = [
                (self.optimize_node(key), self.optimize_node(value))
                for key, value in node.pairs
            ]
            return DictLiteral(pairs=pairs, line=node.line, column=node.column)

        if isinstance(node, IndexAccess):
            return IndexAccess(
                object=self.optimize_node(node.object),
                index=self.optimize_node(node.index),
                line=node.line,
                column=node.column,
            )

        if isinstance(node, MemberAccess):
            return MemberAccess(
                object=self.optimize_node(node.object),
                member=node.member,
                line=node.line,
                column=node.column,
            )

        if isinstance(node, Assignment):
            return Assignment(
                name=node.name,
                value=self.optimize_node(node.value),
                is_const=node.is_const,
                line=node.line,
                column=node.column,
            )

        if isinstance(node, FunctionCall):
            return FunctionCall(
                name=node.name,
                arguments=[self.optimize_node(arg) for arg in node.arguments],
                line=node.line,
                column=node.column,
            )

        if isinstance(node, CallExpression):
            return CallExpression(
                callee=self.optimize_node(node.callee),
                arguments=[self.optimize_node(arg) for arg in node.arguments],
                line=node.line,
                column=node.column,
            )

        if isinstance(node, FunctionDef):
            return FunctionDef(
                name=node.name,
                parameters=node.parameters,
                body=self.optimize_statements(node.body),
                line=node.line,
                column=node.column,
            )

        if isinstance(node, ReturnStatement):
            value = self.optimize_node(node.value) if node.value else None
            return ReturnStatement(value=value, line=node.line, column=node.column)

        if isinstance(node, IfStatement):
            optimized = self.optimize_statement(node)
            return optimized[0] if optimized else node

        if isinstance(node, WhileLoop):
            optimized = self.optimize_statement(node)
            return optimized[0] if optimized else node

        if isinstance(node, ForLoop):
            optimized = self.optimize_statement(node)
            return optimized[0] if optimized else node

        if isinstance(node, BetStatement):
            additional_params = {
                key: self.optimize_node(value)
                for key, value in node.additional_params.items()
            }
            return BetStatement(
                bet_type=node.bet_type,
                team=self.optimize_node(node.team),
                odds=self.optimize_node(node.odds) if node.odds else None,
                stake=self.optimize_node(node.stake) if node.stake else None,
                additional_params=additional_params,
                line=node.line,
                column=node.column,
            )

        if isinstance(node, ParlayStatement):
            return ParlayStatement(
                bets=[self.optimize_node(bet) for bet in node.bets],
                stake=self.optimize_node(node.stake) if node.stake else None,
                line=node.line,
                column=node.column,
            )

        if isinstance(node, (NumberLiteral, StringLiteral, BooleanLiteral, Identifier, ImportStatement, FromImportStatement)):
            return node

        return node

    def try_fold_binary(self, node: BinaryOp, left: ASTNode, right: ASTNode) -> Optional[ASTNode]:
        if not (self.is_literal(left) and self.is_literal(right)):
            return None

        left_value = self.literal_value(left)
        right_value = self.literal_value(right)

        try:
            if node.operator == TokenType.PLUS:
                result = left_value + right_value
            elif node.operator == TokenType.MINUS:
                result = left_value - right_value
            elif node.operator == TokenType.MULTIPLY:
                result = left_value * right_value
            elif node.operator == TokenType.DIVIDE:
                result = left_value / right_value
            elif node.operator == TokenType.MODULO:
                result = left_value % right_value
            elif node.operator == TokenType.EQUAL:
                result = left_value == right_value
            elif node.operator == TokenType.NOT_EQUAL:
                result = left_value != right_value
            elif node.operator == TokenType.LESS_THAN:
                result = left_value < right_value
            elif node.operator == TokenType.GREATER_THAN:
                result = left_value > right_value
            elif node.operator == TokenType.LESS_EQUAL:
                result = left_value <= right_value
            elif node.operator == TokenType.GREATER_EQUAL:
                result = left_value >= right_value
            elif node.operator == TokenType.AND:
                result = self.is_truthy_literal(left) and self.is_truthy_literal(right)
            elif node.operator == TokenType.OR:
                result = self.is_truthy_literal(left) or self.is_truthy_literal(right)
            else:
                return None
        except Exception:
            return None

        return self.make_literal(result, node)

    def try_fold_unary(self, node: UnaryOp, operand: ASTNode) -> Optional[ASTNode]:
        if not self.is_literal(operand):
            return None

        value = self.literal_value(operand)
        try:
            if node.operator == TokenType.MINUS:
                result = -value
            elif node.operator == TokenType.NOT:
                result = not self.is_truthy_literal(operand)
            else:
                return None
        except Exception:
            return None

        return self.make_literal(result, node)

    def is_literal(self, node: ASTNode) -> bool:
        return isinstance(node, (NumberLiteral, StringLiteral, BooleanLiteral))

    def literal_value(self, node: ASTNode) -> Any:
        if isinstance(node, NumberLiteral):
            return node.value
        if isinstance(node, StringLiteral):
            return node.value
        if isinstance(node, BooleanLiteral):
            return node.value
        raise RuntimeError("Node is not a literal")

    def is_truthy_literal(self, node: ASTNode) -> bool:
        value = self.literal_value(node)
        if value is None or value is False:
            return False
        if value == 0 or value == "":
            return False
        return True

    def make_literal(self, value: Any, source: ASTNode) -> Optional[ASTNode]:
        if isinstance(value, bool):
            return BooleanLiteral(value=value, line=source.line, column=source.column)
        if isinstance(value, (int, float)):
            return NumberLiteral(value=value, line=source.line, column=source.column)
        if isinstance(value, str):
            return StringLiteral(value=value, line=source.line, column=source.column)
        return None

    def eval_node(self, node: ASTNode, env: Environment) -> Any:
        """Evaluate an AST node"""
        self.tick(node)

        try:
            return self._eval_node(node, env)
        except ReturnValue:
            raise
        except LanguageRuntimeError:
            raise
        except RuntimeError as err:
            self.runtime_error(str(err), node)

    def _eval_node(self, node: ASTNode, env: Environment) -> Any:
        """Internal evaluation implementation"""

        if isinstance(node, Program):
            result = None
            for statement in node.statements:
                result = self.eval_node(statement, env)
            return result

        elif isinstance(node, NumberLiteral):
            return node.value

        elif isinstance(node, StringLiteral):
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
                value = module.get(name)
                env.define(alias or name, value)
            return None

        elif isinstance(node, ArrayLiteral):
            return [self.eval_node(elem, env) for elem in node.elements]

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
            callee = self.eval_node(node.callee, env)
            return self.call_function_value(callee, node.arguments, env)

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
            while self.is_truthy(self.eval_node(node.condition, env)):
                for stmt in node.body:
                    result = self.eval_node(stmt, env)
            return result

        elif isinstance(node, ForLoop):
            iterable = self.eval_node(node.iterable, env)
            result = None
            for item in iterable:
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
            elif isinstance(obj, Module):
                return obj.get(node.member)
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

    def eval_binary_op(self, node: BinaryOp, env: Environment) -> Any:
        left = self.unwrap_tagged(self.eval_node(node.left, env))
        right = self.unwrap_tagged(self.eval_node(node.right, env))

        if node.operator == TokenType.PLUS:
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
        operand = self.unwrap_tagged(self.eval_node(node.operand, env))

        if node.operator == TokenType.MINUS:
            return -operand
        elif node.operator == TokenType.NOT:
            return not self.is_truthy(operand)
        else:
            raise RuntimeError(f"Unknown unary operator: {node.operator}")

    def call_function_value(self, func: Any, arg_nodes: List[ASTNode], env: Environment) -> Any:
        if callable(func) and not isinstance(func, FunctionDef):
            args = [self.eval_node(arg, env) for arg in arg_nodes]
            return func(*args)

        if isinstance(func, FunctionDef):
            if len(self.call_stack) >= self.max_call_depth:
                self.runtime_error("Maximum call depth exceeded", func)
            if len(arg_nodes) != len(func.parameters):
                raise RuntimeError(
                    f"Function '{func.name}' expects {len(func.parameters)} arguments, got {len(arg_nodes)}"
                )

            func_env = Environment(env)
            for param, arg in zip(func.parameters, arg_nodes):
                arg_value = self.eval_node(arg, env)
                func_env.define(param, arg_value)

            self.call_stack.append(func.name)
            try:
                result = None
                for stmt in func.body:
                    result = self.eval_node(stmt, func_env)
                return result
            except ReturnValue as ret:
                return ret.value
            finally:
                self.call_stack.pop()

        raise RuntimeError("Target is not a function")

    def eval_function_call(self, node: FunctionCall, env: Environment) -> Any:
        if node.name == 'print':
            args = [self.eval_node(arg, env) for arg in node.arguments]
            print(*args)
            return None

        func = env.get(node.name)

        try:
            return self.call_function_value(func, node.arguments, env)
        except RuntimeError as err:
            if str(err) == "Target is not a function":
                raise RuntimeError(f"'{node.name}' is not a function")
            raise

    def eval_bet_statement(self, node: BetStatement, env: Environment) -> Bet:
        team = self.eval_node(node.team, env)
        odds = self.eval_node(node.odds, env) if node.odds else -110
        stake = self.eval_node(node.stake, env) if node.stake else 100
        odds_value = self.unwrap_number(odds, expected_tag="odds", label="odds")
        stake_value = self.unwrap_number(stake, expected_tag="stake", label="stake")

        kwargs = {}
        for key, value_node in node.additional_params.items():
            kwargs[key] = self.unwrap_number(self.eval_node(value_node, env), label=key)

        bet = Bet(node.bet_type, team, odds_value, stake_value, **kwargs)
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
