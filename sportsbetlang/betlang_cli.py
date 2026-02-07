"""
BetLang CLI entry point.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from formatting import format_source
from interpreter import Interpreter, LanguageRuntimeError
from lexer import Lexer
from linting import lint_source
from parser import Parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="betlang",
        description="Run SportsBetLang programs with simple subcommands.",
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run a SportsBetLang .odds file.")
    run_parser.add_argument("source", help="Path to a .odds SportsBetLang program.")
    run_parser.add_argument(
        "--max-steps",
        type=int,
        default=1_000_000,
        help="Maximum interpreter steps before aborting (default: 1,000,000).",
    )

    repl_parser = subparsers.add_parser("repl", help="Start an interactive REPL.")
    repl_parser.add_argument(
        "--max-steps",
        type=int,
        default=1_000_000,
        help="Maximum interpreter steps before aborting (default: 1,000,000).",
    )

    format_parser = subparsers.add_parser("format", help="Format a .odds SportsBetLang program.")
    format_parser.add_argument("source", help="Path to a .odds SportsBetLang program.")
    format_parser.add_argument(
        "--write",
        action="store_true",
        help="Write formatted output back to the source file.",
    )

    lint_parser = subparsers.add_parser("lint", help="Lint a .odds SportsBetLang program.")
    lint_parser.add_argument("source", help="Path to a .odds SportsBetLang program.")

    return parser


def run_source(source: str, filename: str, max_steps: int) -> None:
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens, source)
    ast = parser.parse()
    interpreter = Interpreter(max_steps=max_steps)
    interpreter.interpret(ast)


def run_file(path: str, max_steps: int) -> None:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File '{path}' not found")
    source = file_path.read_text(encoding="utf-8")
    run_source(source, str(file_path), max_steps)


def repl(max_steps: int) -> None:
    print("SportsBetLang v1.0 - Sports Betting Programming Language")
    print("Type 'exit' or 'quit' to exit, 'help' for help")
    print()

    interpreter = Interpreter(max_steps=max_steps)

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

            lexer = Lexer(line)
            tokens = lexer.tokenize()

            parser = Parser(tokens, line)
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
BetLang - SportsBetLang Runner

COMMANDS:
  betlang run examples/01_basic_bet.odds   Run a .odds file
  betlang repl                             Start the REPL
  betlang format examples/01_basic_bet.odds
  betlang lint examples/01_basic_bet.odds
"""
    print(help_text)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "run":
            run_file(args.source, max_steps=args.max_steps)
            return 0
        if args.command == "repl" or args.command is None:
            repl(max_steps=getattr(args, "max_steps", 1_000_000))
            return 0
        if args.command == "format":
            file_path = Path(args.source)
            if not file_path.exists():
                raise FileNotFoundError(f"File '{args.source}' not found")
            source = file_path.read_text(encoding="utf-8")
            formatted = format_source(source)
            if args.write:
                file_path.write_text(formatted, encoding="utf-8")
            else:
                print(formatted, end="")
            return 0
        if args.command == "lint":
            file_path = Path(args.source)
            if not file_path.exists():
                raise FileNotFoundError(f"File '{args.source}' not found")
            source = file_path.read_text(encoding="utf-8")
            issues = lint_source(source)
            if issues:
                for issue in issues:
                    print(issue.format())
                return 1
            return 0
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

    print("Unknown command. Use --help for usage.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
