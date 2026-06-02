from __future__ import annotations

from enum import Enum
from typing import List, Optional


class TokenType(Enum):
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    IDENTIFIER = "IDENTIFIER"
    LET = "LET"
    PRINT = "PRINT"
    PLUS = "+"
    MINUS = "-"
    STAR = "*"
    SLASH = "/"
    ASSIGN = "="
    LPAREN = "("
    RPAREN = ")"
    SEMICOLON = ";"
    NEWLINE = "NEWLINE"
    EOF = "EOF"


class Token:
    def __init__(
        self,
        type: TokenType,
        value: Optional[object],
        line: int,
        col: int,
    ) -> None:
        self.type: TokenType = type
        self.value: Optional[object] = value
        self.line: int = line
        self.col: int = col

    def __repr__(self) -> str:
        return f"Token({self.type}, {self.value!r}, L{self.line}:C{self.col})"


class LexerError(Exception):
    def __init__(self, message: str, line: int, col: int) -> None:
        super().__init__(f"Erro Léxico (L{line}:C{col}): {message}")
        self.line = line
        self.col = col


_KEYWORDS: dict[str, TokenType] = {
    "let": TokenType.LET,
    "print": TokenType.PRINT,
}


class Lexer:
    def __init__(self, source: str) -> None:
        self.source: str = source
        self.pos: int = 0
        self.line: int = 1
        self.col: int = 1

    @property
    def _current(self) -> Optional[str]:
        return self.source[self.pos] if self.pos < len(self.source) else None

    def _peek(self, offset: int = 1) -> Optional[str]:
        idx = self.pos + offset
        return self.source[idx] if idx < len(self.source) else None

    def _advance(self) -> str:
        char = self.source[self.pos]
        self.pos += 1

        if char == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1

        return char

    def _skip_whitespace(self) -> None:
        while self._current and self._current in (" ", "\t", "\r"):
            self._advance()

    def _skip_comment(self) -> None:
        while self._current and self._current != "\n":
            self._advance()

    def _read_number(self) -> Token:
        start_col = self.col
        result = ""
        is_float = False

        while self._current and (
            self._current.isdigit() or self._current == "."
        ):
            if self._current == ".":
                if is_float:
                    raise LexerError(
                        "número com mais de um ponto decimal",
                        self.line,
                        self.col,
                    )

                is_float = True

            result += self._advance()

        if is_float:
            return Token(TokenType.FLOAT, float(result), self.line, start_col)

        return Token(TokenType.INTEGER, int(result), self.line, start_col)

    def _read_identifier(self) -> Token:
        start_col = self.col
        result = ""

        while self._current and (
            self._current.isalnum() or self._current == "_"
        ):
            result += self._advance()

        token_type = _KEYWORDS.get(result, TokenType.IDENTIFIER)
        return Token(token_type, result, self.line, start_col)

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []

        while True:
            self._skip_whitespace()

            if self._current is None:
                tokens.append(Token(TokenType.EOF, None, self.line, self.col))
                break

            current_line = self.line
            current_col = self.col
            char = self._current

            if char == "\n":
                self._advance()
                tokens.append(
                    Token(TokenType.NEWLINE, "\n", current_line, current_col)
                )
                continue

            if char == "#":
                self._skip_comment()
                continue

            if char.isdigit():
                tokens.append(self._read_number())
                continue

            if char.isalpha() or char == "_":
                tokens.append(self._read_identifier())
                continue

            _SIMPLE: dict[str, TokenType] = {
                "+": TokenType.PLUS,
                "-": TokenType.MINUS,
                "*": TokenType.STAR,
                "/": TokenType.SLASH,
                "=": TokenType.ASSIGN,
                "(": TokenType.LPAREN,
                ")": TokenType.RPAREN,
                ";": TokenType.SEMICOLON,
            }

            if char in _SIMPLE:
                self._advance()
                tokens.append(
                    Token(_SIMPLE[char], char, current_line, current_col)
                )
                continue

            raise LexerError(
                f"caractere '{char}' não reconhecido", current_line, current_col
            )

        return tokens
