from __future__ import annotations

from dataclasses import dataclass
from typing import List


class AST:
    pass


@dataclass(frozen=True)
class IntLiteral(AST):
    value: int


@dataclass(frozen=True)
class FloatLiteral(AST):
    value: float


@dataclass(frozen=True)
class Identifier(AST):
    name: str
    line: int


@dataclass(frozen=True)
class UnaryOp(AST):
    op: str
    operand: AST


@dataclass(frozen=True)
class BinaryOp(AST):
    op: str
    left: AST
    right: AST


@dataclass(frozen=True)
class LetStatement(AST):
    name: str
    value: AST
    line: int


@dataclass(frozen=True)
class AssignStatement(AST):
    name: str
    value: AST
    line: int


@dataclass(frozen=True)
class PrintStatement(AST):
    value: AST
    line: int


@dataclass(frozen=True)
class Program(AST):
    statements: List[AST]


class Visitor:
    def visit(self, node: AST):
        method_name = "visit_" + type(node).__name__
        method = getattr(self, method_name, self._generic_visit)
        return method(node)

    def _generic_visit(self, node: AST):
        raise NotImplementedError(
            f"{type(self).__name__} não implementa visit_{type(node).__name__}"
        )


class ASTPrinter(Visitor):
    def __init__(self) -> None:
        self._indent = 0

    def _line(self, text: str) -> None:
        print("  " * self._indent + text)

    def _block(self, label: str, node: AST) -> None:
        self._line(label)
        self._indent += 1
        self.visit(node)
        self._indent -= 1

    def visit_Program(self, node: Program) -> None:
        self._line("Program")
        self._indent += 1

        for stmt in node.statements:
            self.visit(stmt)
            
        self._indent -= 1

    def visit_LetStatement(self, node: LetStatement) -> None:
        self._line(f"LetStatement(name={node.name!r}, L{node.line})")
        self._indent += 1
        self.visit(node.value)
        self._indent -= 1

    def visit_AssignStatement(self, node: AssignStatement) -> None:
        self._line(f"AssignStatement(name={node.name!r}, L{node.line})")
        self._indent += 1
        self.visit(node.value)
        self._indent -= 1

    def visit_PrintStatement(self, node: PrintStatement) -> None:
        self._line(f"PrintStatement(L{node.line})")
        self._indent += 1
        self.visit(node.value)
        self._indent -= 1

    def visit_BinaryOp(self, node: BinaryOp) -> None:
        self._line(f"BinaryOp({node.op!r})")
        self._indent += 1
        self.visit(node.left)
        self.visit(node.right)
        self._indent -= 1

    def visit_UnaryOp(self, node: UnaryOp) -> None:
        self._line(f"UnaryOp({node.op!r})")
        self._indent += 1
        self.visit(node.operand)
        self._indent -= 1

    def visit_IntLiteral(self, node: IntLiteral) -> None:
        self._line(f"IntLiteral({node.value})")

    def visit_FloatLiteral(self, node: FloatLiteral) -> None:
        self._line(f"FloatLiteral({node.value})")

    def visit_Identifier(self, node: Identifier) -> None:
        self._line(f"Identifier({node.name!r}, L{node.line})")
