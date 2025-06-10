import argparse
import sys
from pathlib import Path

# Support both old and new architecture systems
try:
    from activation_records.architecture_frame import (
        set_architecture_frame, reinitialize_temp_map, ArchFrame,
        get_supported_architecture_frames, arch_temp_map, sink, assembly_procedure
    )
    from instruction_selection.codegen import get_supported_architectures
    MULTI_ARCH_SUPPORT = True
except ImportError:
    from activation_records.frame import TempMap, sink, assembly_procedure
    MULTI_ARCH_SUPPORT = False

# Use unified components
from register_allocation.allocation import RegisterAllocator
from putting_it_all_together.file_handler import FileHandler, get_output_handlers

# Common imports
from activation_records.instruction_removal import is_redundant_move
from canonical.canonize import canonize
from intermediate_representation.fragment import (
    FragmentManager, ProcessFragment, StringFragment
)
from semantic_analysis.analyzers import SemanticError, translate_program
from instruction_selection.codegen import Codegen
from lexer import lex as le
from parser import parser as p
from ply import lex


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Tiger Compiler')
    parser.add_argument('input_file', help='Input Tiger source file')
    
    if MULTI_ARCH_SUPPORT:
        parser.add_argument('--arch', choices=['x86-64', 'arm64', 'riscv'], 
                          default='x86-64', help='Target architecture (default: x86-64)')
        parser.add_argument('-o', '--output', help='Output file name (without extension)')
    
    return parser.parse_args()


def setup_architecture(arch_name: str):
    """Setup the compiler for the specified architecture"""
    if not MULTI_ARCH_SUPPORT:
        return None, None, None
    
    code_gen_archs = get_supported_architectures()
    frame_archs = get_supported_architecture_frames()
    output_handlers = get_output_handlers()
    
    if arch_name not in code_gen_archs or arch_name not in frame_archs or arch_name not in output_handlers:
        print(f"Error: {arch_name} not fully supported")
        return None, None, None
    
    code_gen_arch = code_gen_archs[arch_name]
    frame_arch = frame_archs[arch_name]
    output_handler = output_handlers[arch_name]
    
    Codegen.set_target_architecture(code_gen_arch)
    set_architecture_frame(frame_arch)
    reinitialize_temp_map()
    
    return code_gen_arch, frame_arch, output_handler


def read_input_file(input_file: str) -> str:
    """Read and return the contents of the input file"""
    try:
        with open(input_file, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    except IOError as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)


def parse_and_analyze(data: str):
    """Parse and perform semantic analysis"""
    # Lexical and Syntactic Analysis
    lex.input(data)
    try:
        parsed_program = p.parser.parse(data, le.lexer)
    except p.SyntacticError as err:
        print(f"Syntax Error: {err}")
        sys.exit(1)
    
    # Semantic Analysis
    if MULTI_ARCH_SUPPORT:
        arch_temp_map.initialize()
    else:
        TempMap.initialize()
    
    try:
        translate_program(parsed_program)
    except SemanticError as err:
        print(f"Semantic Error: {err}")
        sys.exit(1)


def process_fragments():
    """Separate and canonize fragments"""
    process_fragments = []
    string_fragments = []
    
    for fragment in FragmentManager.get_fragments():
        if isinstance(fragment, ProcessFragment):
            process_fragments.append(fragment)
        elif isinstance(fragment, StringFragment):
            string_fragments.append(fragment)
    
    canonized_bodies = [canonize(fragment.body) for fragment in process_fragments]
    return process_fragments, string_fragments, canonized_bodies


def generate_assembly(canonized_bodies, process_fragments, string_fragments, 
                     output_file: str, output_handler=None):
    """Generate assembly code and write to file"""
    # Instruction Selection
    assembly_bodies = [Codegen.codegen(body) for body in canonized_bodies]
    
    # Create unified file handler
    file_handler = FileHandler(output_file, output_handler)
    
    # Write data section
    file_handler.print_data_header()
    for string_fragment in string_fragments:
        file_handler.print_string_fragment(string_fragment)
    
    file_handler.print_code_header()
    
    # Register Allocation and Assembly Generation
    bodies_with_sink = [sink(assembly_body) for assembly_body in assembly_bodies]
    
    for body, fragment in zip(bodies_with_sink, process_fragments):
        if MULTI_ARCH_SUPPORT:
            # Create architecture-aware frame
            arch_frame = ArchFrame(fragment.frame.name, [])
            arch_frame.formal_parameters = fragment.frame.formal_parameters
            arch_frame.local_variables = fragment.frame.local_variables
            allocation_result = RegisterAllocator(arch_frame).main(body)
            arch_temp_map.update_temp_to_register(allocation_result.temp_to_register)
            
            instruction_list = [
                instruction for instruction in allocation_result.instructions
                if not is_redundant_move(instruction)
            ]
            procedure = assembly_procedure(arch_frame, instruction_list)
        else:
            allocation_result = RegisterAllocator(fragment.frame).main(body)
            TempMap.update_temp_to_register(allocation_result.temp_to_register)
            
            instruction_list = [
                instruction for instruction in allocation_result.instructions
                if not is_redundant_move(instruction)
            ]
            procedure = assembly_procedure(fragment.frame, instruction_list)
        
        file_handler.print_assembly_procedure(procedure)
    
    file_handler.close()


def compile_tiger_program(input_file: str, arch_name: str = 'x86-64', output_file: str = None):
    """Main compilation pipeline"""
    print(f"Compiling '{input_file}' for {arch_name}...")
    
    # Setup architecture if multi-arch is supported
    output_handler = None
    if MULTI_ARCH_SUPPORT:
        _, _, output_handler = setup_architecture(arch_name)
        if output_handler is None and arch_name != 'x86-64':
            return False
    
    # Read and parse input
    data = read_input_file(input_file)
    parse_and_analyze(data)
    
    # Process fragments
    process_fragments, string_fragments, canonized_bodies = process_fragments()
    
    # Determine output filename
    if output_file is None:
        if arch_name == 'x86-64':
            output_file = "output"
        else:
            input_path = Path(input_file)
            output_file = input_path.stem + "_" + arch_name.replace("-", "_")
    
    # Generate assembly
    generate_assembly(canonized_bodies, process_fragments, string_fragments, 
                     output_file, output_handler)
    
    # Print success message
    if MULTI_ARCH_SUPPORT and output_handler:
        output_filename = output_file + output_handler.get_file_extension()
    else:
        output_filename = output_file + ".s"
    
    print(f"Compilation successful! Output: {output_filename}")
    return True


def main():
    """Main compiler entry point"""
    # Handle legacy single-argument case
    if len(sys.argv) == 2 and not sys.argv[1].startswith('-'):
        compile_tiger_program(sys.argv[1])
        return
    
    # Parse arguments
    try:
        args = parse_arguments()
    except SystemExit:
        return
    
    print("Tiger Compiler")
    print("=" * 20)
    
    arch_name = getattr(args, 'arch', 'x86-64')
    output_file = getattr(args, 'output', None)
    
    success = compile_tiger_program(args.input_file, arch_name, output_file)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
