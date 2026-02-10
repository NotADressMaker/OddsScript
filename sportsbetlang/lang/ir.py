"""Intermediate representation (IR) pipeline for SportsBetLang.

The IR layer provides:
- AST normalization + constant folding.
- Reachability cleanup (dead statements after return).
- Static analysis (unused vars, unreachable code, coarse loop cost estimate).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from sportsbetlang.lang.lexer import TokenType
from sportsbetlang.lang.parser import (
    ASTNode,
    ArrayLiteral,
    Assignment,
    BinaryOp,
    BooleanLiteral,
    CallExpression,
    DictLiteral,
    ForLoop,
    FunctionCall,
    FunctionDef,
    Identifier,
    IfStatement,
    ImportStatement,
    IndexAccess,
    MemberAccess,
    NumberLiteral,
    ParlayStatement,
    Program,
    ReturnStatement,
    StringLiteral,
    UnaryOp,
    WhileLoop,
    FromImportStatement,
    BetStatement,
)


@dataclass
class IRProgram:
    statements: list[ASTNode]
    warnings: list[str] = field(default_factory=list)
    loop_cost_estimate: int = 0


@dataclass
class UsageSummary:
    assigned: dict[str, int] = field(default_factory=dict)
    used: dict[str, int] = field(default_factory=dict)
    unreachable: int = 0


def build_ir(program: Program) -> IRProgram:
    usage = UsageSummary()
    optimized = _optimize_block(program.statements, usage)
    warnings = _warnings_from_usage(usage)
    loop_cost = _estimate_loop_cost(optimized)
    return IRProgram(statements=optimized, warnings=warnings, loop_cost_estimate=loop_cost)


def _warnings_from_usage(usage: UsageSummary) -> list[str]:
    warnings: list[str] = []
    for name in sorted(usage.assigned):
        if usage.used.get(name, 0) == 0:
            warnings.append(f"Unused variable '{name}'")
    if usage.unreachable:
        warnings.append(f"Unreachable statements detected: {usage.unreachable}")
    return warnings


def _estimate_loop_cost(statements: list[ASTNode]) -> int:
    cost = 0
    for node in statements:
        if isinstance(node, ForLoop):
            size = _constant_collection_size(node.iterable)
            cost += max(size, 1) * max(len(node.body), 1)
            cost += _estimate_loop_cost(node.body)
        elif isinstance(node, WhileLoop):
            # Unknown while loops are treated as expensive.
            cost += 1_000 * max(len(node.body), 1)
            cost += _estimate_loop_cost(node.body)
        elif isinstance(node, IfStatement):
            cost += _estimate_loop_cost(node.then_block)
            if node.else_block:
                cost += _estimate_loop_cost(node.else_block)
        elif isinstance(node, FunctionDef):
            cost += _estimate_loop_cost(node.body)
    return cost


def _constant_collection_size(node: ASTNode) -> int:
    if isinstance(node, ArrayLiteral):
        return len(node.elements)
    if isinstance(node, DictLiteral):
        return len(node.pairs)
    return 0


def _optimize_block(statements: list[ASTNode], usage: UsageSummary) -> list[ASTNode]:
    out: list[ASTNode] = []
    terminated = False
    for stmt in statements:
        if terminated:
            usage.unreachable += 1
            continue
        opt = _optimize_node(stmt, usage)
        out.append(opt)
        if isinstance(opt, ReturnStatement):
            terminated = True
    return out


def _optimize_node(node: ASTNode, usage: UsageSummary) -> ASTNode:
    if isinstance(node, Assignment):
        usage.assigned[node.name] = usage.assigned.get(node.name, 0) + 1
        return Assignment(name=node.name, value=_optimize_expr(node.value, usage), is_const=node.is_const)
    if isinstance(node, ReturnStatement):
        return ReturnStatement(value=_optimize_expr(node.value, usage) if node.value else None)
    if isinstance(node, IfStatement):
        condition = _optimize_expr(node.condition, usage)
        then_block = _optimize_block(node.then_block, usage)
        else_block = _optimize_block(node.else_block, usage) if node.else_block else None
        if isinstance(condition, BooleanLiteral):
            return Program(statements=then_block if condition.value else (else_block or []))
        return IfStatement(condition=condition, then_block=then_block, else_block=else_block)
    if isinstance(node, WhileLoop):
        condition = _optimize_expr(node.condition, usage)
        body = _optimize_block(node.body, usage)
        return WhileLoop(condition=condition, body=body)
    if isinstance(node, ForLoop):
        iterable = _optimize_expr(node.iterable, usage)
        body = _optimize_block(node.body, usage)
        return ForLoop(variable=node.variable, iterable=iterable, body=body)
    if isinstance(node, FunctionDef):
        body = _optimize_block(node.body, usage)
        return FunctionDef(name=node.name, parameters=node.parameters, body=body)
    if isinstance(node, Program):
        return Program(statements=_optimize_block(node.statements, usage))
    # Other statement-like nodes
    return _optimize_expr(node, usage)


def _optimize_expr(node: ASTNode, usage: UsageSummary) -> ASTNode:
    if isinstance(node, Identifier):
        usage.used[node.name] = usage.used.get(node.name, 0) + 1
        return node
    if isinstance(node, BinaryOp):
        left = _optimize_expr(node.left, usage)
        right = _optimize_expr(node.right, usage)
        folded = _try_fold_binary(left, node.operator, right)
        return folded if folded is not None else BinaryOp(left=left, operator=node.operator, right=right)
    if isinstance(node, UnaryOp):
        operand = _optimize_expr(node.operand, usage)
        folded = _try_fold_unary(node.operator, operand)
        return folded if folded is not None else UnaryOp(operator=node.operator, operand=operand)
    if isinstance(node, ArrayLiteral):
        return ArrayLiteral(elements=[_optimize_expr(e, usage) for e in node.elements])
    if isinstance(node, DictLiteral):
        return DictLiteral(pairs=[(_optimize_expr(k, usage), _optimize_expr(v, usage)) for k, v in node.pairs])
    if isinstance(node, FunctionCall):
        return FunctionCall(name=node.name, arguments=[_optimize_expr(a, usage) for a in node.arguments])
    if isinstance(node, CallExpression):
        return CallExpression(callee=_optimize_expr(node.callee, usage), arguments=[_optimize_expr(a, usage) for a in node.arguments])
    if isinstance(node, IndexAccess):
        return IndexAccess(object=_optimize_expr(node.object, usage), index=_optimize_expr(node.index, usage))
    if isinstance(node, MemberAccess):
        return MemberAccess(object=_optimize_expr(node.object, usage), member=node.member)
    if isinstance(node, BetStatement):
        return BetStatement(
            bet_type=node.bet_type,
            team=_optimize_expr(node.team, usage),
            odds=_optimize_expr(node.odds, usage),
            stake=_optimize_expr(node.stake, usage),
            additional_params={k: _optimize_expr(v, usage) for k, v in node.additional_params.items()},
        )
    if isinstance(node, ParlayStatement):
        return ParlayStatement(
            bets=[_optimize_expr(b, usage) for b in node.bets],
            stake=_optimize_expr(node.stake, usage),
        )
    if isinstance(node, ImportStatement | FromImportStatement | NumberLiteral | StringLiteral | BooleanLiteral):
        return node
    return node


def _try_fold_unary(operator: TokenType, operand: ASTNode) -> Optional[ASTNode]:
    if isinstance(operand, NumberLiteral) and operator == TokenType.MINUS:
        return NumberLiteral(value=-operand.value)
    if isinstance(operand, BooleanLiteral) and operator == TokenType.NOT:
        return BooleanLiteral(value=not operand.value)
    return None


def _try_fold_binary(left: ASTNode, operator: TokenType, right: ASTNode) -> Optional[ASTNode]:
    if isinstance(left, NumberLiteral) and isinstance(right, NumberLiteral):
        a, b = left.value, right.value
        if operator == TokenType.PLUS:
            return NumberLiteral(a + b)
        if operator == TokenType.MINUS:
            return NumberLiteral(a - b)
        if operator == TokenType.MULTIPLY:
            return NumberLiteral(a * b)
        if operator == TokenType.DIVIDE and b != 0:
            return NumberLiteral(a / b)
        if operator == TokenType.MODULO and b != 0:
            return NumberLiteral(a % b)
        if operator == TokenType.LESS_THAN:
            return BooleanLiteral(a < b)
        if operator == TokenType.GREATER_THAN:
            return BooleanLiteral(a > b)
        if operator == TokenType.LESS_EQUAL:
            return BooleanLiteral(a <= b)
        if operator == TokenType.GREATER_EQUAL:
            return BooleanLiteral(a >= b)
        if operator == TokenType.EQUAL:
            return BooleanLiteral(a == b)
        if operator == TokenType.NOT_EQUAL:
            return BooleanLiteral(a != b)
    if isinstance(left, BooleanLiteral) and isinstance(right, BooleanLiteral):
        if operator == TokenType.AND:
            return BooleanLiteral(left.value and right.value)
        if operator == TokenType.OR:
            return BooleanLiteral(left.value or right.value)
        if operator == TokenType.EQUAL:
            return BooleanLiteral(left.value == right.value)
        if operator == TokenType.NOT_EQUAL:
            return BooleanLiteral(left.value != right.value)
    if isinstance(left, StringLiteral) and isinstance(right, StringLiteral) and operator == TokenType.PLUS:
        return StringLiteral(left.value + right.value)
    return None


def has_definitely_infinite_loop(ir_program: IRProgram) -> bool:
    for stmt in ir_program.statements:
        if isinstance(stmt, WhileLoop) and isinstance(stmt.condition, BooleanLiteral) and stmt.condition.value:
            return True
    return False
