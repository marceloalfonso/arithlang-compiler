from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from codegen import RuntimeError_, execute, generate
from lexer import Lexer, LexerError, TokenType
from parser import ParseError, Parser
from semantic import SemanticError, analyze


def pipeline(source: str):
    tokens = Lexer(source).tokenize()
    tree = Parser(tokens).parse()
    analyze(tree)
    instrs = generate(tree)
    return execute(instrs)


def output_of(source: str):
    return pipeline(source).output


class TestLexer(unittest.TestCase):
    def _types(self, source):
        return [t.type for t in Lexer(source).tokenize()]

    def test_01_integer_token(self):
        tokens = Lexer("42").tokenize()
        self.assertEqual(tokens[0].type, TokenType.INTEGER)
        self.assertEqual(tokens[0].value, 42)

    def test_02_float_token(self):
        tokens = Lexer("3.14").tokenize()
        self.assertEqual(tokens[0].type, TokenType.FLOAT)
        self.assertAlmostEqual(tokens[0].value, 3.14)

    def test_03_keywords(self):
        types = self._types("let print x")
        self.assertIn(TokenType.LET, types)
        self.assertIn(TokenType.PRINT, types)
        self.assertIn(TokenType.IDENTIFIER, types)

    def test_04_comment_ignored(self):
        tokens = Lexer("# tudo isso some\nlet x = 1").tokenize()
        types = [t.type for t in tokens]
        self.assertNotIn(
            TokenType.IDENTIFIER, [t.type for t in tokens if t.value == "tudo"]
        )
        self.assertIn(TokenType.LET, types)

    def test_05_line_and_col_tracking(self):
        tokens = Lexer("let x = 1\nlet y = 2").tokenize()
        second_let = [t for t in tokens if t.type == TokenType.LET][1]
        self.assertEqual(second_let.line, 2)
        self.assertEqual(second_let.col, 1)

    def test_06_lexer_error_invalid_char(self):
        with self.assertRaises(LexerError) as ctx:
            Lexer("let x = @").tokenize()
        self.assertIn("L1", str(ctx.exception))
        self.assertIn("@", str(ctx.exception))


class TestParser(unittest.TestCase):
    def _parse(self, source):
        return Parser(Lexer(source).tokenize()).parse()

    def test_07_let_statement_parsed(self):
        from ast_nodes import LetStatement

        tree = self._parse("let x = 10")
        self.assertIsInstance(tree.statements[0], LetStatement)
        self.assertEqual(tree.statements[0].name, "x")

    def test_08_assign_statement_parsed(self):
        from ast_nodes import AssignStatement

        tree = self._parse("let x = 1\nx = 2")
        self.assertIsInstance(tree.statements[1], AssignStatement)

    def test_09_precedence_mul_before_add(self):
        from ast_nodes import BinaryOp

        tree = self._parse("let x = 2 + 3 * 4")
        expr = tree.statements[0].value
        self.assertIsInstance(expr, BinaryOp)
        self.assertEqual(expr.op, "+")
        self.assertIsInstance(expr.right, BinaryOp)
        self.assertEqual(expr.right.op, "*")

    def test_10_parentheses_override_precedence(self):
        from ast_nodes import BinaryOp

        tree = self._parse("let y = (2 + 3) * 4")
        expr = tree.statements[0].value
        self.assertEqual(expr.op, "*")
        self.assertIsInstance(expr.left, BinaryOp)
        self.assertEqual(expr.left.op, "+")

    def test_11_parse_error_missing_rparen(self):
        with self.assertRaises(ParseError):
            self._parse("print(1 + 2")

    def test_12_parse_error_print_without_parens(self):
        with self.assertRaises(ParseError):
            self._parse("print x")


class TestSemantic(unittest.TestCase):
    def _analyze(self, source):
        tokens = Lexer(source).tokenize()
        tree = Parser(tokens).parse()
        return analyze(tree)

    def test_13_undeclared_variable(self):
        with self.assertRaises(SemanticError) as ctx:
            self._analyze("print(y)")

        self.assertIn("'y'", str(ctx.exception))

    def test_14_redeclaration(self):
        with self.assertRaises(SemanticError) as ctx:
            self._analyze("let x = 1\nlet x = 2")

        self.assertIn("'x'", str(ctx.exception))

    def test_15_assign_without_let(self):
        with self.assertRaises(SemanticError):
            self._analyze("z = 10")

    def test_16_use_before_declaration(self):
        with self.assertRaises(SemanticError):
            self._analyze("let b = a + 1\nlet a = 5")

    def test_17_type_inference_div_always_float(self):
        sa = self._analyze("let a = 10\nlet b = 4\nlet r = a / b")
        self.assertEqual(sa.table.symbols["r"], "float")

    def test_18_type_inference_int_plus_float(self):
        sa = self._analyze("let x = 2\nlet y = 1.5\nlet z = x + y")
        self.assertEqual(sa.table.symbols["z"], "float")


class TestExecution(unittest.TestCase):
    def test_19_basic_four_operations(self):
        vm = pipeline(
            "let a = 10\nlet b = 3\nprint(a + b)\nprint(a - b)\nprint(a * b)\nprint(a / b)"
        )
        self.assertEqual(vm.output[0], "13")
        self.assertEqual(vm.output[1], "7")
        self.assertEqual(vm.output[2], "30")
        self.assertEqual(vm.output[3], "3.3333333333333335")

    def test_20_precedence_result(self):
        vm = pipeline(
            "let x = 2 + 3 * 4\nlet y = (2 + 3) * 4\nprint(x)\nprint(y)"
        )
        self.assertEqual(vm.output[0], "14")
        self.assertEqual(vm.output[1], "20")

    def test_21_float_arithmetic(self):
        vm = pipeline(
            "let base = 7.5\nlet altura = 4.0\nlet area = (base * altura) / 2\nprint(area)"
        )
        self.assertEqual(vm.output[0], "15")

    def test_22_unary_minus(self):
        vm = pipeline("let n = -10\nprint(n)")
        self.assertEqual(vm.output[0], "-10")

    def test_23_assign_accumulation(self):
        vm = pipeline("let x = 1\nx = x + 1\nx = x + 1\nprint(x)")
        self.assertEqual(vm.output[0], "3")

    def test_24_mixed_int_float_promotion(self):
        vm = pipeline("let i = 3\nlet f = 0.5\nprint(i + f)")
        self.assertEqual(vm.output[0], "3.5")

    def test_25_division_by_zero(self):
        with self.assertRaises(RuntimeError_) as ctx:
            pipeline("let a = 5\nlet b = 0\nprint(a / b)")

        self.assertIn("divisão por zero", str(ctx.exception))

    def test_26_multiple_prints(self):
        vm = pipeline(
            "let a = 1\nlet b = 2\nlet c = 3\nprint(a)\nprint(b)\nprint(c)"
        )
        self.assertEqual(vm.output, ["1", "2", "3"])

    def test_27_nested_expression(self):
        vm = pipeline("let r = (2 + 3) * (4 - 1) / 3\nprint(r)")
        self.assertEqual(vm.output[0], "5")

    def test_28_semicolon_as_separator(self):
        vm = pipeline("let x = 10; let y = 20; print(x + y)")
        self.assertEqual(vm.output[0], "30")


if __name__ == "__main__":
    unittest.main(verbosity=2)
