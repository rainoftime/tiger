"""
Activation Records and Stack Frame Management for Tiger Compiler

This module implements activation records (stack frames) for the Tiger compiler,
managing function call conventions, local variable storage, and register usage
in the x86-64 architecture.

Key Components:
- **Stack Frame Layout**: Memory organization for function locals and temporaries
- **Register Management**: Mapping between abstract temps and physical registers
- **Access Methods**: In-frame (memory) vs in-register storage for variables
- **Calling Conventions**: Parameter passing and return value handling

x86-64 Architecture Features:
- 64-bit pointers and word size
- System V ABI calling convention
- Separate register classes (argument, callee-saved, caller-saved, special)

Author: Tiger Compiler Project
"""

from typing import List, Dict
from dataclasses import dataclass
from abc import ABC

import intermediate_representation.tree as IRT
import instruction_selection.assembly as Assembly
from activation_records.temp import Temp, TempLabel, TempManager

# =====================================================================
# ARCHITECTURE CONSTANTS
# =====================================================================

# Machine word size in bytes (64-bit architecture)
word_size = 8

# =====================================================================
# REGISTER CLASSIFICATION (System V ABI)
# =====================================================================
# Based on: https://web.stanford.edu/class/archive/cs/cs107/cs107.1216/resources/x86-64-reference.pdf

# A list of registers used to implement "special" registers.
special_registers = ["rip", "rsp", "rax"]

# A list of registers in which to pass outgoing arguments
# (including the static link).
argument_registers = ["rdi", "rsi", "rdx", "rcx", "r8", "r9"]

# A list of registers that the called procedure (callee) must preserve
# unchanged (or save and restore).
callee_saved_registers = ["rbx", "rbp", "r12", "r13", "r14", "r15"]

# A list of registers that the callee may trash.
caller_saved_registers = ["r10", "r11"]

all_registers = (
        special_registers
        + argument_registers
        + callee_saved_registers
        + caller_saved_registers
)


# =====================================================================
# REGISTER-TO-TEMPORARY MAPPING
# =====================================================================

class TempMap:
    """
    Bidirectional mapping between physical registers and abstract temporaries.

    This class maintains the mapping between concrete x86-64 registers and
    abstract temporary variables used during compilation. The mapping is
    essential for translating between IR temporaries and physical registers.

    Class Attributes:
        register_to_temp (Dict[str, Temp]): Maps register names to temp objects
        temp_to_register (Dict[Temp, str]): Maps temp objects to register names
    """

    # Dictionary mapping register names to temporary objects
    register_to_temp: Dict[str, Temp] = {}

    # Dictionary mapping temporary objects to register names
    temp_to_register: Dict[Temp, str] = {}

    @classmethod
    def initialize(cls):
        """
        Initialize the register-to-temporary mapping for all x86-64 registers.

        Creates a temporary for each physical register and establishes
        the bidirectional mapping needed for register allocation.
        """
        for register in all_registers:
            temp = TempManager.new_temp()
            cls.register_to_temp[register] = temp
            cls.temp_to_register[temp] = register

    @classmethod
    def update_temp_to_register(cls, register_allocation: Dict[Temp, Temp]):
        """
        Update temporary-to-register mapping after register allocation.

        After register allocation assigns physical registers to temporaries,
        this method updates the global mapping to reflect the allocation results.

        Args:
            register_allocation (Dict[Temp, Temp]): Maps allocated temps to their assigned registers
        """
        for temporary in register_allocation:
            # Chain through the allocation to find the final register
            cls.temp_to_register[temporary] = cls.temp_to_register[
                register_allocation[temporary]
            ]


# =====================================================================
# SPECIAL REGISTER ACCESSORS
# =====================================================================

def frame_pointer() -> Temp:
    """
    Get the temporary representing the frame pointer register (rbp).

    The frame pointer is used to access local variables and function
    parameters stored on the stack.

    Returns:
        Temp: Temporary representing the %rbp register
    """
    return TempMap.register_to_temp["rbp"]


def return_value() -> Temp:
    """
    Get the temporary representing the return value register (rax).

    Functions return their values in the %rax register according to
    the System V ABI calling convention.

    Returns:
        Temp: Temporary representing the %rax register
    """
    return TempMap.register_to_temp["rax"]


