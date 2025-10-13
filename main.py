"""
Tiger Compiler Main Entry Point

This module orchestrates the complete Tiger-to-x86-64 compilation pipeline.
It coordinates all compilation phases from source code to executable assembly:

1. **Lexical Analysis**: Tokenize source code
2. **Parsing**: Build Abstract Syntax Tree (AST)
3. **Semantic Analysis**: Type checking and IR generation
4. **Canonicalization**: Transform IR to basic blocks
5. **Instruction Selection**: Generate assembly from IR
6. **Register Allocation**: Assign physical registers
7. **Assembly Generation**: Produce final x86-64 code

The compilation process follows the standard compiler architecture:
Source Code → Tokens → AST → Typed IR → Assembly → Executable

Error Handling:
- Lexical errors: Invalid characters in source
- Syntax errors: Malformed Tiger programs
- Semantic errors: Type mismatches, undefined variables
- Code generation errors: Register allocation failures

Usage:
    python main.py <source_file.tig>

Output:
    - output.s: x86-64 assembly code
    - a.out: Compiled executable (after linking with runtime)

Author: Tiger Compiler Project
"""

from activation_records.frame import (
    TempMap,
    sink,
    assembly_procedure,
)
from activation_records.instruction_removal import is_redundant_move
from canonical.canonize import canonize
from intermediate_representation.fragment import (
    FragmentManager,
    ProcessFragment,
    StringFragment,
)
from register_allocation.allocation import RegisterAllocator
from semantic_analysis.analyzers import SemanticError, translate_program
from instruction_selection.codegen import Codegen
from putting_it_all_together.file_handler import FileHandler
from lexer import lex as le
from parser import parser as p
import sys
from ply import lex


def main():
    """
    Execute the complete Tiger compilation pipeline.

    This function orchestrates all compilation phases in sequence:
    1. Input validation and source file reading
    2. Lexical analysis (tokenization)
    3. Parsing (AST construction)
    4. Semantic analysis (type checking and IR generation)
    5. Canonicalization (basic block formation)
    6. Instruction selection (assembly generation)
    7. Register allocation (physical register assignment)
    8. Final assembly output

    Each phase can fail with specific error types that are caught and
    reported with appropriate error messages and exit codes.

    Raises:
        SystemExit: On compilation errors with appropriate exit codes
    """
    # =====================================================================
    # PHASE 1: INPUT VALIDATION AND SOURCE READING
    # =====================================================================

    if len(sys.argv) == 1:
        print("Fatal error. No input file detected.")
        sys.exit(1)

    # Read source file
    try:
        with open(sys.argv[1], "r") as f:
            data = f.read()
    except IOError as e:
        print(f"Fatal error reading input file: {e}")
        sys.exit(1)

    # =====================================================================
    # PHASE 2: LEXICAL ANALYSIS (TOKENIZATION)
    # =====================================================================

    # Initialize lexer with source code
    lex.input(data)

    try:
        # Parse tokens into Abstract Syntax Tree
        parsed_program = p.parser.parse(data, le.lexer)
    except p.SyntacticError as err:
        print(err)
        sys.exit(1)

    # =====================================================================
    # PHASE 3: SEMANTIC ANALYSIS (TYPE CHECKING & IR GENERATION)
    # =====================================================================

    # Initialize register mapping system
    TempMap.initialize()

    try:
        # Perform type checking and generate intermediate representation
        translate_program(parsed_program)
    except SemanticError as err:
        print(err)
        sys.exit(1)

    # =====================================================================
    # PHASE 4: CANONICALIZATION (BASIC BLOCK FORMATION)
    # =====================================================================

    # Separate different types of fragments (functions vs string literals)
    process_fragments = []
    string_fragments = []

    for fragment in FragmentManager.get_fragments():
        if isinstance(fragment, ProcessFragment):
            process_fragments.append(fragment)  # Function definitions
        elif isinstance(fragment, StringFragment):
            string_fragments.append(fragment)   # String literals

    # Transform IR trees into canonical basic block form
    canonized_bodies = [canonize(fragment.body) for fragment in process_fragments]

    # =====================================================================
    # PHASE 5: INSTRUCTION SELECTION (ASSEMBLY GENERATION)
    # =====================================================================

    # Generate assembly instructions from canonical IR
    assembly_bodies = [
        Codegen.codegen(process_body) for process_body in canonized_bodies
    ]

    # =====================================================================
    # PHASE 6: ASSEMBLY OUTPUT AND REGISTER ALLOCATION
    # =====================================================================

    # Initialize output file handler
    file_handler = FileHandler("output.s")

    # Write data section (string literals and static data)
    file_handler.print_data_header()
    for string_fragment in string_fragments:
        file_handler.print_string_fragment(string_fragment)

    # Write code section header
    file_handler.print_code_header()

    # Register Allocation Phase
    # Add sink instructions and perform register allocation for each function
    bodies_with_sink = [sink(assembly_body) for assembly_body in assembly_bodies]

    for body, fragment in zip(bodies_with_sink, process_fragments):
        # Allocate registers for this function
        allocation_result = RegisterAllocator(fragment.frame).main(body)

        # Update global register mapping
        TempMap.update_temp_to_register(allocation_result.temp_to_register)

        # Filter out redundant move instructions
        instruction_list = [
            instruction
            for instruction in allocation_result.instructions
            if not is_redundant_move(instruction)
        ]

        # Generate final procedure assembly
        procedure = assembly_procedure(fragment.frame, instruction_list)
        file_handler.print_assembly_procedure(procedure)


if __name__ == "__main__":
    main()
