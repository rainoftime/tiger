"""
Basic Block Formation for Tiger Compiler

This module implements basic block formation as part of the canonical transformation
phase of the Tiger compiler. Basic blocks are maximal sequences of statements with
no internal jumps or jump targets (except at the beginning).

The basic block formation algorithm:
1. Identifies statement boundaries based on labels and control flow
2. Groups statements into linear sequences (basic blocks)
3. Ensures each block has proper entry and exit points
4. Adds necessary jump statements between blocks

Key Concepts:
- Basic Block: A sequence of statements with single entry and exit points
- Leader: First statement of a basic block (labeled or jump target)
- Block Formation: Grouping statements until next leader is encountered

Author: Tiger Compiler Project
"""

from typing import List
from dataclasses import dataclass

from activation_records.temp import TempLabel, TempManager
from intermediate_representation.tree import (
    Statement,
    Label,
    Jump,
    ConditionalJump,
    Name,
)


@dataclass
class BasicBlock:
    """
    Represents a basic block in the intermediate representation.

    A basic block is a maximal sequence of consecutive statements in which
    flow of control enters at the beginning and leaves at the end without
    halt or possibility of branching except at the end.

    Attributes:
        label (TempLabel): The label marking the start of this basic block
        statement_lists (List[List[Statement]]): List of statement sequences,
                                                where each sequence is a basic block
    """
    label: TempLabel
    statement_lists: List[List[Statement]]


def basic_block(statements: List[Statement]) -> BasicBlock:
    """
    Convert a linear sequence of statements into basic blocks.

    This function performs basic block formation by identifying statement
    boundaries based on control flow instructions and labels. The algorithm:

    1. Scans statements to identify block boundaries (labels, jumps, calls)
    2. Groups statements into basic blocks (sequences with single entry/exit)
    3. Adds explicit jumps between blocks to maintain control flow
    4. Ensures each block starts with a label

    Args:
        statements (List[Statement]): Linear sequence of IR statements

    Returns:
        BasicBlock: Structured representation with basic blocks and connecting jumps

    Note:
        The function creates a final jump to a 'done' label to ensure
        the last block has a proper exit point.
    """
    # Create a synthetic 'done' label for the function exit
    done_label = TempManager.new_label()
    statement_lists = []
    block_start_index = 0

    # Phase 1: Identify basic block boundaries
    # Scan through statements to find where blocks should be split
    for index, statement in enumerate(statements):
        if isinstance(statement, Label):
            # Labels start new blocks, but only if not already at a block boundary
            if block_start_index < index:
                # End previous block before this label
                statement_lists.append(statements[block_start_index:index])
                block_start_index = index
        elif isinstance(statement, Jump) or isinstance(statement, ConditionalJump):
            # Control flow statements end the current block
            # Include the jump/conditional jump in the current block
            statement_lists.append(statements[block_start_index: index + 1])
            block_start_index = index + 1

    # Handle the final block (from last block start to end of function)
    # Add a jump to the synthetic 'done' label to ensure proper termination
    last_block = statements[block_start_index: len(statements)] + [
        Jump(Name(done_label), [done_label])
    ]
    statement_lists.append(last_block)

    # Phase 2: Ensure all blocks start with labels
    # Add synthetic labels to any blocks that don't start with one
    for index, statement_list in enumerate(statement_lists):
        if not isinstance(statement_list[0], Label):
            # Insert a new label at the beginning of this block
            statement_lists[index] = [Label(TempManager.new_label())] + statement_list

    # Phase 3: Add explicit jumps between consecutive blocks
    # Ensure control flows properly from one block to the next
    for index, statement_list in enumerate(statement_lists[:-1]):
        # Check if the current block doesn't end with a control flow statement
        if not isinstance(statement_list[-1], Jump) and not isinstance(
                statement_list[-1], ConditionalJump
        ):
            # Add a jump to the next block's label
            next_block_label = statement_lists[index + 1][0]
            statement_lists[index] = statement_list + [
                Jump(Name(next_block_label.label), [next_block_label.label])
            ]

    # Return the structured basic block representation
    return BasicBlock(done_label, statement_lists)
