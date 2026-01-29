"""
SportsBetLang Interpreter - Executes the AST with built-in betting functions
"""

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from parser import *
from lexer import TokenType
from lib.poisson_calculator import PoissonCalculator


class ReturnValue(Exception):
    """Exception used to handle return statements"""
    def __init__(self, value):
        self.value = value


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
        return f"Bet({self.bet_type}: {self.team}{spread_info} @ {self.odds:+d}, ${self.stake:.2f})"


class Module:
    """Represents a module namespace"""
    def __init__(self, name: str, exports: Dict[str, Any]):
        self.name = name
        self.exports = exports

    def get(self, name: str) -> Any:
        if name in self.exports:
            return self.exports[name]
        raise RuntimeError(f"Module '{self.name}' has no member '{name}'")


@dataclass(frozen=True)
class TaggedNumber:
    """Numeric value with a semantic tag (e.g., odds, probability, stake)."""
    value: float
    tag: str

    def _coerce_other(self, other: Any) -> float:
        if isinstance(other, TaggedNumber):
            if other.tag != self.tag:
                raise RuntimeError(f"Cannot mix tagged values '{self.tag}' and '{other.tag}'")
            return other.value
        if isinstance(other, (int, float)):
            return other
        raise RuntimeError(f"Cannot operate on tagged value with {type(other)}")

    def _binary_op(self, other: Any, op, op_name: str) -> "TaggedNumber":
        other_value = self._coerce_other(other)
        return TaggedNumber(op(self.value, other_value), self.tag)

    def _compare(self, other: Any, op, op_name: str) -> bool:
        other_value = self._coerce_other(other)
        return op(self.value, other_value)

    def __add__(self, other: Any) -> "TaggedNumber":
        return self._binary_op(other, lambda a, b: a + b, "add")

    def __radd__(self, other: Any) -> "TaggedNumber":
        return self.__add__(other)

    def __sub__(self, other: Any) -> "TaggedNumber":
        return self._binary_op(other, lambda a, b: a - b, "sub")

    def __rsub__(self, other: Any) -> "TaggedNumber":
        other_value = self._coerce_other(other)
        return TaggedNumber(other_value - self.value, self.tag)

    def __mul__(self, other: Any) -> "TaggedNumber":
        return self._binary_op(other, lambda a, b: a * b, "mul")

    def __rmul__(self, other: Any) -> "TaggedNumber":
        return self.__mul__(other)

    def __truediv__(self, other: Any) -> "TaggedNumber":
        return self._binary_op(other, lambda a, b: a / b, "truediv")

    def __rtruediv__(self, other: Any) -> "TaggedNumber":
        other_value = self._coerce_other(other)
        return TaggedNumber(other_value / self.value, self.tag)

    def __mod__(self, other: Any) -> "TaggedNumber":
        return self._binary_op(other, lambda a, b: a % b, "mod")

    def __rmod__(self, other: Any) -> "TaggedNumber":
        other_value = self._coerce_other(other)
        return TaggedNumber(other_value % self.value, self.tag)

    def __neg__(self) -> "TaggedNumber":
        return TaggedNumber(-self.value, self.tag)

    def __pos__(self) -> "TaggedNumber":
        return self

    def __eq__(self, other: Any) -> bool:
        return self._compare(other, lambda a, b: a == b, "eq")

    def __lt__(self, other: Any) -> bool:
        return self._compare(other, lambda a, b: a < b, "lt")

    def __le__(self, other: Any) -> bool:
        return self._compare(other, lambda a, b: a <= b, "le")

    def __gt__(self, other: Any) -> bool:
        return self._compare(other, lambda a, b: a > b, "gt")

    def __ge__(self, other: Any) -> bool:
        return self._compare(other, lambda a, b: a >= b, "ge")

    def __float__(self) -> float:
        return float(self.value)

    def __repr__(self) -> str:
        return f"{self.tag}({self.value})"


