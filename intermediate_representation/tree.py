#!/usr/bin/env python3
"""
Tiger Compiler - Tree Intermediate Representation

This module defines the tree-based intermediate representation (IR) used by
the Tiger compiler. The IR serves as a low-level, target-independent
representation of the program that bridges the gap between the high-level
abstract syntax tree and target machine code.

The IR consists of two main categories:
- Statements: Operations that perform actions but don't produce values
- Expressions: Operations that compute and return values

Key features:
- Tree-structured representation for easy manipulation
- Target-independent design
- Support for control flow (jumps, conditionals)
- Memory operations and function calls
- Temporary variables and labels for code generation

This IR is later canonicalized (linearized) and then translated to
target machine instructions.

Author: Tiger Compiler Team
"""

from abc import ABC
from enum import Enum, auto
from typing import Optional, List

from dataclasses import dataclass

from activation_records.temp import TempLabel, Temp


class BinaryOperator(Enum):
    """
    Enumeration of binary operators supported in the IR.
    
    These operators represent arithmetic, logical, and bitwise operations
    that can be performed on two operands.
    """
    plus = auto()     # Addition (+)
    minus = auto()    # Subtraction (-)
    mul = auto()      # Multiplication (*)
    div = auto()      # Division (/)
    andOp = auto()    # Bitwise AND (&)
    orOp = auto()     # Bitwise OR (|)
    lshift = auto()   # Left shift (<<)
    rshift = auto()   # Right shift (>>)
    arshift = auto()  # Arithmetic right shift
    xor = auto()      # Bitwise XOR (^)


class RelationalOperator(Enum):
    """
    Enumeration of relational operators for comparisons.
    
    These operators are used in conditional jumps to compare two values
    and determine control flow. Includes both signed and unsigned variants.
    """
    eq = auto()   # Equal (==)
    ne = auto()   # Not equal (!=)
    lt = auto()   # Less than (<)
    gt = auto()   # Greater than (>)
    le = auto()   # Less than or equal (<=)
    ge = auto()   # Greater than or equal (>=)
    ult = auto()  # Unsigned less than
    ule = auto()  # Unsigned less than or equal
    ugt = auto()  # Unsigned greater than
    uge = auto()  # Unsigned greater than or equal


class Statement(ABC):
    """
    Abstract base class for all IR statements.
    
    Statements represent operations that perform actions but do not
    produce values. They are executed for their side effects, such as
    modifying memory, transferring control, or performing I/O.
    """
    pass


class Expression(ABC):
    """
    Abstract base class for all IR expressions.
    
    Expressions represent computations that produce values. They can be
    evaluated to obtain a result, which may be used by other expressions
    or statements.
    """
    pass


@dataclass
class Sequence(Statement):
    """
    A sequence of statements to be executed in order.
    
    Represents a block of statements that should be executed sequentially.
    This is used to group multiple statements together.
    
    Attributes:
        sequence (List[Statement]): List of statements to execute in order
    """
    sequence: List[Statement]


@dataclass
class Label(Statement):
    """
    A label statement that marks a position in the code.
    
    Labels serve as targets for jump instructions and are used to
    implement control flow structures like loops and conditionals.
    
    Attributes:
        label (TempLabel): The label identifier
    """
    label: TempLabel


@dataclass
class Jump(Statement):
    """
    An unconditional jump statement.
    
    Transfers control to the address computed by the expression.
    The labels list contains all possible jump targets for optimization.
    
    Attributes:
        expression (Expression): Expression computing the target address
        labels (List[TempLabel]): List of possible jump targets
    """
    expression: Expression
    labels: List[TempLabel]


@dataclass
class ConditionalJump(Statement):
    """
    A conditional jump statement.
    
    Compares two expressions using a relational operator and jumps to
    different labels based on the result. Used to implement if statements,
    loops, and other control flow constructs.
    
    Attributes:
        operator (RelationalOperator): Comparison operator to use
        left (Expression): Left operand of the comparison
        right (Expression): Right operand of the comparison
        true (Optional[TempLabel]): Label to jump to if condition is true
        false (Optional[TempLabel]): Label to jump to if condition is false
    """
    operator: RelationalOperator
    left: Expression
    right: Expression
    true: Optional[TempLabel] = None
    false: Optional[TempLabel] = None


@dataclass
class Move(Statement):
    """
    A move (assignment) statement.
    
    Assigns the value of an expression to a temporary variable or memory location.
    This is the primary way to store computed values.
    
    Attributes:
        temporary (Expression): Target location (temporary or memory)
        expression (Expression): Source value to assign
    """
    temporary: Expression
    expression: Expression


