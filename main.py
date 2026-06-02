from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ast_nodes import ASTPrinter
from codegen import (
    RuntimeError_,
    disassemble,
    execute,
    generate,
    load_bytecode,
    save_bytecode,
)
from lexer import Lexer, LexerError
from parser import ParseError, Parser
from semantic import SemanticError, analyze


def compile_and_run(
    source: str, verbose: bool = False, save_path: str = None
) -> int:
    try:
        tokens = Lexer(source).tokenize()
        if verbose:
            print("=== TOKENS ===")
            for t in tokens:
                print(f"  {t}")
            print()

        tree = Parser(tokens).parse()
        if verbose:
            print("=== AST ===")
            ASTPrinter().visit(tree)
            print()

        analyze(tree)

        instructions = generate(tree)
        if verbose:
            print("=== BYTECODE ===")
            print(disassemble(instructions))
            print()
            print("=== SAÍDA ===")

        if save_path:
            save_bytecode(instructions, save_path)
            print(f"Bytecode salvo em: {save_path}", file=sys.stderr)

        execute(instructions)
        return 0

    except (LexerError, ParseError, SemanticError, RuntimeError_) as e:
        print(e, file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Erro interno: {e}", file=sys.stderr)
        return 1


def run_bytecode(alc_path: str) -> int:
    try:
        instructions = load_bytecode(alc_path)
        execute(instructions)
        return 0
    except RuntimeError_ as e:
        print(e, file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Erro interno: {e}", file=sys.stderr)
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="compilador",
        description="Compilador ArithLangs",
    )
    parser.add_argument("file", nargs="?", help="Arquivo fonte .al a compilar")
    parser.add_argument(
        "-c",
        "--code",
        metavar="CÓDIGO",
        help="Executa código ArithLang passado diretamente como string",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Exibe tokens, AST e bytecode antes da saída",
    )
    parser.add_argument(
        "--save-bytecode",
        metavar="ARQUIVO",
        help="Compila e salva o bytecode em output/",
        nargs="?",
        const="",
    )
    parser.add_argument(
        "--run",
        metavar="ARQUIVO.alc",
        help="Executa um arquivo .alc previamente compilado, sem recompilar",
    )

    args = parser.parse_args()

    if args.run:
        alc_path = Path(args.run)

        if not alc_path.exists():
            print(
                f"Erro: arquivo '{args.run}' não encontrado.", file=sys.stderr
            )
            sys.exit(1)

        sys.exit(run_bytecode(str(alc_path)))

    if args.code:
        source = args.code.replace("\\n", "\n")
        src_path = None
    elif args.file:
        src_path = Path(args.file)

        if not src_path.exists():
            print(
                f"Erro: arquivo '{args.file}' não encontrado.", file=sys.stderr
            )
            sys.exit(1)

        source = src_path.read_text(encoding="utf-8")
    else:
        parser.print_help()
        sys.exit(0)

    save_path = None

    if args.save_bytecode is not None:
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        if args.save_bytecode:
            save_path = str(output_dir / Path(args.save_bytecode).name)
        elif src_path:
            save_path = str(output_dir / src_path.with_suffix(".alc").name)
        else:
            save_path = str(output_dir / "saida.alc")

    sys.exit(compile_and_run(source, verbose=args.verbose, save_path=save_path))


if __name__ == "__main__":
    main()
