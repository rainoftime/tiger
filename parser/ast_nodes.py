"""
Abstract Syntax Tree (AST) Node Definitions for Tiger Programming Language

This module defines the data structures that represent the abstract syntax tree
of Tiger programs. Each node in the AST corresponds to a syntactic construct
in the Tiger language and contains all the necessary information for semantic
analysis and code generation.

The AST follows a hierarchical structure:
- ASTNode: Base class for all AST nodes (contains position info)
- Declaration: Base class for declarations (types, variables, functions)
- Type: Base class for type definitions
- Expression: Base class for expressions
- Variable: Base class for variable references

All AST nodes use dataclasses for immutability and automatic equality comparison.

Author: Tiger Compiler Project
"""

from abc import ABC
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class ASTNode(ABC):
    """
    Base class for all Abstract Syntax Tree nodes.

    Every AST node contains position information for error reporting
    and debugging purposes. The position indicates the line number
    where the construct appears in the source code.

    Attributes:
        position (int): Line number in source code where this node appears
    """
    position: int


class Declaration(ASTNode):
    """
    Base class for declaration nodes.

    Declarations introduce new names into the symbol table.
    Subclasses include type declarations, variable declarations,
    and function declarations.
    """
    pass


class Type(ASTNode):
    """
    Base class for type definition nodes.

    Types define the structure of data in Tiger programs.
    Subclasses include named types, record types, and array types.
    """
    pass


class Expression(ASTNode):
    """
    Base class for expression nodes.

    Expressions represent computations that produce values.
    Subclasses include literals, variables, function calls,
    arithmetic operations, and control flow constructs.
    """
    pass


class Variable(ASTNode):
    """
    Base class for variable reference nodes.

    Variables represent named storage locations that can hold values.
    Subclasses include simple variables, field access, and array indexing.
    """
    pass


class Oper(Enum):
    """
    Enumeration of binary and comparison operators in Tiger.

    This enum defines all the operators that can appear in binary
    operations and comparisons. Each operator has a unique integer
    value for easy identification during code generation.

    Binary operators:
    - plus, minus, times, divide: Arithmetic operations
    - eq, neq, lt, le, gt, ge: Comparison operations
    """
    plus = 1    # Addition (+)
    minus = 2   # Subtraction (-)
    times = 3   # Multiplication (*)
    divide = 4  # Division (/)
    eq = 5      # Equal to (=)
    neq = 6     # Not equal to (<>)
    lt = 7      # Less than (<)
    le = 8      # Less than or equal (<=)
    gt = 9      # Greater than (>)
    ge = 10     # Greater than or equal (>=)


# =====================================================================
# DECLARATION NODES
# =====================================================================


@dataclass
class DeclarationBlock(ASTNode):
    """
    Block of declarations in a let expression.

    Groups multiple declarations together that are introduced
    in the same scope. Used in let expressions to define
    types, variables, and functions.

    Attributes:
        declaration_list (List[Declaration]): List of declarations in this block
    """
    declaration_list: List[Declaration]


@dataclass
class TypeDec(ASTNode):
    """
    Type declaration node.

    Declares a new type name as an alias for another type.
    Example: type myint = int

    Attributes:
        name (str): Name of the type being declared
        type (Type): The type being aliased
    """
    name: str
    type: Type


@dataclass
class TypeDecBlock(Declaration):
    """
    Block of type declarations.

    Groups multiple type declarations together. This is used
    when multiple types are declared in the same let expression.

    Attributes:
        type_dec_list (List[TypeDec]): List of type declarations
    """
    type_dec_list: List[TypeDec]


@dataclass
class NameTy(Type):
    """
    Named type reference.

    References a type by name. This can be either a built-in type
    (like int, string) or a user-defined type.

    Attributes:
        name (str): Name of the referenced type
    """
    name: str