@dataclass
class StatementExpression(Statement):
    """
    A statement that evaluates an expression for its side effects.
    
    Used when an expression is evaluated for its side effects (like function calls)
    rather than its return value. The computed value is discarded.
    
    Attributes:
        expression (Expression): Expression to evaluate
    """
    expression: Expression


@dataclass
class BinaryOperation(Expression):
    """
    A binary operation expression.
    
    Applies a binary operator to two operand expressions and produces a result.
    Used for arithmetic, logical, and bitwise operations.
    
    Attributes:
        operator (BinaryOperator): The binary operator to apply
        left (Expression): Left operand expression
        right (Expression): Right operand expression
    """
    operator: BinaryOperator
    left: Expression
    right: Expression


@dataclass
class Memory(Expression):
    """
    A memory access expression.
    
    Reads a value from memory at the address computed by the expression.
    Used to implement variable access, array indexing, and record field access.
    
    Attributes:
        expression (Expression): Expression computing the memory address
    """
    expression: Expression


@dataclass
class Temporary(Expression):
    """
    A temporary variable expression.
    
    Represents a temporary variable that holds an intermediate value during
    computation. Temporaries are later assigned to physical registers.
    
    Attributes:
        temporary (Temp): The temporary variable identifier
    """
    temporary: Temp


@dataclass
class EvaluateSequence(Expression):
    """
    An expression that evaluates a statement then an expression.
    
    Executes a statement for its side effects, then evaluates and returns
    the value of an expression. This allows statements to be embedded
    within expressions.
    
    Attributes:
        statement (Statement): Statement to execute first
        expression (Expression): Expression to evaluate and return
    """
    statement: Statement
    expression: Expression


@dataclass
class Name(Expression):
    """
    A name (label address) expression.
    
    Represents the address of a label, typically used for function addresses
    or jump targets. Evaluates to the memory address where the label is located.
    
    Attributes:
        label (TempLabel): The label whose address to compute
    """
    label: TempLabel


@dataclass
class Constant(Expression):
    """
    A constant integer expression.
    
    Represents a compile-time constant integer value. Used for literals,
    offsets, and other fixed values.
    
    Attributes:
        value (int): The constant integer value
    """
    value: int


@dataclass
class Call(Expression):
    """
    A function call expression.
    
    Calls a function with the given arguments and returns the result.
    The function address is computed by an expression, allowing for
    both direct and indirect function calls.
    
    Attributes:
        function (Expression): Expression computing the function address
        arguments (List[Expression]): List of argument expressions
    """
    function: Expression
    arguments: List[Expression]


@dataclass
class Condition:
    """
    A condition structure for control flow analysis.
    
    Used during IR generation to track conditional expressions and their
    associated jump statements. Helps in generating efficient control flow code.
    
    Attributes:
        statement (Statement): The statement implementing the condition
        trues (List[ConditionalJump]): Jumps taken when condition is true
        falses (List[ConditionalJump]): Jumps taken when condition is false
    """
    statement: Statement
    trues: List[ConditionalJump]
    falses: List[ConditionalJump]


def negate_relational_operator(operator: RelationalOperator) -> RelationalOperator:
    """
    Return the negation of a relational operator.
    
    This function is used during code generation to optimize conditional
    jumps by negating conditions when beneficial.
    
    Args:
        operator (RelationalOperator): The operator to negate
        
    Returns:
        RelationalOperator: The negated operator
        
    Examples:
        >>> negate_relational_operator(RelationalOperator.eq)
        RelationalOperator.ne
        >>> negate_relational_operator(RelationalOperator.lt)
        RelationalOperator.ge
    """
    negations = {
        RelationalOperator.eq: RelationalOperator.ne,
        RelationalOperator.ne: RelationalOperator.eq,
        RelationalOperator.lt: RelationalOperator.ge,  # Fixed: lt negates to ge
        RelationalOperator.gt: RelationalOperator.le,  # Fixed: gt negates to le
        RelationalOperator.le: RelationalOperator.gt,  # Fixed: le negates to gt
        RelationalOperator.ge: RelationalOperator.lt,  # Fixed: ge negates to lt
        RelationalOperator.ult: RelationalOperator.uge, # Fixed: ult negates to uge
        RelationalOperator.ule: RelationalOperator.ugt, # Fixed: ule negates to ugt
        RelationalOperator.ugt: RelationalOperator.ule, # Fixed: ugt negates to ule
        RelationalOperator.uge: RelationalOperator.ult, # Fixed: uge negates to ult
    }

    return negations[operator]
