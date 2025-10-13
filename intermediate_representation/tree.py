"""
Tree Intermediate Representation (IR) for Tiger Compiler

This module defines the tree-based intermediate representation used by the Tiger compiler.
The IR trees represent the program in a form suitable for optimization and code generation.

The IR consists of two main categories:
1. **Statements**: Represent computations that don't produce values (side effects)
2. **Expressions**: Represent computations that produce values

Key Features:
- Immutable tree structure using dataclasses
- Temporary variables for register allocation
- Labels for control flow
- Binary and relational operators for arithmetic and comparisons
- Memory access for variable and field operations

Architecture:
- All IR nodes inherit from Statement or Expression base classes
- Statements include sequences, jumps, conditionals, moves, and function calls
- Expressions include binary operations, memory access, temporaries, and constants
- Control flow uses labeled basic blocks with conditional and unconditional jumps

Author: Tiger Compiler Project
"""

from abc import ABC
from enum import Enum, auto
from typing import Optional, List

from dataclasses import dataclass

from activation_records.temp import TempLabel, Temp


class BinaryOperator(Enum):
    """
    Binary arithmetic and logical operators for IR expressions.

    These operators work on integer and boolean values:
    - Arithmetic: plus, minus, mul, div
    - Logical: andOp, orOp
    - Bitwise: lshift, rshift, arshift, xor
    """
    plus = auto()    # Addition
    minus = auto()   # Subtraction
    mul = auto()     # Multiplication
    div = auto()     # Division
    andOp = auto()   # Bitwise AND
    orOp = auto()    # Bitwise OR
    lshift = auto()  # Left shift
    rshift = auto()  # Right shift (logical)
    arshift = auto() # Arithmetic right shift
    xor = auto()     # Bitwise XOR


class RelationalOperator(Enum):
    """
    Comparison operators for conditional jumps.

    Used in conditional jump statements to test conditions:
    - Equality: eq, ne
    - Ordering: lt, le, gt, ge (signed)
    - Unsigned ordering: ult, ule, ugt, uge
    """
    eq = auto()   # Equal
    ne = auto()   # Not equal
    lt = auto()   # Less than (signed)
    gt = auto()   # Greater than (signed)
    le = auto()   # Less than or equal (signed)
    ge = auto()   # Greater than or equal (signed)
    ult = auto()  # Unsigned less than
    ule = auto()  # Unsigned less than or equal
    ugt = auto()  # Unsigned greater than
    uge = auto()  # Unsigned greater than or equal


class Statement(ABC):
    """
    Abstract base class for IR statement nodes.

    Statements represent computations that may have side effects
    but don't produce values. They include control flow, assignments,
    and procedure calls.
    """
    pass


class Expression(ABC):
    """
    Abstract base class for IR expression nodes.

    Expressions represent computations that produce values.
    They include arithmetic operations, memory access, function calls,
    and constant values.
    """
    pass


@dataclass
class Sequence(Statement):
    """
    Sequence of statements executed in order.

    Represents a block of statements that are executed sequentially.
    The value of a sequence is the value of its last statement.

    Attributes:
        sequence (List[Statement]): List of statements to execute in order
    """
    sequence: List[Statement]


@dataclass
class Label(Statement):
    """
    Label statement for control flow targets.

    Defines a labeled location in the code that can be jumped to.
    Labels are used as targets for jumps and calls.

    Attributes:
        label (TempLabel): The label identifier
    """
    label: TempLabel


@dataclass
class Jump(Statement):
    """
    Unconditional jump statement.

    Transfers control to a target address, which can be a label
    or a computed address expression.

    Attributes:
        expression (Expression): Target address (usually a Name expression)
        labels (List[TempLabel]): Possible target labels for the jump
    """
    expression: Expression
    labels: List[TempLabel]


@dataclass
class ConditionalJump(Statement):
    """
    Conditional jump statement.

    Evaluates a comparison and jumps to true or false label based on result.
    Used to implement if-then-else and loop control flow.

    Attributes:
        operator (RelationalOperator): Comparison operator to use
        left (Expression): Left operand for comparison
        right (Expression): Right operand for comparison
        true (Optional[TempLabel]): Label to jump to if comparison is true
        false (Optional[TempLabel]): Label to jump to if comparison is false
    """
    operator: RelationalOperator
    left: Expression
    right: Expression
    true: Optional[TempLabel] = None
    false: Optional[TempLabel] = None


