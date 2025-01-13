# Compiler for Tiger

Compiler for the Tiger programming language implemented in Python. 


* `lexer`: Chapter 2, Lexical Analysis.
* `parser`: Chapter 3, Parsing and Chapter 4, Abstract Syntax.
* `semantic_analysis`: Chapter 5, Semantic Analysis.
* `activation_records`: Chapter 6, Activation Records.
* `intermediate_representation`: Chapter 7, Translation to Intermediate Code.
* `canonical`: Chapter 8, Basic Blocks and Traces.
* `instruction_selection`: Chapter 9, Instruction Selection.
* `liveness_analysis`: Chapter 10, Liveness Analysis.
* `register_allocation`: Chapter 11, Register Allocation.
* `putting_it_all_together`: Chapter 12, Putting it All Together.
* `examples`: A list of Tiger programs provided by Appel.
* `tests`: Integration tests for specific parts of the compilation process.
* `ply`: [Python Lex-Yacc](https://www.dabeaz.com/ply/). Used in chapters 2-4.

## Setup

This project has been tested on Python version `3.9` (TBD).

From the project root directory, on a virtual Python environment,
run:

```bash
pip3 install -r requirements.txt
```

## Usage

### Compile a Tiger Program

Make sure `src/compile.sh` has execution permissions and that the current directory is added to your `$PYTHONPATH`
environment variable.

Run:

```bash
./compile.sh source_file
```

This will generate an executable with the name `a.out`.

### Dump and View (TBD)

- AST (after parsing)
- Typed AST (after semantic analysis)
- IR Tree
- Canonicalied IR Tree
- Instructions before register allocation
- Instructions after register allocation
- Stack frame?
- ...

## Tests

Run:

```bash
python3 -m unittest
```

This will run both unit and integration tests for the entire project.

To run tests for a specific file or directory, use:

```bash
python3 -m unittest <PATH>
```

## Readings

- The Tiger Book
- Lecture Notes on Principles of Compilers, rainoftime