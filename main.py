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
    if len(sys.argv) == 1:
        print("Fatal error. No input file detected.")
        sys.exit(1)

    f = open(sys.argv[1], "r")
    data = f.read()
    f.close()

    # Lexical Analysis
    lex.input(data)
    try:
        parsed_program = p.parser.parse(data, le.lexer)
    except p.SyntacticError as err:
        print(err)
        sys.exit(1)

    # Semantic Analysis and Intermediate Representation Translation
    TempMap.initialize()
    try:
        translate_program(
            parsed_program,
        )
    except SemanticError as err:
        print(err)
        sys.exit(1)

    # Canonization
    process_fragments = []
    string_fragments = []

    for fragment in FragmentManager.get_fragments():
        if isinstance(fragment, ProcessFragment):
            process_fragments.append(fragment)

        elif isinstance(fragment, StringFragment):
            string_fragments.append(fragment)

    canonized_bodies = [canonize(fragment.body) for fragment in process_fragments]
    # Instruction Selection
    assembly_bodies = [
        Codegen.codegen(process_body) for process_body in canonized_bodies
    ]

    file_handler = FileHandler("output.s")
    file_handler.print_data_header()
    for string_fragment in string_fragments:
        file_handler.print_string_fragment(string_fragment)

    file_handler.print_code_header()
    # Register Allocation
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


if __name__ == "__main__":
    main()
