#!/usr/bin/env bash
#
# Tiger Compiler Build Script
#
# This script provides a complete compilation pipeline for Tiger programs,
# from source code to executable binary. It orchestrates the Tiger compiler
# and system linker to produce a runnable program.
#
# Compilation Process:
# 1. Run the Tiger compiler to generate assembly code
# 2. Compile the runtime support library
# 3. Link the generated assembly with the runtime library
# 4. Clean up intermediate files
#
# Usage:
#     ./compile.sh <tiger_source_file>
#
# Example:
#     ./compile.sh examples/test1.tig
#
# Requirements:
# - Python 3 with Tiger compiler modules
# - GCC compiler for linking
# - Runtime support library (runtime.c)
#
# Author: Tiger Compiler Team

# TODO: Adjust commands based on the current environment
# (e.g., Architecture, OS, C compiler, etc.)

# Step 1: Compile Tiger source to assembly
# Run the Tiger compiler on the input file
echo "Compiling Tiger source file: $1"
python3 main.py "$1"

# Check if Tiger compilation was successful
if [ $? -eq 0 ]; then
    echo "Tiger compilation successful, proceeding with linking..."
    
    # Step 2: Compile the runtime support library
    # The runtime provides essential functions like print, memory allocation, etc.
    echo "Compiling runtime support library..."
    gcc -c putting_it_all_together/runtime.c
    
    # Step 3: Link the generated assembly with the runtime library
    # -no-pie: Disable position-independent executable for compatibility
    # -g: Include debugging information
    echo "Linking assembly code with runtime library..."
    gcc -no-pie -g output.s runtime.o
    
    # Step 4: Clean up intermediate files
    # Remove temporary assembly and object files
    echo "Cleaning up intermediate files..."
    rm "output.s"
    rm "runtime.o"
    
    echo "Compilation complete! Executable: ./a.out"
else
    echo "Tiger compilation failed. Aborting build process."
    exit 1
fi