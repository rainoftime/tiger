from typing import List, Dict
from dataclasses import dataclass
from abc import ABC, abstractmethod
import intermediate_representation.tree as IRT
import instruction_selection.assembly as Assembly
from activation_records.temp import Temp, TempLabel, TempManager


class ArchitectureFrame(ABC):
    """Abstract base class for architecture-specific frame implementations"""
    
    @property
    @abstractmethod
    def word_size(self) -> int:
        pass
    
    @property
    @abstractmethod
    def special_registers(self) -> List[str]:
        pass
    
    @property
    @abstractmethod
    def argument_registers(self) -> List[str]:
        pass
    
    @property
    @abstractmethod
    def callee_saved_registers(self) -> List[str]:
        pass
    
    @property
    @abstractmethod
    def caller_saved_registers(self) -> List[str]:
        pass
    
    @property
    def all_registers(self) -> List[str]:
        return (
            self.special_registers +
            self.argument_registers +
            self.callee_saved_registers +
            self.caller_saved_registers
        )
    
    @abstractmethod
    def get_frame_pointer_register(self) -> str:
        pass
    
    @abstractmethod
    def get_return_register(self) -> str:
        pass
    
    @abstractmethod
    def get_stack_pointer_register(self) -> str:
        pass


class X86_64Frame(ArchitectureFrame):
    """x86-64 architecture frame implementation"""
    
    @property
    def word_size(self) -> int:
        return 8
    
    @property
    def special_registers(self) -> List[str]:
        return ["rip", "rsp", "rax"]
    
    @property
    def argument_registers(self) -> List[str]:
        return ["rdi", "rsi", "rdx", "rcx", "r8", "r9"]
    
    @property
    def callee_saved_registers(self) -> List[str]:
        return ["rbx", "rbp", "r12", "r13", "r14", "r15"]
    
    @property
    def caller_saved_registers(self) -> List[str]:
        return ["r10", "r11"]
    
    def get_frame_pointer_register(self) -> str:
        return "rbp"
    
    def get_return_register(self) -> str:
        return "rax"
    
    def get_stack_pointer_register(self) -> str:
        return "rsp"


class ARM64Frame(ArchitectureFrame):
    """ARM64 architecture frame implementation"""
    
    @property
    def word_size(self) -> int:
        return 8
    
    @property
    def special_registers(self) -> List[str]:
        return ["pc", "sp", "x0"]  # Program counter, stack pointer, return register
    
    @property
    def argument_registers(self) -> List[str]:
        return ["x0", "x1", "x2", "x3", "x4", "x5", "x6", "x7"]
    
    @property
    def callee_saved_registers(self) -> List[str]:
        return ["x19", "x20", "x21", "x22", "x23", "x24", "x25", "x26", "x27", "x28", "x29", "x30"]
    
    @property
    def caller_saved_registers(self) -> List[str]:
        return ["x8", "x9", "x10", "x11", "x12", "x13", "x14", "x15", "x16", "x17", "x18"]
    
    def get_frame_pointer_register(self) -> str:
        return "x29"
    
    def get_return_register(self) -> str:
        return "x0"
    
    def get_stack_pointer_register(self) -> str:
        return "sp"


class RISCVFrame(ArchitectureFrame):
    """RISC-V architecture frame implementation"""
    
    @property
    def word_size(self) -> int:
        return 8
    
    @property
    def special_registers(self) -> List[str]:
        return ["pc", "sp", "a0"]  # Program counter, stack pointer, return register
    
    @property
    def argument_registers(self) -> List[str]:
        return ["a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7"]
    
    @property
    def callee_saved_registers(self) -> List[str]:
        return ["s0", "s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9", "s10", "s11"]
    
    @property
    def caller_saved_registers(self) -> List[str]:
        return ["t0", "t1", "t2", "t3", "t4", "t5", "t6", "ra"]
    
    def get_frame_pointer_register(self) -> str:
        return "s0"  # Also known as fp
    
    def get_return_register(self) -> str:
        return "a0"
    
    def get_stack_pointer_register(self) -> str:
        return "sp"


# Global architecture frame instance
current_arch_frame: ArchitectureFrame = X86_64Frame()


def set_architecture_frame(arch_frame: ArchitectureFrame) -> None:
    """Set the current architecture frame"""
    global current_arch_frame
    current_arch_frame = arch_frame


def get_supported_architecture_frames() -> Dict[str, ArchitectureFrame]:
    """Get dictionary of supported architecture frames"""
    return {
        "x86-64": X86_64Frame(),
        "arm64": ARM64Frame(),
        "riscv": RISCVFrame(),
    }


# Architecture-independent access classes
class Access(ABC):
    pass


@dataclass
class InFrame(Access):
    offset: int


@dataclass
class InRegister(Access):
    register: Temp


# Architecture-aware TempMap
class ArchTempMap:
    """Architecture-aware temperature map"""
    
    def __init__(self, arch_frame: ArchitectureFrame):
        self.arch_frame = arch_frame
        self.register_to_temp: Dict[str, Temp] = {}
        self.temp_to_register: Dict[Temp, str] = {}
        self.initialize()
    
    def initialize(self):
        """Initialize register to temp mappings for current architecture"""
        self.register_to_temp.clear()
        self.temp_to_register.clear()
        
        for register in self.arch_frame.all_registers:
            temp = TempManager.new_temp()
            self.register_to_temp[register] = temp
            self.temp_to_register[temp] = register
    
    def update_temp_to_register(self, register_allocation: Dict[Temp, Temp]):
        """Update temp to register mapping after register allocation"""
        for temporary in register_allocation:
            if register_allocation[temporary] in self.temp_to_register:
                self.temp_to_register[temporary] = self.temp_to_register[
                    register_allocation[temporary]
                ]


