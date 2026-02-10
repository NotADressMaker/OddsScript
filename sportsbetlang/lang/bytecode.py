"""Simple bytecode VM for numeric-heavy SportsBetLang programs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sportsbetlang.lang.lexer import TokenType
from sportsbetlang.lang.parser import Assignment, BinaryOp, Identifier, NumberLiteral, Program


@dataclass
class Instruction:
    op: str
    arg: Any = None


class BytecodeCompiler:
    def compile(self, program: Program) -> list[Instruction]:
        code: list[Instruction] = []
        for stmt in program.statements:
            if isinstance(stmt, Assignment):
                self._emit_expr(stmt.value, code)
                code.append(Instruction("STORE", stmt.name))
            else:
                self._emit_expr(stmt, code)
                code.append(Instruction("POP"))
        code.append(Instruction("HALT"))
        return code

    def _emit_expr(self, node: Any, code: list[Instruction]) -> None:
        if isinstance(node, NumberLiteral):
            code.append(Instruction("PUSH_CONST", node.value))
            return
        if isinstance(node, Identifier):
            code.append(Instruction("LOAD", node.name))
            return
        if isinstance(node, BinaryOp):
            self._emit_expr(node.left, code)
            self._emit_expr(node.right, code)
            code.append(Instruction("BINARY", node.operator))
            return
        raise RuntimeError(f"Unsupported node for bytecode: {type(node).__name__}")


class BytecodeVM:
    def __init__(self) -> None:
        self.stack: list[Any] = []
        self.env: dict[str, Any] = {}

    def run(self, code: list[Instruction]) -> Any:
        ip = 0
        while ip < len(code):
            ins = code[ip]
            if ins.op == "PUSH_CONST":
                self.stack.append(ins.arg)
            elif ins.op == "STORE":
                self.env[ins.arg] = self.stack.pop()
            elif ins.op == "LOAD":
                self.stack.append(self.env[ins.arg])
            elif ins.op == "BINARY":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(self._apply_binary(ins.arg, a, b))
            elif ins.op == "POP":
                if self.stack:
                    self.stack.pop()
            elif ins.op == "HALT":
                return self.stack[-1] if self.stack else None
            else:
                raise RuntimeError(f"Unknown opcode: {ins.op}")
            ip += 1
        return self.stack[-1] if self.stack else None

    def _apply_binary(self, op: TokenType, a: Any, b: Any) -> Any:
        if op == TokenType.PLUS:
            return a + b
        if op == TokenType.MINUS:
            return a - b
        if op == TokenType.MULTIPLY:
            return a * b
        if op == TokenType.DIVIDE:
            return a / b
        if op == TokenType.MODULO:
            return a % b
        raise RuntimeError(f"Unsupported bytecode binary op: {op}")
