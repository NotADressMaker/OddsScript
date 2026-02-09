"""
SportsBetLang Parser - Builds Abstract Syntax Tree from tokens
"""

from __future__ import annotations

from dataclasses import dataclass
from difflib import get_close_matches
from typing import Any, List, Optional

from sportsbetlang.lang.diagnostics import DiagnosticError
from sportsbetlang.lang.lexer import Token, TokenType, Lexer
from sportsbetlang.lang.limits import DEFAULT_LIMITS, RuntimeLimits


# AST Node Types
@dataclass
class ASTNode:
    pass


@dataclass
class Program(ASTNode):
    statements: List[ASTNode]


@dataclass
class NumberLiteral(ASTNode):
    value: float


@dataclass
class StringLiteral(ASTNode):
    value: str


@dataclass
class BooleanLiteral(ASTNode):
    value: bool


@dataclass
class Identifier(ASTNode):
    name: str


@dataclass
class BinaryOp(ASTNode):
    left: ASTNode
    operator: TokenType
    right: ASTNode


@dataclass
class UnaryOp(ASTNode):
    operator: TokenType
    operand: ASTNode


@dataclass
class Assignment(ASTNode):
    name: str
    value: ASTNode
    is_const: bool = False


@dataclass
class FunctionCall(ASTNode):
    name: str
    arguments: List[ASTNode]


@dataclass
class CallExpression(ASTNode):
    callee: ASTNode
    arguments: List[ASTNode]


@dataclass
class IfStatement(ASTNode):
    condition: ASTNode
    then_block: List[ASTNode]
    else_block: Optional[List[ASTNode]] = None


@dataclass
class WhileLoop(ASTNode):
    condition: ASTNode
    body: List[ASTNode]


@dataclass
class ForLoop(ASTNode):
    variable: str
    iterable: ASTNode
    body: List[ASTNode]


@dataclass
class FunctionDef(ASTNode):
    name: str
    parameters: List[str]
    body: List[ASTNode]


@dataclass
class ReturnStatement(ASTNode):
    value: Optional[ASTNode]


@dataclass
class ArrayLiteral(ASTNode):
    elements: List[ASTNode]


@dataclass
class DictLiteral(ASTNode):
    pairs: List[tuple[ASTNode, ASTNode]]


@dataclass
class IndexAccess(ASTNode):
    object: ASTNode
    index: ASTNode


@dataclass
class MemberAccess(ASTNode):
    object: ASTNode
    member: str


@dataclass
class BetStatement(ASTNode):
    bet_type: str
    team: ASTNode
    odds: ASTNode
    stake: ASTNode
    additional_params: dict


@dataclass
class ParlayStatement(ASTNode):
    bets: List[ASTNode]
    stake: ASTNode


@dataclass
class ImportStatement(ASTNode):
    module: str
    alias: Optional[str] = None


@dataclass
class FromImportStatement(ASTNode):
    module: str
    imports: List[tuple[str, Optional[str]]]


