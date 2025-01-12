import instruction_selection.assembly as Assembly
from activation_records.frame import TempMap


def is_redundant_move(instruction: Assembly.Instruction) -> bool:
    if (
            not isinstance(instruction, Assembly.Move)
            or len(instruction.source) != 1
            or len(instruction.destination) != 1
    ):
        return False

    return (
            TempMap.temp_to_register[instruction.source[0]]
            == TempMap.temp_to_register[instruction.destination[0]]
    )
