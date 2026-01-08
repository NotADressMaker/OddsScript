"""
TrackScript Interpreter - Executes the AST with built-in horse racing functions
"""

import math
import sys
import os
from typing import Any, Dict, List, Optional
from parser import *
from lexer import TokenType

# Import advanced packages
sys.path.insert(0, os.path.dirname(__file__))
from packages.breeding import get_breeding_functions
from packages.patterns import get_pattern_functions
from packages.arbitrage import get_arbitrage_functions
from packages.simulation import get_simulation_functions


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


class Wager:
    """Represents a horse racing wager"""
    def __init__(self, wager_type: str, horse: Any, odds: Any, stake: float, **kwargs):
        self.wager_type = wager_type
        self.horse = horse  # Can be single horse number or list
        self.odds = odds    # Can be track odds string like "5-2" or decimal
        self.stake = stake
        self.box = kwargs.get('box', False)
        self.wheel = kwargs.get('wheel', False)
        self.key = kwargs.get('key', None)
        self.with_horses = kwargs.get('with', None)
        self.result = None  # 'win', 'loss', 'push'

    def calculate_payout(self) -> float:
        """Calculate potential payout from track odds"""
        if isinstance(self.odds, str):
            # Parse track odds like "5-2"
            decimal_odds = self._track_odds_to_decimal(self.odds)
        else:
            decimal_odds = self.odds

        return self.stake * (decimal_odds - 1)

    def _track_odds_to_decimal(self, odds_str: str) -> float:
        """Convert track odds (e.g., '5-2') to decimal"""
        if '-' in odds_str:
            parts = odds_str.split('-')
            numerator = float(parts[0])
            denominator = float(parts[1])
            return (numerator / denominator) + 1
        return float(odds_str)

    def calculate_total_return(self) -> float:
        """Calculate total return including stake"""
        return self.stake + self.calculate_payout()

    def __repr__(self):
        horse_info = f"#{self.horse}" if isinstance(self.horse, (int, float)) else str(self.horse)
        modifier = ""
        if self.box:
            modifier = " (BOX)"
        elif self.key:
            modifier = f" (KEY {self.key} WITH {self.with_horses})"
        return f"Wager({self.wager_type}: {horse_info}{modifier} @ {self.odds}, ${self.stake:.2f})"


