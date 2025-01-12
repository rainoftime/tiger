from typing import List
from abc import ABC
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


def convert_relational_operator(operator: IRT.RelationalOperator) -> str:
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


# There are two operators for multiplication and division, one for
# signed values and another for unsigned ones.
# Currently using signed version of mul and div.
def convert_binary_operator(operator: IRT.BinaryOperator) -> str:
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


def munch_statement(stmNode: IRT.Statement) -> None:
    # Label(label): The constant value of name 'label', defined to be the current
    # machine code address.
    if isinstance(stmNode, IRT.Label):
        Codegen.emit(Assembly.Label(line=f"{stmNode.label}:\n", label=stmNode.label))

    # Jump (addr, labels): Transfer control to address 'addr'. The destination may
    # be a literal label, or it may be an address calculated by any other kind of expression.
    # The list of labels 'labels' specifies all possible locations that 'addr' may jump to.
    elif isinstance(stmNode, IRT.Jump):
        Codegen.emit(
            Assembly.Operation(
                line="jmp 'j0\n", source=[], destination=[], jump=stmNode.labels
            )
        )
    # ConditionalJump(operator, exp_left, exp_right, true_label, false_label):
    # evaluate 'exp_left' and 'exp_right' in that order, yielding values 'a' and 'b'.
    # Then compare both values using 'operator'. If the result is TRUE, jump to 'true_label';
    # otherwise jump to 'false_label'.
    elif isinstance(stmNode, IRT.ConditionalJump):
        # The jump itself checks the flags in the EFL register.
        # These are usually set with TEST or CMP.
        # We swap the order of the expressions to match AT&T syntax's
        # order of operands.
        Codegen.emit(
            Assembly.Operation(
                line="cmpq %'s0, %'s1\n",
                source=[
                    munch_expression(stmNode.right),
                    munch_expression(stmNode.left),
                ],
                destination=[],
                jump=None,
            )
        )
        Codegen.emit(
            Assembly.Operation(
                line=f"{convert_relational_operator(stmNode.operator)} 'j0\n",
                source=[],
                destination=[],
                jump=[stmNode.true, stmNode.false],
            )
        )

    # Move(temporary, expression): we consider two different cases, based on the
    # content of 'temporary'.
    elif isinstance(stmNode, IRT.Move):
        # Warning: the IRT is built using the syntax as (move dst, src).
        # Here we swap the order of the expressions to match the AT&T syntax (move src, dst).

        # Move(Temporary t, exp): evaluates 'exp' and moves it to temporary 't'.
        if isinstance(stmNode.temporary, IRT.Temporary):
            Codegen.emit(
                Assembly.Move(
                    line="movq %'s0, %'d0\n",
                    source=[munch_expression(stmNode.expression)],
                    destination=[munch_expression(stmNode.temporary)],
                )
            )

        # Move(mem(e1), e2): evaluates 'e1', yielding address 'addr'.
        # Then evaluate 'e2' and store the result into 'WordSize' bytes of memory
        # starting at 'addr'.
        elif isinstance(stmNode.temporary, IRT.Memory):
            Codegen.emit(
                Assembly.Move(
                    line="movq %'s0, (%'s1)\n",
                    source=[
                        munch_expression(stmNode.expression),
                        munch_expression(stmNode.temporary.expression),
                    ],
                    destination=[],
                )
            )

        else:
            raise Exception("Munching an invalid version of node IRT.Move.")

    # StatementExpression(exp): Evaluates 'exp' and discards the result.
    elif isinstance(stmNode, IRT.StatementExpression):
        munch_expression(stmNode.expression)

    # We do not consider the cases for Sequence nodes here, given the modifications
    # done in chapter 8.
    elif isinstance(stmNode, IRT.Sequence):
        raise Exception("Found a IRT.Sequence node while munching.")

    else:
        raise Exception("No match for IRT node while munching a statement.")