class Parser:
    KEYWORDS = sorted(Lexer.KEYWORDS.keys())

    def __init__(
        self,
        tokens: List[Token],
        source: str = "",
        limits: RuntimeLimits = DEFAULT_LIMITS,
    ) -> None:
        self.tokens = tokens
        self.pos = 0
        self.source = source
        self.limits = limits
        self.ast_nodes = 0

    def _track_node(self, node: ASTNode, token: Optional[Token] = None) -> ASTNode:
        self.ast_nodes += 1
        if self.ast_nodes > self.limits.max_ast_nodes:
            location = token or self.current_token()
            raise DiagnosticError(
                "AST node limit exceeded",
                location.line,
                location.column,
                self.source,
            )
        return node

    def current_token(self) -> Token:
        if self.pos >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[self.pos]

    def peek_token(self, offset: int = 1) -> Token:
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[pos]

    def advance(self) -> None:
        if self.pos < len(self.tokens) - 1:
            self.pos += 1

    def expect(self, token_type: TokenType) -> Token:
        token = self.current_token()
        if token.type != token_type:
            message = f"Expected {token_type.name}, got {token.type.name}"
            if token.type == TokenType.IDENTIFIER and token.value:
                suggestion = self._keyword_suggestion(token.value)
                if suggestion:
                    message = f"{message}. Did you mean '{suggestion}'?"
            raise DiagnosticError(message, token.line, token.column, self.source)
        self.advance()
        return token

    def error(self, message: str, token: Token) -> None:
        if token.type == TokenType.IDENTIFIER and token.value:
            suggestion = self._keyword_suggestion(token.value)
            if suggestion:
                message = f"{message}. Did you mean '{suggestion}'?"
        raise DiagnosticError(message, token.line, token.column, self.source)

    def _keyword_suggestion(self, identifier: str) -> Optional[str]:
        matches = get_close_matches(identifier, self.KEYWORDS, n=1, cutoff=0.8)
        return matches[0] if matches else None

    def skip_newlines(self) -> None:
        while self.current_token().type == TokenType.NEWLINE:
            self.advance()

    def parse(self) -> Program:
        statements: List[ASTNode] = []
        self.skip_newlines()

        while self.current_token().type != TokenType.EOF:
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()

        return self._track_node(Program(statements), self.current_token())

    def parse_statement(self) -> Optional[ASTNode]:
        self.skip_newlines()
        token = self.current_token()

        if token.type == TokenType.LET or token.type == TokenType.CONST:
            return self.parse_variable_declaration()
        elif token.type == TokenType.IF:
            return self.parse_if_statement()
        elif token.type == TokenType.WHILE:
            return self.parse_while_loop()
        elif token.type == TokenType.FOR:
            return self.parse_for_loop()
        elif token.type == TokenType.FUNC:
            return self.parse_function_def()
        elif token.type == TokenType.RETURN:
            return self.parse_return_statement()
        elif token.type == TokenType.BET:
            return self.parse_bet_statement()
        elif token.type == TokenType.PARLAY:
            return self.parse_parlay_statement()
        elif token.type == TokenType.IMPORT:
            return self.parse_import_statement()
        elif token.type == TokenType.FROM:
            return self.parse_from_import_statement()
        elif token.type == TokenType.PRINT:
            return self.parse_print_statement()
        elif token.type == TokenType.IDENTIFIER:
            suggestion = self._keyword_suggestion(token.value or "")
            if suggestion and self.peek_token().type != TokenType.ASSIGN:
                self.error(f"Unexpected identifier '{token.value}'", token)
            # Could be assignment or function call
            if self.peek_token().type == TokenType.ASSIGN:
                return self.parse_assignment()
            else:
                return self.parse_expression_statement()
        else:
            return self.parse_expression_statement()

    def parse_variable_declaration(self) -> Assignment:
        is_const = self.current_token().type == TokenType.CONST
        self.advance()  # skip let/const

        name_token = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.ASSIGN)
        value = self.parse_expression()

        return self._track_node(Assignment(name_token.value, value, is_const), name_token)

    def parse_assignment(self) -> Assignment:
        name_token = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.ASSIGN)
        value = self.parse_expression()

        return self._track_node(Assignment(name_token.value, value, False), name_token)

    def parse_if_statement(self) -> IfStatement:
        self.expect(TokenType.IF)
        condition = self.parse_expression()
        self.expect(TokenType.LBRACE)
        self.skip_newlines()

        then_block = []
        while self.current_token().type != TokenType.RBRACE:
            stmt = self.parse_statement()
            if stmt:
                then_block.append(stmt)
            self.skip_newlines()

        self.expect(TokenType.RBRACE)
        self.skip_newlines()

        else_block = None
        if self.current_token().type == TokenType.ELSE:
            self.advance()
            self.expect(TokenType.LBRACE)
            self.skip_newlines()

            else_block = []
            while self.current_token().type != TokenType.RBRACE:
                stmt = self.parse_statement()
                if stmt:
                    else_block.append(stmt)
                self.skip_newlines()

            self.expect(TokenType.RBRACE)

        return self._track_node(IfStatement(condition, then_block, else_block), self.current_token())

    def parse_while_loop(self) -> WhileLoop:
        self.expect(TokenType.WHILE)
        condition = self.parse_expression()
        self.expect(TokenType.LBRACE)
        self.skip_newlines()

        body = []
        while self.current_token().type != TokenType.RBRACE:
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
            self.skip_newlines()

        self.expect(TokenType.RBRACE)
        return self._track_node(WhileLoop(condition, body), self.current_token())

    def parse_for_loop(self) -> ForLoop:
        self.expect(TokenType.FOR)
        var_token = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.IN)
        iterable = self.parse_expression()
        self.expect(TokenType.LBRACE)
        self.skip_newlines()

        body = []
        while self.current_token().type != TokenType.RBRACE:
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
            self.skip_newlines()

        self.expect(TokenType.RBRACE)
        return self._track_node(ForLoop(var_token.value, iterable, body), var_token)

    def parse_function_def(self) -> FunctionDef:
        self.expect(TokenType.FUNC)
        name_token = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.LPAREN)

        parameters = []
        while self.current_token().type != TokenType.RPAREN:
            param_token = self.expect(TokenType.IDENTIFIER)
            parameters.append(param_token.value)

            if self.current_token().type == TokenType.COMMA:
                self.advance()

        self.expect(TokenType.RPAREN)
        self.expect(TokenType.LBRACE)
        self.skip_newlines()

        body = []
        while self.current_token().type != TokenType.RBRACE:
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
            self.skip_newlines()

        self.expect(TokenType.RBRACE)
        return self._track_node(FunctionDef(name_token.value, parameters, body), name_token)

    def parse_return_statement(self) -> ReturnStatement:
        self.expect(TokenType.RETURN)

        if self.current_token().type in [TokenType.NEWLINE, TokenType.RBRACE]:
            return self._track_node(ReturnStatement(None), self.current_token())

        value = self.parse_expression()
        return self._track_node(ReturnStatement(value), self.current_token())

    def parse_bet_statement(self) -> BetStatement:
        self.expect(TokenType.BET)

        bet_type = "moneyline"  # default
        if self.current_token().type in [TokenType.MONEYLINE, TokenType.SPREAD, TokenType.TOTAL]:
            bet_type = self.current_token().type.name.lower()
            self.advance()

        team = self.parse_expression()

        odds = None
        stake = None
        additional_params = {}

        # Parse optional parameters
        while self.current_token().type in [TokenType.ODDS, TokenType.STAKE, TokenType.SPREAD]:
            if self.current_token().type == TokenType.ODDS:
                self.advance()
                odds = self.parse_expression()
            elif self.current_token().type == TokenType.STAKE:
                self.advance()
                stake = self.parse_expression()
            elif self.current_token().type == TokenType.SPREAD:
                self.advance()
                additional_params['spread'] = self.parse_expression()

        return self._track_node(
            BetStatement(bet_type, team, odds, stake, additional_params),
            self.current_token(),
        )

    def parse_parlay_statement(self) -> ParlayStatement:
        self.expect(TokenType.PARLAY)
        self.expect(TokenType.LBRACKET)

        bets = []
        while self.current_token().type != TokenType.RBRACKET:
            bet = self.parse_expression()
            bets.append(bet)

            if self.current_token().type == TokenType.COMMA:
                self.advance()

        self.expect(TokenType.RBRACKET)

        stake = None
        if self.current_token().type == TokenType.STAKE:
            self.advance()
            stake = self.parse_expression()

        return self._track_node(ParlayStatement(bets, stake), self.current_token())

    def parse_module_path(self) -> str:
        if self.current_token().type == TokenType.STRING:
            token = self.current_token()
            self.advance()
            return token.value

        token = self.expect(TokenType.IDENTIFIER)
        parts = [token.value]
        while self.current_token().type == TokenType.DOT:
            self.advance()
            part_token = self.expect(TokenType.IDENTIFIER)
            parts.append(part_token.value)
        return ".".join(parts)

    def parse_import_statement(self) -> ImportStatement:
        import_token = self.expect(TokenType.IMPORT)
        module = self.parse_module_path()
        alias = None
        if self.current_token().type == TokenType.AS:
            self.advance()
            alias_token = self.expect(TokenType.IDENTIFIER)
            alias = alias_token.value
        return self._track_node(ImportStatement(module, alias), import_token)

    def parse_from_import_statement(self) -> FromImportStatement:
        from_token = self.expect(TokenType.FROM)
        module = self.parse_module_path()
        self.expect(TokenType.IMPORT)
        imports: List[tuple[str, Optional[str]]] = []
        while True:
            name_token = self.expect(TokenType.IDENTIFIER)
            alias = None
            if self.current_token().type == TokenType.AS:
                self.advance()
                alias_token = self.expect(TokenType.IDENTIFIER)
                alias = alias_token.value
            imports.append((name_token.value, alias))
            if self.current_token().type != TokenType.COMMA:
                break
            self.advance()
            if self.current_token().type in (TokenType.NEWLINE, TokenType.SEMICOLON, TokenType.EOF):
                break
        return self._track_node(FromImportStatement(module, imports), from_token)

    def parse_print_statement(self) -> FunctionCall:
        self.expect(TokenType.PRINT)
        self.expect(TokenType.LPAREN)

        args = []
        while self.current_token().type != TokenType.RPAREN:
            args.append(self.parse_expression())
            if self.current_token().type == TokenType.COMMA:
                self.advance()

        self.expect(TokenType.RPAREN)
        return self._track_node(FunctionCall("print", args), self.current_token())

    def parse_expression_statement(self) -> ASTNode:
        return self.parse_expression()

    def parse_expression(self) -> ASTNode:
        return self.parse_or_expression()

    def parse_or_expression(self) -> ASTNode:
        left = self.parse_and_expression()

        while self.current_token().type == TokenType.OR:
            op = self.current_token().type
            self.advance()
            right = self.parse_and_expression()
            left = self._track_node(BinaryOp(left, op, right), self.current_token())

        return left

    def parse_and_expression(self) -> ASTNode:
        left = self.parse_equality_expression()

        while self.current_token().type == TokenType.AND:
            op = self.current_token().type
            self.advance()
            right = self.parse_equality_expression()
            left = self._track_node(BinaryOp(left, op, right), self.current_token())

        return left

    def parse_equality_expression(self) -> ASTNode:
        left = self.parse_comparison_expression()

        while self.current_token().type in [TokenType.EQUAL, TokenType.NOT_EQUAL]:
            op = self.current_token().type
            self.advance()
            right = self.parse_comparison_expression()
            left = self._track_node(BinaryOp(left, op, right), self.current_token())

        return left

    def parse_comparison_expression(self) -> ASTNode:
        left = self.parse_additive_expression()

        while self.current_token().type in [TokenType.LESS_THAN, TokenType.GREATER_THAN,
                                             TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL]:
            op = self.current_token().type
            self.advance()
            right = self.parse_additive_expression()
            left = self._track_node(BinaryOp(left, op, right), self.current_token())

        return left

    def parse_additive_expression(self) -> ASTNode:
        left = self.parse_multiplicative_expression()

        while self.current_token().type in [TokenType.PLUS, TokenType.MINUS]:
            op = self.current_token().type
            self.advance()
            right = self.parse_multiplicative_expression()
            left = self._track_node(BinaryOp(left, op, right), self.current_token())

        return left

    def parse_multiplicative_expression(self) -> ASTNode:
        left = self.parse_unary_expression()

        while self.current_token().type in [TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO]:
            op = self.current_token().type
            self.advance()
            right = self.parse_unary_expression()
            left = BinaryOp(left, op, right)

        return left

    def parse_unary_expression(self) -> ASTNode:
        if self.current_token().type in [TokenType.MINUS, TokenType.NOT]:
            op = self.current_token().type
            self.advance()
            operand = self.parse_unary_expression()
            return self._track_node(UnaryOp(op, operand), self.current_token())

        return self.parse_postfix_expression()

    def parse_postfix_expression(self) -> ASTNode:
        left = self.parse_primary_expression()

        while True:
            if self.current_token().type == TokenType.LPAREN:
                # Function call
                self.advance()
                args = []

                while self.current_token().type != TokenType.RPAREN:
                    args.append(self.parse_expression())
                    if self.current_token().type == TokenType.COMMA:
                        self.advance()

                self.expect(TokenType.RPAREN)

                if isinstance(left, Identifier):
                    left = self._track_node(FunctionCall(left.name, args), self.current_token())
                else:
                    left = self._track_node(CallExpression(left, args), self.current_token())

            elif self.current_token().type == TokenType.LBRACKET:
                # Index access
                self.advance()
                index = self.parse_expression()
                self.expect(TokenType.RBRACKET)
                left = self._track_node(IndexAccess(left, index), self.current_token())

            elif self.current_token().type == TokenType.DOT:
                # Member access
                self.advance()
                member_token = self.expect(TokenType.IDENTIFIER)
                left = self._track_node(MemberAccess(left, member_token.value), member_token)

            else:
                break

        return left

    def parse_primary_expression(self) -> ASTNode:
        token = self.current_token()

        if token.type == TokenType.NUMBER:
            self.advance()
            return self._track_node(NumberLiteral(token.value), token)

        elif token.type == TokenType.STRING:
            self.advance()
            return self._track_node(StringLiteral(token.value), token)

        elif token.type in [TokenType.TRUE, TokenType.FALSE]:
            self.advance()
            return self._track_node(BooleanLiteral(token.type == TokenType.TRUE), token)

        elif token.type == TokenType.IDENTIFIER:
            self.advance()
            return self._track_node(Identifier(token.value), token)

        elif token.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr

        elif token.type == TokenType.LBRACKET:
            return self.parse_array_literal()

        elif token.type == TokenType.LBRACE:
            return self.parse_dict_literal()

        else:
            self.error(f"Unexpected token {token.type.name}", token)

    def parse_array_literal(self) -> ArrayLiteral:
        self.expect(TokenType.LBRACKET)
        elements = []

        while self.current_token().type != TokenType.RBRACKET:
            elements.append(self.parse_expression())
            if self.current_token().type == TokenType.COMMA:
                self.advance()

        self.expect(TokenType.RBRACKET)
        return self._track_node(ArrayLiteral(elements), self.current_token())

    def parse_dict_literal(self) -> DictLiteral:
        self.expect(TokenType.LBRACE)
        pairs = []

        while self.current_token().type != TokenType.RBRACE:
            key = self.parse_expression()
            self.expect(TokenType.COLON)
            value = self.parse_expression()
            pairs.append((key, value))

            if self.current_token().type == TokenType.COMMA:
                self.advance()

        self.expect(TokenType.RBRACE)
        return self._track_node(DictLiteral(pairs), self.current_token())
