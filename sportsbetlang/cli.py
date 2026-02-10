"""
SportsBetLang CLI entry point.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from formatting import format_source
from interpreter import Interpreter, LanguageRuntimeError
from lexer import Lexer
from linting import lint_source
from parser import Parser, Program
from sportsbetlang.lang.ir import build_ir, has_definitely_infinite_loop
from sportsbetlang.lang.limits import EXPERT_LIMITS, SAFE_LIMITS, resolve_runtime_limits
from sportsbetlang.lang.sandbox import HostCapabilities


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sportsbetlang",
        description="Run SportsBetLang programs or start an interactive REPL.",
    )
    parser.add_argument(
        "source",
        nargs="?",
        help="Path to a .odds SportsBetLang program to execute.",
    )
    parser.add_argument(
        "--mode",
        choices=("safe", "expert"),
        default="safe",
        help="Runtime profile: safe defaults for new users (default) or expert.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Maximum interpreter steps before aborting.",
    )
    parser.add_argument(
        "--max-loop",
        type=int,
        default=None,
        help="Maximum loop iterations before aborting.",
    )
    parser.add_argument(
        "--max-recursion",
        type=int,
        default=None,
        help="Maximum recursion depth before aborting.",
    )
    parser.add_argument(
        "--format",
        action="store_true",
        help="Format a .odds SportsBetLang program.",
    )
    parser.add_argument(
        "--lint",
        action="store_true",
        help="Lint a .odds SportsBetLang program.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write formatted output back to the source file (with --format).",
    )
    parser.add_argument("--no-io", action="store_true", help="Disable host file/network functions (default deny).")
    parser.add_argument("--allow-read-dir", action="append", default=[], help="Allow host_read_text() access under this directory. Repeatable.")
    parser.add_argument("--allow-domain", action="append", default=[], help="Allow host_http_get() to this domain. Repeatable.")
    parser.add_argument("--audit-log", default=None, help="Write host capability audit events to this file.")
    return parser


def run_source(source: str, filename: str, *, mode: str, max_steps: int | None, max_loop: int | None, max_recursion: int | None, no_io: bool = True, allow_read_dirs: list[str] | None = None, allow_domains: list[str] | None = None, audit_log_path: str | None = None) -> None:
    base_limits = SAFE_LIMITS if mode == "safe" else EXPERT_LIMITS
    limits = resolve_runtime_limits(
        source,
        base_limits=base_limits,
        max_steps=max_steps,
        max_loop=max_loop,
        max_recursion=max_recursion,
    )
    lexer = Lexer(source, limits=limits)
    tokens = lexer.tokenize()
    parser = Parser(tokens, source, limits=limits)
    ast = parser.parse()
    ir_program = build_ir(ast)
    if has_definitely_infinite_loop(ir_program):
        raise LanguageRuntimeError("Program contains a definitely-infinite while true loop")
    interpreter = Interpreter(
        limits=limits,
        source=source,
        capabilities=HostCapabilities(
            no_io=no_io,
            allow_read_dirs=allow_read_dirs or [],
            allow_domains=allow_domains or [],
        ),
    )
    optimized_program = Program(statements=ir_program.statements)
    interpreter.interpret(optimized_program)
    if audit_log_path:
        Path(audit_log_path).write_text("\n".join(interpreter.capabilities.snapshot_audit_log()) + "\n", encoding="utf-8")


def run_file(path: str, *, mode: str, max_steps: int | None, max_loop: int | None, max_recursion: int | None, no_io: bool, allow_read_dirs: list[str], allow_domains: list[str], audit_log_path: str | None) -> None:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File '{path}' not found")
    source = file_path.read_text(encoding="utf-8")
    run_source(source, str(file_path), mode=mode, max_steps=max_steps, max_loop=max_loop, max_recursion=max_recursion, no_io=no_io, allow_read_dirs=allow_read_dirs, allow_domains=allow_domains, audit_log_path=audit_log_path)


def repl(*, mode: str, max_steps: int | None, max_loop: int | None, max_recursion: int | None, no_io: bool, allow_read_dirs: list[str], allow_domains: list[str], audit_log_path: str | None) -> None:
    print("SportsBetLang v1.0 - Sports Betting Programming Language")
    print("Type 'exit' or 'quit' to exit, 'help' for help")
    print()

    limits = resolve_runtime_limits("", base_limits=SAFE_LIMITS if mode == "safe" else EXPERT_LIMITS, max_steps=max_steps, max_loop=max_loop, max_recursion=max_recursion)
    interpreter = Interpreter(limits=limits, source="", capabilities=HostCapabilities(no_io=no_io, allow_read_dirs=allow_read_dirs, allow_domains=allow_domains))

    while True:
        try:
            line = input(">>> ")

            if line.strip() in ["exit", "quit"]:
                break

            if line.strip() == "help":
                print_help()
                continue

            if not line.strip():
                continue

            lexer = Lexer(line, limits=limits)
            tokens = lexer.tokenize()

            parser = Parser(tokens, line, limits=limits)
            ast = parser.parse()

            result = interpreter.interpret(ast)

            if result is not None:
                print(result)

        except EOFError:
            break
        except KeyboardInterrupt:
            print("\nInterrupted")
            break
        except LanguageRuntimeError as exc:
            print(f"Error: {exc.format()}")
        except Exception as exc:
            print(f"Error: {exc}")


def print_help() -> None:
    help_text = """
