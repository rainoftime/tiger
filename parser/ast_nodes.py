#!/usr/bin/env python3
"""
Tiger Language Abstract Syntax Tree (AST) Node Definitions

This module defines the data structures representing the Abstract Syntax Tree
for the Tiger programming language. Each node type corresponds to a syntactic
construct in the Tiger language grammar.

The AST is built during parsing and serves as the intermediate representation
between the source code and the semantic analysis phase. All nodes inherit
from the base ASTNode class and include position information for error reporting.

Node Categories:
- Declarations: Type, variable, and function declarations
- Types: Type specifications (named, record, array)
- Expressions: All Tiger expressions (literals, operations, control flow)
- Variables: Variable access patterns (simple, field, subscript)

Author: Tiger Compiler Team
"""

from abc import ABC
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class ASTNode(ABC):
    """
    Base class for all Abstract Syntax Tree nodes.
    
    All AST nodes include position information for error reporting
    and debugging purposes.
    
    Attributes:
        position (int): Character position in source code where this construct begins
    """
    position: int


class Declaration(ASTNode):
    """
    Base class for all declaration nodes.
    
    Declarations introduce new names into the Tiger program's namespace,
    including type definitions, variable declarations, and function definitions.
    """
    pass


class Type(ASTNode):
    """
    Base class for all type specification nodes.
    
    Type nodes represent type annotations in Tiger programs,
    including named types, record types, and array types.
    """
    pass


class Expression(ASTNode):
    """
    Base class for all expression nodes.
    
    Expressions represent computations that produce values in Tiger programs,
    including literals, operations, function calls, and control structures.
    """
    pass


class Variable(ASTNode):
    """
    Base class for all variable access nodes.
    
    Variable nodes represent different ways to access stored values,
    including simple variables, record fields, and array elements.
    """
    pass


class Oper(Enum):
    """
    Enumeration of binary operators in Tiger.
    
    Defines all binary operators supported by the Tiger language,
    including arithmetic, comparison, and logical operators.
    """
    plus = 1     # +  (addition)
    minus = 2    # -  (subtraction)
    times = 3    # *  (multiplication)
    divide = 4   # /  (division)
    eq = 5       # =  (equality)
    neq = 6      # <> (inequality)
    lt = 7       # <  (less than)
    le = 8       # <= (less than or equal)
    gt = 9       # >  (greater than)
    ge = 10      # >= (greater than or equal)


# DECLARATION NODES
# These nodes represent various forms of declarations in Tiger programs


@dataclass
class DeclarationBlock(ASTNode):
    """
    A block containing multiple declarations.
    
    Used in let expressions to group type, variable, and function declarations
    that are mutually recursive and share the same scope.
    
    Attributes:
        declaration_list: List of declarations in this block
    """
    declaration_list: List[Declaration]


@dataclass
class TypeDec(ASTNode):
    """
    A single type declaration within a type declaration block.
    
    Defines a new type name and its corresponding type specification.
    Example: type intArray = array of int
    
    Attributes:
        name: Name of the new type being declared
        type: Type specification for the new type
    """
    name: str
    type: Type


@dataclass
class TypeDecBlock(Declaration):
    """
    A block of mutually recursive type declarations.
    
    Groups related type declarations that may reference each other.
    All types in the block are declared simultaneously.
    
    Attributes:
        type_dec_list: List of individual type declarations
    """
    type_dec_list: List[TypeDec]


@dataclass
class NameTy(Type):
    """
    A named type reference.
    
    References an existing type by name, either built-in (int, string)
    or user-defined.
    
    Attributes:
        name: Name of the referenced type
    """
    name: str


@dataclass
class Field(ASTNode):
    """
    A field definition in a record type or function parameter list.
    
    Specifies a name and its associated type, used in record type
    definitions and function parameter lists.
    
    Attributes:
        name: Name of the field or parameter
        type: Type name for this field or parameter
    """
    name: str
    type: str


@dataclass
class RecordTy(Type):
    """
    A record type definition.
    
    Defines a structured type with named fields.
    Example: type person = {name: string, age: int}
    
    Attributes:
        field_list: List of fields in the record
    """
    field_list: List[Field]


@dataclass
class ArrayTy(Type):
    """
    An array type definition.
    
    Defines an array type with elements of a specified type.
    Example: type intArray = array of int
    
    Attributes:
        array: Name of the element type
    """
    array: str


@dataclass
class VariableDec(Declaration):
    """
    A variable declaration.
    
    Declares a new variable with optional type annotation and initial value.
    Example: var x: int := 42 or var y := "hello"
    
    Attributes:
        name: Name of the variable being declared
        type: Optional type annotation
        exp: Initial value expression
        escape: Whether variable escapes to nested functions (for optimization)
    """
    name: str
    type: Optional[str]
    exp: Expression
    escape: bool = False


@dataclass
class FunctionDec(ASTNode):
    """
    A single function declaration.
    
    Defines a function with parameters, optional return type, and body.
    Example: function factorial(n: int): int = if n <= 1 then 1 else n * factorial(n-1)
    
    Attributes:
        name: Name of the function
        params: List of parameter specifications
        param_escapes: List indicating which parameters escape to nested functions
        return_type: Optional return type annotation
        body: Function body expression
    """
    name: str
    params: List[Field]
    param_escapes: List[bool]
    return_type: Optional[str]
    body: Expression


@dataclass
class FunctionDecBlock(Declaration):
    """
    A block of mutually recursive function declarations.
    
    Groups related function declarations that may call each other.
    All functions in the block are declared simultaneously.
    
    Attributes:
        function_dec_list: List of individual function declarations
    """
    function_dec_list: List[FunctionDec]


# EXPRESSION NODES
# These nodes represent all forms of expressions in Tiger programs


