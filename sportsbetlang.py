#!/usr/bin/env python3
"""
SportsBetLang - A programming language for sports betting
Main entry point for running SportsBetLang programs
"""

import argparse
import sys
from lexer import Lexer
from parser import Parser
from interpreter import Interpreter, LanguageRuntimeError
from formatting import format_source
from linting import lint_source


def run_file(filename: str):
    """Execute a SportsBetLang file"""
    try:
        with open(filename, 'r') as f:
            source = f.read()

        run(source, filename)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)


def run(source: str, filename: str = "<stdin>"):
    """Execute SportsBetLang source code"""
    try:
        # Lexical analysis
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # Parsing
        parser = Parser(tokens, source)
        ast = parser.parse()

        # Interpretation
        interpreter = Interpreter()
        interpreter.interpret(ast)

    except SyntaxError as e:
        print(f"Syntax Error in {filename}: {e}")
        sys.exit(1)
    except LanguageRuntimeError as e:
        print(f"Runtime Error in {filename}: {e.format()}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"Runtime Error in {filename}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error in {filename}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def repl():
    """Run an interactive REPL"""
    print("SportsBetLang v1.0 - Sports Betting Programming Language")
    print("Type 'exit' or 'quit' to exit, 'help' for help")
    print()

    interpreter = Interpreter()

    while True:
        try:
            line = input(">>> ")

            if line.strip() in ['exit', 'quit']:
                break

            if line.strip() == 'help':
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
        except LanguageRuntimeError as e:
            print(f"Error: {e.format()}")
        except Exception as e:
            print(f"Error: {e}")


def print_help():
    """Print help information"""
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sportsbetlang",
        description="Run, format, or lint SportsBetLang programs.",
    )
    parser.add_argument(
        "source",
        nargs="?",
        help="Path to a .odds SportsBetLang program.",
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
    return parser


def main() -> int:
    """Main entry point"""
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.format or args.lint:
            if not args.source:
                raise FileNotFoundError("No source file provided")
            with open(args.source, "r", encoding="utf-8") as handle:
                source = handle.read()
            if args.format:
                formatted = format_source(source)
                if args.write:
                    with open(args.source, "w", encoding="utf-8") as handle:
                        handle.write(formatted)
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
            run_file(args.source)
        else:
            repl()
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


if __name__ == '__main__':
    raise SystemExit(main())