@dataclass
class Move(Statement):
    """
    Move/assignment statement.

    Assigns the value of an expression to a temporary or memory location.
    Used for variable assignments and register transfers.

    Attributes:
        temporary (Expression): Destination (temporary or memory location)
        expression (Expression): Source expression to evaluate
    """
    temporary: Expression
    expression: Expression


@dataclass
class StatementExpression(Statement):
    """
    Statement that evaluates an expression for side effects.

    Executes an expression that may have side effects but discards the result.
    Used for function calls that don't return values.

    Attributes:
        expression (Expression): Expression to evaluate for side effects
    """
    expression: Expression


@dataclass
class BinaryOperation(Expression):
    """
    Binary operation expression.

    Represents a binary operation between two expressions using
    arithmetic, logical, or bitwise operators.

    Attributes:
        operator (BinaryOperator): The operation to perform
        left (Expression): Left operand
        right (Expression): Right operand
    """
    operator: BinaryOperator
    left: Expression
    right: Expression


@dataclass
class Memory(Expression):
    """
    Memory access expression.

    Represents reading from a memory location specified by an address expression.
    Used for variable access and pointer dereferencing.

    Attributes:
        expression (Expression): Address expression that specifies the memory location
    """
    expression: Expression


@dataclass
class Temporary(Expression):
    """
    Temporary variable expression.

    Represents a reference to a temporary variable (compiler-generated variable).
    Temporaries are used during register allocation and optimization.

    Attributes:
        temporary (Temp): The temporary variable identifier
    """
    temporary: Temp


@dataclass
class EvaluateSequence(Expression):
    """
    Expression sequence (ESEQ) - evaluates statement then expression.

    Represents an expression that first executes a statement (for side effects)
    and then evaluates to the value of an expression. Used to sequence
    computations where one expression depends on side effects of another.

    Attributes:
        statement (Statement): Statement to execute first
        expression (Expression): Expression to evaluate after the statement
    """
    statement: Statement
    expression: Expression


@dataclass
class Name(Expression):
    """
    Named label expression.

    Represents a reference to a labeled memory location.
    Used for function entry points and static data addresses.

    Attributes:
        label (TempLabel): The label being referenced
    """
    label: TempLabel


@dataclass
class Constant(Expression):
    """
    Constant value expression.

    Represents a constant integer value in the IR.
    Used for literal constants and compile-time computations.

    Attributes:
        value (int): The constant integer value
    """
    value: int


@dataclass
class Call(Expression):
    """
    Function call expression.

    Represents a call to a function with arguments.
    The function can be a named function or a function pointer.

    Attributes:
        function (Expression): Expression evaluating to the function to call
        arguments (List[Expression]): List of argument expressions
    """
    function: Expression
    arguments: List[Expression]


@dataclass
class Condition:
    """
    Conditional control flow helper structure.

    Groups together the components needed for conditional execution:
    a statement and the conditional jumps that depend on it.

    Attributes:
        statement (Statement): The statement that sets condition flags
        trues (List[ConditionalJump]): Jumps that occur when condition is true
        falses (List[ConditionalJump]): Jumps that occur when condition is false
    """
    statement: Statement
    trues: List[ConditionalJump]
    falses: List[ConditionalJump]


def negate_relational_operator(operator: RelationalOperator) -> RelationalOperator:
    """
    Get the logical negation of a relational operator.

    Used for implementing logical NOT operations and reversing
    conditional jump targets.

    Args:
        operator (RelationalOperator): The operator to negate

    Returns:
        RelationalOperator: The negated operator

    Examples:
        negate_relational_operator(RelationalOperator.lt) returns RelationalOperator.ge
        negate_relational_operator(RelationalOperator.eq) returns RelationalOperator.ne
    """
    negations = {
        RelationalOperator.eq: RelationalOperator.ne,
        RelationalOperator.ne: RelationalOperator.eq,
        RelationalOperator.lt: RelationalOperator.gt,
        RelationalOperator.gt: RelationalOperator.lt,
        RelationalOperator.le: RelationalOperator.le,
        RelationalOperator.ge: RelationalOperator.ge,
        RelationalOperator.ult: RelationalOperator.ule,
        RelationalOperator.ule: RelationalOperator.ult,
        RelationalOperator.ugt: RelationalOperator.ugt,
        RelationalOperator.uge: RelationalOperator.uge,
    }

    return negations[operator]