def munch_arguments(arg_list: List[IRT.Expression]) -> List[Temp.Temp]:
    # Pass arguments through registers.
    temp_list = []
    for argument, register in zip(arg_list, Frame.argument_registers):
        register_temp = Frame.TempMap.register_to_temp[register]
        Codegen.emit(
            Assembly.Move(
                line="movq %'s0, %'d0\n",
                source=[munch_expression(argument)],
                destination=[register_temp],
            )
        )
        temp_list.append(register_temp)

    # Put the remaining arguments in the stack (if any).
    rsp = Frame.TempMap.register_to_temp["rsp"]
    for index in range(len(Frame.argument_registers), len(arg_list)):
        offset = Frame.word_size * (index - len(Frame.argument_registers))
        Codegen.emit(
            Assembly.Operation(
                line=f"movq %'s0, {offset}(%'s1)\n",
                source=[munch_expression(arg_list[index]), rsp],
                destination=[],
                jump=None,
            )
        )

    return temp_list


def munch_expression(expNode: IRT.Expression) -> Temp.Temp:
    # BinaryOperation(operator, exp_left, exp_right): Apply the binary operator
    # 'operator' to operands 'exp_left' and 'exp_right'. 'exp_left' is evaluated
    # before 'exp_right'.
    if isinstance(expNode, IRT.BinaryOperation):
        if expNode.operator in (
                IRT.BinaryOperator.plus,
                IRT.BinaryOperator.minus,
                IRT.BinaryOperator.andOp,
                IRT.BinaryOperator.orOp,
                IRT.BinaryOperator.xor,
        ):
            # add/sub/and/or/xor src, dst
            temp = Temp.TempManager.new_temp()
            Codegen.emit(
                Assembly.Move(
                    line="movq %'s0, %'d0\n",
                    source=[munch_expression(expNode.left)],
                    destination=[temp],
                )
            )
            Codegen.emit(
                Assembly.Operation(
                    line=f"{convert_binary_operator(expNode.operator)} %'s1, %'d0\n",
                    source=[temp, munch_expression(expNode.right)],
                    destination=[temp],
                    jump=None,
                )
            )
            return temp

        elif expNode.operator in (IRT.BinaryOperator.mul, IRT.BinaryOperator.div):
            # imul S :  RDX:RAX <--- S * RAX
            # In this implementation, we switch left and right operands, since
            # multiplication is commutative.
            # In this implementation, S has the right operand.
            # In this implementation, RAX has the left operand.
            # RDX:RAX has the result.
            # RDX is discarded in this implementation.

            # idiv S :  RDX <--- RDX:RAX mod S
            #           RAX <--- RDX:RAX / S
            # S has the divisor.
            # RDX:RAX has the dividend, but RDX is not used for the dividend in this
            # implementation. So, RAX has the dividend.
            # RAX has the quotient.
            # RDX has the remainder.

            temp = Temp.TempManager.new_temp()
            rax = Frame.TempMap.register_to_temp["rax"]
            rdx = Frame.TempMap.register_to_temp["rdx"]

            Codegen.emit(
                Assembly.Move(
                    line="movq %'s0, %'d0\n",
                    source=[munch_expression(expNode.left)],
                    destination=[rax],
                )
            )
            # R[%rdx]:R[%rax] <- SignExtend(R[%rax])
            # This is necessary only for the division, since it uses RDX:RAX as the dividend.
            if expNode.operator == IRT.BinaryOperator.div:
                Codegen.emit(
                    Assembly.Operation(
                        line="cqto\n", source=[rax], destination=[rdx], jump=None
                    )
                )
            Codegen.emit(
                Assembly.Operation(
                    line=f"{convert_binary_operator(expNode.operator)} %'s2\n",
                    source=[rax, rdx, munch_expression(expNode.right)],
                    destination=[rax, rdx],
                    jump=None,
                )
            )
            Codegen.emit(
                Assembly.Move(
                    line="movq %'s0, %'d0\n", source=[rax], destination=[temp]
                )
            )
            return temp

        elif isinstance(
                expNode.operator,
                (
                        IRT.BinaryOperator.lshift,
                        IRT.BinaryOperator.rshift,
                        IRT.BinaryOperator.arshift,
                ),
        ):
            # sal/sar/shr count, dst : dst <<=/>>= count
            dst_temp = munch_expression(expNode.left)
            Codegen.emit(
                Assembly.Operation(
                    line=f"{convert_binary_operator(expNode.operator)} %'s0, %'d0\n",
                    source=[munch_expression(expNode.right), dst_temp],
                    destination=[dst_temp],
                    jump=None,
                )
            )
            return dst_temp

        else:
            raise Exception(
                "Munching a node IRT.BinaryOperator with an invalid operator"
            )

    # Memory(addr): The contents of 'Frame.word_size' bytes of memory, starting at address addr.
    elif isinstance(expNode, IRT.Memory):
        temp = Temp.TempManager.new_temp()
        Codegen.emit(
            # This is an Operation and not a Move, since it should not be deleted if src and
            # dst are the same (they're not really the same, the source is a memory location).
            Assembly.Operation(
                line="movq (%'s0), %'d0\n",
                source=[munch_expression(expNode.expression)],
                destination=[temp],
                jump=None,
            )
        )
        return temp

    # Temporary(temp): the temporary 'temp'.
    elif isinstance(expNode, IRT.Temporary):
        return expNode.temporary

    # Name(n): Symbolic constant 'n' corresponding to an assembly language label.
    elif isinstance(expNode, IRT.Name):
        temp = Temp.TempManager.new_temp()
        rip = Frame.TempMap.register_to_temp["rip"]
        Codegen.emit(
            Assembly.Operation(
                line=f"leaq {expNode.label}(%'s0), %'d0\n",
                source=[rip],
                destination=[temp],
                jump=None,
            )
        )
        return temp

    # Constant(const): The integer constant 'const'.
    elif isinstance(expNode, IRT.Constant):
        temp = Temp.TempManager.new_temp()
        Codegen.emit(
            Assembly.Move(
                line=f"movq ${expNode.value}, %'d0\n",
                source=[],
                destination=[temp],
            )
        )
        return temp

    # Call(function, args): A procedure call: the application of function 'function'
    # to argument list 'args'. The subexpression 'function' is evaluated before the
    # arguments, which are evaluated left to right.
    elif isinstance(expNode, IRT.Call):
        # A CALL is expected to “trash” certain registers – the caller-save registers,
        # and the return-value register. This list of calldefs should be listed as
        # “destinations” of the CALL, so that the later phases of the compiler know
        # that something happens to them here.
        calldefs = [
            Frame.TempMap.register_to_temp[register]
            for register in Frame.caller_saved_registers
                            + Frame.argument_registers
                            + ["rax"]
        ]

        if isinstance(expNode.function, IRT.Name):
            # Reserve space in the stack for extra arguments.
            rsp = Frame.TempMap.register_to_temp["rsp"]
            stack_arguments_size = Frame.word_size * (
                    len(expNode.arguments) - len(Frame.argument_registers)
            )
            if stack_arguments_size > 0:
                Codegen.emit(
                    Assembly.Operation(
                        line=f"subq ${stack_arguments_size}, %'d0\n",
                        source=[rsp],
                        destination=[rsp],
                        jump=None,
                    )
                )

            Codegen.emit(
                Assembly.Operation(
                    line=f"call {expNode.function.label}\n",
                    source=munch_arguments(expNode.arguments),
                    destination=calldefs,
                    jump=None,
                )
            )

            # Restore the stack pointer (deallocate the space reserved earlier).
            if stack_arguments_size > 0:
                Codegen.emit(
                    Assembly.Operation(
                        line=f"addq ${stack_arguments_size}, %'d0\n",
                        source=[rsp],
                        destination=[rsp],
                        jump=None,
                    )
                )

        else:
            raise Exception("Found a IRT.Call where function is not an IRT.Name.")

        return Frame.TempMap.register_to_temp["rax"]

    # We do not consider the cases for EvaluateSequence nodes here, given the modifications
    # done in chapter 8.
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