class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        self.setup_builtins()

    def setup_builtins(self):
        """Setup built-in functions for horse racing operations"""

        # Odds Conversion Functions
        def track_to_decimal(odds_str: str) -> float:
            """Convert track odds (e.g., '5-2', '7-5') to decimal odds"""
            if isinstance(odds_str, (int, float)):
                return float(odds_str)
            if '-' in odds_str:
                parts = odds_str.split('-')
                numerator = float(parts[0])
                denominator = float(parts[1])
                return (numerator / denominator) + 1
            return float(odds_str)

        def decimal_to_track(decimal_odds: float) -> str:
            """Convert decimal odds to track odds format"""
            numerator = decimal_odds - 1
            # Find best fractional representation
            for denom in [1, 2, 5]:
                num = numerator * denom
                if abs(num - round(num)) < 0.1:
                    return f"{int(round(num))}-{denom}"
            # Fallback to -1 denominator
            return f"{int(round((decimal_odds - 1) * 10))}-10"

        def track_to_american(odds_str: str) -> float:
            """Convert track odds to American odds"""
            decimal = track_to_decimal(odds_str)
            if decimal >= 2.0:
                return (decimal - 1) * 100
            else:
                return -100 / (decimal - 1)

        def american_to_track(american_odds: float) -> str:
            """Convert American odds to track odds"""
            if american_odds > 0:
                decimal = (american_odds / 100) + 1
            else:
                decimal = (100 / abs(american_odds)) + 1
            return decimal_to_track(decimal)

        def fractional_to_decimal(fractional_str: str) -> float:
            """Convert fractional odds to decimal (same as track_to_decimal)"""
            return track_to_decimal(fractional_str)

        # Payout Calculations
        def win_payout(odds, stake: float) -> float:
            """Calculate win bet payout"""
            if isinstance(odds, str):
                decimal_odds = track_to_decimal(odds)
            else:
                decimal_odds = odds
            return stake * decimal_odds

        def place_payout(odds, stake: float, place_ratio: float = 0.4) -> float:
            """Calculate place bet payout (typically pays 40% of win odds)"""
            if isinstance(odds, str):
                decimal_odds = track_to_decimal(odds)
            else:
                decimal_odds = odds
            place_decimal = 1 + ((decimal_odds - 1) * place_ratio)
            return stake * place_decimal

        def show_payout(odds, stake: float, show_ratio: float = 0.25) -> float:
            """Calculate show bet payout (typically pays 25% of win odds)"""
            if isinstance(odds, str):
                decimal_odds = track_to_decimal(odds)
            else:
                decimal_odds = odds
            show_decimal = 1 + ((decimal_odds - 1) * show_ratio)
            return stake * show_decimal

        def exacta_payout(odds: float, stake: float) -> float:
            """Calculate exacta payout"""
            return stake * odds

        def trifecta_payout(odds: float, stake: float) -> float:
            """Calculate trifecta payout"""
            return stake * odds

        def superfecta_payout(odds: float, stake: float) -> float:
            """Calculate superfecta payout"""
            return stake * odds

        # Track Analysis
        def calculate_takeout(pool_size: float, takeout_rate: float) -> float:
            """Calculate net pool after track takeout"""
            return pool_size * (1 - takeout_rate)

        def breakage_adjustment(payout: float, breakage: float = 0.10) -> float:
            """Apply standard track breakage rules (round down to nearest dime)"""
            return math.floor(payout / breakage) * breakage

        def odds_from_pool(horse_pool: float, total_pool: float, takeout: float = 0.17) -> float:
            """Calculate odds from pool sizes"""
            net_pool = calculate_takeout(total_pool, takeout)
            if horse_pool == 0:
                return 99.0
            odds_decimal = net_pool / horse_pool
            return odds_decimal

        # Exotic Bet Combinations
        def exacta_combinations(num_horses: int) -> int:
            """Calculate possible exacta combinations (P(n,2))"""
            if num_horses < 2:
                return 0
            return num_horses * (num_horses - 1)

        def trifecta_combinations(num_horses: int) -> int:
            """Calculate possible trifecta combinations (P(n,3))"""
            if num_horses < 3:
                return 0
            return num_horses * (num_horses - 1) * (num_horses - 2)

        def superfecta_combinations(num_horses: int) -> int:
            """Calculate possible superfecta combinations (P(n,4))"""
            if num_horses < 4:
                return 0
            return num_horses * (num_horses - 1) * (num_horses - 2) * (num_horses - 3)

        def box_cost(bet_type: str, num_horses: int, unit_stake: float) -> float:
            """Calculate cost of boxing a bet"""
            if bet_type == "exacta":
                combos = exacta_combinations(num_horses)
            elif bet_type == "trifecta":
                combos = trifecta_combinations(num_horses)
            elif bet_type == "superfecta":
                combos = superfecta_combinations(num_horses)
            else:
                combos = 1
            return combos * unit_stake

        def wheel_cost(bet_type: str, key_horses: int, other_horses: int, unit_stake: float) -> float:
            """Calculate wheel bet cost"""
            if bet_type == "exacta":
                # Key horse first, all others second + all others first, key horse second
                combos = key_horses * other_horses * 2
            elif bet_type == "trifecta":
                # More complex for trifecta wheels
                combos = key_horses * other_horses * (other_horses - 1)
            else:
                combos = key_horses * other_horses
            return combos * unit_stake

        def key_cost(bet_type: str, key_horse: int, with_horses: int, unit_stake: float) -> float:
            """Calculate key bet cost (key horse in specific position)"""
            if bet_type == "exacta":
                combos = with_horses
            elif bet_type == "trifecta":
                combos = with_horses * (with_horses - 1)
            elif bet_type == "superfecta":
                combos = with_horses * (with_horses - 1) * (with_horses - 2)
            else:
                combos = with_horses
            return combos * unit_stake

        # Handicapping Functions
        def speed_rating(time: float, track_condition: str, distance: float) -> float:
            """Calculate speed figure (simplified Beyer-style)"""
            # Base par time for 6 furlongs on fast track
            par_time = 110.0
            # Adjust for distance
            par_time = par_time * (distance / 6.0)
            # Adjust for track condition
            condition_variants = {
                "fast": 0, "good": 0.5, "muddy": 1.0, "sloppy": 1.5,
                "firm": 0, "yielding": 0.5, "soft": 1.0
            }
            variant = condition_variants.get(track_condition, 0)
            # Calculate rating (100 = par)
            rating = 100 - ((time - par_time - variant) * 5)
            return rating

        def class_rating(current_class: float, previous_class: float) -> float:
            """Analyze class change (positive = move up, negative = drop down)"""
            if previous_class == 0:
                return 0
            change_pct = ((current_class - previous_class) / previous_class) * 100
            # Convert to rating where drop in class is positive
            return -change_pct / 10

        def pace_rating(splits: list, distance: float) -> float:
            """Calculate pace figures from fractional times"""
            if not splits or len(splits) == 0:
                return 0
            # Average the split times and compare to par
            avg_split = sum(splits) / len(splits)
            par_split = 24.0 * (distance / 6.0)  # Par quarter in seconds
            rating = 100 - ((avg_split - par_split) * 10)
            return rating

        def recency_factor(days_since_last: int) -> float:
            """Calculate recency adjustment factor"""
            if days_since_last <= 7:
                return 1.0
            elif days_since_last <= 14:
                return 0.95
            elif days_since_last <= 30:
                return 0.90
            elif days_since_last <= 60:
                return 0.80
            else:
                return 0.70

        def jockey_trainer_combo(jockey_win_pct: float, trainer_win_pct: float) -> float:
            """Calculate combined jockey/trainer statistics"""
            # Weighted average with bonus for strong combo
            combined = (jockey_win_pct * 0.6 + trainer_win_pct * 0.4)
            if jockey_win_pct > 0.20 and trainer_win_pct > 0.20:
                combined *= 1.1  # 10% bonus for strong combo
            return combined

        def track_bias_adjustment(post_position: int, bias_factor: float) -> float:
            """Post position adjustment based on track bias"""
            # Negative bias favors inside, positive favors outside
            return bias_factor * (post_position - 6)

        # Wagering Strategy
        def kelly_racing(true_prob: float, track_odds_str: str, bankroll: float) -> float:
            """Kelly criterion for horse racing"""
            decimal_odds = track_to_decimal(track_odds_str)
            b = decimal_odds - 1
            p = true_prob
            q = 1 - p
            if b <= 0:
                return 0
            kelly = (b * p - q) / b
            return max(0, min(kelly, 0.25))  # Cap at 25% for safety

        def dutching(horses_data: list, total_stake: float) -> list:
            """Calculate dutching stakes for multiple horses"""
            # horses_data should be list of dicts with 'odds' key
            stakes = []
            total_prob = 0

            for horse in horses_data:
                if isinstance(horse, dict) and 'odds' in horse:
                    odds = horse['odds']
                    if isinstance(odds, str):
                        decimal = track_to_decimal(odds)
                    else:
                        decimal = odds
                    prob = 1 / decimal
                    total_prob += prob

            for horse in horses_data:
                if isinstance(horse, dict) and 'odds' in horse:
                    odds = horse['odds']
                    if isinstance(odds, str):
                        decimal = track_to_decimal(odds)
                    else:
                        decimal = odds
                    prob = 1 / decimal
                    stake = (prob / total_prob) * total_stake
                    stakes.append({"horse": horse.get('number', '?'), "amount": stake})

            return stakes

        def calculate_roi(wins: int, total_bets: int, avg_payout: float, avg_stake: float) -> float:
            """Calculate ROI from betting record"""
            if total_bets == 0:
                return 0
            total_staked = total_bets * avg_stake
            total_returned = wins * avg_payout
            roi = ((total_returned - total_staked) / total_staked) * 100
            return roi

        def overlay_percentage(true_odds_str: str, morning_line_str: str) -> float:
            """Calculate overlay/underlay percentage"""
            true_decimal = track_to_decimal(true_odds_str)
            ml_decimal = track_to_decimal(morning_line_str)
            true_prob = 1 / true_decimal
            ml_prob = 1 / ml_decimal
            overlay = ((ml_prob - true_prob) / true_prob) * 100
            return overlay

        def calculate_odds_value(estimated_odds_str: str, actual_odds_str: str) -> float:
            """Calculate value of a bet (positive = good value)"""
            est_decimal = track_to_decimal(estimated_odds_str)
            actual_decimal = track_to_decimal(actual_odds_str)
            value = actual_decimal - est_decimal
            return value

        # Register all built-in functions
        self.global_env.define('track_to_decimal', track_to_decimal)
        self.global_env.define('decimal_to_track', decimal_to_track)
        self.global_env.define('track_to_american', track_to_american)
        self.global_env.define('american_to_track', american_to_track)
        self.global_env.define('fractional_to_decimal', fractional_to_decimal)

        self.global_env.define('win_payout', win_payout)
        self.global_env.define('place_payout', place_payout)
        self.global_env.define('show_payout', show_payout)
        self.global_env.define('exacta_payout', exacta_payout)
        self.global_env.define('trifecta_payout', trifecta_payout)
        self.global_env.define('superfecta_payout', superfecta_payout)

        self.global_env.define('calculate_takeout', calculate_takeout)
        self.global_env.define('breakage_adjustment', breakage_adjustment)
        self.global_env.define('odds_from_pool', odds_from_pool)

        self.global_env.define('exacta_combinations', exacta_combinations)
        self.global_env.define('trifecta_combinations', trifecta_combinations)
        self.global_env.define('superfecta_combinations', superfecta_combinations)
        self.global_env.define('box_cost', box_cost)
        self.global_env.define('wheel_cost', wheel_cost)
        self.global_env.define('key_cost', key_cost)

        self.global_env.define('speed_rating', speed_rating)
        self.global_env.define('class_rating', class_rating)
        self.global_env.define('pace_rating', pace_rating)
        self.global_env.define('recency_factor', recency_factor)
        self.global_env.define('jockey_trainer_combo', jockey_trainer_combo)
        self.global_env.define('track_bias_adjustment', track_bias_adjustment)

        self.global_env.define('kelly_racing', kelly_racing)
        self.global_env.define('dutching', dutching)
        self.global_env.define('calculate_roi', calculate_roi)
        self.global_env.define('overlay_percentage', overlay_percentage)
        self.global_env.define('calculate_odds_value', calculate_odds_value)

        # Standard utility functions
        self.global_env.define('abs', abs)
        self.global_env.define('min', min)
        self.global_env.define('max', max)
        self.global_env.define('sqrt', math.sqrt)
        self.global_env.define('pow', pow)
        self.global_env.define('round', round)
        self.global_env.define('len', len)
        self.global_env.define('range', range)
        self.global_env.define('sum', sum)
        self.global_env.define('sort', sorted)

        # Load advanced packages
        self._load_advanced_packages()

    def _load_advanced_packages(self):
        """Load all advanced TrackScript packages"""
        # Breeding & Pedigree Analysis
        breeding_funcs = get_breeding_functions()
        for name, func in breeding_funcs.items():
            self.global_env.define(name, func)

        # Pattern Recognition
        pattern_funcs = get_pattern_functions()
        for name, func in pattern_funcs.items():
            self.global_env.define(name, func)

        # Arbitrage & Value Finding
        arbitrage_funcs = get_arbitrage_functions()
        for name, func in arbitrage_funcs.items():
            self.global_env.define(name, func)

        # Race Simulation & Probability
        simulation_funcs = get_simulation_functions()
        for name, func in simulation_funcs.items():
            self.global_env.define(name, func)

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
            return env.get(node.name)

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
            if isinstance(obj, Wager):
                return getattr(obj, node.member)
            elif isinstance(obj, dict):
                return obj.get(node.member)
            else:
                raise RuntimeError(f"Cannot access member '{node.member}' on {type(obj)}")

        elif isinstance(node, WagerStatement):
            return self.eval_wager_statement(node, env)

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

    def eval_wager_statement(self, node: WagerStatement, env: Environment) -> Wager:
        """Evaluate a horse racing wager statement"""
        horse = self.eval_node(node.horse, env) if node.horse else 1
        odds = self.eval_node(node.odds, env) if node.odds else "5-2"
        stake = self.eval_node(node.stake, env) if node.stake else 20

        kwargs = {}
        for key, value_node in node.additional_params.items():
            kwargs[key] = self.eval_node(value_node, env)

        wager = Wager(node.wager_type, horse, odds, stake, **kwargs)
        print(f"Created: {wager}")
        return wager

    def is_truthy(self, value: Any) -> bool:
        """Determine if a value is truthy"""
        if value is None or value is False:
            return False
        if value == 0 or value == "":
            return False
        return True