@dataclass
class Field(ASTNode):
    """
    Field definition in records or function parameters.

    Represents a single field with a name and type.
    Used in record type definitions and function signatures.

    Attributes:
        name (str): Name of the field
        type (str): Type name of the field
    """
    name: str
    type: str


@dataclass
class RecordTy(Type):
    """
    Record type definition.

    Defines a record type with multiple named fields.
    Example: {name: string, age: int}

    Attributes:
        field_list (List[Field]): List of fields in the record
    """
    field_list: List[Field]


@dataclass
class ArrayTy(Type):
    """
    Array type definition.

    Defines an array type that can hold multiple elements
    of a base type. Example: array of int

    Attributes:
        array (str): Name of the base type for array elements
    """
    array: str


@dataclass
class VariableDec(Declaration):
    """
    Variable declaration node.

    Declares a new variable with an optional type annotation
    and an initializing expression.

    Attributes:
        name (str): Name of the variable
        type (Optional[str]): Optional type annotation
        exp (Expression): Initializing expression
        escape (bool): Whether variable escapes (needs heap allocation)
    """
    name: str
    type: Optional[str]
    exp: Expression
    escape: bool = False


@dataclass
class FunctionDec(ASTNode):
    """
    Function declaration node.

    Declares a function with parameters, return type, and body.
    This represents a single function definition.

    Attributes:
        name (str): Name of the function
        params (List[Field]): Parameter list
        param_escapes (List[bool]): Escape information for parameters
        return_type (Optional[str]): Return type (None for void functions)
        body (Expression): Function body expression
    """
    name: str
    params: List[Field]
    param_escapes: List[bool]
    return_type: Optional[str]
    body: Expression


@dataclass
class FunctionDecBlock(Declaration):
    """
    Block of function declarations.

    Groups multiple function declarations together.
    Used when multiple functions are declared in the same scope.

    Attributes:
        function_dec_list (List[FunctionDec]): List of function declarations
    """
    function_dec_list: List[FunctionDec]


# =====================================================================
# EXPRESSION NODES
# =====================================================================


@dataclass
class VarExp(Expression):
    """
    Variable expression node.

    Represents a reference to a variable. The variable can be
    a simple variable, field access, or array element access.

    Attributes:
        var (Variable): The variable being referenced
    """
    var: Variable


@dataclass
class NilExp(Expression):
    """
    Nil expression node.

    Represents the nil value, which is Tiger's null reference.
    Used for empty references and uninitialized pointers.
    """
    pass


@dataclass
class IntExp(Expression):
    """
    Integer literal expression node.

    Represents an integer constant value.

    Attributes:
        int (int): The integer value
    """
    int: int


@dataclass
class StringExp(Expression):
    """
    String literal expression node.

    Represents a string constant value.

    Attributes:
        string (str): The string value
    """
    string: str


@dataclass
class CallExp(Expression):
    """
    Function call expression node.

    Represents a call to a function with arguments.

    Attributes:
        func (str): Name of the function being called
        args (List[Expression]): List of argument expressions
    """
    func: str
    args: List[Expression]


@dataclass
class OpExp(Expression):
    """
    Binary operation expression node.

    Represents a binary operation between two expressions.
    Includes arithmetic, comparison, and logical operations.

    Attributes:
        oper (Oper): The operation to perform
        left (Expression): Left operand
        right (Expression): Right operand
    """
    oper: Oper
    left: Expression
    right: Expression


@dataclass
class ExpField(ASTNode):
    """
    Field in a record expression.

    Represents a field assignment in a record creation expression.
    Each field has a name and an initializing expression.

    Attributes:
        name (str): Name of the field
        exp (Expression): Expression that initializes this field
    """
    name: str
    exp: Expression


@dataclass
class RecordExp(Expression):
    """
    Record creation expression node.

    Represents the creation of a record with named fields.
    Example: Point {x = 10, y = 20}

    Attributes:
        type (str): Name of the record type
        fields (List[ExpField]): List of field initializations
    """
    type: str
    fields: List[ExpField]


