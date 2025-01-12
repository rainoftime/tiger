from typing import List

from activation_records.temp import TempLabel, TempManager
from canonical.basic_block import BasicBlock
from intermediate_representation.tree import (
    Statement,
    Jump,
    ConditionalJump,
    negate_relational_operator,
    Label,
    Name,
)


def block_label(statements: List[Statement]) -> TempLabel:
    return statements[0].label


def add_new_false_label(statements: List[Statement]):
    new_false_label = TempManager.new_label()
    statements[-1].false = new_false_label
    statements.append(Label(new_false_label))
    statements.append(Jump(Name(new_false_label), [new_false_label]))


def reorder_blocks(statement_lists: List[List[Statement]]) -> List[List[Statement]]:
    unmarked_blocks = {
        block_label(statements): statements for statements in statement_lists
    }
    result = []
    for block in statement_lists:
        current_block = block
        while block_label(current_block) in unmarked_blocks:
            unmarked_blocks.pop(block_label(current_block))
            result.append(current_block)
            last_statement = current_block[-1]
            if isinstance(last_statement, Jump):
                target_label = last_statement.labels[0]
                if target_label in unmarked_blocks:
                    current_block = unmarked_blocks[target_label]
            elif isinstance(last_statement, ConditionalJump):
                if last_statement.false in unmarked_blocks:
                    current_block = unmarked_blocks[last_statement.false]
                elif last_statement.true in unmarked_blocks:
                    current_block = unmarked_blocks[last_statement.true]
    return result


def fix_jumps(statement_lists: List[List[Statement]]):
    for index, statements in enumerate(statement_lists[:-1]):
        last_statement = statements[-1]
        if isinstance(last_statement, Jump):
            jump_label = last_statement.labels[0]
            next_block_label = block_label(statement_lists[index + 1])
            if next_block_label == jump_label:
                statement_lists[index] = statement_lists[index][:-1]

        elif isinstance(last_statement, ConditionalJump):
            true_label = last_statement.true
            false_label = last_statement.false
            next_block_label = block_label(statement_lists[index + 1])

            if next_block_label != true_label and next_block_label != false_label:
                add_new_false_label(statements)

            elif next_block_label == true_label:
                last_statement.true = false_label
                last_statement.false = true_label
                last_statement.operator = negate_relational_operator(
                    last_statement.operator
                )

    last_list = statement_lists[-1]
    if isinstance(last_list[-1], ConditionalJump):
        add_new_false_label(last_list)


def trace_schedule(block: BasicBlock) -> List[Statement]:
    reordered_blocks = reorder_blocks(block.statement_lists)
    reordered_blocks.append([Label(block.label)])
    fix_jumps(reordered_blocks)
    return [statement for block in reordered_blocks for statement in block]