# Global architecture-aware temp map
arch_temp_map: ArchTempMap = ArchTempMap(current_arch_frame)


def reinitialize_temp_map():
    """Reinitialize temp map when architecture changes"""
    global arch_temp_map
    arch_temp_map = ArchTempMap(current_arch_frame)


# Architecture-independent functions
def frame_pointer() -> Temp:
    """Get frame pointer temporary for current architecture"""
    fp_reg = current_arch_frame.get_frame_pointer_register()
    return arch_temp_map.register_to_temp[fp_reg]


def return_value() -> Temp:
    """Get return value temporary for current architecture"""
    ret_reg = current_arch_frame.get_return_register()
    return arch_temp_map.register_to_temp[ret_reg]


def temp_to_str(temp: Temp) -> str:
    """Convert temp to register string for current architecture"""
    return arch_temp_map.temp_to_register[temp]


class ArchFrame:
    """Architecture-aware frame class"""
    
    def __init__(self, name: TempLabel, formal_escapes: List[bool]):
        self.name = name
        self.arch_frame = current_arch_frame
        # The previous frame pointer value is stored at 0(fp)
        # Non-volatile registers are stored starting at negative offsets
        self.offset = 0
        
        # Lists of access locations for parameters and local variables
        self.formal_parameters = []
        self.local_variables = []
        
        # Process parameters passed by registers
        for escape in formal_escapes[:len(self.arch_frame.argument_registers)]:
            self._alloc_single_var(escape, self.formal_parameters)
        
        # Process extra parameters (stored in the previous frame)
        extra_argument_offset = 2 * self.arch_frame.word_size  # Skip saved fp and return address
        for escape in formal_escapes[len(self.arch_frame.argument_registers):]:
            self.formal_parameters.append(InFrame(extra_argument_offset))
            extra_argument_offset += self.arch_frame.word_size
    
    def alloc_local(self, escape: bool) -> Access:
        """Allocate a new local variable in the frame"""
        return self._alloc_single_var(escape, self.local_variables)
    
    def _alloc_single_var(self, escape: bool, access_list: List[Access]) -> Access:
        """Allocate a single variable or parameter in the frame"""
        if escape:
            self.offset -= self.arch_frame.word_size
            access_list.append(InFrame(self.offset))
        else:
            access_list.append(InRegister(TempManager.new_temp()))
        return access_list[-1]


def access_to_exp(access: Access, frame_pointer: IRT.Expression) -> IRT.Expression:
    """Convert frame access to IRT expression"""
    if isinstance(access, InFrame):
        return IRT.Memory(
            IRT.BinaryOperation(
                IRT.BinaryOperator.plus, frame_pointer, IRT.Constant(access.offset)
            )
        )
    if isinstance(access, InRegister):
        return IRT.Temporary(access.register)


def external_call(function_name: str, arguments: List[IRT.Expression]) -> IRT.Expression:
    """Create external function call"""
    return IRT.Call(IRT.Name(TempManager.named_label(function_name)), arguments)


def shift_view(frame: ArchFrame, function_body: IRT.Statement) -> IRT.Statement:
    """Apply view shift for function parameters"""
    shift_parameters = []
    
    for access, argument_register in zip(
        frame.formal_parameters, frame.arch_frame.argument_registers
    ):
        arg_temp = arch_temp_map.register_to_temp[argument_register]
        
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
                    IRT.Temporary(arg_temp),
                )
            )
        else:
            shift_parameters.append(
                IRT.Move(
                    IRT.Temporary(access.register),
                    IRT.Temporary(arg_temp),
                )
            )
    
    return IRT.Sequence(shift_parameters + [function_body])


def preserve_callee_registers(
    frame: ArchFrame, function_body: IRT.Statement
) -> IRT.Statement:
    """Preserve callee-saved registers across function call"""
    saves = []
    restores = []
    
    for register in frame.arch_frame.callee_saved_registers:
        reg_temp = arch_temp_map.register_to_temp[register]
        new_temp = TempManager.new_temp()
        
        # Save register to new temporary
        saves.append(IRT.Move(IRT.Temporary(new_temp), IRT.Temporary(reg_temp)))
        # Restore register from temporary
        restores.append(IRT.Move(IRT.Temporary(reg_temp), IRT.Temporary(new_temp)))
    
    return IRT.Sequence(saves + [function_body] + restores)


def sink(function_body: List[Assembly.Instruction]) -> List[Assembly.Instruction]:
    """Architecture-independent instruction sinking"""
    # Move the last instruction to the end if it's a label
    if function_body and isinstance(function_body[-1], Assembly.Label):
        return function_body[:-1] + [function_body[-1]]
    return function_body


def assembly_procedure(
    frame: ArchFrame, body: List[Assembly.Instruction]
) -> Assembly.Procedure:
    """Create assembly procedure with architecture-specific prologue/epilogue"""
    # Architecture-specific prologue and epilogue would be added here
    # For now, return a basic procedure
    return Assembly.Procedure(
        prologue="",  # Architecture-specific prologue
        body=body,
        epilogue="",  # Architecture-specific epilogue
        frame=frame,
    )


def string_literal(label: TempLabel, string: str) -> str:
    """Generate architecture-independent string literal"""
    # This might need architecture-specific handling in the future
    return f"{label}:\n\t.string \"{string}\"\n" 