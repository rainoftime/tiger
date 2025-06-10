#!/usr/bin/env python3
"""
Example demonstrating multi-architecture code generation support.

This example shows how to generate assembly code for the same intermediate
representation across different target architectures: x86-64, ARM64, and RISC-V.
"""

import sys
import os

# Add the parent directory to sys.path to import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import intermediate_representation.tree as IRT
import activation_records.temp as Temp
from instruction_selection.codegen import (
    Codegen, X86_64Architecture, ARMArchitecture, RISCVArchitecture
)


def create_sample_ir() -> list[IRT.Statement]:
    """Create a sample intermediate representation for demonstration."""
    
    # Create some temporaries
    temp1 = Temp.TempManager.new_temp()
    temp2 = Temp.TempManager.new_temp() 
    temp3 = Temp.TempManager.new_temp()
    result_temp = Temp.TempManager.new_temp()
    
    # Create some labels
    start_label = Temp.TempManager.named_label("start")
    end_label = Temp.TempManager.named_label("end")
    
    # Build a simple program:
    # start:
    #   temp1 = 10
    #   temp2 = 20  
    #   temp3 = temp1 + temp2
    #   if temp3 > 25 goto end
    #   result_temp = temp3 * 2
    # end:
    #   return result_temp
    
    statements = [
        # Label: start
        IRT.Label(start_label),
        
        # temp1 = 10
        IRT.Move(
            IRT.Temporary(temp1),
            IRT.Constant(10)
        ),
        
        # temp2 = 20
        IRT.Move(
            IRT.Temporary(temp2),
            IRT.Constant(20)
        ),
        
        # temp3 = temp1 + temp2
        IRT.Move(
            IRT.Temporary(temp3),
            IRT.BinaryOperation(
                IRT.BinaryOperator.plus,
                IRT.Temporary(temp1),
                IRT.Temporary(temp2)
            )
        ),
        
        # if temp3 > 25 goto end
        IRT.ConditionalJump(
            IRT.RelationalOperator.gt,
            IRT.Temporary(temp3),
            IRT.Constant(25),
            end_label,
            "continue"
        ),
        
        # result_temp = temp3 * 2
        IRT.Move(
            IRT.Temporary(result_temp),
            IRT.BinaryOperation(
                IRT.BinaryOperator.mul,
                IRT.Temporary(temp3),
                IRT.Constant(2)
            )
        ),
        
        # Label: end
        IRT.Label(end_label)
    ]
    
    return statements


def generate_code_for_architecture(arch, arch_name: str, ir_statements: list[IRT.Statement]):
    """Generate and display assembly code for a specific architecture."""
    
    print(f"\n{'='*50}")
    print(f"Code generation for {arch_name}")
    print(f"{'='*50}")
    
    # Set the target architecture
    Codegen.set_target_architecture(arch)
    
    # Generate assembly instructions
    instructions = Codegen.codegen(ir_statements)
    
    # Display the generated assembly
    print(f"\nGenerated {arch_name} Assembly:")
    print("-" * 30)
    
    for i, instruction in enumerate(instructions):
        print(f"{i+1:2d}: {instruction.line.rstrip()}")
    
    return instructions


def main():
    """Main function demonstrating multi-architecture code generation."""
    
    print("Multi-Architecture Code Generation Demo")
    print("======================================")
    
    # Create sample intermediate representation
    ir_statements = create_sample_ir()
    
    print("\nIntermediate Representation (IR):")
    print("-" * 35)
    for i, stmt in enumerate(ir_statements):
        print(f"{i+1:2d}: {type(stmt).__name__}: {stmt}")
    
    # Generate code for each supported architecture
    architectures = [
        (X86_64Architecture(), "x86-64"),
        (ARMArchitecture(), "ARM64"),
        (RISCVArchitecture(), "RISC-V")
    ]
    
    generated_code = {}
    
    for arch, arch_name in architectures:
        try:
            instructions = generate_code_for_architecture(arch, arch_name, ir_statements)
            generated_code[arch_name] = instructions
        except Exception as e:
            print(f"\nError generating code for {arch_name}: {e}")
            continue
    
    # Summary
    print(f"\n{'='*50}")
    print("Summary")
    print(f"{'='*50}")
    
    for arch_name, instructions in generated_code.items():
        print(f"{arch_name:>10}: {len(instructions)} instructions generated")
    
    print(f"\nSuccessfully demonstrated code generation for {len(generated_code)} architectures")


if __name__ == "__main__":
    main() 