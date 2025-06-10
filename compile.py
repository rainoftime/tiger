#!/usr/bin/env python3
"""
Tiger Compiler with Debugging and Dump Options

This module provides a Tiger compiler with extensive debugging capabilities.
It allows dumping the output of each compilation phase for analysis and debugging.
This is particularly useful for understanding the compilation process and 
troubleshooting issues in specific phases.

Compilation phases that can be dumped:
1. Lexical Analysis - Token stream
2. Parsing - Abstract Syntax Tree
3. Semantic Analysis - Type-checked expressions
4. IR Translation - Intermediate representation trees
5. Canonicalization - Linearized IR
6. Instruction Selection - Assembly instructions
7. Register Allocation - Final assembly with register assignments

Author: Tiger Compiler Team
"""

# Core compiler components
from activation_records.frame import TempMap, sink, assembly_procedure
from activation_records.instruction_removal import is_redundant_move
from canonical.canonize import canonize
from intermediate_representation.fragment import FragmentManager, ProcessFragment, StringFragment
from register_allocation.allocation import RegisterAllocator
from semantic_analysis.analyzers import SemanticError, translate_program
from instruction_selection.codegen import Codegen
from putting_it_all_together.file_handler import FileHandler

# Lexer and parser components
from lexer import lex as le
from parser import parser as p

# Standard library imports
import sys
import logging
import argparse
from ply import lex