SportsBetLang - Sports Betting Programming Language

BASIC SYNTAX:
  let x = 100              # Variable declaration
  const bankroll = 1000    # Constant declaration
  print(x)                 # Print to console

BETTING OPERATIONS:
  bet "Lakers" odds -110 stake 100              # Create a moneyline bet
  bet spread "Chiefs" odds -110 stake 50        # Spread bet
  parlay [bet1, bet2, bet3] stake 100          # Create parlay

BUILT-IN FUNCTIONS:
  american_to_decimal(odds)           # Convert American to decimal odds
  decimal_to_american(odds)           # Convert decimal to American odds
  implied_probability(odds)           # Calculate implied probability
  calculate_ev(prob, odds, stake)     # Calculate expected value
  kelly_criterion(prob, odds)         # Kelly criterion bet sizing
  parlay_odds(odds1, odds2, ...)      # Calculate parlay odds
  vig_calculator(odds1, odds2)        # Calculate bookmaker's vig
  break_even_percentage(odds)         # Break-even win percentage
  arbitrage_stakes(odds1, odds2, stake) # Two-way arbitrage sizing
  hedge_stake(odds, stake, hedge_odds)  # Hedge bet sizing

CONTROL FLOW:
  if condition { ... } else { ... }   # Conditional
  while condition { ... }             # While loop
  for x in array { ... }              # For loop
  func name(param1, param2) { ... }   # Function definition

EXAMPLES:
  See the examples/ directory for sample programs
"""
    print(help_text)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.format or args.lint:
            if not args.source:
                raise FileNotFoundError("No source file provided")
            file_path = Path(args.source)
            if not file_path.exists():
                raise FileNotFoundError(f"File '{args.source}' not found")
            source = file_path.read_text(encoding="utf-8")
            if args.format:
                formatted = format_source(source)
                if args.write:
                    file_path.write_text(formatted, encoding="utf-8")
                else:
                    print(formatted, end="")
            if args.lint:
                issues = lint_source(source)
                if issues:
                    for issue in issues:
                        print(issue.format())
                    return 1
            return 0
        if args.source:
            run_file(args.source, mode=args.mode, max_steps=args.max_steps, max_loop=args.max_loop, max_recursion=args.max_recursion, no_io=args.no_io, allow_read_dirs=args.allow_read_dir, allow_domains=args.allow_domain, audit_log_path=args.audit_log)
        else:
            repl(mode=args.mode, max_steps=args.max_steps, max_loop=args.max_loop, max_recursion=args.max_recursion, no_io=args.no_io, allow_read_dirs=args.allow_read_dir, allow_domains=args.allow_domain, audit_log_path=args.audit_log)
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        return 1
    except LanguageRuntimeError as exc:
        print(f"Runtime Error: {exc.format()}")
        return 1
    except SyntaxError as exc:
        print(f"Syntax Error: {exc}")
        return 1
    except Exception as exc:
        print(f"Unexpected Error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
