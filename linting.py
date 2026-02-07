"""
Simple linter for SportsBetLang source code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from lexer import Lexer
from parser import (
    Assignment,
    BetStatement,
    ForLoop,
    FunctionDef,
    IfStatement,
    ParlayStatement,
    Program,
    ReturnStatement,
    WhileLoop,
    Parser,
)


@dataclass
class LintIssue:
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    severity: str = "warning"

    def format(self) -> str:
        location = ""
        if self.line is not None and self.column is not None:
            location = f" (line {self.line}, column {self.column})"
        return f"[{self.severity}] {self.message}{location}"


class Linter:
    def __init__(self) -> None:
        self.issues: List[LintIssue] = []
        self._const_scopes: List[set[str]] = []
        self._in_function = 0

    def lint(self, program: Program) -> List[LintIssue]:
        self._push_scope()
        self._visit(program)
        self._pop_scope()
        return self.issues

    def _push_scope(self) -> None:
        self._const_scopes.append(set())

    def _pop_scope(self) -> None:
        self._const_scopes.pop()

    def _define_const(self, name: str) -> None:
        self._const_scopes[-1].add(name)

    def _is_const(self, name: str) -> bool:
        return any(name in scope for scope in reversed(self._const_scopes))

    def _visit(self, node) -> None:
        if isinstance(node, Program):
            for stmt in node.statements:
                self._visit(stmt)
        elif isinstance(node, Assignment):
            if node.is_const:
                if node.name in self._const_scopes[-1]:
                    self._warn("Constant redeclared in same scope", node)
                self._define_const(node.name)
            else:
                if self._is_const(node.name):
                    self._warn("Attempting to reassign constant", node)
        elif isinstance(node, FunctionDef):
            self._in_function += 1
            self._push_scope()
            for param in node.parameters:
                # Parameters are mutable bindings by default
                pass
            for stmt in node.body:
                self._visit(stmt)
            self._pop_scope()
            self._in_function -= 1
        elif isinstance(node, ReturnStatement):
            if self._in_function == 0:
                self._warn("Return statement outside of a function", node)
        elif isinstance(node, ForLoop):
            self._push_scope()
            for stmt in node.body:
                self._visit(stmt)
            self._pop_scope()
        elif isinstance(node, IfStatement):
            for stmt in node.then_block:
                self._visit(stmt)
            if node.else_block:
                for stmt in node.else_block:
                    self._visit(stmt)
        elif isinstance(node, WhileLoop):
            for stmt in node.body:
                self._visit(stmt)
        elif isinstance(node, BetStatement):
            if node.odds is None:
                self._warn("Bet statement missing odds", node)
            if node.stake is None:
                self._warn("Bet statement missing stake", node)
        elif isinstance(node, ParlayStatement):
            if not node.bets:
                self._warn("Parlay statement has no bets", node)

    def _warn(self, message: str, node) -> None:
        self.issues.append(
            LintIssue(
                message=message,
                line=getattr(node, "line", None),
                column=getattr(node, "column", None),
            )
        )


def lint_source(source: str) -> List[LintIssue]:
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens, source)
    program = parser.parse()
    return Linter().lint(program)
