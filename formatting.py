"""
Simple formatter for SportsBetLang source code.
"""

from __future__ import annotations

from typing import Optional


OPERATORS = {
    "==",
    "!=",
    "<=",
    ">=",
    "+",
    "-",
    "*",
    "/",
    "%",
    "<",
    ">",
    "=",
}
KEYWORD_OPERATORS = {"and", "or", "not"}


def _split_comment(line: str) -> tuple[str, Optional[str]]:
    in_string = False
    quote_char = ""
    escaped = False
    for idx, ch in enumerate(line):
        if in_string:
            if escaped:
                escaped = False
                continue
            if ch == "\\":
                escaped = True
                continue
            if ch == quote_char:
                in_string = False
                quote_char = ""
        else:
            if ch in ("'", '"'):
                in_string = True
                quote_char = ch
            elif ch == "#":
                return line[:idx].rstrip(), line[idx:].rstrip()
    return line.rstrip(), None


def _tokenize_line(code: str) -> list[str]:
    tokens: list[str] = []
    i = 0
    length = len(code)
    while i < length:
        ch = code[i]
        if ch.isspace():
            i += 1
            continue
        if ch in ("'", '"'):
            quote = ch
            value = ch
            i += 1
            escaped = False
            while i < length:
                value += code[i]
                if escaped:
                    escaped = False
                elif code[i] == "\\":
                    escaped = True
                elif code[i] == quote:
                    i += 1
                    break
                i += 1
            tokens.append(value)
            continue
        if ch.isdigit():
            value = ch
            i += 1
            has_dot = False
            while i < length and (code[i].isdigit() or (code[i] == "." and not has_dot)):
                if code[i] == ".":
                    has_dot = True
                value += code[i]
                i += 1
            tokens.append(value)
            continue
        if ch.isalpha() or ch == "_":
            value = ch
            i += 1
            while i < length and (code[i].isalnum() or code[i] == "_"):
                value += code[i]
                i += 1
            tokens.append(value)
            continue

        if i + 1 < length and code[i : i + 2] in {"==", "!=", "<=", ">=", "->"}:
            tokens.append(code[i : i + 2])
            i += 2
            continue

        tokens.append(ch)
        i += 1
    return tokens


def _is_number(token: str) -> bool:
    if not token:
        return False
    if token.count(".") > 1:
        return False
    return token.replace(".", "", 1).isdigit()


def _is_word(token: str) -> bool:
    if not token:
        return False
    if token[0] in ("'", '"'):
        return True
    return token[0].isalnum() or token[0] == "_"


def _is_unary_minus(prev: Optional[str], next_token: Optional[str]) -> bool:
    if next_token is None or not _is_number(next_token):
        return False
    if prev is None:
        return True
    if prev in OPERATORS or prev in KEYWORD_OPERATORS:
        return True
    if prev in {
        "(",
        "[",
        "{",
        ",",
        ":",
        "=",
        "return",
        "let",
        "const",
        "bet",
        "parlay",
        "odds",
        "stake",
        "spread",
    }:
        return True
    if prev in {"if", "while", "for", "in"}:
        return True
    return False


def _needs_space_before(current: str, prev: Optional[str]) -> bool:
    if prev is None:
        return False
    if current in {")", "]", "}", ",", ".", ":", ";"}:
        return False
    if prev in {"(", "[", "{", "."}:
        return False
    if current in {"(", "["}:
        return prev in {"if", "while", "for"}
    if current == "{":
        return prev not in {"(", "[", "{", "."}
    if current in OPERATORS or prev in OPERATORS or current in KEYWORD_OPERATORS or prev in KEYWORD_OPERATORS:
        return True
    if _is_word(prev) and _is_word(current):
        return True
    return False


def _format_code_line(code: str) -> str:
    tokens = _tokenize_line(code)
    output = []
    i = 0
    prev_token: Optional[str] = None
    while i < len(tokens):
        token = tokens[i]
        next_token = tokens[i + 1] if i + 1 < len(tokens) else None
        if token == "-" and _is_unary_minus(prev_token, next_token):
            token = f"-{next_token}"
            i += 2
        else:
            i += 1

        if _needs_space_before(token, prev_token):
            output.append(" ")
        output.append(token)
        if token in {",", ";", ":"}:
            if i < len(tokens) and tokens[i] not in {")", "]", "}", ",", ";"}:
                output.append(" ")
        prev_token = token
    return "".join(output).strip()


def _count_braces(code: str) -> tuple[int, int]:
    open_count = 0
    close_count = 0
    in_string = False
    quote_char = ""
    escaped = False
    for ch in code:
        if in_string:
            if escaped:
                escaped = False
                continue
            if ch == "\\":
                escaped = True
                continue
            if ch == quote_char:
                in_string = False
                quote_char = ""
            continue
        if ch in ("'", '"'):
            in_string = True
            quote_char = ch
            continue
        if ch == "{":
            open_count += 1
        elif ch == "}":
            close_count += 1
    return open_count, close_count


def format_source(source: str, indent_width: int = 4) -> str:
    lines = source.splitlines()
    formatted_lines: list[str] = []
    indent = 0
    trailing_newline = source.endswith("\n")

    for line in lines:
        code, comment = _split_comment(line)
        stripped = code.strip()
        if not stripped:
            if comment:
                formatted_lines.append(" " * (indent * indent_width) + comment)
            else:
                formatted_lines.append("")
            continue

        leading_close = stripped.startswith("}")
        if leading_close:
            indent = max(indent - 1, 0)

        formatted_code = _format_code_line(stripped)
        formatted_line = " " * (indent * indent_width) + formatted_code
        if comment:
            formatted_line += " " + comment
        formatted_lines.append(formatted_line)

        open_count, close_count = _count_braces(stripped)
        adjust = open_count - close_count + (1 if leading_close else 0)
        indent = max(indent + adjust, 0)

    result = "\n".join(formatted_lines)
    if trailing_newline:
        result += "\n"
    return result
