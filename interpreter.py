"""
SportsBetLang Interpreter - Executes the AST with built-in betting functions
"""

import math
from typing import Any, Dict, List, Optional
from parser import *
from lexer import TokenType


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


class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        self.setup_builtins()

    def setup_builtins(self):
        """Setup built-in functions for betting operations"""

        def american_to_decimal(odds: float) -> float:
            """Convert American odds to decimal odds"""
            if odds > 0:
                return (odds / 100) + 1
            else:
                return (100 / abs(odds)) + 1

        def decimal_to_american(odds: float) -> float:
            """Convert decimal odds to American odds"""
            if odds >= 2.0:
                return (odds - 1) * 100
            else:
                return -100 / (odds - 1)

        def implied_probability(odds: float) -> float:
            """Calculate implied probability from American odds"""
            if odds > 0:
                return 100 / (odds + 100)
            else:
                return abs(odds) / (abs(odds) + 100)

        def calculate_ev(true_prob: float, odds: float, stake: float = 100) -> float:
            """Calculate expected value of a bet"""
            decimal_odds = american_to_decimal(odds)
            win_amount = stake * (decimal_odds - 1)
            loss_amount = stake
            ev = (true_prob * win_amount) - ((1 - true_prob) * loss_amount)
            return ev

        def kelly_criterion(true_prob: float, odds: float) -> float:
            """Calculate optimal bet size using Kelly Criterion"""
            decimal_odds = american_to_decimal(odds)
            b = decimal_odds - 1  # net odds received on the wager
            p = true_prob
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

        def parlay_probability(*probs) -> float:
            """Calculate probability of winning a parlay"""
            result = 1
            for p in probs:
                result *= p
            return result

        def break_even_percentage(odds: float) -> float:
            """Calculate break-even win percentage"""
            return implied_probability(odds)

        def vig_calculator(odds1: float, odds2: float) -> float:
            """Calculate bookmaker's vig (juice) from two-way market"""
            prob1 = implied_probability(odds1)
            prob2 = implied_probability(odds2)
            total = prob1 + prob2
            vig = total - 1
            return vig * 100  # Return as percentage

        def true_odds_from_vig(odds: float, total_vig: float) -> float:
            """Remove vig to get true odds"""
            implied_prob = implied_probability(odds)
            true_prob = implied_prob / (1 + total_vig)
            if true_prob >= 0.5:
                true_american = -100 * true_prob / (1 - true_prob)
            else:
                true_american = 100 * (1 - true_prob) / true_prob
            return true_american

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
            avg_payout = calculate_ev(win_rate, avg_odds, 100)
            total_staked = (wins + losses) * 100
            total_return = wins * (100 + abs(avg_payout))
            roi = ((total_return - total_staked) / total_staked) * 100
            return roi

        def round_robin(bets_count: int, parlay_size: int) -> int:
            """Calculate number of parlays in a round robin"""
            from math import comb
            return comb(bets_count, parlay_size)

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
        self.global_env.define('abs', abs)
        self.global_env.define('min', min)
        self.global_env.define('max', max)
        self.global_env.define('sqrt', math.sqrt)
        self.global_env.define('pow', pow)
        self.global_env.define('len', len)
        self.global_env.define('range', range)
        self.global_env.define('sum', sum)

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

        elif isinstance(node, TeaserStatement):
            return self.eval_teaser_statement(node, env)

        elif isinstance(node, RoundRobinStatement):
            return self.eval_round_robin_statement(node, env)

        elif isinstance(node, QuickBetStatement):
            return self.eval_quick_bet_statement(node, env)

        elif isinstance(node, IfWinStatement):
            return self.eval_if_win_statement(node, env)

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
        elif node.operator == TokenType.PLUS:
            return +operand
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

    def eval_teaser_statement(self, node: TeaserStatement, env: Environment) -> Dict[str, Any]:
        """Evaluate a teaser bet - adjusts spreads/totals in favor of bettor"""
        bets = [self.eval_node(bet_node, env) for bet_node in node.bets]
        points = self.eval_node(node.points, env)
        odds = self.eval_node(node.odds, env)
        stake = self.eval_node(node.stake, env)

        # Create adjusted bets for the teaser
        adjusted_bets = []
        for bet in bets:
            if isinstance(bet, Bet):
                # Adjust spread/total by teaser points
                if bet.spread is not None:
                    adjusted_spread = bet.spread + points if bet.spread < 0 else bet.spread - points
                    adjusted_bet = Bet(bet.bet_type, bet.team, odds, 0, spread=adjusted_spread)
                    adjusted_bets.append(adjusted_bet)
                else:
                    # For totals or moneylines, just use the teaser odds
                    adjusted_bet = Bet(bet.bet_type, bet.team, odds, 0)
                    adjusted_bets.append(adjusted_bet)

        # Calculate payout based on teaser odds
        if odds > 0:
            potential_payout = stake * (odds / 100)
        else:
            potential_payout = stake * (100 / abs(odds))

        teaser = {
            'type': 'teaser',
            'bets': adjusted_bets,
            'original_bets': bets,
            'points': points,
            'stake': stake,
            'odds': odds,
            'potential_payout': potential_payout,
            'total_return': stake + potential_payout
        }

        print(f"Teaser created: {len(bets)} legs, {points} points, ${stake:.2f} @ {odds:+d} to win ${potential_payout:.2f}")
        return teaser

    def eval_round_robin_statement(self, node: RoundRobinStatement, env: Environment) -> Dict[str, Any]:
        """Evaluate a round robin bet - creates all combinations of parlays"""
        from itertools import combinations

        bets = [self.eval_node(bet_node, env) for bet_node in node.bets]
        legs = int(self.eval_node(node.legs, env))
        stake_per = self.eval_node(node.stake_per, env)

        # Generate all combinations
        bet_combinations = list(combinations(bets, legs))

        parlays = []
        total_stake = len(bet_combinations) * stake_per
        total_potential_payout = 0

        for combo in bet_combinations:
            # Calculate parlay odds for this combination
            combined_decimal = 1
            for bet in combo:
                if isinstance(bet, Bet):
                    combined_decimal *= bet.to_decimal_odds()

            potential_payout = stake_per * (combined_decimal - 1)
            total_potential_payout += potential_payout

            parlays.append({
                'bets': combo,
                'stake': stake_per,
                'decimal_odds': combined_decimal,
                'potential_payout': potential_payout
            })

        round_robin = {
            'type': 'round_robin',
            'all_bets': bets,
            'legs': legs,
            'parlays': parlays,
            'num_parlays': len(bet_combinations),
            'stake_per_parlay': stake_per,
            'total_stake': total_stake,
            'total_potential_payout': total_potential_payout,
            'total_return': total_stake + total_potential_payout
        }

        print(f"Round Robin created: {len(bets)} picks, {legs}-leg parlays = {len(bet_combinations)} parlays")
        print(f"Total stake: ${total_stake:.2f}, Max win: ${total_potential_payout:.2f}")
        return round_robin

    def eval_quick_bet_statement(self, node: QuickBetStatement, env: Environment) -> Bet:
        """Evaluate a quick bet - shorthand for simple bets"""
        team = self.eval_node(node.team, env)
        odds = self.eval_node(node.odds, env)
        amount = self.eval_node(node.amount, env)

        if node.mode == 'to_win':
            # Calculate stake needed to win the target amount
            if odds > 0:
                stake = amount / (odds / 100)
            else:
                stake = amount / (100 / abs(odds))
            print(f"Quick bet: Risk ${stake:.2f} to win ${amount:.2f} on {team} @ {odds:+d}")
        else:  # mode == 'risk'
            stake = amount
            if odds > 0:
                payout = stake * (odds / 100)
            else:
                payout = stake * (100 / abs(odds))
            print(f"Quick bet: Risk ${stake:.2f} to win ${payout:.2f} on {team} @ {odds:+d}")

        bet = Bet('moneyline', team, odds, stake)
        return bet

    def eval_if_win_statement(self, node: IfWinStatement, env: Environment) -> Dict[str, Any]:
        """Evaluate an if-win bet - conditional betting where second bet uses payout from first"""
        first_bet = self.eval_node(node.first_bet, env)
        second_bet = self.eval_node(node.second_bet, env)

        # Calculate first bet payout
        if isinstance(first_bet, Bet):
            first_payout = first_bet.calculate_total_return()
        else:
            raise RuntimeError("First bet in if_win must be a Bet object")

        # Use first bet's total return as stake for second bet
        if isinstance(second_bet, Bet):
            # Create a new bet with the first bet's payout as stake
            second_bet_adjusted = Bet(
                second_bet.bet_type,
                second_bet.team,
                second_bet.odds,
                first_payout,
                spread=second_bet.spread
            )
            final_payout = second_bet_adjusted.calculate_payout()
        else:
            raise RuntimeError("Second bet in if_win must be a Bet object")

        if_win = {
            'type': 'if_win',
            'first_bet': first_bet,
            'second_bet': second_bet_adjusted,
            'initial_stake': first_bet.stake,
            'if_win_stake': first_payout,
            'potential_payout': final_payout,
            'total_return': first_payout + final_payout
        }

        print(f"If-Win created: ${first_bet.stake:.2f} -> ${first_payout:.2f} -> ${final_payout:.2f}")
        return if_win

    def is_truthy(self, value: Any) -> bool:
        """Determine if a value is truthy"""
        if value is None or value is False:
            return False
        if value == 0 or value == "":
            return False
        return True
