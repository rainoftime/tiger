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
    label: TempLabel
    statement_lists: List[List[Statement]]


def basic_block(statements: List[Statement]) -> BasicBlock:
    """
    创建一个新的结束标签 done_label。
    初始化 statement_lists 和 block_start_index。
    遍历输入的语句列表，根据 Label、Jump 和 ConditionalJump 将语句划分为多个基本块。
    为每个基本块添加必要的标签和跳转语句。
    返回一个包含所有基本块的 BasicBlock 对象？
    """
    done_label = TempManager.new_label()
    statement_lists = []

    block_start_index = 0
    for index, statement in enumerate(statements):
        if isinstance(statement, Label):
            # If the label is supposed to be the beginning of a new block, we do not end the
            # previous block since it was already ended by a jump.
            # If not, then we end the previous block and start the new one with the current label.
            if block_start_index < index:
                statement_lists.append(statements[block_start_index:index])
                block_start_index = index
        elif isinstance(statement, Jump) or isinstance(statement, ConditionalJump):
            statement_lists.append(statements[block_start_index: index + 1])
            block_start_index = index + 1
    last_block = statements[block_start_index: len(statements)] + [
        Jump(Name(done_label), [done_label])
    ]
    statement_lists.append(last_block)

    for index, statement_list in enumerate(statement_lists):
        if not isinstance(statement_list[0], Label):
            statement_lists[index] = [Label(TempManager.new_label())] + statement_list

    for index, statement_list in enumerate(statement_lists[:-1]):
        if not isinstance(statement_list[-1], Jump) and not isinstance(
                statement_list[-1], ConditionalJump
        ):
            next_block_label = statement_lists[index + 1][0]
            statement_lists[index] = statement_list + [
                Jump(Name(next_block_label.label), [next_block_label.label])
            ]
    return BasicBlock(done_label, statement_lists)
