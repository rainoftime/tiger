#!/usr/bin/env python3
"""
Tiger Compiler - Main Entry Point

This module serves as the main entry point for the Tiger programming language compiler.
It orchestrates the entire compilation pipeline from source code to assembly output,
supporting multiple target architectures when available.

The compilation process follows these stages:
1. Lexical and Syntactic Analysis
2. Semantic Analysis and IR Translation
3. Canonicalization
4. Instruction Selection
5. Register Allocation
6. Assembly Code Generation

Author: Tiger Compiler Team
"""

import argparse
import sys
from pathlib import Path

# Support both old and new architecture systems
# This allows the compiler to work with either single-architecture or multi-architecture setups
try:
    from activation_records.architecture_frame import (
        set_architecture_frame, reinitialize_temp_map, ArchFrame,
        get_supported_architecture_frames, arch_temp_map, sink, assembly_procedure
    )
    from instruction_selection.codegen import get_supported_architectures
    MULTI_ARCH_SUPPORT = True
except ImportError:
    # Fallback to single-architecture support
    from activation_records.frame import TempMap, sink, assembly_procedure
    MULTI_ARCH_SUPPORT = False

# Use unified components for compilation pipeline
from register_allocation.allocation import RegisterAllocator
from putting_it_all_together.file_handler import FileHandler, get_output_handlers

# Common imports for all compilation stages
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
    """
    Parse command line arguments for the Tiger compiler.
    
    Returns:
        argparse.Namespace: Parsed command line arguments containing:
            - input_file: Path to the Tiger source file to compile
            - arch: Target architecture (if multi-arch support is available)
            - output: Output file name without extension (optional)
    """
    parser = argparse.ArgumentParser(description='Tiger Compiler')
    parser.add_argument('input_file', help='Input Tiger source file')
    
    # Add architecture-specific options if multi-arch support is available
    if MULTI_ARCH_SUPPORT:
        parser.add_argument('--arch', choices=['x86-64', 'arm64', 'riscv'], 
                          default='x86-64', help='Target architecture (default: x86-64)')
        parser.add_argument('-o', '--output', help='Output file name (without extension)')
    
    return parser.parse_args()


def setup_architecture(arch_name: str):
    """
    Configure the compiler for the specified target architecture.
    
    This function sets up architecture-specific code generation, frame layout,
    and output handling components. It ensures all components are compatible
    with the selected architecture.
    
    Args:
        arch_name (str): Name of the target architecture ('x86-64', 'arm64', or 'riscv')
        
    Returns:
        tuple: (code_gen_arch, frame_arch, output_handler) or (None, None, None) if unsupported
    """
    if not MULTI_ARCH_SUPPORT:
        return None, None, None
    
    # Get available architecture components
    code_gen_archs = get_supported_architectures()
    frame_archs = get_supported_architecture_frames()
    output_handlers = get_output_handlers()
    
    # Verify architecture is fully supported across all components
    if arch_name not in code_gen_archs or arch_name not in frame_archs or arch_name not in output_handlers:
        print(f"Error: {arch_name} not fully supported")
        return None, None, None
    
    # Extract architecture-specific components
    code_gen_arch = code_gen_archs[arch_name]
    frame_arch = frame_archs[arch_name]
    output_handler = output_handlers[arch_name]
    
    # Configure global compiler state for the target architecture
    Codegen.set_target_architecture(code_gen_arch)
    set_architecture_frame(frame_arch)
    reinitialize_temp_map()
    
    return code_gen_arch, frame_arch, output_handler


def read_input_file(input_file: str) -> str:
    """
    Read the contents of the Tiger source file.
    
    Args:
        input_file (str): Path to the Tiger source file
        
    Returns:
        str: Contents of the source file
        
    Exits:
        System exit with code 1 if file cannot be read
    """
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
    """
    Perform lexical analysis, parsing, and semantic analysis on the source code.
    
    This function runs the first three phases of compilation:
    1. Lexical analysis - tokenizes the input
    2. Syntactic analysis - builds an abstract syntax tree
    3. Semantic analysis - type checking and IR translation
    
    Args:
        data (str): Tiger source code to analyze
        
    Exits:
        System exit with code 1 if syntax or semantic errors are found
    """
    # Lexical and Syntactic Analysis
    lex.input(data)
    try:
        parsed_program = p.parser.parse(data, le.lexer)
    except p.SyntacticError as err:
        print(f"Syntax Error: {err}")
        sys.exit(1)
    
    # Initialize temporary variable mapping system
    if MULTI_ARCH_SUPPORT:
        arch_temp_map.initialize()
    else:
        TempMap.initialize()
    
    # Semantic Analysis - type checking and IR translation
    try:
        translate_program(parsed_program)
    except SemanticError as err:
        print(f"Semantic Error: {err}")
        sys.exit(1)


def process_fragments():
    """
    Separate and canonize intermediate representation fragments.
    
    Fragments are divided into two categories:
    - ProcessFragment: Contains executable code (functions/procedures)
    - StringFragment: Contains string literals for the data section
    
    Returns:
        tuple: (process_fragments, string_fragments, canonized_bodies)
            - process_fragments: List of executable code fragments
            - string_fragments: List of string literal fragments
            - canonized_bodies: List of canonicalized IR trees for each process fragment
    """
    process_fragments = []
    string_fragments = []
    
    # Separate fragments by type
    for fragment in FragmentManager.get_fragments():
        if isinstance(fragment, ProcessFragment):
            process_fragments.append(fragment)
        elif isinstance(fragment, StringFragment):
            string_fragments.append(fragment)
    
    # Canonicalize IR trees to linearize control flow
    canonized_bodies = [canonize(fragment.body) for fragment in process_fragments]
    return process_fragments, string_fragments, canonized_bodies


