#!/usr/bin/env python3
"""
OddsScript - A programming language for sports betting
Main entry point for running OddsScript programs
"""

import sys
from lexer import Lexer
from parser import Parser
from interpreter import Interpreter


def run_file(filename: str):
    """Execute an OddsScript file"""
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
    """Execute OddsScript source code"""
    try:
        # Lexical analysis
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # Parsing
        parser = Parser(tokens)
        ast = parser.parse()

        # Interpretation
        interpreter = Interpreter()
        interpreter.interpret(ast)

    except SyntaxError as e:
        print(f"Syntax Error in {filename}: {e}")
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
    print("OddsScript v1.0 - Sports Betting Programming Language")
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
        except Exception as e:
            print(f"Error: {e}")


def print_help():
    """Print help information"""
    help_text = """
OddsScript - Sports Betting Programming Language

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

CONTROL FLOW:
  if condition { ... } else { ... }   # Conditional
  while condition { ... }             # While loop
  for x in array { ... }              # For loop
  func name(param1, param2) { ... }   # Function definition

EXAMPLES:
  See the examples/ directory for sample programs
"""
    print(help_text)


def main():
    """Main entry point"""
    if len(sys.argv) == 1:
        repl()
    elif len(sys.argv) == 2:
        if sys.argv[1] in ['-h', '--help']:
            print_help()
        else:
            run_file(sys.argv[1])
    else:
        print("Usage: oddsscript.py [filename]")
        print("       oddsscript.py          (start REPL)")
        sys.exit(1)


if __name__ == '__main__':
    main()
