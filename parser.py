"""
SportsBetLang Parser - Builds Abstract Syntax Tree from tokens
"""

from dataclasses import dataclass
from typing import List, Optional, Any
from lexer import Token, TokenType, Lexer


# AST Node Types
@dataclass
class ASTNode:
    line: Optional[int] = None
    column: Optional[int] = None


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
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current_token(self) -> Token:
        if self.pos >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[self.pos]

    def peek_token(self, offset=1) -> Token:
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[pos]

    def advance(self):
        if self.pos < len(self.tokens) - 1:
            self.pos += 1

    def expect(self, token_type: TokenType) -> Token:
        token = self.current_token()
        if token.type != token_type:
            raise SyntaxError(f"Expected {token_type.name}, got {token.type.name} at {token.line}:{token.column}")
        self.advance()
        return token

    def skip_newlines(self):
        while self.current_token().type == TokenType.NEWLINE:
            self.advance()

    def parse(self) -> Program:
        statements = []
        self.skip_newlines()

        while self.current_token().type != TokenType.EOF:
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()

        return Program(statements)

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
        elif token.type == TokenType.PRINT:
            return self.parse_print_statement()
        elif token.type == TokenType.IMPORT:
            return self.parse_import_statement()
        elif token.type == TokenType.FROM:
            return self.parse_from_import_statement()
        elif token.type == TokenType.IDENTIFIER:
            # Could be assignment or function call
            if self.peek_token().type == TokenType.ASSIGN:
                return self.parse_assignment()
            else:
                return self.parse_expression_statement()
        else:
            return self.parse_expression_statement()

    def with_span(self, node: ASTNode, token: Token) -> ASTNode:
        node.line = token.line
        node.column = token.column
        return node

    def parse_variable_declaration(self) -> Assignment:
        is_const = self.current_token().type == TokenType.CONST
        self.advance()  # skip let/const

        name_token = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.ASSIGN)
        value = self.parse_expression()

        return self.with_span(Assignment(name_token.value, value, is_const), name_token)

    def parse_assignment(self) -> Assignment:
        name_token = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.ASSIGN)
        value = self.parse_expression()

        return self.with_span(Assignment(name_token.value, value, False), name_token)

    def parse_if_statement(self) -> IfStatement:
        if_token = self.expect(TokenType.IF)
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

        return self.with_span(IfStatement(condition, then_block, else_block), if_token)

    def parse_while_loop(self) -> WhileLoop:
        while_token = self.expect(TokenType.WHILE)
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
        return self.with_span(WhileLoop(condition, body), while_token)

    def parse_for_loop(self) -> ForLoop:
        for_token = self.expect(TokenType.FOR)
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
        return self.with_span(ForLoop(var_token.value, iterable, body), for_token)

    def parse_function_def(self) -> FunctionDef:
        func_token = self.expect(TokenType.FUNC)
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
        return self.with_span(FunctionDef(name_token.value, parameters, body), func_token)

    def parse_return_statement(self) -> ReturnStatement:
        return_token = self.expect(TokenType.RETURN)

        if self.current_token().type in [TokenType.NEWLINE, TokenType.RBRACE]:
            return self.with_span(ReturnStatement(None), return_token)

        value = self.parse_expression()
        return self.with_span(ReturnStatement(value), return_token)

    def parse_bet_statement(self) -> BetStatement:
        bet_token = self.expect(TokenType.BET)

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

        return self.with_span(BetStatement(bet_type, team, odds, stake, additional_params), bet_token)

    def parse_parlay_statement(self) -> ParlayStatement:
        parlay_token = self.expect(TokenType.PARLAY)
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

        return self.with_span(ParlayStatement(bets, stake), parlay_token)

    def parse_print_statement(self) -> FunctionCall:
        print_token = self.expect(TokenType.PRINT)
        self.expect(TokenType.LPAREN)

        args = []
        while self.current_token().type != TokenType.RPAREN:
            args.append(self.parse_expression())
            if self.current_token().type == TokenType.COMMA:
                self.advance()

        self.expect(TokenType.RPAREN)
        return self.with_span(FunctionCall('print', args), print_token)

    def parse_expression_statement(self) -> ASTNode:
        return self.parse_expression()

    def parse_expression(self) -> ASTNode:
        return self.parse_or_expression()

    def parse_or_expression(self) -> ASTNode:
        left = self.parse_and_expression()

        while self.current_token().type == TokenType.OR:
            op_token = self.current_token()
            op = op_token.type
            self.advance()
            right = self.parse_and_expression()
            left = self.with_span(BinaryOp(left, op, right), op_token)

        return left

    def parse_and_expression(self) -> ASTNode:
        left = self.parse_equality_expression()

        while self.current_token().type == TokenType.AND:
            op_token = self.current_token()
            op = op_token.type
            self.advance()
            right = self.parse_equality_expression()
            left = self.with_span(BinaryOp(left, op, right), op_token)

        return left

    def parse_equality_expression(self) -> ASTNode:
        left = self.parse_comparison_expression()

        while self.current_token().type in [TokenType.EQUAL, TokenType.NOT_EQUAL]:
            op_token = self.current_token()
            op = op_token.type
            self.advance()
            right = self.parse_comparison_expression()
            left = self.with_span(BinaryOp(left, op, right), op_token)

        return left

    def parse_comparison_expression(self) -> ASTNode:
        left = self.parse_additive_expression()

        while self.current_token().type in [TokenType.LESS_THAN, TokenType.GREATER_THAN,
                                             TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL]:
            op_token = self.current_token()
            op = op_token.type
            self.advance()
            right = self.parse_additive_expression()
            left = self.with_span(BinaryOp(left, op, right), op_token)

        return left

    def parse_additive_expression(self) -> ASTNode:
        left = self.parse_multiplicative_expression()

        while self.current_token().type in [TokenType.PLUS, TokenType.MINUS]:
            op_token = self.current_token()
            op = op_token.type
            self.advance()
            right = self.parse_multiplicative_expression()
            left = self.with_span(BinaryOp(left, op, right), op_token)

        return left

    def parse_multiplicative_expression(self) -> ASTNode:
        left = self.parse_unary_expression()

        while self.current_token().type in [TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO]:
            op_token = self.current_token()
            op = op_token.type
            self.advance()
            right = self.parse_unary_expression()
            left = self.with_span(BinaryOp(left, op, right), op_token)

        return left

    def parse_unary_expression(self) -> ASTNode:
        if self.current_token().type in [TokenType.MINUS, TokenType.NOT]:
            op_token = self.current_token()
            op = op_token.type
            self.advance()
            operand = self.parse_unary_expression()
            return self.with_span(UnaryOp(op, operand), op_token)

        return self.parse_postfix_expression()

    def parse_postfix_expression(self) -> ASTNode:
        left = self.parse_primary_expression()

        while True:
            if self.current_token().type == TokenType.LPAREN:
                # Function call
                call_token = self.current_token()
                self.advance()
                args = []

                while self.current_token().type != TokenType.RPAREN:
                    args.append(self.parse_expression())
                    if self.current_token().type == TokenType.COMMA:
                        self.advance()

                self.expect(TokenType.RPAREN)

                if isinstance(left, Identifier):
                    left = self.with_span(FunctionCall(left.name, args), call_token)
                else:
                    left = self.with_span(CallExpression(left, args), call_token)

            elif self.current_token().type == TokenType.LBRACKET:
                # Index access
                bracket_token = self.current_token()
                self.advance()
                index = self.parse_expression()
                self.expect(TokenType.RBRACKET)
                left = self.with_span(IndexAccess(left, index), bracket_token)

            elif self.current_token().type == TokenType.DOT:
                # Member access
                self.advance()
                member_token = self.expect(TokenType.IDENTIFIER)
                left = self.with_span(MemberAccess(left, member_token.value), member_token)

            else:
                break

        return left

    def parse_primary_expression(self) -> ASTNode:
        token = self.current_token()

        if token.type == TokenType.NUMBER:
            self.advance()
            return self.with_span(NumberLiteral(token.value), token)

        elif token.type == TokenType.STRING:
            self.advance()
            return self.with_span(StringLiteral(token.value), token)

        elif token.type in [TokenType.TRUE, TokenType.FALSE]:
            self.advance()
            return self.with_span(BooleanLiteral(token.type == TokenType.TRUE), token)

        elif token.type == TokenType.IDENTIFIER:
            self.advance()
            return self.with_span(Identifier(token.value), token)

        elif token.type == TokenType.LPAREN:
            lparen_token = self.current_token()
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return self.with_span(expr, lparen_token)

        elif token.type == TokenType.LBRACKET:
            return self.parse_array_literal()

        elif token.type == TokenType.LBRACE:
            return self.parse_dict_literal()

        else:
            raise SyntaxError(f"Unexpected token {token.type.name} at {token.line}:{token.column}")

    def parse_array_literal(self) -> ArrayLiteral:
        lbracket_token = self.expect(TokenType.LBRACKET)
        elements = []

        while self.current_token().type != TokenType.RBRACKET:
            elements.append(self.parse_expression())
            if self.current_token().type == TokenType.COMMA:
                self.advance()

        self.expect(TokenType.RBRACKET)
        return self.with_span(ArrayLiteral(elements), lbracket_token)

    def parse_dict_literal(self) -> DictLiteral:
        lbrace_token = self.expect(TokenType.LBRACE)
        pairs = []

        while self.current_token().type != TokenType.RBRACE:
            key = self.parse_expression()
            self.expect(TokenType.COLON)
            value = self.parse_expression()
            pairs.append((key, value))

            if self.current_token().type == TokenType.COMMA:
                self.advance()

        self.expect(TokenType.RBRACE)
        return self.with_span(DictLiteral(pairs), lbrace_token)

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
        return self.with_span(ImportStatement(module, alias), import_token)

    def parse_from_import_statement(self) -> FromImportStatement:
        from_token = self.expect(TokenType.FROM)
        module = self.parse_module_path()
        self.expect(TokenType.IMPORT)
        imports = []
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
        return self.with_span(FromImportStatement(module, imports), from_token)
