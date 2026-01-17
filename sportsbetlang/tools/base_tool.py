"""
Base class for all SportsBetLang CLI tools.

Provides common functionality to reduce code duplication across 18+ tools:
- Argument parsing patterns
- Configuration access
- Storage access
- Error handling
- Output formatting (text, JSON, CSV)
- Common CLI arguments
"""

import argparse
import sys
import json
import csv
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pathlib import Path

from sportsbetlang.config import get_config
from sportsbetlang.data.storage import create_storage
from sportsbetlang.common.validators import ValidationError


class BaseTool(ABC):
    """Abstract base class for all CLI tools"""

    def __init__(self, name: str, description: str):
        """
        Initialize base tool

        Args:
            name: Tool name (e.g., 'bet-tracker', 'sharp-tracker')
            description: Tool description for help text
        """
        self.name = name
        self.description = description
        self.config = get_config()
        self.storage = None  # Lazy initialization
        self.parser = self._create_base_parser()

    def _create_base_parser(self) -> argparse.ArgumentParser:
        """Create argument parser with common arguments"""
        parser = argparse.ArgumentParser(
            prog=self.name,
            description=self.description,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        # Common arguments for all tools
        parser.add_argument(
            '--config',
            type=str,
            metavar='PATH',
            help='Path to configuration file'
        )

        parser.add_argument(
            '--output-format',
            choices=['text', 'json', 'csv'],
            default='text',
            metavar='FORMAT',
            help='Output format: text, json, or csv (default: text)'
        )

        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Verbose output with additional details'
        )

        parser.add_argument(
            '--quiet', '-q',
            action='store_true',
            help='Suppress non-essential output'
        )

        parser.add_argument(
            '--no-color',
            action='store_true',
            help='Disable colored output'
        )

        return parser

    @abstractmethod
    def add_arguments(self, parser: argparse.ArgumentParser):
        """
        Add tool-specific arguments (implement in subclass)

        Args:
            parser: ArgumentParser to add arguments to

        Example:
            def add_arguments(self, parser):
                parser.add_argument('--sport', required=True)
                parser.add_argument('--odds', type=float)
        """
        pass

    @abstractmethod
    def run(self, args: argparse.Namespace) -> int:
        """
        Run tool logic (implement in subclass)

        Args:
            args: Parsed command-line arguments

        Returns:
            Exit code (0 for success, non-zero for error)

        Example:
            def run(self, args):
                result = self.do_calculation(args.odds)
                self.print_output(result, args.output_format)
                return 0
        """
        pass

    def main(self, argv: Optional[List[str]] = None) -> int:
        """
        Main entry point for tool

        Args:
            argv: Command-line arguments (defaults to sys.argv)

        Returns:
            Exit code
        """
        # Add tool-specific arguments
        self.add_arguments(self.parser)

        # Parse arguments
        try:
            args = self.parser.parse_args(argv)
        except SystemExit as e:
            return e.code if isinstance(e.code, int) else 1

        # Load custom config if specified
        if hasattr(args, 'config') and args.config:
            from sportsbetlang.config import SportsBetLangConfig, set_config
            try:
                config = SportsBetLangConfig.load_from_file(Path(args.config))
                set_config(config)
                self.config = config
            except Exception as e:
                self.print_error(f"Failed to load config file: {e}")
                return 1

        # Initialize storage if not already done
        if self.storage is None:
            self.storage = create_storage(self.config.storage_backend)

        # Run tool
        try:
            return self.run(args)

        except ValidationError as e:
            self.print_error(f"Validation Error: {e}")
            if hasattr(args, 'verbose') and args.verbose:
                import traceback
                traceback.print_exc()
            return 1

        except KeyboardInterrupt:
            if not (hasattr(args, 'quiet') and args.quiet):
                self.print_error("\nInterrupted by user")
            return 130

        except Exception as e:
            self.print_error(f"Error: {e}")
            if hasattr(args, 'verbose') and args.verbose:
                import traceback
                traceback.print_exc()
            return 1

    # ===== Output Methods =====

    def print_output(self, data: Any, format: str = 'text'):
        """
        Print output in specified format

        Args:
            data: Data to output (dict, list, or string)
            format: Output format ('text', 'json', 'csv')
        """
        if format == 'json':
            self._print_json(data)
        elif format == 'csv':
            self._print_csv(data)
        else:
            self._print_text(data)

    def _print_text(self, data: Any):
        """Print in human-readable text format"""
        if isinstance(data, str):
            print(data)
        elif isinstance(data, dict):
            for key, value in data.items():
                print(f"{key}: {value}")
        elif isinstance(data, list):
            for item in data:
                print(item)
        else:
            print(data)

    def _print_json(self, data: Any):
        """Print in JSON format"""
        print(json.dumps(data, indent=2, default=str))

    def _print_csv(self, data: Any):
        """Print in CSV format"""
        if isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], dict):
                # List of dictionaries
                writer = csv.DictWriter(sys.stdout, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            else:
                # List of values
                writer = csv.writer(sys.stdout)
                for item in data:
                    writer.writerow([item])
        elif isinstance(data, dict):
            # Single dictionary
            writer = csv.DictWriter(sys.stdout, fieldnames=data.keys())
            writer.writeheader()
            writer.writerow(data)
        else:
            print(data)

    def print_error(self, message: str):
        """Print error message to stderr"""
        print(f"❌ {message}", file=sys.stderr)

    def print_success(self, message: str):
        """Print success message"""
        print(f"✅ {message}")

    def print_warning(self, message: str):
        """Print warning message"""
        print(f"⚠️  {message}")

    def print_info(self, message: str):
        """Print info message"""
        print(f"ℹ️  {message}")

    # ===== Formatting Helpers =====

    def format_odds(self, odds: float) -> str:
        """
        Format odds for display

        Args:
            odds: American odds

        Returns:
            Formatted string (e.g., "-110", "+150")
        """
        if odds > 0:
            return f"+{odds:.0f}"
        else:
            return f"{odds:.0f}"

    def format_percentage(self, value: float) -> str:
        """
        Format percentage for display

        Args:
            value: Decimal value (0.55 = 55%)

        Returns:
            Formatted percentage string
        """
        return f"{value * 100:.{self.config.decimal_places}f}%"

    def format_currency(self, value: float, symbol: str = '$') -> str:
        """
        Format currency for display

        Args:
            value: Currency value
            symbol: Currency symbol

        Returns:
            Formatted currency string
        """
        if value >= 0:
            return f"{symbol}{value:.{self.config.decimal_places}f}"
        else:
            return f"-{symbol}{abs(value):.{self.config.decimal_places}f}"

    def format_probability(self, value: float) -> str:
        """Format probability (0-1) as percentage"""
        return self.format_percentage(value)

    # ===== Table Formatting =====

    def print_table(self, headers: List[str], rows: List[List[Any]], title: Optional[str] = None):
        """
        Print formatted table

        Args:
            headers: Column headers
            rows: Table rows
            title: Optional table title
        """
        if title:
            print(f"\n{title}")
            print("=" * len(title))

        # Calculate column widths
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))

        # Print header
        header_row = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
        print(header_row)
        print("-" * len(header_row))

        # Print rows
        for row in rows:
            print(" | ".join(str(cell).ljust(w) for cell, w in zip(row, col_widths)))

        print()

    # ===== Validation Helpers =====

    def validate_odds(self, odds: float) -> float:
        """Validate odds using common validator"""
        from sportsbetlang.common.validators import validate_odds
        return validate_odds(odds)

    def validate_probability(self, prob: float) -> float:
        """Validate probability using common validator"""
        from sportsbetlang.common.validators import validate_probability
        return validate_probability(prob)

    def validate_stake(self, stake: float) -> float:
        """Validate stake using common validator"""
        from sportsbetlang.common.validators import validate_stake
        return validate_stake(stake)

    def validate_bankroll(self, bankroll: float) -> float:
        """Validate bankroll using common validator"""
        from sportsbetlang.common.validators import validate_bankroll
        return validate_bankroll(bankroll)

    # ===== Convenience Methods =====

    def get_storage(self):
        """Get storage backend (lazy initialization)"""
        if self.storage is None:
            self.storage = create_storage(self.config.storage_backend)
        return self.storage

    def confirm(self, message: str, default: bool = False) -> bool:
        """
        Ask user for confirmation

        Args:
            message: Confirmation message
            default: Default value if user just presses Enter

        Returns:
            True if confirmed, False otherwise
        """
        suffix = " [Y/n]: " if default else " [y/N]: "
        response = input(message + suffix).strip().lower()

        if not response:
            return default

        return response in ['y', 'yes']


# ===== Decorator for easy tool creation =====

def cli_tool(name: str, description: str):
    """
    Decorator to create a CLI tool from a class

    Usage:
        @cli_tool('my-tool', 'Does something cool')
        class MyTool(BaseTool):
            def add_arguments(self, parser):
                parser.add_argument('--foo')

            def run(self, args):
                print(f"Foo: {args.foo}")
                return 0

        if __name__ == '__main__':
            sys.exit(MyTool().main())
    """
    def decorator(cls):
        # Set name and description as class attributes
        cls._tool_name = name
        cls._tool_description = description

        # Override __init__ to use decorator values
        original_init = cls.__init__

        def new_init(self, *args, **kwargs):
            BaseTool.__init__(self, cls._tool_name, cls._tool_description)
            if original_init != BaseTool.__init__:
                original_init(self, *args, **kwargs)

        cls.__init__ = new_init
        return cls

    return decorator