@dataclass
class SeqExp(Expression):
    """
    Sequence expression node.

    Represents a sequence of expressions evaluated in order.
    The value of the sequence is the value of the last expression.
    Example: (expr1; expr2; expr3)

    Attributes:
        seq (List[Expression]): List of expressions in the sequence
    """
    seq: List[Expression]


@dataclass
class AssignExp(Expression):
    """
    Assignment expression node.

    Represents an assignment to a variable.
    Example: var := expression

    Attributes:
        var (Variable): The variable being assigned to
        exp (Expression): The expression being assigned
    """
    var: Variable
    exp: Expression


@dataclass
class IfExp(Expression):
    """
    Conditional expression node.

    Represents an if-then-else expression.
    Example: if condition then then_expr else else_expr

    Attributes:
        test (Expression): The condition expression
        then_do (Expression): Expression evaluated if condition is true
        else_do (Optional[Expression]): Expression evaluated if condition is false (can be None)
    """
    test: Expression
    then_do: Expression
    else_do: Optional[Expression]


@dataclass
class WhileExp(Expression):
    """
    While loop expression node.

    Represents a while loop that evaluates the body as long as the condition is true.
    The value of a while loop is always 0.
    Example: while condition do body

    Attributes:
        test (Expression): The loop condition
        body (Expression): The loop body
    """
    test: Expression
    body: Expression


@dataclass
class BreakExp(Expression):
    """
    Break expression node.

    Represents a break statement that exits the innermost loop.
    Can only appear within for or while loops.
    """
    pass


@dataclass
class ForExp(Expression):
    """
    For loop expression node.

    Represents a for loop that iterates from lo to hi inclusive.
    The loop variable is immutable within the loop body.
    Example: for i := lo to hi do body

    Attributes:
        var (str): Name of the loop variable
        lo (Expression): Lower bound expression
        hi (Expression): Upper bound expression
        body (Expression): Loop body expression
        escape (bool): Whether loop variable escapes (needs heap allocation)
    """
    var: str
    lo: Expression
    hi: Expression
    body: Expression
    escape: bool = False


@dataclass
class LetExp(Expression):
    """
    Let expression node.

    Represents a let expression that introduces local declarations
    and evaluates a body expression in that scope.
    Example: let declarations in body end

    Attributes:
        decs (DeclarationBlock): Declarations introduced in this scope
        body (SeqExp): Body expression evaluated in the declared scope
    """
    decs: DeclarationBlock
    body: SeqExp


@dataclass
class ArrayExp(Expression):
    """
    Array creation expression node.

    Represents the creation of an array with a given size and initial value.
    Example: ArrayType [size] of init_value

    Attributes:
        type (str): Name of the array type
        size (Expression): Expression for the array size
        init (Expression): Expression for initial value of all elements
    """
    type: str
    size: Expression
    init: Expression


@dataclass
class EmptyExp(Expression):
    """
    Empty expression node.

    Represents an empty expression that produces no value.
    Used internally by the parser for optional elements.
    """
    pass


# =====================================================================
# VARIABLE NODES
# =====================================================================


@dataclass
class SimpleVar(Variable):
    """
    Simple variable reference node.

    Represents a reference to a variable by name.
    This is the most basic form of variable access.
    Example: myVariable

    Attributes:
        sym (str): Name of the variable
    """
    sym: str


@dataclass
class FieldVar(Variable):
    """
    Field access variable node.

    Represents access to a field of a record variable.
    Example: record.field

    Attributes:
        var (Variable): The record variable being accessed
        sym (str): Name of the field
    """
    var: Variable
    sym: str


@dataclass
class SubscriptVar(Variable):
    """
    Array element access variable node.

    Represents access to an element of an array variable.
    Example: array[index]

    Attributes:
        var (Variable): The array variable being accessed
        exp (Expression): Index expression for element access
    """
    var: Variable
    exp: Expression