def generate_assembly(canonized_bodies, process_fragments, string_fragments, 
                     output_file: str, output_handler=None):
    """
    Generate assembly code from canonicalized intermediate representation.
    
    This function performs the final stages of compilation:
    1. Instruction selection - convert IR to assembly instructions
    2. Register allocation - assign physical registers to temporaries
    3. Assembly output - write final assembly code to file
    
    Args:
        canonized_bodies: List of canonicalized IR trees
        process_fragments: List of process fragments (functions/procedures)
        string_fragments: List of string fragments for data section
        output_file (str): Base name for output file
        output_handler: Architecture-specific output handler (optional)
    """
    # Instruction Selection - convert IR trees to assembly instructions
    assembly_bodies = [Codegen.codegen(body) for body in canonized_bodies]
    
    # Create unified file handler for assembly output
    file_handler = FileHandler(output_file, output_handler)
    
    # Write data section with string literals
    file_handler.print_data_header()
    for string_fragment in string_fragments:
        file_handler.print_string_fragment(string_fragment)
    
    # Write code section header
    file_handler.print_code_header()
    
    # Add sink instruction to handle function return values
    bodies_with_sink = [sink(assembly_body) for assembly_body in assembly_bodies]
    
    # Process each function/procedure
    for body, fragment in zip(bodies_with_sink, process_fragments):
        if MULTI_ARCH_SUPPORT:
            # Create architecture-aware frame for multi-arch support
            arch_frame = ArchFrame(fragment.frame.name, [])
            arch_frame.formal_parameters = fragment.frame.formal_parameters
            arch_frame.local_variables = fragment.frame.local_variables
            
            # Perform register allocation
            allocation_result = RegisterAllocator(arch_frame).main(body)
            arch_temp_map.update_temp_to_register(allocation_result.temp_to_register)
            
            # Remove redundant move instructions
            instruction_list = [
                instruction for instruction in allocation_result.instructions
                if not is_redundant_move(instruction)
            ]
            procedure = assembly_procedure(arch_frame, instruction_list)
        else:
            # Single-architecture path
            allocation_result = RegisterAllocator(fragment.frame).main(body)
            TempMap.update_temp_to_register(allocation_result.temp_to_register)
            
            # Remove redundant move instructions
            instruction_list = [
                instruction for instruction in allocation_result.instructions
                if not is_redundant_move(instruction)
            ]
            procedure = assembly_procedure(fragment.frame, instruction_list)
        
        # Write the assembly procedure to output file
        file_handler.print_assembly_procedure(procedure)
    
    file_handler.close()


def compile_tiger_program(input_file: str, arch_name: str = 'x86-64', output_file: str = None):
    """
    Execute the complete Tiger compilation pipeline.
    
    This is the main compilation function that orchestrates all compilation phases
    from source code parsing to assembly generation.
    
    Args:
        input_file (str): Path to the Tiger source file
        arch_name (str): Target architecture name (default: 'x86-64')
        output_file (str): Output file name without extension (optional)
        
    Returns:
        bool: True if compilation succeeded, False otherwise
    """
    print(f"Compiling '{input_file}' for {arch_name}...")
    
    # Setup architecture-specific components if multi-arch is supported
    output_handler = None
    if MULTI_ARCH_SUPPORT:
        _, _, output_handler = setup_architecture(arch_name)
        if output_handler is None and arch_name != 'x86-64':
            return False
    
    # Phase 1-3: Read, parse, and analyze source code
    data = read_input_file(input_file)
    parse_and_analyze(data)
    
    # Phase 4: Process and canonicalize IR fragments
    process_fragments, string_fragments, canonized_bodies = process_fragments()
    
    # Determine output filename if not specified
    if output_file is None:
        if arch_name == 'x86-64':
            output_file = "output"
        else:
            input_path = Path(input_file)
            output_file = input_path.stem + "_" + arch_name.replace("-", "_")
    
    # Phase 5-7: Generate assembly code
    generate_assembly(canonized_bodies, process_fragments, string_fragments, 
                     output_file, output_handler)
    
    # Print success message with output filename
    if MULTI_ARCH_SUPPORT and output_handler:
        output_filename = output_file + output_handler.get_file_extension()
    else:
        output_filename = output_file + ".s"
    
    print(f"Compilation successful! Output: {output_filename}")
    return True


def main():
    """
    Main compiler entry point.
    
    Handles command line argument parsing and initiates the compilation process.
    Supports both legacy single-argument usage and modern multi-architecture usage.
    """
    # Handle legacy single-argument case for backward compatibility
    if len(sys.argv) == 2 and not sys.argv[1].startswith('-'):
        compile_tiger_program(sys.argv[1])
        return
    
    # Parse modern command line arguments
    try:
        args = parse_arguments()
    except SystemExit:
        return
    
    print("Tiger Compiler")
    print("=" * 20)
    
    # Extract arguments with defaults for backward compatibility
    arch_name = getattr(args, 'arch', 'x86-64')
    output_file = getattr(args, 'output', None)
    
    # Execute compilation pipeline
    success = compile_tiger_program(args.input_file, arch_name, output_file)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
