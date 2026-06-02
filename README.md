# Instruções de uso

Este projeto implementa um compilador para a ArithLang, uma mini-linguagem aritmética que suporta as quatro operações básicas (adição, subtração, multiplicação e divisão) e o comando `print`. O compilador é organizado em cinco fases independentes: análise léxica, análise sintática, análise semântica, geração de bytecode e execução em máquina virtual de pilha.

Para executar um programa ArithLang, é necessário ter o [uv](https://docs.astral.sh/uv/) instalado. Com ele, rode:

```bash
uv run main.py examples/basic-math-operations.al
```

Para passar código diretamente pela linha de comando, sem precisar de um arquivo, use a flag `-c`:

```bash
uv run main.py -c "let x = 10 * 2\nprint(x)"
```

O modo verbose, ativado com `-v`, exibe os tokens gerados pelo lexer, a árvore sintática abstrata (AST) e o bytecode produzido antes de executar o programa — útil para inspecionar cada fase do pipeline:

```bash
uv run main.py -v examples/complex-expressions.al
```

O compilador também permite separar as etapas de compilação e execução. A flag `--save-bytecode` compila o arquivo `.al` e salva o bytecode gerado na pasta `output/`, que é criada automaticamente caso não exista. O nome do arquivo `.alc` é derivado do fonte:

```bash
uv run main.py examples/basic-math-operations.al --save-bytecode
```

Um nome alternativo pode ser informado diretamente após a flag:

```bash
uv run main.py examples/basic-math-operations.al --save-bytecode saida.alc
```

Para executar um arquivo `.alc` já compilado, sem passar pelo pipeline de compilação novamente, use `--run`:

```bash
uv run main.py --run output/basic-math-operations.alc
```

Para rodar a suite de testes automatizados:

```bash
uv run tests/test_compiler.py
```