def temp_to_str(temp: Temp) -> str:
    """
    Convert a temporary to its string representation (register name).

    This function is used after register allocation to get the physical
    register name assigned to a temporary variable.

    Args:
        temp (Temp): The temporary to convert

    Returns:
        str: Register name (e.g., "rax", "rbx", "rbp")

    Raises:
        KeyError: If the temporary has not been assigned a register
    """
    return TempMap.temp_to_register[temp]


# =====================================================================
# VARIABLE ACCESS METHODS
# =====================================================================

class Access(ABC):
    """
    Abstract base class for variable access methods.

    Variables can be stored either in registers (InRegister) or in stack
    frames (InFrame). This class hierarchy represents the different
    ways variables can be accessed in the compiled code.
    """
    pass


@dataclass
class InFrame(Access):
    """
    Variable stored in stack frame memory.

    Represents a local variable or parameter stored at a specific
    offset from the frame pointer (%rbp).

    Attributes:
        offset (int): Byte offset from frame pointer where variable is stored
    """
    offset: int


@dataclass
class InRegister(Access):
    """
    Variable stored in a register.

    Represents a variable that has been allocated to a physical
    register for efficient access.

    Attributes:
        register (Temp): Temporary representing the physical register
    """
    register: Temp


# Frame is the class responsible for:
# * the locations of all the formals.
# * the number of locals allocated so far.
# * the label at which the function's machine code is to begin.
class Frame:
    # Creates a new frame for function "name" with "formalEscapes" list of
    # booleans (list of parameters for function "name"). True means
    # escaped variable.
    def __init__(self, name: TempLabel, formal_escapes: List[bool]):
        self.name = name
        # The previous %rbp value is stored at 0(%rbp).
        # Non-volatile registers are stored starting at -8(%rbp).
        # (subtraction is performed before allocation)
        self.offset = 0

        # [Access] denoting the locations where the formal parameters will be
        # kept at run time, as seen from inside the callee.
        self.formal_parameters = []
        self.local_variables = []

        # Process the parameters passed by registers.
        for escape in formal_escapes[: len(argument_registers)]:
            self._alloc_single_var(escape, self.formal_parameters)

        # Process the extra parameters (stored in the previous frame).
        extra_argument_offset = 16
        for escape in formal_escapes[len(argument_registers):]:
            self.formal_parameters.append(InFrame(extra_argument_offset))
            extra_argument_offset += word_size

    # Allocates a new local variable in the frame. The "escape"
    # variable indicates whether the variable escapes or not.
    def alloc_local(self, escape: bool) -> Access:
        return self._alloc_single_var(escape, self.local_variables)

    # Allocates a single variable or parameter in the frame and adds it
    # to access_list.
    def _alloc_single_var(self, escape: bool, access_list: List[Access]) -> Access:
        if escape:
            self.offset -= word_size
            access_list.append(InFrame(self.offset))
        else:
            access_list.append(InRegister(TempManager.new_temp()))
        return access_list[-1]


# This function is used by Translate to turn a Frame.Access into an IRT.Expression.
# The frame_pointer argument is the address of the stack frame that the access lives in.
# If access is a register access, such as InReg(t82), then the frame_pointer argument
# will be discarded.
def access_to_exp(access: Access, frame_pointer: IRT.Expression) -> IRT.Expression:
    if isinstance(access, InFrame):
        return IRT.Memory(
            IRT.BinaryOperation(
                IRT.BinaryOperator.plus, frame_pointer, IRT.Constant(access.offset)
            )
        )
    if isinstance(access, InRegister):
        return IRT.Temporary(access.register)


# Sometimes we will need to call external functions that as written in C or assembly language
# (such as a function that allocates memory for a Tiger array).
def external_call(
        function_name: str, arguments: List[IRT.Expression]
) -> IRT.Expression:
    return IRT.Call(IRT.Name(TempManager.named_label(function_name)), arguments)


