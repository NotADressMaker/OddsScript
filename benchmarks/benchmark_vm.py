"""Micro-benchmark: AST interpreter vs bytecode VM for arithmetic workloads."""

from __future__ import annotations

import time

from sportsbetlang.lang.bytecode import BytecodeCompiler, BytecodeVM
from sportsbetlang.lang.interpreter import Interpreter
from sportsbetlang.lang.lexer import Lexer
from sportsbetlang.lang.parser import Parser


def build_program(n: int = 2000) -> str:
    lines = ["let accum = 0"]
    for i in range(1, n + 1):
        lines.append(f"accum = accum + {i}")
    lines.append("accum")
    return "\n".join(lines)


def main() -> None:
    source = build_program()
    ast = Parser(Lexer(source).tokenize(), source).parse()

    t0 = time.perf_counter()
    Interpreter().interpret(ast)
    t1 = time.perf_counter()

    code = BytecodeCompiler().compile(ast)
    vm = BytecodeVM()
    t2 = time.perf_counter()
    vm.run(code)
    t3 = time.perf_counter()

    print(f"interpreter_s={(t1 - t0):.6f}")
    print(f"bytecode_s={(t3 - t2):.6f}")


if __name__ == "__main__":
    main()
