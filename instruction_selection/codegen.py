from typing import List, Dict, Optional
from abc import ABC, abstractmethod
import instruction_selection.assembly as Assembly
import intermediate_representation.tree as IRT
import activation_records.temp as Temp
import activation_records.frame as Frame


# x86-64
# AT&T syntax:
# instruction source, destination
# System V ABI

# Addressing modes for source operands in 'mov src, dst'
# $val: is a constant value
# %R: is a register
# 0xaddr: source read from Mem[0xaddr]
# (%R): source read from Mem[%R], where R is a register
# D(%R): source read from Mem[%R+D] where D is the displacement and R is a register


class Architecture(ABC):
    """Abstract base class for different target architectures"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def word_size(self) -> int:
        pass
    
    @property
    @abstractmethod
    def register_prefix(self) -> str:
        pass
    
    @abstractmethod
    def convert_relational_operator(self, operator: IRT.RelationalOperator) -> str:
        pass
    
    @abstractmethod
    def convert_binary_operator(self, operator: IRT.BinaryOperator) -> str:
        pass
    
    @abstractmethod
    def emit_label(self, label: str) -> Assembly.Instruction:
        pass
    
    @abstractmethod
    def emit_jump(self, labels: List[str]) -> Assembly.Instruction:
        pass
    
    @abstractmethod
    def emit_conditional_jump(self, operator: IRT.RelationalOperator, 
                            left_temp: Temp.Temp, right_temp: Temp.Temp,
                            true_label: str, false_label: str) -> List[Assembly.Instruction]:
        pass
    
    @abstractmethod
    def emit_move_reg_to_reg(self, src: Temp.Temp, dst: Temp.Temp) -> Assembly.Instruction:
        pass
    
    @abstractmethod
    def emit_move_reg_to_mem(self, src: Temp.Temp, addr: Temp.Temp) -> Assembly.Instruction:
        pass
    
    @abstractmethod
    def emit_load_immediate(self, value: int, dst: Temp.Temp) -> Assembly.Instruction:
        pass
    
    @abstractmethod
    def emit_load_memory(self, addr: Temp.Temp, dst: Temp.Temp) -> Assembly.Instruction:
        pass
    
    @abstractmethod
    def emit_load_address(self, label: str, dst: Temp.Temp) -> Assembly.Instruction:
        pass
    
    @abstractmethod
    def emit_binary_operation(self, operator: IRT.BinaryOperator,
                            left: Temp.Temp, right: Temp.Temp, dst: Temp.Temp) -> List[Assembly.Instruction]:
        pass
    
    @abstractmethod
    def emit_function_call(self, function_label: str, args: List[Temp.Temp]) -> List[Assembly.Instruction]:
        pass
    
    @abstractmethod
    def get_return_register(self) -> str:
        pass


class X86_64Architecture(Architecture):
    """x86-64 architecture with AT&T syntax"""
    
    @property
    def name(self) -> str:
        return "x86-64"
    
    @property
    def word_size(self) -> int:
        return 8
    
    @property
    def register_prefix(self) -> str:
        return "%"
    
    def convert_relational_operator(self, operator: IRT.RelationalOperator) -> str:
        conversion_dictionary = {
            IRT.RelationalOperator.eq: "je",
            IRT.RelationalOperator.ne: "jne",
            IRT.RelationalOperator.lt: "jl",
            IRT.RelationalOperator.gt: "jg",
            IRT.RelationalOperator.le: "jle",
            IRT.RelationalOperator.ge: "jge",
            IRT.RelationalOperator.ult: "jb",
            IRT.RelationalOperator.ule: "jbe",
            IRT.RelationalOperator.ugt: "ja",
            IRT.RelationalOperator.uge: "jae",
        }
        return conversion_dictionary[operator]
    
    def convert_binary_operator(self, operator: IRT.BinaryOperator) -> str:
        conversion_dictionary = {
            IRT.BinaryOperator.plus: "addq",
            IRT.BinaryOperator.minus: "subq",
            IRT.BinaryOperator.mul: "imulq",
            IRT.BinaryOperator.div: "idivq",
            IRT.BinaryOperator.andOp: "andq",
            IRT.BinaryOperator.orOp: "orq",
            IRT.BinaryOperator.lshift: "salq",
            IRT.BinaryOperator.rshift: "sarq",
            IRT.BinaryOperator.arshift: "shrq",
            IRT.BinaryOperator.xor: "xorq",
        }
        return conversion_dictionary[operator]
    
    def emit_label(self, label: str) -> Assembly.Instruction:
        return Assembly.Label(line=f"{label}:\n", label=label)
    
    def emit_jump(self, labels: List[str]) -> Assembly.Instruction:
        return Assembly.Operation(
            line="jmp 'j0\n", source=[], destination=[], jump=labels
        )
    
    def emit_conditional_jump(self, operator: IRT.RelationalOperator,
                            left_temp: Temp.Temp, right_temp: Temp.Temp,
                            true_label: str, false_label: str) -> List[Assembly.Instruction]:
        instructions = []
        # Compare instruction (swap order for AT&T syntax)
        instructions.append(Assembly.Operation(
            line="cmpq %'s0, %'s1\n",
            source=[right_temp, left_temp],
            destination=[],
            jump=None,
        ))
        # Conditional jump
        instructions.append(Assembly.Operation(
            line=f"{self.convert_relational_operator(operator)} 'j0\n",
            source=[],
            destination=[],
            jump=[true_label, false_label],
        ))
        return instructions
    
    def emit_move_reg_to_reg(self, src: Temp.Temp, dst: Temp.Temp) -> Assembly.Instruction:
        return Assembly.Move(
            line="movq %'s0, %'d0\n",
            source=[src],
            destination=[dst],
        )
    
    def emit_move_reg_to_mem(self, src: Temp.Temp, addr: Temp.Temp) -> Assembly.Instruction:
        return Assembly.Move(
            line="movq %'s0, (%'s1)\n",
            source=[src, addr],
            destination=[],
        )
    
    def emit_load_immediate(self, value: int, dst: Temp.Temp) -> Assembly.Instruction:
        return Assembly.Move(
            line=f"movq ${value}, %'d0\n",
            source=[],
            destination=[dst],
        )
    
    def emit_load_memory(self, addr: Temp.Temp, dst: Temp.Temp) -> Assembly.Instruction:
        return Assembly.Operation(
            line="movq (%'s0), %'d0\n",
            source=[addr],
            destination=[dst],
            jump=None,
        )
    
    def emit_load_address(self, label: str, dst: Temp.Temp) -> Assembly.Instruction:
        rip = Frame.TempMap.register_to_temp["rip"]
        return Assembly.Operation(
            line=f"leaq {label}(%'s0), %'d0\n",
            source=[rip],
            destination=[dst],
            jump=None,
        )
    
    def emit_binary_operation(self, operator: IRT.BinaryOperator,
                            left: Temp.Temp, right: Temp.Temp, dst: Temp.Temp) -> List[Assembly.Instruction]:
        instructions = []
        
        if operator in (
            IRT.BinaryOperator.plus,
            IRT.BinaryOperator.minus,
            IRT.BinaryOperator.andOp,
            IRT.BinaryOperator.orOp,
            IRT.BinaryOperator.xor,
        ):
            instructions.append(self.emit_move_reg_to_reg(left, dst))
            instructions.append(Assembly.Operation(
                line=f"{self.convert_binary_operator(operator)} %'s1, %'d0\n",
                source=[dst, right],
                destination=[dst],
                jump=None,
            ))
        
        elif operator in (IRT.BinaryOperator.mul, IRT.BinaryOperator.div):
            rax = Frame.TempMap.register_to_temp["rax"]
            rdx = Frame.TempMap.register_to_temp["rdx"]
            
            instructions.append(self.emit_move_reg_to_reg(left, rax))
            
            if operator == IRT.BinaryOperator.div:
                instructions.append(Assembly.Operation(
                    line="cqto\n", source=[rax], destination=[rdx], jump=None
                ))
            
            instructions.append(Assembly.Operation(
                line=f"{self.convert_binary_operator(operator)} %'s2\n",
                source=[rax, rdx, right],
                destination=[rax, rdx],
                jump=None,
            ))
            instructions.append(self.emit_move_reg_to_reg(rax, dst))
        
        elif operator in (
            IRT.BinaryOperator.lshift,
            IRT.BinaryOperator.rshift,
            IRT.BinaryOperator.arshift,
        ):
            instructions.append(self.emit_move_reg_to_reg(left, dst))
            instructions.append(Assembly.Operation(
                line=f"{self.convert_binary_operator(operator)} %'s0, %'d0\n",
                source=[right, dst],
                destination=[dst],
                jump=None,
            ))
        
        return instructions
    
    def emit_function_call(self, function_label: str, args: List[Temp.Temp]) -> List[Assembly.Instruction]:
        instructions = []
        
        # Move arguments to registers and stack
        for i, arg in enumerate(args):
            if i < len(Frame.argument_registers):
                reg_temp = Frame.TempMap.register_to_temp[Frame.argument_registers[i]]
                instructions.append(self.emit_move_reg_to_reg(arg, reg_temp))
            else:
                # Put on stack
                rsp = Frame.TempMap.register_to_temp["rsp"]
                offset = Frame.word_size * (i - len(Frame.argument_registers))
                instructions.append(Assembly.Operation(
                    line=f"movq %'s0, {offset}(%'s1)\n",
                    source=[arg, rsp],
                    destination=[],
                    jump=None,
                ))
        
        # Reserve/restore stack space for extra arguments
        rsp = Frame.TempMap.register_to_temp["rsp"]
        stack_size = Frame.word_size * max(0, len(args) - len(Frame.argument_registers))
        
        if stack_size > 0:
            instructions.append(Assembly.Operation(
                line=f"subq ${stack_size}, %'d0\n",
                source=[rsp],
                destination=[rsp],
                jump=None,
            ))
        
        # Call instruction
        calldefs = [
            Frame.TempMap.register_to_temp[register]
            for register in (Frame.caller_saved_registers + 
                           Frame.argument_registers + ["rax"])
        ]
        instructions.append(Assembly.Operation(
            line=f"call {function_label}\n",
            source=[Frame.TempMap.register_to_temp[reg] for reg in Frame.argument_registers[:len(args)]],
            destination=calldefs,
            jump=None,
        ))
        
        if stack_size > 0:
            instructions.append(Assembly.Operation(
                line=f"addq ${stack_size}, %'d0\n",
                source=[rsp],
                destination=[rsp],
                jump=None,
            ))
        
        return instructions
    
    def get_return_register(self) -> str:
        return "rax"


class ARMArchitecture(Architecture):
    """ARM64 (AArch64) architecture"""
    
    @property
    def name(self) -> str:
        return "ARM64"
    
    @property
    def word_size(self) -> int:
        return 8
    
    @property
    def register_prefix(self) -> str:
        return "x"
    
    def convert_relational_operator(self, operator: IRT.RelationalOperator) -> str:
        conversion_dictionary = {
            IRT.RelationalOperator.eq: "b.eq",
            IRT.RelationalOperator.ne: "b.ne", 
            IRT.RelationalOperator.lt: "b.lt",
            IRT.RelationalOperator.gt: "b.gt",
            IRT.RelationalOperator.le: "b.le",
            IRT.RelationalOperator.ge: "b.ge",
            IRT.RelationalOperator.ult: "b.lo",
            IRT.RelationalOperator.ule: "b.ls",
            IRT.RelationalOperator.ugt: "b.hi",
            IRT.RelationalOperator.uge: "b.hs",
        }
        return conversion_dictionary[operator]
    
    def convert_binary_operator(self, operator: IRT.BinaryOperator) -> str:
        conversion_dictionary = {
            IRT.BinaryOperator.plus: "add",
            IRT.BinaryOperator.minus: "sub",
            IRT.BinaryOperator.mul: "mul",
            IRT.BinaryOperator.div: "sdiv",
            IRT.BinaryOperator.andOp: "and",
            IRT.BinaryOperator.orOp: "orr",
            IRT.BinaryOperator.lshift: "lsl",
            IRT.BinaryOperator.rshift: "asr",
            IRT.BinaryOperator.arshift: "lsr",
            IRT.BinaryOperator.xor: "eor",
        }
        return conversion_dictionary[operator]
    
    def emit_label(self, label: str) -> Assembly.Instruction:
        return Assembly.Label(line=f"{label}:\n", label=label)
    
    def emit_jump(self, labels: List[str]) -> Assembly.Instruction:
        return Assembly.Operation(
            line="b 'j0\n", source=[], destination=[], jump=labels
        )
    
    def emit_conditional_jump(self, operator: IRT.RelationalOperator,
                            left_temp: Temp.Temp, right_temp: Temp.Temp,
                            true_label: str, false_label: str) -> List[Assembly.Instruction]:
        instructions = []
        # Compare instruction
        instructions.append(Assembly.Operation(
            line="cmp %'s0, %'s1\n",
            source=[left_temp, right_temp],
            destination=[],
            jump=None,
        ))
        # Conditional branch
        instructions.append(Assembly.Operation(
            line=f"{self.convert_relational_operator(operator)} 'j0\n",
            source=[],
            destination=[],
            jump=[true_label, false_label],
        ))
        return instructions
    
    def emit_move_reg_to_reg(self, src: Temp.Temp, dst: Temp.Temp) -> Assembly.Instruction:
        return Assembly.Move(
            line="mov %'d0, %'s0\n",
            source=[src],
            destination=[dst],
        )
    
    def emit_move_reg_to_mem(self, src: Temp.Temp, addr: Temp.Temp) -> Assembly.Instruction:
        return Assembly.Move(
            line="str %'s0, [%'s1]\n",
            source=[src, addr],
            destination=[],
        )
    
    def emit_load_immediate(self, value: int, dst: Temp.Temp) -> Assembly.Instruction:
        return Assembly.Move(
            line=f"mov %'d0, #{value}\n",
            source=[],
            destination=[dst],
        )
    
    def emit_load_memory(self, addr: Temp.Temp, dst: Temp.Temp) -> Assembly.Instruction:
        return Assembly.Operation(
            line="ldr %'d0, [%'s0]\n",
            source=[addr],
            destination=[dst],
            jump=None,
        )
    
    def emit_load_address(self, label: str, dst: Temp.Temp) -> Assembly.Instruction:
        return Assembly.Operation(
            line=f"adr %'d0, {label}\n",
            source=[],
            destination=[dst],
            jump=None,
        )
    
    def emit_binary_operation(self, operator: IRT.BinaryOperator,
                            left: Temp.Temp, right: Temp.Temp, dst: Temp.Temp) -> List[Assembly.Instruction]:
        instructions = []
        op_str = self.convert_binary_operator(operator)
        
        if operator in (IRT.BinaryOperator.lshift, IRT.BinaryOperator.rshift, IRT.BinaryOperator.arshift):
            # Shift operations
            instructions.append(Assembly.Operation(
                line=f"{op_str} %'d0, %'s0, %'s1\n",
                source=[left, right],
                destination=[dst],
                jump=None,
            ))
        else:
            # Regular binary operations
            instructions.append(Assembly.Operation(
                line=f"{op_str} %'d0, %'s0, %'s1\n",
                source=[left, right],
                destination=[dst],
                jump=None,
            ))
        
        return instructions
    
    def emit_function_call(self, function_label: str, args: List[Temp.Temp]) -> List[Assembly.Instruction]:
        instructions = []
        
        # ARM64 uses x0-x7 for arguments
        arg_registers = ["x0", "x1", "x2", "x3", "x4", "x5", "x6", "x7"]
        
        # Move arguments to registers and stack
        for i, arg in enumerate(args):
            if i < len(arg_registers):
                # For ARM, we'll assume register mapping exists
                instructions.append(Assembly.Move(
                    line=f"mov {arg_registers[i]}, %'s0\n",
                    source=[arg],
                    destination=[],
                ))
            else:
                # Put on stack - simplified for now
                instructions.append(Assembly.Operation(
                    line=f"str %'s0, [sp, #{8 * (i - len(arg_registers))}]\n",
                    source=[arg],
                    destination=[],
                    jump=None,
                ))
        
        # Call instruction
        instructions.append(Assembly.Operation(
            line=f"bl {function_label}\n",
            source=args[:min(len(args), len(arg_registers))],
            destination=[],  # Simplified caller-saved register handling
            jump=None,
        ))
        
        return instructions
    
    def get_return_register(self) -> str:
        return "x0"


class RISCVArchitecture(Architecture):
    """RISC-V 64-bit architecture"""
    
    @property
    def name(self) -> str:
        return "RISC-V"
    
    @property
    def word_size(self) -> int:
        return 8
    
    @property
    def register_prefix(self) -> str:
        return "x"
    
    def convert_relational_operator(self, operator: IRT.RelationalOperator) -> str:
        conversion_dictionary = {
            IRT.RelationalOperator.eq: "beq",
            IRT.RelationalOperator.ne: "bne",
            IRT.RelationalOperator.lt: "blt",
            IRT.RelationalOperator.gt: "bgt",
            IRT.RelationalOperator.le: "ble",
            IRT.RelationalOperator.ge: "bge",
            IRT.RelationalOperator.ult: "bltu",
            IRT.RelationalOperator.ule: "bleu",
            IRT.RelationalOperator.ugt: "bgtu",
            IRT.RelationalOperator.uge: "bgeu",
        }
        return conversion_dictionary[operator]
    
    def convert_binary_operator(self, operator: IRT.BinaryOperator) -> str:
        conversion_dictionary = {
            IRT.BinaryOperator.plus: "add",
            IRT.BinaryOperator.minus: "sub",
            IRT.BinaryOperator.mul: "mul",
            IRT.BinaryOperator.div: "div",
            IRT.BinaryOperator.andOp: "and",
            IRT.BinaryOperator.orOp: "or",
            IRT.BinaryOperator.lshift: "sll",
            IRT.BinaryOperator.rshift: "sra",
            IRT.BinaryOperator.arshift: "srl",
            IRT.BinaryOperator.xor: "xor",
        }
        return conversion_dictionary[operator]
    
    def emit_label(self, label: str) -> Assembly.Instruction:
        return Assembly.Label(line=f"{label}:\n", label=label)
    
    def emit_jump(self, labels: List[str]) -> Assembly.Instruction:
        return Assembly.Operation(
            line="j 'j0\n", source=[], destination=[], jump=labels
        )
    
    def emit_conditional_jump(self, operator: IRT.RelationalOperator,
                            left_temp: Temp.Temp, right_temp: Temp.Temp,
                            true_label: str, false_label: str) -> List[Assembly.Instruction]:
        instructions = []
        # RISC-V has direct conditional branches
        instructions.append(Assembly.Operation(
            line=f"{self.convert_relational_operator(operator)} %'s0, %'s1, 'j0\n",
            source=[left_temp, right_temp],
            destination=[],
            jump=[true_label, false_label],
        ))
        return instructions
    
    def emit_move_reg_to_reg(self, src: Temp.Temp, dst: Temp.Temp) -> Assembly.Instruction:
        return Assembly.Move(
            line="mv %'d0, %'s0\n",
            source=[src],
            destination=[dst],
        )
    
    def emit_move_reg_to_mem(self, src: Temp.Temp, addr: Temp.Temp) -> Assembly.Instruction:
        return Assembly.Move(
            line="sd %'s0, 0(%'s1)\n",
            source=[src, addr],
            destination=[],
        )
    
    def emit_load_immediate(self, value: int, dst: Temp.Temp) -> Assembly.Instruction:
        return Assembly.Move(
            line=f"li %'d0, {value}\n",
            source=[],
            destination=[dst],
        )
    
    def emit_load_memory(self, addr: Temp.Temp, dst: Temp.Temp) -> Assembly.Instruction:
        return Assembly.Operation(
            line="ld %'d0, 0(%'s0)\n",
            source=[addr],
            destination=[dst],
            jump=None,
        )
    
    def emit_load_address(self, label: str, dst: Temp.Temp) -> Assembly.Instruction:
        return Assembly.Operation(
            line=f"la %'d0, {label}\n",
            source=[],
            destination=[dst],
            jump=None,
        )
    
    def emit_binary_operation(self, operator: IRT.BinaryOperator,
                            left: Temp.Temp, right: Temp.Temp, dst: Temp.Temp) -> List[Assembly.Instruction]:
        instructions = []
        op_str = self.convert_binary_operator(operator)
        
        instructions.append(Assembly.Operation(
            line=f"{op_str} %'d0, %'s0, %'s1\n",
            source=[left, right],
            destination=[dst],
            jump=None,
        ))
        
        return instructions
    
    def emit_function_call(self, function_label: str, args: List[Temp.Temp]) -> List[Assembly.Instruction]:
        instructions = []
        
        # RISC-V uses a0-a7 for arguments
        arg_registers = ["a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7"]
        
        # Move arguments to registers and stack
        for i, arg in enumerate(args):
            if i < len(arg_registers):
                instructions.append(Assembly.Move(
                    line=f"mv {arg_registers[i]}, %'s0\n",
                    source=[arg],
                    destination=[],
                ))
            else:
                # Put on stack - simplified
                instructions.append(Assembly.Operation(
                    line=f"sd %'s0, {8 * (i - len(arg_registers))}(sp)\n",
                    source=[arg],
                    destination=[],
                    jump=None,
                ))
        
        # Call instruction
        instructions.append(Assembly.Operation(
            line=f"call {function_label}\n",
            source=args[:min(len(args), len(arg_registers))],
            destination=[],  # Simplified caller-saved register handling
            jump=None,
        ))
        
        return instructions
    
    def get_return_register(self) -> str:
        return "a0"


# Global architecture instance - can be configured
current_architecture: Architecture = X86_64Architecture()


def set_architecture(arch: Architecture) -> None:
    """Set the current target architecture"""
    global current_architecture
    current_architecture = arch


def munch_statement(stmNode: IRT.Statement) -> None:
    """Convert IRT statement to assembly instructions using current architecture"""
    # Label(label): The constant value of name 'label', defined to be the current
    # machine code address.
    if isinstance(stmNode, IRT.Label):
        Codegen.emit(current_architecture.emit_label(stmNode.label))

    # Jump (addr, labels): Transfer control to address 'addr'. 
    elif isinstance(stmNode, IRT.Jump):
        Codegen.emit(current_architecture.emit_jump(stmNode.labels))
    
    # ConditionalJump(operator, exp_left, exp_right, true_label, false_label):
    elif isinstance(stmNode, IRT.ConditionalJump):
        left_temp = munch_expression(stmNode.left)
        right_temp = munch_expression(stmNode.right)
        instructions = current_architecture.emit_conditional_jump(
            stmNode.operator, left_temp, right_temp, stmNode.true, stmNode.false
        )
        for instr in instructions:
            Codegen.emit(instr)

    # Move(temporary, expression): we consider two different cases
    elif isinstance(stmNode, IRT.Move):
        # Move(Temporary t, exp): evaluates 'exp' and moves it to temporary 't'.
        if isinstance(stmNode.temporary, IRT.Temporary):
            src_temp = munch_expression(stmNode.expression)
            dst_temp = munch_expression(stmNode.temporary)
            Codegen.emit(current_architecture.emit_move_reg_to_reg(src_temp, dst_temp))

        # Move(mem(e1), e2): evaluates 'e1', yielding address 'addr'.
        elif isinstance(stmNode.temporary, IRT.Memory):
            src_temp = munch_expression(stmNode.expression)
            addr_temp = munch_expression(stmNode.temporary.expression)
            Codegen.emit(current_architecture.emit_move_reg_to_mem(src_temp, addr_temp))

        else:
            raise Exception("Munching an invalid version of node IRT.Move.")

    # StatementExpression(exp): Evaluates 'exp' and discards the result.
    elif isinstance(stmNode, IRT.StatementExpression):
        munch_expression(stmNode.expression)

    elif isinstance(stmNode, IRT.Sequence):
        raise Exception("Found a IRT.Sequence node while munching.")

    else:
        raise Exception("No match for IRT node while munching a statement.")


def munch_arguments(arg_list: List[IRT.Expression]) -> List[Temp.Temp]:
    """Convert argument expressions to temporaries"""
    temp_list = []
    for argument in arg_list:
        temp_list.append(munch_expression(argument))
    return temp_list


def munch_expression(expNode: IRT.Expression) -> Temp.Temp:
    """Convert IRT expression to assembly instructions and return result temporary"""
    # BinaryOperation(operator, exp_left, exp_right): Apply the binary operator
    if isinstance(expNode, IRT.BinaryOperation):
        left_temp = munch_expression(expNode.left)
        right_temp = munch_expression(expNode.right)
        result_temp = Temp.TempManager.new_temp()
        
        instructions = current_architecture.emit_binary_operation(
            expNode.operator, left_temp, right_temp, result_temp
        )
        for instr in instructions:
            Codegen.emit(instr)
        
        return result_temp

    # Memory(addr): The contents of memory starting at address addr.
    elif isinstance(expNode, IRT.Memory):
        addr_temp = munch_expression(expNode.expression)
        result_temp = Temp.TempManager.new_temp()
        Codegen.emit(current_architecture.emit_load_memory(addr_temp, result_temp))
        return result_temp

    # Temporary(temp): the temporary 'temp'.
    elif isinstance(expNode, IRT.Temporary):
        return expNode.temporary

    # Name(n): Symbolic constant 'n' corresponding to an assembly language label.
    elif isinstance(expNode, IRT.Name):
        result_temp = Temp.TempManager.new_temp()
        Codegen.emit(current_architecture.emit_load_address(expNode.label, result_temp))
        return result_temp

    # Constant(const): The integer constant 'const'.
    elif isinstance(expNode, IRT.Constant):
        result_temp = Temp.TempManager.new_temp()
        Codegen.emit(current_architecture.emit_load_immediate(expNode.value, result_temp))
        return result_temp

    # Call(function, args): A procedure call
    elif isinstance(expNode, IRT.Call):
        if isinstance(expNode.function, IRT.Name):
            arg_temps = munch_arguments(expNode.arguments)
            instructions = current_architecture.emit_function_call(
                expNode.function.label, arg_temps
            )
            for instr in instructions:
                Codegen.emit(instr)
            
            # Return value is in the architecture-specific return register
            return_reg = current_architecture.get_return_register()
            if hasattr(Frame.TempMap, 'register_to_temp') and return_reg in Frame.TempMap.register_to_temp:
                return Frame.TempMap.register_to_temp[return_reg]
            else:
                # Fallback for architectures not fully integrated with Frame
                result_temp = Temp.TempManager.new_temp()
                return result_temp
        else:
            raise Exception("Found a IRT.Call where function is not an IRT.Name.")

    elif isinstance(expNode, IRT.EvaluateSequence):
        raise Exception("Found a IRT.EvaluateSequence node while munching.")

    else:
        raise Exception("No match for IRT node while munching an expression.")


class Codegen(ABC):
    instruction_list = []

    @classmethod
    def emit(cls, instruction: Assembly.Instruction) -> None:
        cls.instruction_list.append(instruction)

    @classmethod
    def codegen(cls, statement_list: List[IRT.Statement]) -> List[Assembly.Instruction]:
        for statement in statement_list:
            munch_statement(statement)
        instruction_list_copy = cls.instruction_list
        cls.instruction_list = []
        return instruction_list_copy

    @classmethod
    def set_target_architecture(cls, architecture: Architecture) -> None:
        """Set the target architecture for code generation"""
        set_architecture(architecture)

    @classmethod
    def get_supported_architectures(cls) -> Dict[str, Architecture]:
        """Get dictionary of supported architectures"""
        return {
            "x86-64": X86_64Architecture(),
            "arm": ARMArchitecture(), 
            "riscv": RISCVArchitecture(),
        }
