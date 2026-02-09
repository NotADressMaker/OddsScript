"""
Diagnostics helpers for SportsBetLang syntax errors (core package).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


def _caret_column(line: str, column: int, tab_width: int = 4) -> int:
    if column <= 1:
        return 1
    caret = 1
    for ch in line[: column - 1]:
        if ch == "\t":
            caret += tab_width - ((caret - 1) % tab_width)
        else:
            caret += 1
    return caret


def format_snippet(source: str, line: Optional[int], column: Optional[int]) -> str:
    if not source or line is None or column is None:
        return ""
    lines = source.splitlines()
    if line < 1 or line > len(lines):
        return ""
    raw_line = lines[line - 1]
    expanded_line = raw_line.expandtabs(4)
    caret_column = _caret_column(raw_line, column)
    caret_line = " " * (max(caret_column - 1, 0)) + "^"
    return f"{expanded_line}\n{caret_line}"


@dataclass
class DiagnosticError(SyntaxError):
    message: str
    line: Optional[int]
    column: Optional[int]
    source: Optional[str] = None

    def format(self) -> str:
        details = self.message
        if self.line is not None and self.column is not None:
            details = f"{details} (line {self.line}, column {self.column})"
        snippet = format_snippet(self.source or "", self.line, self.column)
        if snippet:
            details = f"{details}\n{snippet}"
        return details

    def __str__(self) -> str:
        return self.format()
