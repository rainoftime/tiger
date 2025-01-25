"""

"""
from activation_records.frame import TempMap, sink, assembly_procedure
from activation_records.instruction_removal import is_redundant_move
from canonical.canonize import canonize
from intermediate_representation.fragment import FragmentManager, ProcessFragment, StringFragment
from register_allocation.allocation import RegisterAllocator
from semantic_analysis.analyzers import SemanticError, translate_program
from instruction_selection.codegen import Codegen
from putting_it_all_together.file_handler import FileHandler
from lexer import lex as le
from parser import parser as p
import sys
import logging
import argparse
from ply import lex


def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s'
    )


def setup_arguments():
    parser = argparse.ArgumentParser(description='Tiger compiler')
    parser.add_argument('input_file', help='Input source file')
    parser.add_argument('-dump-lex', action='store_true', help='Dump lexer output')
    parser.add_argument('-dump-parse', action='store_true', help='Dump parser output')
    parser.add_argument('-dump-sem', action='store_true', help='Dump semantic analysis output')
    parser.add_argument('-dump-ir', action='store_true', help='Dump intermediate representation')
    parser.add_argument('-dump-canon-ir', action='store_true', help='Dump canonized IR')
    parser.add_argument('-dump-assembly', action='store_true', help='Dump output of instruction selection')
    parser.add_argument('-dump-regalloc', action='store_true', help='Dump output of register allocation')
    return parser.parse_args()


def main():
    args = setup_arguments()
    setup_logger()

    logging.info("Starting compilation")

    try:
        with open(args.input_file, "r") as f:
            data = f.read()
    except FileNotFoundError:
        logging.error("Input file not found")
        sys.exit(1)

    # Lexical Analysis
    logging.info("Starting lexical analysis")
    lex.input(data)

    if args.dump_lex:
        # will the following code affect other subsequent phases?
        while True:
            tok = lex.token()
            if not tok:
                break  # No more input
            print(tok)

    # Parsing
    try:
        parsed_program = p.parser.parse(data, le.lexer)
    except p.SyntacticError as err:
        logging.error(f"Syntax error: {err}")
        sys.exit(1)

    if args.dump_parse:
        print(parsed_program)

    # Semantic Analysis and IR Translation
    logging.info("Starting semantic analysis")
    TempMap.initialize()
    try:
        # translate_program(parsed_program)
        typed_exp = translate_program(parsed_program)
    except SemanticError as err:
        logging.error(f"Semantic error: {err}")
        sys.exit(1)

    if args.dump_sem:
        print(typed_exp)

    # IR Processing
    process_fragments = []
    string_fragments = []

    for fragment in FragmentManager.get_fragments():
        if isinstance(fragment, ProcessFragment):
            process_fragments.append(fragment)
        elif isinstance(fragment, StringFragment):
            string_fragments.append(fragment)

    if args.dump_ir:
        # TODO: pretty print (and dump as a dot file?)
        #  Make the basic block more ``explicit'' in the dumped IR?
        for fragment in process_fragments:
            print(fragment.body)

    # Canonization
    logging.info("Starting IR canonization")
    canonized_bodies = [canonize(fragment.body) for fragment in process_fragments]

    if args.dump_canon_ir:
        # Dump the canonized IR
        print(canonized_bodies)

    # Instruction Selection
    logging.info("Starting instruction selection")
    assembly_bodies = [Codegen.codegen(process_body) for process_body in canonized_bodies]

    if args.dump_assembly:
        print(assembly_bodies)

    file_handler = FileHandler("output.s")
    file_handler.print_data_header()
    for string_fragment in string_fragments:
        file_handler.print_string_fragment(string_fragment)

    file_handler.print_code_header()

    # Register Allocation
    logging.info("Starting register allocation")
    bodies_with_sink = [sink(assembly_body) for assembly_body in assembly_bodies]
    for body, fragment in zip(bodies_with_sink, process_fragments):
        allocation_result = RegisterAllocator(fragment.frame).main(body)
        TempMap.update_temp_to_register(allocation_result.temp_to_register)
        instruction_list = [
            instruction
            for instruction in allocation_result.instructions
            if not is_redundant_move(instruction)
        ]
        procedure = assembly_procedure(fragment.frame, instruction_list)
        file_handler.print_assembly_procedure(procedure)

    if args.dump_regalloc:
        print(file_handler)

    logging.info("Compilation completed successfully")


if __name__ == "__main__":
    main()
