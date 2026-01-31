# SportsBetLang Architecture

## Overview
SportsBetLang is a domain-specific language plus analytics toolkit for sports betting workflows. The repository hosts two layers:

1. **Language runtime** (lexer → parser → AST → interpreter) for `.odds` scripts.
2. **Python analytics libraries** that provide betting math, sports models, and data utilities.

The runtime is intentionally lightweight and keeps execution in-process (no external code execution).

## Language Runtime Flow
1. **Lexer** (`lexer.py`) converts source text into tokens.
2. **Parser** (`parser.py`) builds an AST from tokens.
3. **Interpreter** (`interpreter.py`) evaluates the AST in a scoped environment with built-in betting functions.

Execution happens through the CLI (`sportsbetlang/cli.py`) or the legacy script entry point (`sportsbetlang.py`).

## Key Directories
- `lexer.py`, `parser.py`, `interpreter.py`: Core SportsBetLang runtime implementation.
- `sportsbetlang/`: Packaged Python API, CLI entry point, and core utilities.
- `lib/`: Domain-specific analytics libraries (odds conversion, model utilities, sport modules).
- `examples/`: Example scripts and Python demos.
- `tests/`: Unit tests and CLI smoke tests.

## Packaging & Entry Points
- `setup.py` and `pyproject.toml` define packaging metadata.
- `sportsbetlang` console script points to `sportsbetlang.cli:main`.
- `python -m sportsbetlang` invokes the same CLI.