# This applies the view shift of calling a function.
# This means concatenating a sequence of IRT.Moves to the function
# body, where each move changes a register parameter to the place
# from which it is seen from within the function.
def shift_view(frame: Frame, function_body: IRT.Statement) -> IRT.Statement:
    shift_parameters = []
    for access, argument_register in zip(frame.formal_parameters, argument_registers):
        if isinstance(access, InFrame):
            shift_parameters.append(
                IRT.Move(
                    IRT.Memory(
                        IRT.BinaryOperation(
                            IRT.BinaryOperator.plus,
                            IRT.Temporary(frame_pointer()),
                            IRT.Constant(access.offset),
                        )
                    ),
                    IRT.Temporary(TempMap.register_to_temp[argument_register]),
                )
            )
        else:
            shift_parameters.append(
                IRT.Move(
                    IRT.Temporary(access.register),
                    IRT.Temporary(TempMap.register_to_temp[argument_register]),
                )
            )

    return IRT.Sequence(shift_parameters + [function_body])


# This preserves the callee_saved registers across a function call.
# We need to make up new temporaries for each callee-save register. On entry, we move
# all these registers to their new temporary locations, and on exit, we move them back.
def preserve_callee_registers(
        frame: Frame, function_body: IRT.Statement
) -> IRT.Statement:
    save_registers = []
    restore_registers = []
    for callee_register in callee_saved_registers:
        temp = TempManager.new_temp()
        save_registers.append(
            IRT.Move(
                IRT.Temporary(temp),
                IRT.Temporary(TempMap.register_to_temp[callee_register]),
            )
        )
        restore_registers.append(
            IRT.Move(
                IRT.Temporary(TempMap.register_to_temp[callee_register]),
                IRT.Temporary(temp),
            )
        )
    return IRT.Sequence(save_registers + [function_body] + restore_registers)


# This function appends a “sink” instruction to the function body to tell the
# register allocator that certain registers are live at procedure exit.
def sink(function_body: List[Assembly.Instruction]) -> List[Assembly.Instruction]:
    sink_registers = callee_saved_registers + ["rsp", "rip"]
    sink_temps = [TempMap.register_to_temp[register] for register in sink_registers]
    function_body.append(
        Assembly.Operation(line="", source=sink_temps, destination=[], jump=None)
    )
    return function_body


def assembly_procedure(
        frame: Frame, body: List[Assembly.Instruction]
) -> Assembly.Procedure:
    # Prologue
    prologue = f"# PROCEDURE {frame.name}\n"
    prologue += f"{frame.name}:\n"

    # After the call instruction the stack looks like this:
    # *       ...        *
    # *      arg 7       *<- %rsp + 8
    # *   ------------   *
    # * return  adddress *<- %rsp
    # *       🚮         *<- %rsp - 8
    # *       🚮         *<- %rsp - 16
    # *       ...        *<- %rsp - 24

    # After the prologue, it should look like this:
    # (the locals aren't stored yet, but the space is reserved)
    # *       ...        *
    # *      arg 7       *<- %rbp + 16
    # *   ------------   *
    # * return  adddress *<- %rbp + 8
    # *   previous rbp   *<- %rbp
    # *   local 1 (sl)   *<- %rbp - 8
    # *       ...        *<- %rbp - 16
    # *     local n      *<- %rsp

    prologue += "pushq %rbp\n"  # push rbp onto the stack
    prologue += "movq %rsp, %rbp\n"  # rbp <- rsp, now rbp points to the old rbp

    # Here stack space is reserved only for formal parameters and local variables.
    # Stack space for outgoing arguments is reserved in codegen (when munching
    # IRT.Call).
    # The amount of stack space necessary for formal parameters and local variables
    # is equal to word_size * amount of InFrames.
    # Each time an InFrame is created, frame.offset decreases by word_size.
    # Align the stack_size to 16 bytes.
    stack_size = -frame.offset - (frame.offset % -16)
    prologue += f"subq ${stack_size}, %rsp\n"
    prologue += "\n\n"
    # Epilogue
    epilogue = "\n\n"
    # Move rsp to where the old rbp value was stored.
    epilogue += "movq %rbp, %rsp\n"
    epilogue += "popq %rbp\n"  # Restore old rbp value.
    epilogue += "ret\n"
    epilogue += f"# END {frame.name}\n"

    return Assembly.Procedure(prologue, body, epilogue)


def string_literal(label: TempLabel, string: str) -> str:
    return f"{label}:\n\t.asciz {string}\n"
