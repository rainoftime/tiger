from typing import List, Dict

from dataclasses import dataclass

from abc import ABC
import intermediate_representation.tree as IRT
import instruction_selection.assembly as Assembly

from activation_records.temp import Temp, TempLabel, TempManager

# Constant for the machine's word size.
word_size = 8

# The register lists should not overlap according to Appel, but some are
# ambiguous (like rbp, which is "special" but also callee-saved).
# The assignment to each list has been done in accordance to:
# https://web.stanford.edu/class/archive/cs/cs107/cs107.1216/resources/x86-64-reference.pdf

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


# Bidirectional mapping between registers and temporaries.
class TempMap:
    # Dictionary mapping registers to temporaries.
    register_to_temp = {}
    # Dictionary mapping temporaries to registers.
    temp_to_register = {}

    @classmethod
    def initialize(cls):
        for register in all_registers:
            temp = TempManager.new_temp()
            cls.register_to_temp[register] = temp
            cls.temp_to_register[temp] = register

    @classmethod
    def update_temp_to_register(cls, register_allocation: Dict[Temp, Temp]):
        for temporary in register_allocation:
            cls.temp_to_register[temporary] = cls.temp_to_register[
                register_allocation[temporary]
            ]


# Temporal corresponding to the frame pointer register rbp.
def frame_pointer() -> Temp:
    return TempMap.register_to_temp["rbp"]


# Temporal corresponding to the return value register rax.
def return_value() -> Temp:
    return TempMap.register_to_temp["rax"]


# This is called after register allocation. All temps have an assigned
# register in the TempMap (if not, this should fail loudly).
def temp_to_str(temp: Temp) -> str:
    return TempMap.temp_to_register[temp]


# Access describes formals and locals stored in a frame or in registers
# as seen from the calee's perspective.
class Access(ABC):
    pass


# InFrame(X) indicates a memory location at offset X from the frame pointer.
@dataclass
class InFrame(Access):
    offset: int


# InReg(t84) indicates storage in the "register" t84.
@dataclass
class InRegister(Access):
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
