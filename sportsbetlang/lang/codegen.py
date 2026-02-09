"""
SportsBetLang Code Generator - Emits Python, R, or Julia code from AST.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from sportsbetlang.lang.lexer import Lexer, TokenType
from sportsbetlang.lang.parser import (
    ArrayLiteral,
    Assignment,
    ASTNode,
    BetStatement,
    BinaryOp,
    BooleanLiteral,
    DictLiteral,
    ForLoop,
    FunctionCall,
    FunctionDef,
    Identifier,
    IfStatement,
    IndexAccess,
    MemberAccess,
    NumberLiteral,
    ParlayStatement,
    Program,
    ReturnStatement,
    StringLiteral,
    UnaryOp,
    WhileLoop,
    Parser,
)


SUPPORTED_LANGUAGES = {"python", "r", "julia"}


@dataclass
class GeneratedCode:
    language: str
    source: str


class CodeGenerator:
    """Generate target language code from a SportsBetLang AST."""

    def __init__(self, language: str = "python", include_prelude: bool = True) -> None:
        if language not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language '{language}'. Choose from {sorted(SUPPORTED_LANGUAGES)}")
        self.language = language
        self.include_prelude = include_prelude
        self._helpers: Set[str] = set()
        self._needs_math = False
        self._needs_range_helper = False
        self._needs_index_helper = False

    def generate(self, program: Program) -> GeneratedCode:
        self._helpers.clear()
        self._needs_math = False
        self._needs_range_helper = False
        self._needs_index_helper = False
        self._collect_helpers(program)
        body = self._render_program(program)
        prelude = self._render_prelude() if self.include_prelude else ""
        source = "".join([prelude, body])
        return GeneratedCode(language=self.language, source=source)

    def generate_from_source(self, source: str) -> GeneratedCode:
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        program = Parser(tokens, source).parse()
        return self.generate(program)

    def _collect_helpers(self, node: ASTNode) -> None:
        if isinstance(node, Program):
            for stmt in node.statements:
                self._collect_helpers(stmt)
        elif isinstance(node, FunctionCall):
            name = node.name
            if name in {
                "american_to_decimal",
                "decimal_to_american",
                "implied_probability",
                "calculate_ev",
                "kelly_criterion",
                "parlay_odds",
                "parlay_probability",
                "break_even_percentage",
                "vig_calculator",
                "true_odds_from_vig",
                "units_to_risk",
                "roi_calculator",
                "round_robin",
                "arbitrage_stakes",
                "hedge_stake",
            }:
                self._helpers.add(name)
                if name == "round_robin" and self.language == "python":
                    self._needs_math = True
            elif name == "range" and self.language != "python":
                self._needs_range_helper = True
            elif name == "sqrt" and self.language == "python":
                self._needs_math = True
            for arg in node.arguments:
                self._collect_helpers(arg)
        elif isinstance(node, BetStatement):
            self._helpers.add("sbl_create_bet")
            self._helpers.add("american_to_decimal")
            for value in [node.team, node.odds, node.stake]:
                if value is not None:
                    self._collect_helpers(value)
            for value in node.additional_params.values():
                self._collect_helpers(value)
        elif isinstance(node, ParlayStatement):
            self._helpers.add("sbl_create_parlay")
            self._helpers.add("american_to_decimal")
            self._helpers.add("decimal_to_american")
            for bet in node.bets:
                self._collect_helpers(bet)
            if node.stake is not None:
                self._collect_helpers(node.stake)
        elif isinstance(node, (Assignment, ReturnStatement, UnaryOp, BinaryOp, IndexAccess, MemberAccess)):
            for child in self._iter_children(node):
                self._collect_helpers(child)
        elif isinstance(node, (IfStatement, WhileLoop, ForLoop, FunctionDef)):
            for child in self._iter_children(node):
                self._collect_helpers(child)
        elif isinstance(node, (ArrayLiteral, DictLiteral)):
            for child in self._iter_children(node):
                self._collect_helpers(child)
        elif isinstance(node, (NumberLiteral, StringLiteral, BooleanLiteral, Identifier)):
            return

        if isinstance(node, IndexAccess) and self.language in {"r", "julia"}:
            self._needs_index_helper = True

    def _iter_children(self, node: ASTNode) -> List[ASTNode]:
        if isinstance(node, Assignment):
            return [node.value]
        if isinstance(node, ReturnStatement):
            return [node.value] if node.value is not None else []
        if isinstance(node, UnaryOp):
            return [node.operand]
        if isinstance(node, BinaryOp):
            return [node.left, node.right]
        if isinstance(node, IndexAccess):
            return [node.object, node.index]
        if isinstance(node, MemberAccess):
            return [node.object]
        if isinstance(node, IfStatement):
            nodes = [node.condition]
            nodes.extend(node.then_block)
            if node.else_block:
                nodes.extend(node.else_block)
            return nodes
        if isinstance(node, WhileLoop):
            nodes = [node.condition]
            nodes.extend(node.body)
            return nodes
        if isinstance(node, ForLoop):
            nodes = [node.iterable]
            nodes.extend(node.body)
            return nodes
        if isinstance(node, FunctionDef):
            return node.body
        if isinstance(node, ArrayLiteral):
            return node.elements
        if isinstance(node, DictLiteral):
            children: List[ASTNode] = []
            for key, value in node.pairs:
                children.append(key)
                children.append(value)
            return children
        return []

    def _render_program(self, program: Program) -> str:
        lines: List[str] = []
        for stmt in program.statements:
            lines.extend(self._render_statement(stmt, indent=0))
        return "\n".join(lines) + ("\n" if lines else "")

    def _render_statement(self, node: ASTNode, indent: int) -> List[str]:
        ind = self._indent(indent)
        if isinstance(node, Assignment):
            value = self._render_expression(node.value)
            if self.language == "r":
                return [f"{ind}{node.name} <- {value}"]
            return [f"{ind}{node.name} = {value}"]
        if isinstance(node, FunctionDef):
            return self._render_function_def(node, indent)
        if isinstance(node, IfStatement):
            return self._render_if(node, indent)
        if isinstance(node, WhileLoop):
            return self._render_while(node, indent)
        if isinstance(node, ForLoop):
            return self._render_for(node, indent)
        if isinstance(node, ReturnStatement):
            if node.value is None:
                return [f"{ind}return" if self.language != "r" else f"{ind}return()"]
            value = self._render_expression(node.value)
            if self.language == "r":
                return [f"{ind}return({value})"]
            return [f"{ind}return {value}"]
        if isinstance(node, BetStatement):
            return [f"{ind}{self._render_bet_statement(node)}"]
        if isinstance(node, ParlayStatement):
            return [f"{ind}{self._render_parlay_statement(node)}"]
        return [f"{ind}{self._render_expression(node)}"]

    def _render_function_def(self, node: FunctionDef, indent: int) -> List[str]:
        ind = self._indent(indent)
        params = ", ".join(node.parameters)
        lines: List[str] = []
        if self.language == "python":
            lines.append(f"{ind}def {node.name}({params}):")
            if not node.body:
                lines.append(f"{self._indent(indent + 1)}pass")
            else:
                for stmt in node.body:
                    lines.extend(self._render_statement(stmt, indent + 1))
        elif self.language == "r":
            lines.append(f"{ind}{node.name} <- function({params}) {{")
            if not node.body:
                lines.append(f"{self._indent(indent + 1)}NULL")
            else:
                for stmt in node.body:
                    lines.extend(self._render_statement(stmt, indent + 1))
            lines.append(f"{ind}}}")
        else:
            lines.append(f"{ind}function {node.name}({params})")
            if not node.body:
                lines.append(f"{self._indent(indent + 1)}nothing")
            else:
                for stmt in node.body:
                    lines.extend(self._render_statement(stmt, indent + 1))
            lines.append(f"{ind}end")
        return lines

    def _render_if(self, node: IfStatement, indent: int) -> List[str]:
        ind = self._indent(indent)
        cond = self._render_expression(node.condition)
        lines: List[str] = []
        if self.language == "python":
            lines.append(f"{ind}if {cond}:")
            lines.extend(self._render_block(node.then_block, indent + 1, "pass"))
            if node.else_block is not None:
                lines.append(f"{ind}else:")
                lines.extend(self._render_block(node.else_block, indent + 1, "pass"))
        elif self.language == "r":
            lines.append(f"{ind}if ({cond}) {{")
            lines.extend(self._render_block(node.then_block, indent + 1, "NULL"))
            if node.else_block is not None:
                lines.append(f"{ind}}} else {{")
                lines.extend(self._render_block(node.else_block, indent + 1, "NULL"))
            lines.append(f"{ind}}}")
        else:
            lines.append(f"{ind}if {cond}")
            lines.extend(self._render_block(node.then_block, indent + 1, "nothing"))
            if node.else_block is not None:
                lines.append(f"{ind}else")
                lines.extend(self._render_block(node.else_block, indent + 1, "nothing"))
            lines.append(f"{ind}end")
        return lines

    def _render_while(self, node: WhileLoop, indent: int) -> List[str]:
        ind = self._indent(indent)
        cond = self._render_expression(node.condition)
        lines: List[str] = []
        if self.language == "python":
            lines.append(f"{ind}while {cond}:")
            lines.extend(self._render_block(node.body, indent + 1, "pass"))
        elif self.language == "r":
            lines.append(f"{ind}while ({cond}) {{")
            lines.extend(self._render_block(node.body, indent + 1, "NULL"))
            lines.append(f"{ind}}}")
        else:
            lines.append(f"{ind}while {cond}")
            lines.extend(self._render_block(node.body, indent + 1, "nothing"))
            lines.append(f"{ind}end")
        return lines

    def _render_for(self, node: ForLoop, indent: int) -> List[str]:
        ind = self._indent(indent)
        iterable = self._render_expression(node.iterable)
        lines: List[str] = []
        if self.language == "python":
            lines.append(f"{ind}for {node.variable} in {iterable}:")
            lines.extend(self._render_block(node.body, indent + 1, "pass"))
        elif self.language == "r":
            lines.append(f"{ind}for ({node.variable} in {iterable}) {{")
            lines.extend(self._render_block(node.body, indent + 1, "NULL"))
            lines.append(f"{ind}}}")
        else:
            lines.append(f"{ind}for {node.variable} in {iterable}")
            lines.extend(self._render_block(node.body, indent + 1, "nothing"))
            lines.append(f"{ind}end")
        return lines

    def _render_block(self, statements: List[ASTNode], indent: int, fallback: str) -> List[str]:
        if not statements:
            return [f"{self._indent(indent)}{fallback}"]
        lines: List[str] = []
        for stmt in statements:
            lines.extend(self._render_statement(stmt, indent))
        return lines

    def _render_expression(self, node: ASTNode) -> str:
        if isinstance(node, NumberLiteral):
            return str(node.value)
        if isinstance(node, StringLiteral):
            return self._string_literal(node.value)
        if isinstance(node, BooleanLiteral):
            return self._boolean_literal(node.value)
        if isinstance(node, Identifier):
            return node.name
        if isinstance(node, ArrayLiteral):
            elems = ", ".join(self._render_expression(elem) for elem in node.elements)
            if self.language == "r":
                return f"c({elems})"
            return f"[{elems}]"
        if isinstance(node, DictLiteral):
            return self._render_dict(node)
        if isinstance(node, BinaryOp):
            left = self._render_expression(node.left)
            right = self._render_expression(node.right)
            op = self._binary_operator(node.operator)
            return f"({left} {op} {right})"
        if isinstance(node, UnaryOp):
            operand = self._render_expression(node.operand)
            op = self._unary_operator(node.operator)
            if op == "not" and self.language == "python":
                return f"(not {operand})"
            return f"({op}{operand})"
        if isinstance(node, FunctionCall):
            return self._render_function_call(node)
        if isinstance(node, IndexAccess):
            obj = self._render_expression(node.object)
            index = self._render_expression(node.index)
            if self.language == "python":
                return f"{obj}[{index}]"
            return f"sbl_index({obj}, {index})"
        if isinstance(node, MemberAccess):
            obj = self._render_expression(node.object)
            if self.language == "r":
                return f"{obj}${node.member}"
            return f"{obj}.{node.member}"
        if isinstance(node, BetStatement):
            return self._render_bet_statement(node)
        if isinstance(node, ParlayStatement):
            return self._render_parlay_statement(node)
        raise RuntimeError(f"Unsupported node type: {type(node)}")

    def _render_function_call(self, node: FunctionCall) -> str:
        name = node.name
        args = [self._render_expression(arg) for arg in node.arguments]
        if name == "print":
            return self._render_print(args)
        if name == "len" and self.language != "python":
            mapped = "length"
            return f"{mapped}({', '.join(args)})"
        if name == "sqrt" and self.language == "python":
            self._needs_math = True
            return f"math.sqrt({', '.join(args)})"
        if name == "sqrt" and self.language == "r":
            return f"sqrt({', '.join(args)})"
        if name == "sqrt" and self.language == "julia":
            return f"sqrt({', '.join(args)})"
        if name == "pow" and self.language in {"r", "julia"}:
            return f"^({', '.join(args)})"
        if name == "range" and self.language != "python":
            return f"sbl_range({', '.join(args)})"
        return f"{name}({', '.join(args)})"

    def _render_print(self, args: List[str]) -> str:
        if self.language == "julia":
            return f"println({', '.join(args)})"
        return f"print({', '.join(args)})"

    def _boolean_literal(self, value: bool) -> str:
        if self.language == "python":
            return "True" if value else "False"
        if self.language == "r":
            return "TRUE" if value else "FALSE"
        return "true" if value else "false"

    def _render_dict(self, node: DictLiteral) -> str:
        if self.language == "python":
            pairs = ", ".join(
                f"{self._render_expression(key)}: {self._render_expression(value)}"
                for key, value in node.pairs
            )
            return f"{{{pairs}}}"
        if self.language == "r":
            values = ", ".join(self._render_expression(value) for _, value in node.pairs)
            keys = ", ".join(self._render_expression(key) for key, _ in node.pairs)
            return f"setNames(list({values}), c({keys}))"
        pairs = ", ".join(
            f"{self._render_expression(key)} => {self._render_expression(value)}"
            for key, value in node.pairs
        )
        return f"Dict({pairs})"

    def _render_bet_statement(self, node: BetStatement) -> str:
        team = self._render_expression(node.team)
        odds = self._render_expression(node.odds) if node.odds is not None else None
        stake = self._render_expression(node.stake) if node.stake is not None else None
        spread = None
        if "spread" in node.additional_params:
            spread = self._render_expression(node.additional_params["spread"])

        args = [self._string_literal(node.bet_type), team]
        kwargs: List[str] = []
        if odds is not None:
            kwargs.append(self._render_kwarg("odds", odds))
        if stake is not None:
            kwargs.append(self._render_kwarg("stake", stake))
        if spread is not None:
            kwargs.append(self._render_kwarg("spread", spread))

        if self.language == "julia" and kwargs:
            return f"sbl_create_bet({', '.join(args)}; {', '.join(kwargs)})"
        all_args = ", ".join(args + kwargs)
        return f"sbl_create_bet({all_args})"

    def _render_parlay_statement(self, node: ParlayStatement) -> str:
        bets = ", ".join(self._render_expression(bet) for bet in node.bets)
        stake = self._render_expression(node.stake) if node.stake is not None else None
        args = [f"[{bets}]"] if self.language != "r" else [f"list({bets})"]
        kwargs: List[str] = []
        if stake is not None:
            kwargs.append(self._render_kwarg("stake", stake))
        if self.language == "julia" and kwargs:
            return f"sbl_create_parlay({', '.join(args)}; {', '.join(kwargs)})"
        all_args = ", ".join(args + kwargs)
        return f"sbl_create_parlay({all_args})"

    def _render_kwarg(self, name: str, value: str) -> str:
        if self.language == "r":
            return f"{name} = {value}"
        if self.language == "python":
            return f"{name}={value}"
        return f"{name} = {value}"

    def _indent(self, level: int) -> str:
        return "    " * level

    def _string_literal(self, value: str) -> str:
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f"\"{escaped}\""

    def _binary_operator(self, operator: TokenType) -> str:
        mapping = {
            TokenType.PLUS: "+",
            TokenType.MINUS: "-",
            TokenType.MULTIPLY: "*",
            TokenType.DIVIDE: "/",
            TokenType.MODULO: "%%" if self.language == "r" else "%",
            TokenType.EQUAL: "==",
            TokenType.NOT_EQUAL: "!=",
            TokenType.LESS_THAN: "<",
            TokenType.GREATER_THAN: ">",
            TokenType.LESS_EQUAL: "<=",
            TokenType.GREATER_EQUAL: ">=",
            TokenType.AND: "and" if self.language == "python" else "&&",
            TokenType.OR: "or" if self.language == "python" else "||",
        }
        return mapping[operator]

    def _unary_operator(self, operator: TokenType) -> str:
        mapping = {
            TokenType.MINUS: "-",
            TokenType.NOT: "not " if self.language == "python" else "!",
        }
        return mapping[operator]

    def _render_prelude(self) -> str:
        lines: List[str] = []
        if self.language == "python" and self._needs_math:
            lines.append("import math")
            lines.append("")
        if self.language == "python":
            lines.extend(self._python_helpers())
        elif self.language == "r":
            lines.extend(self._r_helpers())
        else:
            lines.extend(self._julia_helpers())
        if lines:
            return "\n".join(lines) + "\n"
        return ""

    def _python_helpers(self) -> List[str]:
        helpers: List[str] = []
        helper_map: Dict[str, List[str]] = {}

        helper_map["american_to_decimal"] = [
            "def american_to_decimal(odds):",
            "    if odds > 0:",
            "        return (odds / 100) + 1",
            "    return (100 / abs(odds)) + 1",
            "",
        ]
        helper_map["decimal_to_american"] = [
            "def decimal_to_american(odds):",
            "    if odds >= 2.0:",
            "        return (odds - 1) * 100",
            "    return -100 / (odds - 1)",
            "",
        ]
        helper_map["implied_probability"] = [
            "def implied_probability(odds):",
            "    if odds > 0:",
            "        return 100 / (odds + 100)",
            "    return abs(odds) / (abs(odds) + 100)",
            "",
        ]
        helper_map["calculate_ev"] = [
            "def calculate_ev(true_prob, odds, stake=100):",
            "    decimal_odds = american_to_decimal(odds)",
            "    win_amount = stake * (decimal_odds - 1)",
            "    loss_amount = stake",
            "    return (true_prob * win_amount) - ((1 - true_prob) * loss_amount)",
            "",
        ]
        helper_map["kelly_criterion"] = [
            "def kelly_criterion(true_prob, odds):",
            "    decimal_odds = american_to_decimal(odds)",
            "    b = decimal_odds - 1",
            "    p = true_prob",
            "    q = 1 - p",
            "    kelly = (b * p - q) / b",
            "    return max(0, kelly)",
            "",
        ]
        helper_map["parlay_odds"] = [
            "def parlay_odds(*odds_list):",
            "    decimal_odds = [american_to_decimal(o) for o in odds_list]",
            "    combined = 1",
            "    for odd in decimal_odds:",
            "        combined *= odd",
            "    return decimal_to_american(combined)",
            "",
        ]
        helper_map["parlay_probability"] = [
            "def parlay_probability(*probs):",
            "    result = 1",
            "    for p in probs:",
            "        result *= p",
            "    return result",
            "",
        ]
        helper_map["break_even_percentage"] = [
            "def break_even_percentage(odds):",
            "    return implied_probability(odds)",
            "",
        ]
        helper_map["vig_calculator"] = [
            "def vig_calculator(odds1, odds2):",
            "    prob1 = implied_probability(odds1)",
            "    prob2 = implied_probability(odds2)",
            "    total = prob1 + prob2",
            "    vig = total - 1",
            "    return vig * 100",
            "",
        ]
        helper_map["true_odds_from_vig"] = [
            "def true_odds_from_vig(odds, total_vig):",
            "    implied_prob = implied_probability(odds)",
            "    true_prob = implied_prob / (1 + total_vig)",
            "    if true_prob >= 0.5:",
            "        return -100 * true_prob / (1 - true_prob)",
            "    return 100 * (1 - true_prob) / true_prob",
            "",
        ]
        helper_map["units_to_risk"] = [
            "def units_to_risk(odds, units_to_win=1):",
            "    if odds > 0:",
            "        return units_to_win * (100 / odds)",
            "    return units_to_win * (abs(odds) / 100)",
            "",
        ]
        helper_map["roi_calculator"] = [
            "def roi_calculator(wins, losses, avg_odds):",
            "    if wins + losses == 0:",
            "        return 0",
            "    win_rate = wins / (wins + losses)",
            "    avg_payout = calculate_ev(win_rate, avg_odds, 100)",
            "    total_staked = (wins + losses) * 100",
            "    total_return = wins * (100 + abs(avg_payout))",
            "    return ((total_return - total_staked) / total_staked) * 100",
            "",
        ]
        helper_map["round_robin"] = [
            "def round_robin(bets_count, parlay_size):",
            "    return math.comb(bets_count, parlay_size)",
            "",
        ]
        helper_map["arbitrage_stakes"] = [
            "def arbitrage_stakes(odds1, odds2, total_stake=100):",
            "    decimal1 = american_to_decimal(odds1)",
            "    decimal2 = american_to_decimal(odds2)",
            "    implied1 = 1 / decimal1",
            "    implied2 = 1 / decimal2",
            "    total_implied = implied1 + implied2",
            "    stake1 = total_stake * (implied1 / total_implied)",
            "    stake2 = total_stake * (implied2 / total_implied)",
            "    payout1 = stake1 * decimal1",
            "    payout2 = stake2 * decimal2",
            "    profit = min(payout1, payout2) - total_stake",
            "    return {",
            "        'odds1': odds1,",
            "        'odds2': odds2,",
            "        'stake_total': total_stake,",
            "        'stake1': stake1,",
            "        'stake2': stake2,",
            "        'total_implied': total_implied,",
            "        'arb_margin_pct': (1 - total_implied) * 100,",
            "        'profit': profit,",
            "        'roi_pct': (profit / total_stake) * 100,",
            "    }",
            "",
        ]
        helper_map["hedge_stake"] = [
            "def hedge_stake(odds, stake, hedge_odds):",
            "    decimal_main = american_to_decimal(odds)",
            "    decimal_hedge = american_to_decimal(hedge_odds)",
            "    hedge_amount = stake * (decimal_main - 1) / (decimal_hedge - 1)",
            "    total_stake = stake + hedge_amount",
            "    profit_main = (stake * decimal_main) - total_stake",
            "    profit_hedge = (hedge_amount * decimal_hedge) - total_stake",
            "    return {",
            "        'original_odds': odds,",
            "        'original_stake': stake,",
            "        'hedge_odds': hedge_odds,",
            "        'hedge_stake': hedge_amount,",
            "        'total_stake': total_stake,",
            "        'profit_if_original_wins': profit_main,",
            "        'profit_if_hedge_wins': profit_hedge,",
            "        'locked_profit': min(profit_main, profit_hedge),",
            "    }",
            "",
        ]
        helper_map["sbl_create_bet"] = [
            "def sbl_create_bet(bet_type, team, odds=-110, stake=100, spread=None):",
            "    bet = {'bet_type': bet_type, 'team': team, 'odds': odds, 'stake': stake}",
            "    if spread is not None:",
            "        bet['spread'] = spread",
            "    return bet",
            "",
        ]
        helper_map["sbl_create_parlay"] = [
            "def sbl_create_parlay(bets, stake=100):",
            "    combined_decimal = 1",
            "    for bet in bets:",
            "        combined_decimal *= american_to_decimal(bet.get('odds', -110))",
            "    if combined_decimal >= 2.0:",
            "        combined_american = (combined_decimal - 1) * 100",
            "    else:",
            "        combined_american = -100 / (combined_decimal - 1)",
            "    potential_payout = stake * (combined_decimal - 1)",
            "    return {",
            "        'bets': bets,",
            "        'stake': stake,",
            "        'combined_odds': combined_american,",
            "        'decimal_odds': combined_decimal,",
            "        'potential_payout': potential_payout,",
            "        'total_return': stake + potential_payout,",
            "    }",
            "",
        ]

        if self._needs_range_helper:
            helper_map["sbl_range"] = [
                "def sbl_range(start, stop=None, step=1):",
                "    if stop is None:",
                "        stop = start",
                "        start = 0",
                "    if step == 0:",
                "        raise ValueError('step cannot be 0')",
                "    if (step > 0 and start >= stop) or (step < 0 and start <= stop):",
                "        return []",
                "    return list(range(start, stop, step))",
                "",
            ]
        if self._needs_index_helper:
            helper_map["sbl_index"] = [
                "def sbl_index(obj, idx):",
                "    return obj[idx]",
                "",
            ]

        for helper in sorted(self._helpers):
            helpers.extend(helper_map.get(helper, []))
        if self._needs_range_helper:
            helpers.extend(helper_map["sbl_range"])
        if self._needs_index_helper:
            helpers.extend(helper_map["sbl_index"])
        return helpers

    def _r_helpers(self) -> List[str]:
        helpers: List[str] = []
        helper_map: Dict[str, List[str]] = {}

        helper_map["american_to_decimal"] = [
            "american_to_decimal <- function(odds) {",
            "    if (odds > 0) {",
            "        return((odds / 100) + 1)",
            "    }",
            "    return((100 / abs(odds)) + 1)",
            "}",
            "",
        ]
        helper_map["decimal_to_american"] = [
            "decimal_to_american <- function(odds) {",
            "    if (odds >= 2.0) {",
            "        return((odds - 1) * 100)",
            "    }",
            "    return(-100 / (odds - 1))",
            "}",
            "",
        ]
        helper_map["implied_probability"] = [
            "implied_probability <- function(odds) {",
            "    if (odds > 0) {",
            "        return(100 / (odds + 100))",
            "    }",
            "    return(abs(odds) / (abs(odds) + 100))",
            "}",
            "",
        ]
        helper_map["calculate_ev"] = [
            "calculate_ev <- function(true_prob, odds, stake=100) {",
            "    decimal_odds <- american_to_decimal(odds)",
            "    win_amount <- stake * (decimal_odds - 1)",
            "    loss_amount <- stake",
            "    return((true_prob * win_amount) - ((1 - true_prob) * loss_amount))",
            "}",
            "",
        ]
        helper_map["kelly_criterion"] = [
            "kelly_criterion <- function(true_prob, odds) {",
            "    decimal_odds <- american_to_decimal(odds)",
            "    b <- decimal_odds - 1",
            "    p <- true_prob",
            "    q <- 1 - p",
            "    kelly <- (b * p - q) / b",
            "    return(max(0, kelly))",
            "}",
            "",
        ]
        helper_map["parlay_odds"] = [
            "parlay_odds <- function(...) {",
            "    odds_list <- list(...)",
            "    decimal_odds <- sapply(odds_list, american_to_decimal)",
            "    combined <- prod(decimal_odds)",
            "    return(decimal_to_american(combined))",
            "}",
            "",
        ]
        helper_map["parlay_probability"] = [
            "parlay_probability <- function(...) {",
            "    probs <- unlist(list(...))",
            "    return(prod(probs))",
            "}",
            "",
        ]
        helper_map["break_even_percentage"] = [
            "break_even_percentage <- function(odds) {",
            "    return(implied_probability(odds))",
            "}",
            "",
        ]
        helper_map["vig_calculator"] = [
            "vig_calculator <- function(odds1, odds2) {",
            "    prob1 <- implied_probability(odds1)",
            "    prob2 <- implied_probability(odds2)",
            "    total <- prob1 + prob2",
            "    vig <- total - 1",
            "    return(vig * 100)",
            "}",
            "",
        ]
        helper_map["true_odds_from_vig"] = [
            "true_odds_from_vig <- function(odds, total_vig) {",
            "    implied_prob <- implied_probability(odds)",
            "    true_prob <- implied_prob / (1 + total_vig)",
            "    if (true_prob >= 0.5) {",
            "        return(-100 * true_prob / (1 - true_prob))",
            "    }",
            "    return(100 * (1 - true_prob) / true_prob)",
            "}",
            "",
        ]
        helper_map["units_to_risk"] = [
            "units_to_risk <- function(odds, units_to_win=1) {",
            "    if (odds > 0) {",
            "        return(units_to_win * (100 / odds))",
            "    }",
            "    return(units_to_win * (abs(odds) / 100))",
            "}",
            "",
        ]
        helper_map["roi_calculator"] = [
            "roi_calculator <- function(wins, losses, avg_odds) {",
            "    if (wins + losses == 0) {",
            "        return(0)",
            "    }",
            "    win_rate <- wins / (wins + losses)",
            "    avg_payout <- calculate_ev(win_rate, avg_odds, 100)",
            "    total_staked <- (wins + losses) * 100",
            "    total_return <- wins * (100 + abs(avg_payout))",
            "    return(((total_return - total_staked) / total_staked) * 100)",
            "}",
            "",
        ]
        helper_map["round_robin"] = [
            "round_robin <- function(bets_count, parlay_size) {",
            "    return(choose(bets_count, parlay_size))",
            "}",
            "",
        ]
        helper_map["arbitrage_stakes"] = [
            "arbitrage_stakes <- function(odds1, odds2, total_stake=100) {",
            "    decimal1 <- american_to_decimal(odds1)",
            "    decimal2 <- american_to_decimal(odds2)",
            "    implied1 <- 1 / decimal1",
            "    implied2 <- 1 / decimal2",
            "    total_implied <- implied1 + implied2",
            "    stake1 <- total_stake * (implied1 / total_implied)",
            "    stake2 <- total_stake * (implied2 / total_implied)",
            "    payout1 <- stake1 * decimal1",
            "    payout2 <- stake2 * decimal2",
            "    profit <- min(payout1, payout2) - total_stake",
            "    return(list(",
            "        odds1 = odds1,",
            "        odds2 = odds2,",
            "        stake_total = total_stake,",
            "        stake1 = stake1,",
            "        stake2 = stake2,",
            "        total_implied = total_implied,",
            "        arb_margin_pct = (1 - total_implied) * 100,",
            "        profit = profit,",
            "        roi_pct = (profit / total_stake) * 100",
            "    ))",
            "}",
            "",
        ]
        helper_map["hedge_stake"] = [
            "hedge_stake <- function(odds, stake, hedge_odds) {",
            "    decimal_main <- american_to_decimal(odds)",
            "    decimal_hedge <- american_to_decimal(hedge_odds)",
            "    hedge_amount <- stake * (decimal_main - 1) / (decimal_hedge - 1)",
            "    total_stake <- stake + hedge_amount",
            "    profit_main <- (stake * decimal_main) - total_stake",
            "    profit_hedge <- (hedge_amount * decimal_hedge) - total_stake",
            "    return(list(",
            "        original_odds = odds,",
            "        original_stake = stake,",
            "        hedge_odds = hedge_odds,",
            "        hedge_stake = hedge_amount,",
            "        total_stake = total_stake,",
            "        profit_if_original_wins = profit_main,",
            "        profit_if_hedge_wins = profit_hedge,",
            "        locked_profit = min(profit_main, profit_hedge)",
            "    ))",
            "}",
            "",
        ]
        helper_map["sbl_create_bet"] = [
            "sbl_create_bet <- function(bet_type, team, odds=-110, stake=100, spread=NULL) {",
            "    bet <- list(bet_type = bet_type, team = team, odds = odds, stake = stake)",
            "    if (!is.null(spread)) {",
            "        bet$spread <- spread",
            "    }",
            "    return(bet)",
            "}",
            "",
        ]
        helper_map["sbl_create_parlay"] = [
            "sbl_create_parlay <- function(bets, stake=100) {",
            "    combined_decimal <- 1",
            "    for (bet in bets) {",
            "        combined_decimal <- combined_decimal * american_to_decimal(bet$odds)",
            "    }",
            "    if (combined_decimal >= 2.0) {",
            "        combined_american <- (combined_decimal - 1) * 100",
            "    } else {",
            "        combined_american <- -100 / (combined_decimal - 1)",
            "    }",
            "    potential_payout <- stake * (combined_decimal - 1)",
            "    return(list(",
            "        bets = bets,",
            "        stake = stake,",
            "        combined_odds = combined_american,",
            "        decimal_odds = combined_decimal,",
            "        potential_payout = potential_payout,",
            "        total_return = stake + potential_payout",
            "    ))",
            "}",
            "",
        ]
        if self._needs_range_helper:
            helper_map["sbl_range"] = [
                "sbl_range <- function(start, stop=NULL, step=1) {",
                "    if (is.null(stop)) {",
                "        stop <- start",
                "        start <- 0",
                "    }",
                "    if (step == 0) {",
                "        stop('step cannot be 0')",
                "    }",
                "    if ((step > 0 && start >= stop) || (step < 0 && start <= stop)) {",
                "        return(c())",
                "    }",
                "    return(seq(from=start, to=stop - step, by=step))",
                "}",
                "",
            ]
        if self._needs_index_helper:
            helper_map["sbl_index"] = [
                "sbl_index <- function(obj, idx) {",
                "    return(obj[[idx + 1]])",
                "}",
                "",
            ]

        for helper in sorted(self._helpers):
            helpers.extend(helper_map.get(helper, []))
        if self._needs_range_helper:
            helpers.extend(helper_map["sbl_range"])
        if self._needs_index_helper:
            helpers.extend(helper_map["sbl_index"])
        return helpers

    def _julia_helpers(self) -> List[str]:
        helpers: List[str] = []
        helper_map: Dict[str, List[str]] = {}

        helper_map["american_to_decimal"] = [
            "function american_to_decimal(odds)",
            "    if odds > 0",
            "        return (odds / 100) + 1",
            "    end",
            "    return (100 / abs(odds)) + 1",
            "end",
            "",
        ]
        helper_map["decimal_to_american"] = [
            "function decimal_to_american(odds)",
            "    if odds >= 2.0",
            "        return (odds - 1) * 100",
            "    end",
            "    return -100 / (odds - 1)",
            "end",
            "",
        ]
        helper_map["implied_probability"] = [
            "function implied_probability(odds)",
            "    if odds > 0",
            "        return 100 / (odds + 100)",
            "    end",
            "    return abs(odds) / (abs(odds) + 100)",
            "end",
            "",
        ]
        helper_map["calculate_ev"] = [
            "function calculate_ev(true_prob, odds, stake=100)",
            "    decimal_odds = american_to_decimal(odds)",
            "    win_amount = stake * (decimal_odds - 1)",
            "    loss_amount = stake",
            "    return (true_prob * win_amount) - ((1 - true_prob) * loss_amount)",
            "end",
            "",
        ]
        helper_map["kelly_criterion"] = [
            "function kelly_criterion(true_prob, odds)",
            "    decimal_odds = american_to_decimal(odds)",
            "    b = decimal_odds - 1",
            "    p = true_prob",
            "    q = 1 - p",
            "    kelly = (b * p - q) / b",
            "    return max(0, kelly)",
            "end",
            "",
        ]
        helper_map["parlay_odds"] = [
            "function parlay_odds(odds_list...)",
            "    decimal_odds = [american_to_decimal(o) for o in odds_list]",
            "    combined = 1",
            "    for odd in decimal_odds",
            "        combined *= odd",
            "    end",
            "    return decimal_to_american(combined)",
            "end",
            "",
        ]
        helper_map["parlay_probability"] = [
            "function parlay_probability(probs...)",
            "    result = 1",
            "    for p in probs",
            "        result *= p",
            "    end",
            "    return result",
            "end",
            "",
        ]
        helper_map["break_even_percentage"] = [
            "function break_even_percentage(odds)",
            "    return implied_probability(odds)",
            "end",
            "",
        ]
        helper_map["vig_calculator"] = [
            "function vig_calculator(odds1, odds2)",
            "    prob1 = implied_probability(odds1)",
            "    prob2 = implied_probability(odds2)",
            "    total = prob1 + prob2",
            "    vig = total - 1",
            "    return vig * 100",
            "end",
            "",
        ]
        helper_map["true_odds_from_vig"] = [
            "function true_odds_from_vig(odds, total_vig)",
            "    implied_prob = implied_probability(odds)",
            "    true_prob = implied_prob / (1 + total_vig)",
            "    if true_prob >= 0.5",
            "        return -100 * true_prob / (1 - true_prob)",
            "    end",
            "    return 100 * (1 - true_prob) / true_prob",
            "end",
            "",
        ]
        helper_map["units_to_risk"] = [
            "function units_to_risk(odds, units_to_win=1)",
            "    if odds > 0",
            "        return units_to_win * (100 / odds)",
            "    end",
            "    return units_to_win * (abs(odds) / 100)",
            "end",
            "",
        ]
        helper_map["roi_calculator"] = [
            "function roi_calculator(wins, losses, avg_odds)",
            "    if wins + losses == 0",
            "        return 0",
            "    end",
            "    win_rate = wins / (wins + losses)",
            "    avg_payout = calculate_ev(win_rate, avg_odds, 100)",
            "    total_staked = (wins + losses) * 100",
            "    total_return = wins * (100 + abs(avg_payout))",
            "    return ((total_return - total_staked) / total_staked) * 100",
            "end",
            "",
        ]
        helper_map["round_robin"] = [
            "function round_robin(bets_count, parlay_size)",
            "    return binomial(bets_count, parlay_size)",
            "end",
            "",
        ]
        helper_map["arbitrage_stakes"] = [
            "function arbitrage_stakes(odds1, odds2, total_stake=100)",
            "    decimal1 = american_to_decimal(odds1)",
            "    decimal2 = american_to_decimal(odds2)",
            "    implied1 = 1 / decimal1",
            "    implied2 = 1 / decimal2",
            "    total_implied = implied1 + implied2",
            "    stake1 = total_stake * (implied1 / total_implied)",
            "    stake2 = total_stake * (implied2 / total_implied)",
            "    payout1 = stake1 * decimal1",
            "    payout2 = stake2 * decimal2",
            "    profit = min(payout1, payout2) - total_stake",
            "    return Dict(",
            "        \"odds1\" => odds1,",
            "        \"odds2\" => odds2,",
            "        \"stake_total\" => total_stake,",
            "        \"stake1\" => stake1,",
            "        \"stake2\" => stake2,",
            "        \"total_implied\" => total_implied,",
            "        \"arb_margin_pct\" => (1 - total_implied) * 100,",
            "        \"profit\" => profit,",
            "        \"roi_pct\" => (profit / total_stake) * 100",
            "    )",
            "end",
            "",
        ]
        helper_map["hedge_stake"] = [
            "function hedge_stake(odds, stake, hedge_odds)",
            "    decimal_main = american_to_decimal(odds)",
            "    decimal_hedge = american_to_decimal(hedge_odds)",
            "    hedge_amount = stake * (decimal_main - 1) / (decimal_hedge - 1)",
            "    total_stake = stake + hedge_amount",
            "    profit_main = (stake * decimal_main) - total_stake",
            "    profit_hedge = (hedge_amount * decimal_hedge) - total_stake",
            "    return Dict(",
            "        \"original_odds\" => odds,",
            "        \"original_stake\" => stake,",
            "        \"hedge_odds\" => hedge_odds,",
            "        \"hedge_stake\" => hedge_amount,",
            "        \"total_stake\" => total_stake,",
            "        \"profit_if_original_wins\" => profit_main,",
            "        \"profit_if_hedge_wins\" => profit_hedge,",
            "        \"locked_profit\" => min(profit_main, profit_hedge)",
            "    )",
            "end",
            "",
        ]
        helper_map["sbl_create_bet"] = [
            "function sbl_create_bet(bet_type, team; odds=-110, stake=100, spread=nothing)",
            "    bet = Dict(\"bet_type\" => bet_type, \"team\" => team, \"odds\" => odds, \"stake\" => stake)",
            "    if spread !== nothing",
            "        bet[\"spread\"] = spread",
            "    end",
            "    return bet",
            "end",
            "",
        ]
        helper_map["sbl_create_parlay"] = [
            "function sbl_create_parlay(bets; stake=100)",
            "    combined_decimal = 1",
            "    for bet in bets",
            "        combined_decimal *= american_to_decimal(get(bet, \"odds\", -110))",
            "    end",
            "    if combined_decimal >= 2.0",
            "        combined_american = (combined_decimal - 1) * 100",
            "    else",
            "        combined_american = -100 / (combined_decimal - 1)",
            "    end",
            "    potential_payout = stake * (combined_decimal - 1)",
            "    return Dict(",
            "        \"bets\" => bets,",
            "        \"stake\" => stake,",
            "        \"combined_odds\" => combined_american,",
            "        \"decimal_odds\" => combined_decimal,",
            "        \"potential_payout\" => potential_payout,",
            "        \"total_return\" => stake + potential_payout",
            "    )",
            "end",
            "",
        ]
        if self._needs_range_helper:
            helper_map["sbl_range"] = [
                "function sbl_range(start, stop=nothing, step=1)",
                "    if stop === nothing",
                "        stop = start",
                "        start = 0",
                "    end",
                "    if step == 0",
                "        error(\"step cannot be 0\")",
                "    end",
                "    if (step > 0 && start >= stop) || (step < 0 && start <= stop)",
                "        return Int[]",
                "    end",
                "    return collect(start:step:(stop - step))",
                "end",
                "",
            ]
        if self._needs_index_helper:
            helper_map["sbl_index"] = [
                "function sbl_index(obj, idx)",
                "    return obj[idx + 1]",
                "end",
                "",
            ]

        for helper in sorted(self._helpers):
            helpers.extend(helper_map.get(helper, []))
        if self._needs_range_helper:
            helpers.extend(helper_map["sbl_range"])
        if self._needs_index_helper:
            helpers.extend(helper_map["sbl_index"])
        return helpers


def generate_code(source: str, language: str = "python", include_prelude: bool = True) -> str:
    """Convenience function to generate code from SportsBetLang source."""
    generator = CodeGenerator(language=language, include_prelude=include_prelude)
    return generator.generate_from_source(source).source
