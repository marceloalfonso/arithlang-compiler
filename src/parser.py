from __future__ import annotations

from typing import List, Optional

from ast_nodes import (
    AST,
    AssignStatement,
    BinaryOp,
    FloatLiteral,
    Identifier,
    IntLiteral,
    LetStatement,
    PrintStatement,
    Program,
    UnaryOp,
)
from lexer import Token, TokenType


class ParseError(Exception):
    def __init__(self, message: str, line: int) -> None:
        super().__init__(f"Erro Sintático (L{line}): {message}")
        self.line = line


class Parser:
    def __init__(self, tokens: List[Token]) -> None:
        self._tokens: List[Token] = [
            t
            for t in tokens
            if t.type not in (TokenType.NEWLINE, TokenType.SEMICOLON)
        ]
        self._pos: int = 0

    @property
    def _current(self) -> Token:
        return self._tokens[self._pos]

    def _peek(self, offset: int = 1) -> Optional[Token]:
        idx = self._pos + offset
        return self._tokens[idx] if idx < len(self._tokens) else None

    def _advance(self) -> Token:
        token = self._current
        if token.type != TokenType.EOF:
            self._pos += 1
        return token

    def _expect(self, type_: TokenType) -> Token:
        if self._current.type == type_:
            return self._advance()
        raise ParseError(
            f"'{type_.value}' esperado, encontrado {self._current.type.value!r}",
            self._current.line,
        )

    def _match(self, *types: TokenType) -> bool:
        return self._current.type in types

    def parse(self) -> Program:
        statements: List[AST] = []

        while not self._match(TokenType.EOF):
            stmt = self._statement()

            if stmt is not None:
                statements.append(stmt)

        return Program(statements=statements)

    def _statement(self) -> Optional[AST]:
        if self._match(TokenType.LET):
            return self._let_statement()
        if self._match(TokenType.PRINT):
            return self._print_statement()
        if self._match(TokenType.IDENTIFIER):
            next_tok = self._peek()
            if next_tok and next_tok.type == TokenType.ASSIGN:
                return self._assign_statement()
        raise ParseError(
            f"início de comando inesperado: {self._current.type.value!r}",
            self._current.line,
        )

    def _let_statement(self) -> LetStatement:
        line = self._current.line
        self._expect(TokenType.LET)
        name_tok = self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.ASSIGN)
        value = self._expression()
        return LetStatement(name=name_tok.value, value=value, line=line)

    def _assign_statement(self) -> AssignStatement:
        name_tok = self._advance()  # IDENTIFIER
        line = name_tok.line
        self._expect(TokenType.ASSIGN)
        value = self._expression()
        return AssignStatement(name=name_tok.value, value=value, line=line)

    def _print_statement(self) -> PrintStatement:
        line = self._current.line
        self._expect(TokenType.PRINT)
        self._expect(TokenType.LPAREN)
        value = self._expression()
        self._expect(TokenType.RPAREN)
        return PrintStatement(value=value, line=line)

    def _expression(self) -> AST:
        node = self._term()

        while self._match(TokenType.PLUS, TokenType.MINUS):
            op_tok = self._advance()
            right = self._term()
            node = BinaryOp(op=op_tok.value, left=node, right=right)

        return node

    def _term(self) -> AST:
        node = self._unary()

        while self._match(TokenType.STAR, TokenType.SLASH):
            op_tok = self._advance()
            right = self._unary()
            node = BinaryOp(op=op_tok.value, left=node, right=right)

        return node

    def _unary(self) -> AST:
        if self._match(TokenType.MINUS):
            op_tok = self._advance()
            operand = self._unary()
            return UnaryOp(op=op_tok.value, operand=operand)

        return self._primary()

    def _primary(self) -> AST:
        tok = self._current

        if tok.type == TokenType.INTEGER:
            self._advance()
            return IntLiteral(value=tok.value)

        if tok.type == TokenType.FLOAT:
            self._advance()
            return FloatLiteral(value=tok.value)

        if tok.type == TokenType.IDENTIFIER:
            self._advance()
            return Identifier(name=tok.value, line=tok.line)

        if tok.type == TokenType.LPAREN:
            self._advance()
            node = self._expression()
            self._expect(TokenType.RPAREN)
            return node

        if tok.type == TokenType.EOF:
            raise ParseError(
                "expressão incompleta — fim de arquivo inesperado", tok.line
            )

        raise ParseError(
            f"token inesperado em expressão: {tok.type.value!r}",
            tok.line,
        )
