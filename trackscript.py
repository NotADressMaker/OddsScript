#!/usr/bin/env python3
"""
TrackScript - A programming language for horse racing betting
Main entry point for running TrackScript programs
"""

import sys
from lexer import Lexer
from parser import Parser
from interpreter import Interpreter


def run_file(filename: str):
    """Execute a TrackScript file"""
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
    """Execute TrackScript source code"""
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
    print("TrackScript v1.0 - Horse Racing Programming Language")
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
TrackScript - Horse Racing Programming Language

BASIC SYNTAX:
  let x = 100              # Variable declaration
  const bankroll = 1000    # Constant declaration
  print(x)                 # Print to console

WAGERING OPERATIONS:
  wager win horse 5 odds "7-2" stake 20          # Win bet
  wager place horse 3 odds "3-5" stake 40        # Place bet
  wager exacta box [5, 7, 8] stake 12           # Exacta box
  wager trifecta key 5 with [2, 7, 8, 9] stake 24   # Trifecta key

BUILT-IN FUNCTIONS:
  track_to_decimal(odds)              # Convert track odds to decimal
  win_payout(odds, stake)             # Calculate win bet payout
  exacta_combinations(horses)         # Calculate exacta combinations
  box_cost(bet_type, horses, stake)   # Calculate box bet cost
  speed_rating(time, condition, dist) # Calculate speed figure
  kelly_racing(prob, odds, bankroll)  # Kelly criterion for racing
  dutching(horses, stake)             # Calculate dutching stakes
  overlay_percentage(true, ml)        # Calculate overlay/underlay

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
        print("Usage: trackscript.py [filename]")
        print("       trackscript.py          (start REPL)")
        sys.exit(1)


if __name__ == '__main__':
    main()
