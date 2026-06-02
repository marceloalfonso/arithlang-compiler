from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ast_nodes import (
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

Instruction = Tuple[str, ...]


class RuntimeError_(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(f"Erro de Execução: {message}")


_BINOP_TO_OPCODE: Dict[str, str] = {
    "+": "ADD",
    "-": "SUB",
    "*": "MUL",
    "/": "DIV",
}


class CodeGenerator(Visitor):
    def __init__(self) -> None:
        self._instructions: List[Instruction] = []

    def _emit(self, *args: Any) -> None:
        self._instructions.append(tuple(str(a) for a in args))

    def generate(self, tree: Program) -> List[Instruction]:
        self.visit(tree)
        self._emit("HALT")
        return list(self._instructions)

    def visit_Program(self, node: Program) -> None:
        for stmt in node.statements:
            self.visit(stmt)

    def visit_LetStatement(self, node: LetStatement) -> None:
        self.visit(node.value)
        self._emit("STORE", node.name)

    def visit_AssignStatement(self, node: AssignStatement) -> None:
        self.visit(node.value)
        self._emit("STORE", node.name)

    def visit_PrintStatement(self, node: PrintStatement) -> None:
        self.visit(node.value)
        self._emit("PRINT")

    def visit_IntLiteral(self, node: IntLiteral) -> None:
        self._emit("PUSH", node.value)

    def visit_FloatLiteral(self, node: FloatLiteral) -> None:
        self._emit("PUSH", node.value)

    def visit_Identifier(self, node: Identifier) -> None:
        self._emit("LOAD", node.name)

    def visit_UnaryOp(self, node: UnaryOp) -> None:
        self.visit(node.operand)
        self._emit("NEG")

    def visit_BinaryOp(self, node: BinaryOp) -> None:
        self.visit(node.left)
        self.visit(node.right)
        self._emit(_BINOP_TO_OPCODE[node.op])


class VirtualMachine:
    def __init__(self) -> None:
        self.stack: List[Any] = []
        self.env: Dict[str, Any] = {}
        self.output: List[str] = []

    def run(self, instructions: List[Instruction]) -> None:
        for instr in instructions:
            op, *args = instr

            if op == "PUSH":
                raw = args[0]

                try:
                    value = int(raw)
                except ValueError:
                    value = float(raw)

                self.stack.append(value)

            elif op == "LOAD":
                name = args[0]

                if name not in self.env:
                    raise RuntimeError_(
                        f"variável '{name}' não encontrada no ambiente"
                    )

                self.stack.append(self.env[name])

            elif op == "STORE":
                self.env[args[0]] = self.stack.pop()

            elif op == "ADD":
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a + b)

            elif op == "SUB":
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a - b)

            elif op == "MUL":
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a * b)

            elif op == "DIV":
                b, a = self.stack.pop(), self.stack.pop()

                if b == 0:
                    raise RuntimeError_("divisão por zero")

                self.stack.append(a / b)

            elif op == "NEG":
                self.stack.append(-self.stack.pop())

            elif op == "PRINT":
                value = self.stack.pop()

                text = (
                    str(int(value))
                    if isinstance(value, float) and value == int(value)
                    else str(value)
                )
                self.output.append(text)

                print(text)
            elif op == "HALT":
                break

            else:
                raise RuntimeError_(f"opcode desconhecido: '{op}'")


def generate(tree: Program) -> List[Instruction]:
    return CodeGenerator().generate(tree)


def execute(instructions: List[Instruction]) -> VirtualMachine:
    vm = VirtualMachine()
    vm.run(instructions)
    return vm


def disassemble(instructions: List[Instruction]) -> str:
    lines = []

    for i, instr in enumerate(instructions):
        lines.append(f"  {i:03d}  {instr[0]:<6} {' '.join(instr[1:])}")

    return "\n".join(lines)


def save_bytecode(instructions: List[Instruction], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for instr in instructions:
            f.write(" ".join(instr) + "\n")


def load_bytecode(path: str) -> List[Instruction]:
    instructions: List[Instruction] = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line:
                parts = line.split()
                instructions.append(tuple(parts))

    return instructions
