"""
SportsBetLang CLI entry point.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from interpreter import Interpreter, LanguageRuntimeError
from lexer import Lexer
from parser import Parser


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
        "--max-steps",
        type=int,
        default=1_000_000,
        help="Maximum interpreter steps before aborting (default: 1,000,000).",
    )
    return parser


def run_source(source: str, filename: str, max_steps: int) -> None:
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
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

            parser = Parser(tokens)
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
        if args.source:
            run_file(args.source, max_steps=args.max_steps)
        else:
            repl(max_steps=args.max_steps)
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