def setup_logger():
    """
    Configure the logging system for compilation progress tracking.
    
    Sets up INFO level logging with a clean format showing only
    the log level and message for better readability during compilation.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s'
    )


def setup_arguments():
    """
    Parse command line arguments for the Tiger compiler with dump options.
    
    Returns:
        argparse.Namespace: Parsed arguments containing:
            - input_file: Source file to compile
            - dump_lex: Flag to dump lexical analysis output
            - dump_parse: Flag to dump parser output
            - dump_sem: Flag to dump semantic analysis output
            - dump_ir: Flag to dump intermediate representation
            - dump_canon_ir: Flag to dump canonicalized IR
            - dump_assembly: Flag to dump instruction selection output
            - dump_regalloc: Flag to dump register allocation output
            - dump_all: Flag to enable all dump options
    """
    parser = argparse.ArgumentParser(description='Tiger compiler')
    parser.add_argument('input_file', help='Input source file')
    
    # Individual phase dump options
    parser.add_argument('-dump-lex', action='store_true', help='Dump lexer output')
    parser.add_argument('-dump-parse', action='store_true', help='Dump parser output')
    parser.add_argument('-dump-sem', action='store_true', help='Dump semantic analysis output')
    parser.add_argument('-dump-ir', action='store_true', help='Dump intermediate representation')
    parser.add_argument('-dump-canon-ir', action='store_true', help='Dump canonized IR')
    parser.add_argument('-dump-assembly', action='store_true', help='Dump output of instruction selection')
    parser.add_argument('-dump-regalloc', action='store_true', help='Dump output of register allocation')

    # Convenience option to dump all phases
    parser.add_argument('-dump-all', action='store_true', help='Dump output of each phase')
    return parser.parse_args()


def main():
    """
    Main compilation function with debugging support.
    
    Executes the complete Tiger compilation pipeline with optional dumping
    of intermediate results from each phase. This allows developers to
    inspect the transformation of code through each compilation stage.
    """
    # Parse command line arguments and setup logging
    args = setup_arguments()
    setup_logger()

    logging.info("Starting compilation")

    # Enable all dump flags if dump-all is specified
    if args.dump_all:
        args.dump_lex = True
        args.dump_parse = True
        args.dump_sem = True
        args.dump_ir = True
        args.dump_canon_ir = True
        args.dump_assembly = True
        args.dump_regalloc = True

    # Read input source file
    try:
        with open(args.input_file, "r") as f:
            data = f.read()
    except FileNotFoundError:
        logging.error("Input file not found")
        sys.exit(1)

    # Phase 1: Lexical Analysis
    # Convert source code into a stream of tokens
    logging.info("Starting lexical analysis")
    lex.input(data)

    if args.dump_lex:
        # Dump token stream for debugging lexical analysis
        # Note: This consumes the token stream, so lexer needs to be re-initialized
        print("\n" + "="*50)
        print("Lexical Analysis Output")
        print("="*50)
        while True:
            tok = lex.token()
            if not tok:
                break  # No more input
            print(tok)
        print("="*50 + "\n")

    # Phase 2: Syntactic Analysis (Parsing)
    # Build Abstract Syntax Tree from token stream
    try:
        parsed_program = p.parser.parse(data, le.lexer)
    except p.SyntacticError as err:
        logging.error(f"Syntax error: {err}")
        sys.exit(1)

    if args.dump_parse:
        # Dump Abstract Syntax Tree structure
        print("\n" + "="*50)
        print("Parser Output")
        print("="*50)
        print(parsed_program)
        print("="*50 + "\n")

    # Phase 3: Semantic Analysis and IR Translation
    # Type checking and translation to intermediate representation
    logging.info("Starting semantic analysis")
    TempMap.initialize()  # Initialize temporary variable mapping
    
    try:
        # Perform semantic analysis and generate IR
        typed_exp = translate_program(parsed_program)
    except SemanticError as err:
        logging.error(f"Semantic error: {err}")
        sys.exit(1)

    if args.dump_sem:
        # Dump type-checked expression tree
        print("\n" + "="*50)
        print("Semantic Analysis Output")
        print("="*50)
        print(typed_exp)
        print("="*50 + "\n")

    # Phase 4: Fragment Processing
    # Separate code fragments from string literals
    process_fragments = []  # Executable code (functions/procedures)
    string_fragments = []   # String literals for data section

    for fragment in FragmentManager.get_fragments():
        if isinstance(fragment, ProcessFragment):
            process_fragments.append(fragment)
        elif isinstance(fragment, StringFragment):
            string_fragments.append(fragment)

    if args.dump_ir:
        # Dump intermediate representation trees
        # TODO: Consider adding pretty printing and DOT file generation
        # TODO: Make basic blocks more explicit in dumped IR
        print("\n" + "="*50)
        print("Tree IR")
        print("="*50)
        from persistence.ir_dump import print_ir_list
        print_ir_list([fragment.body for fragment in process_fragments])
        print("="*50)
        for fragment in process_fragments:
            print(fragment.body)
        print("="*50 + "\n")

    # Phase 5: Canonicalization
    # Linearize control flow and eliminate complex expressions
    logging.info("Starting IR canonization")
    canonized_bodies = [canonize(fragment.body) for fragment in process_fragments]

    if args.dump_canon_ir:
        # Dump canonicalized (linearized) IR
        from persistence.ir_dump import print_canonized_ir
        print("\n" + "="*50)
        print("Canonized Tree IR")
        print("="*50)
        print_canonized_ir(canonized_bodies)
        print("="*50)
        print(canonized_bodies)
        print("="*50 + "\n")

    # Phase 6: Instruction Selection
    # Convert IR trees to target machine assembly instructions
    logging.info("Starting instruction selection")
    assembly_bodies = [Codegen.codegen(process_body) for process_body in canonized_bodies]

    if args.dump_assembly:
        # Dump generated assembly instructions before register allocation
        print("\n" + "="*50)
        print("Instruction Selection Output")
        print(assembly_bodies)
        print("="*50 + "\n")

    # Initialize output file handler
    file_handler = FileHandler("output.s")
    
    # Write data section with string literals
    file_handler.print_data_header()
    for string_fragment in string_fragments:
        file_handler.print_string_fragment(string_fragment)

    # Write code section header
    file_handler.print_code_header()

    # Phase 7: Register Allocation and Final Assembly Generation
    # Assign physical registers to temporary variables and generate final code
    logging.info("Starting register allocation")
    
    # Add sink instructions to handle function return values
    bodies_with_sink = [sink(assembly_body) for assembly_body in assembly_bodies]
    
    # Process each function/procedure
    for body, fragment in zip(bodies_with_sink, process_fragments):
        # Perform register allocation using graph coloring algorithm
        allocation_result = RegisterAllocator(fragment.frame).main(body)
        
        # Update global temporary-to-register mapping
        TempMap.update_temp_to_register(allocation_result.temp_to_register)
        
        # Remove redundant move instructions (optimization)
        instruction_list = [
            instruction
            for instruction in allocation_result.instructions
            if not is_redundant_move(instruction)
        ]
        
        # Generate final assembly procedure
        procedure = assembly_procedure(fragment.frame, instruction_list)
        file_handler.print_assembly_procedure(procedure)

    if args.dump_regalloc:
        # Dump final register allocation results
        print("\n" + "="*50)
        print("Register Allocation Output")
        print("="*50)
        print(file_handler)
        print("="*50 + "\n")

    logging.info("Compilation completed successfully")


if __name__ == "__main__":
    main()
