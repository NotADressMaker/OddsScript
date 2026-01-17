"""
Command-line tools for SportsBetLang.

Contains 18+ professional betting tools using BaseTool architecture:
- Odds Calculator (✓ refactored)
- Bet tracker (pending)
- Sharp money tracker (pending)
- Public fade calculator (pending)
- Parlay optimizer (pending)
- Arbitrage calculator (pending)
- Hedge calculator (pending)
- And many more...
"""

from sportsbetlang.tools.base_tool import BaseTool, cli_tool

__all__ = [
    'BaseTool',
    'cli_tool',
]