@dataclass
class VarExp(Expression):
    """
    A variable reference expression.
    
    Represents accessing the value of a variable, record field, or array element.
    
    Attributes:
        var: Variable access specification
    """
    var: Variable


@dataclass
class NilExp(Expression):
    """
    The nil literal expression.
    
    Represents the nil value, which can be assigned to any record type
    or used in comparisons.
    """
    pass


@dataclass
class IntExp(Expression):
    """
    An integer literal expression.
    
    Represents a constant integer value.
    
    Attributes:
        int: The integer value
    """
    int: int


@dataclass
class StringExp(Expression):
    """
    A string literal expression.
    
    Represents a constant string value.
    
    Attributes:
        string: The string value (including quotes)
    """
    string: str


@dataclass
class CallExp(Expression):
    """
    A function call expression.
    
    Represents calling a function with a list of argument expressions.
    Example: factorial(5) or print("hello")
    
    Attributes:
        func: Name of the function to call
        args: List of argument expressions
    """
    func: str
    args: List[Expression]


@dataclass
class OpExp(Expression):
    """
    A binary operation expression.
    
    Represents applying a binary operator to two operand expressions.
    Example: x + y or a < b
    
    Attributes:
        oper: The binary operator
        left: Left operand expression
        right: Right operand expression
    """
    oper: Oper
    left: Expression
    right: Expression


@dataclass
class ExpField(ASTNode):
    """
    A field assignment in a record creation expression.
    
    Specifies a field name and its value expression for record construction.
    
    Attributes:
        name: Name of the field being assigned
        exp: Expression providing the field's value
    """
    name: str
    exp: Expression


@dataclass
class RecordExp(Expression):
    """
    A record creation expression.
    
    Creates a new record instance with specified field values.
    Example: person{name="John", age=25}
    
    Attributes:
        type: Name of the record type to create
        fields: List of field assignments
    """
    type: str
    fields: List[ExpField]


@dataclass
class SeqExp(Expression):
    """
    A sequence expression.
    
    Evaluates a list of expressions in order, returning the value of the last one.
    Example: (print("hello"); x := 5; x + 1)
    
    Attributes:
        seq: List of expressions to evaluate in sequence
    """
    seq: List[Expression]


@dataclass
class AssignExp(Expression):
    """
    An assignment expression.
    
    Assigns a new value to a variable, record field, or array element.
    Example: x := 42 or arr[i] := value
    
    Attributes:
        var: Variable being assigned to
        exp: Expression providing the new value
    """
    var: Variable
    exp: Expression


@dataclass
class IfExp(Expression):
    """
    A conditional expression.
    
    Evaluates a test expression and chooses between two alternatives.
    Example: if x > 0 then "positive" else "non-positive"
    
    Attributes:
        test: Boolean test expression
        then_do: Expression to evaluate if test is true
        else_do: Optional expression to evaluate if test is false
    """
    test: Expression
    then_do: Expression
    else_do: Optional[Expression]


@dataclass
class WhileExp(Expression):
    """
    A while loop expression.
    
    Repeatedly evaluates a body expression while a test condition is true.
    Example: while i < 10 do (print(i); i := i + 1)
    
    Attributes:
        test: Boolean test expression
        body: Expression to evaluate repeatedly
    """
    test: Expression
    body: Expression


@dataclass
class BreakExp(Expression):
    """
    A break expression.
    
    Exits the innermost enclosing loop (while or for).
    Can only be used within loop constructs.
    """
    pass


@dataclass
class ForExp(Expression):
    """
    A for loop expression.
    
    Iterates over a range of integer values with a loop variable.
    Example: for i := 1 to 10 do print(i)
    
    Attributes:
        var: Name of the loop variable
        lo: Expression for the starting value
        hi: Expression for the ending value
        body: Expression to evaluate for each iteration
        escape: Whether loop variable escapes to nested functions
    """
    var: str
    lo: Expression
    hi: Expression
    body: Expression
    escape: bool = False


@dataclass
class LetExp(Expression):
    """
    A let expression.
    
    Introduces local declarations and evaluates a body expression in their scope.
    Example: let var x := 5 in x + 1 end
    
    Attributes:
        decs: Block of local declarations
        body: Expression to evaluate with the declarations in scope
    """
    decs: DeclarationBlock
    body: SeqExp


@dataclass
class ArrayExp(Expression):
    """
    An array creation expression.
    
    Creates a new array of specified size with all elements initialized to the same value.
    Example: intArray[10] of 0
    
    Attributes:
        type: Name of the array type to create
        size: Expression specifying the array size
        init: Expression providing the initial value for all elements
    """
    type: str
    size: Expression
    init: Expression


@dataclass
class EmptyExp(Expression):
    """
    An empty expression.
    
    Represents a missing or empty expression, typically used as a placeholder
    or in contexts where no expression is needed.
    """
    pass


# VARIABLE ACCESS NODES
# These nodes represent different ways to access stored values


@dataclass
class SimpleVar(Variable):
    """
    A simple variable reference.
    
    Accesses a variable by name.
    Example: x or myVariable
    
    Attributes:
        sym: Name of the variable
    """
    sym: str


@dataclass
class FieldVar(Variable):
    """
    A record field access.
    
    Accesses a field of a record variable.
    Example: person.name or record.field
    
    Attributes:
        var: Variable representing the record
        sym: Name of the field to access
    """
    var: Variable
    sym: str


@dataclass
class SubscriptVar(Variable):
    """
    An array element access.
    
    Accesses an element of an array variable using an index expression.
    Example: arr[i] or matrix[row][col]
    
    Attributes:
        var: Variable representing the array
        exp: Expression providing the index
    """
    var: Variable
    exp: Expression