class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        self.modules: Dict[str, Module] = {}
        self.setup_builtins()

    def format_location(self, node: Optional[ASTNode]) -> str:
        if node is None:
            return ""
        line = getattr(node, "line", None)
        column = getattr(node, "column", None)
        if line is None or column is None:
            return ""
        return f" at {line}:{column}"

    def runtime_error(self, message: str, node: Optional[ASTNode]) -> None:
        raise RuntimeError(f"{message}{self.format_location(node)}")

    def unwrap_number(self, value: Any, expected_tag: Optional[str] = None, label: str = "value") -> float:
        if isinstance(value, TaggedNumber):
            if expected_tag and value.tag != expected_tag:
                raise RuntimeError(f"Expected {label} to be '{expected_tag}', got '{value.tag}'")
            return value.value
        if isinstance(value, (int, float)):
            return value
        raise RuntimeError(f"Expected {label} to be a number")

    def setup_builtins(self):
        """Setup built-in functions for betting operations"""

        def register_global_builtin(name: str, func: Any, module: Optional[str] = None):
            self.global_env.define(name, func)
            if module:
                module_exports = modules.setdefault(module, {})
                module_exports[name] = func

        def register_module_builtin(name: str, func: Any, module: str):
            module_exports = modules.setdefault(module, {})
            module_exports[name] = func

        modules: Dict[str, Dict[str, Any]] = {}

        def tag_value(tag: str, value: Any) -> TaggedNumber:
            return TaggedNumber(self.unwrap_number(value, label=tag), tag)

        def ensure_probability(value: Any, label: str = "probability") -> float:
            prob = self.unwrap_number(value, expected_tag="probability", label=label)
            if not 0 <= prob <= 1:
                raise RuntimeError(f"Expected {label} between 0 and 1, got {prob}")
            return prob

        def american_to_decimal(odds: Any) -> float:
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

        # Register built-in functions
        register_module_builtin('american_to_decimal', american_to_decimal, module='betting')
        register_module_builtin('decimal_to_american', decimal_to_american, module='betting')
        register_module_builtin('implied_probability', implied_probability, module='betting')
        register_module_builtin('calculate_ev', calculate_ev, module='betting')
        register_module_builtin('kelly_criterion', kelly_criterion, module='betting')
        register_module_builtin('parlay_odds', parlay_odds, module='betting')
        register_module_builtin('parlay_probability', parlay_probability, module='betting')
        register_module_builtin('break_even_percentage', break_even_percentage, module='betting')
        register_module_builtin('vig_calculator', vig_calculator, module='betting')
        register_module_builtin('true_odds_from_vig', true_odds_from_vig, module='betting')
        register_module_builtin('units_to_risk', units_to_risk, module='betting')
        register_module_builtin('roi_calculator', roi_calculator, module='betting')
        register_module_builtin('round_robin', round_robin, module='betting')
        register_module_builtin('arbitrage_stakes', arbitrage_stakes, module='betting')
        register_module_builtin('hedge_stake', hedge_stake, module='betting')
        register_global_builtin('odds', lambda value: tag_value("odds", value), module='core')
        register_global_builtin('probability', lambda value: tag_value("probability", value), module='core')
        register_global_builtin('stake', lambda value: tag_value("stake", value), module='core')
        register_global_builtin('abs', abs, module='core')
        register_global_builtin('min', min, module='core')
        register_global_builtin('max', max, module='core')
        register_global_builtin('sqrt', math.sqrt, module='core')
        register_global_builtin('pow', pow, module='core')
        register_global_builtin('len', len, module='core')
        register_global_builtin('range', range, module='core')
        register_global_builtin('sum', sum, module='core')

        # Poisson distribution functions
        register_module_builtin('poisson_probability', poisson_probability, module='stats')
        register_module_builtin('poisson_cumulative', poisson_cumulative, module='stats')
        register_module_builtin('poisson_simulate_event', poisson_simulate_event, module='stats')
        register_module_builtin('poisson_simulate_match', poisson_simulate_match, module='stats')
        register_module_builtin('poisson_simulate_matches', poisson_simulate_matches, module='stats')

        for name, exports in modules.items():
            self.modules[name] = Module(name, exports)

    def load_module(self, module_path: str) -> Module:
        if module_path in self.modules:
            return self.modules[module_path]
        raise RuntimeError(f"Unknown module '{module_path}'")

    def interpret(self, program: Program) -> Any:
        """Execute the program"""
        result = None
        for statement in program.statements:
            result = self.eval_node(statement, self.global_env)
        return result

    def eval_node(self, node: ASTNode, env: Environment) -> Any:
        """Evaluate an AST node"""

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
            try:
                return env.get(node.name)
            except RuntimeError as err:
                self.runtime_error(str(err), node)

        elif isinstance(node, ImportStatement):
            try:
                module = self.load_module(node.module)
                alias = node.alias or node.module.split(".")[-1]
                env.define(alias, module)
                return module
            except RuntimeError as err:
                self.runtime_error(str(err), node)

        elif isinstance(node, FromImportStatement):
            try:
                module = self.load_module(node.module)
                for name, alias in node.imports:
                    value = module.get(name)
                    env.define(alias or name, value)
                return None
            except RuntimeError as err:
                self.runtime_error(str(err), node)

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
            try:
                if env.exists(node.name):
                    env.set(node.name, value)
                else:
                    env.define(node.name, value, node.is_const)
                return value
            except RuntimeError as err:
                self.runtime_error(str(err), node)

        elif isinstance(node, FunctionCall):
            return self.eval_function_call(node, env)

        elif isinstance(node, CallExpression):
            callee = self.eval_node(node.callee, env)
            try:
                return self.call_function_value(callee, node.arguments, env)
            except RuntimeError as err:
                self.runtime_error(str(err), node)

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
            try:
                if isinstance(obj, Bet):
                    return getattr(obj, node.member)
                elif isinstance(obj, Module):
                    return obj.get(node.member)
                elif isinstance(obj, dict):
                    return obj.get(node.member)
                else:
                    raise RuntimeError(f"Cannot access member '{node.member}' on {type(obj)}")
            except RuntimeError as err:
                self.runtime_error(str(err), node)

        elif isinstance(node, BetStatement):
            return self.eval_bet_statement(node, env)

        elif isinstance(node, ParlayStatement):
            return self.eval_parlay_statement(node, env)

        else:
            raise RuntimeError(f"Unknown node type: {type(node)}")

    def eval_binary_op(self, node: BinaryOp, env: Environment) -> Any:
        left = self.eval_node(node.left, env)
        right = self.eval_node(node.right, env)

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
        operand = self.eval_node(node.operand, env)

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
            if len(arg_nodes) != len(func.parameters):
                raise RuntimeError(
                    f"Function '{func.name}' expects {len(func.parameters)} arguments, got {len(arg_nodes)}"
                )

            func_env = Environment(env)
            for param, arg in zip(func.parameters, arg_nodes):
                arg_value = self.eval_node(arg, env)
                func_env.define(param, arg_value)

            try:
                result = None
                for stmt in func.body:
                    result = self.eval_node(stmt, func_env)
                return result
            except ReturnValue as ret:
                return ret.value

        raise RuntimeError("Target is not a function")

    def eval_function_call(self, node: FunctionCall, env: Environment) -> Any:
        if node.name == 'print':
            args = [self.eval_node(arg, env) for arg in node.arguments]
            print(*args)
            return None

        try:
            func = env.get(node.name)
        except RuntimeError as err:
            self.runtime_error(str(err), node)

        try:
            return self.call_function_value(func, node.arguments, env)
        except RuntimeError as err:
            if str(err) == "Target is not a function":
                self.runtime_error(f"'{node.name}' is not a function", node)
            self.runtime_error(str(err), node)

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
