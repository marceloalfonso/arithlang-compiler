from __future__ import annotations

from typing import Dict

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
    Visitor,
)


class SemanticError(Exception):
    def __init__(self, message: str, line: int) -> None:
        super().__init__(f"Erro Semântico (L{line}): {message}")
        self.line = line


class SymbolTable:
    def __init__(self) -> None:
        self.symbols: Dict[str, str] = {}

    def define(self, name: str, type_: str, line: int) -> None:
        if name in self.symbols:
            raise SemanticError(f"variável '{name}' já declarada", line)

        self.symbols[name] = type_

    def assign(self, name: str, type_: str, line: int) -> None:
        if name not in self.symbols:
            raise SemanticError(
                f"variável '{name}' não declarada — use 'let {name} = ...' para declarar",
                line,
            )

        self.symbols[name] = type_

    def lookup(self, name: str, line: int) -> str:
        if name not in self.symbols:
            raise SemanticError(f"variável '{name}' usada sem declaração", line)
        return self.symbols[name]


def _infer_binop(op: str, left: str, right: str) -> str:
    if op == "/":
        return "float"
    if "float" in (left, right):
        return "float"
    return "int"


class SemanticAnalyzer(Visitor):
    def __init__(self) -> None:
        self.table: SymbolTable = SymbolTable()
        self.types: Dict[int, str] = {}

    def _record(self, node: AST, type_: str) -> str:
        self.types[id(node)] = type_
        return type_

    def visit_Program(self, node: Program) -> None:
        for stmt in node.statements:
            self.visit(stmt)

    def visit_LetStatement(self, node: LetStatement) -> None:
        type_ = self.visit(node.value)
        self.table.define(node.name, type_, node.line)

    def visit_AssignStatement(self, node: AssignStatement) -> None:
        type_ = self.visit(node.value)
        self.table.assign(node.name, type_, node.line)

    def visit_PrintStatement(self, node: PrintStatement) -> None:
        self.visit(node.value)

    def visit_IntLiteral(self, node: IntLiteral) -> str:
        return self._record(node, "int")

    def visit_FloatLiteral(self, node: FloatLiteral) -> str:
        return self._record(node, "float")

    def visit_Identifier(self, node: Identifier) -> str:
        type_ = self.table.lookup(node.name, node.line)
        return self._record(node, type_)

    def visit_UnaryOp(self, node: UnaryOp) -> str:
        type_ = self.visit(node.operand)
        return self._record(node, type_)

    def visit_BinaryOp(self, node: BinaryOp) -> str:
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        type_ = _infer_binop(node.op, left_type, right_type)
        return self._record(node, type_)


def analyze(tree: Program) -> SemanticAnalyzer:
    analyzer = SemanticAnalyzer()
    analyzer.visit(tree)
    return analyzer
