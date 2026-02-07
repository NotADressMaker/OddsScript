"""
SportsBetLang Lexer - Tokenizes source code for the sports betting language
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional

from diagnostics import DiagnosticError

class TokenType(Enum):
    # Literals
    NUMBER = auto()
    STRING = auto()
    TRUE = auto()
    FALSE = auto()

    # Identifiers and keywords
    IDENTIFIER = auto()
    BET = auto()
    BANKROLL = auto()
    ODDS = auto()
    STAKE = auto()
    PARLAY = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    IN = auto()
    FUNC = auto()
    RETURN = auto()
    LET = auto()
    CONST = auto()
    PRINT = auto()
    IMPORT = auto()
    FROM = auto()
    AS = auto()

    # Betting specific
    TEAM = auto()
    GAME = auto()
    OVER = auto()
    UNDER = auto()
    SPREAD = auto()
    MONEYLINE = auto()
    TOTAL = auto()
    CALCULATE = auto()
    KELLY = auto()
    EV = auto()
    IMPLIED = auto()
    PROBABILITY = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    MODULO = auto()
    ASSIGN = auto()
    EQUAL = auto()
    NOT_EQUAL = auto()
    LESS_THAN = auto()
    GREATER_THAN = auto()
    LESS_EQUAL = auto()
    GREATER_EQUAL = auto()
    AND = auto()
    OR = auto()
    NOT = auto()

    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    DOT = auto()
    COLON = auto()
    SEMICOLON = auto()
    ARROW = auto()

    # Special
    EOF = auto()
    NEWLINE = auto()


@dataclass
class Token:
    type: TokenType
    value: any
    line: int
    column: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value}, {self.line}:{self.column})"


class Lexer:
    KEYWORDS = {
        'bet': TokenType.BET,
        'odds': TokenType.ODDS,
        'stake': TokenType.STAKE,
        'parlay': TokenType.PARLAY,
        'if': TokenType.IF,
        'else': TokenType.ELSE,
        'while': TokenType.WHILE,
        'for': TokenType.FOR,
        'in': TokenType.IN,
        'func': TokenType.FUNC,
        'return': TokenType.RETURN,
        'let': TokenType.LET,
        'const': TokenType.CONST,
        'print': TokenType.PRINT,
        'import': TokenType.IMPORT,
        'from': TokenType.FROM,
        'as': TokenType.AS,
        'spread': TokenType.SPREAD,
        'moneyline': TokenType.MONEYLINE,
        'total': TokenType.TOTAL,
        'true': TokenType.TRUE,
        'false': TokenType.FALSE,
        'and': TokenType.AND,
        'or': TokenType.OR,
        'not': TokenType.NOT,
    }

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []

    def current_char(self) -> Optional[str]:
        if self.pos >= len(self.source):
            return None
        return self.source[self.pos]

    def peek_char(self, offset=1) -> Optional[str]:
        pos = self.pos + offset
        if pos >= len(self.source):
            return None
        return self.source[pos]

    def advance(self):
        if self.pos < len(self.source):
            if self.source[self.pos] == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.pos += 1

    def skip_whitespace(self):
        while self.current_char() and self.current_char() in ' \t\r':
            self.advance()

    def skip_comment(self):
        if self.current_char() == '#':
            while self.current_char() and self.current_char() != '\n':
                self.advance()

    def read_number(self) -> Token:
        start_line, start_col = self.line, self.column
        num_str = ''
        has_dot = False

        while self.current_char() and (self.current_char().isdigit() or self.current_char() == '.'):
            if self.current_char() == '.':
                if has_dot:
                    break
                has_dot = True
            num_str += self.current_char()
            self.advance()

        value = float(num_str) if has_dot else int(num_str)
        return Token(TokenType.NUMBER, value, start_line, start_col)

    def read_string(self) -> Token:
        start_line, start_col = self.line, self.column
        quote_char = self.current_char()
        self.advance()  # Skip opening quote

        string_val = ''
        while self.current_char() and self.current_char() != quote_char:
            if self.current_char() == '\\':
                self.advance()
                if self.current_char() == 'n':
                    string_val += '\n'
                elif self.current_char() == 't':
                    string_val += '\t'
                elif self.current_char() == '\\':
                    string_val += '\\'
                elif self.current_char() == quote_char:
                    string_val += quote_char
                else:
                    string_val += self.current_char()
                self.advance()
            else:
                string_val += self.current_char()
                self.advance()

        if self.current_char() != quote_char:
            raise DiagnosticError(
                "Unterminated string literal",
                start_line,
                start_col,
                self.source,
            )

        self.advance()  # Skip closing quote
        return Token(TokenType.STRING, string_val, start_line, start_col)

    def read_identifier(self) -> Token:
        start_line, start_col = self.line, self.column
        identifier = ''

        while self.current_char() and (self.current_char().isalnum() or self.current_char() == '_'):
            identifier += self.current_char()
            self.advance()

        token_type = self.KEYWORDS.get(identifier, TokenType.IDENTIFIER)
        value = identifier if token_type == TokenType.IDENTIFIER else None

        return Token(token_type, value, start_line, start_col)

    def tokenize(self) -> List[Token]:
        while self.current_char():
            self.skip_whitespace()

            if not self.current_char():
                break

            # Comments
            if self.current_char() == '#':
                self.skip_comment()
                continue

            # Newlines
            if self.current_char() == '\n':
                token = Token(TokenType.NEWLINE, None, self.line, self.column)
                self.tokens.append(token)
                self.advance()
                continue

            # Numbers
            if self.current_char().isdigit():
                self.tokens.append(self.read_number())
                continue

            # Strings
            if self.current_char() in '"\'':
                self.tokens.append(self.read_string())
                continue

            # Identifiers and keywords
            if self.current_char().isalpha() or self.current_char() == '_':
                self.tokens.append(self.read_identifier())
                continue

            # Two-character operators
            start_line, start_col = self.line, self.column
            current = self.current_char()
            next_char = self.peek_char()

            if current == '=' and next_char == '=':
                self.tokens.append(Token(TokenType.EQUAL, None, start_line, start_col))
                self.advance()
                self.advance()
                continue

            if current == '!' and next_char == '=':
                self.tokens.append(Token(TokenType.NOT_EQUAL, None, start_line, start_col))
                self.advance()
                self.advance()
                continue

            if current == '<' and next_char == '=':
                self.tokens.append(Token(TokenType.LESS_EQUAL, None, start_line, start_col))
                self.advance()
                self.advance()
                continue

            if current == '>' and next_char == '=':
                self.tokens.append(Token(TokenType.GREATER_EQUAL, None, start_line, start_col))
                self.advance()
                self.advance()
                continue

            if current == '-' and next_char == '>':
                self.tokens.append(Token(TokenType.ARROW, None, start_line, start_col))
                self.advance()
                self.advance()
                continue

            # Single-character tokens
            single_char_tokens = {
                '+': TokenType.PLUS,
                '-': TokenType.MINUS,
                '*': TokenType.MULTIPLY,
                '/': TokenType.DIVIDE,
                '%': TokenType.MODULO,
                '=': TokenType.ASSIGN,
                '<': TokenType.LESS_THAN,
                '>': TokenType.GREATER_THAN,
                '(': TokenType.LPAREN,
                ')': TokenType.RPAREN,
                '{': TokenType.LBRACE,
                '}': TokenType.RBRACE,
                '[': TokenType.LBRACKET,
                ']': TokenType.RBRACKET,
                ',': TokenType.COMMA,
                '.': TokenType.DOT,
                ':': TokenType.COLON,
                ';': TokenType.SEMICOLON,
            }

            if current in single_char_tokens:
                self.tokens.append(Token(single_char_tokens[current], None, start_line, start_col))
                self.advance()
                continue

            raise DiagnosticError(
                f"Unexpected character '{current}'",
                self.line,
                self.column,
                self.source,
            )

        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens
